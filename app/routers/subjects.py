from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.core.auth import get_current_user, get_current_teacher_or_admin, get_current_admin
from app.models.auth import User
from app.models.subjects import Subject, SubjectCreate, SubjectUpdate
from app.services.subject_service import SubjectService
from app.core.database import get_database

router = APIRouter()

# POSTMAN: create-subject (OK)
@router.post("/subjects", response_model=Subject, status_code=status.HTTP_201_CREATED, tags=["Subjects"])
async def create_subject(
    subject_data: SubjectCreate,
    current_user: User = Depends(get_current_teacher_or_admin),
    db=Depends(get_database)
):
    """Create subject (admin/teacher)"""
    subject_service = SubjectService(db)
    return await subject_service.create_subject(subject_data, current_user)

# POSTMAN: get-subjects (OK)
@router.get("/subjects", response_model=List[Subject], tags=["Subjects"])
async def list_subjects(
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """List subjects visible to caller"""
    subject_service = SubjectService(db)
    return await subject_service.get_subjects_for_user(current_user)

# POSTMAN: get-subject (OK)
@router.get("/subjects/{subject_slug}", response_model=Subject, tags=["Subjects"])
async def get_subject(
    subject_slug: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_database)
):
    """Get subject details"""
    subject_service = SubjectService(db)
    subject = await subject_service.get_subject_by_slug(subject_slug, current_user)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject

# POSTMAN: delete-subject (OK)
@router.delete("/subjects/{subject_slug}", status_code=status.HTTP_204_NO_CONTENT, tags=["Subjects"])
async def delete_subject(
    subject_slug: str,
    current_user: User = Depends(get_current_admin),
    db=Depends(get_database)
):
    """Delete subject (admin)"""
    subject_service = SubjectService(db)
    success = await subject_service.delete_subject(subject_slug, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Subject not found")

# NOTE: Untested endpoint
# Can be added if we choose to display metadata for the subject in the Frontend
@router.patch("/subjects/{subject_slug}", response_model=Subject, tags=["Subjects"])
async def update_subject(
    subject_slug: str,
    subject_update: SubjectUpdate,
    current_user: User = Depends(get_current_teacher_or_admin),
    db=Depends(get_database)
):
    """Update subject (admin/teacher)"""
    subject_service = SubjectService(db)
    subject = await subject_service.update_subject(subject_slug, subject_update, current_user)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject

