"""Walk directories and collect audio files."""

from __future__ import annotations

import os
import stat as stat_mod
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path

from ..models import AudioFile

# Extensions we treat as audio. Lowercase, with leading dot.
DEFAULT_AUDIO_EXTS: frozenset[str] = frozenset(
    {".mp3", ".flac", ".m4a", ".aac", ".ogg", ".oga", ".opus", ".wav", ".wma", ".aiff", ".aif"}
)

# Windows file attributes marking a file that is NOT fully on local disk
# (e.g. OneDrive / cloud "online-only" placeholders). Reading such a file
# yields a stub, so every placeholder hashes identically — a false duplicate.
_CLOUD_PLACEHOLDER_ATTRS = (
    getattr(stat_mod, "FILE_ATTRIBUTE_OFFLINE", 0)
    | getattr(stat_mod, "FILE_ATTRIBUTE_RECALL_ON_OPEN", 0)
    | getattr(stat_mod, "FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS", 0)
)


def is_cloud_placeholder(st: os.stat_result) -> bool:
    """True if ``st`` describes a not-yet-materialized cloud placeholder file."""
    attrs = getattr(st, "st_file_attributes", 0)
    return bool(attrs & _CLOUD_PLACEHOLDER_ATTRS)


def iter_audio_files(
    roots: Iterable[Path],
    exts: frozenset[str] = DEFAULT_AUDIO_EXTS,
    should_cancel: Callable[[], bool] | None = None,
) -> Iterator[AudioFile]:
    """Yield an AudioFile for every audio file found under ``roots``.

    Follows no symlinks (to avoid cycles) and silently skips unreadable
    entries. ``should_cancel`` is polled periodically; if it returns True the
    walk stops early.
    """
    seen: set[str] = set()  # real paths, to dedupe overlapping roots
    for root in roots:
        root = Path(root)
        if should_cancel and should_cancel():
            return
        if root.is_file():
            af = _make_audio_file(root, exts, seen)
            if af is not None:
                yield af
            continue
        for dirpath, _dirnames, filenames in os.walk(root, followlinks=False):
            if should_cancel and should_cancel():
                return
            for fn in filenames:
                p = Path(dirpath) / fn
                af = _make_audio_file(p, exts, seen)
                if af is not None:
                    yield af


def _make_audio_file(
    path: Path, exts: frozenset[str], seen: set[str]
) -> AudioFile | None:
    if path.suffix.lower() not in exts:
        return None
    try:
        real = os.path.realpath(path)
        if real in seen:
            return None
        st = path.stat()
    except OSError:
        return None
    if not os.path.isfile(real):
        return None
    # Skip cloud "online-only" placeholders — they are not real local audio
    # and would otherwise all hash to the same stub -> bogus exact duplicates.
    if is_cloud_placeholder(st):
        return None
    seen.add(real)
    return AudioFile(path=path, size=st.st_size, mtime=st.st_mtime)
