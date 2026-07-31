from core.pdf.parser import extract_documents
from core.pdf.header_detector import detect_headers

DOCS_PATH = "docs"


def main():

    pages = extract_documents(DOCS_PATH)
    
    for page in pages:
        page["headers"] = detect_headers(page)

    for page in pages[40:45]:

        print("=" * 60)
        print(f"Document : {page['document_name']}")
        print(f"Page {page['page_number']}")
        print("=" * 60)
        
        print("\nHeaders Found:")

        for header in page["headers"]:
            print(header["text"])


if __name__ == "__main__":
    main()