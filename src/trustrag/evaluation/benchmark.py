"""Latency benchmark: 100 consecutive queries through the real HTTP API."""
from __future__ import annotations

import csv
import json
import statistics
import time
from pathlib import Path
from typing import Any

import httpx


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * (p / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    frac = k - lo
    return s[lo] * (1 - frac) + s[hi] * frac


def run_benchmark(
    base_url: str,
    queries: list[str],
    mode: str,
    n: int = 100,
    warmup: int = 5,
    use_cache: bool = False,
    timeout: float = 30.0,
) -> dict[str, Any]:
    payloads = [{"query": q, "mode": mode, "use_cache": use_cache} for q in queries]
    rows: list[dict] = []
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        for p in payloads[:warmup]:
            client.post("/search", json=p)
        for q, p in zip(queries[:n], payloads[:n]):
            t0 = time.perf_counter()
            resp = client.post("/search", json=p)
            dt = (time.perf_counter() - t0) * 1000.0
            timings = {}
            if resp.status_code == 200:
                timings = resp.json().get("timings_ms", {})
            rows.append({"query": q, "client_ms": round(dt, 2), "timings_ms": timings})

    client_ms = [r["client_ms"] for r in rows]
    summary = {
        "mode": mode,
        "n": len(rows),
        "warmup": warmup,
        "p50": round(percentile(client_ms, 50), 2),
        "p90": round(percentile(client_ms, 90), 2),
        "p95": round(percentile(client_ms, 95), 2),
        "p99": round(percentile(client_ms, 99), 2),
        "max": round(max(client_ms), 2) if client_ms else 0.0,
        "mean": round(statistics.fmean(client_ms), 2) if client_ms else 0.0,
    }
    return {"summary": summary, "rows": rows}


def write_csv(path: str, result: dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["query", "client_ms", "timings_ms"])
        writer.writeheader()
        for r in result["rows"]:
            writer.writerow(
                {"query": r["query"], "client_ms": r["client_ms"], "timings_ms": json.dumps(r["timings_ms"])}
            )


def write_summary(path: str, result: dict) -> None:
    """Write the summary (p50/p90/p95/p99/max) as JSON, consumed by `trustrag report`."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
