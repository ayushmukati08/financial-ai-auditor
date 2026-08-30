"""
app.py
FastAPI Server for Financial AI Auditor.
Exposes REST APIs and serves the interactive web UI.
"""

import os
import shutil
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.config import BASE_DIR, DOCS_PATH, CHROMA_DB_PATH, GEMINI_MODEL
from core.pipeline import FinancialAIAuditorPipeline
from core.retrieval.vector_store import get_vector_store

# Initialize FastAPI App
app = FastAPI(
    title="Financial AI Auditor",
    description="Grounded Financial Filing Question-Answering with Hybrid Retrieval & Citations",
    version="1.0.0",
)

# Paths
WEB_DIR = BASE_DIR / "web"
STATIC_DIR = WEB_DIR / "static"
TEMPLATES_DIR = WEB_DIR / "templates"

# Mount Static Assets
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Singleton Pipeline
_pipeline = None


def get_pipeline() -> FinancialAIAuditorPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = FinancialAIAuditorPipeline()
    return _pipeline


# --- Pydantic Request Models ---
class AskRequest(BaseModel):
    query: str
    top_k: int = 5
    filter_dict: Optional[dict] = None


# --- API Routes ---

@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """
    Serves the main web dashboard.
    """
    index_file = TEMPLATES_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="index.html not found.")
    return FileResponse(str(index_file))


@app.get("/api/health")
async def health_check():
    """
    Returns engine health status and vector database statistics.
    """
    try:
        vs = get_vector_store()
        count = vs._collection.count()
    except Exception:
        count = 0

    return {
        "status": "online",
        "vectors_count": count,
        "gemini_model": GEMINI_MODEL,
        "chroma_db": str(CHROMA_DB_PATH),
    }


@app.get("/api/documents")
async def list_documents():
    """
    Returns all distinct financial filings indexed in ChromaDB.
    """
    try:
        vs = get_vector_store()
        data = vs._collection.get(include=["metadatas"])
        
        doc_stats = {}
        for m in data.get("metadatas", []):
            dname = m.get("document_name", "unknown")
            if dname not in doc_stats:
                doc_stats[dname] = {"name": dname, "chunks": 0, "tables": 0, "text": 0}
            doc_stats[dname]["chunks"] += 1
            if m.get("chunk_type") == "table":
                doc_stats[dname]["tables"] += 1
            else:
                doc_stats[dname]["text"] += 1

        return {"documents": list(doc_stats.values())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ask")
async def ask_auditor(request: AskRequest):
    """
    Runs the full hybrid retrieval (Dense + BM25 -> RRF -> Cross-Encoder)
    and generates a cited response with Gemini.
    """
    q = request.query.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    pipeline = get_pipeline()
    try:
        result = pipeline.ask(
            question=q,
            top_k=request.top_k,
            filter_dict=request.filter_dict,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auditor Pipeline Error: {str(e)}")


@app.post("/api/upload")
async def upload_documents(files: list[UploadFile] = File(...)):
    """
    Uploads new 10-K / 10-Q PDF documents and indexes them.
    """
    docs_dir = Path(DOCS_PATH)
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    saved_files = []
    for upload in files:
        if not upload.filename.endswith(".pdf"):
            continue
        dest_path = docs_dir / upload.filename
        with open(dest_path, "wb") as f:
            shutil.copyfileobj(upload.file, f)
        saved_files.append(upload.filename)

    if not saved_files:
        raise HTTPException(status_code=400, detail="No valid PDF files provided.")

    # Trigger ingestion
    pipeline = get_pipeline()
    try:
        summary = pipeline.ingest_documents(force_reload=False)
        return {
            "status": "success",
            "uploaded_files": saved_files,
            "ingestion_summary": summary,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 70)
    print("STARTING FINANCIAL AI AUDITOR SERVER")
    print("Open your browser at: http://127.0.0.1:8000")
    print("=" * 70 + "\n")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
