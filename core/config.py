import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

"""
Central configuration for project paths, embedding models, LLM settings, and chunking parameters.
"""

# Base project directories
BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_PATH = os.getenv("DOCS_PATH", str(BASE_DIR / "docs"))
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", str(BASE_DIR / "db" / "chroma_db"))
COLLECTION_NAME = "financial_filings"

# Chunking parameters
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200

# Embedding & Retrieval parameters
DEFAULT_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
DEFAULT_RERANKER_MODEL = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
DEFAULT_TOP_K = 5

# Gemini LLM parameters
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")