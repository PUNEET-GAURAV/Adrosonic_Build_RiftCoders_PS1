"""Explain helpers (stdlib only)."""
from __future__ import annotations

from ..core.text import tokenize


def matched_terms(query: str, text: str, limit: int = 8) -> list[str]:
    """Query tokens that appear verbatim in the passage text (deduplicated, order-preserved)."""
    q_tokens = tokenize(query)
    t_tokens = set(tokenize(text))
    seen: set[str] = set()
    out: list[str] = []
    for tok in q_tokens:
        if tok in t_tokens and tok not in seen:
            seen.add(tok)
            out.append(tok)
        if len(out) >= limit:
            break
    return out
