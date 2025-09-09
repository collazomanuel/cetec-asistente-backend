from typing import List, Optional, AsyncGenerator
from uuid import uuid4
from datetime import datetime
import httpx
from app.models.auth import User
from app.models.chat import (
    Conversation, MessageCreate, Message, MessageRole, 
    Citation, SSEChunk
)
from app.services.a2a_service import A2AService

class ChatService:
    def __init__(self, db):
        self.db = db
        self.conversations_collection = db["conversations"]
        self.messages_collection = db["messages"]
        self.a2a_service = A2AService(db)

    async def create_conversation(
        self,
        user: User,
        subject_hint: Optional[str] = None,
        title: Optional[str] = None
    ) -> Conversation:
        """Create a new conversation"""
        conversation_id = str(uuid4())
        
        conversation_doc = {
            "_id": conversation_id,
            "title": title,
            "subject_hint": subject_hint,
            "created_at": datetime.utcnow(),
            "user_id": user.id
        }
        
        await self.conversations_collection.insert_one(conversation_doc)
        
        return Conversation(
            id=conversation_id,
            title=title,
            subject_hint=subject_hint,
            created_at=conversation_doc["created_at"]
        )

    async def get_conversations_for_user(self, user: User) -> List[Conversation]:
        """Get conversations for a user"""
        cursor = self.conversations_collection.find(
            {"user_id": user.id}
        ).sort("created_at", -1)
        
        conversations = []
        async for doc in cursor:
            conversation = Conversation(
                id=str(doc["_id"]),
                title=doc.get("title"),
                subject_hint=doc.get("subject_hint"),
                created_at=doc["created_at"]
            )
            conversations.append(conversation)
        
        return conversations

    async def get_conversation(
        self,
        conversation_id: str,
        user: User
    ) -> Optional[Conversation]:
        """Get a specific conversation"""
        doc = await self.conversations_collection.find_one({
            "_id": conversation_id,
            "user_id": user.id
        })
        
        if not doc:
            return None
        
        return Conversation(
            id=str(doc["_id"]),
            title=doc.get("title"),
            subject_hint=doc.get("subject_hint"),
            created_at=doc["created_at"]
        )

    async def delete_conversation(
        self,
        conversation_id: str,
        user: User
    ) -> bool:
        """Delete a conversation and its messages"""
        # Delete messages first
        await self.messages_collection.delete_many({
            "conversation_id": conversation_id
        })
        
        # Delete conversation
        result = await self.conversations_collection.delete_one({
            "_id": conversation_id,
            "user_id": user.id
        })
        
        return result.deleted_count > 0

    async def send_message(
        self,
        conversation_id: str,
        message_data: MessageCreate,
        user: User
    ) -> Message:
        """Send a message and get response"""
        # Verify conversation exists and belongs to user
        conversation = await self.get_conversation(conversation_id, user)
        if not conversation:
            raise ValueError("Conversation not found")
        
        # Save user message
        user_message_id = str(uuid4())
        user_message_doc = {
            "_id": user_message_id,
            "conversation_id": conversation_id,
            "role": MessageRole.USER.value,
            "content": message_data.content,
            "created_at": datetime.utcnow()
        }
        await self.messages_collection.insert_one(user_message_doc)
        
        # Route to A2A server and get response
        server_id, response_content, citations = await self._route_and_process(
            message_data.content,
            message_data.subject_hint or conversation.subject_hint
        )
        
        # Save assistant message
        assistant_message_id = str(uuid4())
        assistant_message_doc = {
            "_id": assistant_message_id,
            "conversation_id": conversation_id,
            "role": MessageRole.ASSISTANT.value,
            "content": response_content,
            "routed_to": server_id,
            "subject": message_data.subject_hint or conversation.subject_hint,
            "citations": [citation.dict() for citation in citations],
            "created_at": datetime.utcnow()
        }
        await self.messages_collection.insert_one(assistant_message_doc)
        
        return Message(
            id=assistant_message_id,
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=response_content,
            routed_to=server_id,
            subject=message_data.subject_hint or conversation.subject_hint,
            citations=citations,
            created_at=assistant_message_doc["created_at"]
        )

    async def get_messages(
        self,
        conversation_id: str,
        user: User,
        page: int = 1,
        page_size: int = 50
    ) -> List[Message]:
        """Get messages for a conversation"""
        # Verify conversation exists and belongs to user
        conversation = await self.get_conversation(conversation_id, user)
        if not conversation:
            return []
        
        skip = (page - 1) * page_size
        cursor = self.messages_collection.find(
            {"conversation_id": conversation_id}
        ).sort("created_at", 1).skip(skip).limit(page_size)
        
        messages = []
        async for doc in cursor:
            citations = [Citation(**citation) for citation in doc.get("citations", [])]
            
            message = Message(
                id=str(doc["_id"]),
                conversation_id=doc["conversation_id"],
                role=MessageRole(doc["role"]),
                content=doc["content"],
                routed_to=doc.get("routed_to"),
                subject=doc.get("subject"),
                citations=citations,
                created_at=doc["created_at"]
            )
            messages.append(message)
        
        return messages

    async def send_message_stream(
        self,
        conversation_id: str,
        message_data: MessageCreate,
        user: User
    ) -> AsyncGenerator[SSEChunk, None]:
        """Send a message and stream the response"""
        # Verify conversation exists and belongs to user
        conversation = await self.get_conversation(conversation_id, user)
        if not conversation:
            raise ValueError("Conversation not found")
        
        # Save user message
        user_message_id = str(uuid4())
        user_message_doc = {
            "_id": user_message_id,
            "conversation_id": conversation_id,
            "role": MessageRole.USER.value,
            "content": message_data.content,
            "created_at": datetime.utcnow()
        }
        await self.messages_collection.insert_one(user_message_doc)
        
        # Stream response from A2A server
        server_id = await self.a2a_service.get_server_for_subject(
            message_data.subject_hint or conversation.subject_hint
        )
        
        full_response = ""
        message_id = str(uuid4())
        
        # Mock streaming response
        # In a real implementation, you would stream from the A2A server
        response_text = f"This is a mock response to: {message_data.content}"
        words = response_text.split()
        
        for i, word in enumerate(words):
            chunk = SSEChunk(
                delta=word + " ",
                finish=False,
                routed_to=server_id,
                subject=message_data.subject_hint or conversation.subject_hint,
                message_id=message_id
            )
            yield chunk
            full_response += word + " "
        
        # Final chunk
        citations = []  # Mock citations
        final_chunk = SSEChunk(
            delta="",
            finish=True,
            routed_to=server_id,
            subject=message_data.subject_hint or conversation.subject_hint,
            citations=citations,
            message_id=message_id
        )
        yield final_chunk
        
        # Save complete assistant message
        assistant_message_doc = {
            "_id": message_id,
            "conversation_id": conversation_id,
            "role": MessageRole.ASSISTANT.value,
            "content": full_response.strip(),
            "routed_to": server_id,
            "subject": message_data.subject_hint or conversation.subject_hint,
            "citations": [citation.dict() for citation in citations],
            "created_at": datetime.utcnow()
        }
        await self.messages_collection.insert_one(assistant_message_doc)

    async def _route_and_process(
        self,
        content: str,
        subject_hint: Optional[str] = None
    ) -> tuple[str, str, List[Citation]]:
        """Route message to appropriate A2A server and process response"""
        server_id = await self.a2a_service.get_server_for_subject(subject_hint)
        
        # Mock response - in a real implementation, you would call the A2A server
        response_content = f"This is a mock response to: {content}"
        citations = []
        
        return server_id, response_content, citations
