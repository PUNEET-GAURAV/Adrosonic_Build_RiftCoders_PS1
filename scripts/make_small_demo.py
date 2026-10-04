"""Index a tiny deterministic demo corpus into the in-memory store (no Docker, no network).

Used to smoke-test the orchestrator end-to-end and for the 10k `make demo-small` path.
"""
from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from trustrag.adapters.bm25_sparse import BM25SparseEncoder  # noqa: E402
from trustrag.adapters.in_memory_store import InMemoryStore  # noqa: E402
from trustrag.adapters.st_embedder import SentenceTransformerEmbedder  # noqa: E402
from trustrag.core.models import Passage, SearchRequest  # noqa: E402
from trustrag.retrieval.orchestrator import RetrievalOrchestrator  # noqa: E402

CORPUS = [
    ("p1", "The capital of France is Paris.", "NUMERIC"),
    ("p2", "Paris is known for the Eiffel Tower.", "DESCRIPTION"),
    ("p3", "The capital of Japan is Tokyo.", "NUMERIC"),
    ("p4", "Boiling an egg typically takes ten minutes.", "NUMERIC"),
    ("p5", "Apples are a common fruit grown in orchards.", "DESCRIPTION"),
]


def main() -> None:
    from trustrag.adapters.qdrant_store import QdrantStore
    store = QdrantStore("http://localhost:6333", "passages")
    embedder = SentenceTransformerEmbedder("BAAI/bge-small-en-v1.5")
    sparse = BM25SparseEncoder()
    orch = RetrievalOrchestrator(embedder, sparse, store, config={})

    passages = [Passage(passage_id=pid, text=text, category=cat) for pid, text, cat in CORPUS]
    dense = embedder.embed_documents([p.text for p in passages])
    sp = sparse.encode_documents([p.text for p in passages])
    store.upsert(passages, dense, sp)

    for q in ["What is the capital of France?", "How long to boil an egg?"]:
        r = orch.search(SearchRequest(query=q, mode="hybrid", top_k=3))
        print(f"\nQ: {q}")
        for item in r.results:
            print(f"  #{item.rank} {item.passage_id} ({item.score:.4f}): {item.text}")


if __name__ == "__main__":
    main()
