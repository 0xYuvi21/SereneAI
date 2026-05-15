"""
MCP Server — SereneAI RAG Memory Tools

Exposes two tools to any MCP-compatible client (e.g., LangGraph agent):
  • rag_index    — Store a user memory into the vector DB.
  • rag_retrieve — Retrieve relevant past memories by semantic similarity.

Run as a standalone stdio process:
    python -m rag_pipeline.mcp_server
"""

import json
import logging
from typing import Optional

from mcp.server.fastmcp import FastMCP

from rag_pipeline.indexer import memory_indexer
from rag_pipeline.retriever import memory_retriever
from rag_pipeline.schemas import MemoryDocument, RetrievalQuery

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("SereneAI RAG Memory Server")


# ──────────────────────────────────────────────────────────────────────────────
# Tool 1 — rag_index
# ──────────────────────────────────────────────────────────────────────────────
@mcp.tool()
def rag_index(
    user_id: str,
    content: str,
    memory_type: str = "personal_fact",
    session_id: Optional[str] = None,
    emotion: Optional[str] = None,
    importance: float | str = 1.0,
    source: str = "chat",
) -> str:
    """
    Store a user memory into the vector database.

    Call this tool whenever the user shares:
    - Personal facts (name, age, location, relationships)
    - Preferences or dislikes
    - Goals or aspirations
    - Emotional states or mood patterns
    - Any fact that would make future responses more personalized.

    Args:
        user_id: Unique user identifier — ALWAYS use the USER_ID from system context.
        content: The exact text of the memory to store.
        memory_type: Category. One of:
            personal_fact | preference | emotional_state | goal | session_summary
        session_id: Current session ID (optional).
        emotion: Detected emotion at time of memory (optional).
        importance: Relevance weight 0.0–1.0 (default 1.0).
        source: Origin of the memory (default "chat").

    Returns:
        JSON string with status and doc_id.
    """
    try:
        # Cast importance to float in case it was sent as a string
        imp = float(importance) if isinstance(importance, str) else importance
        
        doc = MemoryDocument(
            user_id=user_id,
            content=content,
            memory_type=memory_type,  # type: ignore[arg-type]
            session_id=session_id,
            emotion=emotion,
            importance=imp,
            source=source,
        )
        doc_id = memory_indexer.ingest(doc)
        return json.dumps(
            {"status": "success", "doc_id": doc_id, "message": "Memory stored."}
        )
    except Exception as e:
        logger.error(f"rag_index error: {e}")
        return json.dumps({"status": "error", "message": str(e)})


# ──────────────────────────────────────────────────────────────────────────────
# Tool 2 — rag_retrieve
# ──────────────────────────────────────────────────────────────────────────────
@mcp.tool()
def rag_retrieve(
    user_id: str,
    query: str,
    top_k: int | str = 5,
    filter_memory_type: Optional[str] = None,
    filter_emotion: Optional[str] = None,
    min_score: float | str = 0.3,
) -> str:
    """
    Retrieve relevant past memories for a user using semantic similarity search.

    Call this tool when:
    - The user's message relates to something they may have mentioned before.
    - You need personal context to give a more tailored, empathetic response.
    - The user asks "do you remember…" or references past conversations.
    - You want to check if this user has stated relevant preferences or goals.

    Memories are pre-filtered by metadata before similarity scoring,
    ensuring only the current user's data is searched.

    Args:
        user_id: Unique user identifier — ALWAYS use the USER_ID from system context.
        query: Search text (usually the user's current message or key topic).
        top_k: Max number of memories to return (default 5).
        filter_memory_type: Optional filter. One of:
            personal_fact | preference | emotional_state | goal | session_summary
        filter_emotion: Optional emotion filter (e.g., "happy", "anxious").
        min_score: Minimum similarity threshold 0.0–1.0 (default 0.3).

    Returns:
        JSON string with list of matching memories and their metadata.
    """
    try:
        # Cast numeric values in case they were sent as strings
        tk = int(top_k) if isinstance(top_k, str) else top_k
        ms = float(min_score) if isinstance(min_score, str) else min_score

        q = RetrievalQuery(
            user_id=user_id,
            query=query,
            top_k=tk,
            filter_memory_type=filter_memory_type,
            filter_emotion=filter_emotion,
            min_score=ms,
        )
        results = memory_retriever.retrieve(q)

        if not results:
            return json.dumps(
                {"status": "success", "memories": [], "message": "No relevant memories found."}
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
# Entry point
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")
