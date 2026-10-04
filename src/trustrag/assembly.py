"""Assemble the full stack from config + environment. Used by the API and the CLI.

This is the only place adapters are instantiated; the rest of the system sees ports.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from .config import config_hash, load_config


@dataclass
class Stack:
    orchestrator: Any
    store: Any
    embedder: Any
    sparse: Any
    cache: Any
    generator: Any
    config: dict[str, Any] = field(default_factory=dict)
    config_hash: str = ""


def build_stack(
    use_qdrant: bool = True,
    enable_reranker: bool | None = None,
    enable_cache: bool | None = None,
) -> Stack:
    from .adapters.bm25_sparse import BM25SparseEncoder
    from .adapters.ce_reranker import CrossEncoderReranker
    from .adapters.colbert_reranker import ColbertReranker
    from .adapters.groq_generator import GroqGenerator
    from .adapters.in_memory_store import InMemoryStore
    from .adapters.memory_cache import MemoryCache
    from .adapters.qdrant_store import QdrantStore
    from .adapters.st_embedder import SentenceTransformerEmbedder
    from .retrieval.orchestrator import RetrievalOrchestrator

    ret = load_config("retrieval")
    models = load_config("models")
    cfg = {**ret, **models}

    embedder = SentenceTransformerEmbedder(
        models["embedder"], query_prefix=ret.get("dense", {}).get("query_prefix", "")
    )
    sparse = BM25SparseEncoder(hash_bits=int(ret.get("sparse", {}).get("hash_bits", 32)))

    if use_qdrant:
        url = os.environ.get("QDRANT_URL", "http://localhost:6333")
        coll = os.environ.get("QDRANT_COLLECTION", "passages")
        store = QdrantStore(url, collection=coll)
    else:
        store = InMemoryStore()

    use_rerank = enable_reranker if enable_reranker is not None else bool(ret.get("rerank", {}).get("enabled"))
    reranker = CrossEncoderReranker(models["reranker"]) if use_rerank else None
    colbert_reranker = ColbertReranker()

    use_cache = enable_cache if enable_cache is not None else bool(ret.get("cache", {}).get("enabled"))
    cache = (
        MemoryCache(
            maxsize=int(ret.get("cache", {}).get("maxsize", 4096)),
            semantic_threshold=float(ret.get("cache", {}).get("semantic_threshold", 0.95)),
        )
        if use_cache
        else None
    )

    api_key = os.environ.get("GROQ_API_KEY") or ""
    if api_key:
        generator = GroqGenerator(api_key, models["generator_model"])
    elif str(os.environ.get("USE_LOCAL_LLM", "true")).lower() == "true":
        from .adapters.local_gpu_generator import LocalGPUGenerator
        generator = LocalGPUGenerator("HuggingFaceTB/SmolLM2-135M-Instruct") # Switched back to ultra-fast 0.5B model for CPU execution
    else:
        generator = None

    orch = RetrievalOrchestrator(
        embedder, sparse, store, reranker=reranker,
        colbert_reranker=colbert_reranker, cache=cache, generator=generator, config=cfg
    )
    h = config_hash(cfg)
    orch.set_config_hash(h)
    return Stack(
        orchestrator=orch,
        store=store,
        embedder=embedder,
        sparse=sparse,
        cache=cache,
        generator=generator,
        config=cfg,
        config_hash=h,
    )
