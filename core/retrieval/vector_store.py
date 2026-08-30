"""
Vector database management using ChromaDB.
"""

import os
from langchain_core.documents import Document
from langchain_chroma import Chroma
from core.retrieval.embedding import get_embedding_model
from core.config import CHROMA_DB_PATH, COLLECTION_NAME


def get_vector_store(
    persist_directory: str = CHROMA_DB_PATH,
    collection_name: str = COLLECTION_NAME,
    embedding_model=None,
) -> Chroma:
    """
    Returns an instance of the persistent Chroma vector store.
    """
    if embedding_model is None:
        embedding_model = get_embedding_model()

    os.makedirs(persist_directory, exist_ok=True)

    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=embedding_model,
        persist_directory=persist_directory,
    )
    return vector_store


def add_chunks_to_vector_store(
    chunks: list[dict],
    vector_store: Chroma = None,
    batch_size: int = 100,
) -> Chroma:
    """
    Converts chunk dictionaries to LangChain Documents and inserts them into ChromaDB.
    """
    if vector_store is None:
        vector_store = get_vector_store()

    documents = []
    ids = []

    for chunk in chunks:
        doc_metadata = {
            "chunk_id": str(chunk.get("chunk_id", "")),
            "chunk_type": chunk.get("chunk_type", "text"),
            "section": chunk.get("section_title", chunk.get("section", "")),
            "document_name": chunk.get("document_name", ""),
            "start_page": chunk.get("start_page", 1),
            "end_page": chunk.get("end_page", 1),
        }

        if "table_metadata" in chunk and chunk["table_metadata"]:
            doc_metadata["table_metadata"] = " | ".join(chunk["table_metadata"])

        doc_content = chunk.get("content", chunk.get("text", ""))
        doc = Document(
            page_content=doc_content,
            metadata=doc_metadata,
        )
        documents.append(doc)
        ids.append(str(chunk.get("chunk_id", f"{chunk.get('document_name', 'doc')}_{len(documents)}")))

    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i : i + batch_size]
        batch_ids = ids[i : i + batch_size]
        vector_store.add_documents(documents=batch_docs, ids=batch_ids)

    return vector_store