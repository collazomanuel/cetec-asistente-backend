# src/agentic_rag/ingestion/embedder.py
from transformers import AutoTokenizer, AutoModel
import torch
from typing import List
from app.utils.logger import Logger
from app.utils.error_handler import ErrorHandler

class Embedder:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.logger = Logger()
        self.error_handler = ErrorHandler(self.logger)
        try:
            self.embedding_size = 384  # Dimension for all-MiniLM-L6-v2
            self.logger.debug(f"Loading embedding model: {model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            self.model.to(self.device)
            self.logger.info(f"Loaded embedding model: {model_name}")
        except Exception as e:
            self.error_handler.handle(e, context="Embedder.__init__")

    def generate(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        self.logger.debug(f"Generating embeddings for {len(texts)} texts with batch size {batch_size}")
        embeddings = []
        try:
            for i in range(0, len(texts), batch_size):
                self.logger.debug(f"Processing batch {i // batch_size + 1}")
                batch = texts[i:i+batch_size]
                inputs = self.tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=512)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                with torch.no_grad():
                    outputs = self.model(**inputs)
                batch_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
                embeddings.extend(batch_embeddings)
            self.logger.info(f"Generated embeddings for {len(texts)} texts.")
        except Exception as e:
            self.error_handler.handle(e, context="Embedder.generate")
        return embeddings

