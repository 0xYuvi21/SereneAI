import chromadb
from chromadb.config import Settings as ChromaSettings
from rag_pipeline.config import rag_settings
import logging
import os

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manages per-user ChromaDB collections backed by persistent storage."""

    def __init__(self):
        self._client: chromadb.PersistentClient | None = None
        self._collections: dict[str, chromadb.Collection] = {}

    def _get_client(self) -> chromadb.PersistentClient:
        if self._client is None:
            os.makedirs(rag_settings.chroma_persist_dir, exist_ok=True)
            self._client = chromadb.PersistentClient(
                path=rag_settings.chroma_persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            logger.info(
                f"ChromaDB client initialized at: {rag_settings.chroma_persist_dir}"
            )
        return self._client

    def get_collection(self, user_id: str) -> chromadb.Collection:
        """Get or create the isolated collection for a specific user."""
        # Sanitize collection name — ChromaDB requires [a-zA-Z0-9_-]
        collection_name = f"user_{user_id}".replace("-", "_")

        if collection_name not in self._collections:
            client = self._get_client()
            collection = client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._collections[collection_name] = collection
            logger.info(f"Collection ready: {collection_name}")

        return self._collections[collection_name]

    def list_user_collections(self) -> list[str]:
        client = self._get_client()
        return [col.name for col in client.list_collections()]


# Module-level singleton
vector_store_manager = VectorStoreManager()
