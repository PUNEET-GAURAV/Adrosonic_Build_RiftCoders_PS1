"""Command-line interface (typer). `python -m trustrag.cli <command>`.

Commands: up, build-evalset, ingest, eval, bench, report, serve-api, serve-ui, snapshot.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(help="TrustRAG — precision-first retrieval for enterprise RAG.")


def _stack(use_qdrant: bool = True, enable_reranker: bool | None = None):
    from .assembly import build_stack

    return build_stack(use_qdrant=use_qdrant, enable_reranker=enable_reranker)


@app.command()
def up() -> None:
    """Start Qdrant via docker compose."""
    subprocess.run(["docker", "compose", "up", "-d"], check=True)


@app.command("build-evalset")
def build_evalset(
    dev_size: int = 200,
    test_size: int = 400,
    seed: int = 42,
) -> None:
    """Build and commit data/eval/eval_queries.jsonl from MS MARCO validation."""
    from .ingestion.eval_set import build_eval_set
    from .ingestion.msmarco_loader import iter_msmarco

    rows = build_eval_set(iter_msmarco("validation"), seed=seed, dev_size=dev_size, test_size=test_size)
    print(f"wrote {len(rows)} eval queries (dev={dev_size}, test={test_size})")


@app.command()
def ingest(
    n: int = typer.Option(100000, help="target number of unique passages"),
    split: str = "train",
    checkpoint: str = "results/ingest_checkpoint.json",
    use_qdrant: bool = True,
) -> None:
    """Stream, dedupe, embed and index MS MARCO passages."""
    from .ingestion.msmarco_loader import iter_msmarco
    from .ingestion.pipeline import ingest_corpus

    stack = _stack(use_qdrant=use_qdrant)
    summary = ingest_corpus(
        stack.store,
        stack.embedder,
        stack.sparse,
        iter_msmarco(split),
        n=n,
        checkpoint_path=checkpoint,
    )
    print(json.dumps(summary, indent=2))


@app.command()
def eval(
    mode: str = typer.Option("hybrid"),
    split: str = typer.Option("test"),
    judge: str = typer.Option("non-llm"),
    top_k: int = 5,
    use_qdrant: bool = True,
) -> None:
    """Run IR + RAGAS evaluation on the eval set and write results/."""
    from .config import load_config
    from .evaluation.evaluator import run_eval
    from .ingestion.eval_set import load_eval_set

    stack = _stack(use_qdrant=use_qdrant)
    rows = load_eval_set()

    judge_fn = None
    if judge == "llm":
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            typer.echo("GROQ_API_KEY not set; falling back to non-llm judge.", err=True)
        else:
            from groq import Groq

            from .evaluation.ragas_runner import make_groq_judge, judge_relevance_llm

            client = Groq(api_key=api_key)
            raw_judge = make_groq_judge(client, load_config("models")["judge_model"])
            judge_fn = lambda q, ref, pas: judge_relevance_llm(raw_judge, q, ref, pas)  # noqa: E731

    ragas_payload, ir_payload = run_eval(
        stack.orchestrator,
        rows,
        mode=mode,
        split=split,
        judge=judge_fn,
        top_k=top_k,
        config_hash=stack.config_hash,
        models=load_config("models"),
    )
    print("RAGAS:", json.dumps(ragas_payload.get("aggregate", {}), indent=2))
    print("IR:", json.dumps(ir_payload.get("aggregate", {}), indent=2))


@app.command()
def bench(
    mode: str = typer.Option("hybrid"),
    n: int = 100,
    no_cache: bool = True,
    base_url: str = "http://localhost:8000",
) -> None:
    """Run the 100-query latency benchmark against the running HTTP API."""
    from .evaluation.benchmark import run_benchmark, write_csv, write_summary
    from .ingestion.eval_set import load_eval_set

    rows = load_eval_set()
    test_queries = [r["query"] for r in rows if r.get("split") == "test"][:n]
    result = run_benchmark(base_url, test_queries, mode=mode, n=n, use_cache=not no_cache)
    base = f"results/latency_{mode}"
    write_csv(f"{base}.csv", result)
    write_summary(f"{base}.json", result)
    print(json.dumps(result["summary"], indent=2))


@app.command()
def report() -> None:
    """Generate docs/BENCHMARK_REPORT.md from results/."""
    from .evaluation.report import write_report

    text = write_report()
    print(text)


@app.command("serve-api")
def serve_api(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run the FastAPI service."""
    import uvicorn

    uvicorn.run("trustrag.api.app:app", host=host, port=port, reload=False)


@app.command("serve-ui")
def serve_ui() -> None:
    """Run the Streamlit control room."""
    subprocess.run(["streamlit", "run", "src/trustrag/ui/app.py"], check=True)


@app.command()
def snapshot(action: str = typer.Argument(..., help="create | restore")) -> None:
    """Create or restore a Qdrant snapshot (evaluators can restore in minutes)."""
    stack = _stack(use_qdrant=True)
    if action == "create":
        snap = stack.store.client.create_snapshot(stack.store.collection)
        print("snapshot:", snap)
    elif action == "restore":
        typer.echo("Restore: pass a snapshot URL to `trustrag snapshot restore <url>`.", err=True)
    else:
        typer.echo(f"unknown action {action!r}", err=True)


if __name__ == "__main__":
    app()
