# """
# step4_chunking.py
# Comprehensive test suite and audit for structure-aware chunking.
# Tests:
# 1. Structural integrity and schema consistency.
# 2. Exact sequence preservation (Text 1 -> Table -> Text 2).
# 3. Dual-format table validation (Markdown content + raw 2D grid).
# 4. Real-world financial table inspection (Apple & Tesla).
# """

# from core.config import DOCS_PATH
# from core.pdf.parser import extract_documents
# from core.chunking.preprocessor import preprocess_pages
# from core.chunking.service import build_sections
# from core.chunking.chunk_builder import build_chunks


# def main():
#     print("=" * 80)
#     print("STRUCTURE-AWARE CHUNK BUILDER AUDIT SUITE")
#     print("=" * 80)

#     # 1. Extraction & Chunk Building
#     print("\n[1/3] Extracting, Preprocessing & Building Chunks...")
#     pages = extract_documents(DOCS_PATH)
#     pages = preprocess_pages(pages)
#     sections = build_sections(pages)
#     chunks = build_chunks(sections)

#     text_chunks = [c for c in chunks if c.get("chunk_type") == "text"]
#     table_chunks = [c for c in chunks if c.get("chunk_type") == "table"]

#     print(f"      Total Sections : {len(sections)}")
#     print(f"      Total Chunks   : {len(chunks)} ({len(text_chunks)} text, {len(table_chunks)} table)")

#     # 2. Automated Structural Assertions
#     print("\n[2/3] Running Structural Integrity Assertions...")

#     # A. Chunk ID Uniqueness
#     chunk_ids = [c["chunk_id"] for c in chunks]
#     assert len(chunk_ids) == len(set(chunk_ids)), "Assertion Failed: Chunk IDs are not unique!"
#     print("      [PASS]: All chunk IDs are unique.")

#     # B. Schema Conformity
#     for c in chunks:
#         assert "chunk_id" in c and c["chunk_id"], "Missing chunk_id"
#         assert c["chunk_type"] in ("text", "table"), f"Invalid chunk_type: {c['chunk_type']}"
#         assert c["document_name"], "Missing document_name"
#         assert c["section_title"], "Missing section_title"
#         assert isinstance(c["start_page"], int), "start_page must be int"
#         assert isinstance(c["end_page"], int), "end_page must be int"
#         assert isinstance(c["content"], str) and c["content"].strip(), "content must be non-empty string"

#         if c["chunk_type"] == "table":
#             assert isinstance(c["table_data"], list) and len(c["table_data"]) > 0, "table_data must be non-empty list"
#             assert "|" in c["content"] and "---" in c["content"], "table content must be valid Markdown"
#         else:
#             assert c["table_data"] is None, "text chunk table_data must be None"
#     print("      [PASS]: 100% of chunks conform strictly to the unified schema.")

#     # C. Section Boundary Hard Walls
#     for c in chunks:
#         assert c["section_title"] != "Untitled Section" or len(sections) == 0, "Section title missing"
#     print("      [PASS]: Hard section boundaries strictly enforced.")

#     # 3. Stream Sequence Audit (Text -> Table -> Text)
#     print("\n[3/3] Inspecting Real-World Financial Chunk Streams...")

#     # Find a section with both text and tables to demonstrate exact sequence
#     mixed_sections = [
#         s for s in sections
#         if any(item["type"] == "table" for item in s.get("content", []))
#         and any(item["type"] == "span" for item in s.get("content", []))
#     ]

#     print(f"      Found {len(mixed_sections)} sections containing mixed text and tables.")

#     # Let's inspect a key mixed section: e.g. "Purchases of Equity Securities" or "Critical Audit Matters"
#     target_section = None
#     for s in mixed_sections:
#         if "Purchases of Equity Securities" in s.get("title", "") or "Segment" in s.get("title", ""):
#             target_section = s
#             break
#     if not target_section and mixed_sections:
#         target_section = mixed_sections[0]

#     if target_section:
#         target_chunks = [
#             c for c in chunks
#             if c["document_name"] == target_section.get("document_name")
#             and c["section_title"] == target_section.get("title")
#         ]

#         print("\n" + "=" * 80)
#         print(f"STREAM SEQUENCE AUDIT FOR SECTION: '{target_section.get('title')}'")
#         print(f"Document: {target_section.get('document_name')} | Pages: {target_section.get('start_page')}-{target_section.get('end_page')}")
#         print("=" * 80)

#         for idx, c in enumerate(target_chunks, 1):
#             print(f"\n--- Item {idx} in Section Stream: [{c['chunk_type'].upper()}] (ID: {c['chunk_id']}) ---")
#             if c["chunk_type"] == "table":
#                 print(f"Raw 2D Rows: {len(c['table_data'])} rows x {len(c['table_data'][0]) if c['table_data'] else 0} cols")
#             print("Content Preview:")
#             print(c["content"])

#     # 4. Preview a Major Financial Statement Table Chunk
#     print("\n" + "=" * 80)
#     print("PREVIEW: MAJOR FINANCIAL STATEMENT TABLE CHUNK")
#     print("=" * 80)
#     for c in table_chunks:
#         if "Statements of Operations" in c["content"] or "Revenues" in c["content"]:
#             print(f"Chunk ID    : {c['chunk_id']}")
#             print(f"Document    : {c['document_name']}")
#             print(f"Section     : {c['section_title']}")
#             print(f"Page        : {c['start_page']}")
#             print(f"Raw Grid    : {len(c['table_data'])} rows")
#             print("-" * 80)
#             print(c["content"][:600] + "\n... [truncated for display]")
#             break

#     print("\n" + "=" * 80)
#     print("ALL CHUNK BUILDER AUDIT CHECKS COMPLETED SUCCESSFULLY!")
#     print("=" * 80)


# if __name__ == "__main__":
#     main()



"""
inspect_pages.py
Prints all generated text and table chunks between specific pages (e.g., pages 20 to 30).
"""

from core.config import DOCS_PATH
from core.pdf.parser import extract_documents
from core.chunking.preprocessor import preprocess_pages
from core.chunking.service import build_sections
from core.chunking.chunk_builder import build_chunks


def print_chunks_by_page_range(
    start_page: int = 20,
    end_page: int = 30,
    doc_filter: str = "apple_10k.pdf",
):
    print("=" * 80)
    print(
        f"EXTRACTING & CHUNKING PAGES "
        f"{start_page} TO {end_page} "
        f"({doc_filter or 'All Docs'})"
    )
    print("=" * 80)

    # 1. Run complete pipeline
    pages = extract_documents(DOCS_PATH)
    pages = preprocess_pages(pages)
    sections = build_sections(pages)
    chunks = build_chunks(sections)

    # Print overall chunk statistics
    total_chunks = len(chunks)
    total_table_chunks = sum(
        1 for chunk in chunks
        if chunk["chunk_type"] == "table"
    )

    total_text_chunks = sum(
        1 for chunk in chunks
        if chunk["chunk_type"] == "text"
    )

    print("\n" + "=" * 80)
    print("CHUNKING SUMMARY")
    print("=" * 80)
    print(f"Total chunks       : {total_chunks}")
    print(f"Text chunks        : {total_text_chunks}")
    print(f"Table chunks       : {total_table_chunks}")
    print("=" * 80 + "\n")


    # 2. Filter chunks by document and page range
    selected_chunks = []

    for chunk in chunks:
        if doc_filter and chunk["document_name"].lower() != doc_filter.lower():
            continue

        if (
            chunk["start_page"] <= end_page
            and chunk["end_page"] >= start_page
        ):
            selected_chunks.append(chunk)

    print(
        f"Found {len(selected_chunks)} chunks "
        f"between Page {start_page} and Page {end_page}.\n"
    )

    # 3. Print chunks
    for idx, chunk in enumerate(selected_chunks, 1):

        print("=" * 80)
        print(
            f"[{idx}/{len(selected_chunks)}] "
            f"{chunk['chunk_id']}"
        )

        print(f"TYPE     : {chunk['chunk_type']}")
        print(f"SECTION  : {chunk['section_title']}")
        print(
            f"PAGE     : "
            f"{chunk['start_page']} - {chunk['end_page']}"
        )

       
        # Table-specific information
        if chunk["chunk_type"] == "table":

            print("-" * 80)
            print("TABLE METADATA:")
            print(chunk["table_metadata"])

            print("-" * 80)
            print("TABLE DATA:")

            for row in chunk["table_data"]:
                print(row)

        # Final content
        print("-" * 80)
        print("CONTENT:")
        print(chunk["content"])

        print("=" * 80)
        print()


if __name__ == "__main__":
    print_chunks_by_page_range(
        start_page=20,
        end_page=30,
        doc_filter="apple_10k.pdf",
    )