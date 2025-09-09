from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.core.auth import get_current_user, get_current_teacher_or_admin
from app.models.auth import User
from app.models.ingestion import IngestionRequest, IngestionJob
from app.services.ingestion_service import IngestionService
from app.core.database import get_database

router = APIRouter()

@router.post("/subjects/{subject_slug}/ingestions", response_model=IngestionJob, status_code=status.HTTP_202_ACCEPTED, tags=["Ingestion"])
async def start_ingestion(
    subject_slug: str,
    ingestion_request: IngestionRequest,
    current_user: User = Depends(get_current_teacher_or_admin),
    db=Depends(get_database)
):
    """Start an ingestion job for this subject"""
    ingestion_service = IngestionService(db)
    return await ingestion_service.start_ingestion(subject_slug, ingestion_request, current_user)

@router.get("/subjects/{subject_slug}/ingestions", response_model=List[IngestionJob], tags=["Ingestion"])
async def list_ingestions(
    subject_slug: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """List ingestion jobs for subject"""
    ingestion_service = IngestionService(db)
    return await ingestion_service.get_ingestions_for_subject(subject_slug, current_user)

@router.get("/ingestions/{job_id}", response_model=IngestionJob, tags=["Ingestion"])
async def get_ingestion_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """Get ingestion job status"""
    ingestion_service = IngestionService(db)
    job = await ingestion_service.get_ingestion_job(job_id, current_user)
    if not job:
        raise HTTPException(status_code=404, detail="Ingestion job not found")
    return job

@router.post("/ingestions/{job_id}/cancel", status_code=status.HTTP_202_ACCEPTED, tags=["Ingestion"])
async def cancel_ingestion(
    job_id: str,
    current_user: User = Depends(get_current_teacher_or_admin),
    db=Depends(get_database)
):
    """Cancel ingestion job (best effort)"""
    ingestion_service = IngestionService(db)
    success = await ingestion_service.cancel_ingestion(job_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Ingestion job not found")
    return {"message": "Cancel requested"}
