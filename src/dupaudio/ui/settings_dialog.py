"""Settings dialog: metadata matching toggle and file extensions."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from ..core.scanner import DEFAULT_AUDIO_EXTS


class SettingsDialog(QDialog):
    def __init__(
        self,
        parent=None,
        *,
        enable_metadata: bool = True,
        require_valid_audio: bool = True,
        exts: str = "",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        layout = QVBoxLayout(self)

        self.metadata_check = QCheckBox("Also match by metadata (artist / title / album)")
        self.metadata_check.setChecked(enable_metadata)
        layout.addWidget(self.metadata_check)

        self.valid_audio_check = QCheckBox(
            "Only compare real audio files (skip cloud placeholders & unreadable files)"
        )
        self.valid_audio_check.setChecked(require_valid_audio)
        self.valid_audio_check.setToolTip(
            "Recommended. Prevents cloud 'online-only' stub files (all identical\n"
            "4 KB placeholders) from being wrongly grouped as exact duplicates."
        )
        layout.addWidget(self.valid_audio_check)

        layout.addWidget(QLabel("Audio extensions to scan (comma-separated):"))
        self.exts_edit = QLineEdit(exts or ",".join(sorted(DEFAULT_AUDIO_EXTS)))
        layout.addWidget(self.exts_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def enable_metadata(self) -> bool:
        return self.metadata_check.isChecked()

    def require_valid_audio(self) -> bool:
        return self.valid_audio_check.isChecked()

    def extensions(self) -> frozenset[str]:
        raw = self.exts_edit.text().split(",")
        exts = {e.strip().lower() for e in raw if e.strip()}
        exts = {e if e.startswith(".") else f".{e}" for e in exts}
        return frozenset(exts) or DEFAULT_AUDIO_EXTS
