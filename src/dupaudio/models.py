"""Core data models shared across the app."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class MatchType(str, Enum):
    """How the files in a group were determined to be duplicates."""

    EXACT = "exact"       # byte-identical (same SHA-256)
    METADATA = "metadata"  # same artist/title/album tags, different bytes


@dataclass
class AudioFile:
    """A single audio file discovered during a scan."""

    path: Path
    size: int
    mtime: float
    # Populated lazily — may be None if not yet computed / unreadable.
    sha256: str | None = None
    artist: str | None = None
    title: str | None = None
    album: str | None = None
    bitrate: int | None = None       # bits per second
    duration: float | None = None    # seconds
    error: str | None = None         # set if the file could not be read

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def tag_completeness(self) -> int:
        """Number of populated core tag fields (for keep-rule ranking)."""
        return sum(bool(v) for v in (self.artist, self.title, self.album))

    @property
    def is_valid_audio(self) -> bool:
        """True only if mutagen actually decoded audio stream info.

        Cloud placeholder stubs and corrupt/non-audio files yield no bitrate
        or duration; treating them as duplicates by byte-hash is meaningless
        (all stubs share identical filler bytes), so they must be excluded.
        Requires :func:`core.metadata.read_metadata` to have run first.
        """
        return self.error is None and (
            self.bitrate is not None or self.duration is not None
        )

    def metadata_key(self) -> tuple[str, str, str] | None:
        """Normalized (artist, title, album) key, or None if too little tag data."""
        if not (self.artist and self.title):
            return None
        norm = lambda s: (s or "").strip().casefold()
        return (norm(self.artist), norm(self.title), norm(self.album))


@dataclass
class DuplicateGroup:
    """A set of files considered duplicates of one another."""

    match_type: MatchType
    files: list[AudioFile] = field(default_factory=list)
    # Path of the file the keep-rules picked to keep. User can override.
    keep_path: Path | None = None

    @property
    def total_size(self) -> int:
        return sum(f.size for f in self.files)

    @property
    def reclaimable_size(self) -> int:
        """Bytes freed if every file except the kept one is removed."""
        if not self.files:
            return 0
        # Keep the largest single file's size occupied; free the rest.
        return self.total_size - max(f.size for f in self.files)
