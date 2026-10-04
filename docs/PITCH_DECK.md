# Pitch Deck — TrustRAG (9 slides)

**Format:** 9 slides, one idea each. Every metric on a slide cites its `results/` file in the
speaker notes (replace `<…>` from the real run). Mapped to your three axes (architecture /
add-ons / business) **and** the official scorecard (30/20/20/20/10).

---

## Slide 1 — The problem (hook)
**Headline:** *"The model gets the blame. The retriever decides."*
**Body:** RAG is the standard way to put an LLM on private data. At scale, dense vector
search returns chunks that are *semantically similar but factually wrong* — and the LLM
turns that into a fluent, confident wrong answer. In insurance, banking and compliance,
that's a trust-breaking, costly failure.

> **Speaker note:** label any illustrative "wrong answer" clearly. Sets up the *why*.
> Serves: demo/presentation (10%) — the desire-first arc.

## Slide 2 — The contrast (dense vs TrustRAG)
**Headline:** *Same query, two retrievers.*
**Body:** Side-by-side top-5 for one prepared query where naive dense returns a similar-but-
wrong passage and TrustRAG hybrid returns the correct one (from
`docs/examples_hybrid_vs_dense.md` / `results/`).

> **Speaker note:** one concrete before/after. Honest line: *"the baseline problem from the
> brief, made visible."* Serves: retrieval quality (30%) narrative.

## Slide 3 — Architecture (axis 1)
**Headline:** *One store. Ports and adapters. Measured at every stage.*
**Body:** `core/` defines interfaces and imports **no** vendor SDK; `adapters/` implements
Qdrant (dense + BM25 sparse + payload on one point), sentence-transformers, and Groq. The
store is swappable behind a port. Every response carries `timings_ms`. 12 ADRs + C4 diagrams
in `docs/`.

> **Speaker note:** this is the architecture-quality row (20%) — *show* the ports, not just
> say it. Point to `docs/adr/`. Serves: architecture axis + architecture quality (20%).

## Slide 4 — Hybrid search + filters (the core win)
**Headline:** *BM25 catches the exact term the embedding blurs; RRF fuses the two.*
**Body:** Dense + BM25 prefetch, **filter applied inside every query** (true pre-retrieval),
fused by RRF (configurable `k`/weights). Live upsert/delete with no re-index. Selective-
filter proof test returns a full top-5 at ≈0.1% selectivity.

> **Speaker note:** map to FR-3/FR-4/FR-5 and the 7-step demo beats 3 + 6. Serves:
> hybrid search (20%) + retrieval quality (30%).

## Slide 5 — Add-on features (axis 2)
**Headline:** *Each add-on earns its place with a measured number.*
**Body:** cross-encoder reranker (+Δ precision), latency-budget guard, query cache (with
`index_version` invalidation), grounded answers with `[n]` citations + abstention, live
RAGAS dashboard, 500k scale curve.

> **Speaker note:** the PDF's bonus list, each tied to a logged delta. Don't list — *show one
> measured lift*. Serves: add-ons axis + retrieval quality (30%).

## Slide 6 — Measured results (the proof)
**Headline:** *Ablation ladder + p95, all from committed logs.*
**Body:** dense → sparse → hybrid → hybrid+rerank: P@5 / R@5 / MRR@10 / nDCG@10 / RAGAS
CP & CR, plus `p95 < 300 ms` over 100 consecutive queries (cache off, HTTP API). Every number
traces to `results/`.

> **Speaker note:** the 30% + 20% rows live here. Say the *method* (dev/test split, no tuning
> on test) in one line. Serves: retrieval quality (30%) + performance (20%).

## Slide 7 — Business model (axis 3)
**Headline:** *A reusable, vendor-neutral retrieval accelerator — delivered by Adrosonic.*
**Body:** open-core + fixed-fee POC → integration (Power Platform / Dynamics 365) → managed
service + enterprise add-ons (SSO, permissions, audit). Unit economics from first principles
(memory/vector, cost-per-1k-queries from measured throughput) + ROI method with labelled
inputs. Insurance first.

> **Speaker note:** cite `docs/BUSINESS_RESEARCH.md` (Adrosonic = consultancy + Microsoft
> Power Platform + industries practice). *Never quote an invented market number.* Serves:
> business axis + demo (10%).

## Slide 8 — Live demo (7-step checklist)
**Headline:** *The judges' 7 steps, end to end.*
**Body:** live dense query → RAGAS baseline → hybrid on the same query → Phase 1 vs 2 side
by side → latency p95 → metadata-filtered query → GitHub repo + README.

> **Speaker note:** run the 10-min run-of-show from `docs/DEMO.md` §2. Keep the repo + tags
> on screen for step 7. Serves: demo (10%) — the whole checklist.

## Slide 9 — Close
**Headline:** *"We reduced ungrounded retrieval by <Δ> within <p95> ms — on free-tier tools."*
**Body:** strongest proof number + honest limitation (MS MARCO ≠ enterprise docs) + next
step: *"a two-week POC on your documents."*

> **Speaker note:** end on the number and the next step; people remember the end. Include the
> one honest limitation (judges reward it).

---

## One-line axis map (for your own prep)
- **Architecture (20%)** → Slides 3–4: ports/adapters, 12 ADRs, filter-in-prefetch, timings.
- **Add-ons (bonus §09)** → Slide 5: reranker, cache, answers, dashboard, 500k.
- **Business (your emphasis)** → Slide 7: accelerator + Adrosonic fit + first-principles economics.
- **Quality 30% + perf 20%** → Slide 6: ablation ladder + p95.
- **Demo 10%** → Slides 1, 8: hook + 7-step checklist.
