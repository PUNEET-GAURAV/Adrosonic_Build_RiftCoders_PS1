"""Ports (interfaces) of the system. Adapters implement these; the core depends on
the interfaces only, never on a vendor SDK.

Uses typing.Protocol so adapters need not inherit anything — they just satisfy the
shape, which also keeps the in-memory fakes in tests trivial.
"""
from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from .models import DenseVector, Filters, Passage, ScoredPassage, SparseVector


@runtime_checkable
class Embedder(Protocol):
    """Turns text into dense vectors. Queries and documents may use different prefixes."""

    def embed_queries(self, queries: Sequence[str]) -> list[DenseVector]: ...
    def embed_documents(self, texts: Sequence[str]) -> list[DenseVector]: ...


@runtime_checkable
class SparseEncoder(Protocol):
    """Turns text into BM25 sparse vectors (term-frequency values; IDF applied server-side)."""

    def encode_queries(self, queries: Sequence[str]) -> list[SparseVector]: ...
    def encode_documents(self, texts: Sequence[str]) -> list[SparseVector]: ...


@runtime_checkable
class VectorStore(Protocol):
    """The single store: dense + sparse + payload on every point."""

    def upsert(
        self,
        passages: Sequence[Passage],
        dense: Sequence[DenseVector],
        sparse: Sequence[SparseVector],
    ) -> None: ...

    def delete(self, passage_ids: Sequence[str]) -> None: ...

    def count(self) -> int: ...

    def search_dense(
        self, vector: DenseVector, top_k: int, filters: Filters
    ) -> list[ScoredPassage]: ...

    def search_sparse(
        self, vector: SparseVector, top_k: int, filters: Filters
    ) -> list[ScoredPassage]: ...

    def index_version(self) -> int: ...

    def bump_index_version(self) -> int: ...


@runtime_checkable
class Reranker(Protocol):
    """Re-scores (query, passage) pairs, e.g. a cross-encoder."""

    def rerank(self, query: str, passages: Sequence[ScoredPassage]) -> list[ScoredPassage]: ...


@runtime_checkable
class Generator(Protocol):
    """Generates a grounded answer from retrieved passages (or returns None on failure)."""

    def generate(self, query: str, passages: Sequence[ScoredPassage]) -> str | None: ...


@runtime_checkable
class Cache(Protocol):
    """Keyed cache for search results, with index-version awareness."""

    def get(self, key: str) -> object | None: ...
    def put(self, key: str, value: object) -> None: ...
