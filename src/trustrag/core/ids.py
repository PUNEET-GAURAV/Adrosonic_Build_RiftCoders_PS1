"""Deterministic point IDs (stdlib only). ADR-010."""
from __future__ import annotations

import uuid

_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # RFC 4122 DNS namespace


def passage_uuid(passage_id: str) -> str:
    """Deterministic UUIDv5 of a passage_id, so upsert is idempotent and ingestion
    is resumable (same passage -> same point ID)."""
    return str(uuid.uuid5(_NAMESPACE, passage_id))
