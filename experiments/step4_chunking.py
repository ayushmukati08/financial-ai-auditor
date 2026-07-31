"""
step4_chunking.py
Exploratory / throwaway script for this step.
Once the logic works here, promote a clean version into core/.
"""
from core.pdf.parser import extract_documents
from core.chunking.service import build_sections
from core.chunking.chunk_builder import build_chunks

DOCS_PATH = "docs"


def main():
    # Step 1: Parse PDFs
    pages = extract_documents(DOCS_PATH)

    # Step 2: Build sections (includes header detection)
    sections = build_sections(pages)

    # Step 3: Build chunks
    chunks = build_chunks(sections)

    print("=" * 70)
    print("CHUNKING SUMMARY")
    print("=" * 70)

    print(f"Total Sections: {len(sections)}")
    print(f"Total Chunks  : {len(chunks)}\n")

    for chunk in chunks[:10]:
        print("=" * 70)
        print(f"Chunk ID : {chunk['chunk_id']}")
        print(f"Document : {chunk['document_name']}")
        print(f"Section  : {chunk['section']}")
        print(f"Pages    : {chunk['start_page']} - {chunk['end_page']}")
        print("-" * 70)
        print(chunk["text"][:300])
        print()


if __name__ == "__main__":
    main()