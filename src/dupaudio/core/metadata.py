"""Read audio tags and stream info using mutagen."""

from __future__ import annotations

from pathlib import Path

from mutagen import File as MutagenFile  # type: ignore[import-untyped]

from ..models import AudioFile

# mutagen's EasyMP3/EasyMP4 style keys are lists; these are the common ones.
_ARTIST_KEYS = ("artist", "albumartist", "author")
_TITLE_KEYS = ("title",)
_ALBUM_KEYS = ("album",)


def _first(tags, keys) -> str | None:
    for key in keys:
        val = tags.get(key)
        if val:
            if isinstance(val, (list, tuple)):
                val = val[0] if val else None
            if val:
                return str(val).strip() or None
    return None


def read_metadata(af: AudioFile) -> AudioFile:
    """Populate tag/bitrate/duration fields on ``af`` in place and return it.

    Never raises: on failure sets ``af.error`` and leaves fields as None.
    """
    try:
        mf = MutagenFile(af.path, easy=True)
    except Exception as exc:  # noqa: BLE001 — mutagen raises varied errors
        af.error = f"metadata read failed: {exc}"
        return af

    if mf is None:
        # Unrecognized / unsupported container — not fatal, just no tags.
        return af

    tags = mf.tags or {}
    af.artist = _first(tags, _ARTIST_KEYS)
    af.title = _first(tags, _TITLE_KEYS)
    af.album = _first(tags, _ALBUM_KEYS)

    info = getattr(mf, "info", None)
    if info is not None:
        br = getattr(info, "bitrate", None)
        af.bitrate = int(br) if br else None
        length = getattr(info, "length", None)
        af.duration = float(length) if length else None
    return af
