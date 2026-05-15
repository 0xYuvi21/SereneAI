from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum


class MemoryType(str, Enum):
    personal_fact = "personal_fact"
    preference = "preference"
    emotional_state = "emotional_state"
    goal = "goal"
    session_summary = "session_summary"
    user_details = "User's Details"


class MemoryDocument(BaseModel):
    user_id: str
    content: str
    memory_type: MemoryType = MemoryType.personal_fact
    session_id: Optional[str] = None
    emotion: Optional[str] = None
    importance: float = Field(default=1.0, ge=0.0, le=1.0)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    source: str = "chat"


class RetrievalQuery(BaseModel):
    user_id: str
    query: str
    top_k: int = 5
    filter_memory_type: Optional[str] = None
    filter_emotion: Optional[str] = None
    min_score: float = 0.3


class RetrievalResult(BaseModel):
    content: str
    memory_type: str
    emotion: Optional[str] = None
    timestamp: str
    score: float
    source: str
