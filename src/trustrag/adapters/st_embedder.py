"""Sentence-transformers dense embedder (BGE-small)."""
from __future__ import annotations

from typing import Sequence

from ..core.models import DenseVector


class SentenceTransformerEmbedder:
    def __init__(
        self,
        model_name: str,
        query_prefix: str = "",
        device: str | None = None,
        normalize: bool = True,
    ) -> None:
        from sentence_transformers import SentenceTransformer  # local import: heavy

        self.model = SentenceTransformer(model_name, device=device)
        self.query_prefix = query_prefix
        self.normalize = normalize

    def embed_documents(self, texts: Sequence[str]) -> list[DenseVector]:
        return self.model.encode(
            list(texts),
            normalize_embeddings=self.normalize,
            show_progress_bar=False,
            batch_size=64,
        ).tolist()

    def embed_queries(self, queries: Sequence[str]) -> list[DenseVector]:
        prefixed = [self.query_prefix + q for q in queries]
        return self.model.encode(
            prefixed,
            normalize_embeddings=self.normalize,
            show_progress_bar=False,
            batch_size=64,
        ).tolist()
