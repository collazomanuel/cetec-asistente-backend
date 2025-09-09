from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from typing import List, Optional
from app.core.auth import get_current_user
from app.models.auth import User
from app.models.chat import Conversation, MessageCreate, Message
from app.services.chat_service import ChatService
from app.core.database import get_database

router = APIRouter()

@router.post("/conversations", response_model=Conversation, status_code=status.HTTP_201_CREATED, tags=["Chat"])
async def create_conversation(
    subject_hint: Optional[str] = None,
    title: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """Create a new conversation"""
    chat_service = ChatService(db)
    return await chat_service.create_conversation(current_user, subject_hint, title)

@router.get("/conversations", response_model=List[Conversation], tags=["Chat"])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """List my conversations"""
    chat_service = ChatService(db)
    return await chat_service.get_conversations_for_user(current_user)

@router.get("/conversations/{conversation_id}", response_model=Conversation, tags=["Chat"])
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """Get conversation"""
    chat_service = ChatService(db)
    conversation = await chat_service.get_conversation(conversation_id, current_user)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Chat"])
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """Delete conversation"""
    chat_service = ChatService(db)
    success = await chat_service.delete_conversation(conversation_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")

@router.post("/conversations/{conversation_id}/messages", response_model=Message, status_code=status.HTTP_201_CREATED, tags=["Chat"])
async def send_message(
    conversation_id: str,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """Send a message (non-streaming)"""
    chat_service = ChatService(db)
    return await chat_service.send_message(conversation_id, message_data, current_user)

@router.get("/conversations/{conversation_id}/messages", response_model=List[Message], tags=["Chat"])
async def list_messages(
    conversation_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """List messages (history)"""
    chat_service = ChatService(db)
    return await chat_service.get_messages(conversation_id, current_user, page, page_size)

@router.post("/conversations/{conversation_id}/messages/stream", tags=["Chat"])
async def send_message_stream(
    conversation_id: str,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """Send a message and stream the assistant response (SSE)"""
    chat_service = ChatService(db)
    
    async def generate_stream():
        async for chunk in chat_service.send_message_stream(conversation_id, message_data, current_user):
            yield f"data: {chunk.json()}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
