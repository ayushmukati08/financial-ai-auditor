"""
Experiment:
Detect logical sections from the extracted PDF while preserving
the relative order of narrative text and tables.
"""

from core.pdf.parser import extract_documents
from core.chunking.service import build_sections
from core.chunking.preprocessor import preprocess_pages

DOCS_PATH = "docs"


def main():
    print("Extracting documents...")
    pages = extract_documents(DOCS_PATH)

    # preprocessing 
    pages = preprocess_pages(pages)

    print("Building sections...")
    sections = build_sections(pages)

    print("=" * 90)
    print("SECTION DETECTION SUMMARY")
    print("=" * 90)
    print(f"Total Sections Detected: {len(sections)}")

    sections_with_tables = [
        s for s in sections if any(item["type"] == "table" for item in s["content"])
    ]
    print(f"Sections containing tables: {len(sections_with_tables)}\n")

    # Display first 100 sections in full without any slicing or truncation
    for i, section in enumerate(sections[:100], start=1):
        has_tables = any(item["type"] == "table" for item in section["content"])
        table_flag = (
            f" [CONTAINS {sum(1 for it in section['content'] if it['type'] == 'table')} TABLE(S)]"
            if has_tables
            else ""
        )

        print("=" * 90)
        print(f"Section {i}: '{section['title']}'{table_flag}")
        print(f"Document : {section['document_name']}")
        print(f"Pages    : {section['start_page']} - {section['end_page']}")
        print(f"Total Items: {len(section['content'])}")
        print("-" * 90)

        for idx, item in enumerate(section["content"]):
            if item["type"] == "span":
                sp = item["data"]
                print(f"  [{idx:03d}] SPAN (Page {sp['page_number']}) : {sp['text']}")
            elif item["type"] == "table":
                t = item["data"]
                grid = t.get("data", [])
                rows_count = len(grid)
                cols_count = len(grid[0]) if rows_count else 0
                meta = t.get("metadata", [])
                print(
                    f"\n  [{idx:03d}] *** TABLE (Page {t['page_number']}) *** : "
                    f"{rows_count} rows x {cols_count} cols | Meta: {meta}"
                )
                for r in grid:
                    row_str = " | ".join(
                        str(c).replace("\n", " ") if c is not None else "" for c in r
                    )
                    print(f"        | {row_str} |")
                print()
        print()


if __name__ == "__main__":
    main()