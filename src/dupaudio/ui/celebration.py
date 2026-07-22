"""A centered media overlay played after files are moved to the Trash.

Tries to play the .mp4 via QtMultimedia; if that backend is unavailable or the
file fails to load, it falls back to the animated .gif via QMovie. Closes on
media end, on click, on Esc, or after a safety timeout.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, QObject, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QMovie, QPainter
from PySide6.QtWidgets import QLabel, QWidget

ASSETS = Path(__file__).resolve().parent.parent / "assets"
MP4 = ASSETS / "trash.mp4"
GIF = ASSETS / "trash.gif"

# Safety net: never leave the overlay stuck if the media never signals its end.
_MAX_MS = 12_000


class CelebrationOverlay(QWidget):
    """Semi-transparent overlay that plays a short clip centered on its parent."""

    closed = Signal()

    def __init__(self, parent: QWidget, mp4: Path = MP4, gif: Path = GIF) -> None:
        super().__init__(parent)
        self._mode: str | None = None
        self._player = None
        self._audio = None
        self._video = None
        self._movie: QMovie | None = None
        self._label: QLabel | None = None
        self._native_ratio = 16 / 9
        self._closing = False

        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self._build_media(mp4, gif)

        if self._mode:
            parent.installEventFilter(self)  # follow parent resizes
            self._timeout = QTimer(self)
            self._timeout.setSingleShot(True)
            self._timeout.timeout.connect(self._close)
            self._timeout.start(_MAX_MS)

    def has_media(self) -> bool:
        return self._mode is not None

    # ---- construction ----------------------------------------------------
    def _build_media(self, mp4: Path, gif: Path) -> None:
        if mp4 and Path(mp4).exists() and self._try_video(mp4):
            self._mode = "video"
            return
        if gif and Path(gif).exists() and self._try_gif(gif):
            self._mode = "gif"
            return

    def _try_video(self, mp4: Path) -> bool:
        try:
            from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
            from PySide6.QtMultimediaWidgets import QVideoWidget
        except Exception:
            return False
        try:
            self._video = QVideoWidget(self)
            self._video.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            self._player = QMediaPlayer(self)
            self._audio = QAudioOutput(self)
            self._player.setAudioOutput(self._audio)
            self._player.setVideoOutput(self._video)
            self._player.setSource(QUrl.fromLocalFile(str(mp4)))
            self._player.mediaStatusChanged.connect(self._on_media_status)
            return True
        except Exception:
            self._player = None
            self._video = None
            return False

    def _try_gif(self, gif: Path) -> bool:
        movie = QMovie(str(gif))
        if not movie.isValid():
            return False
        self._movie = movie
        movie.jumpToFrame(0)
        native = movie.currentPixmap().size()
        if native.width() and native.height():
            self._native_ratio = native.width() / native.height()
        self._label = QLabel(self)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._label.setMovie(movie)
        movie.frameChanged.connect(self._on_gif_frame)
        return True

    # ---- show / layout ---------------------------------------------------
    def play_centered(self) -> None:
        """Show the overlay covering the parent and start playback."""
        if not self._mode:
            return
        self.setGeometry(self.parentWidget().rect())
        self._layout_media()
        self.show()
        self.raise_()
        self.setFocus()
        if self._mode == "video":
            self._player.play()
        else:
            self._movie.start()

    def _layout_media(self) -> None:
        pw = self.width()
        ph = self.height()
        w = int(pw * 0.6)
        h = int(w / self._native_ratio)
        max_h = int(ph * 0.7)
        if h > max_h:
            h = max_h
            w = int(h * self._native_ratio)
        x = (pw - w) // 2
        y = (ph - h) // 2
        if self._mode == "video":
            self._video.setGeometry(x, y, w, h)
        else:
            self._label.setGeometry(x, y, w, h)
            self._movie.setScaledSize(self._fit(w, h))

    def _fit(self, w: int, h: int):
        from PySide6.QtCore import QSize

        # Fit the gif inside w x h while keeping its aspect ratio.
        bw = w
        bh = int(bw / self._native_ratio)
        if bh > h:
            bh = h
            bw = int(bh * self._native_ratio)
        return QSize(bw, bh)

    # ---- events ----------------------------------------------------------
    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Resize and obj is self.parentWidget():
            self.setGeometry(self.parentWidget().rect())
            self._layout_media()
        return super().eventFilter(obj, event)

    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(0, 0, 0, 190))
        p.end()

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self._close()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() in (Qt.Key_Escape, Qt.Key_Space, Qt.Key_Return):
            self._close()

    def _on_media_status(self, status) -> None:
        from PySide6.QtMultimedia import QMediaMetaData, QMediaPlayer

        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            res = self._player.metaData().value(QMediaMetaData.Key.Resolution)
            if res is not None and res.width() and res.height():
                self._native_ratio = res.width() / res.height()
                self._layout_media()
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            self._close()

    def _on_gif_frame(self, frame: int) -> None:
        # Play the gif once, then close on its last frame.
        if self._movie and self._movie.frameCount() > 0 and frame >= self._movie.frameCount() - 1:
            QTimer.singleShot(150, self._close)

    # ---- teardown --------------------------------------------------------
    def _close(self) -> None:
        if self._closing:
            return
        self._closing = True
        try:
            if self._player is not None:
                self._player.stop()
            if self._movie is not None:
                self._movie.stop()
            self.parentWidget().removeEventFilter(self)
        except Exception:
            pass
        self.hide()
        self.closed.emit()
        self.deleteLater()
