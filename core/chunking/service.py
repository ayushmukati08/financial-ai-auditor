from core.pdf.header_detector import detect_headers
from core.chunking.section_detector import detect_sections


def build_sections(pages: list[dict]) -> list[dict]:

    for page in pages:
        page["headers"] = detect_headers(page)

    return detect_sections(pages)