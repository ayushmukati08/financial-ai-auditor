"""
Detect logical document sections from header candidates.

Input:
    Pages with:
        - spans
        - tables
        - headers

Output:
    List of sections.
"""

from copy import deepcopy


def detect_sections(pages: list[dict]) -> list[dict]:
    """
    Groups document content into logical sections.

    A new section starts whenever a detected header is encountered.
    """

    sections = []
    current_section = None

    for page in pages:
        # Convert headers into a lookup for quick membership testing
        header_texts = {
            header["text"]
            for header in page["headers"]
        }

        for span in page["spans"]:
            text = span["text"]
            # ----------------------------
            # New Section
            # ----------------------------
            if text in header_texts:

                # Save previous section
                if current_section is not None:
                    sections.append(current_section)

                # Start new section
                current_section = {
                    "title": text,
                    "document_name": page["document_name"],
                    "start_page": page["page_number"],
                    "end_page": page["page_number"],
                    "spans": [],
                    "tables": [],
                }

            # ----------------------------
            # Ignore text before first section
            # ----------------------------
            if current_section is None:
                continue

            current_section["spans"].append(deepcopy(span))
            current_section["end_page"] = page["page_number"]

        # ----------------------------
        # Attach tables
        # ----------------------------
        if current_section is not None:
            current_section["tables"].extend(page["tables"])

    # Save last section
    if current_section is not None:
        sections.append(current_section)

    return sections