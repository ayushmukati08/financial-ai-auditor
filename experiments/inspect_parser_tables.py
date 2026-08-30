"""
Inspect Parser Table Metadata Test Script

Runs extract_documents() directly and prints:
1. Total number of detected tables across the document corpus.
2. Extracted metadata and sample data for the first 60 tables.
"""

from core.config import DOCS_PATH
from core.pdf.parser import extract_documents


def inspect_parser_tables(limit: int = 60):
    print("=" * 90)
    print("PARSER TABLE METADATA EXTRACTION AUDIT")
    print("=" * 90)
    print(f"Loading documents from: {DOCS_PATH}...\n")

    pages = extract_documents(DOCS_PATH)

    # Collect all tables across all pages
    all_tables = []
    for page in pages:
        doc_name = page.get("document_name", "unknown")
        page_num = page.get("page_number", 0)
        for t in page.get("tables", []):
            all_tables.append({
                "document_name": doc_name,
                "page_number": page_num,
                "bbox": t.get("bbox"),
                "metadata": t.get("metadata", []),
                "data": t.get("data", []),
            })

    total_tables = len(all_tables)
    print(f"TOTAL TABLES DETECTED ACROSS ALL DOCUMENTS: {total_tables}")
    print(f"DISPLAYING FIRST {min(limit, total_tables)} TABLES:\n")
    print("=" * 90)

    for idx, table in enumerate(all_tables[:limit], start=1):
        doc = table["document_name"]
        page = table["page_number"]
        meta = table["metadata"]
        raw_data = table["data"]
        num_rows = len(raw_data)
        num_cols = len(raw_data[0]) if raw_data else 0

        print(f"\n[TABLE {idx:02d} / {total_tables}] | DOC: {doc} | PAGE: {page}")
        print(f"  Shape in PDF : {num_rows} rows x {num_cols} cols")
        print(f"  Header Count : {len(meta)}")
        print(f"  Extracted Metadata:")
        if meta:
            for m_idx, col_name in enumerate(meta, start=1):
                print(f"    [{m_idx}] {col_name}")
        else:
            print("    (No metadata extracted / standalone table)")

        # Preview first data row
        if raw_data:
            first_row_cleaned = [
                str(c).replace("\n", " ").strip() if c is not None else ""
                for c in raw_data[0]
            ]
            print(f"  First Row Sample : {first_row_cleaned}")

        print("-" * 90)


if __name__ == "__main__":
    inspect_parser_tables(limit=60)