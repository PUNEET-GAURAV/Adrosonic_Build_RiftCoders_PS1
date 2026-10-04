# ADR-010: Partitioning by Payload Filters vs. Separate Collections

## Context
When building multitenant or multi-domain vector systems (like our Banking vertical), there is an architectural choice for achieving logical isolation:
1. **Separate Collections**: One Qdrant collection per tenant or per domain (e.g., `verity_loans`, `verity_kyc`).
2. **Payload Filters**: A single massive Qdrant collection (`verity_banking`) using payload matching (e.g., `FieldCondition(key="domain", match=MatchValue(value="loans"))`).

## Decision
We chose **Payload Filters** within a single collection for the Verity-RAG Banking implementation.

## Rationale
- **Flexibility**: We can search across all domains for ambiguous queries (`fallback` routing strategy) instantly. If data were split across collections, we would have to map-reduce across N collections, incurring heavy I/O latency.
- **Maintenance**: Schema updates, backups, and index regeneration happen once, not N times.
- **Tenant Isolation**: By enforcing `tenant = session.tenant` at the Orchestrator level before any Qdrant call, we achieve secure multi-tenancy without the overhead of spinning up dedicated collections for small tenants. 

## Consequences
- Requires strict `MatchAny` payload indexing (configured on `tenant` and `domain`) to ensure pre-retrieval filtering remains fast at massive scale.
- We must enforce strict RBAC and query patching at the API/Orchestrator layer to prevent data leakage.

## Status
Accepted.
