from datetime import datetime, timezone
import uuid


def new_user_doc(name: str, email: str, hashed_password: str, reason_for_using_app: str = "", age: int = None, gender: str = None, location: str = None, preferred_language: str = None):
    now = datetime.now(timezone.utc)
    return {
        "user_id": str(uuid.uuid4()),
        "name": name,
        "email": email,
        "hashed_password": hashed_password,
        "created_at": now,
        "last_login_date": now,
        "login_streak": 1,
        "reason_for_using_app": reason_for_using_app,
        # Optional profile fields
        "age": age,
        "gender": gender,
        "location": location,
        "preferred_language": preferred_language or "en",
        "is_active": True,
        # Derived counters -- incremented by services
        "total_sessions": 0,
        "total_messages": 0,
    }
