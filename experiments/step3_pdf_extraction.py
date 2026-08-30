"""
step3_pdf_extraction.py

Exploratory / throwaway script for this step.
Once the logic works here, promote a clean version into core/.
"""

from core.pdf.parser import extract_documents

DOCS_PATH = "docs"


def main():

    pages = extract_documents(DOCS_PATH)

    print("=" * 70)
    print("PDF EXTRACTION SUMMARY")
    print("=" * 70)

    print(f"Total Pages Extracted : {len(pages)}")

    print("=" * 70)

    # Inspect a few pages
    for page in pages[20:30]:

        print(f"Document     : {page['document_name']}")
        print(f"Page Number  : {page['page_number']}")
        print(f"Page Size    : {page['page_width']:.1f} x {page['page_height']:.1f}")

        print(f"Text Spans   : {len(page['spans'])}")
        print(f"Tables Found : {len(page['tables'])}")

        print("-" * 70)

        # First few spans
        print("First 10 Text Spans:")

        for span in page["spans"][:10]:

            print(
                f"[size={span['size']:.1f}, "
                f"bold={span['bold']}] "
                f"{span['text']}"
            )

        # Tables
        if page["tables"]:

            print("\nTables:")

            for i, table in enumerate(page["tables"], start=1):

                print(f"\nTable {i}")

                for row in table["data"][:5]:
                    print(row)

                if len(table["data"]) > 5:
                    print("...")

        print("=" * 70)


if __name__ == "__main__":
    main()