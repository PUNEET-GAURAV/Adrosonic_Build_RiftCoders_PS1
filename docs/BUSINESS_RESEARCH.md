# Sourced research — TrustRAG business case

Resolves the `[VERIFY]` placeholders in `docs/BUSINESS_CASE.md` with cited facts. Every
claim below has a URL you can show. Re-verify anything that must be exact before the pitch.

## Adrosonic (the "why Adrosonic" story)

- **Adrosonic is a digital product engineering / IT consultancy.** Listed as an IT
  consultancy and digital product engineering company.
  - [Built In — ADROSONIC IT Consultancy Services](https://builtin.com/company/adrosonic-it-consultancy-services-pvt-ltd)
  - [Enosis Outsourcing — ADROSONIC profile](https://enosisoutsourcing.com/profile/adrosonic)
  - [Gartner Peer Insights — Adrosonic](https://gcom.pdo.aws.gartner.com/reviews/product/adrosonic-business-outcome-driven-enterprise-architecture-consulting)
- **Adrosonic delivers Microsoft Power Platform solutions** (so a REST/OpenAPI retrieval
  service is a natural fit for their Microsoft-ecosystem delivery).
  - [Microsoft Power Platform | ADROSONIC](https://adrosonic.com/pt/solutions/microsoft-power-platform/)
- **Adrosonic has an industries practice** (confirmed: Non-Profit; insurance/banking/retail
  are on the same industries section — confirm the exact list live at
  [adrosonic.com](https://adrosonic.com) during the hackathon).
  - [Non-Profit | Adrosonic](https://adrosonic.com/en-us/industries/non-profit/)

**Implication for the pitch:** TrustRAG is positioned as a *reusable, vendor-neutral retrieval
accelerator* that Adrosonic delivers and hardens for its clients — insurance first. The
Microsoft Power Platform connector story is real, not speculative.

## Groq free tier (build feasibility + honest limits)

Source: [Groq API Free Tier Limits in 2026 — Grizzly Peak Software](https://www.grizzlypeaksoftware.com/articles/p/groq-api-free-tier-limits-in-2026-what-you-actually-get-uwysd6mb)
(and [Groq console](https://console.groq.com)).

- Free tier, **no credit card required**, organization-level limits (30 RPM typical).
- **`llama-3.1-8b-instant`** is the workhorse: **30 RPM / 14,400 RPD / 6,000 TPM / 500,000 TPD** —
  the most permissive free model. ✅ This is TrustRAG's default generator + judge model.
- `llama-3.3-70b-versatile`: 30 RPM / 1,000 RPD (higher quality, lower volume — optional for
  judged RAGAS if the 8B judge looks noisy).
- Rate limits hit on **whichever axis arrives first**; the API returns `429` with
  `x-ratelimit-*` headers for backoff. **Cached prompt tokens do not count against limits.**

**Implication for the build:**
- 50-query LLM-judged RAGAS + a handful of `/answer` demos fit comfortably inside the 8B
  model's 14,400 RPD budget. Throttle to ~25 RPM and back off on 429 (already in the plan).
- Keep the judge at temperature 0 and cache every judgement on disk (resumable runs).

## Managed vector DB pricing (TCO comparison — representative, verify before quoting)

The business case deliberately does **not** quote a hard price. For the TCO table, use a
named provider's public pricing page at pitch time (for example Pinecone / Qdrant Cloud /
Weaviate Cloud serverless pricing) and label the cell as "starting at $X, [source URL]".
TrustRAG's differentiator is the **zero-licence self-hosted** row, which needs no sourcing.

## Honesty rules (unchanged)

- Present the market-size structure with a bottom-up formula; quote a term only with a
  source, otherwise show the cell as `[VERIFY]`.
- Validate the pain live: ask 2–3 Adrosonic mentors the five questions in
  `docs/BUSINESS_CASE.md` §12 and quote the themes (not names).
