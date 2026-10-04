# ADR-009: Fast Lexical Intent Routing for RAG Pre-filtering

## Context
A major challenge with generic RAG over partitioned enterprise data (like a bank with distinct verticals: cards, loans, KYC) is that exhaustive global similarity search retrieves irrelevant but highly semantically similar cross-domain results. To prevent this, queries must be pre-filtered. 

The hackathon strict SLA is < 15ms p95 for the router. Traditional LLM-as-a-judge routing takes 300-800ms. Dense vector clustering routing requires hitting the encoder twice.

## Decision
We implemented an ultra-fast **Lexical Intent Router** (`LexicalRouter`) configured by a YAML taxonomy (`banking_taxonomy.yaml`). 
- Queries are normalized and matched against domain keywords.
- Pseudo-probabilities are calculated. 
- A decision strategy (`hard`, `soft`, `fallback`) is selected based on confidence margins.
- If a query hits `fallback`, we expose a `needs_clarification` flag and suggest the top 2-3 domains to the UI.

## Trade-offs
- **Pros:** Executes in 0.04ms. Zero network dependency. Deterministic. No extra GPU usage. Easily updated by non-engineers via YAML.
- **Cons:** Vocabulary mapping relies on explicit keywords rather than deep semantic understanding (synonyms must be manually added to the config).

## Status
Accepted.
