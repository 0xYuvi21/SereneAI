import hashlib
from typing import List
from rag_pipeline.schemas import MemoryDocument
from rag_pipeline.vector_store import vector_store_manager
import logging

logger = logging.getLogger(__name__)


class MemoryIndexer:
    """Embeds and stores memory documents into the user's ChromaDB collection."""

    def _generate_doc_id(self, doc: MemoryDocument) -> str:
        """Stable deterministic ID from user_id + content + timestamp."""
        raw = f"{doc.user_id}:{doc.content}:{doc.timestamp}"
        return hashlib.sha256(raw.encode()).hexdigest()[:24]

    def _build_metadata(self, doc: MemoryDocument) -> dict:
        """
        ChromaDB metadata must be flat (str, int, float, bool only).
        Enum values are serialized to their string value.
        """
        return {
            "user_id": doc.user_id,
            "memory_type": (
                doc.memory_type.value
                if hasattr(doc.memory_type, "value")
                else str(doc.memory_type)
            ),
            "session_id": doc.session_id or "",
            "emotion": doc.emotion or "",
            "importance": doc.importance,
            "timestamp": doc.timestamp,
            "source": doc.source,
        }

    def ingest(self, doc: MemoryDocument) -> str:
        """Embed and upsert a memory document. Returns the doc_id."""
        vector_store = vector_store_manager.get_vector_store(doc.user_id)

        doc_id = self._generate_doc_id(doc)
        metadata = self._build_metadata(doc)

        vector_store.add_texts(
            texts=[doc.content],
            metadatas=[metadata],
            ids=[doc_id],
        )
        logger.info(
            f"[Indexer] Stored memory [{metadata['memory_type']}] "
            f"for user={doc.user_id} | doc_id={doc_id}"
        )
        return doc_id

    def ingest_batch(self, docs: List[MemoryDocument]) -> List[str]:
        """Batch ingest multiple memory documents."""
        return [self.ingest(doc) for doc in docs]


# Module-level singleton
memory_indexer = MemoryIndexer()
