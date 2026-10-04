"""Evaluation metrics (stdlib only). Pure and deterministic, so they can be unit-tested
offline with no ML stack.

``gold`` is an iterable of relevant passage ids; ``retrieved`` is the ranked list of ids.
"""
from __future__ import annotations

import math
from collections.abc import Iterable, Sequence


def _g(gold: Iterable[str]) -> set[str]:
    return set(gold)


def hit_at_k(gold: Iterable[str], retrieved: Sequence[str], k: int = 5) -> float:
    g = _g(gold)
    return 1.0 if any(r in g for r in retrieved[:k]) else 0.0


def precision_at_k(gold: Iterable[str], retrieved: Sequence[str], k: int = 5) -> float:
    g = _g(gold)
    top = retrieved[:k]
    if not top:
        return 0.0
    return sum(1 for r in top if r in g) / len(top)


def recall_at_k(gold: Iterable[str], retrieved: Sequence[str], k: int = 5) -> float:
    g = _g(gold)
    if not g:
        return 0.0
    return sum(1 for r in retrieved[:k] if r in g) / len(g)


def mrr(gold: Iterable[str], retrieved: Sequence[str], k: int = 10) -> float:
    g = _g(gold)
    for i, r in enumerate(retrieved[:k], start=1):
        if r in g:
            return 1.0 / i
    return 0.0


def ndcg_at_k(gold: Iterable[str], retrieved: Sequence[str], k: int = 10) -> float:
    g = _g(gold)
    top = retrieved[:k]
    dcg = 0.0
    for i, r in enumerate(top):
        if r in g:
            dcg += 1.0 / math.log2(i + 2)
    ideal = sum(1.0 / math.log2(i + 2) for i in range(min(len(g), k)))
    if ideal == 0:
        return 0.0
    return dcg / ideal


# ---- RAGAS-style formulas (pure; the LLM judge supplies per-passage relevance) ----
def context_precision_from_relevance(relevances: Sequence[bool]) -> float:
    """RAGAS context precision: average over relevant positions i of (relevant-up-to-i / i)."""
    relevant_total = sum(1 for r in relevances if r)
    if relevant_total == 0:
        return 0.0
    acc = 0.0
    relevant_seen = 0
    for i, r in enumerate(relevances, start=1):
        if r:
            relevant_seen += 1
            acc += relevant_seen / i
    return acc / relevant_total


def context_recall_from_relevance(relevances: Sequence[bool], total_relevant: int) -> float:
    if total_relevant <= 0:
        return 0.0
    return min(1.0, sum(1 for r in relevances if r) / total_relevant)


def token_overlap_relevant(reference: str, passage: str, threshold: float = 0.035) -> bool:
    """Non-LLM relevance approximation: Jaccard overlap of tokens above a threshold."""
    a = set(reference.lower().split())
    b = set(passage.lower().split())
    if not a or not b:
        return False
    return len(a & b) / len(a | b) >= threshold
