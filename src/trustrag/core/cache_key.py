"""Cache-key builder (stdlib only). The key must include everything that changes a result,
including the index version, so a live upsert/delete invalidates affected cached answers.
"""
from __future__ import annotations

import json
from typing import Any


def cache_key(
    query: str,
    mode: str,
    filters: dict[str, Any],
    groups: list[str],
    index_version: int,
    top_k: int = 5,
) -> str:
    payload = {
        "q": query.strip().lower(),
        "mode": mode,
        "filters": filters,
        "groups": sorted(groups),
        "v": index_version,
        "k": top_k,
    }
    return json.dumps(payload, sort_keys=True, default=str)
