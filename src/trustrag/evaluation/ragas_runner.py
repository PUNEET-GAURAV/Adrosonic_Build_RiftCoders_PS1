"""RAGAS-style evaluation runner.

Two judge modes:
- ``llm``: per-passage relevance is judged by an LLM (Groq free tier) against the
  reference answer; computes Context Precision and Context Recall.
- ``non-llm``: relevance is approximated by token overlap (metrics.token_overlap_relevant);
  deterministic and rate-limit-proof.

If the ``ragas`` package is installed, ``llm`` mode can optionally delegate to its official
metrics; by default we use our own faithful re-implementation to avoid version churn.
"""
from __future__ import annotations

import json
import time
from typing import Any, Callable

from ..core.models import SearchResult
from .metrics import (
    context_precision_from_relevance,
    context_recall_from_relevance,
    token_overlap_relevant,
)

_CP_PROMPT = (
    "Question: {question}\nReference answer: {reference}\n"
    "Passage: {passage}\n"
    "Is this passage relevant to answering the question? Reply exactly YES or NO."
)


def judge_relevance_llm(judge: Callable[[str], str], question: str, reference: str, passage: str) -> bool:
    prompt = _CP_PROMPT.format(question=question, reference=reference, passage=passage)
    out = (judge(prompt) or "").strip().upper()
    return out.startswith("YES")


def evaluate_query(
    question: str,
    reference: str,
    retrieved: list[str],
    passages: dict[str, str],
    judge: Callable[[str, str, str], bool] | None,
    total_relevant: int,
) -> dict[str, float]:
    relevances: list[bool] = []
    for pid in retrieved:
        text = passages.get(pid, "")
        if judge is not None:
            rel = judge(question, reference, text)
        else:
            rel = token_overlap_relevant(reference, text)
        relevances.append(rel)
    return {
        "context_precision": context_precision_from_relevance(relevances),
        "context_recall": context_recall_from_relevance(relevances, total_relevant),
    }


class RagasRunner:
    def __init__(
        self,
        results_by_query: dict[str, SearchResult],
        passages: dict[str, str],
        judge: Callable[[str, str, str], bool] | None = None,
        config: dict[str, Any] | None = None,
    ) -> None:
        self.results = results_by_query
        self.passages = passages
        self.judge = judge
        self.cfg = config or {}

    def run(self, queries: list[dict]) -> tuple[dict[str, dict], dict[str, float]]:
        per_query: dict[str, dict] = {}
        cp_sum = cr_sum = 0.0
        n = 0
        for q in queries:
            qid = q["query_id"]
            result = self.results.get(qid)
            if result is None:
                continue
            retrieved = [r.passage_id for r in result.results]
            metrics = evaluate_query(
                q["query"],
                q["reference_answer"],
                retrieved,
                self.passages,
                self.judge,
                q.get("total_relevant", len(q.get("gold_passage_ids", []))),
            )
            per_query[qid] = metrics
            cp_sum += metrics["context_precision"]
            cr_sum += metrics["context_recall"]
            n += 1
        aggregate = {
            "context_precision": cp_sum / n if n else 0.0,
            "context_recall": cr_sum / n if n else 0.0,
            "n_queries": n,
        }
        return per_query, aggregate


def make_groq_judge(client, model: str) -> Callable[[str], str]:
    def _judge(prompt: str) -> str:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=4,
        )
        return resp.choices[0].message.content

    return _judge


def save_result(path: str, payload: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
