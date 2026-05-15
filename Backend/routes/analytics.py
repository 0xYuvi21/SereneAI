from fastapi import APIRouter, Depends
from Backend.core.security import get_current_user
from Backend.schemas.analytics import EmotionTrendsResponse, DropoutRiskResponse, RecoveryRateResponse
from Backend.services import analytics_service

router = APIRouter()

@router.get("/emotion-trends/{user_id}", response_model=EmotionTrendsResponse)
async def get_emotion_trends(user_id: str, current_user: str = Depends(get_current_user)):
    return await analytics_service.get_emotion_trends(user_id)

@router.get("/dropout-risk/{user_id}", response_model=DropoutRiskResponse)
async def get_dropout_risk(user_id: str, current_user: str = Depends(get_current_user)):
    return await analytics_service.get_dropout_risk(user_id)

@router.get("/recovery-rate/{user_id}", response_model=RecoveryRateResponse)
async def get_recovery_rate(user_id: str, current_user: str = Depends(get_current_user)):
    return await analytics_service.get_recovery_rate(user_id)

@router.get("/anxiety-trends/{user_id}")
async def get_anxiety_trends(user_id: str, current_user: str = Depends(get_current_user)):
    return await analytics_service.get_anxiety_trends(user_id)
