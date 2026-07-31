import re

MAX_HEADER_LENGTH = 80

# Known boilerplate patterns that get falsely flagged as
# headers because they're short and bold (SEC filing checkboxes
IGNORE_SPANS = {
    "x",
    "o",
    "(Mark One)",
    "☒",
    "☐",
    "—",
}

IGNORE_RE = re.compile(
    r"^(OR|AND)$",
    re.IGNORECASE
)

def detect_headers(page: dict, size_ratio_threshold: float = 1.15,) -> list[dict]:
    """
    Detect likely heading candidates.

    This function DOES NOT identify sections.

    It simply marks spans that look visually
    important.
    """

    spans = page["spans"]

    if not spans:
        return []

    sizes = sorted(span["size"] for span in spans)
    median_size = sizes[len(sizes) // 2]
    header_candidates = []

    for span in spans:
        text = span["text"].strip()

        if _is_noise(text):
            continue
        
        is_large = span["size"] >= median_size * size_ratio_threshold

        is_short_bold = span["bold"] and len(text) < MAX_HEADER_LENGTH

        if is_large or is_short_bold:
            header_candidates.append(span)

    return header_candidates


def _is_noise(text: str) -> bool:
    """
    Returns True only for obvious extraction artifacts that can never
    represent meaningful document content.
    """
    
    text = text.strip()

    if not text:
        return True

    if text in IGNORE_SPANS:
        return True

    if IGNORE_RE.fullmatch(text):
        return True

    return False