from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.core.auth import get_current_user, get_current_teacher_or_admin
from app.models.auth import User
from app.models.documents import (
    Document, DocumentsResponse, UploadRequest, UploadPresignResponse, 
    UploadCompleteRequest, DocumentStatus
)
from app.services.document_service import DocumentService
from app.core.database import get_database

router = APIRouter()

@router.get("/subjects/{subject_slug}/documents", response_model=DocumentsResponse, tags=["Documents"])
async def list_documents(
    subject_slug: str,
    status_filter: Optional[DocumentStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """List documents for subject (with ingest status)"""
    document_service = DocumentService(db)
    return await document_service.get_documents(
        subject_slug, current_user, status_filter, page, page_size
    )

@router.post("/subjects/{subject_slug}/uploads/presign", response_model=UploadPresignResponse, tags=["Documents"])
async def presign_uploads(
    subject_slug: str,
    upload_request: UploadRequest,
    current_user: User = Depends(get_current_teacher_or_admin),
    db=Depends(get_database)
):
    """Get S3 presigned URLs for direct upload"""
    document_service = DocumentService(db)
    return await document_service.create_presigned_uploads(subject_slug, upload_request, current_user)

@router.post("/subjects/{subject_slug}/uploads/complete", status_code=status.HTTP_202_ACCEPTED, tags=["Documents"])
async def complete_uploads(
    subject_slug: str,
    complete_request: UploadCompleteRequest,
    current_user: User = Depends(get_current_teacher_or_admin),
    db=Depends(get_database)
):
    """Confirm completed uploads (persist metadata)"""
    document_service = DocumentService(db)
    doc_ids = await document_service.complete_uploads(subject_slug, complete_request, current_user)
    return {"doc_ids": doc_ids}

@router.get("/subjects/{subject_slug}/documents/{doc_id}", response_model=Document, tags=["Documents"])
async def get_document(
    subject_slug: str,
    doc_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """Get document metadata"""
    document_service = DocumentService(db)
    document = await document_service.get_document(subject_slug, doc_id, current_user)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document

@router.delete("/subjects/{subject_slug}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Documents"])
async def delete_document(
    subject_slug: str,
    doc_id: str,
    current_user: User = Depends(get_current_teacher_or_admin),
    db=Depends(get_database)
):
    """Delete document from S3 and purge vectors"""
    document_service = DocumentService(db)
    success = await document_service.delete_document(subject_slug, doc_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
