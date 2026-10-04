"""Cross-encoder reranker (ms-marco MiniLM) using Optimum ONNX Runtime for blazing fast CPU inference."""
from __future__ import annotations

from typing import Sequence
import numpy as np

from ..core.models import ScoredPassage

class CrossEncoderReranker:
    def __init__(self, model_name: str) -> None:
        from optimum.onnxruntime import ORTModelForSequenceClassification
        from transformers import AutoTokenizer
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        # Load the ONNX model (it will auto-export or pull the onnx variant if available)
        try:
            self.model = ORTModelForSequenceClassification.from_pretrained(model_name, export=True)
        except Exception:
            # Fallback if export fails, though it usually succeeds for standard HF models
            self.model = ORTModelForSequenceClassification.from_pretrained(model_name)

    def rerank(self, query: str, passages: Sequence[ScoredPassage]) -> list[ScoredPassage]:
        if not passages:
            return []
            
        pairs = [[query, p.text] for p in passages]
        inputs = self.tokenizer(pairs, padding=True, truncation=True, return_tensors="pt")
        
        import torch
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits.squeeze(-1).numpy()
            
        scores = logits.tolist()
        if isinstance(scores, float):
            scores = [scores]
            
        scored = sorted(zip(scores, passages), key=lambda t: -float(t[0]))
        out: list[ScoredPassage] = []
        for rank, (s, p) in enumerate(scored, start=1):
            p.score = float(s)
            p.rerank_score = float(s)
            p.rank = rank
            out.append(p)
        return out
