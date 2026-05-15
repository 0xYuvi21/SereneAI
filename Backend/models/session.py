from datetime import datetime, timezone
import uuid


def new_session_doc(user_id: str, emotion_at_start: str = "neutral"):
    now = datetime.now(timezone.utc)
    return {
        "session_id": str(uuid.uuid4()),
        "user_id": user_id,
        "session_date": now.strftime("%Y-%m-%d"),
        "session_start_time": now,
        "session_end_time": None,
        "session_duration": None,
        "messages_sent_count": 0,
        "emotion_at_start": emotion_at_start,
        "emotion_at_end": None,
        "days_since_last_session": None,
        "session_quality_score": None,
        "dropout_risk_score": None,
        "is_active": False,  # flips True once the user sends 7+ messages
    }
