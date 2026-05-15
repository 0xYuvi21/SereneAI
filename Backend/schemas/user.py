from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    reason_for_using_app: Optional[str] = ""
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    preferred_language: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserProfileUpdate(BaseModel):
    """Optional fields a user can fill in after registration."""
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    preferred_language: Optional[str] = None
    reason_for_using_app: Optional[str] = None


class UserResponse(BaseModel):
    """Returned on register and /me."""
    user_id: str
    name: str
    email: EmailStr
    reason_for_using_app: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    preferred_language: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_login_date: datetime
    login_streak: int
    total_sessions: int
    total_messages: int
