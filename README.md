<div align="center">

<img src="src/dupaudio/assets/icon.png" width="150" alt="Duplicate Audio Finder logo">

# Duplicate Audio Finder

### Find &amp; safely delete duplicate audio files — on macOS &amp; Windows

<em>A native desktop app. No browser, no cloud, no nonsense. Your files stay on your machine.</em>

<br>

**English** · [ไทย 🇹🇭](README.th.md)

<br>

[![Release](https://img.shields.io/github/v/release/Thaitablist/duplicate-audio-finder?style=for-the-badge&color=00E5FF)](https://github.com/Thaitablist/duplicate-audio-finder/releases/latest)
[![Build](https://img.shields.io/github/actions/workflow/status/Thaitablist/duplicate-audio-finder/build.yml?style=for-the-badge)](https://github.com/Thaitablist/duplicate-audio-finder/actions)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows-7C4DFF?style=for-the-badge)](#-download)
[![License](https://img.shields.io/badge/license-MIT-FF2D95?style=for-the-badge)](#-license)

<br>

### ⬇️ Download

[![Download for Windows](https://img.shields.io/badge/Download-Windows%20Installer-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/Thaitablist/duplicate-audio-finder/releases/latest/download/DuplicateAudioFinder-Setup.exe)
&nbsp;
[![Download for macOS](https://img.shields.io/badge/Download-macOS%20(.dmg)-000000?style=for-the-badge&logo=apple&logoColor=white)](https://github.com/Thaitablist/duplicate-audio-finder/releases/latest/download/DuplicateAudioFinder.dmg)

<br>

<img src="docs/screenshot.png" width="820" alt="Duplicate Audio Finder screenshot">

</div>

---

## ✨ Features

- 🎯 **Exact match** — byte-identical files, verified with a size pre-filter + SHA-256 (fast &amp; 100% accurate).
- 🏷️ **Metadata match** — same *artist / title / album* tags but different bytes (e.g. the same track at a different bitrate). Flagged separately so you look before you delete.
- ☁️ **Cloud-safe** — skips OneDrive / cloud "online-only" placeholder stubs so they're never mistaken for duplicates.
- 🧠 **Smart keep-rules** — auto-picks one file to keep per group (highest bitrate → most complete tags → non-"copy" path → oldest).
- 🗑️ **Safe delete** — files go to the **Recycle Bin / Trash** (never permanent), every deletion is logged, and the app refuses to wipe an entire group.
- ⚡ **Responsive** — scanning runs off the UI thread with an animated equalizer, live progress, and cancel.
- 🎬 **Satisfying** — a little celebration clip plays when the trash is taken out.

## ⬇️ Download

| Platform | File | Link |
|---|---|---|
| 🪟 Windows | `DuplicateAudioFinder-Setup.exe` | [Download](https://github.com/Thaitablist/duplicate-audio-finder/releases/latest/download/DuplicateAudioFinder-Setup.exe) |
| 🍎 macOS | `DuplicateAudioFinder.dmg` | [Download](https://github.com/Thaitablist/duplicate-audio-finder/releases/latest/download/DuplicateAudioFinder.dmg) |

> **First launch:** the app isn't code-signed, so the OS will warn once.
> - **Windows:** SmartScreen → *More info* → *Run anyway*.
> - **macOS:** right-click the app → *Open* (or run `xattr -dr com.apple.quarantine "/Applications/Duplicate Audio Finder.app"`).

## 🎧 How duplicate detection works

1. **Bucket by size** — only same-size files can be byte-identical, which skips most of the work.
2. **Hash** — SHA-256 (streamed in 64&nbsp;KB chunks) confirms an **exact** duplicate.
3. **Tags** — remaining files with matching normalized *artist + title + album* form a **metadata** group.

Only files that decode as real audio (valid bitrate/duration) are compared, so placeholders and corrupt files never create false duplicates.

## 🛠️ Build from source

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python -m dupaudio                  # run it
pytest                             # run the tests
```

### Package a native app

**macOS** → `.app` + `.dmg`
```bash
python build/make_icons.py
pyinstaller build/dupaudio.spec --distpath dist --workpath build/_work --noconfirm
bash build/make_dmg.sh
```

**Windows** → `.exe` + installer (needs [Inno Setup 6](https://jrsoftware.org/isdl.php))
```bat
build\build_windows.bat
```

> Releases are built automatically by GitHub Actions on every `v*` tag — see [`.github/workflows/build.yml`](.github/workflows/build.yml).

## 🧱 Tech stack

Python 3.11+ · [PySide6](https://doc.qt.io/qtforpython/) (Qt) · [mutagen](https://mutagen.readthedocs.io/) · [Send2Trash](https://github.com/arsenetar/send2trash) · packaged with [PyInstaller](https://pyinstaller.org/).

The `src/dupaudio/core/` package has no Qt dependency, so all detection/deletion logic is unit-tested without a display.

## 📝 License

MIT

---

<div align="center">
<sub>⚡ Developed by <strong>Dev ZLEX</strong> · <strong>DJ LAB SIAM</strong> 🎧</sub>
</div>
