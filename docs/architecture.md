# Architecture — TrustRAG

## Design principles
1. **The API is the product.** UI, benchmark runner, eval harness and MCP clients are all clients of the same service.
2. **Ports and adapters.** `core/` defines interfaces and imports no vendor SDK; `adapters/` implements them. The store is swappable.
3. **One store, one truth.** Dense + BM25 sparse + payload on one Qdrant point.
4. **Config over constants.** Behaviour from `configs/*.yaml`, overridable per request, hashed into every result.
5. **Measure every stage.** Every response carries `timings_ms`.
6. **Fail soft.** Reranker, cache and LLM are optional; each degrades gracefully.
7. **Reproducible.** Pinned deps, seeded splits, resumable ingestion, snapshot restore.

## System context

```mermaid
flowchart LR
  U["Analyst / Judge"] -->|"query + filters"| UI["Streamlit control room"]
  UI --> API["FastAPI retrieval service"]
  API --> Q[("Qdrant: dense + BM25 sparse + payload")]
  API -. optional .-> LLM["Groq free-tier LLM"]
  ING["Ingestion CLI"] --> Q
  HF["HuggingFace: MS MARCO + models"] --> ING
  EVAL["Eval + benchmark runner"] --> API
  EVAL --> RES[("results: json + csv")]
  RES --> UI
```

## Query path (components)

```mermaid
flowchart TB
  subgraph SVC["FastAPI service"]
    R["Router: search, answer, documents, metrics"] --> ORCH["Retrieval orchestrator"]
    ORCH --> CH{"Cache hit?"}
    CH -- "yes" --> OUT["Top-k + scores + timings"]
    CH -- "no" --> EMB["Dense embedder: BGE-small"]
    CH -- "no" --> SPE["Sparse encoder: BM25"]
    EMB --> PD["search_dense (filter inside)"]
    SPE --> PS["search_sparse (filter inside)"]
    PD --> FUS["Client-side fusion (RRF/weighted/DBSF)"]
    PS --> FUS
    FUS --> RR{"hybrid_rerank?"}
    RR -- "yes" --> CE["Cross-encoder: top-30 to top-5"]
    RR -- "no" --> OUT
    CE --> OUT
  end
```

## Repository layout

```
trustrag/
├── configs/            # retrieval.yaml, models.yaml, eval.yaml
├── src/trustrag/
│   ├── core/           # models, ports, fusion, ids, text, cache_key (no vendor SDK)
│   ├── adapters/       # qdrant_store, st_embedder, bm25_sparse, ce_reranker,
│   │                   #   groq_generator, memory_cache, in_memory_store
│   ├── ingestion/      # msmarco_loader, eval_set, enrich, pipeline, upload
│   ├── retrieval/      # orchestrator, filters, explain
│   ├── answering/      # answerer (evidence gate, citations, abstention)
│   ├── evaluation/     # metrics, ragas_runner, evaluator, benchmark, report
│   ├── api/            # FastAPI app + schemas
│   ├── ui/             # Streamlit control room
│   └── cli.py          # trustrag <command>
├── tests/              # unit tests (pure-logic modules)
├── data/eval/          # committed eval_queries.jsonl (seed 42)
├── results/            # committed result json/csv
└── docs/               # PRD, architecture, ADRs, BUSINESS_CASE, DEMO, STATUS
```

## Latency budget (planning estimates — measured in `results/`)

| Stage | Budget |
|---|---|
| Dense query encode (CPU) | ≤ 40 ms |
| BM25 query encode | ≤ 5 ms |
| Dense + sparse queries (2 × 50, filters inside) | ≤ 60 ms |
| Fusion (client-side) | ≤ 5 ms |
| API + serialisation (localhost) | ≤ 15 ms |
| **Hybrid total (target p95)** | **≤ 150 ms** |
| Cross-encoder rerank, 30 pairs (CPU) | ≤ 130 ms |
| **Hybrid + rerank total (target p95)** | **≤ 280 ms** (official limit 300 ms) |

## Decisions

All 12 architecture decisions are recorded in [`docs/adr/`](adr/).

## Banking Intent Router

```mermaid
flowchart TB
  Q[User Query] --> R[Lexical Intent Router]
  R -->|High Confidence| H[Hard Strategy: Filter to domain]
  R -->|Medium Confidence| S[Soft Strategy: Filter to top 2 domains]
  R -->|Low Confidence| F[Fallback: Global Hybrid Search + Needs Clarification]
  H --> Qdrant
  S --> Qdrant
  F --> Qdrant
```
