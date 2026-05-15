from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SessionStart(BaseModel):
    emotion_at_start: str = "neutral"


class SessionEnd(BaseModel):
    emotion_at_end: Optional[str] = None
    session_quality_score: Optional[int] = None


class SessionResponse(BaseModel):
    session_id: str  # returns the UUID string, not the ObjectId


class SessionDetailResponse(BaseModel):
    session_id: str
    user_id: str
    session_date: str
    session_start_time: datetime
    session_end_time: Optional[datetime] = None
    session_duration: Optional[float] = None
    messages_sent_count: int
    emotion_at_start: Optional[str] = None
    emotion_at_end: Optional[str] = None
    days_since_last_session: Optional[int] = None
    session_quality_score: Optional[int] = None
    dropout_risk_score: Optional[float] = None
    is_active: bool
