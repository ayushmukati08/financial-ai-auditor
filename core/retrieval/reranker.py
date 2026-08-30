"""
reranker.py
Neural Cross-Encoder reranking for candidate documents using cross-encoder/ms-marco-MiniLM-L-6-v2.
Pure deep learning cross-attention scoring. Zero hardcoded dictionaries.
"""

from langchain_core.documents import Document
from sentence_transformers import CrossEncoder
from core.config import DEFAULT_RERANKER_MODEL

_reranker_instance = None


def get_reranker(model_name: str = DEFAULT_RERANKER_MODEL) -> CrossEncoder:
    """
    Returns a singleton CrossEncoder instance.
    """
    global _reranker_instance
    if _reranker_instance is None:
        _reranker_instance = CrossEncoder(model_name)
    return _reranker_instance


def rerank_documents(
    query: str,
    documents: list[Document],
    reranker: CrossEncoder = None,
    top_k: int = 5,
) -> list[tuple[Document, float]]:
    """
    Scores and ranks candidate Documents against the query using a neural Cross-Encoder.
    Returns list of (Document, score) sorted descending by relevance score.
    """
    if not documents:
        return []

    if reranker is None:
        reranker = get_reranker()

    pairs = [(query, doc.page_content) for doc in documents]
    scores = reranker.predict(pairs)

    doc_scores = list(zip(documents, [float(s) for s in scores]))
    doc_scores.sort(key=lambda x: x[1], reverse=True)

    return doc_scores[:top_k]
