from langchain_huggingface import HuggingFaceEmbeddings
from rag_pipeline.config import rag_settings
import logging
import os

logger = logging.getLogger(__name__)

_embedding_model: HuggingFaceEmbeddings | None = None


def get_embedding_model() -> HuggingFaceEmbeddings:
    """Singleton -- loads the embedding model once and reuses it from local cache."""
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading embedding model: {rag_settings.embedding_model}")

        # Check if the model is already cached locally
        cache_dir = os.path.join(
            os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface")),
            "hub",
        )
        model_slug = rag_settings.embedding_model.replace("/", "--")
        is_cached = any(
            entry.startswith(f"models--{model_slug}")
            for entry in os.listdir(cache_dir)
        ) if os.path.isdir(cache_dir) else False

        model_kwargs = {"device": "cpu"}
        if is_cached:
            model_kwargs["local_files_only"] = True
            logger.info("Using locally cached embedding model (no network calls).")

        _embedding_model = HuggingFaceEmbeddings(
            model_name=rag_settings.embedding_model,
            model_kwargs=model_kwargs,
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info("Embedding model loaded successfully.")
    return _embedding_model

