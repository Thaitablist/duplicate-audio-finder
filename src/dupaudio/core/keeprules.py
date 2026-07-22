"""Decide which file in each duplicate group to keep."""

from __future__ import annotations

import re
from collections.abc import Iterable

from ..models import AudioFile, DuplicateGroup

# Path fragments that suggest a file is a copy / not the canonical original.
_COPY_HINTS = re.compile(r"(?:\bcopy\b|\(\d+\)|/downloads?/|/temp/|~$)", re.IGNORECASE)


def _copy_penalty(af: AudioFile) -> int:
    return 1 if _COPY_HINTS.search(str(af.path).replace("\\", "/")) else 0


def _rank_key(af: AudioFile) -> tuple:
    """Sort key: the file that sorts FIRST is the one we keep.

    Priority (best first):
      1. highest bitrate
      2. more complete tags
      3. not a "copy"-looking path
      4. shorter path
      5. older mtime (treated as the original)
    """
    return (
        -(af.bitrate or 0),
        -af.tag_completeness,
        _copy_penalty(af),
        len(str(af.path)),
        af.mtime,
    )


def choose_keeper(files: Iterable[AudioFile]) -> AudioFile | None:
    """Return the file that should be kept from a group, or None if empty."""
    files = list(files)
    if not files:
        return None
    return min(files, key=_rank_key)


def apply_keep_rules(groups: Iterable[DuplicateGroup]) -> None:
    """Set ``keep_path`` on each group in place using the ranking rules."""
    for group in groups:
        keeper = choose_keeper(group.files)
        group.keep_path = keeper.path if keeper else None
