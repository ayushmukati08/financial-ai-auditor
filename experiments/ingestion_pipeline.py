import os
# from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from dotenv import load_dotenv
from collections import Counter

# defining global variables 
DOCS_PATH = "docs"
CHROMA_DB_PATH = "db/chroma_db"
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
COLLECTION_METADATA = {
    "hnsw:space": "cosine"
}

load_dotenv()

def get_embedding_model() -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    
def load_documents(docs_path=DOCS_PATH) -> list[Document]:
    """Load all text files from the docs directory"""
    print(f"\n📂 Loading documents from {docs_path}...")
    
    # Check if docs directory exists
    if not os.path.exists(docs_path):
        raise FileNotFoundError(f"The directory {docs_path} does not exist. Please create it and add your company files.")
    
    documents = []
    
    pdf_counter = Counter()
    
    # Load all .pdf files from the docs directory
    for file in os.listdir(docs_path):
        if file.lower().endswith(".pdf"):
            pdf_path = os.path.join(docs_path, file)

            loader = PyMuPDFLoader(pdf_path)
            docs = loader.load()
            
            # Clean metadata
            for doc in docs:
                doc.metadata = {
                    "source": doc.metadata.get("source"),
                    "page": doc.metadata.get("page"),
                    "page_label": doc.metadata.get("page_label"),
                    "total_pages": doc.metadata.get("total_pages"),
                }
                pdf_counter[doc.metadata["source"]] += 1
            
        documents.extend(docs)
    
    if not documents:
        raise FileNotFoundError(f"No .pdf files found in {docs_path}. Please add your company documents.")
    
    print(f"✅ Successfully Loaded {len(documents)} pages.")
    
    # detailed summary
    # for i, doc in enumerate(documents[:2]):  # Show first 2 documents
    #     print(f"\nDocument {i+1}:")
    #     print(f"  Source: {doc.metadata.get('source')}")
    #     print(f"  Page   : {doc.metadata.get('page')}")
    #     print(f"  Content length: {len(doc.page_content)} characters")
    #     print(f"  Content preview: {doc.page_content[:100]}...")
    #     print(f"  metadata: {doc.metadata}")
    
    # print precise summary
    print("\nDocuments Found:")
    
    for pdf, pages in pdf_counter.items():
        filename = os.path.basename(pdf)
        print(f"  • {filename:<70} {pages:>3} pages")
        
    print(f"\nTotal PDFs : {len(pdf_counter)}")
    print(f"Total Pages: {len(documents)}")
    print("-" * 60)
    
    return documents

def split_documents(documents, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    """Split documents into smaller chunks with overlap"""
    print("\n✂️ Splitting documents into chunks...")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, 
        chunk_overlap=chunk_overlap,
        separators=[
            "\n\n",
            "\n",
            " ",
            ""
        ]
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"✅ Created {len(chunks)} chunks.")
    
    # detailed summary
    # if chunks:
    #     for i, chunk in enumerate(chunks[:5]):
    #         print(f"\n--- Chunk {i+1} ---")
    #         print(f"Source: {chunk.metadata['source']}")
    #         print(f"Page   : {chunk.metadata['page']}")
    #         print(f"Length: {len(chunk.page_content)} characters")
    #         print(f"Content:")
    #         print(chunk.page_content)
    #         print("-" * 50)
        
    #     if len(chunks) > 5:
    #         print(f"\n... and {len(chunks) - 5} more chunks")
    
    
    # precise summary
    if chunks:
        avg_chunk = sum(len(chunk.page_content) for chunk in chunks) / len(chunks)
        print(f"Average Chunk Size : {avg_chunk:.0f} characters")
    print(f"Chunk Size         : {chunk_size} characters")
    print(f"Chunk Overlap      : {chunk_overlap} characters")
    print("-" * 60)
    
    return chunks

def create_vector_store(chunks, persist_directory=CHROMA_DB_PATH):
    """Create and persist ChromaDB vector store"""
    
    print("\n🧠 Loading embedding model...")
    embedding_model = get_embedding_model()
    
    # Create ChromaDB vector store
    print("🗄️ Creating Chroma vector database...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=persist_directory, 
        collection_metadata=COLLECTION_METADATA
    )
    print("✅ Finished creating vector store.")
    
    print(f"✅ Stored {len(chunks)} vectors.")
    print(f"📁 Database Location : {persist_directory}")
    print("-" * 60)
    return vectorstore

def main():
    """Main ingestion pipeline"""
    print("=" * 60)
    print("RAG Document Ingestion Pipeline")
    print("=" * 60)
    
    # Check if vector store already exists
    if os.path.exists(CHROMA_DB_PATH):
        print("📦 Existing vector database found.")
        print("Skipping ingestion and loading vector database...")
        
        embedding_model = get_embedding_model()
        
        vectorstore = Chroma(
            persist_directory=CHROMA_DB_PATH,
            embedding_function=embedding_model, 
            collection_metadata=COLLECTION_METADATA
        )
        print(f"✅ Loaded {vectorstore._collection.count()} vectors.") # accessing a private attribute need to change in future while publishing
        print("-" * 60)
        return vectorstore
    
    print("📂 No existing vector database found.\nStarting document ingestion...\n")
    
    # Step 1: Load documents
    documents = load_documents(DOCS_PATH)  
    
    # Step 2: Split into chunks
    chunks = split_documents(documents)
    
    # # # Step 3: Create vector store
    vectorstore = create_vector_store(chunks, CHROMA_DB_PATH)
    
    print("\n✅ Ingestion complete! Your documents are now ready for RAG queries.")
    return vectorstore

if __name__ == "__main__":
    main()
