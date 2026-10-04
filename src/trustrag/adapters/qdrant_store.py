"""Qdrant adapter: dense + sparse + payload on a single point.

Implements the VectorStore port. The collection is created with BOTH a dense vector and a
BM25 sparse vector from the start, so no re-indexing is needed for hybrid search (ADR-001).
"""
from __future__ import annotations

from typing import Sequence

from ..core.ids import passage_uuid
from ..core.models import DenseVector, Filters, Passage, ScoredPassage, SparseVector

try:
    from qdrant_client import QdrantClient, models
except ImportError:  # pragma: no cover - only when running without qdrant-client
    QdrantClient = None  # type: ignore
    models = None  # type: ignore

DENSE = "dense"
SPARSE = "bm25"


def _to_qdrant_filter(filters: Filters):
    """Translate a domain Filters into a Qdrant Filter (empty Filters -> None)."""
    if filters.is_empty():
        return None
    must = []
    if filters.category:
        must.append(models.FieldCondition(key="category", match=models.MatchAny(any=filters.category)))
    if filters.source:
        must.append(models.FieldCondition(key="source", match=models.MatchAny(any=filters.source)))
    if filters.topic:
        must.append(models.FieldCondition(key="topic", match=models.MatchAny(any=filters.topic)))
    if filters.acl_groups:
        must.append(models.FieldCondition(key="acl_groups", match=models.MatchAny(any=filters.acl_groups)))
    if filters.ingested_after:
        must.append(
            models.FieldCondition(
                key="ingested_at", range=models.DatetimeRange(gte=filters.ingested_after)
            )
        )
    if filters.ingested_before:
        must.append(
            models.FieldCondition(
                key="ingested_at", range=models.DatetimeRange(lte=filters.ingested_before)
            )
        )
    if filters.doc_version is not None:
        must.append(models.FieldCondition(key="doc_version", match=models.MatchValue(value=filters.doc_version)))
    if filters.domain:
        must.append(models.FieldCondition(key="domain", match=models.MatchAny(any=filters.domain)))
    if filters.audience:
        must.append(models.FieldCondition(key="audience", match=models.MatchAny(any=filters.audience)))
    if filters.tenant is not None:
        must.append(models.FieldCondition(key="tenant", match=models.MatchValue(value=filters.tenant)))
    if filters.superseded is not None:
        must.append(models.FieldCondition(key="superseded", match=models.MatchValue(value=filters.superseded)))
    return models.Filter(must=must) if must else None


class QdrantStore:
    def __init__(
        self,
        url: str,
        collection: str = "passages",
        dense_size: int = 384,
        index_version: int = 0,
    ) -> None:
        self.client = QdrantClient(url=url)
        self.collection = collection
        self.dense_size = dense_size
        self._index_version = index_version
        self._ensure_collection()

    # -- setup -------------------------------------------------------------
    def _ensure_collection(self) -> None:
        if self.client.collection_exists(self.collection):
            return
        self.client.create_collection(
            collection_name=self.collection,
            vectors_config={
                DENSE: models.VectorParams(size=self.dense_size, distance=models.Distance.COSINE)
            },
            sparse_vectors_config={
                SPARSE: models.SparseVectorParams(modifier=models.Modifier.IDF)
            },
        )
        for field, schema in [
            ("category", models.PayloadSchemaType.KEYWORD),
            ("source", models.PayloadSchemaType.KEYWORD),
            ("topic", models.PayloadSchemaType.KEYWORD),
            ("acl_groups", models.PayloadSchemaType.KEYWORD),
            ("ingested_at", models.PayloadSchemaType.DATETIME),
            ("doc_version", models.PayloadSchemaType.INTEGER),
            ("domain", models.PayloadSchemaType.KEYWORD),
            ("audience", models.PayloadSchemaType.KEYWORD),
            ("tenant", models.PayloadSchemaType.KEYWORD),
            ("superseded", models.PayloadSchemaType.BOOL),
        ]:
            self.client.create_payload_index(self.collection, field, field_schema=schema)

    # -- VectorStore port ---------------------------------------------------
    def upsert(
        self,
        passages: Sequence[Passage],
        dense: Sequence[DenseVector],
        sparse: Sequence[SparseVector],
    ) -> None:
        points = []
        for p, d, s in zip(passages, dense, sparse):
            points.append(
                models.PointStruct(
                    id=passage_uuid(p.passage_id),
                    vector={
                        DENSE: d,
                        SPARSE: models.SparseVector(indices=s.indices, values=s.values),
                    },
                    payload={
                        "passage_id": p.passage_id,
                        "text": p.text,
                        "source": p.source,
                        "category": p.category,
                        "topic": p.topic,
                        "acl_groups": p.acl_groups,
                        "doc_version": p.doc_version,
                        "ingested_at": p.ingested_at,
                        "label_origin": p.label_origin,
                        "domain": p.domain,
                        "audience": p.audience,
                        "tenant": p.tenant,
                        "superseded": p.superseded,
                    },
                )
            )
        self.client.upsert(collection_name=self.collection, points=points, wait=True)
        self._index_version += 1

    def delete(self, passage_ids: Sequence[str]) -> None:
        uuids = [passage_uuid(pid) for pid in passage_ids]
        self.client.delete(
            collection_name=self.collection,
            points_selector=models.PointIdsList(points=uuids),
            wait=True,
        )
        self._index_version += 1

    def count(self) -> int:
        return self.client.count(collection_name=self.collection, exact=True).count

    def search_dense(self, vector: DenseVector, top_k: int, filters: Filters) -> list[ScoredPassage]:
        res = self.client.query_points(
            collection_name=self.collection,
            query=vector,
            using=DENSE,
            limit=top_k,
            query_filter=_to_qdrant_filter(filters),
            with_payload=True,
        )
        return self._to_scored(res, DENSE)

    def search_sparse(self, vector: SparseVector, top_k: int, filters: Filters) -> list[ScoredPassage]:
        res = self.client.query_points(
            collection_name=self.collection,
            query=models.SparseVector(indices=vector.indices, values=vector.values),
            using=SPARSE,
            limit=top_k,
            query_filter=_to_qdrant_filter(filters),
            with_payload=True,
        )
        return self._to_scored(res, SPARSE)

    def index_version(self) -> int:
        return self._index_version

    def bump_index_version(self) -> int:
        self._index_version += 1
        return self._index_version

    # -- helpers ------------------------------------------------------------
    def _to_scored(self, res, leg: str) -> list[ScoredPassage]:
        out: list[ScoredPassage] = []
        for rank, pt in enumerate(res.points, start=1):
            payload = pt.payload or {}
            sp = ScoredPassage(
                passage_id=payload.get("passage_id", str(pt.id)),
                text=payload.get("text", ""),
                score=float(pt.score),
                rank=rank,
                metadata={
                    "category": payload.get("category"),
                    "source": payload.get("source"),
                    "topic": payload.get("topic"),
                    "doc_version": payload.get("doc_version"),
                    "domain": payload.get("domain"),
                    "audience": payload.get("audience"),
                    "tenant": payload.get("tenant"),
                    "superseded": payload.get("superseded"),
                },
            )
            if leg == DENSE:
                sp.dense_score = float(pt.score)
                sp.dense_rank = rank
            else:
                sp.sparse_score = float(pt.score)
                sp.sparse_rank = rank
            out.append(sp)
        return out
