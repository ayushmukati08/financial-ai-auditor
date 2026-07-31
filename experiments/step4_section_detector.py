"""
Experiment:
Detect logical sections from the extracted PDF.
"""

from core.pdf.parser import extract_documents
from core.chunking.service import build_sections

DOCS_PATH = "docs"


def main():
    pages = extract_documents(DOCS_PATH)
    sections = build_sections(pages)

    print("=" * 70)
    print("SECTION DETECTION SUMMARY")
    print("=" * 70)

    print(f"Total Sections: {len(sections)}\n")

    for i, section in enumerate(sections[:100], start=1):

        print(f"Section {i}")
        print(f"Title      : {section['title']}")
        print(
            f"Pages      : {section['start_page']} - {section['end_page']}"
        )
        print(f"Spans      : {len(section['spans'])}")
        print(f"Tables     : {len(section['tables'])}")
        print("-" * 70)


if __name__ == "__main__":
    main()