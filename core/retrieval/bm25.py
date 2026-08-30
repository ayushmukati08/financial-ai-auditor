"""
bm25.py
Pure-Python, self-contained implementation of BM25Okapi statistical lexical retrieval.
Requires zero external pip dependencies and works across any environment.
"""

import math
import re
from collections import Counter
from langchain_core.documents import Document
from core.retrieval.vector_store import get_vector_store


def _tokenize(text: str) -> list[str]:
    """
    Standard lowercased tokenization for lexical search.
    """
    return [t.lower() for t in re.findall(r"\b[a-zA-Z0-9$%\-–]+\b", text)]


class BM25Okapi:
    """
    Standard Okapi BM25 implementation (Robertson et al.).
    k1 = 1.5, b = 0.75
    """

    def __init__(self, corpus: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.doc_lengths = [len(doc) for doc in corpus]
        self.avgdl = sum(self.doc_lengths) / max(self.corpus_size, 1)

        # Document frequencies (DF)
        self.df = Counter()
        self.doc_freqs = []
        for doc in corpus:
            term_freq = Counter(doc)
            self.doc_freqs.append(term_freq)
            for term in term_freq:
                self.df[term] += 1

        # Inverse Document Frequencies (IDF)
        self.idf = {}
        for term, freq in self.df.items():
            # Standard Lucene/BM25 IDF formula
            self.idf[term] = math.log(1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def get_scores(self, query: list[str]) -> list[float]:
        """
        Computes BM25 relevance scores for all documents given tokenized query.
        """
        scores = [0.0] * self.corpus_size
        query_counter = Counter(query)

        for term, _ in query_counter.items():
            if term not in self.idf:
                continue
            idf_val = self.idf[term]
            for doc_idx in range(self.corpus_size):
                tf = self.doc_freqs[doc_idx].get(term, 0)
                if tf == 0:
                    continue
                doc_len = self.doc_lengths[doc_idx]
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avgdl))
                scores[doc_idx] += idf_val * (numerator / denominator)

        return scores


class BM25Retriever:
    """
    In-memory BM25 index built directly from the persistent ChromaDB collection.
    """

    def __init__(self, documents: list[Document]):
        self.documents = documents
        self.corpus_tokens = [_tokenize(doc.page_content) for doc in documents]
        self.bm25 = BM25Okapi(self.corpus_tokens)

    def retrieve(
        self,
        query: str,
        top_k: int = 20,
        filter_dict: dict = None,
    ) -> list[Document]:
        """
        Retrieves top_k documents by BM25 score, with optional metadata filtering.
        """
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)

        scored_docs = []
        for doc, score in zip(self.documents, scores):
            if filter_dict:
                match = True
                for k, v in filter_dict.items():
                    if doc.metadata.get(k) != v:
                        match = False
                        break
                if not match:
                    continue
            scored_docs.append((doc, float(score)))

        scored_docs.sort(key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in scored_docs[:top_k]]


_bm25_instance = None


def get_bm25_retriever(vector_store=None, force_reload: bool = False) -> BM25Retriever:
    """
    Singleton factory for the BM25Retriever.
    Loads all documents from ChromaDB once into memory.
    """
    global _bm25_instance
    if _bm25_instance is None or force_reload:
        if vector_store is None:
            vector_store = get_vector_store()

        data = vector_store._collection.get(include=["documents", "metadatas"])
        docs = []
        for content, meta in zip(data["documents"], data["metadatas"]):
            docs.append(Document(page_content=content, metadata=meta))

        _bm25_instance = BM25Retriever(docs)
    return _bm25_instance
