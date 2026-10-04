# Judge Q&A — honest answers grounded in this repo

Delete any answer you cannot back up. Every technical claim below maps to a file in this
repo (ADR, test, or `results/`).

## Evaluation & quality

1. **How do you know hybrid is better, not lucky?**
   Same held-out test queries, same top-5, tuned only on the dev split (200). We report
   LLM-judged RAGAS, non-LLM RAGAS, and classical IR (Hit@5, P@5, R@5, MRR@10, nDCG@10),
   all logged with git SHA + config hash in `results/`. (ADR-009)

2. **Did you tune on the test set?** No. Dev (200) for every sweep; test (400) only for
   reported numbers; `data/eval/eval_queries.jsonl` is committed and never regenerated.

3. **RAGAS depends on an LLM judge — can we trust it?** That's why we also report non-LLM
   RAGAS and IR metrics on gold labels for all 400 test queries. The LLM judge runs at
   temperature 0 and is only one of three families.

4. **MS MARCO has very sparse relevance labels — doesn't that distort precision?**
   Yes, most queries have one or few labelled passages, so strict P@5 is bounded. We lean
   on Hit@5, MRR, nDCG and RAGAS's graded judging, and say so.

5. **What didn't work?** Client-side fusion costs one extra round-trip vs server-side RRF
   (ADR-004); our BM25 uses hashed token indices rather than a learned vocabulary (ADR-002).
   Naming real trade-offs is a strength.

## Architecture

6. **Why Qdrant and not pgvector/Chroma?** ADR-001: dense + sparse on one point, payload
   indexes, quantization, snapshots; the store sits behind a port so a pgvector adapter
   can be added without touching the core.

7. **Why BM25-as-sparse and not `rank_bm25`?** ADR-002: Qdrant computes IDF server-side over
   the live corpus, so upserts/deletes keep statistics current, and the same filter applies
   to the sparse leg. An external in-memory index would break both.

8. **Why client-side fusion, not the Qdrant Query-API RRF?** ADR-004: portable across
   `qdrant-client` versions, deterministic, unit-testable offline, and it yields per-leg
   rank/score for explain mode for free. Filters are still applied *inside* each query.

9. **How do you know filters are pre-retrieval?** The filter is translated to a Qdrant
   `Filter` and passed into *each* dense and sparse query (ADR-005). The selective-filter
   test proves a filter matching ≈0.1% of the corpus still returns a full top-5.

10. **Cache staleness after an update?** The cache key includes `index_version`; every
    upsert/delete bumps it (ADR-011). There's a proof test.

## Performance & scale

11. **p95 under concurrency?** The brief specifies 100 *consecutive* queries and we measure
    exactly that (cache off, HTTP API, idle machine). Concurrency is *not* measured; here's
    the plan if asked: a small concurrent sweep, reported separately.

12. **What breaks at 10M passages?** Memory and index build. Levers: int8 scalar
    quantization (with measured recall/RAM trade-off), on-disk vectors, sharding. Measured
    scale curve 10k → 100k → 500k is the honest answer.

## Trust & business

13. **Do you eliminate hallucination?** No. We improve evidence quality, abstain on weak
    evidence, and validate that every `[n]` citation maps to a returned passage. Reduced and
    measured, not eliminated.

14. **Data privacy?** Self-hosted store, retrieval-only mode, optional local LLM; only the
    query and retrieved passages ever go to the free LLM API, and only if enabled.

15. **Why Adrosonic, and who pays?** Insurance/banking clients need provable accuracy and
    governance; Adrosonic monetises delivery, integration and managed service (it already
    delivers Microsoft Power Platform — see `docs/BUSINESS_RESEARCH.md`). The accelerator
    cuts cost/risk of every RAG engagement.

16. **Where's the market number?** We don't quote one we can't source. Here's the bottom-up
    structure and the two inputs we validated with mentors; the rest is `[VERIFY]`.

17. **How does it plug into Microsoft platforms?** REST + OpenAPI (FastAPI) is the natural
    starting point for a Power Platform custom connector — *designed for*, tested only if
    time allows.
