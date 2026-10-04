"""Build docs/BENCHMARK_REPORT.md from results/ only (no hand-typed numbers)."""
from __future__ import annotations

import json
from pathlib import Path

_RESULTS = Path(__file__).resolve().parents[3] / "results"
_DOCS = Path(__file__).resolve().parents[3] / "docs"


def _load(name_part: str) -> dict | None:
    for p in _RESULTS.glob("*.json"):
        if name_part in p.name:
            return json.loads(p.read_text(encoding="utf-8"))
    return None


def _latency_row(name_part: str) -> str:
    data = _load(name_part)
    if not data:
        return "| — | — |"
    s = data.get("summary", data)
    return (
        f"| {s.get('mode', '?')} | {s.get('n', '?')} | {s.get('p50', '—')} | "
        f"{s.get('p95', '—')} | {s.get('p99', '—')} | {s.get('max', '—')} |"
    )


def generate() -> str:
    lines = [
        "# Benchmark Report — TrustRAG",
        "",
        "> Generated from `results/` only. Every number traces to a committed result file.",
        "",
        "## Retrieval quality",
        "",
        "| Mode | Context Precision | Context Recall | P@5 | R@5 | MRR@10 | nDCG@10 |",
        "|---|---|---|---|---|---|---|",
    ]
    for mode in ["dense", "sparse", "hybrid", "hybrid_rerank"]:
        rag = _load(f"ragas_{mode}") or {}
        agg = rag.get("aggregate", rag)
        ir = _load(f"ir_{mode}") or {}
        ir_agg = ir.get("aggregate", ir)
        lines.append(
            f"| {mode} | {agg.get('context_precision', '—')} | {agg.get('context_recall', '—')} | "
            f"{ir_agg.get('precision_at_5', '—')} | {ir_agg.get('recall_at_5', '—')} | "
            f"{ir_agg.get('mrr', '—')} | {ir_agg.get('ndcg', '—')} |"
        )

    lines += [
        "",
        "## Latency (100 consecutive queries, HTTP API)",
        "",
        "| Mode | n | p50 (ms) | p95 (ms) | p99 (ms) | max (ms) |",
        "|---|---|---|---|---|---|",
        _latency_row("latency_dense"),
        _latency_row("latency_hybrid"),
        _latency_row("latency_hybrid_rerank"),
        _latency_row("latency_cache"),
        "",
        "## Methodology",
        "",
        "- Eval set: seed-42 pool (dev 200 / test 400), MS MARCO validation queries with a selected passage.",
        "- Tuned only on dev; reported numbers are on the held-out test split.",
        "- RAGAS: LLM-judged (Groq free tier, temperature 0) and non-LLM (token overlap) variants.",
        "- Official p95: hybrid mode, cache off, 100 distinct queries, idle machine.",
        "",
    ]
    return "\n".join(lines)


def write_report() -> str:
    _DOCS.mkdir(parents=True, exist_ok=True)
    text = generate()
    (_DOCS / "BENCHMARK_REPORT.md").write_text(text, encoding="utf-8")
    return text
