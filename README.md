# DocMind — Your Open Notebook Assistant

DocMind is a private, fully offline Retrieval-Augmented Generation (RAG) document intelligence platform. It enables users to process, query, and analyze complex PDF documentation using locally deployed machine learning models. By performing processing, index generation, and inference locally on host hardware, DocMind eliminates external API dependencies and addresses data confidentiality, latency, and operational persistence concerns.

## System Overview

Organizations and researchers often handle sensitive internal documentation that cannot be processed via third-party cloud models due to data sovereignty and regulatory constraints. Standard search approaches also lack context-aware semantic retrieval and precise source attribution, leading to lower information extraction accuracy.

DocMind resolves these challenges through an end-to-end, on-premise pipeline:

* **Complete Data Privacy:** Ingestion, vector storage, and inference operate strictly within local environments.
* **Grounding & Precision:** Cross-encoder reranking coupled with deterministic prompt constraints mitigates model hallucinations by strictly anchoring answers to retrieved text.
* **Auditability:** Every generated response includes explicit, page-level citations to verify source facts directly within documents.
* **Document Ingestion:** Features automated fallback to Optical Character Recognition (OCR) for scanned PDFs and complex multi-column layouts.

```mermaid
flowchart TD
    subgraph Frontend [User Interface]
        UI[React + Vite + TypeScript]
    end

    subgraph Backend [FastAPI Application Server]
        API[API Routers]
        Ingest[PDF Parser & OCR Engine]
        Chunker[Semantic Chunker]
        Embedder[Local Embedding Engine]
        Retriever[Vector Search & Cross-Encoder]
        LLM[Ollama Local LLM]
    end

    subgraph Storage [Persistent Storage]
        PDFStore[(PDF File Storage)]
        VectorDB[(FAISS Vector Index)]
    end

    UI <-->|REST / SSE| API
    API --> Ingest
    Ingest --> PDFStore
    Ingest --> Chunker
    Chunker --> Embedder
    Embedder --> VectorDB
    API --> Retriever
    VectorDB --> Retriever
    Retriever --> LLM
    LLM --> API
