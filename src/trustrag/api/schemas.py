"""API request bodies beyond the core domain models."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ..core.models import Filters


class DocumentIn(BaseModel):
    text: str
    category: str = "user_upload"
    source: str = "manual"


class AnswerRequest(BaseModel):
    query: str
    mode: str = "hybrid"
    top_k: int = 5
    filters: Filters = Field(default_factory=Filters)


class DocumentUploadOut(BaseModel):
    source: str
    chunks: int
    index_version: int


class HealthOut(BaseModel):
    status: str
    collection_count: int
    index_version: int
    config_hash: str


class MetricsOut(BaseModel):
    index_version: int
    collection_count: int
    p50_ms: float | None = None
    p95_ms: float | None = None
    requests: int = 0
    cache_hits: int = 0
    degraded: int = 0
