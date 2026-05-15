from fastapi import APIRouter, Depends
from Backend.core.security import get_current_user
from Backend.schemas.user import UserCreate, UserLogin, Token, UserResponse, UserProfileUpdate
from Backend.schemas.analytics import DashboardResponse
from Backend.services import user_service, analytics_service

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    return await user_service.register_user(user)


@router.post("/login")
async def login(user: UserLogin):
    return await user_service.login_user(user)


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: str = Depends(get_current_user)):
    return await user_service.get_user_by_id(current_user)


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(current_user: str = Depends(get_current_user)):
    return await analytics_service.get_dashboard_summary(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    data: UserProfileUpdate,
    current_user: str = Depends(get_current_user)
):
    """Update optional profile fields: age, gender, location, preferred_language, reason_for_using_app."""
    return await user_service.update_user_profile(current_user, data)
