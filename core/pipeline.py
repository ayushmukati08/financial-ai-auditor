"""
pipeline.py
End-to-End Financial AI Auditor Pipeline.
Orchestrates:
1. Extraction -> Chunking -> ChromaDB Vector Store
2. Hybrid Retrieval (Dense + BM25 -> RRF Fusion -> Cross-Encoder Reranker)
3. Citation-Forced Financial Auditor Answer Generation with Gemini
"""

from core.config import DOCS_PATH, CHROMA_DB_PATH, DEFAULT_TOP_K
from core.pdf.parser import extract_documents
from core.chunking.preprocessor import preprocess_pages
from core.chunking.service import build_sections
from core.chunking.chunk_builder import build_chunks
from core.retrieval.vector_store import get_vector_store, add_chunks_to_vector_store
from core.retrieval.retriever import retrieve_hybrid_reranked
from core.llm.service import generate_audited_response


class FinancialAIAuditorPipeline:
    """
    Main entry point for the Financial AI Auditor system.
    """

    def __init__(
        self,
        docs_path: str = DOCS_PATH,
        db_path: str = CHROMA_DB_PATH,
    ):
        self.docs_path = docs_path
        self.db_path = db_path
        self.vector_store = get_vector_store(persist_directory=self.db_path)

    def ingest_documents(self, force_reload: bool = False) -> dict:
        """
        Runs the full extraction, sectioning, chunking, and indexing flow.
        """
        # Step 1: Extract PDF content
        pages = extract_documents(self.docs_path)

        # Step 2: Preprocess margins & wrapped spans
        pages = preprocess_pages(pages)

        # Step 3: Detect sections
        sections = build_sections(pages)

        # Step 4: Build text and table chunks
        chunks = build_chunks(sections)

        # Step 5: Index into ChromaDB
        self.vector_store = add_chunks_to_vector_store(
            chunks, vector_store=self.vector_store
        )

        return {
            "total_pages": len(pages),
            "total_sections": len(sections),
            "total_chunks": len(chunks),
            "text_chunks": sum(1 for c in chunks if c.get("chunk_type") == "text"),
            "table_chunks": sum(1 for c in chunks if c.get("chunk_type") == "table"),
        }

    def ask(
        self,
        question: str,
        top_k: int = DEFAULT_TOP_K,
        filter_dict: dict = None,
    ) -> dict:
        """
        Retrieves relevant evidence using Hybrid Search (Dense + BM25 -> RRF -> Cross-Encoder)
        and generates a cited financial audit response.
        """
        # Step 1: Hybrid Two-Stage Retrieval
        results = retrieve_hybrid_reranked(
            query=question,
            vector_store=self.vector_store,
            dense_k=20,
            bm25_k=20,
            rrf_k=60,
            final_k=top_k,
            filter_dict=filter_dict,
        )

        # Step 2: Format evidence metadata
        evidence = []
        for i, (doc, score) in enumerate(results, 1):
            meta = doc.metadata
            chunk_type = meta.get("chunk_type", "text").upper()
            doc_name = meta.get("document_name", "unknown")
            section = meta.get("section", "N/A")
            start_p = meta.get("start_page", 1)
            end_p = meta.get("end_page", 1)
            chunk_id = meta.get("chunk_id", f"chunk_{i}")

            page_str = f"Page {start_p}" if start_p == end_p else f"Pages {start_p}-{end_p}"

            evidence.append({
                "citation_id": f"[C{i}]",
                "chunk_id": chunk_id,
                "chunk_type": chunk_type,
                "document_name": doc_name,
                "section": section,
                "page": page_str,
                "rerank_score": float(score),
                "content": doc.page_content,
            })

        # Step 3: Generate cited answer via LLM service
        answer, prompt = generate_audited_response(question, evidence)

        return {
            "query": question,
            "answer": answer,
            "evidence": evidence,
            "prompt": prompt,
        }
