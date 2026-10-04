"""Text and vector primitives (stdlib only, no vendor SDK, no pydantic).

Kept dependency-free so BM25 tokenisation, hashing and cosine similarity can be
unit-tested offline.
"""
from __future__ import annotations

import re
from collections import Counter

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    """Lowercase and split on runs of alphanumerics (simple, deterministic tokeniser)."""
    return _TOKEN_RE.findall(text.lower())


def fnv1a32(token: str) -> int:
    """FNV-1a 32-bit hash. Stable across runs/machines; used as a sparse-vector index."""
    h = 2166136261
    for byte in token.encode("utf-8"):
        h = ((h ^ byte) * 16777619) & 0xFFFFFFFF
    return h


def term_frequencies(text: str) -> dict[int, int]:
    """token -> (hashed index -> term frequency). Qdrant applies IDF server-side."""
    counts: Counter[str] = Counter(tokenize(text))
    return {fnv1a32(tok): freq for tok, freq in counts.items()}


def cosine_sim(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def normalize(v: list[float]) -> list[float]:
    n = sum(x * x for x in v) ** 0.5
    if n == 0:
        return [0.0] * len(v)
    return [x / n for x in v]
