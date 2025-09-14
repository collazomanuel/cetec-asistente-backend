from fastapi import APIRouter, Depends
from app.core.auth import get_current_user
from app.models.auth import User

router = APIRouter()

# NOTE: 'Depends' on FastAPI is a 'dependency injection' system.
# It means for the endpoint to work it needs X
# In this case, it needs the current user, which it gets from app.core.auth.get_current_user
# This means every request to /me calls this function passing its 
# return value as the current_user parameter.
@router.get("/me", tags=["Auth"])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user and roles"""
    return current_user
