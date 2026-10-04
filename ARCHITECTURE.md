# Architecture

```mermaid
graph TD
    %% User Interfaces
    subgraph UI [User Interfaces]
        Web[Web Dashboard UI]
        API[FastAPI HTTP Interface]
    end

    %% API Gateway & Routing
    subgraph Gateway [API Gateway]
        Router[Retrieval Orchestrator]
    end

    %% Search Pipelines
    subgraph Pipelines [Search Pipelines]
        Dense[Phase 1: Dense Retrieval<br/>all-MiniLM-L6-v2]
        Hybrid[Phase 2: Hybrid Search<br/>Dense + BM25 Sparse]
        Rerank[Phase 3: Cross-Encoder Reranker<br/>bge-reranker-base]
    end

    %% Vector Database
    subgraph Database [Vector Database]
        Qdrant[(Qdrant Vector DB<br/>Local Async instance)]
    end

    %% Ingestion
    subgraph Ingestion [Ingestion Pipeline]
        Parser[Data Parsers<br/>MS MARCO + Custom]
        Embed[ONNX FastEmbed<br/>Text -> Dense + Sparse]
    end

    %% Edges
    Web --> API
    API --> Router
    Router --> Dense
    Router --> Hybrid
    Router --> Rerank

    Dense --> Qdrant
    Hybrid --> Qdrant
    
    Qdrant --> Rerank
    Rerank --> Router

    Parser --> Embed
    Embed --> Qdrant
```

## System Components
1. **Frontend**: Standalone HTML/JS dashboard `index.html` communicating with the backend.
2. **Backend**: FastAPI web server (`app.py`) providing `/search` and `/stats` endpoints.
3. **Retrieval Orchestrator**: Manages dense, sparse, and reranking pipelines. Automatically routes queries.
4. **Vector Store**: Qdrant engine running locally, holding 100k+ passages with dual-vectors (Dense + Sparse) for hybrid search.
5. **Models**: Local ONNX runtimes of `all-MiniLM-L6-v2` (Dense) and `bge-reranker-base` (Cross-encoder).
