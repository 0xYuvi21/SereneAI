import logging
from typing import AsyncGenerator

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent

from Backend.services.pipeline.interfaces import ILLMResponder
from Backend.services.pipeline.tools import rag_tools
from Backend.core.config import settings

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# AgentResponder — LangGraph ReAct agent with direct RAG tools (no MCP).
# ──────────────────────────────────────────────────────────────────────────────
class AgentResponder(ILLMResponder):
    """
    LangGraph ReAct agent that uses rag_index + rag_retrieve tools
    bound directly in-process via LangChain's @tool decorator.
    """

    def __init__(self) -> None:
        self.llm = ChatGroq(
            model=settings.groq_model,
            api_key=settings.groq_api_key,
            temperature=0.7,
            max_tokens=512,
        )

    async def generate_response(
        self,
        system_prompt: str,
        human_message: str,
        user_id: str,
    ) -> AsyncGenerator[str, None]:
        agent = create_react_agent(
            model=self.llm,
            tools=rag_tools,
            prompt=system_prompt,
        )

        messages = [HumanMessage(content=human_message)]

        # ainvoke() fully resolves the agent (including any tool calls)
        result = await agent.ainvoke({"messages": messages})

        all_msgs = result.get("messages", [])

        # Debug: log every message in the trace so we can inspect the flow
        for i, msg in enumerate(all_msgs):
            logger.debug(
                "Message[%d] type=%s tool_calls=%s content_preview=%.120s",
                i,
                type(msg).__name__,
                getattr(msg, "tool_calls", []),
                str(msg.content)[:120],
            )

        # Extract the last AIMessage that is NOT a tool-call intermediary.
        # Messages that triggered tool calls have `tool_calls` populated —
        # those are intermediate and should be skipped to avoid leaking
        # raw function-call markup into the chat response.
        final_text = ""
        for msg in reversed(all_msgs):
            if isinstance(msg, AIMessage):
                # Skip intermediate messages that triggered tool calls
                if getattr(msg, "tool_calls", None):
                    continue

                content = msg.content

                # Some models return content as a list of content blocks
                if isinstance(content, list):
                    content = "\n".join(
                        part.get("text", "") if isinstance(part, dict) else str(part)
                        for part in content
                    ).strip()

                if isinstance(content, str) and content.strip():
                    final_text = content
                    break

        if not final_text:
            logger.warning("Agent produced no final text response. Messages: %s", all_msgs)
            final_text = "I'm sorry, I wasn't able to formulate a response. Could you try again?"

        logger.info("Agent response (%d chars): %.80s...", len(final_text), final_text)
        yield final_text
