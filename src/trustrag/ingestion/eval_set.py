"""Build the committed eval set (seed 42, generated once, never regenerated)."""
from __future__ import annotations

import json
import random
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "eval"


def _is_good(row: dict) -> bool:
    if not row["answer"] or row["answer"].strip().lower() in ("", "no answer present."):
        return False
    return any(p["is_selected"] == 1 for p in row["passages"])


def build_eval_set(
    loader_iter,
    seed: int = 42,
    dev_size: int = 200,
    test_size: int = 400,
    path: str | Path | None = None,
) -> list[dict]:
    """Select queries with a gold passage + real answer, split into dev/test, and write
    ``data/eval/eval_queries.jsonl``. Returns the eval-query list (dev first, then test)."""
    good: list[dict] = []
    rng = random.Random(seed)
    for row in loader_iter:
        if _is_good(row):
            gold = [p["passage_id"] for p in row["passages"] if p["is_selected"] == 1]
            good.append(
                {
                    "query_id": row["query_id"],
                    "query": row["query"],
                    "category": row["query_type"],
                    "reference_answer": row["answer"],
                    "gold_passage_ids": gold,
                    "total_relevant": len(gold),
                }
            )
        if len(good) >= dev_size + test_size:
            break

    rng.shuffle(good)
    dev = good[:dev_size]
    test = good[dev_size : dev_size + test_size]
    for item in dev:
        item["split"] = "dev"
    for item in test:
        item["split"] = "test"
    all_rows = dev + test

    out_path = Path(path) if path else _DATA_DIR / "eval_queries.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for item in all_rows:
            f.write(json.dumps(item) + "\n")
    return all_rows


def load_eval_set(path: str | Path | None = None) -> list[dict]:
    p = Path(path) if path else _DATA_DIR / "eval_queries.jsonl"
    with p.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def split_eval_set(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    dev = [r for r in rows if r.get("split") == "dev"]
    test = [r for r in rows if r.get("split") == "test"]
    return dev, test
