"""
Embedding generation for chunks and queries using HuggingFace models.
"""

from langchain_huggingface import HuggingFaceEmbeddings
from core.config import DEFAULT_EMBEDDING_MODEL


def get_embedding_model(model_name: str = DEFAULT_EMBEDDING_MODEL) -> HuggingFaceEmbeddings:
    """
    Initializes and returns the HuggingFace embeddings model.
    Uses CPU / GPU automatically based on availability.
    """
    model_kwargs = {"device": "cpu"}
    encode_kwargs = {"normalize_embeddings": True}

    embeddings = HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs,
    )
    return embeddings
