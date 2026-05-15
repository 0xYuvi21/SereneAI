from fastapi import HTTPException
from Backend.database.connection import get_database
from Backend.database.redis_connection import get_redis
from Backend.models.session import new_session_doc
from Backend.services.dropout_predictor import predict_dropout_risk
from Backend.services.anxiety_analyzer import analyze_session_anxiety
from Backend.services.insights_analyzer import generate_dashboard_insights
from datetime import datetime, timezone
import json

# Lazy import to avoid circular dependency
async def _increment_user_counters(user_id: str, sessions: int = 0, messages: int = 0):
    from Backend.services.user_service import increment_user_counters
    await increment_user_counters(user_id, sessions=sessions, messages=messages)


async def start_session(user_id: str, emotion_at_start: str = "neutral"):
    db = get_database()

    # Compute days since last session
    last_session = await db.sessions.find_one(
        {"user_id": user_id, "session_end_time": {"$ne": None}},
        sort=[("session_start_time", -1)]
    )
    days_since_last = None
    if last_session and last_session.get("session_start_time"):
        delta = datetime.now(timezone.utc) - last_session["session_start_time"].replace(tzinfo=timezone.utc)
        days_since_last = delta.days

    doc = new_session_doc(user_id, emotion_at_start)
    doc["days_since_last_session"] = days_since_last

    await db.sessions.insert_one(doc)
    await _increment_user_counters(user_id, sessions=1)

    # User is engaging again — ensure they are marked active
    await db.users.update_one({"user_id": user_id}, {"$set": {"is_active": True}})

    return {"session_id": doc["session_id"]}  # return UUID string, not ObjectId


async def end_session(
    session_id: str,
    user_id: str,
    emotion_at_end: str = None,
    session_quality_score: int = None
):
    db = get_database()

    # Look up by session_id UUID field (not _id)
    session = await db.sessions.find_one({"session_id": session_id, "user_id": user_id})
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    end_time = datetime.now(timezone.utc)
    start_time = session["session_start_time"]
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    duration = (end_time - start_time).total_seconds()

    conv_doc = await db.conversations.find_one({"session_id": session_id}, {"messages": 1})
    msg_count = len(conv_doc.get("messages", [])) if conv_doc else 0

    # Persist core session-end fields first so the predictor sees complete data
    update_data = {
        "session_end_time": end_time,
        "session_duration": duration,
        "emotion_at_end": emotion_at_end,
        "messages_sent_count": msg_count,
        "session_quality_score": session_quality_score,
        # is_active is NOT reset here — it reflects engagement (7+ messages sent)
    }
    await db.sessions.update_one({"session_id": session_id}, {"$set": update_data})

    # Build an up-to-date in-memory session dict for the predictor
    updated_session = {**session, **update_data}

    # Run the neural-network dropout risk prediction
    risk_probability, risk_label = await predict_dropout_risk(updated_session, user_id, db)

    # Run the anxiety scale analysis
    anxiety_scores = await analyze_session_anxiety(session_id, db)

    # Persist the predicted scores back to the session document
    await db.sessions.update_one(
        {"session_id": session_id},
        {"$set": {
            "dropout_risk_score": risk_probability,
            "ras_score": anxiety_scores["ras_score"],
            "tas_score": anxiety_scores["tas_score"]
        }}
    )

    redis = get_redis()
    await redis.delete(f"chat_history:{session_id}")

    # Generate new AI insights based on the updated dashboard stats
    await generate_dashboard_insights(user_id, db)

    return {
        "message": "Session ended successfully",
        "duration": duration,
        "messages": msg_count,
        "dropout_risk_score": risk_probability,
        "dropout_risk_label": risk_label,
    }
