# AGENTS.md — rules for the coding agent (TrustRAG)

You are building **TrustRAG** for the ADROSONIC Build 24-hour hackathon. The full spec is `docs/PRD.md`. The original problem statement is `docs/problem_statement.pdf`. If they ever disagree, the problem statement's mandatory constraints (C-01 … C-07) win.

## Non-negotiables
1. **Free tier only.** No paid API, no paid GPU. The repo must run with no paid key. A Groq key is optional; without it the system falls back to extractive answers and non-LLM evaluation.
2. **No fabricated numbers.** Never state a metric, latency, throughput or count unless a logged run produced it. Every reported number must trace to a file in `results/` (with timestamp, git SHA and config hash). If something fails or underperforms, say so plainly.
3. **No secrets in git.** Keys come from the environment. Maintain `.env.example` with empty values. Never print keys in logs.
4. **Evaluation discipline.** `data/eval/eval_queries.jsonl` is generated once (seed 42) and committed. Tune only on the **dev** split. Touch the **test** split only for reported numbers. Phase 1 and Phase 2 use identical queries and `top_k = 5`.
5. **Benchmark hygiene.** Never run the latency benchmark while ingestion or other heavy jobs are running. The official p95 is: `hybrid` mode, cache off, 100 distinct queries, through the HTTP API.
6. **Phase 1 baseline is sacred.** Tag `phase1-baseline` before any hybrid code is merged. Never edit baseline results after the tag.

## Architecture rules
- Ports and adapters. `src/trustrag/core/` holds domain models and interfaces and **imports no vendor SDK**. Vendor code (Qdrant, sentence-transformers, Groq) lives only in `adapters/`.
- Behaviour comes from `configs/*.yaml`, overridable per request, and the config hash is written into every result.
- Every API response carries `timings_ms` per stage.
- Optional components (rerank, cache, LLM) must degrade gracefully, never crash the request.
- Point IDs are deterministic UUIDv5 of `passage_id`; ingestion is idempotent and resumable.
- Filters go **inside every prefetch** so they are applied before fusion. Prove it with the selective-filter test.
- Any cache key includes query, mode, filters, user groups and `index_version`; every upsert/delete bumps `index_version`.

## Engineering rules
- Python 3.11+, type hints, `ruff` clean, pinned dependencies.
- Small commits with clear messages (`feat:`, `fix:`, `docs:`, `test:`, `perf:`, `chore:`).
- Write the test first for logic that has a clear contract (fusion, filters, cache invalidation, citation check, metrics math).
- **Verify third-party APIs against the installed version** before using them. `qdrant-client`, `ragas`, `streamlit` and the Groq SDK change between versions.
- Prefer boring and readable over clever. A judge must be able to follow the code in five minutes.

## Working protocol
- Work **one phase at a time**. At the start of each phase: list the skills you loaded (name and path), write a short task list with a verification step for each task.
- At the end of each phase: run the verification commands and show real output; update `docs/STATUS.md`; commit and tag; then **stop and report in at most 15 lines**.
- If blocked or if a requirement is ambiguous, ask one precise question rather than guessing silently.

## Definition of done (per phase)
Code runs from a clean shell using documented commands, tests pass, `docs/STATUS.md` is current, results (if any) are written to `results/`, and the work is committed and tagged.
