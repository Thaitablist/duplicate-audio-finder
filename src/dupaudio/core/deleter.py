"""Safely delete files by moving them to the OS trash, with an undo log."""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from send2trash import send2trash  # type: ignore[import-untyped]

# Injectable so tests can substitute a fake trash function.
TrashFn = Callable[[str], None]


@dataclass
class DeleteResult:
    trashed: list[Path]
    failed: list[tuple[Path, str]]  # (path, error message)


class AllFilesInGroupError(ValueError):
    """Raised when a delete request would remove every file in a group."""


def undo_log_path() -> Path:
    """Location of the JSON undo log in the user's app-data directory."""
    from ..paths import app_data_dir

    return app_data_dir() / "delete_history.jsonl"


def validate_no_full_group_wipe(
    groups_files: Sequence[Sequence[Path]], to_delete: set[Path]
) -> None:
    """Ensure no group has ALL of its files marked for deletion."""
    for files in groups_files:
        files = list(files)
        if files and all(p in to_delete for p in files):
            raise AllFilesInGroupError(
                f"Refusing to delete every file in a duplicate group: "
                f"{[str(p) for p in files]}"
            )


def delete_files(
    paths: Sequence[Path],
    *,
    trash: TrashFn = send2trash,
    write_log: bool = True,
) -> DeleteResult:
    """Move each path to the OS trash. Returns which succeeded/failed.

    Records an entry in the undo log for every successfully trashed file so
    the user can see what was removed and when.
    """
    trashed: list[Path] = []
    failed: list[tuple[Path, str]] = []

    for p in paths:
        try:
            trash(str(p))
            trashed.append(p)
        except Exception as exc:  # noqa: BLE001 — send2trash raises OSError subclasses
            failed.append((p, str(exc)))

    if write_log and trashed:
        _append_undo_log(trashed)

    return DeleteResult(trashed=trashed, failed=failed)


def _append_undo_log(paths: Sequence[Path]) -> None:
    log = undo_log_path()
    log.parent.mkdir(parents=True, exist_ok=True)
    ts = time.time()
    with open(log, "a", encoding="utf-8") as f:
        for p in paths:
            f.write(
                json.dumps({"path": str(p), "trashed_at": ts}, ensure_ascii=False)
                + "\n"
            )
