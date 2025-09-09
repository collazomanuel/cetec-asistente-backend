from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

class Citation(BaseModel):
    title: str
    url: str
    score: float
    doc_id: Optional[str] = None

class Conversation(BaseModel):
    id: str
    title: Optional[str] = None
    subject_hint: Optional[str] = None
    created_at: datetime

class MessageCreate(BaseModel):
    role: MessageRole = MessageRole.USER
    content: str
    subject_hint: Optional[str] = None

class Message(BaseModel):
    id: str
    conversation_id: str
    role: MessageRole
    content: str
    routed_to: Optional[str] = None  # A2A server id
    subject: Optional[str] = None
    citations: List[Citation] = []
    created_at: datetime

class SSEChunk(BaseModel):
    delta: Optional[str] = None  # Partial text token(s)
    finish: bool = False
    routed_to: Optional[str] = None
    subject: Optional[str] = None
    citations: List[Citation] = []
    message_id: Optional[str] = None
