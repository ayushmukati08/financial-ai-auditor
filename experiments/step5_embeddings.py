"""
step5_embeddings.py
Generates dense embeddings using BAAI/bge-base-en-v1.5 and ingests all 1,100 chunks
into a persistent ChromaDB vector store with structured metadata.
"""

import time
import os
import shutil
from core.config import DOCS_PATH, CHROMA_DB_PATH, COLLECTION_NAME, DEFAULT_EMBEDDING_MODEL
from core.pdf.parser import extract_documents
from core.chunking.preprocessor import preprocess_pages
from core.chunking.service import build_sections
from core.chunking.chunk_builder import build_chunks
from core.retrieval.embedding import get_embedding_model
from core.retrieval.vector_store import get_vector_store, add_chunks_to_vector_store


def main():
    print("=" * 80)
    print("STEP 5: VECTOR STORE INGESTION (ChromaDB + BGE-base-en-v1.5)")
    print("=" * 80)

    # 1. Pipeline extraction & chunk generation
    t0 = time.time()
    print("\n[1/4] Extracting and chunking documents from:", DOCS_PATH)
    pages = extract_documents(DOCS_PATH)
    pages = preprocess_pages(pages)
    sections = build_sections(pages)
    chunks = build_chunks(sections)
    print(f"      Extracted {len(pages)} pages across {len(sections)} sections.")
    print(f"      Generated {len(chunks)} chunks ({sum(1 for c in chunks if c['chunk_type']=='text')} text, {sum(1 for c in chunks if c['chunk_type']=='table')} table).")
    print(f"      Time taken: {time.time() - t0:.2f}s")

    # 2. Reset existing ChromaDB directory for a clean ingest
    print(f"\n[2/4] Initializing vector store at: {CHROMA_DB_PATH}")
    if os.path.exists(CHROMA_DB_PATH):
        try:
            shutil.rmtree(CHROMA_DB_PATH)
            print("      Cleaned existing ChromaDB persist directory.")
        except Exception as e:
            print(f"      Notice: Could not wipe directory ({e}), overwriting collection.")

    # 3. Load Embedding Model
    print(f"\n[3/4] Loading embedding model: {DEFAULT_EMBEDDING_MODEL}")
    t_embed = time.time()
    embedding_model = get_embedding_model(DEFAULT_EMBEDDING_MODEL)
    print(f"      Embedding model initialized in {time.time() - t_embed:.2f}s")

    # 4. Batch Ingestion into ChromaDB
    print(f"\n[4/4] Ingesting {len(chunks)} chunks into collection '{COLLECTION_NAME}'...")
    t_ingest = time.time()
    vector_store = get_vector_store(
        persist_directory=CHROMA_DB_PATH,
        collection_name=COLLECTION_NAME,
        embedding_model=embedding_model,
    )

    add_chunks_to_vector_store(
        chunks=chunks,
        vector_store=vector_store,
        batch_size=100,
    )

    total_count = vector_store._collection.count()
    ingest_time = time.time() - t_ingest
    total_time = time.time() - t0

    print(f"      Successfully ingested {total_count} documents into ChromaDB.")
    print(f"      Ingestion speed: {total_count / ingest_time:.1f} chunks/sec (Time: {ingest_time:.2f}s)")
    print(f"      Total pipeline runtime: {total_time:.2f}s")

    # Assertions
    assert total_count == len(chunks), f"Mismatch: expected {len(chunks)} in collection, found {total_count}"
    print("\n[PASS]: Vector store integrity verified. Step 5 complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
