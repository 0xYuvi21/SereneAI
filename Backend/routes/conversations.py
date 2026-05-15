from fastapi import APIRouter, Depends
from typing import List
from Backend.core.security import get_current_user
from Backend.schemas.conversation import ConversationCreate, ConversationResponse
from Backend.services import conversation_service

router = APIRouter()

@router.post("/")
async def create_conversation(data: ConversationCreate, current_user: str = Depends(get_current_user)):
    return await conversation_service.create_conversation(
        data.session_id, current_user, data.user_input, data.bot_response, data.sentiment_score, data.response_time
    )

@router.get("/{session_id}", response_model=List[ConversationResponse])
async def get_conversations(session_id: str, current_user: str = Depends(get_current_user)):
    return await conversation_service.get_conversations_by_session(session_id)
