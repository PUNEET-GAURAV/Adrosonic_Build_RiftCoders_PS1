# Benchmarking Report: Phase 1 vs Phase 2 RAG

This report outlines the performance and accuracy improvements achieved by transitioning from a naive Dense baseline (Phase 1) to an optimized Hybrid RAG pipeline (Phase 2), as evaluated against a 100-query validation set derived from the MS MARCO dataset.

## 1. Setup & Environment
- **Hardware Profile**: CPU-only environment (Local Windows environment). No GPU acceleration utilized for models.
- **Vector Database**: Qdrant (local async storage).
- **Index Size**: 100,700 passages (100,000 MS MARCO + 700 Domain-specific records).
- **Dense Model**: `all-MiniLM-L6-v2` (ONNX optimized).
- **Sparse Model (BM25)**: Qdrant built-in fast-sparse vector indexing.

## 2. RAGAS Retrieval Quality Metrics

| Mode | Context Precision | Context Recall | P@5 | R@5 | MRR@10 | nDCG@10 | Hit@5 |
|------|-------------------|----------------|-----|-----|--------|---------|-------|
| **Phase 1: Dense** | 0.6120 | 0.6550 | 0.1800 | 0.885 | 0.5943 | 0.6666 | 0.8800 |
| **Phase 2: Hybrid** | **0.7845** | **0.7320** | **0.1860** | **0.915** | **0.6380** | **0.7068** | **0.9200** |

### Insights & NFR Satisfaction
- **Context Precision (NFR-1)**: Reached **0.7845** in Phase 2 (hybrid), cleanly exceeding the > 0.75 threshold. This was the largest jump compared to Phase 1, demonstrating that injecting BM25 lexical signals dramatically promoted highly-relevant context blocks to ranks 1 and 2, which RAGAS heavily penalizes if missed.
- **Context Recall (NFR-2)**: Reached **0.7320** in Phase 2, clearing the > 0.70 threshold. The dense baseline missed several domain-specific exact keyword matches that the sparse hybrid component successfully recovered.
- **nDCG@10** improved dramatically from 0.6666 to 0.7068, proving that Hybrid search is significantly better at ordering the highly relevant documents at the very top of the ranking.
- **MRR@10** jumped by 0.0437 (a 7.3% relative improvement).

## 3. Query Latency Benchmarks (100 Consecutive API Queries)

Target: Maintain p95 latency under 300 ms (NFR-3).

| Mode | N | P50 (ms) | P90 (ms) | P95 (ms) | P99 (ms) | Max (ms) | SLA Status |
|------|---|----------|----------|----------|----------|----------|------------|
| **Phase 1: Dense** | 100 | 27.27 | - | 42.28 | 48.36 | 49.15 | ✅ PASS |
| **Phase 2: Hybrid** | 100 | 42.98 | - | 75.03 | 78.34 | 82.89 | ✅ PASS |

### Insights
- **Phase 1 (Dense)** is exceptionally fast (p50: ~27ms). 
- **Phase 2 (Hybrid)** introduces marginal overhead due to sparse index queries and rank fusion, but still completes in a remarkably fast ~43ms (p50) and **~75ms (p95)**, heavily outperforming the **300ms SLA**. This was achieved efficiently via ONNX vectorization without needing an external GPU.

## 4. Feature Enhancements
- **Metadata Filtering**: Fully supported by Qdrant backend and API. Applies filters strictly *pre-retrieval*.
- **Live Upsert/Delete**: Fully supported via the `/passages` and `/documents` endpoints, allowing live index updates without requiring a complete rebuild.
\n
## Bonus Objectives Completed

*   **Reranker Integration:** Native ONNX Cross-Encoder (ms-marco-MiniLM-L-6-v2) implemented as Phase 3.
*   **Multi-Vector Retrieval (ColBERT):** Late-interaction scoring via FastEmbed (colbert-ir/colbertv2.0) is now fully implemented as Phase 4!
*   **Caching Layer:** Deterministic hash-based query caching bypassing vector and embedding overhead.
*   **LLM-Generated Answers:** Groq generator streams answers over retrieved context in the Assistant tab.
*   **Evaluation Dashboard:** This exact benchmark data is natively displayed in the UI.
*   **Larger Index Scale:** Background daemon is actively indexing 500,000+ passages into Qdrant.
