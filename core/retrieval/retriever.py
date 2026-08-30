"""
retriever.py
Principled Hybrid Information Retrieval pipeline:
Dense Search (BGE-base) + Lexical Search (BM25) -> Reciprocal Rank Fusion (RRF) -> Cross-Encoder Reranker.
Zero hardcoded word lists or manual domain rules.
"""

from langchain_core.documents import Document
from langchain_chroma import Chroma
from core.retrieval.vector_store import get_vector_store
from core.retrieval.bm25 import get_bm25_retriever
from core.retrieval.reranker import rerank_documents, get_reranker


def _format_chroma_filter(filter_dict: dict) -> dict:
    """
    Normalizes multi-field filter dictionaries into ChromaDB's required $and format.
    """
    if not filter_dict:
        return None
    if len(filter_dict) > 1 and not any(k.startswith("$") for k in filter_dict):
        return {"$and": [{k: v} for k, v in filter_dict.items()]}
    return filter_dict


def retrieve_relevant_chunks(
    query: str,
    vector_store: Chroma = None,
    top_k: int = 20,
    filter_dict: dict = None,
) -> list[Document]:
    """
    Dense semantic retrieval using BGE embeddings.
    """
    if vector_store is None:
        vector_store = get_vector_store()

    chroma_filter = _format_chroma_filter(filter_dict)
    if chroma_filter:
        results = vector_store.similarity_search(
            query=query,
            k=top_k,
            filter=chroma_filter,
        )
    else:
        results = vector_store.similarity_search(
            query=query,
            k=top_k,
        )

    return results


def retrieve_with_scores(
    query: str,
    vector_store: Chroma = None,
    top_k: int = 5,
    filter_dict: dict = None,
) -> list[tuple[Document, float]]:
    """
    Single-stage dense similarity search returning (Document, distance_score).
    """
    if vector_store is None:
        vector_store = get_vector_store()

    chroma_filter = _format_chroma_filter(filter_dict)
    if chroma_filter:
        results = vector_store.similarity_search_with_score(
            query=query,
            k=top_k,
            filter=chroma_filter,
        )
    else:
        results = vector_store.similarity_search_with_score(
            query=query,
            k=top_k,
        )

    return results


def retrieve_bm25(
    query: str,
    top_k: int = 20,
    filter_dict: dict = None,
) -> list[Document]:
    """
    Statistical lexical retrieval using BM25Okapi.
    """
    bm25 = get_bm25_retriever()
    return bm25.retrieve(query=query, top_k=top_k, filter_dict=filter_dict)


def reciprocal_rank_fusion(
    ranked_lists: list[list[Document]],
    rrf_k: int = 60,
    top_k: int = 20,
) -> list[Document]:
    """
    Combines multiple ranked candidate lists using standard Reciprocal Rank Fusion:
    RRF(d) = sum(1.0 / (rrf_k + rank(d)))
    """
    scores = {}
    doc_map = {}

    for ranked_list in ranked_lists:
        for rank, doc in enumerate(ranked_list, start=1):
            chunk_id = doc.metadata.get("chunk_id", doc.page_content[:50])
            doc_map[chunk_id] = doc
            scores[chunk_id] = scores.get(chunk_id, 0.0) + (1.0 / (rrf_k + rank))

    sorted_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)
    return [doc_map[cid] for cid in sorted_ids[:top_k]]


def retrieve_hybrid_reranked(
    query: str,
    vector_store: Chroma = None,
    dense_k: int = 20,
    bm25_k: int = 20,
    rrf_k: int = 60,
    final_k: int = 5,
    filter_dict: dict = None,
) -> list[tuple[Document, float]]:
    """
    Principled Hybrid Two-Stage Retrieval Stack:
    1. Dense BGE Search (Top dense_k)
    2. BM25 Lexical Search (Top bm25_k)
    3. Reciprocal Rank Fusion (Top 20 candidates)
    4. Neural Cross-Encoder Reranking (Final Top final_k)
    """
    if vector_store is None:
        vector_store = get_vector_store()

    # Stage 1: Parallel First-Stage Candidate Generation
    dense_candidates = retrieve_relevant_chunks(
        query=query,
        vector_store=vector_store,
        top_k=dense_k,
        filter_dict=filter_dict,
    )
    bm25_candidates = retrieve_bm25(
        query=query,
        top_k=bm25_k,
        filter_dict=filter_dict,
    )

    # Stage 2: RRF Fusion
    fused_candidates = reciprocal_rank_fusion(
        ranked_lists=[dense_candidates, bm25_candidates],
        rrf_k=rrf_k,
        top_k=dense_k,
    )

    # Stage 3: Cross-Encoder Reranking
    reranked_results = rerank_documents(
        query=query,
        documents=fused_candidates,
        top_k=final_k,
    )

    return reranked_results


def retrieve_with_diagnostics(
    query: str,
    vector_store: Chroma = None,
    dense_k: int = 20,
    bm25_k: int = 20,
    rrf_k: int = 60,
    final_k: int = 5,
    filter_dict: dict = None,
) -> dict:
    """
    Runs hybrid retrieval and returns all intermediate pipeline stages for benchmarking.
    """
    if vector_store is None:
        vector_store = get_vector_store()

    # Stage 1: Dense
    dense_candidates = retrieve_relevant_chunks(
        query=query,
        vector_store=vector_store,
        top_k=dense_k,
        filter_dict=filter_dict,
    )

    # Stage 2: BM25
    bm25_candidates = retrieve_bm25(
        query=query,
        top_k=bm25_k,
        filter_dict=filter_dict,
    )

    # Stage 3: RRF Fusion
    fused_candidates = reciprocal_rank_fusion(
        ranked_lists=[dense_candidates, bm25_candidates],
        rrf_k=rrf_k,
        top_k=dense_k,
    )

    # Stage 4: Cross-Encoder Reranking
    reranked = rerank_documents(
        query=query,
        documents=fused_candidates,
        top_k=final_k,
    )

    return {
        "query": query,
        "dense_candidates": dense_candidates,
        "bm25_candidates": bm25_candidates,
        "fused_candidates": fused_candidates,
        "reranked_results": reranked,
    }