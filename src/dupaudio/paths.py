"""Per-user application data directory, resolved per platform."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from . import APP_NAME


def app_data_dir() -> Path:
    """Return (without creating) the app's data directory for this user.

    - Windows: %APPDATA%\\Duplicate Audio Finder
    - macOS:   ~/Library/Application Support/Duplicate Audio Finder
    - other:   $XDG_DATA_HOME/dupaudio or ~/.local/share/dupaudio
    """
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming")
        return Path(base) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    base = os.environ.get("XDG_DATA_HOME") or (Path.home() / ".local" / "share")
    return Path(base) / "dupaudio"
