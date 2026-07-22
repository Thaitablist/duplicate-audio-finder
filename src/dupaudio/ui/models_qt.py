"""A QAbstractItemModel exposing DuplicateGroups + files as a checkable tree."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt
from PySide6.QtGui import QColor

from ..models import DuplicateGroup, MatchType
from . import theme

COLUMNS = ["File / Group", "Bitrate", "Size", "Folder"]
KEEP_COLOR = theme.KEEP        # neon green — the file being kept
DELETE_COLOR = theme.DELETE    # neon pink — marked for deletion
META_COLOR = theme.META        # amber — metadata-match group header


def _human_size(n: int) -> str:
    val = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if val < 1024 or unit == "TB":
            return f"{val:.0f} {unit}" if unit == "B" else f"{val:.1f} {unit}"
        val /= 1024
    return f"{n} B"


class DuplicateTreeModel(QAbstractItemModel):
    """Two-level tree: groups at the top, their files as children.

    Files carry a checkbox in column 0. The keep-file starts unchecked; every
    other file starts checked (marked for deletion).
    """

    def __init__(self, groups: list[DuplicateGroup] | None = None) -> None:
        super().__init__()
        self._groups: list[DuplicateGroup] = groups or []
        # path -> checked(True = will be deleted)
        self._checked: dict[Path, bool] = {}
        self._init_check_state()

    # ---- public API ------------------------------------------------------
    def set_groups(self, groups: list[DuplicateGroup]) -> None:
        self.beginResetModel()
        self._groups = groups
        self._checked.clear()
        self._init_check_state()
        self.endResetModel()

    def files_to_delete(self) -> list[Path]:
        return [p for p, checked in self._checked.items() if checked]

    def groups_as_paths(self) -> list[list[Path]]:
        return [[f.path for f in g.files] for g in self._groups]

    def _init_check_state(self) -> None:
        for g in self._groups:
            for f in g.files:
                # Kept file unchecked; others checked for deletion.
                self._checked[f.path] = f.path != g.keep_path

    # ---- tree structure --------------------------------------------------
    # internalId encoding (must be non-negative — Qt stores it unsigned):
    #   0            -> a top-level GROUP row
    #   group_idx+1  -> a FILE row whose parent is groups[group_idx]
    def index(self, row, column, parent=QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        if not parent.isValid():
            return self.createIndex(row, column, 0)  # group row
        return self.createIndex(row, column, parent.row() + 1)  # file row

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        gid = index.internalId()
        if gid == 0:
            return QModelIndex()  # group has no parent
        return self.createIndex(gid - 1, 0, 0)

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return len(self._groups)
        if parent.internalId() == 0:
            return len(self._groups[parent.row()].files)
        return 0

    def columnCount(self, parent=QModelIndex()):
        return len(COLUMNS)

    # ---- data ------------------------------------------------------------
    def _is_group(self, index) -> bool:
        return index.internalId() == 0

    def _group_of_file(self, index) -> DuplicateGroup:
        return self._groups[index.internalId() - 1]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        col = index.column()

        if self._is_group(index):
            g = self._groups[index.row()]
            if role == Qt.DisplayRole and col == 0:
                label = "Exact copy" if g.match_type == MatchType.EXACT else "Same tags"
                return f"[{label}] {len(g.files)} files · save {_human_size(g.reclaimable_size)}"
            if role == Qt.ForegroundRole and col == 0:
                if g.match_type == MatchType.METADATA:
                    return META_COLOR  # amber: be careful
                return QColor(theme.NEON_CYAN)
            return None

        # file row
        g = self._group_of_file(index)
        f = g.files[index.row()]
        is_keep = f.path == g.keep_path

        if role == Qt.CheckStateRole and col == 0:
            return Qt.Checked if self._checked.get(f.path) else Qt.Unchecked
        if role == Qt.DisplayRole:
            if col == 0:
                return f.name + ("  (keep)" if is_keep else "")
            if col == 1:
                return f"{f.bitrate // 1000} kbps" if f.bitrate else "—"
            if col == 2:
                return _human_size(f.size)
            if col == 3:
                return str(f.path.parent)
        if role == Qt.ForegroundRole and col == 0:
            return KEEP_COLOR if is_keep else DELETE_COLOR if self._checked.get(f.path) else None
        if role == Qt.ToolTipRole:
            return str(f.path)
        return None

    def setData(self, index, value, role=Qt.EditRole):
        if role == Qt.CheckStateRole and index.isValid() and not self._is_group(index):
            g = self._group_of_file(index)
            f = g.files[index.row()]
            self._checked[f.path] = Qt.CheckState(value) == Qt.Checked
            self.dataChanged.emit(index, index, [Qt.CheckStateRole, Qt.ForegroundRole])
            return True
        return False

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        base = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if not self._is_group(index) and index.column() == 0:
            base |= Qt.ItemIsUserCheckable
        return base

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return COLUMNS[section]
        return None
