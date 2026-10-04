"""Grounded-answer generator via the Groq free tier. Returns None on any failure so the
orchestrator can fall back to an extractive answer (never crash the request).
"""
from __future__ import annotations

from typing import Sequence

from ..core.models import ScoredPassage

_GROUNDED_PROMPT = """Answer the question using ONLY the numbered passages below.
If the passages do not contain enough evidence, reply exactly: INSUFFICIENT_EVIDENCE.
Otherwise answer concisely and cite the passage numbers you used as [n].

Question: {query}

Passages:
{context}

Answer:"""


class GroqGenerator:
    def __init__(self, api_key: str | None, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self.client = None
        if api_key:
            from groq import Groq  # local import

            self.client = Groq(api_key=api_key)

    def generate(self, query: str, passages: Sequence[ScoredPassage]) -> str | None:
        if self.client is None:
            return None
        context = "\n\n".join(f"[{i + 1}] {p.text}" for i, p in enumerate(passages))
        prompt = _GROUNDED_PROMPT.format(query=query, context=context)
        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=256,
            )
            return resp.choices[0].message.content
        except Exception:
            return None
