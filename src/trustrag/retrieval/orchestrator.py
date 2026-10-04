"""Retrieval orchestrator: wires the ports together, applies mode logic, fusion,
reranking (with a latency budget guard), caching and per-stage timing.

Depends only on the ports, so it is unit-testable with the in-memory store.
"""
from __future__ import annotations

import time
import uuid
from typing import Any

from ..core.cache_key import cache_key
from ..core.fusion import fuse, sort_by_fused
from ..core.models import Filters, ScoredPassage, SearchRequest, SearchResult, Timings
from ..core.ports import Cache, Embedder, Generator, Reranker, SparseEncoder, VectorStore
from .explain import matched_terms

try:
    from ..routing.router import LexicalRouter
except ImportError:
    LexicalRouter = None

class RetrievalOrchestrator:
    def __init__(
        self,
        embedder: Embedder,
        sparse_encoder: SparseEncoder,
        store: VectorStore,
        reranker: Reranker | None = None,
        colbert_reranker = None,
        cache: Cache | None = None,
        generator: Generator | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.embedder = embedder
        self.sparse = sparse_encoder
        self.store = store
        self.reranker = reranker
        self.colbert_reranker = colbert_reranker
        self.cache = cache
        self.generator = generator
        self.cfg = config or {}
        self._config_hash = ""
        self.router = LexicalRouter() if LexicalRouter else None

    def set_config_hash(self, value: str) -> None:
        self._config_hash = value

    # ------------------------------------------------------------------ search
    def search(self, request: SearchRequest) -> SearchResult:
        t0 = time.perf_counter()
        groups = list(request.user.get("groups", []))
        if groups and request.filters.acl_groups is None:
            # permission-aware retrieval: the caller's groups become a pre-retrieval filter
            request.filters.acl_groups = list(groups)
            
        # ALWAYS-ON BANKING FILTERS
        if getattr(request, "session", None):
            if "tenant" in request.session and getattr(request.filters, "tenant", None) is None:
                setattr(request.filters, "tenant", request.session["tenant"])
            if "audience" in request.session and getattr(request.filters, "audience", None) is None:
                setattr(request.filters, "audience", request.session["audience"])
        if getattr(request.filters, "superseded", None) is None and getattr(request, "as_of", None) is None:
            setattr(request.filters, "superseded", False)
            
        # -- ROUTING INJECTION --
        route_res = None
        needs_clarification = False
        clarification_options = []
        if request.route != "off" and self.router is not None:
            try:
                route_res = self.router.route(request.query)
                # Inject filters
                if route_res.filters_applied:
                    for k, v in route_res.filters_applied.items():
                        setattr(request.filters, k, v)
                needs_clarification = route_res.needs_clarification
                clarification_options = route_res.clarification_options
            except Exception as e:
                # Safe Fallback
                print(f"Router failed: {e}. Falling back to global hybrid.")
                
        filters_dict = request.filters.model_dump()

        # 1. cache (exact-match)
        if request.use_cache and self.cache is not None:
            key = cache_key(
                request.query, request.mode, filters_dict, groups, self.store.index_version(), request.top_k
            )
            hit = self.cache.get(key)
            if isinstance(hit, SearchResult):
                hit.cache_hit = True
                return hit

        timings = Timings()

        # 2. encode query
        t = time.perf_counter()
        dense_vec = self.embedder.embed_queries([request.query])[0] if request.mode != "sparse" else None
        sparse_vec = self.sparse.encode_queries([request.query])[0] if request.mode != "dense" else None
        timings.embed = round((time.perf_counter() - t) * 1000, 2)

        # 3. retrieve + fuse
        t = time.perf_counter()
        degraded = False
        if request.mode == "colbert" and self.colbert_reranker is not None:
            n = int(self.cfg.get("rerank", {}).get("candidates", 30))
            pool = self._retrieve(request, dense_vec, sparse_vec, candidate_limit=n)
            results = self.colbert_reranker.rerank(request.query, pool)[: request.top_k]
            timings.rerank = round((time.perf_counter() - t) * 1000, 2)
            degraded = self._over_budget(t0, request.latency_budget_ms)
        elif request.mode == "hybrid_rerank" and self.reranker is not None:
            n = int(self.cfg.get("rerank", {}).get("candidates", 30))
            pool = self._retrieve(request, dense_vec, sparse_vec, candidate_limit=n)
            results = self.reranker.rerank(request.query, pool)[: request.top_k]
            timings.rerank = round((time.perf_counter() - t) * 1000, 2)
            degraded = self._over_budget(t0, request.latency_budget_ms)
        else:
            results = self._retrieve(request, dense_vec, sparse_vec)
            
        # -- ROUTING RETRY FALLBACK --
        if len(results) < request.top_k and route_res and route_res.strategy != "fallback":
            # Clear the filter and retry globally
            request.filters.domain = None
            route_res.retries += 1
            route_res.strategy = "fallback"
            
            if request.mode == "colbert" and self.colbert_reranker is not None:
                pool = self._retrieve(request, dense_vec, sparse_vec, candidate_limit=n)
                results = self.colbert_reranker.rerank(request.query, pool)[: request.top_k]
            elif request.mode == "hybrid_rerank" and self.reranker is not None:
                pool = self._retrieve(request, dense_vec, sparse_vec, candidate_limit=n)
                results = self.reranker.rerank(request.query, pool)[: request.top_k]
            else:
                results = self._retrieve(request, dense_vec, sparse_vec)
                
        timings.retrieve = round((time.perf_counter() - t) * 1000, 2)

        # 4. explain highlights
        if request.explain:
            for r in results:
                r.highlights = matched_terms(request.query, r.text)

        timings.total = round((time.perf_counter() - t0) * 1000, 2)
        result = SearchResult(
            request_id=str(uuid.uuid4()),
            mode=request.mode,
            results=self._finalize(results, request.top_k),
            timings_ms=timings,
            degraded=degraded,
            config_hash=self._config_hash,
            route_result=route_res.model_dump() if route_res else None,
            needs_clarification=needs_clarification,
            clarification_options=clarification_options
        )

        # 5. cache store
        if request.use_cache and self.cache is not None:
            key = cache_key(
                request.query, request.mode, filters_dict, groups, self.store.index_version(), request.top_k
            )
            self.cache.put(key, result)
            if dense_vec is not None and hasattr(self.cache, "put_semantic"):
                self.cache.put_semantic(dense_vec, key)  # type: ignore[attr-defined]

        return result

    # ------------------------------------------------------------- internals
    def _retrieve(
        self,
        request: SearchRequest,
        dense_vec,
        sparse_vec,
        candidate_limit: int | None = None,
    ) -> list[ScoredPassage]:
        cfg = self.cfg
        dl = candidate_limit or int(cfg.get("dense", {}).get("prefetch_limit", 50))
        sl = candidate_limit or int(cfg.get("sparse", {}).get("prefetch_limit", 50))

        if request.mode == "dense":
            return self.store.search_dense(dense_vec, request.top_k, request.filters)
        if request.mode == "sparse":
            return self.store.search_sparse(sparse_vec, request.top_k, request.filters)

        # hybrid (+ rerank): two legs, fused, filter applied inside each store call.
        # Config drives behaviour; the request only overrides when it sets a value.
        fusion_cfg = cfg.get("fusion", {}) or {}
        method = request.fusion.method or fusion_cfg.get("method", "rrf")
        k = request.fusion.k if request.fusion.k is not None else float(fusion_cfg.get("k", 60.0))
        weights = request.fusion.weights or fusion_cfg.get("weights", {"dense": 1.0, "sparse": 1.0})
        dense_leg = self.store.search_dense(dense_vec, dl, request.filters)
        sparse_leg = self.store.search_sparse(sparse_vec, sl, request.filters)
        fused = fuse({"dense": dense_leg, "sparse": sparse_leg}, method=method, k=k, weights=weights)
        top = candidate_limit or request.top_k
        return sort_by_fused({"dense": dense_leg, "sparse": sparse_leg}, fused, top)

    def _over_budget(self, t0: float, budget_ms: int) -> bool:
        return (time.perf_counter() - t0) * 1000 > budget_ms

    def _finalize(self, results: list[ScoredPassage], top_k: int) -> list[ScoredPassage]:
        for i, r in enumerate(results[:top_k], start=1):
            r.rank = i
        return results[:top_k]

    # ------------------------------------------------------------------ answer
    def retrieve(
        self,
        query: str,
        mode: str = "hybrid",
        top_k: int = 5,
        filters: Filters | None = None,
    ) -> list[ScoredPassage]:
        request = SearchRequest(
            query=query, mode=mode, top_k=top_k, filters=filters or Filters(), use_cache=False
        )
        dense_vec = self.embedder.embed_queries([query])[0] if mode != "sparse" else None
        sparse_vec = self.sparse.encode_queries([query])[0] if mode != "dense" else None
        if mode == "colbert" and self.colbert_reranker is not None:
            n = int(self.cfg.get("rerank", {}).get("candidates", 30))
            pool = self._retrieve(request, dense_vec, sparse_vec, candidate_limit=n)
            return self.colbert_reranker.rerank(query, pool)[:top_k]
        if mode == "hybrid_rerank" and self.reranker is not None:
            n = int(self.cfg.get("rerank", {}).get("candidates", 30))
            pool = self._retrieve(request, dense_vec, sparse_vec, candidate_limit=n)
            return self.reranker.rerank(query, pool)[:top_k]
        return self._retrieve(request, dense_vec, sparse_vec)
