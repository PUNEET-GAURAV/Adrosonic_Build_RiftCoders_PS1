# Business Case — TrustRAG

**Purpose:** give the "business evaluation" axis real substance without inventing facts.
**Rules for this document**
- Anything marked **`[VERIFY]`** is a placeholder for an external fact. Source it (with a link you can show) or delete the claim before the pitch.
- Anything marked **`[MEASURED]`** must be filled from `results/` after the benchmark runs.
- Anything marked **ILLUSTRATIVE** is a worked example with made-up inputs to show the method; never present it as data.
- Figures that follow from arithmetic (for example memory per vector) are stated as such.

---

## 1. One-line positioning

> **TrustRAG is an open, measurable retrieval layer that makes enterprise RAG answers trustworthy: higher precision than naive vector search, fast enough for a live workflow, governed by filters and permissions, always fresh, and cheap enough to run anywhere.**

**Thesis:** in enterprise RAG the language model gets the blame, but the retriever decides the outcome. If the evidence handed to the model is semantically close but factually wrong, a fluent wrong answer follows. Fixing retrieval is the highest-leverage, lowest-cost place to buy trust.

---

## 2. Who has the problem

| Segment (Adrosonic industry) | Typical knowledge corpus | What a wrong retrieval costs | Why precision matters |
|---|---|---|---|
| **Insurance** (primary) | Policy wordings, endorsements, claims SOPs, underwriting guidelines | Wrong coverage decision, claim leakage, rework, complaints, regulatory exposure | Near-duplicate clauses differ in exclusions; "similar" is dangerous |
| **Banking and Finance** | Product terms, KYC/AML procedures, regulatory circulars | Compliance breach, mis-selling, audit findings | Answers must be scoped to the right product, jurisdiction and date |
| **E-Commerce and Retail** | Catalogue, returns policy, support playbooks | Wrong promise to customers, refunds, churn | Exact identifiers (SKUs, order codes) need keyword matching; descriptions need semantics: hybrid fits |
| **Non-Profit** | Grant rules, eligibility policies, donor FAQs | Wrong eligibility advice, compliance with funders | Small teams, low budget: the free-tier stack matters |

Insurance is the lead story because two of the three hackathon problem statements are insurance-themed and Adrosonic lists insurance first among its industries. `[VERIFY: pull one or two sentences from Adrosonic's own insurance page to echo their language.]`

### Buyer and user
- **Economic buyer:** head of claims/operations, CIO/CTO, or compliance head.
- **Technical owner:** platform / data engineering lead.
- **Daily user:** claims handler, compliance analyst, support agent.

---

## 3. Value proposition (and how each pillar is proven)

| Pillar | Customer benefit | Proof we can show |
|---|---|---|
| **Precision** | Fewer plausible-but-wrong passages reach the model | Ablation ladder: dense → hybrid → hybrid+rerank on a held-out test split `[MEASURED]` |
| **Speed** | Fits inside a live workflow (call, chat, form) | p95 over 100 consecutive queries, hybrid and hybrid+rerank `[MEASURED]` |
| **Control** | Search scoped to what is relevant and permitted | Filters applied before retrieval; selective-filter test; permission-aware demo (P2) |
| **Freshness** | New or corrected policy is searchable immediately | Upsert → searchable in one request cycle; delete → gone; no reindex |
| **Trust** | Auditable answers | Citations, abstention on weak evidence, explain mode, evaluation dashboard |
| **Cost** | Runs on commodity hardware with open components | Memory and throughput arithmetic below; free-tier stack |
| **Portability** | No lock-in; fits client stacks | Ports-and-adapters: the vector store sits behind an interface (pgvector adapter as proof, P2) |

**Honest claim to make on stage:** TrustRAG *reduces* the chance of ungrounded answers by improving evidence quality and refusing to answer on weak evidence. It does not "eliminate" hallucination, and the dashboard measures the reduction rather than asserting it.

---

## 4. Competitive landscape (qualitative; verify before presenting)

| Option | Strengths | Gaps TrustRAG addresses | Note |
|---|---|---|---|
| Naive dense-only RAG | Easy to build | Misses exact terms and identifiers; semantically similar but wrong passages; no governance | This is the baseline in the problem statement |
| Managed vector database services | Fast to start, hosted | Usage-based cost, data leaves the client's boundary, platform lock-in `[VERIFY pricing before quoting]` | TrustRAG can sit in front of, or replace, them via the store port |
| Cloud search suites (for example Azure AI Search, Elastic, Vertex AI Search) | Rich features, managed scale `[VERIFY current capabilities]` | Cost and platform coupling; harder to run fully on-prem or on a laptop POC | Relevant: Adrosonic works on Microsoft Dynamics 365 and Power Platform; the REST/OpenAPI surface is built to be consumable from that world |
| **TrustRAG** | Open, measurable, hybrid + rerank, governed, fresh, portable, runnable on a laptop | Not a managed service at global scale (yet) | Positioned as a **reference accelerator** that Adrosonic can deploy and harden per client |

---

## 5. Business model

**Open-core accelerator delivered through services.**

| Layer | What it is | Who pays and why |
|---|---|---|
| **Community core** (open source) | The retrieval pipeline, evaluation harness, UI, ADRs | Nobody; builds trust, adoption and talent pull |
| **Accelerator POC** (fixed-fee service) | "Your documents, our pipeline, measured against your questions in two weeks" | Clients who need proof before committing |
| **Implementation and integration** | Connectors to client sources, security review, deployment, Power Platform / Dynamics 365 integration | Existing Adrosonic delivery revenue |
| **Managed service** | Hosted, monitored, upgraded retrieval layer | Recurring fee, priced on documents indexed and queries |
| **Enterprise add-ons** | SSO, fine-grained permissions, audit logs, compliance reports, SLAs | Regulated clients |

**Why this suits Adrosonic specifically:** a consultancy monetises delivery, integration and managed services; an open accelerator lowers the cost and risk of every RAG engagement and creates a reusable asset across insurance, banking and retail accounts.

### Pricing logic (structure only; values to be validated)
- Charge on a metric that tracks value, not infrastructure: documents indexed (data scale) and queries per month (usage).
- Keep a generous free/community tier to drive adoption (apply the `free-tier-strategy` skill's upgrade-trigger thinking).
- Use fixed-fee POCs to de-risk first deals.
- **Prices:** `$X / ₹X` placeholders until validated with real buyers. Do not publish numbers you cannot justify.

---

## 6. Unit economics (from first principles)

### 6.1 Memory per vector (pure arithmetic)
- Dense vector: 384 dimensions × 4 bytes (float32) = **1,536 bytes** per passage.
- Per 100,000 passages: ≈ **154 MB**; per 500,000: ≈ **768 MB**; per 1,000,000: ≈ **1.5 GB** (raw vectors only).
- With int8 scalar quantization: about one quarter of that (≈ 384 bytes per passage): ≈ **192 MB per 500,000**.
- Add HNSW graph and payload overhead `[MEASURED from the Qdrant container at 100k and 500k]`.

### 6.2 Cost per 1,000 queries (formula)
```
cost_per_1k_queries = (host_cost_per_hour / sustained_queries_per_hour) × 1000   +   llm_cost_per_1k_answers
```
- `sustained_queries_per_hour` comes from the measured p50/p95 and a concurrency test `[MEASURED]`.
- `host_cost_per_hour`: price of a modest 8 GB CPU instance `[VERIFY with a current price from a named provider]`, or zero marginal cost on existing client hardware.
- `llm_cost_per_1k_answers`: free tier for the hackathon; for production use tokens per answer × the provider's current price `[VERIFY]`. Retrieval-only deployments have none.

### 6.3 Total cost of ownership comparison (template)
| Cost line | TrustRAG self-hosted | Managed vector DB | Cloud search suite |
|---|---|---|---|
| Licence / subscription | 0 | `[VERIFY]` | `[VERIFY]` |
| Infrastructure | one small VM | included in fee | included in fee |
| Egress / data residency | stays in client boundary | `[VERIFY]` | `[VERIFY]` |
| Engineering effort | accelerator reduces it | low | low–medium |
| Lock-in risk | low (store port) | higher | higher |

---

## 7. ROI model (method, with an ILLUSTRATIVE example)

### 7.1 Inputs the client supplies
`N_users`, `lookups_per_user_per_day`, `minutes_saved_per_lookup`, `loaded_cost_per_hour`, `error_rate_before`, `error_rate_after`, `cost_per_error`, `working_days_per_year`.

### 7.2 Formulas
```
time_value_per_year   = N_users × lookups_per_user_per_day × (minutes_saved_per_lookup / 60)
                        × loaded_cost_per_hour × working_days_per_year

error_cost_avoided    = N_users × lookups_per_user_per_day × working_days_per_year
                        × (error_rate_before − error_rate_after) × cost_per_error

annual_benefit        = time_value_per_year + error_cost_avoided
payback_months        = (implementation_cost + first_year_run_cost) / (annual_benefit / 12)
```
`error_rate_before/after` should come from a **client-specific pilot** (retrieval precision uplift measured on their questions), not from our MS MARCO numbers.

### 7.3 ILLUSTRATIVE example (made-up inputs, method only)
- 50 users × 20 lookups/day × 3 minutes saved = 3,000 minutes/day = **50 hours/day** of analyst time.
- Multiply by your client's loaded hourly cost and working days to get `time_value_per_year`.
- The error-avoidance term usually dominates in claims and compliance; that is why the pilot must measure it.

> Present this as a *method the client can fill in*, not a promise. Judges trust a clear method over a big unsourced number.

---

## 8. Go-to-market

1. **Land (weeks 0–6):** run the 2-week accelerator POC for one or two existing Adrosonic accounts, starting with insurance. Deliverable: before/after precision on the client's own questions, plus latency and a governance review.
2. **Expand (months 2–6):** add connectors, permission-aware retrieval, Power Platform / Dynamics 365 integration, and a managed-service option.
3. **Scale (months 6–12):** package as a repeatable offering across banking and retail; publish case studies; contribute the core upstream as open source.

**Channels:** Adrosonic's existing client base; Microsoft ecosystem touchpoints (custom connector or API integration); technical content (benchmark report, ADRs) as a credibility asset.

**Integration story (verify before claiming):** the service exposes a documented REST API with an OpenAPI description, which is the natural starting point for a Power Platform custom connector. Test the import before saying "ready"; otherwise say "designed for".

---

## 9. Roadmap

| Horizon | Focus |
|---|---|
| Hackathon (24 h) | Phase 1 baseline, Phase 2 hybrid, filters, live updates, benchmark, rerank, answers with abstention, dashboard |
| 30 days | Domain evaluation on real client documents; chunking for long, structured documents; permission model; connectors |
| 90 days | Managed deployment, monitoring and alerting, audit logs, multi-tenant isolation, second store adapter in production |
| 12 months | Evaluation-as-a-service, fine-tuned domain embeddings, agent integrations (MCP), industry packs (insurance, banking) |

---

## 10. Risks and honest limitations

| Risk | Reality | Mitigation |
|---|---|---|
| **Benchmark is MS MARCO (short web passages)** | Enterprise documents are longer, structured and domain-specific; results may not transfer directly | The POC exists precisely to measure on client data; chunking and structure-aware ingestion are on the 30-day plan |
| **LLM-judged metrics are noisy** | RAGAS depends on a judge model | We also report non-LLM RAGAS and classical IR metrics on gold labels |
| **Synthetic labels in the demo** | Topic and ACL labels are derived or synthetic | Marked in the data (`label_origin`) and disclosed in the demo |
| **Data privacy** | Sending text to an external LLM may be unacceptable | Retrieval-only mode, self-hosted store, optional local LLM; only query + retrieved passages ever leave, and only with consent |
| **Compliance** | Regulated clients need audit and access control | Permission-aware retrieval, audit logging on the roadmap; apply `privacy-by-design` and `gdpr-data-handling` checklists `[VERIFY relevant regulations per client geography]` |
| **Scale beyond a single node** | Hackathon scale is 100k–500k passages | Qdrant supports distributed deployment; the store port limits rework `[VERIFY before quoting limits]` |
| **Free-tier dependency** | Groq limits can change | Extractive fallback; the core runs without any LLM |

---

## 11. KPIs and the north-star metric

**North star:** *precision of the top-5 evidence under a 300 ms p95 budget, at the lowest cost per 1,000 queries.*

| KPI | Definition | Target / source |
|---|---|---|
| Precision uplift | Hybrid(+rerank) context precision minus naive baseline | `[MEASURED]` |
| Recall | Context recall at k=5 | `[MEASURED]` |
| p95 latency | 100 consecutive queries, via HTTP API | < 300 ms `[MEASURED]` |
| Freshness | Seconds from upsert to searchable | `[MEASURED]` |
| Abstention rate | Share of queries answered "insufficient evidence" | dev split `[MEASURED]` |
| Citation validity | Share of citations that map to a returned passage | dev split `[MEASURED]` |
| Cost per 1,000 queries | Formula in §6.2 | `[MEASURED + VERIFY]` |

---

## 12. Validate the pain during the hackathon (free, and judges notice)

You will be around Adrosonic people. Spend 5 minutes each with 2–3 mentors or staff and ask:
1. "In your insurance or banking projects, where does retrieval quality hurt most today?"
2. "How do clients currently check that an AI answer is grounded?"
3. "What would a client need to see in a two-week proof of concept to say yes?"
4. "How much do permissions and audit matter versus raw accuracy?"
5. "Which of your platforms would this need to plug into first?"

Quote the *themes* (not names, unless they agree) on your business slide. Real validation beats any made-up market figure.

---

## 13. Market sizing (only if you have the time; do it honestly)

Use the `market-sizing-analysis` and `startup-business-analyst-market-opportunity` skills with a **bottom-up** approach:
```
SAM ≈ (number of target firms in the segment) × (share with an enterprise RAG initiative) × (annual spend per firm on retrieval/RAG tooling and services)
```
Every term needs a cited source. If you cannot source a term, show the structure with the cell marked `[VERIFY]` rather than a guess. Skip TAM headline figures from low-quality sources.
