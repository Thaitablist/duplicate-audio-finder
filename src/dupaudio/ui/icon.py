"""Load the bundled app icon (master PNG) and render it at any size."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap

ASSETS = Path(__file__).resolve().parent.parent / "assets"
PNG_PATH = ASSETS / "icon.png"

_ICON_SIZES = (16, 24, 32, 48, 64, 128, 256, 512)


def render_pixmap(size: int) -> QPixmap:
    """Return the app icon scaled to ``size`` px with smooth filtering."""
    pm = QPixmap(str(PNG_PATH))
    if pm.isNull():
        return pm
    return pm.scaled(
        size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation
    )


def app_icon() -> QIcon:
    """Return a multi-resolution QIcon for windows / the dock / taskbar."""
    icon = QIcon()
    for size in _ICON_SIZES:
        icon.addPixmap(render_pixmap(size))
    return icon
