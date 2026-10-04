"""In-memory VectorStore for unit tests and the 10k small demo (no Qdrant needed).

Implements the same port as QdrantStore. Dense search is brute-force cosine; sparse search
is a simplified BM25 (term-frequency + inverse-document-frequency dot product) that is
close enough to exercise the orchestrator, filters and fusion deterministically.
"""
from __future__ import annotations

import math
from typing import Sequence

from ..core.models import DenseVector, Filters, Passage, ScoredPassage, SparseVector
from ..core.text import cosine_sim
from ..retrieval.filters import matches


class InMemoryStore:
    def __init__(self, index_version: int = 0) -> None:
        self._points: dict[str, dict] = {}
        self._index_version = index_version

    def upsert(
        self,
        passages: Sequence[Passage],
        dense: Sequence[DenseVector],
        sparse: Sequence[SparseVector],
    ) -> None:
        for p, d, s in zip(passages, dense, sparse):
            self._points[p.passage_id] = {
                "passage": p,
                "dense": d,
                "sparse": dict(zip(s.indices, s.values)),
            }
        self._index_version += 1

    def delete(self, passage_ids: Sequence[str]) -> None:
        for pid in passage_ids:
            self._points.pop(pid, None)
        self._index_version += 1

    def count(self) -> int:
        return len(self._points)

    def _meta(self, p: Passage) -> dict:
        return {
            "category": p.category,
            "source": p.source,
            "topic": p.topic,
            "acl_groups": p.acl_groups,
            "doc_version": p.doc_version,
            "ingested_at": p.ingested_at,
        }

    def _pass(self, p: Passage, filters: Filters) -> bool:
        return matches(
            self._meta(p),
            category=filters.category,
            source=filters.source,
            topic=filters.topic,
            acl_groups=filters.acl_groups,
            ingested_after=filters.ingested_after,
            ingested_before=filters.ingested_before,
            doc_version=filters.doc_version,
        )

    def search_dense(self, vector: DenseVector, top_k: int, filters: Filters) -> list[ScoredPassage]:
        scored = []
        for pid, rec in self._points.items():
            p: Passage = rec["passage"]
            if not self._pass(p, filters):
                continue
            scored.append((cosine_sim(vector, rec["dense"]), p))
        scored.sort(key=lambda t: -t[0])
        return [
            ScoredPassage(
                passage_id=p.passage_id, text=p.text, score=s, rank=i,
                dense_score=s, dense_rank=i, metadata=self._meta(p),
            )
            for i, (s, p) in enumerate(scored[:top_k], start=1)
        ]

    def _idf(self, index: int) -> float:
        df = sum(1 for rec in self._points.values() if index in rec["sparse"])
        return math.log((len(self._points) + 1.0) / (df + 1.0)) + 1.0

    def search_sparse(self, vector: SparseVector, top_k: int, filters: Filters) -> list[ScoredPassage]:
        q = dict(zip(vector.indices, vector.values))
        scored = []
        for pid, rec in self._points.items():
            p: Passage = rec["passage"]
            if not self._pass(p, filters):
                continue
            score = 0.0
            for idx, qtf in q.items():
                if idx in rec["sparse"]:
                    score += qtf * rec["sparse"][idx] * self._idf(idx)
            scored.append((score, p))
        scored.sort(key=lambda t: -t[0])
        return [
            ScoredPassage(
                passage_id=p.passage_id, text=p.text, score=s, rank=i,
                sparse_score=s, sparse_rank=i, metadata=self._meta(p),
            )
            for i, (s, p) in enumerate(scored[:top_k], start=1)
        ]

    def index_version(self) -> int:
        return self._index_version

    def bump_index_version(self) -> int:
        self._index_version += 1
        return self._index_version
