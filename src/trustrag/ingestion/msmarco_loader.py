"""MS MARCO loader.

Streams ``microsoft/ms_marco`` from HuggingFace and normalises each row into a flat shape
independent of the dataset's internal list-of-passages representation. The schema of this
dataset varies by config/version, so the loader inspects fields defensively at runtime.
"""
from __future__ import annotations

from collections.abc import Iterator
from typing import Any
import pandas as pd


def _passage_id(split: str, query_id: Any, idx: int) -> str:
    return f"msmarco-{split}-{query_id}-{idx}"


def iter_msmarco(split: str = "train", config_name: str | None = None) -> Iterator[dict]:
    """Yield one dict per query: {query_id, query, query_type, answer, passages:[...]}."""
    # Using pandas to load directly from the parquet URL to bypass dill/datasets bug in python 3.14 alpha
    url = "https://huggingface.co/datasets/microsoft/ms_marco/resolve/refs%2Fconvert%2Fparquet/v1.1/train/0000.parquet"
    print(f"Downloading/Reading MS MARCO from {url}...")
    df = pd.read_parquet(url)
    
    for _, row in df.iterrows():
        query = row.get("query", "")
        query_type = row.get("query_type") or "UNKNOWN"
        query_id = row.get("query_id")
        
        answers = row.get("answers")
        if answers is not None and len(answers) > 0:
            answer = answers[0]
        else:
            answer = ""
            
        passages_dict = row.get("passages", {})
        raw_texts = passages_dict.get("passage_text", [])
        raw_selected = passages_dict.get("is_selected", [])
        
        passages = []
        for i, text in enumerate(raw_texts):
            text = str(text)
            selected = int(raw_selected[i]) if i < len(raw_selected) else 0
            if text:
                passages.append(
                    {
                        "passage_id": _passage_id(split, query_id, i),
                        "text": text,
                        "is_selected": selected,
                    }
                )
        if query:
            yield {
                "query_id": str(query_id),
                "query": query,
                "query_type": query_type,
                "answer": answer,
                "passages": passages,
            }
