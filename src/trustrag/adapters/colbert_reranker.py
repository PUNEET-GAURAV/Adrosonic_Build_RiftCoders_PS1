"""ColBERT late-interaction reranker using FastEmbed."""
from __future__ import annotations

from typing import Sequence
import numpy as np

from ..core.models import ScoredPassage

class ColbertReranker:
    def __init__(self, model_name: str = "colbert-ir/colbertv2.0") -> None:
        from fastembed import LateInteractionTextEmbedding
        self.model = LateInteractionTextEmbedding(model_name)

    def rerank(self, query: str, passages: Sequence[ScoredPassage]) -> list[ScoredPassage]:
        if not passages:
            return []
            
        # FastEmbed ColBERT expects to encode the query and documents separately,
        # but for a reranker we can just compute the late-interaction score.
        # Actually, fastembed's LateInteractionTextEmbedding yields vectors.
        # Let's generate query embeddings and document embeddings.
        query_emb = list(self.model.query_embed([query]))[0]
        
        doc_texts = [p.text for p in passages]
        doc_embs = list(self.model.passage_embed(doc_texts))
        
        # Late interaction scoring: MaxSim
        # query_emb: (query_len, dim)
        # doc_emb: (doc_len, dim)
        out = []
        for p, doc_emb in zip(passages, doc_embs):
            # cosine similarity across all tokens
            # query_emb is shape (Q, D), doc_emb is shape (N, D)
            # score = sum_{q in Q} max_{n in N} (q . n)
            sim = np.dot(query_emb, doc_emb.T)  # (Q, N)
            max_sim = np.max(sim, axis=1)       # (Q,)
            score = float(np.sum(max_sim))      # scalar
            
            p.score = score
            p.rerank_score = score
            out.append(p)
            
        scored = sorted(out, key=lambda x: -x.score)
        for rank, p in enumerate(scored, start=1):
            p.rank = rank
        return scored
