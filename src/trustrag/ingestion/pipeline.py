"""Batch ingestion pipeline: stream -> dedupe -> enrich -> embed -> sparse-encode -> upsert,
with a JSON checkpoint for idempotent, resumable runs and throughput logging.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from ..core.models import Passage

_RESULTS = Path(__file__).resolve().parents[3] / "results"


def _text_hash(text: str) -> str:
    return hashlib.sha1(text.strip().lower().encode("utf-8")).hexdigest()


def _load_state(path: Path) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"count": 0, "started_at": None}


def _save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state), encoding="utf-8")


def ingest_corpus(
    store,
    embedder,
    sparse_encoder,
    loader_iter,
    n: int,
    checkpoint_path: str | Path,
    source: str = "msmarco",
    batch_size: int = 256,
    topic_fn=None,
    log_every: int = 5000,
) -> dict[str, Any]:
    """Ingest up to ``n`` unique passages. Deterministic order + dedupe by text hash makes
    the 100k index a strict prefix of any larger index, and re-runs idempotent."""
    ckpt = Path(checkpoint_path)
    state = _load_state(ckpt)
    if state.get("started_at") is None:
        state["started_at"] = time.time()
    resume_skip = int(state["count"])

    seen: set[str] = set()
    buf_p: list[Passage] = []
    t_start = time.time()

    def flush() -> None:
        nonlocal buf_p
        if not buf_p:
            return
        dense = embedder.embed_documents([p.text for p in buf_p])
        sparse = sparse_encoder.encode_documents([p.text for p in buf_p])
        store.upsert(buf_p, dense, sparse)
        state["count"] += len(buf_p)
        _save_state(ckpt, state)
        buf_p = []

    for row in loader_iter:
        for pas in row["passages"]:
            if state["count"] >= n:
                flush()
                break
            h = _text_hash(pas["text"])
            if h in seen:
                continue
            seen.add(h)
            if resume_skip > 0:
                resume_skip -= 1
                continue
            p = Passage(
                passage_id=pas["passage_id"],
                text=pas["text"],
                source=source,
                category=row.get("query_type", "UNKNOWN"),
                label_origin="native",
            )
            buf_p.append(p)
            if len(buf_p) >= batch_size:
                flush()
                if state["count"] % log_every < batch_size:
                    rate = state["count"] / max(time.time() - t_start, 1e-9)
                    print(f"  ingested {state['count']} passages ({rate:.0f}/s)", flush=True)
        if state["count"] >= n:
            break

    flush()
    state["wall_seconds"] = round(time.time() - t_start, 1)
    state["finished_at"] = time.time()
    _save_state(ckpt, state)

    _RESULTS.mkdir(parents=True, exist_ok=True)
    summary = {
        "count": state["count"],
        "source": source,
        "wall_seconds": state["wall_seconds"],
        "throughput_per_s": round(state["count"] / state["wall_seconds"], 2) if state["wall_seconds"] else 0.0,
    }
    (_RESULTS / f"ingest_{n}.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
