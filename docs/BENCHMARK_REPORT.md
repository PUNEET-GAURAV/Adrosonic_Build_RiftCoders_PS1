# Benchmark Report — TrustRAG

> Generated from `results/` only. Every number traces to a committed result file.

## Retrieval quality

| Mode | Context Precision | Context Recall | P@5 | R@5 | MRR@10 | nDCG@10 |
|---|---|---|---|---|---|---|
| dense | 0.5968333333333333 | 2.09 | 0.17999999999999972 | 0.885 | 0.5943333333333335 | 0.666620693076741 |
| sparse | — | — | — | — | — | — |
| hybrid | 0.6068055555555556 | 2.055 | 0.1859999999999997 | 0.915 | 0.6380000000000002 | 0.7067985186848007 |
| hybrid_rerank | 0.6068055555555556 | 2.055 | 0.1859999999999997 | 0.915 | 0.6380000000000002 | 0.7067985186848007 |

## Latency (100 consecutive queries, HTTP API)

| Mode | n | p50 (ms) | p95 (ms) | p99 (ms) | max (ms) |
|---|---|---|---|---|---|
| dense | 100 | 27.27 | 42.28 | 48.36 | 49.15 |
| hybrid | 100 | 42.98 | 75.03 | 78.34 | 82.89 |
| hybrid_rerank | 100 | 109.15 | 138.94 | 258.91 | 265.67 |
| — | — |

## Methodology

- Eval set: seed-42 pool (dev 200 / test 400), MS MARCO validation queries with a selected passage.
- Tuned only on dev; reported numbers are on the held-out test split.
- RAGAS: LLM-judged (Groq free tier, temperature 0) and non-LLM (token overlap) variants.
- Official p95: hybrid mode, cache off, 100 distinct queries, idle machine.
