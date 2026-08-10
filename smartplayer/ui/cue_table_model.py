from __future__ import annotations

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QRect
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QStyle

from ..cues.cue import Cue, CueAction, CueState, NextAction


class ProgressDelegate(QStyledItemDelegate):
    def __init__(self, model: CueTableModel, parent=None):
        super().__init__(parent)
        self._model = model

    def paint(self, painter, option, index):
        cue = index.data(CueTableModel.CueRole)
        if cue is None:
            super().paint(painter, option, index)
            return

        state = cue.state
        col = index.column()
        is_running = bool(state & CueState.Running)
        is_active = bool(state & (CueState.Running | CueState.Pause | CueState.PreWait))

        super().paint(painter, option, index)

        # Color tag: 1px border around the entire row
        if cue.color and cue.color != "":
            c = QColor(cue.color)
            pen = painter.pen()
            pen.setColor(c)
            pen.setWidth(1)
            painter.setPen(pen)
            rect = option.rect.adjusted(0, 0, -1, -1)
            painter.drawRect(rect)

        if is_active and col == CueTableModel.COL_REMAINING and is_running and cue.duration > 0:
            progress = min(self._model.current_position / max(cue.duration, 1), 1.0)
            if progress > 0:
                fill_width = max(0, int(option.rect.width() * progress))
                fill_rect = option.rect
                fill_rect.setWidth(fill_width)
                fill_color = QColor("#2E7D32")
                fill_color.setAlpha(70)
                painter.fillRect(fill_rect, fill_color)

            accent = QColor("#4CAF50")
            painter.setPen(accent)
            rect = option.rect.adjusted(0, 0, -1, -1)
            painter.drawRect(rect)


class CueTableModel(QAbstractTableModel):
    COL_INDEX = 0
    COL_NAME = 1
    COL_REMAINING = 2
    COL_DURATION = 3
    COL_NEXT = 4
    COL_OUTPUT = 5
    COL_ACTIONS = 6
    COL_COUNT = 7

    HEADERS = ["Cue", "Name", "Remaining", "Duration", "Next", "Out", ""]

    CueRole = Qt.ItemDataRole.UserRole + 1
    StateRole = Qt.ItemDataRole.UserRole + 2

    def __init__(self, cue_model, parent=None):
        super().__init__(parent)
        self._cue_model = cue_model
        self._cue_model.item_added.connect(self._on_data_changed)
        self._cue_model.item_removed.connect(self._on_data_changed)
        self._cue_model.model_reset.connect(self._on_data_changed)
        self.current_position = 0

    def rowCount(self, parent=QModelIndex()):
        return len(self._cue_model)

    def columnCount(self, parent=QModelIndex()):
        return self.COL_COUNT

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if section < len(self.HEADERS):
                return self.HEADERS[section]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        cue = self._cue_model.cue_at(index.row())
        if cue is None:
            return None

        col = index.column()

        if role == self.CueRole:
            return cue
        if role == self.StateRole:
            return cue.state

        if role == Qt.ItemDataRole.DisplayRole:
            if col == self.COL_INDEX:
                return str(cue.index + 1)
            elif col == self.COL_NAME:
                return cue.name
            elif col == self.COL_REMAINING:
                return self._remaining_time(cue)
            elif col == self.COL_DURATION:
                return self._format_time(cue.duration)
            elif col == self.COL_NEXT:
                return self._next_label(cue)
            elif col == self.COL_OUTPUT:
                return str(cue.output_target + 1)
            elif col == self.COL_ACTIONS:
                state = cue.state
                if state & CueState.Running:
                    return "\u23F9"  # ⏹ stop
                elif state & CueState.Pause:
                    return "\u25B6"  # ▶ resume
                return "\u25B6"  # ▶ play

        if role == Qt.ItemDataRole.ForegroundRole:
            return QColor("#ffffff") if cue.state & CueState.Running else QColor("#cccccc")

        if role == Qt.ItemDataRole.FontRole:
            state = cue.state
            if state & (CueState.Running | CueState.Pause | CueState.PreWait):
                font = QFont()
                font.setBold(True)
                return font
            return None

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (self.COL_INDEX, self.COL_REMAINING, self.COL_DURATION, self.COL_NEXT):
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        if role == Qt.ItemDataRole.ToolTipRole and col == self.COL_NAME:
            return (
                f"{cue.name}\n"
                f"Pre: {cue.pre_wait}s | Post: {cue.post_wait}s\n"
                f"FadeIn: {cue.fadein_duration}ms | FadeOut: {cue.fadeout_duration}ms\n"
                f"{cue.description}"
            ) if cue.description else cue.name

        return None

    def _remaining_time(self, cue: Cue) -> str:
        if cue.state & CueState.Running and cue.duration > 0:
            remaining = max(0, cue.duration - self.current_position)
            return "-" + self._format_time(remaining)
        if cue.state & CueState.Pause and self.current_position >= cue.duration > 0:
            return "00:00:00"
        if cue.duration > 0:
            return self._format_time(cue.duration)
        return "00:00:00"

    def _format_time(self, ms: int) -> str:
        if ms <= 0:
            return "00:00:00"
        total_sec = int(ms / 1000)
        mins, secs = divmod(total_sec, 60)
        hours, mins = divmod(mins, 60)
        return f"{hours:02d}:{mins:02d}:{secs:02d}"

    def _next_label(self, cue: Cue) -> str:
        na = cue.next_action
        labels = {
            NextAction.NextCue: "\u25B6\u25B6",
            NextAction.PreviousCue: "\u25C0\u25C0",
            NextAction.StopEndOut: "\u25A0",
            NextAction.PauseKeepLast: "\u23F8",
            NextAction.Loop: "\u21BA",
        }
        return labels.get(na, "")

    def _on_data_changed(self, *args):
        self.endResetModel()

    def cue_at_row(self, row: int) -> Cue | None:
        return self._cue_model.cue_at(row)

    def refresh(self):
        self.endResetModel()

    def refresh_row(self, row: int):
        if 0 <= row < len(self._cue_model):
            self.dataChanged.emit(
                self.index(row, 0),
                self.index(row, self.COL_COUNT - 1)
            )

    def refresh_row_cell(self, row: int, col: int):
        if 0 <= row < len(self._cue_model):
            idx = self.index(row, col)
            self.dataChanged.emit(idx, idx)

    def all_rows(self):
        self.dataChanged.emit(
            self.index(0, 0),
            self.index(self.rowCount() - 1, self.COL_COUNT - 1)
        )
