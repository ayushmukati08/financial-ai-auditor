"""
PDF text + structure extraction (section headers, tables, page numbers).
Promote clean logic here from experiments/step3_pdf_extraction.py.
"""
import os
import fitz

# Maximum distance (points) above a table to search for metadata.
# Chosen empirically from SEC filings. Revisit if evaluation on
# additional document layouts shows poor generalization.
TABLE_METADATA_DISTANCE = 50
TABLE_MAX_VERTICAL_GAP = 5
TABLE_MAX_CENTER_DIFF = 60
COLUMN_X_THRESHOLD = 40
TABLE_HEADER_EXPANSION_GAP = 10


def extract_documents(docs_path: str) -> list[dict]:
    """
    Extract raw PDF content.

    Returns one dictionary per page containing:
    - document metadata
    - page geometry
    - detected tables
    - text spans

    No semantic section/header detection happens here.
    The parser performs layout-based table association so that
    table header spans can be attached to their corresponding
    tables and excluded from narrative text.
    
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
                        "metadata": [],
                        "data": table.extract(),
                        "document_name": file_name,
                        "page_number": page_index + 1,
                    }
                )

                table_bboxes.append(table.bbox)

            spans = _extract_spans(page, table_bboxes)
            
            spans = _attach_table_metadata(
                spans,
                table_entries,
            )
            
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
    span_counter = 0
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
                    _, y0, _, y1 = span["bbox"]

                    page_height = page.rect.height

                    # Ignore page numbers only if they are very near
                    # the top or bottom edge.
                    edge_margin = page_height * 0.06  # roughly top/bottom 6% of the page
                    if y0 < edge_margin or y1 > page_height - edge_margin:
                        continue
                
                spans.append(
                    {
                        "span_id": span_counter,
                        "text": text,
                        "size": span["size"],
                        "bold": bool(span["flags"] & (1 << 4)),
                        "bbox": span["bbox"],
                        "page_number": page.number + 1,
                    }
                )
                
                span_counter += 1
                
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

def _expand_table_metadata_candidates(
    candidates: list[dict],
    rejected: list[dict],
) -> list[dict]:
    """
    Recover the first line of wrapped table headers.

    If a rejected bold span is immediately above an
    accepted candidate, add it back.
    """

    recovered = candidates.copy()

    for r in rejected:
        for c in recovered:

            # must be above
            if r["bbox"][3] >= c["bbox"][1]:
                continue

            gap = c["bbox"][1] - r["bbox"][3]

            if gap > TABLE_HEADER_EXPANSION_GAP:
                continue

            if abs(r["size"] - c["size"]) > 0.1:
                continue

            recovered.append(r)
            break

    recovered.sort(key=lambda s: s["span_id"])
    return recovered


# NOTE:
# PyMuPDF may split a logical table into multiple table regions
# (e.g., table of contents pages). This can produce repeated
# metadata across adjacent tables. Metadata extraction follows
# the table regions returned by PyMuPDF and does not merge them.

def _attach_table_metadata(
    spans: list[dict],
    tables: list[dict],
) -> list[dict]:
    """
    Finds bold text immediately above each table,
    merges wrapped header lines and stores them
    as table metadata.

    The consumed spans are removed from page text
    so they don't become document headers.
    """
    
    used_span_ids = set()

    for table in tables:
        tx0, ty0, tx1, ty1 = table["bbox"]
        candidates = []
        too_far = []
        
        for span in spans:
            # Already assigned to a previous table.
            if span["span_id"] in used_span_ids:
                continue
    
            if not span["bold"]:
                continue
            
            sx0, sy0, sx1, sy1 = span["bbox"]
            
            # must be above table
            if sy1 > ty0:         
                continue
            
            # Above the search window.
            # Preserve spans rejected only because they are slightly above the
            # table search window. They may represent the first line of a
            # wrapped table header and can be recovered later.
            if ty0 - sy1 > TABLE_METADATA_DISTANCE:        
                too_far.append(span)
                continue
                
            # horizontal overlap
            overlap = min(tx1, sx1) - max(tx0, sx0)
            if overlap <= 0:              
                continue

            candidates.append(span)
        
        candidates = _expand_table_metadata_candidates(
            candidates,
            too_far,
        )
         
        columns = _cluster_table_columns(candidates)
        merged = []

        for column in columns:
            column.sort(key=lambda s: s["bbox"][1])
            merged.extend(_merge_wrapped_table_headers(column))

        table["metadata"] = [s["text"] for s in merged]

        for span in candidates:
            used_span_ids.add(span["span_id"])

    filtered = [
        span
        for span in spans
        if span["span_id"] not in used_span_ids
    ]

    return filtered

def _cluster_table_columns(
    spans: list[dict],
) -> list[list[dict]]:
    """
    Group table metadata spans into columns using horizontal bounding-box overlap.
    Spans that share horizontal overlap belong to the same column header.
    """
    if not spans:
        return []

    # Sort spans by vertical top (y0), then horizontal left (x0)
    sorted_spans = sorted(spans, key=lambda s: (s["bbox"][1], s["bbox"][0]))
    columns: list[list[dict]] = []

    for span in sorted_spans:
        placed = False
        sx0, sy0, sx1, sy1 = span["bbox"]

        # Check against existing columns for horizontal overlap
        best_col = None
        max_overlap = 0.0

        for col in columns:
            cx0 = min(s["bbox"][0] for s in col)
            cx1 = max(s["bbox"][2] for s in col)
            overlap = min(sx1, cx1) - max(sx0, cx0)
            if overlap > max_overlap:
                max_overlap = overlap
                best_col = col

        if best_col is not None and max_overlap > 0:
            best_col.append(span)
        else:
            # Fallback: check center distance within column tolerance
            scenter = (sx0 + sx1) / 2
            for col in columns:
                cx0 = min(s["bbox"][0] for s in col)
                cx1 = max(s["bbox"][2] for s in col)
                ccenter = (cx0 + cx1) / 2
                if abs(scenter - ccenter) <= COLUMN_X_THRESHOLD:
                    col.append(span)
                    placed = True
                    break
            if not placed:
                columns.append([span])

    # Sort columns from left to right by their minimum x0
    columns.sort(key=lambda col: min(s["bbox"][0] for s in col))
    return columns


def _merge_wrapped_table_headers(
    spans: list[dict],
) -> list[dict]:
    """
    Merge wrapped table header spans within a single column cluster.
    Sorts top-to-bottom, then left-to-right, merging tokens cleanly.
    """
    if not spans:
        return spans

    sorted_spans = sorted(
        spans,
        key=lambda s: (round(s["bbox"][1], 1), s["bbox"][0])
    )

    merged_span = sorted_spans[0].copy()
    tokens = [s["text"].strip() for s in sorted_spans if s["text"].strip()]
    merged_span["text"] = " ".join(tokens)
    merged_span["bbox"] = (
        min(s["bbox"][0] for s in sorted_spans),
        min(s["bbox"][1] for s in sorted_spans),
        max(s["bbox"][2] for s in sorted_spans),
        max(s["bbox"][3] for s in sorted_spans),
    )

    return [merged_span]

def _can_merge_table(
    current: dict,
    nxt: dict,
) -> bool:

    if abs(current["size"] - nxt["size"]) > 0.1:
        return False

    current_bottom = current["bbox"][3]
    next_top = nxt["bbox"][1]

    if next_top - current_bottom > TABLE_MAX_VERTICAL_GAP:
        return False

    # Compare horizontal centers instead of left edge
    current_center = (current["bbox"][0] + current["bbox"][2]) / 2
    next_center = (nxt["bbox"][0] + nxt["bbox"][2]) / 2

    if abs(current_center - next_center) > TABLE_MAX_CENTER_DIFF:
        return False

    return True


# KNOWN LIMITATION: span order follows PyMuPDF's internal block order, which
# does not always match visual reading order on multi-column layouts (e.g.,
# side-by-side text + table footnotes). This can cause incorrect header/body
# attribution in the chunker for multi-column pages. Revisit with column-aware
# sorting (cluster spans by x-position, sort top-to-bottom per column) if this
# causes noticeable chunk quality issues on real 10-Q/10-K documents.

# KNOWN LIMITATION: extracted tables may include empty separator rows
# (e.g., ['', '', '', '', '', '', '']). Filter these during chunk
# construction, not here, to keep raw extraction output unmodified.

# KNOWN LIMITATION:
# Multi-level table headers (parent-child column groups)
# are flattened into sequential metadata rather than
# preserving hierarchical relationships.