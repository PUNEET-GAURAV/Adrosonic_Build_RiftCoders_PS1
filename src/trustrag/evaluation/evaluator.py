"""End-to-end evaluation: retrieve on the eval set, compute IR + RAGAS metrics, write
result JSONs (schema from PRD section 8.3)."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

from ..core.models import ScoredPassage
from .metrics import hit_at_k, mrr, ndcg_at_k, precision_at_k, recall_at_k
from .ragas_runner import evaluate_query

_RESULTS = Path(__file__).resolve().parents[3] / "results"


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def run_eval(
    orchestrator,
    eval_rows: list[dict],
    mode: str,
    split: str,
    judge: Callable[[str, str, str], bool] | None,
    top_k: int = 5,
    config_hash: str = "",
    models: dict[str, str] | None = None,
) -> tuple[dict, dict]:
    per_query_ir: dict[str, dict] = {}
    per_query_ragas: dict[str, dict] = {}
    cp_sum = cr_sum = 0.0
    hit = recall = precision = mrr_sum = ndcg_sum = 0.0
    n = 0

    for row in eval_rows:
        if row.get("split") != split:
            continue
        results: list[ScoredPassage] = orchestrator.retrieve(row["query"], mode=mode, top_k=top_k)
        retrieved = [r.passage_id for r in results]
        gold = row["gold_passage_ids"]
        passages = {r.passage_id: r.text for r in results}

        ir = {
            "hit_at_5": hit_at_k(gold, retrieved, 5),
            "precision_at_5": precision_at_k(gold, retrieved, 5),
            "recall_at_5": recall_at_k(gold, retrieved, 5),
            "mrr": mrr(gold, retrieved, 10),
            "ndcg": ndcg_at_k(gold, retrieved, 10),
        }
        rag = evaluate_query(
            row["query"], row["reference_answer"], retrieved, passages, judge, row["total_relevant"]
        )
        per_query_ir[row["query_id"]] = ir
        per_query_ragas[row["query_id"]] = rag

        cp_sum += rag["context_precision"]
        cr_sum += rag["context_recall"]
        hit += ir["hit_at_5"]
        recall += ir["recall_at_5"]
        precision += ir["precision_at_5"]
        mrr_sum += ir["mrr"]
        ndcg_sum += ir["ndcg"]
        n += 1

    if n == 0:
        return {}, {}

    ir_agg = {
        "hit_at_5": hit / n, "precision_at_5": precision / n, "recall_at_5": recall / n,
        "mrr": mrr_sum / n, "ndcg": ndcg_sum / n, "n_queries": n,
    }
    ragas_agg = {
        "context_precision": cp_sum / n, "context_recall": cr_sum / n, "n_queries": n,
    }

    ir_payload = {
        "run_id": f"{time.strftime('%Y-%m-%dT%H-%M-%S')}_{mode}_{split}_ir",
        "git_sha": _git_sha(),
        "config_hash": config_hash,
        "mode": mode,
        "split": split,
        "n_queries": n,
        "top_k": top_k,
        "models": models or {},
        "aggregate": ir_agg,
        "per_query": per_query_ir,
    }
    ragas_payload = {
        "run_id": f"{time.strftime('%Y-%m-%dT%H-%M-%S')}_{mode}_{split}_ragas",
        "git_sha": _git_sha(),
        "config_hash": config_hash,
        "mode": mode,
        "split": split,
        "n_queries": n,
        "top_k": top_k,
        "models": models or {},
        "aggregate": ragas_agg,
        "per_query": per_query_ragas,
    }

    _RESULTS.mkdir(parents=True, exist_ok=True)
    (_RESULTS / f"ir_{mode}_{split}.json").write_text(json.dumps(ir_payload, indent=2), encoding="utf-8")
    (_RESULTS / f"ragas_{mode}_{split}.json").write_text(json.dumps(ragas_payload, indent=2), encoding="utf-8")
    return ragas_payload, ir_payload
