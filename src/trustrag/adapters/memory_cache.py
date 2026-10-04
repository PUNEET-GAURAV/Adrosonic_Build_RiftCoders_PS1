"""In-memory cache: exact-match LRU plus an optional semantic (cosine) lookup.

Implements the Cache port. Key building lives in core/cache_key.py (includes
query/mode/filters/groups/index_version) so a live update invalidates affected entries.
"""
from __future__ import annotations

from collections import OrderedDict

from ..core.text import cosine_sim


class MemoryCache:
    def __init__(self, maxsize: int = 4096, semantic_threshold: float = 0.95) -> None:
        self.maxsize = maxsize
        self.threshold = semantic_threshold
        self._data: OrderedDict[str, object] = OrderedDict()
        self._semantic: list[tuple[list[float], str]] = []

    def get(self, key: str) -> object | None:
        if key in self._data:
            self._data.move_to_end(key)
            return self._data[key]
        return None

    def put(self, key: str, value: object) -> None:
        self._data[key] = value
        self._data.move_to_end(key)
        if len(self._data) > self.maxsize:
            self._data.popitem(last=False)

    def put_semantic(self, vector: list[float], key: str) -> None:
        self._semantic.append((vector, key))

    def get_semantic(self, vector: list[float]) -> object | None:
        best_key: str | None = None
        best_sim = -1.0
        for stored_vec, key in self._semantic:
            sim = cosine_sim(vector, stored_vec)
            if sim > best_sim:
                best_sim = sim
                best_key = key
        if best_key is not None and best_sim >= self.threshold:
            return self.get(best_key)
        return None
