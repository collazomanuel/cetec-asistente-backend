from typing import List, Optional
from uuid import uuid4
from datetime import datetime
import asyncio
import tempfile
import os
import boto3
from app.models.auth import User
from app.models.ingestion import (
    IngestionRequest, IngestionJob, IngestionStatus, IngestionMode
)
from app.models.documents import DocumentStatus
from app.utils.pdf_handler import PDFHandler
from app.utils.qdrant_client import QdrantStore
from app.utils.logger import Logger
from app.core.config import settings

class IngestionService:
    def __init__(self, db):
        self.db = db
        self.collection = db["ingestion_jobs"]
        self.documents_collection = db["documents"]
        self.logger = Logger()
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_KEY,
            region_name=settings.AWS_REGION
        )
        
        # Initialize PDF handler
        self.pdf_handler = PDFHandler()
        
        # Initialize Qdrant store
        self.qdrant_store = QdrantStore(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            collection_name=settings.QDRANT_COLLECTION_NAME or "academia_docs"
        )

    async def start_ingestion(
        self,
        subject_slug: str,
        ingestion_request: IngestionRequest,
        user: User
    ) -> IngestionJob:
        self.logger.info(f"Starting ingestion for subject: {subject_slug} by user: {user.id}")
        self.logger.debug(f"IngestionRequest: mode={ingestion_request.mode}, doc_ids={ingestion_request.doc_ids}, options={getattr(ingestion_request, 'options', None)}")
        job_id = str(uuid4())
        
        # Count documents to process and provide diagnostic info
        if ingestion_request.mode == IngestionMode.NEW:
            docs_query = {"subject_slug": subject_slug, "status": DocumentStatus.UPLOADED.value}
        elif ingestion_request.mode == IngestionMode.SELECTED and ingestion_request.doc_ids:
            docs_query = {"subject_slug": subject_slug, "status": DocumentStatus.UPLOADED.value, "_id": {"$in": ingestion_request.doc_ids}}
        elif ingestion_request.mode == IngestionMode.ALL:
            docs_query = {"subject_slug": subject_slug, "status": {"$in": [DocumentStatus.UPLOADED.value, DocumentStatus.INGESTED.value]}}
        elif ingestion_request.mode == IngestionMode.REINGEST:
            docs_query = {"subject_slug": subject_slug, "status": DocumentStatus.INGESTED.value}
        else:
            # Default to NEW mode
            docs_query = {"subject_slug": subject_slug, "status": DocumentStatus.UPLOADED.value}
            
        self.logger.debug(f"MongoDB docs_query: {docs_query}")
        docs_total = await self.documents_collection.count_documents(docs_query)
        self.logger.info(f"Total documents to ingest: {docs_total}")
        
        # Log diagnostic information about document statuses
        total_docs = await self.documents_collection.count_documents({"subject_slug": subject_slug})
        uploaded_docs = await self.documents_collection.count_documents({"subject_slug": subject_slug, "status": DocumentStatus.UPLOADED.value})
        ingested_docs = await self.documents_collection.count_documents({"subject_slug": subject_slug, "status": DocumentStatus.INGESTED.value})
        failed_docs = await self.documents_collection.count_documents({"subject_slug": subject_slug, "status": DocumentStatus.FAILED.value})
        
        self.logger.info(f"Subject '{subject_slug}' document status summary: Total={total_docs}, Uploaded={uploaded_docs}, Ingested={ingested_docs}, Failed={failed_docs}")
        
        # Create job record
        job_doc = {
            "_id": job_id,
            "subject_slug": subject_slug,
            "status": IngestionStatus.QUEUED.value,
            "docs_total": docs_total,
            "docs_done": 0,
            "vectors": 0,
            "logs_url": None,
            "created_at": datetime.utcnow(),
            "created_by": user.id,
            "request": ingestion_request.dict()
        }
        self.logger.debug(f"Inserting job record: {job_doc}")
        await self.collection.insert_one(job_doc)
        self.logger.info(f"Ingestion job {job_id} created and queued.")
        
        # Start the actual ingestion process in the background
        self.logger.info(f"Dispatching background ingestion task for job {job_id}...")
        asyncio.create_task(self._process_ingestion(job_id, subject_slug, docs_query))
        
        self.logger.info(f"Ingestion job {job_id} started for subject {subject_slug}.")
        return IngestionJob(
            job_id=job_id,
            subject_slug=subject_slug,
            status=IngestionStatus.QUEUED,
            docs_total=docs_total,
            docs_done=0,
            vectors=0,
            logs_url=None
        )

    async def get_ingestions_for_subject(
        self,
        subject_slug: str,
        user: User
    ) -> List[IngestionJob]:
        """Get ingestion jobs for a subject"""
        self.logger.info(f"Getting ingestion jobs for subject {subject_slug} for user {user.id}")
        cursor = self.collection.find(
            {"subject_slug": subject_slug}
        ).sort("created_at", -1)
        
        jobs = []
        async for doc in cursor:
            self.logger.debug(f"Found job {doc['_id']}: status={doc['status']}, docs_total={doc['docs_total']}")
            job = IngestionJob(
                job_id=str(doc["_id"]),
                subject_slug=doc["subject_slug"],
                status=IngestionStatus(doc["status"]),
                docs_total=doc["docs_total"],
                docs_done=doc["docs_done"],
                vectors=doc["vectors"],
                logs_url=doc.get("logs_url")
            )
            jobs.append(job)
        
        self.logger.info(f"Returning {len(jobs)} jobs for subject {subject_slug}")
        return jobs

    async def get_ingestion_job(
        self,
        job_id: str,
        user: User
    ) -> Optional[IngestionJob]:
        """Get a specific ingestion job"""
        self.logger.info(f"Getting ingestion job {job_id} for user {user.id}")
        doc = await self.collection.find_one({"_id": job_id})
        
        if not doc:
            self.logger.warning(f"Ingestion job {job_id} not found in database")
            return None
        
        self.logger.info(f"Found job {job_id}: status={doc['status']}, docs_total={doc['docs_total']}, docs_done={doc['docs_done']}, vectors={doc['vectors']}")
        
        return IngestionJob(
            job_id=str(doc["_id"]),
            subject_slug=doc["subject_slug"],
            status=IngestionStatus(doc["status"]),
            docs_total=doc["docs_total"],
            docs_done=doc["docs_done"],
            vectors=doc["vectors"],
            logs_url=doc.get("logs_url")
        )

    async def cancel_ingestion(
        self,
        job_id: str,
        user: User
    ) -> bool:
        """Cancel an ingestion job"""
        result = await self.collection.update_one(
            {
                "_id": job_id,
                "status": {"$in": [IngestionStatus.QUEUED.value, IngestionStatus.RUNNING.value]}
            },
            {"$set": {"status": IngestionStatus.CANCELED.value}}
        )
        
        # In a real implementation, you would also signal the worker to stop
        
        return result.modified_count > 0

    async def _process_ingestion(self, job_id: str, subject_slug: str, docs_query: dict):
        self.logger.info(f"[Job {job_id}] Starting background ingestion for subject '{subject_slug}' with query: {docs_query}")
        try:
            # Update job status to running
            self.logger.info(f"[Job {job_id}] Setting status to RUNNING.")
            await self.collection.update_one(
                {"_id": job_id},
                {"$set": {"status": IngestionStatus.RUNNING.value}}
            )
            
            # Initialize Qdrant collection
            self.logger.info(f"[Job {job_id}] Initializing Qdrant collection...")
            await self.qdrant_store.init_store()
            
            # Get all documents to process
            cursor = self.documents_collection.find(docs_query)
            docs_processed = 0
            total_vectors = 0
            
            # Check if there are any documents to process
            has_documents = False
            async for doc in cursor:
                has_documents = True
                try:
                    self.logger.info(f"[Job {job_id}] Processing document {doc['_id']}: {doc['filename']}")
                    
                    # Download PDF from S3
                    self.logger.debug(f"[Job {job_id}] Downloading {doc['s3_key']} from S3...")
                    pdf_content = await self._download_pdf_from_s3(doc['s3_key'])
                    
                    if pdf_content:
                        self.logger.debug(f"[Job {job_id}] PDF downloaded. Extracting text...")
                        # Extract text from PDF
                        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                            temp_file.write(pdf_content)
                            temp_file_path = temp_file.name
                        
                        try:
                            text = self.pdf_handler.read(temp_file_path)
                            self.logger.debug(f"[Job {job_id}] Extracted text length: {len(text)}")
                            
                            if text.strip():
                                # Chunk the text
                                chunks = self.pdf_handler.chunk(text, chunk_size=1000)
                                self.logger.debug(f"[Job {job_id}] Chunked into {len(chunks)} chunks.")
                                
                                # Prepare chunks for Qdrant
                                qdrant_chunks = []
                                for chunk_idx, chunk_text in enumerate(chunks):
                                    if chunk_text.strip():
                                        qdrant_chunks.append({
                                            "text": chunk_text,
                                            "subject": self._map_subject_to_category(subject_slug),
                                            "s3_uri": f"s3://{settings.S3_BUCKET}/{doc['s3_key']}",
                                            "doc_id": doc['_id'],
                                            "page": 1,  # PDF page detection could be improved
                                            "chunk_id": chunk_idx,
                                            "title": doc['filename'],
                                            "topics": []
                                        })
                                self.logger.debug(f"[Job {job_id}] Prepared {len(qdrant_chunks)} Qdrant chunks.")
                                
                                # Upload to Qdrant
                                if qdrant_chunks:
                                    try: 
                                        self.logger.info(f"[Job {job_id}] Uploading {len(qdrant_chunks)} chunks to Qdrant...")
                                        await self.qdrant_store.upsert_chunks(qdrant_chunks)
                                        total_vectors += len(qdrant_chunks)
                                    except Exception as e:
                                        self.logger.error(f"[Job {job_id}] Failed to upload chunks to Qdrant: {str(e)}")
                                        raise                        
                                    # Update document status to ingested
                                    await self.documents_collection.update_one(
                                        {"_id": doc['_id']},
                                        {"$set": {"status": DocumentStatus.INGESTED.value}}
                                    )
                                    self.logger.info(f"[Job {job_id}] Successfully ingested {len(qdrant_chunks)} chunks from {doc['filename']}")
                                else:
                                    self.logger.warning(f"[Job {job_id}] No valid chunks extracted from {doc['filename']}")
                            else:
                                self.logger.warning(f"[Job {job_id}] No text extracted from {doc['filename']}")
                                
                        finally:
                            # Clean up temp file
                            if os.path.exists(temp_file_path):
                                os.unlink(temp_file_path)
                                self.logger.debug(f"[Job {job_id}] Deleted temp file {temp_file_path}")
                    else:
                        self.logger.error(f"[Job {job_id}] Failed to download {doc['s3_key']} from S3")
                        
                    docs_processed += 1
                    
                    # Update job progress
                    self.logger.info(f"[Job {job_id}] Progress: {docs_processed} docs processed, {total_vectors} vectors so far.")
                    await self.collection.update_one(
                        {"_id": job_id},
                        {"$set": {
                            "docs_done": docs_processed,
                            "vectors": total_vectors
                        }}
                    )
                    
                except Exception as e:
                    self.logger.error(f"[Job {job_id}] Error processing document {doc['_id']}: {str(e)}")
                    # Mark document as failed
                    await self.documents_collection.update_one(
                        {"_id": doc['_id']},
                        {"$set": {"status": DocumentStatus.FAILED.value}}
                    )
                    docs_processed += 1
            
            # Handle case where no documents were found
            if not has_documents:
                self.logger.info(f"[Job {job_id}] No documents found matching query. All documents may already be ingested.")
            
            # Update job status to completed
            self.logger.info(f"[Job {job_id}] COMPLETED: {docs_processed} docs, {total_vectors} vectors.")
            await self.collection.update_one(
                {"_id": job_id},
                {"$set": {
                    "status": IngestionStatus.COMPLETED.value,
                    "docs_done": docs_processed,
                    "vectors": total_vectors
                }}
            )
            
        except Exception as e:
            self.logger.error(f"[Job {job_id}] Ingestion job failed: {str(e)}")
            # Update job status to failed
            await self.collection.update_one(
                {"_id": job_id},
                {"$set": {"status": IngestionStatus.FAILED.value}}
            )

    async def _download_pdf_from_s3(self, s3_key: str) -> bytes:
        """Download PDF content from S3"""
        try:
            response = self.s3_client.get_object(Bucket=settings.S3_BUCKET, Key=s3_key)
            return response['Body'].read()
        except Exception as e:
            self.logger.error(f"Failed to download {s3_key} from S3: {str(e)}")
            return None
    
    def _map_subject_to_category(self, subject_slug: str) -> str:
        """Map subject slug to a standard category for Qdrant filtering"""
        # Simple mapping - could be more sophisticated
        slug_lower = subject_slug.lower()
        if 'math' in slug_lower or 'calculo' in slug_lower or 'algebra' in slug_lower:
            return "Math"
        elif 'physic' in slug_lower or 'fisica' in slug_lower:
            return "Physics"
        elif 'quimica' in slug_lower or 'chemistry' in slug_lower:
            return "Chemistry"
        elif 'circuit' in slug_lower or 'electr' in slug_lower:
            return "Physics"  # Electrical circuits -> Physics
        else:
            return "General"
