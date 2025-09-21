from typing import List, Optional
from uuid import uuid4
from datetime import datetime
import boto3
from botocore.config import Config
from fastapi import UploadFile
from fastapi import HTTPException
from app.models.auth import User
from app.models.documents import (
    Document, DocumentsResponse, UploadRequest, UploadPresignResponse,
    UploadCompleteRequest, DocumentStatus, UploadInfo
)
from app.core.config import settings

class DocumentService:
    def __init__(self, db):
        self.db = db
        self.collection = db["documents"]
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_KEY,
            region_name=settings.AWS_REGION,
            config=Config(signature_version='s3v4')
        )

    async def get_documents(
        self,
        subject_slug: str,
        user: User,
        status_filter: Optional[DocumentStatus] = None,
        page: int = 1,
        page_size: int = 25
    ) -> DocumentsResponse:
        """Get documents for a subject with pagination"""
        query = {"subject_slug": subject_slug}
        if status_filter:
            query["status"] = status_filter.value

        # Count total documents
        total = await self.collection.count_documents(query)
        
        # Get paginated documents
        skip = (page - 1) * page_size
        cursor = self.collection.find(query).skip(skip).limit(page_size).sort("created_at", -1)
        
        documents = []
        async for doc in cursor:
            document = Document(
                id=str(doc["_id"]),
                subject_slug=doc["subject_slug"],
                filename=doc["filename"],
                s3_key=doc["s3_key"],
                mime=doc["mime"],
                size=doc["size"],
                status=DocumentStatus(doc["status"]),
                created_at=doc["created_at"]
            )
            documents.append(document)
        
        return DocumentsResponse(items=documents, total=total)

    async def create_presigned_uploads(
        self,
        subject_slug: str,
        upload_request: UploadRequest,
        user: User
    ) -> UploadPresignResponse:
        """Create presigned URLs for S3 uploads"""
        uploads = []
        
        for file_info in upload_request.files:
            doc_id = str(uuid4())
            s3_key = f"{subject_slug}/{doc_id}_{file_info.filename}"
            
            # Generate presigned POST
            presigned_post = self.s3_client.generate_presigned_post(
                Bucket=settings.S3_BUCKET,
                Key=s3_key,
                Fields={
                    "Content-Type": file_info.mime,
                    "Content-Length": str(file_info.size)
                },
                Conditions=[
                    ["content-length-range", file_info.size, file_info.size],
                    {"Content-Type": file_info.mime}
                ],
                ExpiresIn=3600  # 1 hour
            )
            
            upload_info = UploadInfo(
                doc_id=doc_id,
                s3_key=s3_key,
                url=presigned_post["url"],
                fields=presigned_post["fields"]
            )
            uploads.append(upload_info)
            
            # Create document record with uploaded status
            doc_record = {
                "_id": doc_id,
                "subject_slug": subject_slug,
                "filename": file_info.filename,
                "s3_key": s3_key,
                "mime": file_info.mime,
                "size": file_info.size,
                "status": DocumentStatus.UPLOADED.value,
                "created_at": datetime.utcnow(),
                "created_by": user.id
            }
            await self.collection.insert_one(doc_record)
        
        return UploadPresignResponse(uploads=uploads)

    async def complete_uploads(
        self,
        subject_slug: str,
        complete_request: UploadCompleteRequest,
        user: User
    ) -> List[str]:
        """Mark uploads as completed"""
        # In a real implementation, you might verify the files exist in S3
        # and update their status accordingly
        
        result = await self.collection.update_many(
            {
                "_id": {"$in": complete_request.doc_ids},
                "subject_slug": subject_slug
            },
            {"$set": {"status": DocumentStatus.UPLOADED.value}}
        )
        
        return complete_request.doc_ids

    async def get_document(
        self,
        subject_slug: str,
        doc_id: str,
        user: User
    ) -> Optional[Document]:
        """Get a specific document"""
        doc = await self.collection.find_one({
            "_id": doc_id,
            "subject_slug": subject_slug
        })
        
        if not doc:
            return None
            
        return Document(
            id=str(doc["_id"]),
            subject_slug=doc["subject_slug"],
            filename=doc["filename"],
            s3_key=doc["s3_key"],
            mime=doc["mime"],
            size=doc["size"],
            status=DocumentStatus(doc["status"]),
            created_at=doc["created_at"]
        )

    async def delete_document(
        self,
        subject_slug: str,
        doc_id: str,
        user: User
    ) -> bool:
        """Delete document from database and S3"""
        # Get document first to get S3 key
        doc = await self.collection.find_one({
            "_id": doc_id,
            "subject_slug": subject_slug
        })
        
        if not doc:
            return False
        
        # Delete from S3
        try:
            self.s3_client.delete_object(
                Bucket=settings.S3_BUCKET,
                Key=doc["s3_key"]
            )
        except Exception:
            # Log error, but continue with database deletion
            pass
        
        # Delete from database
        result = await self.collection.delete_one({
            "_id": doc_id,
            "subject_slug": subject_slug
        })
        
        return result.deleted_count > 0

    async def upload_document_direct(
        self,
        subject_slug: str,
        file: UploadFile,
        user: User
    ) -> Document:
        """Upload file directly to S3 and create document record"""

        # Check if subject exists
        subject = await self.db["subjects"].find_one({"slug": subject_slug})
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")

        # Generate unique document ID and S3 key
        doc_id = str(uuid4())
        s3_key = f"docentes/{subject_slug}/{doc_id}_{file.filename}"
        
        # Upload file to S3
        try:
            self.s3_client.upload_fileobj(
                file.file,
                settings.S3_BUCKET,
                s3_key,
                ExtraArgs={
                    'ContentType': file.content_type or 'application/octet-stream'
                }
            )
        except Exception as e:
            raise Exception(f"Failed to upload file to S3: {str(e)}")
        
        # Create document record in database
        doc_record = {
            "_id": doc_id,
            "subject_slug": subject_slug,
            "filename": file.filename,
            "s3_key": s3_key,
            "mime": file.content_type or 'application/octet-stream',
            "size": file.size or 0,
            "status": DocumentStatus.UPLOADED.value,
            "created_at": datetime.utcnow(),
            "created_by": user.id
        }
        
        try:
            await self.collection.insert_one(doc_record)
        except Exception as e:
            # If database insert fails, try to cleanup S3 object
            try:
                self.s3_client.delete_object(Bucket=settings.S3_BUCKET, Key=s3_key)
            except:
                pass
            raise Exception(f"Failed to save document metadata: {str(e)}")
        
        # Return the created document
        return Document(
            id=doc_id,
            subject_slug=subject_slug,
            filename=file.filename,
            s3_key=s3_key,
            mime=file.content_type or 'application/octet-stream',
            size=file.size or 0,
            status=DocumentStatus.UPLOADED,
            created_at=doc_record["created_at"]
        )
