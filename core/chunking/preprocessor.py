from collections import Counter

REPEATED_HEADER_THRESHOLD = 5  # min occurrences across pages to treat as running header/footer

def find_repeated_running_text(pages: list[dict], threshold: int = REPEATED_HEADER_THRESHOLD) -> set[str]:
    """
    Scans all pages in a document and returns span texts that recur on many
    pages near-identically — a signal for running headers/footers (e.g.
    "Table of Contents" repeated on every page) that should be excluded
    from both header detection and body-text chunking.

    Call this once per document, pass the result into chunking to strip
    these spans wherever they appear.
    """
    counts = Counter()
    for page in pages:
        seen_this_page = set()
        for span in page["spans"]:
            text = span["text"].strip()
            if text and text not in seen_this_page:
                counts[text] += 1
                seen_this_page.add(text)

    return {text for text, count in counts.items() if count >= threshold}