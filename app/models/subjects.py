from pydantic import BaseModel
from typing import Optional

class Subject(BaseModel):
    id: str
    name: str
    slug: str
    s3_bucket: str
    s3_prefix: str
    vector_collection: str
    a2a_server_id: str

class SubjectCreate(BaseModel):
    name: str
    slug: str
    s3_bucket: str
    s3_prefix: str
    vector_collection: str
    a2a_server_id: str

class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    s3_bucket: Optional[str] = None
    s3_prefix: Optional[str] = None
    vector_collection: Optional[str] = None
    a2a_server_id: Optional[str] = None
