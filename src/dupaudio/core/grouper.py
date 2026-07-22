"""Group audio files into duplicate sets (exact byte match + metadata match)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Sequence

from ..models import AudioFile, DuplicateGroup, MatchType
from .hasher import hash_file
from .metadata import read_metadata

# A progress callback: (done, total, message)
ProgressFn = Callable[[int, int, str], None]
CancelFn = Callable[[], bool]


def _noop_progress(done: int, total: int, message: str) -> None:  # pragma: no cover
    pass


def find_duplicates(
    files: Sequence[AudioFile],
    *,
    enable_metadata: bool = True,
    require_valid_audio: bool = False,
    progress: ProgressFn | None = None,
    should_cancel: CancelFn | None = None,
) -> list[DuplicateGroup]:
    """Return duplicate groups found among ``files``.

    Two-layer strategy:
      1. Bucket by file size; only same-size files can be byte-identical.
      2. SHA-256 each candidate; equal hashes -> EXACT group.
      3. (optional) Among files that were NOT exact duplicates, bucket by
         normalized (artist, title, album) tags -> METADATA group.

    When ``require_valid_audio`` is True, files that mutagen could not decode
    as real audio (no bitrate/duration — e.g. cloud placeholder stubs) are
    excluded up front. Metadata must already have been read for this to work.
    """
    progress = progress or _noop_progress
    groups: list[DuplicateGroup] = []

    if require_valid_audio:
        files = [af for af in files if af.is_valid_audio]

    # ---- Layer 1: size buckets -------------------------------------------
    by_size: dict[int, list[AudioFile]] = defaultdict(list)
    for af in files:
        by_size[af.size].append(af)

    # Only sizes with 2+ files are hashing candidates.
    hash_candidates = [af for grp in by_size.values() if len(grp) > 1 for af in grp]
    total = len(hash_candidates)

    # ---- Layer 2: hash candidates, bucket by hash ------------------------
    by_hash: dict[str, list[AudioFile]] = defaultdict(list)
    exact_paths: set = set()
    for i, af in enumerate(hash_candidates, start=1):
        if should_cancel and should_cancel():
            return groups
        progress(i, total, f"Hashing {af.name}")
        try:
            af.sha256 = hash_file(af.path)
        except OSError as exc:
            af.error = f"hash failed: {exc}"
            continue
        by_hash[af.sha256].append(af)

    for dupes in by_hash.values():
        if len(dupes) > 1:
            groups.append(DuplicateGroup(match_type=MatchType.EXACT, files=list(dupes)))
            exact_paths.update(f.path for f in dupes)

    # ---- Layer 3: metadata grouping (files not already exact-duplicated) --
    if enable_metadata:
        remaining = [af for af in files if af.path not in exact_paths]
        # Read metadata for these (may not have been read yet).
        for j, af in enumerate(remaining, start=1):
            if should_cancel and should_cancel():
                return groups
            progress(j, len(remaining), f"Reading tags {af.name}")
            if af.artist is None and af.title is None and af.error is None:
                read_metadata(af)

        by_meta: dict[tuple[str, str, str], list[AudioFile]] = defaultdict(list)
        for af in remaining:
            key = af.metadata_key()
            if key is not None:
                by_meta[key].append(af)

        for dupes in by_meta.values():
            if len(dupes) > 1:
                groups.append(
                    DuplicateGroup(match_type=MatchType.METADATA, files=list(dupes))
                )

    return groups
