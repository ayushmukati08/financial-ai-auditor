"""
PDF text + structure extraction (section headers, tables, page numbers).
Promote clean logic here from experiments/step3_pdf_extraction.py.
"""
import os
import fitz

def extract_documents(docs_path: str) -> list[dict]:
    """
    Extract raw PDF content.

    Returns one dictionary per page containing:
    - document metadata
    - page geometry
    - detected tables
    - text spans

    No structural interpretation happens here.
    
    Args:
        docs_path: Path to the folder where pdf's are stored.

    Returns:
        A list where each element represents one page.

        Example:
    [
        {
            "document_name": "apple_10q.pdf",
            "page_number": 1,
            "page_width": 612.0,
            "page_height": 792.0,
            "tables": [
                {
                    "bbox": (72.0, 400.0, 540.0, 620.0),
                    "data": [["row1col1", "row1col2"], ["row2col1", "row2col2"]],
                },
                ...
            ],
            "spans": [
                {
                    "text": "Item 7. MD&A",
                    "size": 14.0,
                    "bold": True,
                    "bbox": (72.0, 100.5, 310.2, 115.0),
                },
                ...
            ],
        },
        ...
    ]

    Note: header/section detection is NOT performed here — see header_detector.py.
    This function returns raw content only (tables, and text broken into spans
    with position/font metadata), with table regions excluded from spans to
    avoid double-extraction.
        
    refactor to dataclass later when page objects grow to include many fields (document ID, chunk IDs, metadata, etc.)
    """
    
    if not os.path.exists(docs_path):
        raise FileNotFoundError(
            f"Directory '{docs_path}' does not exist."
        )

    pages = []

    for file_name in sorted(os.listdir(docs_path)):
        if not file_name.lower().endswith(".pdf"):
            continue

        pdf_path = os.path.join(docs_path, file_name)
        document = fitz.open(pdf_path)
        
        for page_index in range(len(document)):
            page = document[page_index]
            
            # tables first — so we know their bounding boxes and can flag
            # which text spans belong to a table vs. narrative text later
            table_entries = []
            table_bboxes = []
            
            found_tables = page.find_tables()
            
            for table in found_tables.tables:
                table_entries.append(
                    {
                        "bbox": table.bbox,
                        "data": table.extract(),
                    }
                )

                table_bboxes.append(table.bbox)

            spans = _extract_spans(page, table_bboxes)
            
            pages.append({
                    "document_name": file_name,
                    "page_number": page_index + 1,
                    "page_width": page.rect.width,
                    "page_height": page.rect.height,
                    "tables": table_entries,
                    "spans": spans,
                })
            
        document.close()

    if not pages:
        raise FileNotFoundError(
            f"No PDF files found in '{docs_path}'."
        )

    return pages


def _extract_spans(
    page: fitz.Page, 
    table_bboxes: list[tuple]
) -> list[dict]:
    spans = []
    blocks = page.get_text("dict")["blocks"]

    for block in blocks:
        if "lines" not in block:
            continue

        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()

                if not text:
                    continue

                if _bbox_inside_table(span["bbox"], table_bboxes):
                    continue
                
                if text.isdigit():
                    x0, y0, x1, y1 = span["bbox"]

                    page_height = page.rect.height

                    # Ignore page numbers only if they are very near
                    # the top or bottom edge.
                    edge_margin = page_height * 0.06  # roughly top/bottom 6% of the page
                    if y0 < edge_margin or y1 > page_height - edge_margin:
                        continue
                
                spans.append(
                    {
                        "text": text,
                        "size": span["size"],
                        "bold": bool(span["flags"] & (1 << 4)),
                        "bbox": span["bbox"],
                        "page_number": page.number + 1,
                    }
                )
                
    return spans


def _bbox_inside_table(
    bbox: tuple,
    table_bboxes: list[tuple],
    overlap_threshold: float = 0.5,
) -> bool:
    x0, y0, x1, y1 = bbox
    span_area = max(0, x1 - x0) * max(0, y1 - y0)

    if span_area == 0:
        return False

    for tb in table_bboxes:
        tx0, ty0, tx1, ty1 = tb

        ix0 = max(x0, tx0)
        iy0 = max(y0, ty0)

        ix1 = min(x1, tx1)
        iy1 = min(y1, ty1)

        inter_area = max(0, ix1 - ix0) * max(0, iy1 - iy0)

        if inter_area / span_area >= overlap_threshold:
            return True

    return False




# KNOWN LIMITATION: span order follows PyMuPDF's internal block order, which
# does not always match visual reading order on multi-column layouts (e.g.,
# side-by-side text + table footnotes). This can cause incorrect header/body
# attribution in the chunker for multi-column pages. Revisit with column-aware
# sorting (cluster spans by x-position, sort top-to-bottom per column) if this
# causes noticeable chunk quality issues on real 10-Q/10-K documents.

# KNOWN LIMITATION: extracted tables may include empty separator rows
# (e.g., ['', '', '', '', '', '', '']). Filter these during chunk
# construction, not here, to keep raw extraction output unmodified.