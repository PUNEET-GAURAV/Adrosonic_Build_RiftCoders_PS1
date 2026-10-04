"""Direct MS MARCO ingestion — bypasses the broken HuggingFace `datasets` library entirely.

Downloads raw parquet files from HuggingFace Hub via HTTPS, reads them with pandas/pyarrow,
and streams passages directly into Qdrant. Works on Python 3.14 where `dill` is broken.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

import httpx
import pandas as pd

# ── Add src to path ──────────────────────────────────────────────────────────
SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from trustrag.adapters.bm25_sparse import BM25SparseEncoder
from trustrag.adapters.qdrant_store import QdrantStore
from trustrag.adapters.st_embedder import SentenceTransformerEmbedder
from trustrag.core.models import Passage

# ── Config ───────────────────────────────────────────────────────────────────
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6333")
COLLECTION = "passages"
TARGET_N = int(os.environ.get("MSMARCO_N", "100000"))
BATCH_SIZE = 128
LOG_EVERY = 2000
RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
CHECKPOINT = RESULTS_DIR / "ingest_direct_checkpoint.json"

# HuggingFace parquet API URLs for MS MARCO v2.1 train split
PARQUET_URLS = [
    "https://huggingface.co/api/datasets/microsoft/ms_marco/parquet/v2.1/train/0.parquet",
    "https://huggingface.co/api/datasets/microsoft/ms_marco/parquet/v2.1/train/1.parquet",
    "https://huggingface.co/api/datasets/microsoft/ms_marco/parquet/v2.1/train/2.parquet",
]


def _text_hash(text: str) -> str:
    return hashlib.sha1(text.strip().lower().encode("utf-8")).hexdigest()


def _load_checkpoint() -> dict:
    if CHECKPOINT.exists():
        return json.loads(CHECKPOINT.read_text("utf-8"))
    return {"count": 0, "file_idx": 0, "row_idx": 0}


def _save_checkpoint(state: dict) -> None:
    CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
    CHECKPOINT.write_text(json.dumps(state), "utf-8")


def download_parquet(url: str, dest: Path) -> Path:
    """Download a parquet file with progress."""
    if dest.exists() and dest.stat().st_size > 1_000_000:
        print(f"  [cached] {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  Downloading {dest.name} ...")

    with httpx.stream("GET", url, follow_redirects=True, timeout=300) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_bytes(chunk_size=1_048_576):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = downloaded / total * 100
                    print(f"\r    {downloaded / 1e6:.1f} / {total / 1e6:.1f} MB ({pct:.0f}%)", end="", flush=True)
        print()  # newline after progress

    print(f"  [OK] Downloaded {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")
    return dest


def extract_passages_from_df(df: pd.DataFrame, file_idx: int, start_row: int = 0):
    """Yield (passage_id, text, query_type) from a MS MARCO parquet DataFrame.
    
    The parquet schema has passages as a dict with numpy arrays:
      {'is_selected': array([...]), 'passage_text': array([...]), 'url': array([...])}
    """
    for row_idx in range(start_row, len(df)):
        row = df.iloc[row_idx]
        query_type = row.get("query_type", "UNKNOWN") or "UNKNOWN"
        query_id = row.get("query_id", row_idx)

        passages_data = row.get("passages")
        if passages_data is None:
            continue

        # Extract passage_text array from the dict structure
        if isinstance(passages_data, dict):
            texts = passages_data.get("passage_text", [])
        else:
            continue

        # Iterate over the numpy array or list
        for p_idx, text in enumerate(texts):
            text = str(text).strip() if text is not None else ""
            if len(text) > 20:
                pid = f"msmarco-{file_idx}-{query_id}-{p_idx}"
                yield pid, text, query_type, row_idx


def main():
    print("=" * 60)
    print(f"MS MARCO Direct Ingestion — Target: {TARGET_N:,} passages")
    print("=" * 60)

    # Initialize components
    print("\n[1/3] Initializing embedding model + Qdrant store...")
    embedder = SentenceTransformerEmbedder("BAAI/bge-small-en-v1.5")
    sparse = BM25SparseEncoder()
    store = QdrantStore(QDRANT_URL, COLLECTION)
    print(f"  Qdrant collection '{COLLECTION}' has {store.count()} points currently.")

    # Load checkpoint
    state = _load_checkpoint()
    count = state["count"]
    start_file = state["file_idx"]
    start_row = state["row_idx"]
    seen: set[str] = set()

    if count > 0:
        print(f"  Resuming from checkpoint: {count:,} passages already ingested.")

    print(f"\n[2/3] Downloading & processing parquet files...")
    t_start = time.time()

    cache_dir = RESULTS_DIR / "parquet_cache"

    for file_idx, url in enumerate(PARQUET_URLS):
        if file_idx < start_file:
            continue
        if count >= TARGET_N:
            break

        fname = f"msmarco_train_{file_idx:04d}.parquet"
        local_path = download_parquet(url, cache_dir / fname)

        print(f"\n  Reading {fname} into memory...")
        df = pd.read_parquet(local_path)
        print(f"  Loaded {len(df):,} rows from {fname}")

        row_start = start_row if file_idx == start_file else 0
        buf_p: list[Passage] = []

        for pid, text, qtype, row_idx in extract_passages_from_df(df, file_idx, row_start):
            if count >= TARGET_N:
                break

            h = _text_hash(text)
            if h in seen:
                continue
            seen.add(h)

            p = Passage(
                passage_id=pid,
                text=text,
                source="msmarco",
                category=qtype,
                label_origin="native",
            )
            buf_p.append(p)

            if len(buf_p) >= BATCH_SIZE:
                dense = embedder.embed_documents([p.text for p in buf_p])
                sp = sparse.encode_documents([p.text for p in buf_p])
                store.upsert(buf_p, dense, sp)
                count += len(buf_p)
                buf_p = []

                # Save checkpoint
                state = {"count": count, "file_idx": file_idx, "row_idx": row_idx}
                _save_checkpoint(state)

                if count % LOG_EVERY < BATCH_SIZE:
                    elapsed = time.time() - t_start
                    rate = count / max(elapsed, 0.1)
                    eta = (TARGET_N - count) / max(rate, 0.1)
                    print(f"  [OK] {count:>7,} / {TARGET_N:,} passages | {rate:.0f}/s | ETA {eta/60:.1f} min")

        # Flush remaining
        if buf_p and count < TARGET_N:
            dense = embedder.embed_documents([p.text for p in buf_p])
            sp = sparse.encode_documents([p.text for p in buf_p])
            store.upsert(buf_p, dense, sp)
            count += len(buf_p)
            state = {"count": count, "file_idx": file_idx, "row_idx": row_idx}
            _save_checkpoint(state)

        # Free memory
        del df

    wall = time.time() - t_start
    print(f"\n[3/3] DONE! Ingested {count:,} passages in {wall:.0f}s ({count/max(wall,1):.0f}/s)")
    print(f"  Qdrant now has {store.count():,} points total.")

    # Save summary
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    summary = {
        "count": count,
        "source": "msmarco-direct-parquet",
        "wall_seconds": round(wall, 1),
        "throughput_per_s": round(count / max(wall, 1), 2),
    }
    (RESULTS_DIR / f"ingest_{TARGET_N}.json").write_text(json.dumps(summary, indent=2), "utf-8")
    print(f"  Summary saved to {RESULTS_DIR / f'ingest_{TARGET_N}.json'}")


if __name__ == "__main__":
    main()
