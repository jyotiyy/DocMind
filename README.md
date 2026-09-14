# DocMind — Private, Offline RAG Document Q&A

DocMind is a private Retrieval-Augmented Generation (RAG) system that lets you upload
PDF documents and ask natural-language questions answered **strictly from the content
of those documents**. It runs entirely offline once models are downloaded — your
documents and questions never leave your machine.

---

## Features

- 📄 **Multi-PDF upload** with automatic scanned-page detection and OCR fallback
- ✂️ **Semantic chunking** that preserves section headers and page numbers
- 🧠 **Local embeddings** via `sentence-transformers/all-MiniLM-L6-v2`
- 🔍 **FAISS vector search** with persistent, on-disk indexes
- 🎯 **Cross-encoder reranking** (`cross-encoder/ms-marco-MiniLM-L-6-v2`) for precision
- 🤖 **Local LLM generation** via [Ollama](https://ollama.com) (`llama3.1:8b`), with
  a strict grounding prompt that refuses to answer beyond the retrieved context
- 📊 **Confidence scoring** combining retrieval + rerank signals
- 📌 **Page-level citations** for every answer
- 🗑️ **Document management** — list, delete, and rebuild the index on demand
- 💬 **Streaming chat UI** built with React, Vite, TypeScript, and Tailwind

---

## Architecture

```
                     ┌─────────────────────────┐
                     │        Frontend          │
                     │  React + Vite + TS + TW   │
                     └────────────┬─────────────┘
                                  │ REST / SSE
                     ┌────────────▼─────────────┐
                     │        FastAPI            │
                     │  routers / services /     │
                     │  schemas / core / utils    │
                     └────────────┬─────────────┘
             ┌────────────────────┼────────────────────┐
             ▼                    ▼                     ▼
     PDF Parser + OCR     Chunker + Embedder      FAISS Vector Store
     (PyMuPDF, Tesseract) (SentenceTransformers)   (persistent, on disk)
             │                    │                     │
             └────────────────────┴─────────┬───────────┘
                                             ▼
                                  Retriever → Reranker
                                  (cross-encoder)
                                             ▼
                                        Ollama LLM
                                  (grounded generation)
```

### Retrieval pipeline

```
Question → Query Embedding → FAISS Top-10 → Cross-Encoder Rerank → Top-5 → Context → LLM
```

### Folder structure

```
docmind/
├── backend/
│   ├── app/
│   │   ├── routers/       # upload, ask, documents, health
│   │   ├── services/      # pdf_parser, ocr, chunker, embedding, vector_store,
│   │   │                  # retriever, reranker, llm, confidence, citation,
│   │   │                  # document_manager
│   │   ├── schemas/       # request, response, document (Pydantic models)
│   │   ├── core/          # config, logging, exceptions
│   │   ├── utils/         # file_utils, text_utils
│   │   ├── dependencies/  # FastAPI DI accessors
│   │   └── main.py
│   ├── data/uploads/      # stored PDFs
│   ├── indexes/           # FAISS index + JSON metadata/registry
│   ├── tests/             # pytest suite
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/    # Sidebar, PDFUploader, ChatWindow, MessageBubble,
│   │   │                  # CitationCard, ConfidenceBadge, LoadingIndicator, EmptyState
│   │   ├── pages/          # HomePage, ChatPage
│   │   ├── hooks/          # useDocuments, useChat
│   │   ├── services/       # api.ts (Axios layer)
│   │   └── types/          # api.ts (TypeScript interfaces)
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Screenshots

> _Add screenshots here once the app is running locally:_
>
> - `docs/screenshots/home.png` — landing page with uploader
> - `docs/screenshots/chat.png` — chat view with citations and confidence badge
> - `docs/screenshots/sidebar.png` — document management sidebar

---

## Installation

### Prerequisites

- Python 3.12+
- Node.js 20+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed and on `PATH`
- [Ollama](https://ollama.com) installed, with the model pulled:
  ```bash
  ollama pull llama3.1:8b
  ```

### Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`, with interactive docs at
`http://localhost:8000/docs`.

### Frontend setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The UI will be available at `http://localhost:5173`.

---

## Running with Docker

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

This starts three services:

| Service    | Port  | Description                          |
|------------|-------|---------------------------------------|
| `ollama`   | 11434 | Local LLM runtime                     |
| `backend`  | 8000  | FastAPI RAG API                       |
| `frontend` | 3000  | Nginx-served React app (proxies /api) |

After the stack is up, pull the model into the Ollama container once:

```bash
docker exec -it docmind-ollama ollama pull llama3.1:8b
```

---

## Running tests

```bash
cd backend
pytest -v --cov=app
```

The suite covers upload validation, OCR routing, chunking, embeddings,
retrieval/reranking, and the `/ask` endpoint (with Ollama mocked out so no
live model is required for CI).

---

## API documentation

Base URL: `/api/v1`

### `POST /upload`
Upload one or more PDFs (multipart `files[]`). Runs the full ingestion
pipeline (parse → OCR if needed → chunk → embed → index) synchronously and
returns per-document stats.

### `POST /ask`
```json
{
  "question": "What are the key findings in chapter 3?",
  "document_ids": null,
  "top_k": null,
  "stream": false
}
```
Returns an answer grounded in retrieved chunks, with citations and a
confidence score. Set `"stream": true` to receive Server-Sent Events
(`event: token` for incremental text, `event: done` for citations/confidence).

### `GET /documents`
Lists all indexed documents with page/chunk counts and OCR stats.

### `DELETE /documents/{id}`
Deletes a document's file, vectors, and registry entry.

### `POST /reindex`
```json
{ "document_ids": null }
```
Rebuilds vectors for the given documents, or all documents if omitted.

### `GET /health`
Reports service status, Ollama reachability, and model load state.

---

## Future improvements

- Async/background ingestion queue for large batch uploads
- Hybrid search (BM25 + dense) for better keyword-heavy queries
- Multi-turn conversational memory with follow-up question rewriting
- Per-document access control and multi-user workspaces
- Support for additional file types (DOCX, TXT, HTML)
- Swap FAISS for a server-based vector DB (Qdrant/pgvector) for larger corpora
- Answer caching keyed on (question, document set) hash
