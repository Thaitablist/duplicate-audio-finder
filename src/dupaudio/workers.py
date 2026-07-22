"""Background workers that keep the UI responsive during scan/delete."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QThread, Signal

from .core import grouper, scanner
from .core.keeprules import apply_keep_rules
from .core.metadata import read_metadata
from .models import DuplicateGroup


class ScanWorker(QObject):
    """Runs a full scan (walk -> hash -> group -> keep-rules) off the UI thread."""

    progress = Signal(int, int, str)          # done, total, message
    finished = Signal(list)                    # list[DuplicateGroup]
    failed = Signal(str)

    def __init__(
        self,
        roots: list[Path],
        enable_metadata: bool = True,
        require_valid_audio: bool = True,
    ) -> None:
        super().__init__()
        self._roots = roots
        self._enable_metadata = enable_metadata
        self._require_valid_audio = require_valid_audio
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def _should_cancel(self) -> bool:
        return self._cancel

    def run(self) -> None:
        try:
            self.progress.emit(0, 0, "Scanning folders…")
            files = list(
                scanner.iter_audio_files(self._roots, should_cancel=self._should_cancel)
            )
            if self._cancel:
                self.finished.emit([])
                return

            # Read metadata up front so keep-rules have bitrate/tags to rank on.
            total = len(files)
            for i, af in enumerate(files, start=1):
                if self._cancel:
                    self.finished.emit([])
                    return
                self.progress.emit(i, total, f"Reading {af.name}")
                read_metadata(af)

            groups = grouper.find_duplicates(
                files,
                enable_metadata=self._enable_metadata,
                require_valid_audio=self._require_valid_audio,
                progress=lambda d, t, m: self.progress.emit(d, t, m),
                should_cancel=self._should_cancel,
            )
            apply_keep_rules(groups)
            self.finished.emit(groups)
        except Exception as exc:  # noqa: BLE001 — surface any error to the UI
            self.failed.emit(str(exc))


def run_in_thread(worker: QObject) -> QThread:
    """Move ``worker`` to a new QThread and start it. Caller keeps references.

    The worker must expose a ``run()`` slot and a ``finished``/``failed`` signal.
    """
    thread = QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.run)  # type: ignore[attr-defined]
    # Ensure the thread quits when the worker is done.
    if hasattr(worker, "finished"):
        worker.finished.connect(thread.quit)  # type: ignore[attr-defined]
    if hasattr(worker, "failed"):
        worker.failed.connect(thread.quit)  # type: ignore[attr-defined]
    thread.start()
    return thread
