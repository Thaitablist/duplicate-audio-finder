"""Build a macOS-style rounded (squircle) app icon and platform icon files.

Run once before packaging:  python build/make_icons.py

Pipeline:
  assets/icon_source.png  (raw square artwork)
      -> assets/icon.png   (1024px, Apple superellipse mask + standard margin)
      -> assets/icon.icns  (macOS, via iconutil)
      -> assets/icon.ico    (Windows, if Pillow is available)

icon.png is the runtime icon loaded by the app (window / dock / header logo).
"""

from __future__ import annotations

import math
import subprocess
import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QPainter, QPainterPath, QPixmap

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "src" / "dupaudio" / "assets"
SOURCE = ASSETS / "icon_source.png"   # raw artwork
MASTER = ASSETS / "icon.png"          # rounded runtime icon

CANVAS = 1024          # full icon canvas
CONTENT = 824          # Apple Big Sur content square (transparent margin around it)
SQUIRCLE_N = 5.0       # superellipse exponent (~Apple squircle)


def _superellipse_path(cx: float, cy: float, a: float, n: float, steps: int = 720) -> QPainterPath:
    """A superellipse (rounded-square) path centered at (cx, cy), half-size a."""
    path = QPainterPath()
    for i in range(steps + 1):
        t = 2 * math.pi * i / steps
        ct, st = math.cos(t), math.sin(t)
        x = cx + a * math.copysign(abs(ct) ** (2.0 / n), ct)
        y = cy + a * math.copysign(abs(st) ** (2.0 / n), st)
        path.moveTo(x, y) if i == 0 else path.lineTo(x, y)
    path.closeSubpath()
    return path


def build_rounded_master() -> QPixmap:
    """Mask the raw artwork into a macOS squircle with the standard margin."""
    src = QPixmap(str(SOURCE)).scaled(
        CONTENT, CONTENT, Qt.KeepAspectRatio, Qt.SmoothTransformation
    )
    out = QPixmap(CANVAS, CANVAS)
    out.fill(Qt.transparent)

    painter = QPainter(out)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)
    path = _superellipse_path(CANVAS / 2, CANVAS / 2, CONTENT / 2, SQUIRCLE_N)
    painter.setClipPath(path)
    offset = (CANVAS - CONTENT) // 2
    painter.drawPixmap(offset, offset, src)
    painter.end()
    return out


def scaled(pm: QPixmap, size: int) -> QPixmap:
    return pm.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)


def main() -> int:
    QGuiApplication(sys.argv)  # needed for QPixmap
    if not SOURCE.exists():
        print(f"missing raw artwork: {SOURCE}", file=sys.stderr)
        return 1

    master = build_rounded_master()
    master.save(str(MASTER), "PNG")
    print("wrote", MASTER)

    # ---- macOS .icns via iconutil ----
    if sys.platform == "darwin":
        with tempfile.TemporaryDirectory() as tmp:
            iconset = Path(tmp) / "icon.iconset"
            iconset.mkdir()
            for base in (16, 32, 128, 256, 512):
                scaled(master, base).save(str(iconset / f"icon_{base}x{base}.png"), "PNG")
                scaled(master, base * 2).save(str(iconset / f"icon_{base}x{base}@2x.png"), "PNG")
            out = ASSETS / "icon.icns"
            subprocess.run(
                ["iconutil", "-c", "icns", str(iconset), "-o", str(out)], check=True
            )
            print("wrote", out)

    # ---- Windows .ico via Pillow (optional) ----
    try:
        from PIL import Image  # type: ignore
    except ImportError:
        print("Pillow not installed — skipping .ico (needed for Windows build)")
        return 0

    tmp_png = ASSETS / "_ico_tmp.png"
    scaled(master, 256).save(str(tmp_png), "PNG")
    Image.open(tmp_png).convert("RGBA").save(
        ASSETS / "icon.ico",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    tmp_png.unlink(missing_ok=True)
    print("wrote", ASSETS / "icon.ico")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
