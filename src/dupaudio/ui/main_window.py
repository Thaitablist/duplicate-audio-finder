"""Main application window (DJ LAB SIAM themed)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from .. import APP_NAME
from ..core.deleter import (
    AllFilesInGroupError,
    delete_files,
    validate_no_full_group_wipe,
)
from ..models import DuplicateGroup
from ..workers import ScanWorker, run_in_thread
from . import theme
from .help_dialog import HelpDialog
from .icon import app_icon, render_pixmap
from .models_qt import DuplicateTreeModel, _human_size
from .settings_dialog import SettingsDialog
from .widgets import EqualizerIndicator

CREDIT = "⚡ DEV ZLEX"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(app_icon())
        self.resize(940, 660)

        self._enable_metadata = True
        self._require_valid_audio = True
        self._scan_thread = None
        self._scan_worker: ScanWorker | None = None

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 16, 18, 12)
        root.setSpacing(12)

        root.addLayout(self._build_header())
        root.addLayout(self._build_folder_controls())

        self.folder_list = QListWidget()
        self.folder_list.setMaximumHeight(96)
        root.addWidget(self.folder_list)

        root.addLayout(self._build_scan_row())

        # --- results tree ---
        self.model = DuplicateTreeModel()
        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setColumnWidth(0, 400)
        self.tree.setAlternatingRowColors(False)
        root.addWidget(self.tree, 1)

        root.addLayout(self._build_delete_row())
        root.addLayout(self._build_footer())

        self.setCentralWidget(central)
        self._wire()

    # ---- layout builders -------------------------------------------------
    def _build_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(render_pixmap(46))
        logo.setFixedSize(46, 46)
        theme.neon_glow(logo, theme.NEON_CYAN, radius=26)
        header.addWidget(logo)

        titles = QVBoxLayout()
        titles.setSpacing(0)
        brand = QLabel("DJ LAB SIAM")
        brand.setObjectName("appBrand")
        title = QLabel("Duplicate Audio Finder")
        title.setObjectName("appTitle")
        titles.addWidget(brand)
        titles.addWidget(title)
        header.addLayout(titles)
        header.addStretch()

        self.help_btn = QPushButton("คู่มือการใช้งาน")
        self.settings_btn = QPushButton("Settings")
        header.addWidget(self.help_btn)
        header.addWidget(self.settings_btn)
        return header

    def _build_folder_controls(self) -> QHBoxLayout:
        row = QHBoxLayout()
        label = QLabel("SCAN FOLDERS")
        label.setObjectName("sectionLabel")
        self.add_btn = QPushButton("Add folder…")
        self.remove_btn = QPushButton("Remove")
        row.addWidget(label)
        row.addStretch()
        row.addWidget(self.add_btn)
        row.addWidget(self.remove_btn)
        return row

    def _build_scan_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self.scan_btn = QPushButton("Scan for duplicates")
        self.scan_btn.setObjectName("primary")
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setEnabled(False)

        self.eq = EqualizerIndicator()
        self.eq.stop()  # start in the dim idle state

        self.progress = QProgressBar()
        self.progress.setTextVisible(True)

        row.addWidget(self.scan_btn)
        row.addWidget(self.cancel_btn)
        row.addWidget(self.eq)
        row.addWidget(self.progress, 1)
        return row

    def _build_delete_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self.summary = QLabel("Ready. Add a folder and hit Scan.")
        self.summary.setObjectName("summaryLabel")
        self.delete_btn = QPushButton("Move selected to Trash")
        self.delete_btn.setObjectName("danger")
        self.delete_btn.setEnabled(False)
        row.addWidget(self.summary, 1)
        row.addWidget(self.delete_btn)
        return row

    def _build_footer(self) -> QHBoxLayout:
        row = QHBoxLayout()
        credit = QLabel(CREDIT)
        credit.setObjectName("creditLabel")
        credit.setToolTip("Developed by Dev ZLEX · DJ LAB SIAM")
        brand = QLabel("DJ LAB SIAM ✕ DUPLICATE AUDIO FINDER")
        brand.setObjectName("footerBrand")
        row.addWidget(credit)
        row.addStretch()
        row.addWidget(brand)
        return row

    def _wire(self) -> None:
        self.add_btn.clicked.connect(self._add_folder)
        self.remove_btn.clicked.connect(self._remove_folder)
        self.settings_btn.clicked.connect(self._open_settings)
        self.help_btn.clicked.connect(self._open_help)
        self.scan_btn.clicked.connect(self._start_scan)
        self.cancel_btn.clicked.connect(self._cancel_scan)
        self.delete_btn.clicked.connect(self._delete_selected)

    # ---- folder management ----
    def _add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose a folder to scan")
        if folder:
            existing = {self.folder_list.item(i).text() for i in range(self.folder_list.count())}
            if folder not in existing:
                self.folder_list.addItem(folder)

    def _remove_folder(self) -> None:
        for item in self.folder_list.selectedItems():
            self.folder_list.takeItem(self.folder_list.row(item))

    def _open_settings(self) -> None:
        dlg = SettingsDialog(
            self,
            enable_metadata=self._enable_metadata,
            require_valid_audio=self._require_valid_audio,
        )
        if dlg.exec():
            self._enable_metadata = dlg.enable_metadata()
            self._require_valid_audio = dlg.require_valid_audio()

    def _open_help(self) -> None:
        HelpDialog(self).exec()

    # ---- scanning ----
    def _roots(self) -> list[Path]:
        return [Path(self.folder_list.item(i).text()) for i in range(self.folder_list.count())]

    def _start_scan(self) -> None:
        roots = self._roots()
        if not roots:
            QMessageBox.information(self, APP_NAME, "Add at least one folder to scan.")
            return
        self._set_scanning(True)
        self.model.set_groups([])
        self.summary.setText("Scanning…")

        worker = ScanWorker(
            roots,
            enable_metadata=self._enable_metadata,
            require_valid_audio=self._require_valid_audio,
        )
        worker.progress.connect(self._on_progress)
        worker.finished.connect(self._on_scan_finished)
        worker.failed.connect(self._on_scan_failed)
        self._scan_worker = worker
        self._scan_thread = run_in_thread(worker)

    def _cancel_scan(self) -> None:
        if self._scan_worker:
            self._scan_worker.cancel()
            self.summary.setText("Cancelling…")

    def _on_progress(self, done: int, total: int, message: str) -> None:
        if total > 0:
            self.progress.setMaximum(total)
            self.progress.setValue(done)
        else:
            self.progress.setMaximum(0)  # indeterminate
        self.progress.setFormat(f"{message}  (%p%)" if total else message)

    def _on_scan_finished(self, groups: list[DuplicateGroup]) -> None:
        self._set_scanning(False)
        self.model.set_groups(groups)
        self.tree.expandAll()
        total_files = sum(len(g.files) for g in groups)
        reclaim = sum(g.reclaimable_size for g in groups)
        if groups:
            self.summary.setText(
                f"{len(groups)} duplicate groups · {total_files} files · "
                f"up to {_human_size(reclaim)} reclaimable"
            )
            self.delete_btn.setEnabled(True)
        else:
            self.summary.setText("No duplicates found. 🎧")
            self.delete_btn.setEnabled(False)

    def _on_scan_failed(self, msg: str) -> None:
        self._set_scanning(False)
        QMessageBox.critical(self, APP_NAME, f"Scan failed:\n{msg}")

    def _set_scanning(self, scanning: bool) -> None:
        self.scan_btn.setEnabled(not scanning)
        self.cancel_btn.setEnabled(scanning)
        self.add_btn.setEnabled(not scanning)
        self.remove_btn.setEnabled(not scanning)
        if scanning:
            self.eq.start()
        else:
            self.eq.stop()
            self.progress.setMaximum(100)
            self.progress.reset()

    # ---- deletion ----
    def _delete_selected(self) -> None:
        to_delete = self.model.files_to_delete()
        if not to_delete:
            QMessageBox.information(self, APP_NAME, "No files are selected for deletion.")
            return
        try:
            validate_no_full_group_wipe(self.model.groups_as_paths(), set(to_delete))
        except AllFilesInGroupError as exc:
            QMessageBox.warning(self, APP_NAME, str(exc))
            return

        count = len(to_delete)
        confirm = QMessageBox.question(
            self,
            APP_NAME,
            f"Move {count} file(s) to the Trash/Recycle Bin?\n"
            "They can be restored from there.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return

        result = delete_files(to_delete)
        self.summary.setText(f"Moved {len(result.trashed)} file(s) to Trash 🗑️")
        if result.failed:
            QMessageBox.warning(
                self, APP_NAME, f"{len(result.failed)} file(s) could not be deleted."
            )

        # Celebrate with the Trash clip, then refresh the scan when it closes.
        self._play_celebration(after=self._start_scan)

    def _play_celebration(self, after=None) -> None:
        """Play the centered Trash clip; fall back to rescan if no media."""
        from .celebration import CelebrationOverlay

        overlay = CelebrationOverlay(self.centralWidget())
        if not overlay.has_media():
            overlay.deleteLater()
            if after:
                after()
            return
        if after:
            overlay.closed.connect(after)
        self._celebration = overlay  # keep a reference alive
        overlay.play_centered()
