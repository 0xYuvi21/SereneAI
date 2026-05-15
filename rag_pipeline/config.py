from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

# Project root is one level above rag_pipeline/
PROJECT_ROOT = Path(__file__).parent.parent


class RAGSettings(BaseSettings):
    chroma_persist_dir: str = str(PROJECT_ROOT / "memory" / "chroma")
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    top_k: int = 5
    similarity_threshold: float = 0.3

    model_config = SettingsConfigDict(env_prefix="RAG_", extra="ignore")


rag_settings = RAGSettings()
