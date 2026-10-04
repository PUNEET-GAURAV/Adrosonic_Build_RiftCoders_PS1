"""Self-contained BM25 sparse encoder.

Stores raw term frequencies as sparse indices (stable 32-bit token hashes). Qdrant's
``Modifier.IDF`` computes inverse-document frequency server-side over the live corpus,
so live upserts/deletes keep BM25 statistics current without re-indexing. This avoids the
``fastembed`` + ``onnxruntime`` dependency entirely. See ADR-002.
"""
from __future__ import annotations

from typing import Sequence

from ..core.models import SparseVector
from ..core.text import term_frequencies


class BM25SparseEncoder:
    def __init__(self, hash_bits: int = 32) -> None:
        self.hash_bits = hash_bits

    def encode_documents(self, texts: Sequence[str]) -> list[SparseVector]:
        return [self._encode(t) for t in texts]

    def encode_queries(self, texts: Sequence[str]) -> list[SparseVector]:
        return [self._encode(t) for t in texts]

    def _encode(self, text: str) -> SparseVector:
        tf = term_frequencies(text)
        indices = sorted(tf)
        return SparseVector(indices=indices, values=[float(tf[i]) for i in indices])
