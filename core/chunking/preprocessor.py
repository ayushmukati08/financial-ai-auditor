"""
Preprocessing utilities applied before header detection.

Responsibilities:
1. Remove repeated running headers/footers.
2. Merge wrapped bold spans into logical spans.
"""

from collections import Counter

# min occurrences across pages to treat as running header/footer

REPEATED_HEADER_THRESHOLD = 5

# Maximum distance (points) between two wrapped lines
MAX_VERTICAL_GAP = 5

# Allowed difference in left alignment
MAX_X_DIFF = 5

# Margin percentage to search for running headers/footers (top 8% and bottom 8%)
EDGE_MARGIN_RATIO = 0.08

def preprocess_pages(pages: list[dict]) -> list[dict]:
    """
    Applies all preprocessing before header detection.

    Pipeline:
        1. Detect repeated running text in page margins.
        2. Remove repeated margin spans.
        3. Merge wrapped bold spans.
    """

    repeated = find_repeated_running_text(pages)
    processed_pages = []

    for page in pages:
        spans = remove_running_text(page["spans"], repeated, page.get("page_height", 792.0))
        spans = merge_wrapped_spans(spans)
        page["spans"] = spans
        processed_pages.append(page)

    return processed_pages

def find_repeated_running_text(
    pages: list[dict], 
    threshold: int = REPEATED_HEADER_THRESHOLD,
    edge_ratio: float = EDGE_MARGIN_RATIO,
) -> set[str]:
    """
    Detect repeated running headers/footers that appear
    in the top or bottom margins of many pages.
    """
    counts = Counter()
    for page in pages:
        page_height = page.get("page_height", 792.0)
        edge_margin = page_height * edge_ratio
        
        seen = set()
        for span in page.get("spans", []):
            text = span["text"].strip()
            if not text:
                continue

            if text in seen:
                continue

            y0, y1 = span["bbox"][1], span["bbox"][3]
            # Only count text in the top or bottom margin
            if y0 < edge_margin or y1 > page_height - edge_margin:
                counts[text] += 1
                seen.add(text)

    return {text for text, count in counts.items() if count >= threshold}


def remove_running_text(
    spans: list[dict],
    repeated_text: set[str],
    page_height: float = 792.0,
    edge_ratio: float = EDGE_MARGIN_RATIO,
) -> list[dict]:
    """
    Removes repeated running headers/footers located in page margins.
    """
    if not repeated_text:
        return spans

    edge_margin = page_height * edge_ratio
    
    cleaned = []
    for span in spans:
        text = span["text"].strip()
        y0, y1 = span["bbox"][1], span["bbox"][3]
        in_edge = y0 < edge_margin or y1 > page_height - edge_margin

        if in_edge and text in repeated_text:
            continue
        cleaned.append(span)

    return cleaned

def merge_wrapped_spans(
    spans: list[dict],
) -> list[dict]:
    """
    Merge wrapped bold spans into a single logical span.
    Example
        Global markets for the Company's...
        unable to compete...
    becomes
        Global markets for the Company's...
        unable to compete...
    """

    if not spans:
        return spans

    merged = []
    current = spans[0].copy()

    for nxt in spans[1:]:
        if _can_merge(current, nxt):
            current["text"] += " " + nxt["text"]
            current["bbox"] = (
                min(current["bbox"][0], nxt["bbox"][0]),
                min(current["bbox"][1], nxt["bbox"][1]),
                max(current["bbox"][2], nxt["bbox"][2]),
                max(current["bbox"][3], nxt["bbox"][3]),
            )
        else:
            merged.append(current)
            current = nxt.copy()
            
    merged.append(current)
    return merged

def _can_merge(
    current: dict,
    nxt: dict,
) -> bool:
    """
    Returns True if two spans are likely to be parts
    of the same wrapped heading.
    """

    # Only merge bold spans.
    if not current["bold"] or not nxt["bold"]:
        return False

    # Same font size.
    if abs(current["size"] - nxt["size"]) > 0.1:
        return False

    # Similar left alignment.
    current_x = current["bbox"][0]
    next_x = nxt["bbox"][0]

    if abs(current_x - next_x) > MAX_X_DIFF:
        return False

    # Small vertical gap.
    current_bottom = current["bbox"][3]
    next_top = nxt["bbox"][1]
    if (next_top - current_bottom) > MAX_VERTICAL_GAP:
        return False

    # Wrapped headings usually continue with lowercase.
    # next_text = nxt["text"].lstrip()
    # if next_text and next_text[0].isupper():
    #     return False

    return True