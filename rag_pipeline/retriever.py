from typing import List, Optional
from rag_pipeline.schemas import RetrievalQuery, RetrievalResult
from rag_pipeline.embeddings import get_embedding_model
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
        embedding_model = get_embedding_model()
        collection = vector_store_manager.get_collection(query.user_id)

        if collection.count() == 0:
            logger.info(f"[Retriever] No memories yet for user={query.user_id}")
            return []

        query_embedding = embedding_model.embed_query(query.query)
        where_filter = self._build_where_filter(query)

        n_results = min(query.top_k, collection.count())
        kwargs: dict = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where_filter:
            kwargs["where"] = where_filter

        raw = collection.query(**kwargs)

        results: List[RetrievalResult] = []
        for doc, meta, dist in zip(
            raw["documents"][0],
            raw["metadatas"][0],
            raw["distances"][0],
        ):
            # ChromaDB cosine distance ∈ [0, 2]; convert to similarity ∈ [0, 1]
            score = round(1.0 - (dist / 2.0), 4)
            if score >= query.min_score:
                results.append(
                    RetrievalResult(
                        content=doc,
                        memory_type=meta.get("memory_type", "unknown"),
                        emotion=meta.get("emotion") or None,
                        timestamp=meta.get("timestamp", ""),
                        score=score,
                        source=meta.get("source", "chat"),
                    )
                )

        logger.info(
            f"[Retriever] user={query.user_id} | query='{query.query[:50]}' "
            f"-> {len(results)} memories returned"
        )
        return results


# Module-level singleton
memory_retriever = MemoryRetriever()
