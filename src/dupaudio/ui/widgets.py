"""Custom widgets — the animated equalizer scan indicator."""

from __future__ import annotations

import math

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath
from PySide6.QtWidgets import QWidget

from . import theme


class EqualizerIndicator(QWidget):
    """A row of neon bars that bounce like an audio equalizer while active.

    Call :meth:`start` when a scan begins and :meth:`stop` when it ends. When
    idle it shows short, dim static bars so it still reads as part of the UI.
    """

    def __init__(self, bars: int = 7, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._n = bars
        self._phase = 0.0
        # Each bar has its own speed/offset so they don't move in lock-step.
        self._speeds = [0.9 + 0.35 * i % 1.6 + 0.6 for i in range(bars)]
        self._offsets = [i * 0.7 for i in range(bars)]
        self._active = False
        self.setFixedSize(bars * 8 + 6, 28)

        self._timer = QTimer(self)
        self._timer.setInterval(55)
        self._timer.timeout.connect(self._tick)

    def start(self) -> None:
        self._active = True
        self.show()
        if not self._timer.isActive():
            self._timer.start()

    def stop(self) -> None:
        self._active = False
        self._timer.stop()
        self.update()

    def _tick(self) -> None:
        self._phase += 0.28
        self.update()

    def _level(self, i: int) -> float:
        """Return a 0..1 height fraction for bar ``i``."""
        if not self._active:
            return 0.22
        raw = math.sin(self._phase * self._speeds[i] + self._offsets[i])
        return 0.28 + 0.72 * (0.5 + 0.5 * raw)

    def paintEvent(self, event) -> None:  # noqa: N802 (Qt naming)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        bar_w = 5.0
        gap = (w - self._n * bar_w) / (self._n + 1)

        grad = QLinearGradient(0, h, 0, 0)
        grad.setColorAt(0.0, QColor(theme.NEON_CYAN))
        grad.setColorAt(1.0, QColor(theme.NEON_PINK))
        dim = QColor(theme.BORDER)

        for i in range(self._n):
            level = self._level(i)
            bar_h = max(3.0, level * (h - 4))
            x = gap + i * (bar_w + gap)
            y = (h - bar_h) / 2
            path = QPainterPath()
            path.addRoundedRect(x, y, bar_w, bar_h, 2.5, 2.5)
            p.fillPath(path, grad if self._active else dim)
        p.end()
