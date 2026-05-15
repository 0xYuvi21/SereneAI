from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from Backend.core.security import get_current_user
from Backend.services.pipeline.extractors import (
    ImageEmotionExtractor,
    TextEmotionExtractor,
    UserInputExtractor,
)
from Backend.services.pipeline.aggregators import SystemPromptAggregator
from Backend.services.pipeline.responder import AgentResponder
from Backend.services.pipeline.orchestrator import ChatPipeline

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    sentiment: Optional[str] = "neutral"
    dropout_risk: Optional[bool] = False
    image: Optional[str] = None
    # user_id is injected server-side from JWT — not accepted from the client
    user_id: Optional[str] = None


# Singleton pipeline (responder connects to the long-lived MCP subprocess)
pipeline = ChatPipeline(
    extractors=[
        ImageEmotionExtractor(),
        TextEmotionExtractor(),
        UserInputExtractor(),
    ],
    aggregator=SystemPromptAggregator(),
    responder=AgentResponder(),
)


@router.post("/")
async def chat_endpoint(
    request: ChatRequest,
    current_user: str = Depends(get_current_user),
):
    # Inject the authenticated user_id from JWT into the request object
    request.user_id = current_user

    full_response = await pipeline.execute(request, user_id=current_user)
    return JSONResponse(content={"response": full_response})
