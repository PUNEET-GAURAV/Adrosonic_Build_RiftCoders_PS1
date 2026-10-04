"""Config loading + a stable config hash recorded into every result."""
from __future__ import annotations

import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]


def config_dir() -> Path:
    override = os.environ.get("TRUSTRAG_CONFIG_DIR")
    if override:
        return Path(override)
    return _REPO_ROOT / "configs"


@lru_cache(maxsize=None)
def load_config(name: str) -> dict[str, Any]:
    """Load ``configs/<name>.yaml`` as a dict (cached)."""
    path = config_dir() / f"{name}.yaml"
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"config {name!r} must be a mapping, got {type(data).__name__}")
    return data


def merged_config(*names: str) -> dict[str, Any]:
    """Merge several config files (later names override earlier keys, shallow)."""
    out: dict[str, Any] = {}
    for name in names:
        out.update(load_config(name))
    return out


def config_hash(*objs: Any) -> str:
    """Stable 12-hex-char hash of the given objects (dicts, models, strings)."""
    payload = json.dumps(objs, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
