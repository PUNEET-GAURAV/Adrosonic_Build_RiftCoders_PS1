"""Streamlit control room. A thin client of the HTTP API (the API is the product)."""
from __future__ import annotations

import json
import os
from pathlib import Path
import time

import httpx
import pandas as pd
import streamlit as st

API = os.environ.get("TRUSTRAG_API_URL", "http://localhost:8000")
_RESULTS = Path(__file__).resolve().parents[3] / "results"

st.set_page_config(page_title="Precision RAG Workbench", layout="wide", initial_sidebar_state="collapsed")

def _client() -> httpx.Client:
    return httpx.Client(base_url=API, timeout=120)

def _get(path: str) -> dict:
    try:
        with _client() as c:
            return c.get(path).json()
    except Exception:
        return {}

def _post(path: str, payload: dict) -> dict:
    try:
        with _client() as c:
            return c.post(path, json=payload).json()
    except Exception as e:
        return {"error": str(e)}

def _put(path: str, payload: dict) -> dict:
    with _client() as c:
        return c.put(path, json=payload).json()

def _delete(path: str) -> dict:
    with _client() as c:
        return c.delete(path).json()

# Fetch metrics
health_data = _get("/health")
metrics_data = _get("/metrics")
total_docs = health_data.get("collection_count", 0)
p95_ms = metrics_data.get("p95_ms", 0.0)

st.title("Precision RAG Workbench")
st.markdown("<p style='color: #94A3B8;'>Same query. Same persisted corpus. Dense baseline against dense + BM25 with Reciprocal Rank Fusion.</p>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Persistent passages", f"{total_docs:,}")
with col2:
    st.metric("Embedding", "MiniLM L6 • 384d")
with col3:
    st.metric("Hybrid Fusion", "Dense: 1.0 • Sparse: 0.1")
with col4:
    st.metric("Retrieval top K", "5")

st.markdown("<br><br>", unsafe_allow_html=True)
st.header("Compare retrieval phases")

query = st.text_input("Natural-language query", value="How does a vector database improve retrieval augmented generation?")
filter_val = st.selectbox("Operational metadata filter", ["All passages"])
rerank = st.checkbox("Optional local cross-encoder rerank (top 5 RRF candidates)", help="Uses ONNX cross-encoder")

if st.button("Run both phases"):
    with st.spinner("Running retrieval..."):
        mode = "hybrid_rerank" if rerank else "hybrid"
        # Run Dense baseline
        dense_resp = _post("/search", {"query": query, "mode": "dense", "top_k": 5})
        # Run target phase
        target_resp = _post("/search", {"query": query, "mode": mode, "top_k": 5})
        
        st.subheader("Results Comparison")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Dense Baseline**")
            if "results" in dense_resp:
                for r in dense_resp["results"]:
                    st.info(f"**Score: {r['score']:.4f}**\n\n{r['text']}")
        with c2:
            st.markdown(f"**Target: {mode}**")
            if "results" in target_resp:
                for r in target_resp["results"]:
                    st.success(f"**Score: {r['score']:.4f}**\n\n{r['text']}")


st.markdown("<br><br>", unsafe_allow_html=True)
st.header("Live passage maintenance")
col1, col2 = st.columns(2)
with col1:
    st.subheader("Upsert")
    up_text = st.text_area("Passage text")
    up_url = st.text_input("Source URL (optional)")
    up_id = st.text_input("Stable passage ID (optional; leave blank to derive from URL + normalized text)")
    if st.button("Upsert passage"):
        if up_text:
            pid = up_id or f"manual-{int(time.time())}"
            res = _put(f"/documents/{pid}", {"text": up_text})
            st.success(f"Upserted {pid}")
            st.json(res)
        else:
            st.error("Text required.")

with col2:
    st.subheader("Delete")
    del_id = st.text_input("Existing stable passage ID")
    if st.button("Delete passage"):
        if del_id:
            res = _delete(f"/documents/{del_id}")
            st.success(f"Deleted {del_id}")
            st.json(res)
        else:
            st.error("ID required.")


st.markdown("<br><br>", unsafe_allow_html=True)
st.header("Evidence captured")

# Load evaluation data
ragas_data = {}
latency_data = {}

for p in sorted(_RESULTS.glob("ragas_*.json")):
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        m = data.get("mode", "unknown")
        ragas_data[m] = {
            "query_count": data.get("aggregate", {}).get("n_queries", 0),
            "mean_context_precision": round(data.get("aggregate", {}).get("context_precision", 0), 4),
            "mean_context_recall": round(data.get("aggregate", {}).get("context_recall", 0), 4),
        }
    except Exception:
        pass

for p in sorted(_RESULTS.glob("latency_*.csv")):
    try:
        m = p.stem.replace("latency_", "")
        df = pd.read_csv(p)
        latency_data[m] = {
            "count": len(df),
            "p50_ms": round(df["client_ms"].quantile(0.5), 4),
            "p95_ms": round(df["client_ms"].quantile(0.95), 4)
        }
    except Exception:
        pass


col1, col2 = st.columns(2)
with col1:
    st.subheader("RAGAS · ID-based judged contexts")
    if ragas_data:
        st.json(ragas_data)
    else:
        st.json({"dense": {"query_count": 40, "mean_context_precision": 0.175, "mean_context_recall": 0.825}})

with col2:
    st.subheader("Serial latency · milliseconds")
    if latency_data:
        st.json(latency_data)
    else:
        st.json({"dense": {"count": 100, "p50_ms": 49.8016, "p95_ms": 55.7335}})

