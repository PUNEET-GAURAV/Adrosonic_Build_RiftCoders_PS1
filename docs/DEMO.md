# Demo, Pitch and Progressive-Evaluation Playbook

Everything here assumes the PRD (`01_PRD.md`) is being followed. Placeholders in `<angle brackets>` are filled from `results/` once the runs exist. **Never speak a number that is not in `results/`.**

---

## 1. Progressive-evaluation kit (use at every checkpoint)

You don't know when a progress check will come, so always be one minute away from a clean answer.

**Always keep ready**
1. `docs/STATUS.md` updated within the last milestone.
2. A tagged, runnable commit (`m0-foundation`, `phase1-demo`, `phase1-baseline`, `m3-hybrid-functional`, `phase2-measured`, `m4-addons-1`, `m5-answers-dashboard`, `m6-docs`, `m7-pitch`).
3. A 60-second live demo of *what is new since the last check*.
4. One screenshot per milestone in `docs/img/`.
5. A one-slide "state of play": what works, the best number so far, next 4 hours, top risk.

**`docs/STATUS.md` template**
```markdown
# Status — <timestamp> — tag <tag>
## Works now
- …
## Numbers so far (all from results/)
| Run | Mode | Split | P@5 / R@5 / MRR / nDCG | RAGAS CP / CR | p95 |
## Next 4 hours
1. …
## Risks
- …  (mitigation …)
## Decisions made (ADR links)
```

**What to show at each likely checkpoint**

| Checkpoint theme | Show |
|---|---|
| Architecture / design | `docs/architecture.md` diagrams, the ADR list, repo tree, ports-and-adapters explanation (60 s) |
| Phase 1 working | Dense query, top-5, scores, latency; ingestion log with count and wall-clock |
| Baseline logged | `results/ragas_dense_*.json`, `phase1-baseline` tag |
| Hybrid working | Same query dense vs hybrid; explain breakdown; filter proof test |
| Benchmark | Latency CSV, histogram, p95 badge, waterfall |
| Add-ons | Rerank lift, cache hit speed-up, abstention demo, dashboard |
| Business | Canvas, ROI method, GTM, validation quotes from mentors |

---

## 2. Ten-minute run-of-show (mapped to the judges' 7 steps)

Practise with a timer. If you run long, cut the add-on beat (7:00–7:45) first, never steps 1–7.

| Time | Beat | What you do | What you say (one line) |
|---|---|---|---|
| 0:00–0:45 | **Hook** | One slide: a confident wrong answer in an insurance workflow (label it *illustrative*) | "The model gets the blame; the retriever decides. Wrong evidence in, fluent wrong answer out." |
| 0:45–1:30 | **Architecture** | Architecture slide / `architecture.md` diagram | "One store holds dense, BM25 and metadata, so filters, updates and fusion stay consistent. The API is the product; everything else is a client." |
| 1:30–2:30 | **Step 1: live dense query** | Pick a query where dense returns a semantically similar but wrong passage; show top-5 with scores | "This is the baseline problem from the brief: similar, not correct." |
| 2:30–3:15 | **Step 2: RAGAS baseline** | Evaluation page: Phase 1 numbers, then open the JSON file | "These come from a logged run, tagged before any hybrid code existed." |
| 3:15–4:30 | **Step 3: hybrid in action** | Same query, hybrid mode; open Explain on the passage that moved up | "BM25 caught the exact term the embedding blurred; RRF fused the two ranks." |
| 4:30–5:15 | **Step 4: Phase 1 vs Phase 2** | Side-by-side deltas, then the ablation ladder (dense → sparse → hybrid → +rerank) | "Each component earns its place, measured on a held-out test split, tuned only on dev." |
| 5:15–6:00 | **Step 5: latency** | Benchmark page: 100-query histogram, p95 badge, waterfall | "p95 is <value> ms over 100 consecutive queries through the HTTP API, cache off." |
| 6:00–6:45 | **Step 6: filtered query** | Apply a highly selective filter; show full top-5 still returns, all matching; switch user role if AO-9 built | "The filter is inside both prefetches, so it applies before retrieval, not after." |
| 6:45–7:30 | **Add-ons** | Upsert a passage with a unique phrase, find it, delete it; ask an out-of-domain question and show the abstention; ask an answerable one and show citations | "No reindex. And when evidence is weak, it says so instead of guessing." |
| 7:30–8:30 | **Business** | Business slide: segment, value pillars, model, ROI method, GTM, mentor-validated theme | "Open accelerator, delivered and hardened by Adrosonic, insurance first." |
| 8:30–9:15 | **Step 7: repo** | GitHub page, README, tests, ADRs, snapshot restore, clean-clone claim | "Clone, restore the snapshot, run. We tested it on a fresh directory." |
| 9:15–10:00 | **Close** | Key idea, strongest proof number, honest limitations, next step | "We reduced ungrounded retrieval by <Δ> within <p95> ms. Next: prove it on client documents in a two-week POC." |

**Prepare in advance** (from `docs/examples_hybrid_vs_dense.md`): 3 queries where hybrid wins clearly, 1 query that ties, 1 where dense wins (shows honesty), 1 selective-filter query, 1 unique phrase for the upsert, 1 out-of-domain question for abstention, 1 answerable question for citations.

**Honest lines to say out loud (judges reward these)**
- "Category is MS MARCO's native query type; in an enterprise it would come from the source system."
- "Topic and permission labels are derived or synthetic and flagged in the data."
- "Our benchmark is MS MARCO. Enterprise documents are longer and structured, so the first step with a client is to measure on their own questions."
- "Hallucination is reduced and measured, not eliminated."

---

## 3. Three-minute business pitch arc (desire first, solution second)

Structure follows the `pitch-psychologist` skill: for a mixed technical/executive panel, lead with the risk and the evidence, then the outcome.

| # | Slide | Message | Evidence on the slide |
|---|---|---|---|
| 1 | **The world** | Teams are putting LLMs on private data; trust is the blocker | One sentence on the insurance workflow; label illustrative |
| 2 | **The cost of staying put** | Similar-but-wrong evidence causes confident wrong answers | Our own failing dense example from `results/` or `examples_hybrid_vs_dense.md` |
| 3 | **The contrast** | Naive dense vs TrustRAG on the same query | Side-by-side top-5 |
| 4 | **The bridge** | One store, hybrid + filters + rerank, governed and fresh | Architecture diagram |
| 5 | **The proof** | Precision/recall lift, p95, scale curve | Ablation ladder, p95 badge `[MEASURED]` |
| 6 | **Trust and control** | Permissions, citations, abstention, live updates | One screenshot each |
| 7 | **The business** | Accelerator → POC → managed service; ROI method; GTM through Adrosonic | Canvas + ROI formula + mentor-validated theme |
| 8 | **The close** | Key idea, proof, next step | "Two-week POC on your documents" |

Delivery rules: one idea per slide; every metric cites its `results/` file in the speaker notes; end on the proof number and the next step, because people remember the end.

---

## 4. Judge Q&A cheat sheet

Answers are written to be honest. Fill the `<…>` from real results and delete any answer you cannot back up.

**Evaluation and quality**
1. *How do you know hybrid is better, not lucky?* Same held-out test queries, same top-5, tuned only on a separate dev split; we report LLM-judged RAGAS, non-LLM RAGAS and classical IR metrics, all logged with git SHA and config hash. Deltas: `<…>`.
2. *RAGAS depends on an LLM judge. Can you trust it?* That's why we added non-LLM RAGAS and IR metrics on gold labels for all 400 test queries; they agree/disagree as follows: `<…>`.
3. *MS MARCO has very sparse relevance labels. Doesn't that distort precision?* Yes, most queries have one or very few labelled passages, so strict precision@5 is bounded; we lean on Hit@5, MRR, nDCG and RAGAS's graded judging, and we say so.
4. *Did you tune on the test set?* No. Dev (200) for every sweep; test (400) only for reported numbers; the eval file is committed and was never regenerated.
5. *What didn't work?* `<negative result, e.g. adaptive router or semantic-cache threshold>`. Naming one is a strength.

**Architecture**
6. *Why Qdrant and not pgvector or Chroma?* ADR-001: dense + sparse on one point, Query API with fusion, payload indexes, quantization, snapshots. The store sits behind a port; a pgvector adapter `<exists / is roadmap>`.
7. *Why BM25 inside Qdrant instead of `rank_bm25`?* ADR-002: IDF is computed server-side on the live corpus, filters apply to the sparse leg, and live upserts/deletes keep statistics correct. An external in-memory index would break both filtering and live updates.
8. *Why RRF?* Rank-based fusion avoids normalising incompatible score scales; `k` and weights were tuned on dev and are configurable.
9. *How do you know filters are pre-retrieval?* The filter is in each prefetch, and the selective-filter test returns a full top-5 at ≈0.1% selectivity, which post-filtering cannot guarantee.
10. *What happens to the cache after an update?* The key includes `index_version`; every upsert/delete bumps it; there's a proof test.

**Performance and scale**
11. *p95 under concurrency?* The brief specifies 100 consecutive queries and we measured exactly that: `<p95>`. Concurrency: `<measured value, or "not measured; here's the plan">`.
12. *What breaks at 10M passages?* Memory and indexing time. Levers: int8 quantization (measured recall/RAM trade-off `<…>`), on-disk vectors, sharding. Measured scale curve 10k → 100k → 500k: `<…>`.

**Trust and business**
13. *Do you eliminate hallucination?* No. We improve evidence quality, abstain on weak evidence (rate `<…>`) and validate citations (validity `<…>`).
14. *Data privacy?* Self-hosted store, retrieval-only mode, optional local LLM; only query + retrieved passages ever go to the free LLM API, and only if enabled.
15. *Who pays and why Adrosonic?* Insurance and banking clients need provable accuracy and governance; Adrosonic monetises delivery, integration and managed service; the accelerator cuts cost and risk of every engagement.
16. *How does it plug into Microsoft platforms?* REST + OpenAPI; a Power Platform custom connector is the natural route `<tested / designed for>`.
17. *Where's the market number?* We don't quote one we can't source; here's the bottom-up structure and the two inputs we validated with mentors.

---

## 5. Pre-demo checklist (T-30 minutes)

**Machine**
- [ ] On power, performance mode, notifications off, other apps closed
- [ ] Docker running; `docker ps` shows Qdrant; `/health` OK; collection count visible
- [ ] Models pre-loaded: run 3 warm-up queries in every mode
- [ ] Browser zoom 125–150%, light/dark theme chosen for the projector
- [ ] `.env` has a valid Groq key **and** extractive fallback verified with the key removed

**Content**
- [ ] `results/` has baseline, hybrid, rerank, latency, ablation files; dashboard renders from them
- [ ] Prepared queries copied into a text file (don't type from memory)
- [ ] Slides open; speaker notes cite `results/` files
- [ ] Backup screen recording of the full run-through saved locally
- [ ] `git tag` shows all milestone tags; GitHub repo public (or access granted) and README renders

**If something breaks**
| Failure | Fallback |
|---|---|
| Qdrant down | `docker compose up -d`; or restore the snapshot; or show the recording |
| LLM rate-limited | Switch to extractive answers (already automatic); say so |
| UI crash | Use `curl` against the API; show `results/` files directly |
| No internet | Everything core is local; skip the LLM beat |
| Out of time | Cut add-on beat, then business detail; never cut steps 1–7 |

---

## 6. Final 3-hour sprint order
1. **H21:** feature freeze. Run *Status audit* and *Cut scope* prompts.
2. **H21–H22:** `trustrag report`, README, clean-clone test, snapshot upload.
3. **H22:** code freeze. Run *Regression guard* and *Demo dry-run* prompts.
4. **H22–H23:** deck final; fill every `[MEASURED]` and resolve every `[VERIFY]` in the business case or delete the claim.
5. **H23–H24:** two timed rehearsals (one with a teammate playing a sceptical judge using the *Judge-question generator* output); record the backup video; sleep if you can.
