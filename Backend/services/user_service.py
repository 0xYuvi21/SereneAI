from fastapi import HTTPException, status
from Backend.database.connection import get_database
from Backend.models.user import new_user_doc
from Backend.core.security import hash_password, verify_password, create_access_token
from Backend.schemas.user import UserCreate, UserLogin, UserProfileUpdate
from datetime import datetime, timezone
import asyncio
import logging
from rag_pipeline.schemas import MemoryDocument, MemoryType
from rag_pipeline.indexer import memory_indexer

logger = logging.getLogger(__name__)


def _serialize_user(user: dict) -> dict:
    """Convert a MongoDB user document to a serializable dict."""
    return {
        "user_id": user["user_id"],
        "name": user.get("name", ""),
        "email": user["email"],
        "reason_for_using_app": user.get("reason_for_using_app", ""),
        "age": user.get("age"),
        "gender": user.get("gender"),
        "location": user.get("location"),
        "preferred_language": user.get("preferred_language", "en"),
        "is_active": user.get("is_active", True),
        "created_at": user["created_at"],
        "last_login_date": user["last_login_date"],
        "login_streak": user.get("login_streak", 1),
        "total_sessions": user.get("total_sessions", 0),
        "total_messages": user.get("total_messages", 0),
    }


async def register_user(user: UserCreate):
    db = get_database()
    existing_user = await db.users.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(user.password)
    user_doc = new_user_doc(
        name=user.name,
        email=user.email,
        hashed_password=hashed_password,
        reason_for_using_app=user.reason_for_using_app,
        age=user.age,
        gender=user.gender,
        location=user.location,
        preferred_language=user.preferred_language
    )
    await db.users.insert_one(user_doc)

    # Store user profile details in vector DB
    details = []
    if user.name: details.append(f"Name: {user.name}")
    if user.age: details.append(f"Age: {user.age}")
    if user.gender: details.append(f"Gender: {user.gender}")
    if user.location: details.append(f"Location: {user.location}")
    if user.reason_for_using_app: details.append(f"Reason for using the app: {user.reason_for_using_app}")
    if user.preferred_language: details.append(f"Preferred Language: {user.preferred_language}")
    
    if details:
        content = "User's Details: " + ", ".join(details)
        try:
            doc = MemoryDocument(
                user_id=user_doc["user_id"],
                content=content,
                memory_type=MemoryType.user_details,
                source="registration"
            )
            # Run ingestion in a thread so it doesn't block the API response
            asyncio.create_task(asyncio.to_thread(memory_indexer.ingest, doc))
        except Exception as e:
            logger.error(f"Failed to ingest user details to vector DB: {e}")

    return _serialize_user(user_doc)


async def login_user(user: UserLogin):
    db = get_database()
    db_user = await db.users.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    now = datetime.now(timezone.utc)

    # Compute login streak
    last_login = db_user.get("last_login_date")
    streak = db_user.get("login_streak", 1)
    if last_login:
        if last_login.tzinfo is None:
            last_login = last_login.replace(tzinfo=timezone.utc)
        days_gap = (now.date() - last_login.date()).days
        if days_gap == 1:
            streak += 1          # consecutive day → extend streak
        elif days_gap > 1:
            streak = 1           # gap → reset streak
        # days_gap == 0 means same day, keep streak unchanged

    # Determine is_active: False if no session in the last 7 days
    last_session = await db.sessions.find_one(
        {"user_id": db_user["user_id"], "session_end_time": {"$ne": None}},
        sort=[("session_end_time", -1)]
    )
    if last_session and last_session.get("session_end_time"):
        last_session_end = last_session["session_end_time"]
        if last_session_end.tzinfo is None:
            last_session_end = last_session_end.replace(tzinfo=timezone.utc)
        days_since_session = (now - last_session_end).days
        is_active = days_since_session <= 7
    else:
        # No completed sessions at all — judge by account age
        created_at = db_user.get("created_at", now)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        is_active = (now - created_at).days <= 7

    await db.users.update_one(
        {"user_id": db_user["user_id"]},
        {"$set": {"last_login_date": now, "login_streak": streak, "is_active": is_active}}
    )
    db_user["last_login_date"] = now
    db_user["login_streak"] = streak
    db_user["is_active"] = is_active

    # JWT uses user_id UUID string as the subject
    access_token = create_access_token(data={"sub": db_user["user_id"]})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": _serialize_user(db_user)
    }


async def get_user_by_id(user_id: str):
    """Fetch by user_id UUID string (used by get_current_user dependency)."""
    db = get_database()
    user = await db.users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _serialize_user(user)


async def update_user_profile(user_id: str, data: UserProfileUpdate):
    """PATCH endpoint — update only the fields the user provided."""
    db = get_database()
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    result = await db.users.update_one({"user_id": user_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return await get_user_by_id(user_id)


async def increment_user_counters(user_id: str, sessions: int = 0, messages: int = 0):
    """Called by session_service and conversation_service to keep counters in sync."""
    db = get_database()
    inc = {}
    if sessions:
        inc["total_sessions"] = sessions
    if messages:
        inc["total_messages"] = messages
    if inc:
        await db.users.update_one({"user_id": user_id}, {"$inc": inc})
