from core.pdf.parser import extract_documents
from core.pdf.header_detector import detect_headers
from core.chunking.preprocessor import preprocess_pages

DOCS_PATH = "docs"


def main():

    pages = extract_documents(DOCS_PATH)
    
    # Apply preprocessing 
    pages = preprocess_pages(pages)

    # Apple page 20 (or whichever page had the broken heading)
    # for page in pages[:80]:
    #     print("=" * 70)
    #     print(f"Document : {page['document_name']}")
    #     print(f"Page     : {page['page_number']}")
    #     print("=" * 70)
        
    #     print("\nMerged Bold Spans:\n")
    #     for span in page["spans"]:
    #         if span["bold"]:
    #             print(span["text"])
    #             print("-"*50)
        
    #     # -------------------------------
    #     # Test Header Detector
    #     # -------------------------------

    #     page["headers"] = detect_headers(page)

    #     print("\n" + "=" * 70)
    #     print("Headers Detected:\n")

    #     for header in page["headers"]:
    #         print(header["text"])

    
    
    # checking table headers
    for page in pages[55:60]:
        if not page["tables"]:
            continue

        print("=" * 70)
        print("Document:", page["document_name"])
        print("Page no.:", page["page_number"])
        print("Tables:", len(page["tables"]))

        for table in page["tables"]:
            print("\nMetadata:")
            for line in table["metadata"]:
                print("  ", line)
    
    
    
    
    # for page in pages:
    #     page["headers"] = detect_headers(page)

    # for page in pages[40:45]:

    #     print("=" * 60)
    #     print(f"Document : {page['document_name']}")
    #     print(f"Page {page['page_number']}")
    #     print("=" * 60)
        
    #     print("\nHeaders Found:")

    #     for header in page["headers"]:
    #         print(header["text"])


if __name__ == "__main__":
    main()