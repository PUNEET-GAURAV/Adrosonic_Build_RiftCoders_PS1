"""Pydantic domain models. These are the shared vocabulary of the system.

This module imports pydantic (a base dependency) but no vendor SDK.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

DenseVector = list[float]


class SparseVector(BaseModel):
    """A sparse vector as (indices, values). Indices are stable 32-bit token hashes."""

    indices: list[int] = Field(default_factory=list)
    values: list[float] = Field(default_factory=list)


class Filters(BaseModel):
    """Metadata filters. Every field is optional; an empty instance matches everything."""

    category: list[str] | None = None
    source: list[str] | None = None
    topic: list[str] | None = None
    acl_groups: list[str] | None = None
    ingested_after: str | None = None  # ISO-8601 datetime
    ingested_before: str | None = None
    doc_version: int | None = None
    
    # Banking specific filters
    domain: list[str] | None = None
    tenant: str | None = None
    superseded: bool | None = None
    audience: list[str] | None = None

    def is_empty(self) -> bool:
        return all(
            v is None for v in (
                self.category, self.source, self.topic, self.acl_groups,
                self.ingested_after, self.ingested_before, self.doc_version,
                self.domain, self.tenant, self.superseded, self.audience
            )
        )


class FusionConfig(BaseModel):
    # None = "not overridden by the request"; the orchestrator falls back to config.
    method: Literal["rrf", "weighted", "dbsf"] | None = None
    k: float | None = None
    weights: dict[str, float] | None = None


class SearchRequest(BaseModel):
    query: str
    mode: Literal["dense", "sparse", "hybrid", "hybrid_rerank", "hybrid_colbert"] = "hybrid"
    top_k: int = 5
    filters: Filters = Field(default_factory=Filters)
    fusion: FusionConfig = Field(default_factory=FusionConfig)
    user: dict[str, Any] = Field(default_factory=dict)
    explain: bool = False
    use_cache: bool = True
    latency_budget_ms: int = 250
    route: Literal["auto", "off", "force"] = "auto"
    domain_hint: str | None = None
    session: dict[str, Any] = Field(default_factory=dict)
    as_of: str | None = None


class Passage(BaseModel):
    """A document chunk to index."""

    passage_id: str
    text: str
    source: str = "msmarco"
    category: str = "unknown"
    topic: str | None = None
    acl_groups: list[str] = Field(default_factory=list)
    doc_version: int = 1
    ingested_at: str | None = None
    label_origin: str = "native"  # native | derived | synthetic
    
    # Banking specific fields
    domain: str | None = None
    audience: str | None = None
    product_ids: list[str] = Field(default_factory=list)
    effective_from: str | None = None
    superseded: bool = False
    tenant: str = "bank_default"


class ScoredPassage(BaseModel):
    """A passage as returned by retrieval, with scores and per-leg diagnostics."""

    passage_id: str
    text: str
    score: float
    rank: int
    metadata: dict[str, Any] = Field(default_factory=dict)
    dense_score: float | None = None
    dense_rank: int | None = None
    sparse_score: float | None = None
    sparse_rank: int | None = None
    rerank_score: float | None = None
    highlights: list[str] = Field(default_factory=list)


class Timings(BaseModel):
    """Per-stage timings in milliseconds."""

    embed: float | None = None
    retrieve: float | None = None
    rerank: float | None = None
    total: float | None = None


class SearchResult(BaseModel):
    request_id: str
    mode: str
    results: list[ScoredPassage]
    timings_ms: Timings
    cache_hit: bool = False
    degraded: bool = False
    config_hash: str = ""
    route_result: dict | None = None
    needs_clarification: bool = False
    clarification_options: list[str] = Field(default_factory=list)


class Answer(BaseModel):
    answer: str | None = None
    citations: list[int] = Field(default_factory=list)
    passages: list[ScoredPassage] = Field(default_factory=list)
    abstained: bool = False
    reason: str | None = None
    fallback: bool = False
