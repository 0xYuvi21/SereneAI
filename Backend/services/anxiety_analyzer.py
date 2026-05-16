import json
import logging
import os
from typing import Dict
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from Backend.core.config import settings

logger = logging.getLogger(__name__)


class AnxietyScores(BaseModel):
    ras_score: float = Field(description="Reactive Anxiety Scale (RAS) score, from 1.0 to 4.0")
    tas_score: float = Field(description="Trait Anxiety Scale (TAS) score, from 1.0 to 4.0")

async def analyze_session_anxiety(session_id: str, db) -> Dict[str, float]:
    """
    Analyzes the conversation history of a session and computes RAS and TAS anxiety scores
    using ChatGroq and the rules defined in anxiety-scales.json.
    """
    try:
        # 1. Fetch conversation history
        conv_doc = await db.conversations.find_one({"session_id": session_id})
        if not conv_doc or not conv_doc.get("messages"):
            logger.info(f"No messages found for session {session_id}. Skipping anxiety analysis.")
            return {"ras_score": 0.0, "tas_score": 0.0}

        messages = conv_doc["messages"]
        transcript = "\n".join([f"User: {m.get('user_input', '')}\nBot: {m.get('bot_response', '')}" for m in messages])

        # 2. Load Anxiety Scales
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) # Root dir
        scales_path = os.path.join(base_dir, "anxiety-scales.json")
        
        with open(scales_path, "r") as f:
            scales = json.load(f)

        # 3. Prompt the LLM
        system_prompt = (
            "You are an expert psychological analyzer. Your task is to evaluate a user's conversation transcript "
            "and determine their average Reactive Anxiety Scale (RAS) and Trait Anxiety Scale (TAS) scores based on the provided scales.\n\n"
            f"Here are the scale items for reference (each statement has a weight):\n{json.dumps(scales, indent=2)}\n\n"
            "Based on the user's messages, evaluate their expressions against these statements to compute an "
            "overall average score for RAS (1.0 to 4.0) and TAS (1.0 to 4.0). "
            "If there is insufficient data to calculate a reliable score, provide a default of 2.0."
        )

        # Using ChatGroq as requested by the user
        llm = ChatGroq(model=settings.groq_model, temperature=0.0, api_key=settings.groq_api_key)
        structured_llm = llm.with_structured_output(AnxietyScores)

        response = structured_llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Transcript:\n{transcript}")
        ])

        return {
            "ras_score": round(response.ras_score, 2),
            "tas_score": round(response.tas_score, 2)
        }
    except Exception as e:
        logger.error(f"Error analyzing anxiety for session {session_id}: {e}")
        return {"ras_score": 0.0, "tas_score": 0.0}
