from __future__ import annotations

from PySide6.QtCore import Qt, QAbstractListModel, QModelIndex
from ..cues.cue import Cue, CueAction


class CueListModel(QAbstractListModel):
    NameRole = Qt.ItemDataRole.UserRole + 1
    DurationRole = Qt.ItemDataRole.UserRole + 2
    PreWaitRole = Qt.ItemDataRole.UserRole + 3
    StateRole = Qt.ItemDataRole.UserRole + 4
    CueRole = Qt.ItemDataRole.UserRole + 5
    IndexRole = Qt.ItemDataRole.UserRole + 6

    def __init__(self, cue_model, parent=None):
        super().__init__(parent)
        self._cue_model = cue_model
        self._cue_model.item_added.connect(self._on_cues_changed)
        self._cue_model.item_removed.connect(self._on_cues_changed)
        self._cue_model.model_reset.connect(self._on_cues_changed)

    def rowCount(self, parent=QModelIndex()):
        return len(self._cue_model)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        cue = self._cue_model.cue_at(index.row())
        if cue is None:
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            return cue.name
        elif role == self.NameRole:
            return cue.name
        elif role == self.DurationRole:
            mins, secs = divmod(cue.duration / 1000, 60) if cue.duration else (0, 0)
            return f"{int(mins):02d}:{int(secs):02d}"
        elif role == self.PreWaitRole:
            return f"{cue.pre_wait:.1f}s"
        elif role == self.StateRole:
            return cue.state
        elif role == self.CueRole:
            return cue
        elif role == self.IndexRole:
            return cue.index + 1
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        return None

    def _on_cues_changed(self, *args):
        self.endResetModel()

    def cue_at_row(self, row: int) -> Cue | None:
        return self._cue_model.cue_at(row)

    def add_cue(self, cue: Cue):
        self._cue_model.add(cue)
        self.endResetModel()

    def remove_cue(self, row: int):
        cue = self._cue_model.cue_at(row)
        if cue:
            self._cue_model.remove(cue.id)
            self.endResetModel()

    def move_cue(self, from_row: int, to_row: int):
        cue = self._cue_model.cue_at(from_row)
        if cue:
            self._cue_model.move(cue.id, to_row)
            self.endResetModel()

    def clear(self):
        self._cue_model.clear()
        self.endResetModel()

    def cues(self) -> list[Cue]:
        return self._cue_model.cues()

    def stop_all(self):
        self._cue_model.stop_all()
