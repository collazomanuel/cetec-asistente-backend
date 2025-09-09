from fastapi import APIRouter, Depends
from app.core.auth import get_current_user
from app.models.auth import User

router = APIRouter()

@router.get("/me", tags=["Auth"])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user and roles"""
    return current_user
