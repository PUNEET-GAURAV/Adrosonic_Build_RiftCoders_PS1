"""Answerer: retrieval -> evidence gate -> grounded generation -> citation check,
with an extractive fallback so a missing/rate-limited LLM never crashes the request.
"""
from __future__ import annotations

import re
from typing import Any

from ..core.models import Answer, Filters, ScoredPassage

_CITE_RE = re.compile(r"\[(\d+)\]")


class Answerer:
    def __init__(self, orchestrator, generator=None, config: dict[str, Any] | None = None) -> None:
        self.orchestrator = orchestrator
        self.generator = generator
        self.cfg = config or {}

    def answer(
        self,
        query: str,
        mode: str = "hybrid",
        top_k: int = 5,
        filters: Filters | None = None,
    ) -> Answer:
        passages = self.orchestrator.retrieve(query, mode=mode, top_k=top_k, filters=filters)
        if not passages:
            return Answer(abstained=True, reason="no passages retrieved")

        # evidence gate (threshold calibrated on the dev split)
        if not self._sufficient_evidence(passages):
            return Answer(abstained=True, reason="insufficient evidence", passages=passages)

        if self.generator is None:
            return self._extractive(passages)

        text = self.generator.generate(query, passages)
        if text is None:
            return self._extractive(passages)
        if "INSUFFICIENT_EVIDENCE" in text.upper():
            return Answer(abstained=True, reason="insufficient evidence", passages=passages)

        citations = self._extract_citations(text, len(passages))
        return Answer(answer=text, citations=citations, passages=passages)

    # ------------------------------------------------------------- helpers
    def _sufficient_evidence(self, passages: list[ScoredPassage]) -> bool:
        threshold = self.cfg.get("answering", {}).get("evidence_threshold")
        if threshold is None:
            return True
        return passages[0].score >= float(threshold)

    def _extractive(self, passages: list[ScoredPassage]) -> Answer:
        snippet = passages[0].text[:600].strip()
        return Answer(answer=snippet, citations=[1], fallback=True, passages=passages)

    def _extract_citations(self, text: str, n_passages: int) -> list[int]:
        cites = sorted({int(m) for m in _CITE_RE.findall(text) if 1 <= int(m) <= n_passages})
        return cites
