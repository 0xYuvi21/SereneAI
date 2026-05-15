from pydantic import BaseModel
from typing import Optional

class ConversationCreate(BaseModel):
    session_id: str
    user_input: str
    bot_response: str
    sentiment_score: Optional[float] = 0.0
    response_time: Optional[float] = 0.0

class ConversationResponse(BaseModel):
    conversation_id: str
    session_id: str
    user_input: str
    bot_response: str
