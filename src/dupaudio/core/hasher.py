"""Streaming SHA-256 hashing of files (constant memory)."""

from __future__ import annotations

import hashlib
from pathlib import Path

CHUNK_SIZE = 64 * 1024  # 64 KiB


def hash_file(path: Path, chunk_size: int = CHUNK_SIZE) -> str:
    """Return the hex SHA-256 of ``path``, reading it in fixed-size chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()
