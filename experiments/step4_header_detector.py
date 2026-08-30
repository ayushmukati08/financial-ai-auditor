from core.pdf.parser import extract_documents
from core.pdf.header_detector import detect_headers
from core.chunking.preprocessor import preprocess_pages

DOCS_PATH = "docs"


def main():

    pages = extract_documents(DOCS_PATH)
    
    # Apply preprocessing 
    # pages = preprocess_pages(pages)

    # Apple page 20 (or whichever page had the broken heading)
    for page in pages[:81]:
        print("=" * 80)
        print(f"Document : {page['document_name']}")
        print(f"Page     : {page['page_number']}")
        print("=" * 80)
        
        # print("\nMerged Bold Spans:\n")
        # for span in page["spans"]:
        #     if span["bold"]:
        #         print(span["text"])
        #         print("-"*50)
        
        
        # --------------------------------
        # All remaining bold spans
        # --------------------------------

        print("\nALL BOLD SPANS:\n")

        for span in page["spans"]:
            if span["bold"]:
                print(
                    f"{span['size']:5.1f} | "
                    f"{span['text']}"
                )
        
        
        # -------------------------------
        # Test Header Detector
        # -------------------------------

        page["headers"] = detect_headers(page)

        print("\nHEADER CANDIDATES:\n")

        for header in page["headers"]:
            print(
                f"{header['size']:5.1f} | "
                f"{header['text']}"
            )
        
        
        


if __name__ == "__main__":
    main()