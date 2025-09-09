from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class IngestionMode(str, Enum):
    NEW = "new"
    SELECTED = "selected"

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
    SUCCEEDED = "succeeded"
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
