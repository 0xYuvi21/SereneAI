from pydantic import BaseModel
from typing import List, Optional, Dict


# ── Emotion Trends ────────────────────────────────────────────────
class EmotionTrend(BaseModel):
    date: str           # "YYYY-MM-DD"
    score: int          # 0-100 wellbeing score
    session_date: str   # same as date, kept for frontend compat
    emotion_at_start: Optional[str] = None
    emotion_at_end: Optional[str] = None


class EmotionTrendsResponse(BaseModel):
    trends: List[EmotionTrend]


# ── Dropout Risk ──────────────────────────────────────────────────
class DropoutRiskResponse(BaseModel):
    risk_score: str              # "Low" | "Medium" | "High"
    dropout_risk_probability: float


# ── Recovery Rate ─────────────────────────────────────────────────
class RecoveryRateResponse(BaseModel):
    rate: float                  # 0-100 percentage
    status: str                  # "Improving" | "Stable" | "Declining" | "Insufficient Data"
    sessions_analysed: int
    positive_sessions: int


# ── Dashboard Summary ─────────────────────────────────────────────
class DashboardResponse(BaseModel):
    total_sessions: int
    total_messages: int
    best_session_duration: Optional[float] = None   # seconds
    best_session_date: Optional[str] = None         # "YYYY-MM-DD"
    avg_session_duration: Optional[float] = None    # seconds
    login_streak: int
    emotion_distribution: Dict[str, int]            # {"happy": 3, "sad": 1, ...}
    active_sessions: int                            # sessions with is_active=True (7+ msgs)
    days_since_last_session: Optional[int] = None
    latest_insights: Optional[str] = None
