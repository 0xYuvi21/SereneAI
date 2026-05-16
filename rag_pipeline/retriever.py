from typing import List, Optional
from rag_pipeline.schemas import RetrievalQuery, RetrievalResult
from rag_pipeline.vector_store import vector_store_manager
import logging

logger = logging.getLogger(__name__)


class MemoryRetriever:
    """Performs metadata-filtered semantic search over a user's memory collection."""

    def _build_where_filter(self, query: RetrievalQuery) -> Optional[dict]:
        """
        Build a ChromaDB `where` clause from optional metadata filters.
        Multiple conditions are ANDed together.
        """
        conditions = []

        if query.filter_memory_type:
            conditions.append({"memory_type": {"$eq": query.filter_memory_type}})
        if query.filter_emotion:
            conditions.append({"emotion": {"$eq": query.filter_emotion}})

        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}

    def retrieve(self, query: RetrievalQuery) -> List[RetrievalResult]:
        """
        Retrieve top-k semantically similar memories, optionally pre-filtered
        by metadata. Results below min_score are discarded.
        """
        vector_store = vector_store_manager.get_vector_store(query.user_id)
        where_filter = self._build_where_filter(query)

        # similarity_search_with_relevance_scores returns (Document, score)
        # where score is usually 0-1 (relevance score)
        docs_with_scores = vector_store.similarity_search_with_relevance_scores(
            query.query,
            k=query.top_k,
            filter=where_filter,
        )

        results: List[RetrievalResult] = []
        for doc, score in docs_with_scores:
            if score >= query.min_score:
                results.append(
                    RetrievalResult(
                        content=doc.page_content,
                        memory_type=doc.metadata.get("memory_type", "unknown"),
                        emotion=doc.metadata.get("emotion") or None,
                        timestamp=doc.metadata.get("timestamp", ""),
                        score=round(float(score), 4),
                        source=doc.metadata.get("source", "chat"),
                    )
                )

        logger.info(
            f"[Retriever] user={query.user_id} | query='{query.query[:50]}' "
            f"-> {len(results)} memories returned"
        )
        return results


# Module-level singleton
memory_retriever = MemoryRetriever()
