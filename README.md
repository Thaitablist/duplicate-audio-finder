# Duplicate Audio Finder

A native desktop app (Windows & macOS) to **find and safely delete duplicate audio files**.
No browser required — it installs and runs as a normal desktop application.

## Features

- **Exact match** — byte-identical files, verified with a size pre-filter + SHA-256.
- **Metadata match** — files with the same *artist / title / album* tags but different
  bytes (e.g. the same song at a different bitrate). Shown separately and flagged in
  orange so you look before you delete.
- **Smart keep-rules** — automatically picks one file to keep per group, preferring
  higher bitrate, more complete tags, non-"copy" paths, shorter paths, and older files.
- **Safe deletion** — selected files go to the **Recycle Bin / Trash** (never permanent
  `remove`), every deletion is written to an undo log, and the app refuses to wipe every
  file in a group.
- **Responsive UI** — scanning/hashing runs on a background thread with progress and a
  cancel button, so the window never freezes.

## Tech stack

Python 3.11+ · PySide6 (Qt) · mutagen · Send2Trash · packaged with PyInstaller.

## Run from source

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m dupaudio
```

## Test

```bash
pytest
```

## Build an installable app

Build on the OS you are targeting.

**macOS** — produces `Duplicate Audio Finder.app`:
```bash
pyinstaller build/dupaudio.spec
# optional: package dist/*.app into a .dmg, then codesign + notarize for distribution
```

**Windows** — must be built on a Windows machine (PyInstaller does not
cross-compile). The all-in-one script does everything (venv, deps, icons,
app, installer):
```bat
build\build_windows.bat
```
…or step by step:
```bat
python build\make_icons.py                REM generates icon.ico (needs Pillow)
pyinstaller build\dupaudio.spec --distpath dist --workpath build\_work --noconfirm
ISCC build\installer.iss                  REM Inno Setup -> dist\DuplicateAudioFinder-Setup.exe
```
Requires [Inno Setup 6](https://jrsoftware.org/isdl.php) for the installer step.

## Project layout

```
src/dupaudio/
  core/       scanner, hasher, metadata, grouper, keeprules, deleter  (no Qt)
  ui/         main_window, results tree model, settings dialog
  workers.py  QThread wrappers around core
  models.py   AudioFile, DuplicateGroup
tests/        unit tests for the core logic
build/        PyInstaller spec + Inno Setup script
```

The `core/` package has no Qt dependency, so all detection/deletion logic is unit-tested
without a display.
