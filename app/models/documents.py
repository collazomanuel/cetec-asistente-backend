from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    INGESTED = "ingested"
    FAILED = "failed"

class Document(BaseModel):
    id: str
    subject_slug: str
    filename: str
    s3_key: str
    mime: str
    size: int
    status: DocumentStatus
    created_at: datetime

class UploadFile(BaseModel):
    filename: str
    mime: str
    size: int

class UploadRequest(BaseModel):
    files: List[UploadFile]

class UploadInfo(BaseModel):
    doc_id: str
    s3_key: str
    url: str
    fields: Dict[str, Any]

class UploadPresignResponse(BaseModel):
    uploads: List[UploadInfo]

class UploadCompleteRequest(BaseModel):
    doc_ids: List[str]

class DocumentsResponse(BaseModel):
    items: List[Document]
    total: int
