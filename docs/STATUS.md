# Status — <timestamp> — tag <tag>

## Works now
- Codebase complete: ports/adapters, hybrid retrieval, filters, live updates, answers, eval harness, benchmark, UI, CLI.
- Offline pure-logic checks pass (`python scripts/offline_check.py`).
- 12 ADRs, architecture.md, README written.

## Numbers so far (all from results/)
| Run | Mode | Split | P@5 / R@5 / MRR / nDCG | RAGAS CP / CR | p95 |
|---|---|---|---|---|---|
| (pending — run `trustrag ingest` then `trustrag eval` / `trustrag bench`) |

## Next 4 hours
1. `pip install -r requirements.txt`; `make up` (Qdrant).
2. `trustrag build-evalset`; `trustrag ingest --n 100000` (background).
3. `trustrag eval --mode dense --split test --judge non-llm`; tag `phase1-baseline`.
4. `trustrag eval --mode hybrid ...`; `trustrag bench --mode hybrid`.

## Risks
- qdrant-client / ragas API drift → verify installed versions before use.
- p95 budget → tune prefetch limits, `hnsw_ef`, ONNX encoder if over 300 ms.

## Decisions made (ADR links)
- See docs/adr/ADR-001 … ADR-012.
