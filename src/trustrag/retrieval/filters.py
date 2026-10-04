"""Pure metadata-filter predicate (stdlib only).

This is the single definition of "does a passage satisfy a filter". The Qdrant adapter
translates the same filter into a server-side Filter so it is applied *inside* the index
(pre-retrieval); this pure function powers the in-memory store and the property tests.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any


def _parse_dt(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def matches(
    meta: dict[str, Any],
    category: list[str] | None = None,
    source: list[str] | None = None,
    topic: list[str] | None = None,
    acl_groups: list[str] | None = None,
    ingested_after: str | None = None,
    ingested_before: str | None = None,
    doc_version: int | None = None,
) -> bool:
    """True iff the passage metadata satisfies every provided filter dimension."""
    if category is not None and meta.get("category") not in category:
        return False
    if source is not None and meta.get("source") not in source:
        return False
    if topic is not None and meta.get("topic") not in topic:
        return False
    if acl_groups is not None:
        # passage must share at least one group with the caller
        if not (set(meta.get("acl_groups", [])) & set(acl_groups)):
            return False
    if ingested_after is not None or ingested_before is not None:
        ts = _parse_dt(meta.get("ingested_at"))
        lo = _parse_dt(ingested_after)
        hi = _parse_dt(ingested_before)
        if ts is None:
            return False
        if lo is not None and ts < lo:
            return False
        if hi is not None and ts > hi:
            return False
    if doc_version is not None and meta.get("doc_version") != doc_version:
        return False
    return True
