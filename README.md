# Financial AI Auditor

An AI-powered system for analyzing financial filings using Retrieval-Augmented Generation (RAG), layout-aware document parsing, and evidence-grounded answer generation.

Financial AI Auditor addresses hallucinations in financial question answering by combining document structure understanding, evidence retrieval, and grounded response generation over SEC financial filings.

> **Team Project:** This project is being developed collaboratively as a two-member team project. Both contributors are actively involved in the design, implementation, experimentation, and future development of the system.

---

## Features

- Layout-aware PDF extraction using PyMuPDF
- Table extraction from financial filings
- Font and layout metadata preservation
- Header detection for document structure understanding
- Section-aware chunking
- ChromaDB vector database
- HuggingFace embedding models
- Modular retrieval pipeline
- Citation-aware prompting
- Extensible verification framework

---

## Project Architecture

```
Financial-AI-Auditor
│
├── core
│   ├── pdf
│   │   ├── parser.py
│   │   └── header_detector.py
│   │
│   ├── chunking
│   │   ├── preprocessor.py
│   │   ├── section_detector.py
│   │   ├── chunk_builder.py
│   │   └── service.py
│   │
│   ├── retrieval
│   │   ├── embedding.py
│   │   ├── vector_store.py
│   │   └── retriever.py
│   │
│   ├── llm
│   │   ├── client.py
│   │   ├── prompts.py
│   │   ├── citation_prompt.py
│   │   └── service.py
│   │
│   ├── verification
│   │   └── verifier.py
│   │
│   ├── config.py
│   └── pipeline.py
│
├── docs
├── db
├── experiments
├── README.md
└── requirements.txt
```

---

## Current Pipeline

```
Financial Filing
        │
        ▼
PDF Extraction
        │
        ▼
Header Detection
        │
        ▼
Section-aware Chunking
        │
        ▼
Embedding Generation
        │
        ▼
Vector Database
        │
        ▼
Retrieval Pipeline
        │
        ▼
LLM Response Generation
        │
        ▼
Citation & Verification
```

---

## Tech Stack

### Language

- Python

### Document Processing

- PyMuPDF

### Embeddings

- BAAI/bge-base-en-v1.5

### Vector Database

- ChromaDB

### LLM Framework

- LangChain

### Environment

- Python 3.12+
- Virtual Environment

---

## Repository Structure

| Folder | Purpose |
|---------|----------|
| `core/pdf` | PDF parsing and document extraction |
| `core/chunking` | Section-aware chunk generation |
| `core/retrieval` | Embeddings, vector store and retrieval |
| `core/llm` | Prompt engineering and LLM interaction |
| `core/verification` | Hallucination verification |
| `experiments` | Incremental development experiments |
| `docs` | Sample financial filings |

---

## Current Status

### Completed

- Layout-aware PDF parsing
- Table extraction
- Initial header detection
- Document preprocessing
- Section-aware chunking
- Embedding pipeline
- ChromaDB integration
- Retrieval pipeline
- Modular project architecture

### In Progress

- Improving header detection robustness for complex financial layouts

### Planned

- Cross-Encoder reranking
- NLI-based hallucination detection
- Evidence verification
- Financial citation grounding
- Multi-document reasoning
- Agentic retrieval workflow
- Support for quarterly filings (10-Q)
- Full-stack web application interface

---

## Installation

Clone the repository

```bash
git clone https://github.com/<username>/financial-ai-auditor.git
```

Create a virtual environment

```bash
python -m venv .venv
```

Activate it

Linux / macOS

```bash
source .venv/bin/activate
```

Windows

```bash
.venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

## Example Documents

The repository includes publicly available SEC filings for experimentation.

- Apple 10-K
- Tesla 10-K

---

## Future Improvements

- Layout-aware section reconstruction
- Hybrid BM25 + Dense Retrieval
- Cross-Encoder reranking
- Financial claim verification
- Multi-document reasoning
- Agentic retrieval workflow
- Support for quarterly filings (10-Q)
- Full-stack web application

---

## Team

This project is collaboratively developed by:

- **Ayush Mukati**
- **Nitu Patidar**

Both contributors participate in the research, system design, implementation, experimentation, and evaluation of the project.

---
