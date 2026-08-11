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
        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)

        # Suppress default selection background completely
        opt = QStyleOptionViewItem(option)
        opt.state &= ~QStyle.StateFlag.State_Selected
        if is_selected:
            opt.backgroundBrush = QColor(0, 0, 0, 0)

        # Running: semi-transparent white
        if is_running:
            painter.fillRect(opt.rect, QColor(255, 255, 255, 20))

        super().paint(painter, opt, index)

        # Selected: blue outlined border around entire row (edges only)
        if is_selected:
            c = QColor("#2196F3")
            pen = painter.pen()
            pen.setColor(c)
            pen.setWidth(2)
            painter.setPen(pen)
            r = opt.rect.adjusted(1, 1, -1, -1)
            if col == self._model.COL_INDEX:
                painter.drawLine(r.topLeft(), r.bottomLeft())
                painter.drawLine(r.topLeft(), r.topRight())
                painter.drawLine(r.bottomLeft(), r.bottomRight())
            elif col == self._model.COL_ACTIONS:
                painter.drawLine(r.topRight(), r.bottomRight())
                painter.drawLine(r.topLeft(), r.topRight())
                painter.drawLine(r.bottomLeft(), r.bottomRight())
            else:
                painter.drawLine(r.topLeft(), r.topRight())
                painter.drawLine(r.bottomLeft(), r.bottomRight())

        # Color tag: border around the entire row (edges only)
        if cue.color and cue.color != "":
            c = QColor(cue.color)
            pen = painter.pen()
            pen.setColor(c)
            pen.setWidth(1)
            painter.setPen(pen)
            r = opt.rect.adjusted(0, 0, 0, -1)
            if col == self._model.COL_INDEX:
                painter.drawLine(r.topLeft(), r.bottomLeft())
                painter.drawLine(r.topLeft(), r.topRight())
                painter.drawLine(r.bottomLeft(), r.bottomRight())
            elif col == self._model.COL_ACTIONS:
                painter.drawLine(r.topRight(), r.bottomRight())
                painter.drawLine(r.topLeft(), r.topRight())
                painter.drawLine(r.bottomLeft(), r.bottomRight())
            else:
                painter.drawLine(r.topLeft(), r.topRight())
                painter.drawLine(r.bottomLeft(), r.bottomRight())

        if is_active and col == CueTableModel.COL_REMAINING and is_running and cue.duration > 0:
            # Get position from the cue's own player
            pos = 0
            if cue._type_ == "MediaCue":
                try:
                    pos = getattr(cue, 'currentPositionMs', 0)
                except Exception:
                    pass
            progress = min(pos / max(cue.duration, 1), 1.0)
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
    COL_SIZE = 4
    COL_RESOLUTION = 5
    COL_CODEC = 6
    COL_EXTENSION = 7
    COL_NEXT = 8
    COL_OUTPUT = 9
    COL_ACTIONS = 10
    COL_COUNT = 11

    HEADERS = ["Cue", "Name", "Remaining", "Duration", "Size", "Resolution", "Codec", "Ext", "Next", "Output", "Actions"]

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
            elif col == self.COL_SIZE:
                return self._format_size(cue)
            elif col == self.COL_RESOLUTION:
                return self._format_resolution(cue)
            elif col == self.COL_CODEC:
                return self._format_codec(cue)
            elif col == self.COL_EXTENSION:
                return self._format_extension(cue)
            elif col == self.COL_NEXT:
                return self._next_label(cue)
            elif col == self.COL_OUTPUT:
                return str(cue.output_target + 1)
            elif col == self.COL_ACTIONS:
                return ""

        if role == Qt.ItemDataRole.ForegroundRole:
            if cue.state & (CueState.Running | CueState.Pause):
                return QColor("#ffffff")
            return QColor("#cccccc")

        if role == Qt.ItemDataRole.FontRole:
            return None

        if role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (self.COL_INDEX, self.COL_REMAINING, self.COL_DURATION, self.COL_NEXT, self.COL_OUTPUT):
                return Qt.AlignmentFlag.AlignCenter
            if col == self.COL_ACTIONS:
                return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
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
        from ..cues.media_cue import MediaCue
        pos = 0
        if isinstance(cue, MediaCue):
            pos = getattr(cue, 'currentPositionMs', 0) or 0
        if cue.state & CueState.Running and cue.duration > 0:
            remaining = max(0, cue.duration - pos)
            return "-" + self._format_time(remaining)
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

    def _format_size(self, cue: Cue) -> str:
        from ..cues.media_cue import MediaCue
        if isinstance(cue, MediaCue) and cue.media.file_size > 0:
            size_mb = cue.media.file_size / (1024 * 1024)
            if size_mb >= 1000:
                return f"{size_mb/1024:.1f} GB"
            return f"{size_mb:.1f} MB"
        return "-"

    def _format_resolution(self, cue: Cue) -> str:
        from ..cues.media_cue import MediaCue
        if isinstance(cue, MediaCue) and cue.media.resolution:
            return cue.media.resolution
        return "-"

    def _format_codec(self, cue: Cue) -> str:
        from ..cues.media_cue import MediaCue
        if isinstance(cue, MediaCue) and cue.media.codec:
            return cue.media.codec
        return "-"

    def _format_extension(self, cue: Cue) -> str:
        from ..cues.media_cue import MediaCue
        import os
        if isinstance(cue, MediaCue) and cue.media.uri:
            ext = os.path.splitext(cue.media.uri)[1].lower()
            return ext if ext else "-"
        return "-"

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
        self.beginResetModel()
        self.endResetModel()

    def cue_at_row(self, row: int) -> Cue | None:
        return self._cue_model.cue_at(row)

    def refresh(self):
        self.beginResetModel()
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
