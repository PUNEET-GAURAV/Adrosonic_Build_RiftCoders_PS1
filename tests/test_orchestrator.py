"""Orchestrator integration tests (in-memory store + deterministic fake embedder).

Runs under pytest after `pip install -e .` (needs pydantic, which is a base dependency).
No Qdrant, no network, no model download — this validates the full search/filter/
live-update/answer path before any heavy dependency is touched.
"""
from __future__ import annotations

import hashlib

from trustrag.adapters.bm25_sparse import BM25SparseEncoder
from trustrag.adapters.in_memory_store import InMemoryStore
from trustrag.adapters.memory_cache import MemoryCache
from trustrag.answering.answerer import Answerer
from trustrag.core.models import Filters, Passage, SearchRequest
from trustrag.core.text import normalize, tokenize
from trustrag.retrieval.orchestrator import RetrievalOrchestrator


class HashEmbedder:
    """Deterministic bag-of-words embedder: overlapping text -> higher cosine similarity."""

    def __init__(self, dim: int = 64, query_prefix: str = ""):
        self.dim = dim
        self.query_prefix = query_prefix

    def _embed(self, text: str) -> list[float]:
        v = [0.0] * self.dim
        for tok in tokenize(text):
            h = int(hashlib.md5(tok.encode()).hexdigest()[:8], 16)
            v[h % self.dim] += 1.0
        return normalize(v)

    def embed_documents(self, texts):
        return [self._embed(t) for t in texts]

    def embed_queries(self, queries):
        return [self._embed(self.query_prefix + q) for q in queries]


class FakeGenerator:
    def generate(self, query, passages):
        return "The capital of France is Paris [1]."


CORPUS = [
    ("p1", "the capital of france is paris", "NUMERIC"),
    ("p2", "paris has the eiffel tower", "DESCRIPTION"),
    ("p3", "the capital of japan is tokyo", "NUMERIC"),
    ("p4", "boiling an egg takes ten minutes", "NUMERIC"),
]


def make_stack():
    store = InMemoryStore()
    embedder = HashEmbedder()
    sparse = BM25SparseEncoder()
    cache = MemoryCache(maxsize=64)
    orch = RetrievalOrchestrator(embedder, sparse, store, cache=cache, config={})
    passages = [Passage(passage_id=pid, text=text, category=cat) for pid, text, cat in CORPUS]
    store.upsert(
        passages,
        embedder.embed_documents([p.text for p in passages]),
        sparse.encode_documents([p.text for p in passages]),
    )
    return orch, store


def test_dense_returns_top_k_with_expected_top():
    orch, _ = make_stack()
    r = orch.search(SearchRequest(query="what is the capital of france", mode="dense", top_k=3))
    assert len(r.results) == 3
    assert r.results[0].passage_id == "p1"


def test_hybrid_returns_top_k():
    orch, _ = make_stack()
    r = orch.search(SearchRequest(query="what is the capital of france", mode="hybrid", top_k=3))
    assert len(r.results) == 3
    ids = {x.passage_id for x in r.results}
    assert "p1" in ids


def test_filter_is_applied():
    orch, _ = make_stack()
    f = Filters(category=["NUMERIC"])
    r = orch.search(SearchRequest(query="capital", mode="hybrid", top_k=3, filters=f))
    assert all(x.metadata.get("category") == "NUMERIC" for x in r.results)
    assert all(x.passage_id != "p2" for x in r.results)


def test_upsert_and_delete():
    orch, store = make_stack()
    before = store.count()
    p = Passage(passage_id="p9", text="the unique zephyr flower blooms in spring", category="NUMERIC")
    store.upsert([p], orch.embedder.embed_documents([p.text]), orch.sparse.encode_documents([p.text]))
    assert store.count() == before + 1
    r = orch.search(SearchRequest(query="zephyr flower", mode="hybrid", top_k=1))
    assert r.results[0].passage_id == "p9"
    store.delete(["p9"])
    assert store.count() == before


def test_answer_with_citations():
    orch, store = make_stack()
    answerer = Answerer(orch, generator=FakeGenerator(), config={})
    a = answerer.answer("what is the capital of france", mode="hybrid", top_k=3)
    assert a.abstained is False
    assert a.citations == [1]
    assert "Paris" in a.answer


def test_answer_abstains_without_generator_and_no_passages():
    orch, store = make_stack()
    answerer = Answerer(orch, generator=None, config={})
    # empty store -> no passages -> abstain
    empty = InMemoryStore()
    orch2 = RetrievalOrchestrator(HashEmbedder(), BM25SparseEncoder(), empty, config={})
    a = Answerer(orch2, generator=None, config={}).answer("any query", mode="hybrid")
    assert a.abstained is True


def test_permission_aware_retrieval():
    """Caller groups become a pre-retrieval ACL filter (add-on AO-9)."""
    store = InMemoryStore()
    embedder = HashEmbedder()
    sparse = BM25SparseEncoder()
    orch = RetrievalOrchestrator(embedder, sparse, store, config={})
    passages = [
        Passage(passage_id="a", text="public policy document about claims", category="NUMERIC", acl_groups=["public"]),
        Passage(passage_id="b", text="confidential claims document", category="NUMERIC", acl_groups=["private"]),
    ]
    store.upsert(
        passages,
        embedder.embed_documents([p.text for p in passages]),
        sparse.encode_documents([p.text for p in passages]),
    )
    r = orch.search(SearchRequest(query="claims document", mode="hybrid", top_k=5, user={"groups": ["public"]}))
    ids = {x.passage_id for x in r.results}
    assert "a" in ids
    assert "b" not in ids  # private passage leaks through? must not.
