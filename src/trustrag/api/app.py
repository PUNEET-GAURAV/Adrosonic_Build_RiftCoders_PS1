"""FastAPI app. The API is the product: the UI, benchmark runner and eval harness are all
clients of this same service.
"""
from __future__ import annotations

import time
from collections import deque
from typing import Any

from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import JSONResponse, HTMLResponse

from ..answering.answerer import Answerer
from ..assembly import Stack, build_stack
from ..core.models import Answer, Filters, Passage, SearchRequest, SearchResult
from ..ingestion.upload import upload_document
from .schemas import AnswerRequest, DocumentIn, HealthOut, MetricsOut


def create_app(stack: Stack | None = None) -> FastAPI:
    app = FastAPI(title="TrustRAG", version="0.1.0")
    stack = stack or build_stack(use_qdrant=True)
    app.state.stack = stack
    app.state.answerer = Answerer(stack.orchestrator, generator=stack.generator, config=stack.config)
    app.state.latency_window: deque[float] = deque(maxlen=1000)
    app.state.requests = 0
    app.state.cache_hits = 0
    app.state.degraded = 0
    app.state.feedback_store = []

    def _pct(p: float) -> float | None:
        if not app.state.latency_window:
            return None
        s = sorted(app.state.latency_window)
        k = (len(s) - 1) * (p / 100.0)
        lo = int(k)
        hi = min(lo + 1, len(s) - 1)
        return round(s[lo] * (1 - (k - lo)) + s[hi] * (k - lo), 2)

    @app.get("/health", response_model=HealthOut)
    def health() -> HealthOut:
        return HealthOut(
            status="ok",
            collection_count=stack.store.count(),
            index_version=stack.store.index_version(),
            config_hash=stack.config_hash,
        )

    @app.get("/", response_class=HTMLResponse)
    def index():
        from pathlib import Path
        html_path = Path(__file__).parent.parent / "ui" / "index.html"
        return html_path.read_text(encoding="utf-8")

    @app.get("/config")
    def get_config() -> dict[str, Any]:
        return {"config": stack.config, "config_hash": stack.config_hash}
        
    @app.get("/taxonomy")
    def get_taxonomy() -> dict[str, Any]:
        return stack.orchestrator.router.taxonomy if stack.orchestrator.router else {}
        
    @app.post("/route/explain")
    def route_explain(req: SearchRequest) -> dict[str, Any]:
        if not stack.orchestrator.router:
            return {"strategy": "off"}
        return stack.orchestrator.router.route(req.query).model_dump()

    def _mask_pii(text: str) -> str:
        import re
        # Basic patterns for hacking PII out of logs
        text = re.sub(r'\b\d{4}[ -]?\d{4}[ -]?\d{4}[ -]?\d{4}\b', 'CARD_MASKED', text) # Card numbers
        text = re.sub(r'\b\d{9,18}\b', 'ACCT_MASKED', text) # Account numbers
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'EMAIL_MASKED', text)
        return text

    

    class FeedbackRequest(BaseModel):
        request_id: str
        passage_id: str
        score: int

    @app.post("/feedback")
    def submit_feedback(req: FeedbackRequest):
        app.state.feedback_store.append(req.model_dump())
        return {"status": "ok", "total": len(app.state.feedback_store)}

    @app.get("/feedback-stats")
    def get_feedback_stats():
        store = app.state.feedback_store
        if not store:
            return {"upvotes": 0, "downvotes": 0, "ctr": 0.0}
        up = sum(1 for f in store if f['score'] == 1)
        down = sum(1 for f in store if f['score'] == -1)
        return {"upvotes": up, "downvotes": down, "ctr": round(up / len(store), 2)}

    @app.post("/search", response_model=SearchResult)
    def search(req: SearchRequest) -> SearchResult:
        app.state.requests += 1
        t0 = time.perf_counter()
        result = stack.orchestrator.search(req)
        ms = (time.perf_counter() - t0) * 1000
        app.state.latency_window.append(ms)
        if result.cache_hit:
            app.state.cache_hits += 1
        if result.degraded:
            app.state.degraded += 1
            
        # Audit Log
        masked_query = _mask_pii(req.query)
        route_info = result.route_result.get("strategy") if result.route_result else "off"
        ret_ids = [r.passage_id for r in result.results]
        print(f"[AUDIT] id={result.request_id} tenant={req.session.get('tenant', 'none')} "
              f"query='{masked_query}' route={route_info} time={ms:.2f}ms hits={len(ret_ids)}")
              
        return result

    @app.post("/answer", response_model=Answer)
    def answer(req: AnswerRequest) -> Answer:
        return app.state.answerer.answer(req.query, mode=req.mode, top_k=req.top_k, filters=req.filters)

    @app.put("/documents/{passage_id}")
    def upsert(passage_id: str, doc: DocumentIn) -> dict[str, Any]:
        p = Passage(
            passage_id=passage_id, text=doc.text, category=doc.category,
            source=doc.source, label_origin="native",
        )
        dense = stack.embedder.embed_documents([doc.text])
        sparse = stack.sparse.encode_documents([doc.text])
        stack.store.upsert([p], dense, sparse)
        return {"passage_id": passage_id, "index_version": stack.store.index_version()}

    @app.delete("/documents/{passage_id}")
    def delete(passage_id: str) -> dict[str, Any]:
        stack.store.delete([passage_id])
        return {"passage_id": passage_id, "index_version": stack.store.index_version()}

    @app.post("/documents/upload")
    async def upload(file: UploadFile) -> dict[str, Any]:
        import tempfile
        import os

        suffix = os.path.splitext(file.filename or "upload.txt")[1] or ".txt"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        try:
            n = upload_document(tmp_path, stack.store, stack.embedder, stack.sparse)
        finally:
            os.unlink(tmp_path)
        return {"source": file.filename, "chunks": n, "index_version": stack.store.index_version()}

    @app.get("/metrics", response_model=MetricsOut)
    def metrics() -> MetricsOut:
        return MetricsOut(
            index_version=stack.store.index_version(),
            collection_count=stack.store.count(),
            p50_ms=_pct(50),
            p95_ms=_pct(95),
            requests=app.state.requests,
            cache_hits=app.state.cache_hits,
            degraded=app.state.degraded,
        )


    @app.get("/eval-results")
    def eval_results() -> dict[str, Any]:
        import json
        from pathlib import Path
        results_dir = Path(__file__).resolve().parents[3] / "results"
        data = {}
        for mode in ["dense", "hybrid", "hybrid_rerank"]:
            try:
                p = results_dir / f"ragas_{mode}_test.json"
                if p.exists():
                    d = json.loads(p.read_text(encoding="utf-8"))
                    data[mode] = d.get("aggregate", {})
            except Exception:
                pass
        return data

    @app.exception_handler(Exception)

    async def unhandled(exc: Exception):  # noqa: ANN001
        return JSONResponse(status_code=500, content={"error": type(exc).__name__, "detail": str(exc)})

    return app


app = create_app()
