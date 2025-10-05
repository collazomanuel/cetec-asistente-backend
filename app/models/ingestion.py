from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class IngestionMode(str, Enum):
    NEW = "new"  # Only process documents with 'uploaded' status
    SELECTED = "selected"  # Only process specific document IDs with 'uploaded' status 
    ALL = "all"  # Process all documents regardless of status
    REINGEST = "reingest"  # Re-process already ingested documents

class IngestionOptions(BaseModel):
    chunk_size: int = 1000
    chunk_overlap: int = 150
    embed_model: str = "text-embedding-3-large"
    append: bool = True

class IngestionRequest(BaseModel):
    mode: IngestionMode = IngestionMode.NEW
    doc_ids: Optional[List[str]] = None
    options: Optional[IngestionOptions] = None

class IngestionStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"

class IngestionJob(BaseModel):
    job_id: str
    subject_slug: str
    status: IngestionStatus
    docs_total: int
    docs_done: int
    vectors: int
    logs_url: Optional[str] = None
