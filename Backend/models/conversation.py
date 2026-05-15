from datetime import datetime, timezone
import uuid

def new_conversation_doc(session_id: str, user_id: str, user_input: str, bot_response: str, sentiment_score: float = 0.0, response_time: float = 0.0):
    return {
        "conversation_id": str(uuid.uuid4()),
        "session_id": session_id,
        "user_id": user_id,
        "timestamp": datetime.now(timezone.utc),
        "user_input": user_input,
        "bot_response": bot_response,
        "sentiment_score": sentiment_score,
        "response_time": response_time
    }
