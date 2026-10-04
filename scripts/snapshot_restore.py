"""Create or restore a Qdrant snapshot for fast reproducibility.

Usage:
    python scripts/snapshot_restore.py create
    python scripts/snapshot_restore.py restore <snapshot_url>
"""
from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from trustrag.assembly import build_stack  # noqa: E402


def main() -> None:
    stack = build_stack(use_qdrant=True)
    client = stack.store.client
    collection = stack.store.collection
    action = sys.argv[1] if len(sys.argv) > 1 else "create"

    if action == "create":
        snap = client.create_snapshot(collection_name=collection)
        print(f"snapshot created: {snap.name}")
        print("download it (GET /collections/{collection}/snapshots/{name}) and publish it.")
    elif action == "restore":
        url = sys.argv[2]
        client.recover_snapshot(collection_name=collection, location=url)
        print(f"restored snapshot from {url} into {collection}")
    else:
        print(f"unknown action {action!r}")


if __name__ == "__main__":
    main()
