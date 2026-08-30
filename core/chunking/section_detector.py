"""
Detect logical document sections from header candidates.

Input:
    Pages with:
        - spans
        - tables
        - headers

Output:
    List of logical sections.
    Each section preserves the exact physical reading order:
    span -> span -> table -> span -> table -> span
"""

from copy import deepcopy


def detect_sections(pages: list[dict]) -> list[dict]:
    """
    Groups document content into logical sections while preserving
    the exact physical reading order.

    A detected header starts a new section.
    Text spans and tables are sorted and stored together inside `content`
    according to their vertical position (bbox) on the page.
    """

    sections = []
    current_section = None

    for page in pages:
        header_span_ids = {
            header["span_id"]
            for header in page.get("headers", [])
        }

        # Combine all page elements into a single list
        page_elements = []

        for span in page.get("spans", []):
            page_elements.append({
                "type": "span",
                "data": deepcopy(span),
            })

        for table in page.get("tables", []):
            page_elements.append({
                "type": "table",
                "data": deepcopy(table),
            })

        # Sort all items on this page in top-to-bottom reading order
        page_elements.sort(
            key=lambda item: _get_top_position(item["data"])
        )

        # 3. Walk through sorted elements sequentially
        for item in page_elements:
            if item["type"] == "span" and item["data"]["span_id"] in header_span_ids:
                # Save previous section if it exists
                if current_section is not None:
                    sections.append(current_section)

                # Start new section (header text becomes section title)
                current_section = {
                    "title": item["data"]["text"].strip(),
                    "document_name": page["document_name"],
                    "start_page": page["page_number"],
                    "end_page": page["page_number"],
                    "content": [],
                }
            else:
                # Regular span or table
                if current_section is None:
                    # Document preamble before the very first header
                    current_section = {
                        "title": "Document Preamble",
                        "document_name": page["document_name"],
                        "start_page": page["page_number"],
                        "end_page": page["page_number"],
                        "content": [],
                    }

                current_section["content"].append(item)
                current_section["end_page"] = page["page_number"]

    # Save final section
    if current_section is not None:
        sections.append(current_section)

    return sections


def _get_top_position(item: dict) -> float:
    """
    Return the vertical position (top y0) of a span or table.
    PyMuPDF coordinates start at top-left (0,0), so smaller y0 appears earlier.
    """
    bbox = item.get("bbox")
    if bbox:
        return bbox[1]
    return float("inf")