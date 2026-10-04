"""Pure fusion functions (stdlib only, no vendor SDK).

Each leg is a ranked list of objects exposing `.passage_id` (str) and `.score` (float),
already sorted by descending score. Functions return a mapping ``passage_id -> fused score``;
the caller re-sorts and annotates. Keeping this dependency-free means it is unit-tested
offline with no ML stack.
"""
from __future__ import annotations

from typing import Iterable, Mapping, Sequence

DEFAULT_WEIGHTS = {"dense": 1.0, "sparse": 1.0}


def _leg_scores(leg: Sequence) -> dict[str, float]:
    return {p.passage_id: p.score for p in leg}


def rrf(
    legs: Mapping[str, Sequence],
    k: float = 60.0,
    weights: Mapping[str, float] | None = None,
) -> dict[str, float]:
    """Reciprocal Rank Fusion. Rank-based, so no score normalisation is needed."""
    weights = weights or DEFAULT_WEIGHTS
    fused: dict[str, float] = {}
    for name, ranked in legs.items():
        w = float(weights.get(name, 1.0))
        for rank, item in enumerate(ranked, start=1):
            fused[item.passage_id] = fused.get(item.passage_id, 0.0) + w * (1.0 / (k + rank))
    return fused


def _minmax(leg: Sequence) -> dict[str, float]:
    ids = [p.passage_id for p in leg]
    vals = [p.score for p in leg]
    if not vals:
        return {}
    lo, hi = min(vals), max(vals)
    if hi == lo:
        return {pid: 1.0 for pid in ids}
    return {pid: (s - lo) / (hi - lo) for pid, s in zip(ids, vals)}


def weighted(
    legs: Mapping[str, Sequence],
    weights: Mapping[str, float] | None = None,
) -> dict[str, float]:
    """Weighted linear fusion with per-leg min-max normalisation (dense cosine and
    BM25 scores live on incompatible scales)."""
    weights = weights or DEFAULT_WEIGHTS
    fused: dict[str, float] = {}
    for name, ranked in legs.items():
        w = float(weights.get(name, 1.0))
        norm = _minmax(ranked)
        for pid, s in norm.items():
            fused[pid] = fused.get(pid, 0.0) + w * s
    return fused


def dbsf(
    legs: Mapping[str, Sequence],
    weights: Mapping[str, float] | None = None,
) -> dict[str, float]:
    """Distribution-Based Score Fusion: sum of per-leg z-scores (standard score)."""
    weights = weights or DEFAULT_WEIGHTS
    fused: dict[str, float] = {}
    for name, ranked in legs.items():
        w = float(weights.get(name, 1.0))
        vals = [p.score for p in ranked]
        if not vals:
            continue
        n = len(vals)
        mean = sum(vals) / n
        var = sum((v - mean) ** 2 for v in vals) / n
        std = var ** 0.5
        for p in ranked:
            z = (p.score - mean) / std if std > 0 else 0.0
            fused[p.passage_id] = fused.get(p.passage_id, 0.0) + w * z
    return fused


def fuse(
    legs: Mapping[str, Sequence],
    method: str = "rrf",
    k: float = 60.0,
    weights: Mapping[str, float] | None = None,
) -> dict[str, float]:
    """Dispatch to a fusion method by name."""
    if method == "rrf":
        return rrf(legs, k=k, weights=weights)
    if method == "weighted":
        return weighted(legs, weights=weights)
    if method == "dbsf":
        return dbsf(legs, weights=weights)
    raise ValueError(f"unknown fusion method: {method!r}")


def sort_by_fused(
    legs: Mapping[str, Sequence],
    fused: Mapping[str, float],
    top_k: int,
) -> list:
    """Merge the legs into a single ranked list by fused score, attaching per-leg
    rank/score diagnostics. Returns the top_k items (duck-typed, stable on ties)."""
    leg_rank: dict[str, dict[str, int]] = {}
    leg_score: dict[str, dict[str, float]] = {}
    by_id: dict[str, object] = {}
    for name, ranked in legs.items():
        leg_rank[name] = {p.passage_id: i + 1 for i, p in enumerate(ranked)}
        leg_score[name] = {p.passage_id: p.score for p in ranked}
        for p in ranked:
            by_id.setdefault(p.passage_id, p)

    order = sorted(fused.keys(), key=lambda pid: (-fused[pid], pid))
    out: list = []
    for pid in order[:top_k]:
        item = by_id[pid]
        item.score = fused[pid]
        item.dense_rank = leg_rank.get("dense", {}).get(pid)
        item.sparse_rank = leg_rank.get("sparse", {}).get(pid)
        if getattr(item, "dense_score", None) is None and pid in leg_score.get("dense", {}):
            item.dense_score = leg_score["dense"][pid]
        if getattr(item, "sparse_score", None) is None and pid in leg_score.get("sparse", {}):
            item.sparse_score = leg_score["sparse"][pid]
        out.append(item)
    return out
