# src/agentic_rag/vectorstore/qdrant_client.py
from __future__ import annotations

from typing import List, Dict, Iterable, Optional, Any
from uuid import uuid4

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    MatchAny,
)
from app.utils.logger import Logger
from app.utils.error_handler import ErrorHandler

# Simple Embedder class to avoid import issues
class SimpleEmbedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        try:
            from transformers import AutoTokenizer, AutoModel
            import torch
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)
        except ImportError:
            raise ImportError("Please install transformers and torch: pip install transformers torch")

    def generate(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        import torch
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            inputs = self.tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=512)
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            with torch.no_grad():
                outputs = self.model(**inputs)
            batch_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            embeddings.extend(batch_embeddings.tolist())
        return embeddings


class QdrantStore:
    """
    Opinionated Qdrant wrapper for RAG over S3-hosted PDFs.

    - Single collection (e.g., 'academia_docs') for all subjects.
    - Payload carries: subject, topics, s3_uri, doc_id, page, chunk_id, title, text.
    - Fast filtering via payload indexes on 'subject' and 'topics'.
    - Async client; one Embedder kept warm in RAM.
    """

    def __init__(self, url: str, api_key: str, collection_name: str):
        self.logger = Logger()
        self.error_handler = ErrorHandler(self.logger)
        self.url = url
        self.api_key = api_key
        self.collection_name = collection_name
        self.client = AsyncQdrantClient(url=self.url, api_key=self.api_key)
        self.embedder = SimpleEmbedder()  # single model in RAM
        self.logger.info(f"Qdrant client ready for '{self.collection_name}'")

    # ----------------------- Setup -----------------------

    async def init_store(self, vector_size: Optional[int] = None):
        """
        Ensure the collection exists (idempotent) and payload indexes are present.

        Args:
            vector_size: embedding dimensionality. If omitted, will try to infer from the embedder.
        """
        try:
            # Infer vector size if not provided
            if vector_size is None:
                # Common Embedder patterns: .dim or .embedding_size; fallback to 1536
                vector_size = getattr(self.embedder, "dim", None) or getattr(self.embedder, "embedding_size", None) or 384

            # Create collection if missing
            try:
                await self.client.get_collection(self.collection_name)
                self.logger.info(f"Collection '{self.collection_name}' already exists")
            except Exception:
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=int(vector_size), distance=Distance.COSINE),
                )
                self.logger.info(f"Created collection '{self.collection_name}' (size={vector_size}, metric=COSINE)")

            # Create payload indexes (idempotent)
            await self._ensure_payload_index("subject", "keyword")
            await self._ensure_payload_index("topics", "keyword")  # array of keywords supported
            await self._ensure_payload_index("doc_id", "keyword")

        except Exception as e:
            self.error_handler.handle(e, context="QdrantStore.init_store")

    async def _ensure_payload_index(self, field_name: str, field_schema: str):
        try:
            await self.client.create_payload_index(
                collection_name=self.collection_name,
                field_name=field_name,
                field_schema=field_schema,
            )
            self.logger.info(f"Created payload index: {field_name} ({field_schema})")
        except Exception as e:
            # Qdrant returns an error if the index already exists; keep logs mild
            self.logger.debug(f"Index '{field_name}' may already exist: {e}")

    # ----------------------- Upsert -----------------------

    async def upsert_chunks(
        self,
        chunks: Iterable[Dict[str, Any]],
        *,
        text_key: str = "text",
        batch_size: int = 128,
    ):
        """
        Upsert a batch of chunks (each chunk is a dict with metadata).
        Required per-chunk keys:
          - text (or override with text_key)
          - subject: "Math" | "Physics" | "Chemistry"
          - s3_uri: full S3 path (e.g., s3://bucket/Math/file.pdf)
          - doc_id: stable ID for the PDF
          - page: int
          - chunk_id: int (sequential)
          - title: filename or document title
          - topics: list[str] (optional)
        """
        try:
            buf: List[PointStruct] = []

            async def _flush():
                if not buf:
                    return
                await self.client.upsert(collection_name=self.collection_name, points=buf)
                self.logger.info(f"Upserted {len(buf)} points into '{self.collection_name}'")
                buf.clear()

            texts: List[str] = []
            stash: List[Dict[str, Any]] = []

            # Collect in batches for a single embedding call
            for chunk in chunks:
                t = chunk.get(text_key) or chunk.get("text")
                if not t:
                    self.logger.warning("Skipping chunk with no text")
                    continue
                texts.append(t)
                stash.append(chunk)

                if len(texts) >= batch_size:
                    await self._embed_and_stage_points(texts, stash, buf)
                    await _flush()

            # Tail
            if texts:
                await self._embed_and_stage_points(texts, stash, buf)
                await _flush()

        except Exception as e:
            self.error_handler.handle(e, context="QdrantStore.upsert_chunks")

    async def _embed_and_stage_points(
        self,
        texts: List[str],
        stash: List[Dict[str, Any]],
        point_buffer: List[PointStruct],
    ):
        # 1) Embed in one go
        vectors = self.embedder.generate(texts)
        if hasattr(vectors, "tolist"):
            vectors = vectors.tolist()

        # 2) Build points with payload
        for vec, meta in zip(vectors, stash):
            point_buffer.append(
                PointStruct(
                    id=str(uuid4()),
                    vector=vec,
                    payload={
                        "subject": meta.get("subject"),
                        "topics": meta.get("topics", []),
                        "s3_uri": meta.get("s3_uri"),
                        "doc_id": meta.get("doc_id"),
                        "page": meta.get("page"),
                        "chunk_id": meta.get("chunk_id"),
                        "title": meta.get("title"),
                        "text": meta.get("text") or meta.get("content"),
                    },
                )
            )

        # 3) Clear staging arrays
        texts.clear()
        stash.clear()

    # ----------------------- Search -----------------------

    async def search(
        self,
        query: str,
        *,
        top_k: int = 8,
        subject: Optional[str] = None,
        topics_any: Optional[List[str]] = None,
        doc_ids_any: Optional[List[str]] = None,
        score_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Vector search with optional payload filters.
        - subject: exact match
        - topics_any: at least one topic must match
        - doc_ids_any: restrict to any of these documents
        - score_threshold: keep only hits with score >= threshold (COSINE similarity)

        Returns a normalized list of hits with payload + score.
        """
        import math

        try:
            # 1) Embed query
            qv = self.embedder.generate([query])[0]
            if hasattr(qv, "tolist"):
                qv = qv.tolist()

            # 2) Build filter
            flt = self._build_filter(subject=subject, topics_any=topics_any, doc_ids_any=doc_ids_any)

            # 3) Search
            hits = await self.client.search(
                collection_name=self.collection_name,
                query_vector=qv,
                query_filter=flt,
                limit=top_k,
            )

            # 4) Post-filter by score threshold (if provided)
            results: List[Dict[str, Any]] = []
            for h in hits:
                if score_threshold is not None and (h.score is None or h.score < score_threshold):
                    continue
                payload = h.payload or {}
                results.append(
                    {
                        "score": round(h.score, 6) if h.score is not None else None,
                        "subject": payload.get("subject"),
                        "topics": payload.get("topics"),
                        "s3_uri": payload.get("s3_uri"),
                        "doc_id": payload.get("doc_id"),
                        "page": payload.get("page"),
                        "chunk_id": payload.get("chunk_id"),
                        "title": payload.get("title"),
                        "text": payload.get("text"),
                        "point_id": getattr(h, "id", None),
                    }
                )

            return results
        except Exception as e:
            self.error_handler.handle(e, context="QdrantStore.search")
            return []

    def _build_filter(
        self,
        *,
        subject: Optional[str],
        topics_any: Optional[List[str]],
        doc_ids_any: Optional[List[str]],
    ) -> Optional[Filter]:
        must: List[Any] = []

        if subject:
            must.append(FieldCondition(key="subject", match=MatchValue(value=subject)))

        if topics_any:
            # MatchAny: at least one of these topics
            must.append(FieldCondition(key="topics", match=MatchAny(any=topics_any)))

        if doc_ids_any:
            must.append(FieldCondition(key="doc_id", match=MatchAny(any=doc_ids_any)))

        return Filter(must=must) if must else None

    # ----------------------- Maintenance -----------------------

    async def delete_by_doc(self, doc_id: str) -> int:
        """
        Delete all points that belong to a given doc_id.
        Returns the number of points deleted (best-effort: based on Qdrant response).
        """
        try:
            res = await self.client.delete(
                collection_name=self.collection_name,
                points_selector=Filter(
                    must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
                ),
            )
            # Qdrant's delete returns an operation result; not always a count—log success
            self.logger.info(f"Delete by doc_id='{doc_id}' acknowledged: {res.status}")
            return 0
        except Exception as e:
            self.error_handler.handle(e, context="QdrantStore.delete_by_doc")
            return 0

    async def count(self, subject: Optional[str] = None) -> int:
        """
        Count points in the collection (optionally filtered by subject).
        """
        try:
            flt = self._build_filter(subject=subject, topics_any=None, doc_ids_any=None)
            res = await self.client.count(collection_name=self.collection_name, count_filter=flt, exact=True)
            return int(getattr(res, "count", 0))
        except Exception as e:
            self.error_handler.handle(e, context="QdrantStore.count")
            return 0

    async def close(self):
        try:
            await self.client.close()
        except Exception as e:
            self.logger.debug(f"Qdrant client close error: {e}")
