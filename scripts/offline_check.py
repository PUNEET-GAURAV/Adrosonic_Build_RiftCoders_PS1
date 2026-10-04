"""Offline smoke test: exercises the pure (stdlib-only) modules with no ML stack.

Run: `python scripts/offline_check.py`. Exits non-zero on any failure. This proves the
core logic (fusion, metrics, filters, cache keys, ids, text primitives) before any
dependency is installed, so the repo is verifiable in a bare environment.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from trustrag.adapters.memory_cache import MemoryCache  # noqa: E402
from trustrag.core.cache_key import cache_key  # noqa: E402
from trustrag.core.fusion import rrf, sort_by_fused  # noqa: E402
from trustrag.core.ids import passage_uuid  # noqa: E402
from trustrag.core.text import cosine_sim, fnv1a32, term_frequencies, tokenize  # noqa: E402
from trustrag.evaluation.metrics import (  # noqa: E402
    context_precision_from_relevance,
    hit_at_k,
    mrr,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)
from trustrag.retrieval.filters import matches  # noqa: E402


class Item:
    def __init__(self, pid, score):
        self.passage_id = pid
        self.score = score
        self.dense_rank = self.sparse_rank = None
        self.dense_score = self.sparse_score = None
        self.rerank_score = None
        self.rank = 0


def check(name: str, cond: bool) -> None:
    if not cond:
        raise AssertionError(f"FAILED: {name}")
    print(f"  ok: {name}")


def main() -> None:
    print("Offline pure-logic checks")
    # fusion
    d = [Item("a", 0.9), Item("b", 0.8)]
    s = [Item("b", 5.0), Item("c", 4.0)]
    scores = rrf({"dense": d, "sparse": s}, k=60.0)
    check("rrf union + shared item wins", max(scores, key=scores.get) == "b")
    out = sort_by_fused({"dense": d, "sparse": s}, scores, top_k=3)
    check("sort_by_fused top is shared", out[0].passage_id == "b" and out[0].dense_rank == 2)

    # ids
    check("uuid deterministic", passage_uuid("a") == passage_uuid("a"))

    # text
    check("tokenize", tokenize("Hello, WORLD 123!") == ["hello", "world", "123"])
    check("term frequencies", term_frequencies("cat cat dog")[fnv1a32("cat")] == 2)
    check("cosine", abs(cosine_sim([1, 0], [1, 0]) - 1.0) < 1e-9)

    # metrics
    gold = {"a", "b", "c"}
    retrieved = ["a", "x", "b", "y", "z"]
    check("precision@5", abs(precision_at_k(gold, retrieved, 5) - 0.4) < 1e-9)
    check("recall@5", abs(recall_at_k(gold, retrieved, 5) - 2 / 3) < 1e-9)
    check("hit@5", hit_at_k(gold, retrieved, 5) == 1.0)
    check("mrr", mrr({"b"}, ["a", "b"]) == 0.5)
    check("ndcg", abs(ndcg_at_k({"a", "c"}, ["a", "x", "c", "y"], 4) - 1.0) < 0.1)
    check("context precision", abs(context_precision_from_relevance([True, False, True]) - (1 + 2 / 3) / 2) < 1e-9)

    # filters
    meta = {"category": "NUMERIC", "acl_groups": ["public"], "ingested_at": "2026-10-01T12:00:00Z"}
    check("filter category", matches(meta, category=["NUMERIC"]) and not matches(meta, category=["DESCRIPTION"]))
    check("filter acl", matches(meta, acl_groups=["public"]) and not matches(meta, acl_groups=["admin"]))

    # cache
    check("cache version invalidation", cache_key("q", "hybrid", {}, [], 1) != cache_key("q", "hybrid", {}, [], 2))
    c = MemoryCache(maxsize=2)
    c.put("a", 1)
    c.put("b", 2)
    c.get("a")
    c.put("c", 3)
    check("lru eviction", c.get("a") == 1 and c.get("b") is None)

    print("ALL OFFLINE CHECKS PASSED")


if __name__ == "__main__":
    main()
