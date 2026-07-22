"""Unit tests for the non-UI core logic."""

from __future__ import annotations

from pathlib import Path

import pytest

from dupaudio.core.deleter import (
    AllFilesInGroupError,
    delete_files,
    validate_no_full_group_wipe,
)
from dupaudio.core.grouper import find_duplicates
from dupaudio.core.hasher import hash_file
from dupaudio.core.keeprules import apply_keep_rules, choose_keeper
from dupaudio.core.scanner import iter_audio_files
from dupaudio.models import AudioFile, DuplicateGroup, MatchType


def _make(path: Path, data: bytes) -> AudioFile:
    path.write_bytes(data)
    st = path.stat()
    return AudioFile(path=path, size=st.st_size, mtime=st.st_mtime)


# ---- hashing ----
def test_hash_identical_bytes_match(tmp_path):
    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    a.write_bytes(b"hello world" * 100)
    b.write_bytes(b"hello world" * 100)
    assert hash_file(a) == hash_file(b)


def test_hash_different_bytes_differ(tmp_path):
    a = tmp_path / "a.mp3"
    b = tmp_path / "b.mp3"
    a.write_bytes(b"one")
    b.write_bytes(b"two")
    assert hash_file(a) != hash_file(b)


# ---- scanning ----
def test_scanner_finds_only_audio(tmp_path):
    (tmp_path / "song.mp3").write_bytes(b"x")
    (tmp_path / "notes.txt").write_bytes(b"x")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "track.flac").write_bytes(b"y")
    found = {af.path.name for af in iter_audio_files([tmp_path])}
    assert found == {"song.mp3", "track.flac"}


# ---- grouping: exact ----
def test_exact_duplicates_grouped(tmp_path):
    payload = b"AUDIODATA" * 500
    files = [
        _make(tmp_path / "copy1.mp3", payload),
        _make(tmp_path / "copy2.mp3", payload),
        _make(tmp_path / "unique.mp3", b"different"),
    ]
    groups = find_duplicates(files, enable_metadata=False)
    assert len(groups) == 1
    g = groups[0]
    assert g.match_type == MatchType.EXACT
    assert {f.name for f in g.files} == {"copy1.mp3", "copy2.mp3"}


def test_different_sizes_never_grouped(tmp_path):
    files = [
        _make(tmp_path / "a.mp3", b"short"),
        _make(tmp_path / "b.mp3", b"much longer content here"),
    ]
    groups = find_duplicates(files, enable_metadata=False)
    assert groups == []


def test_require_valid_audio_excludes_stub_placeholders(tmp_path):
    # Simulates the cloud-placeholder bug: byte-identical 4 KB stubs that are
    # NOT real audio (mutagen decoded no bitrate/duration) must NOT be grouped.
    stub = b"\x00" * 4096
    a = _make(tmp_path / "song_one.mp3", stub)
    b = _make(tmp_path / "song_two.mp3", stub)
    # No bitrate/duration -> is_valid_audio is False for both.
    assert not a.is_valid_audio and not b.is_valid_audio

    # Without the guard, they falsely group as an exact duplicate.
    assert len(find_duplicates([a, b], enable_metadata=False)) == 1
    # With the guard, they are excluded entirely.
    assert find_duplicates([a, b], enable_metadata=False, require_valid_audio=True) == []


def test_require_valid_audio_keeps_real_audio(tmp_path):
    payload = b"AUDIO" * 500
    a = _make(tmp_path / "dup1.mp3", payload)
    b = _make(tmp_path / "dup2.mp3", payload)
    for f in (a, b):
        f.bitrate, f.duration = 320000, 210.0  # decoded as real audio
    groups = find_duplicates([a, b], enable_metadata=False, require_valid_audio=True)
    assert len(groups) == 1
    assert {f.name for f in groups[0].files} == {"dup1.mp3", "dup2.mp3"}


# ---- grouping: metadata ----
def test_metadata_duplicates_grouped(tmp_path):
    # Two byte-different files with identical tags.
    a = _make(tmp_path / "low.mp3", b"aaaa")
    b = _make(tmp_path / "high.mp3", b"bbbbbbbb")
    for f in (a, b):
        f.artist, f.title, f.album = "Artist", "Song", "Album"
    a.bitrate, b.bitrate = 128000, 320000
    groups = find_duplicates([a, b], enable_metadata=True)
    meta = [g for g in groups if g.match_type == MatchType.METADATA]
    assert len(meta) == 1
    assert {f.name for f in meta[0].files} == {"low.mp3", "high.mp3"}


# ---- keep rules ----
def test_keeper_prefers_highest_bitrate(tmp_path):
    a = _make(tmp_path / "low.mp3", b"a")
    b = _make(tmp_path / "high.mp3", b"b")
    a.bitrate, b.bitrate = 128000, 320000
    assert choose_keeper([a, b]).name == "high.mp3"


def test_keeper_prefers_more_tags_when_bitrate_equal(tmp_path):
    a = _make(tmp_path / "bare.mp3", b"a")
    b = _make(tmp_path / "tagged.mp3", b"b")
    a.bitrate = b.bitrate = 256000
    b.artist, b.title, b.album = "x", "y", "z"
    assert choose_keeper([a, b]).name == "tagged.mp3"


def test_apply_keep_rules_sets_keep_path(tmp_path):
    a = _make(tmp_path / "low.mp3", b"a")
    b = _make(tmp_path / "high.mp3", b"b")
    a.bitrate, b.bitrate = 96000, 320000
    g = DuplicateGroup(match_type=MatchType.METADATA, files=[a, b])
    apply_keep_rules([g])
    assert g.keep_path == b.path


# ---- deleter ----
def test_delete_uses_trash_not_remove(tmp_path):
    a = tmp_path / "a.mp3"
    a.write_bytes(b"data")
    trashed: list[str] = []
    result = delete_files([a], trash=lambda p: trashed.append(p), write_log=False)
    assert trashed == [str(a)]
    assert result.trashed == [a]
    assert a.exists()  # our fake trash didn't actually remove it


def test_full_group_wipe_blocked():
    g_paths = [[Path("/x/a.mp3"), Path("/x/b.mp3")]]
    with pytest.raises(AllFilesInGroupError):
        validate_no_full_group_wipe(g_paths, {Path("/x/a.mp3"), Path("/x/b.mp3")})


def test_partial_group_delete_allowed():
    g_paths = [[Path("/x/a.mp3"), Path("/x/b.mp3")]]
    # Deleting only one of the two is fine.
    validate_no_full_group_wipe(g_paths, {Path("/x/a.mp3")})
