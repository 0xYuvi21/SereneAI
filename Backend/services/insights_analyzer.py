import logging
import json
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from Backend.schemas.prompts import SystemPrompt
from Backend.core.config import settings

logger = logging.getLogger(__name__)

async def generate_dashboard_insights(user_id: str, db) -> None:
    """
    Fetches the user's dashboard summary, passes it to the Insight Agent via ChatGroq,
    and stores the resulting personalized markdown insight into the user's document.
    """
    try:
        from Backend.services.analytics_service import get_dashboard_summary
        
        summary_data = await get_dashboard_summary(user_id)
        
        # Exclude latest_insights if it happens to be included, so we don't feed it back recursively.
        summary_dict = dict(summary_data)
        if "latest_insights" in summary_dict:
            del summary_dict["latest_insights"]
            
        summary_json = json.dumps(summary_dict, indent=2)

        system_prompt = SystemPrompt.Insight_Agent_System_Prompt
        
        llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.7, api_key=settings.groq_api_key)
        
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User's Analytics Data:\n{summary_json}")
        ])
        
        generated_insight = response.content.strip()

        # Persist the generated insight back to the user's document
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {"latest_insights": generated_insight}}
        )
        logger.info(f"Successfully generated and stored dashboard insights for user {user_id}")

    except Exception as e:
        logger.error(f"Error generating insights for user {user_id}: {e}")
