"""
RAG Memory Tools — Direct LangChain tools (no MCP)
===================================================
Two tools for the ReAct agent to call directly in-process:
  • rag_index     — Store a user memory into the vector DB.
  • rag_retrieve  — Retrieve relevant past memories by semantic similarity.
"""

import json
import logging
from typing import Optional

from langchain_core.tools import tool

from rag_pipeline.indexer import memory_indexer
from rag_pipeline.retriever import memory_retriever
from rag_pipeline.schemas import MemoryDocument, RetrievalQuery

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Tool 1 — rag_index
# ──────────────────────────────────────────────────────────────────────────────
@tool
def rag_index(
    user_id: str,
    content: str,
    memory_type: str = "personal_fact",
    session_id: Optional[str] = None,
    emotion: Optional[str] = None,
) -> str:
    """Store a user memory into the vector database.

    ONLY call this tool when the user's message contains a concrete, memorable fact
    that fits one of these categories:
      - personal_fact: name, age, family, location, job, relationships
      - preference: likes, dislikes, hobbies, favourites
      - goal: aspirations, plans, challenges they want to overcome
      - emotional_state: significant or recurring moods worth tracking
      - session_summary: a brief wrap-up of a completed session

    DO NOT call this tool for:
      - Casual greetings ("hi", "hello", "how are you")
      - Generic questions or chit-chat
      - Messages that don't reveal any new personal information

    Args:
        user_id: Unique user identifier -- ALWAYS use the USER_ID from system context.
        content: The exact text of the memory to store.
        memory_type: Category. One of:
            personal_fact | preference | emotional_state | goal | session_summary
        session_id: Current session ID (optional).
        emotion: Detected emotion at time of memory (optional).

    Returns:
        JSON string with status and doc_id.
    """
    try:
        doc = MemoryDocument(
            user_id=user_id,
            content=content,
            memory_type=memory_type,  # type: ignore[arg-type]
            session_id=session_id,
            emotion=emotion,
            importance=1.0,
            source="chat",
        )
        doc_id = memory_indexer.ingest(doc)
        logger.info(
            "[rag_index] Stored memory | type=%s | user=%s | content='%.80s'",
            memory_type, user_id, content,
        )
        return json.dumps(
            {"status": "success", "doc_id": doc_id, "message": "Memory stored."}
        )
    except Exception as e:
        logger.error(f"rag_index error: {e}")
        return json.dumps({"status": "error", "message": str(e)})


# ──────────────────────────────────────────────────────────────────────────────
# Tool 2 — rag_retrieve
# ──────────────────────────────────────────────────────────────────────────────
@tool
def rag_retrieve(
    user_id: str,
    query: str,
    filter_memory_type: Optional[str] = None,
    filter_emotion: Optional[str] = None,
) -> str:
    """Retrieve relevant past memories for a user using semantic similarity search.

    Call this tool when:
    - When the user ask their personal details.
    - The user's message relates to something they may have mentioned before.
    - You need personal context to give a more tailored, empathetic response.
    - The user asks "do you remember…" or references past conversations.
    - You want to check if this user has stated relevant preferences or goals.

    Memories are pre-filtered by metadata before similarity scoring,
    ensuring only the current user's data is searched.

    Args:
        user_id: Unique user identifier — ALWAYS use the USER_ID from system context.
        query: Search text (usually the user's current message or key topic).
        filter_memory_type: Optional filter. One of:
            personal_fact | preference | emotional_state | goal | session_summary
        filter_emotion: Optional emotion filter (e.g., "happy", "anxious").

    Returns:
        JSON string with list of matching memories and their metadata.
    """
    try:
        q = RetrievalQuery(
            user_id=user_id,
            query=query,
            top_k=5,
            filter_memory_type=filter_memory_type,
            filter_emotion=filter_emotion,
            min_score=0.3,
        )
        results = memory_retriever.retrieve(q)

        if not results:
            logger.info("[rag_retrieve] No memories found for user=%s query='%.60s'", user_id, query)
            return json.dumps(
                {"status": "success", "memories": [], "message": "No relevant memories found."}
            )

        # Log each retrieved chunk
        logger.info("[rag_retrieve] %d chunks retrieved for user=%s query='%.60s'", len(results), user_id, query)
        for i, r in enumerate(results):
            logger.info(
                "  Chunk[%d] score=%.4f type=%s content='%.100s'",
                i, r.score, r.memory_type, r.content,
            )

        return json.dumps(
            {
                "status": "success",
                "count": len(results),
                "memories": [r.model_dump() for r in results],
            }
        )
    except Exception as e:
        logger.error(f"rag_retrieve error: {e}")
        return json.dumps({"status": "error", "message": str(e)})


# ──────────────────────────────────────────────────────────────────────────────
# Convenience list for binding to an agent
# ──────────────────────────────────────────────────────────────────────────────
rag_tools = [rag_index, rag_retrieve]
