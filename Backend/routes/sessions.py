from fastapi import APIRouter, Depends, HTTPException
from Backend.core.security import get_current_user
from Backend.schemas.session import SessionStart, SessionEnd, SessionResponse, SessionDetailResponse
from Backend.services import session_service
from Backend.database.connection import get_database

router = APIRouter()


@router.post("/start", response_model=SessionResponse)
async def start_session(session_data: SessionStart, current_user: str = Depends(get_current_user)):
    return await session_service.start_session(current_user, session_data.emotion_at_start)


@router.put("/{session_id}/end")
async def end_session(
    session_id: str,
    session_data: SessionEnd,
    current_user: str = Depends(get_current_user)
):
    return await session_service.end_session(
        session_id, current_user, session_data.emotion_at_end, session_data.session_quality_score
    )


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: str, current_user: str = Depends(get_current_user)):
    """Return full session details for a given session_id UUID."""
    db = get_database()
    session = await db.sessions.find_one({"session_id": session_id, "user_id": current_user})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session["session_id"],
        "user_id": session["user_id"],
        "session_date": session["session_date"],
        "session_start_time": session["session_start_time"],
        "session_end_time": session.get("session_end_time"),
        "session_duration": session.get("session_duration"),
        "messages_sent_count": session.get("messages_sent_count", 0),
        "emotion_at_start": session.get("emotion_at_start"),
        "emotion_at_end": session.get("emotion_at_end"),
        "days_since_last_session": session.get("days_since_last_session"),
        "session_quality_score": session.get("session_quality_score"),
        "dropout_risk_score": session.get("dropout_risk_score"),
        "is_active": session.get("is_active", False),
    }
