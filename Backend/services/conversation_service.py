from fastapi import HTTPException
from Backend.database.connection import get_database
from Backend.database.redis_connection import get_redis
import json
import uuid
from datetime import datetime, timezone

# Lazy import to avoid circular dependency
async def _increment_message_count(user_id: str):
    from Backend.services.user_service import increment_user_counters
    await increment_user_counters(user_id, messages=1)

async def create_conversation(session_id: str, user_id: str, user_input: str, bot_response: str, sentiment_score: float = 0.0, response_time: float = 0.0):
    db = get_database()
    
    msg_id = str(uuid.uuid4())
    msg = {
        "message_id": msg_id,
        "timestamp": datetime.now(timezone.utc),
        "user_input": user_input,
        "bot_response": bot_response,
        "sentiment_score": sentiment_score,
        "response_time": response_time
    }
    
    await db.conversations.update_one(
        {"session_id": session_id},
        {
            "$setOnInsert": {"session_id": session_id, "user_id": user_id},
            "$push": {"messages": msg}
        },
        upsert=True
    )
    
    redis = get_redis()
    history_key = f"chat_history:{session_id}"
    cache_msg = {
        "user": user_input,
        "bot": bot_response
    }
    await redis.rpush(history_key, json.dumps(cache_msg))
    await redis.expire(history_key, 3600) # 1 hour

    await _increment_message_count(user_id)

    # Flip session.is_active to True once the engagement threshold (7 messages) is reached
    doc = await db.conversations.find_one({"session_id": session_id}, {"messages": 1})
    msg_count = len(doc.get("messages", [])) if doc else 0
    if msg_count >= 7:
        await db.sessions.update_one(
            {"session_id": session_id, "is_active": False},
            {"$set": {"is_active": True}}
        )

    return {"conversation_id": msg_id}

async def get_conversations_by_session(session_id: str):
    db = get_database()
    doc = await db.conversations.find_one({"session_id": session_id})
    if not doc:
        return []
    
    messages = doc.get("messages", [])
    
    conversations = []
    for m in messages:
        conversations.append({
            "conversation_id": m.get("message_id", ""),
            "session_id": session_id,
            "user_input": m.get("user_input", ""),
            "bot_response": m.get("bot_response", "")
        })
    return conversations
