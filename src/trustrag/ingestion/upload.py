"""Bring-your-own-documents: PDF/TXT/MD -> sentence-aware chunking -> upsert."""
from __future__ import annotations

import re
from pathlib import Path

from ..core.models import Passage

_SENT_RE = re.compile(r"(?<=[.!?])\s+")


def extract_text(path: str | Path) -> str:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        from pypdf import PdfReader  # local import

        reader = PdfReader(str(p))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return p.read_text(encoding="utf-8", errors="replace")


def chunk_sentences(text: str, max_chars: int = 500, overlap: int = 1) -> list[str]:
    sentences = [s.strip() for s in _SENT_RE.split(text.replace("\n", " ")) if s.strip()]
    chunks: list[str] = []
    buf: list[str] = []
    size = 0
    for s in sentences:
        buf.append(s)
        size += len(s)
        if size >= max_chars:
            chunks.append(" ".join(buf))
            buf = buf[-overlap:] if overlap else []
            size = sum(len(x) for x in buf)
    if buf:
        chunks.append(" ".join(buf))
    return chunks


def build_passages(text: str, source: str, max_chars: int = 500) -> list[Passage]:
    chunks = chunk_sentences(text, max_chars=max_chars)
    out = []
    for i, c in enumerate(chunks):
        out.append(
            Passage(
                passage_id=f"{source}-{i}",
                text=c,
                source=source,
                category="user_upload",
                label_origin="native",
            )
        )
    return out


def upload_document(path: str | Path, store, embedder, sparse_encoder) -> int:
    p = Path(path)
    text = extract_text(p)
    passages = build_passages(text, source=p.name)
    if not passages:
        return 0
    dense = embedder.embed_documents([pp.text for pp in passages])
    sparse = sparse_encoder.encode_documents([pp.text for pp in passages])
    store.upsert(passages, dense, sparse)
    return len(passages)
