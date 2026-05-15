from Backend.services.pipeline.interfaces import IContextAggregator
from Backend.schemas.prompts import SystemPrompt
from typing import Dict, Any

system_prompts = SystemPrompt()


class SystemPromptAggregator(IContextAggregator):
    """
    Builds the system prompt that is passed to the LangGraph agent.
    The raw user message is handled separately as a HumanMessage.
    """

    SYSTEM_PROMPT = system_prompts.SereneAI_System_Prompt

    async def aggregate(self, extractions: Dict[str, Any]) -> str:
        face = extractions.get("face_sentiment", "neutral")
        text = extractions.get("text_sentiment", "neutral")
        risk = extractions.get("dropout_risk", False)
        user_id = extractions.get("user_id", "")

        return self.SYSTEM_PROMPT.format(
            face_sentiment=face,
            text_sentiment=text,
            dropout_risk="High" if risk else "Normal",
            user_id=user_id,
        )
