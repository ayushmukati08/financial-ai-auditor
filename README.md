# Financial AI Auditor

An AI-powered system for analyzing complex SEC financial filings (10-K / 10-Q) using layout-aware document extraction, hybrid retrieval (Dense + BM25 + Cross-Encoder), and citation-grounded answer synthesis.

Financial AI Auditor addresses the critical challenge of numerical and tabular hallucinations in financial question answering by combining bounding-box table extraction, statistical rank fusion, neural reranking, and sentence-level source citations.

> **Team Project:** Developed collaboratively as a two-member team project by **Ayush Mukati** and **Nitu Patidar**. Both contributors actively participated in the system architecture, mathematical retrieval design, experimentation, and full-stack implementation.

---

## Key Features

- **Universal Layout & Table Extraction**: Uses PyMuPDF with coordinate bounding-box alignment to extract complex, multi-column financial statements while preserving tabular relationships and Markdown grids.
- **Section-Aware Chunking**: Detects SEC Item and Note boundaries, generating table-atomic chunks and sliding paragraph chunks without splitting tables across vector boundaries.
- **Two-Stage Hybrid Retrieval**:
  - **Stage 1 (Parallel Recall Pool)**: Dense Semantic Search (`BAAI/bge-base-en-v1.5`) + Lexical Search (`BM25Okapi`).
  - **Reciprocal Rank Fusion (RRF)**: Merges lexical and dense candidate pools using $RRF(d) = \sum \frac{1}{k + r(d)}$ with $k=60$.
  - **Stage 2 (Neural Precision)**: Neural Cross-Encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`) scoring and ranking the Top 5 evidence chunks.
- **Citation-Enforced Synthesis**: Grounded responses via Google Gemini (`gemini-3.5-flash`) with inline citation tags (`[C1]`, `[C2]`) mapped directly to source document, section, and page numbers.
- **Interactive Web Dashboard**: Full-stack FastAPI web application with responsive UI, live citation inspector modal, chat history, and drag-and-drop 10-K upload.
- **Domain-Agnostic & Zero-Heuristic**: No hardcoded financial dictionaries or artificial rule-based hacks; driven purely by statistical and neural ranking.

---

## System Architecture

```
                                  SEC 10-K / 10-Q PDF
                                           │
                                           ▼
                             Universal PDF Table & Text Parser
                                           │
                                           ▼
                               SEC Section & Note Detector
                                           │
                                           ▼
                              Structure-Aware Chunking
                            (1,100 High-Fidelity Chunks)
                                           │
                                           ▼
                                 ChromaDB Vector Store
                                (BAAI/bge-base-en-v1.5)
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ↓                                             ↓
             Dense Retrieval                               BM25 Retrieval
          (Top 20 Semantic BGE)                         (Top 20 Lexical Okapi)
                    └──────────────────────┬──────────────────────┘
                                           ↓
                              Reciprocal Rank Fusion (RRF)
                                           │
                                           ▼
                                 Top 20 Candidate Pool
                                           │
                                           ▼
                                 Cross-Encoder Reranker
                         (cross-encoder/ms-marco-MiniLM-L-6-v2)
                                           │
                                           ▼
                                 Top 5 Evidence Chunks
                              [C1], [C2], [C3], [C4], [C5]
                                           │
                                           ▼
                              Strict Financial Prompting
                                           │
                                           ▼
                                  Gemini 3.5 Flash LLM
                                           │
                                           ▼
                              Cited Answer & Evidence Modal
                               (FastAPI + Responsive Web UI)
```

---

## 25-Query Benchmark Evaluation

The retrieval architecture was evaluated on a comprehensive 25-query financial benchmark (16 complex table queries, 9 narrative queries) across Apple and Tesla 10-K filings:

| Pipeline Architecture | Hit@1 (Rank 1) | Recall@5 (Top 5) | Table Recall@5 | Text Recall@5 |
| :--- | :---: | :---: | :---: | :---: |
| **Dense Only (`bge-base`)** | 28.0% (7/25) | 68.0% (17/25) | 56.2% (9/16) | 88.9% (8/9) |
| **Dense + Cross-Encoder** | **52.0% (13/25)** | 80.0% (20/25) | 75.0% (12/16) | 88.9% (8/9) |
| **BM25 + Dense + RRF + Cross-Encoder** | 48.0% (12/25) | **84.0% (21/25)** | **81.2% (13/16)** | **88.9% (8/9)** |

*Key Takeaway: Adding Lexical BM25 via Reciprocal Rank Fusion increased Table Recall@5 from 75.0% to 81.2% (+6.2 percentage points) without any handcoded financial dictionaries.*

---

## Tech Stack

- **Backend / Web API**: FastAPI, Uvicorn, Pydantic, Python 3.12+
- **Document Processing**: PyMuPDF (`fitz`), LangChain Text Splitters
- **Dense Embeddings**: `BAAI/bge-base-en-v1.5` via HuggingFace / Sentence-Transformers
- **Lexical Search**: Custom Pure-Python `BM25Okapi` ($k_1=1.5, b=0.75$)
- **Reranker**: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- **Vector Database**: ChromaDB
- **LLM Synthesis**: Google GenAI SDK (`gemini-3.5-flash`)
- **Frontend**: Responsive HTML5, CSS3, JavaScript (Fetch API, Marked.js)

---

## Project Structure

```
financial-ai-auditor/
│
├── core/
│   ├── chunking/
│   │   ├── chunk_builder.py       # Table-atomic and text chunk builder
│   │   ├── preprocessor.py        # Margin & span cleaner
│   │   ├── section_detector.py    # SEC Item / Note header detection
│   │   └── service.py             # Section building orchestrator
│   │
│   ├── llm/
│   │   ├── citation_prompt.py     # Auditor system prompt & citation blocks
│   │   ├── client.py              # Gemini client configuration
│   │   └── service.py             # Answer generation & error handling
│   │
│   ├── pdf/
│   │   ├── header_detector.py     # Font & size header heuristics
│   │   └── parser.py              # Universal bounding-box table parser
│   │
│   ├── retrieval/
│   │   ├── bm25.py                # Pure-Python BM25Okapi retriever
│   │   ├── embedding.py           # HuggingFace BGE embeddings
│   │   ├── reranker.py            # Neural Cross-Encoder sentence-pair scorer
│   │   ├── retriever.py           # Hybrid Dense+BM25+RRF orchestrator
│   │   └── vector_store.py        # ChromaDB collection management
│   │
│   ├── config.py                  # Project paths and hyperparameters
│   └── pipeline.py                # End-to-end FinancialAIAuditorPipeline class
│
├── docs/                          # Sample SEC filings (Apple 10-K, Tesla 10-K)
│   ├── apple_10k.pdf
│   └── tesla_10K.pdf
│
├── experiments/                   # Progressive evaluation & milestone scripts
│   ├── step1_llm_call.py
│   ├── step2_context_injection.py
│   ├── step3_pdf_extraction.py
│   ├── step4_chunking.py
│   ├── step5_embeddings.py
│   ├── step6_similarity_search.py # 25-Query 3-Way Benchmark
│   └── step7_rag_loop.py          # End-to-end RAG with citations
│
├── web/                           # Interactive Web UI
│   ├── static/
│   │   ├── script.js              # Citation modal, chat streaming, file uploads
│   │   └── style.css              # Responsive dark/light theme & source cards
│   └── templates/
│       └── index.html             # Main dashboard template
│
├── .env.example                   # Environment configuration template
├── .gitignore                     # Production Git ignore rules
├── app.py                         # FastAPI server entrypoint
├── requirements.txt               # Project dependencies
└── README.md
```

---

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/<username>/financial-ai-auditor.git
cd financial-ai-auditor
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root (copy from `.env.example`):
```env
GEMINI_API_KEY=your_actual_gemini_api_key
GEMINI_MODEL=gemini-3.5-flash
```

---

## Running the Application

### Launch the Web Dashboard
```bash
python app.py
```
Open your browser at: **`http://127.0.0.1:8000`**

### Run the 25-Query Retrieval Benchmark
```bash
python -m experiments.step6_similarity_search
```

### Run the End-to-End RAG Loop Test
```bash
python -m experiments.step7_rag_loop
```

---

## Team & Acknowledgements

- **Ayush Mukati**
- **Nitu Patidar**

*Developed for rigorous, verifiable financial auditing with zero numerical hallucinations.*
