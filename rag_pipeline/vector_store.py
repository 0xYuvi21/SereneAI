import chromadb
from typing import Optional
from langchain_chroma import Chroma
from rag_pipeline.config import rag_settings
from rag_pipeline.embeddings import get_embedding_model
import logging
import os

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages per-user LangChain Chroma instances sharing a single client."""

    def __init__(self):
        self._client: Optional[chromadb.PersistentClient] = None
        self._stores: dict[str, Chroma] = {}

    def _get_client(self) -> chromadb.PersistentClient:
        if self._client is None:
            os.makedirs(rag_settings.chroma_persist_dir, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=rag_settings.chroma_persist_dir,
                settings=chromadb.Settings(anonymized_telemetry=False),
            )
            logger.info(f"Chroma PersistentClient initialized at: {rag_settings.chroma_persist_dir}")
        return self._client

    def get_vector_store(self, user_id: str) -> Chroma:
        """Get or create the LangChain Chroma instance for a specific user."""
        # Sanitize collection name — ChromaDB requires [a-zA-Z0-9_-]
        collection_name = f"user_{user_id}".replace("-", "_")

        if collection_name not in self._stores:
            store = Chroma(
                client=self._get_client(),
                collection_name=collection_name,
                embedding_function=get_embedding_model(),
                collection_metadata={"hnsw:space": "cosine"}
            )
            self._stores[collection_name] = store
            logger.info(f"LangChain Chroma store ready: {collection_name}")

        return self._stores[collection_name]


# Module-level singleton
vector_store_manager = VectorStoreManager()
