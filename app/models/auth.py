from pydantic import BaseModel, EmailStr
from typing import List, Optional
from enum import Enum

class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"

class User(BaseModel):
    id: str
    email: EmailStr
    roles: List[UserRole]

class UserInDB(User):
    hashed_password: str
