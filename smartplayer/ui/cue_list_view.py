from __future__ import annotations

import os
from functools import partial

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView, QHeaderView,
    QPushButton, QLabel, QFileDialog, QSlider, QFrame,
    QSplitter, QSizePolicy, QAbstractItemView
)
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtGui import QKeySequence, QShortcut, QColor

from ..cues.cue import Cue, CueAction, CueState, NextAction
from ..cues.media_cue import MediaCue
from ..cues.cue_factory import CueFactory
from .cue_table_model import CueTableModel, ProgressDelegate
from .video_output_manager import VideoOutputManager
from .undo_stack import UndoStack, LambdaCommand
from .cue_editor_panel import CueEditorPanel

MEDIA_FILTER = (
    "All Media (*.wav *.mp3 *.ogg *.flac *.aac *.m4a *.wma "
    "*.mp4 *.avi *.mkv *.mov *.wmv *.webm *.m4v *.mpg *.mpeg *.flv *.3gp);;"
    "Audio (*.wav *.mp3 *.ogg *.flac *.aac *.m4a *.wma);;"
    "Video (*.mp4 *.avi *.mkv *.mov *.wmv *.webm *.m4v *.mpg *.mpeg *.flv *.3gp);;"
    "All Files (*.*)"
)

VIDEO_EXTENSIONS = {
    ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".webm",
    ".m4v", ".mpg", ".mpeg", ".flv", ".3gp"
}

STYLE_PRIMARY = "QPushButton { background-color: #4CAF50; color: #fff; border: none; border-radius: 3px; padding: 5px 16px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #43A047; }"
STYLE_DANGER = "QPushButton { background-color: #E53935; color: #fff; border: none; border-radius: 3px; padding: 5px 16px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #C62828; }"
STYLE_WARN = "QPushButton { background-color: #FB8C00; color: #fff; border: none; border-radius: 3px; padding: 5px 16px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #EF6C00; }"
STYLE_INFO = "QPushButton { background-color: #1E88E5; color: #fff; border: none; border-radius: 3px; padding: 5px 12px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #1565C0; }"
STYLE_PURPLE = "QPushButton { background-color: #8E24AA; color: #fff; border: none; border-radius: 3px; padding: 5px 12px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #6A1B9A; }"
STYLE_DARK = "QPushButton { background-color: #424242; color: #ccc; border: none; border-radius: 3px; padding: 5px 12px; font-size: 12px; } QPushButton:hover { background-color: #616161; color: #fff; }"
STYLE_DISPLAY_ON = "QPushButton { background-color: #1B5E20; color: #A5D6A7; border: 1px solid #2E7D32; border-radius: 3px; padding: 5px 12px; font-size: 12px; font-weight: bold; } QPushButton:hover { background-color: #2E7D32; }"
STYLE_DISPLAY_OFF = "QPushButton { background-color: #424242; color: #888; border: 1px solid #555; border-radius: 3px; padding: 5px 12px; font-size: 12px; } QPushButton:hover { background-color: #555; }"


class CueListView(QWidget):
    def __init__(self, cue_model, video_manager: VideoOutputManager, undo_stack: UndoStack, parent=None):
        super().__init__(parent)
        self._cue_model = cue_model
        self._video_manager = video_manager
        self._undo_stack = undo_stack
        self._table_model = CueTableModel(cue_model)
        self._standby_index = 0
        self._pending_go = False
        self._current_cue: Cue | None = None
        self._current_row = -1
        self._display_enabled = True
        self._progress_timer = QTimer()
        self._progress_timer.setInterval(100)
        self._progress_timer.timeout.connect(self._update_progress)
        self._build_ui()
        self._setup_shortcuts()

    @property
    def video_manager(self) -> VideoOutputManager:
        return self._video_manager

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        header = QHBoxLayout()
        header.setSpacing(4)

        self._go_btn = QPushButton("GO")
        self._go_btn.setMinimumHeight(28)
        self._go_btn.setMinimumWidth(50)
        self._go_btn.setStyleSheet(STYLE_PRIMARY)
        self._go_btn.clicked.connect(self._on_go)
        header.addWidget(self._go_btn)

        self._stop_btn = QPushButton("STOP")
        self._stop_btn.setMinimumHeight(28)
        self._stop_btn.setMinimumWidth(50)
        self._stop_btn.setStyleSheet(STYLE_DANGER)
        self._stop_btn.clicked.connect(self._on_stop)
        header.addWidget(self._stop_btn)

        self._pause_btn = QPushButton("PAUSE")
        self._pause_btn.setMinimumHeight(28)
        self._pause_btn.setMinimumWidth(55)
        self._pause_btn.setStyleSheet(STYLE_WARN)
        self._pause_btn.clicked.connect(self._on_pause)
        header.addWidget(self._pause_btn)

        header.addStretch()

        self._display_btn = QPushButton("DISPLAY ON")
        self._display_btn.setMinimumHeight(28)
        self._display_btn.setStyleSheet(STYLE_DISPLAY_ON)
        self._display_btn.clicked.connect(self._toggle_display)
        if self._video_manager.has_external_display:
            self._display_btn.setText("EXT DISPLAY ON")
        header.addWidget(self._display_btn)

        self._pattern_btn = QPushButton("PATTERN OFF")
        self._pattern_btn.setMinimumHeight(28)
        self._pattern_btn.setStyleSheet(STYLE_DARK)
        self._pattern_btn.clicked.connect(self._toggle_pattern)
        header.addWidget(self._pattern_btn)

        self._add_btn = QPushButton("Add Media")
        self._add_btn.setMinimumHeight(28)
        self._add_btn.setStyleSheet(STYLE_DARK)
        self._add_btn.clicked.connect(self._on_add_media)
        header.addWidget(self._add_btn)

        self._remove_btn = QPushButton("Remove")
        self._remove_btn.setMinimumHeight(28)
        self._remove_btn.setStyleSheet(STYLE_DARK)
        self._remove_btn.clicked.connect(self._on_remove)
        header.addWidget(self._remove_btn)

        self._stop_all_btn = QPushButton("Stop All")
        self._stop_all_btn.setMinimumHeight(28)
        self._stop_all_btn.setStyleSheet(STYLE_DARK)
        self._stop_all_btn.clicked.connect(self._on_stop_all)
        header.addWidget(self._stop_all_btn)

        layout.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self._table = QTableView()
        self._table.setModel(self._table_model)
        self._table.setItemDelegate(ProgressDelegate(self._table_model))
        self._table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(False)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(30)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)
        self._table.setColumnWidth(CueTableModel.COL_INDEX, 32)
        self._table.setColumnWidth(CueTableModel.COL_NAME, 120)
        self._table.setColumnWidth(CueTableModel.COL_REMAINING, 80)
        self._table.setColumnWidth(CueTableModel.COL_DURATION, 75)
        self._table.setColumnWidth(CueTableModel.COL_SIZE, 55)
        self._table.setColumnWidth(CueTableModel.COL_RESOLUTION, 95)
        self._table.setColumnWidth(CueTableModel.COL_CODEC, 130)
        self._table.setColumnWidth(CueTableModel.COL_EXTENSION, 36)
        self._table.setColumnWidth(CueTableModel.COL_NEXT, 34)
        self._table.setColumnWidth(CueTableModel.COL_OUTPUT, 45)
        self._table.setColumnWidth(CueTableModel.COL_ACTIONS, 92)
        self._table.clicked.connect(self._on_cue_clicked)
        self._table.doubleClicked.connect(self._on_cue_double_clicked)
        self._table.resizeColumnsToContents()
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table_model.rowsInserted.connect(self._on_rows_changed)
        self._table_model.rowsRemoved.connect(self._on_rows_changed)
        self._table_model.modelReset.connect(self._on_rows_changed)
        self._table.setStyleSheet(
            "QTableView { border: 1px solid #3a3a3a; }"
            "QTableView::item { padding: 2px 6px; }"
            "QTableView::item:selected { background-color: transparent; color: #fff; }"
        )
        left_layout.addWidget(self._table)

        splitter.addWidget(left_widget)

        self._editor_panel = CueEditorPanel(self._undo_stack)
        self._editor_panel.set_refresh_callback(lambda: self._table_model.refresh())
        splitter.addWidget(self._editor_panel)

        splitter.setSizes([600, 320])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)

        layout.addWidget(splitter, 1)

        controls = QHBoxLayout()
        controls.setSpacing(4)

        layout.addLayout(controls)

        vol_bar = QHBoxLayout()
        vol_bar.setSpacing(6)
        vol_label = QLabel("VOL")
        vol_label.setStyleSheet("color: #777; font-size: 11px;")
        vol_bar.addWidget(vol_label)
        self._volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(80)
        self._volume_slider.setMaximumWidth(100)
        self._volume_slider.valueChanged.connect(self._on_volume_changed)
        vol_bar.addWidget(self._volume_slider)
        self._vol_label = QLabel("80%")
        self._vol_label.setStyleSheet("color: #777; font-size: 11px;")
        self._vol_label.setFixedWidth(30)
        vol_bar.addWidget(self._vol_label)
        vol_bar.addStretch()
        layout.addLayout(vol_bar)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Z), self, self._on_undo)
        QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Y), self, self._on_redo)
        QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Modifier.SHIFT | Qt.Key.Key_Z), self, self._on_redo)
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, self._on_go)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self._on_stop)

    def _is_video_file(self, filepath: str) -> bool:
        return os.path.splitext(filepath)[1].lower() in VIDEO_EXTENSIONS

    def _toggle_display(self):
        self._display_enabled = not self._display_enabled
        if self._display_enabled:
            self._display_btn.setStyleSheet(STYLE_DISPLAY_ON)
            if self._video_manager.has_external_display:
                self._display_btn.setText("EXT DISPLAY ON")
                self._video_manager.show_black_screen()
            else:
                self._display_btn.setText("DISPLAY ON")
        else:
            self._display_btn.setStyleSheet(STYLE_DISPLAY_OFF)
            self._display_btn.setText("DISPLAY OFF")
            self._video_manager.force_hide()

    def _toggle_pattern(self):
        if self._video_manager.is_pattern_playing():
            self._video_manager.stop_pattern()
            self._update_pattern_btn(False)
            self._video_manager.show_black_screen()
        elif self._video_manager.has_test_pattern():
            self._video_manager.show_last_pattern()
            self._update_pattern_btn(True)

    def _update_pattern_btn(self, playing: bool):
        if not self._video_manager.has_test_pattern():
            self._pattern_btn.setText("NO PATTERN")
            self._pattern_btn.setStyleSheet(STYLE_DISPLAY_OFF)
            self._pattern_btn.setEnabled(False)
        elif playing:
            self._pattern_btn.setText("PATTERN ON")
            self._pattern_btn.setStyleSheet(STYLE_DISPLAY_ON)
            self._pattern_btn.setEnabled(True)
        else:
            self._pattern_btn.setText("PATTERN OFF")
            self._pattern_btn.setStyleSheet(STYLE_DARK)
            self._pattern_btn.setEnabled(True)

    def refresh_pattern_btn(self):
        self._update_pattern_btn(self._video_manager.is_pattern_playing())

    def _refresh_action_buttons(self):
        from PySide6.QtCore import QTimer
        QTimer.singleShot(200, self._do_refresh_buttons)

    def _on_rows_changed(self, *args):
        self._refresh_action_buttons()

    def _do_refresh_buttons(self):
        play_style   = "QPushButton { background-color: #4CAF50; color: #fff; border: none; border-radius: 2px; padding: 0px 3px; font-size: 11px; font-weight: bold; } QPushButton:hover { background-color: #43A047; }"
        stop_style   = "QPushButton { background-color: #E53935; color: #fff; border: none; border-radius: 2px; padding: 0px 3px; font-size: 11px; font-weight: bold; } QPushButton:hover { background-color: #C62828; }"
        pause_style  = "QPushButton { background-color: #FB8C00; color: #fff; border: none; border-radius: 2px; padding: 0px 3px; font-size: 11px; font-weight: bold; } QPushButton:hover { background-color: #EF6C00; }"

        for row in range(self._table_model.rowCount()):
            self._table.setIndexWidget(self._table_model.index(row, CueTableModel.COL_ACTIONS), None)

        for row in range(self._table_model.rowCount()):
            cue = self._cue_model.cue_at(row)
            if cue is None:
                continue

            container = QWidget()
            container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            container.setStyleSheet("background: transparent; border: none;")
            container.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            layout = QHBoxLayout(container)
            layout.setContentsMargins(2, 0, 0, 0)
            layout.setSpacing(2)
            layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            b_play = QPushButton("\u25B6")
            b_play.setFixedSize(20, 20)
            b_play.setStyleSheet(play_style)
            b_play.clicked.connect(partial(self._play_cue_at, row))
            layout.addWidget(b_play)

            b_stop = QPushButton("\u25A0")
            b_stop.setFixedSize(20, 20)
            b_stop.setStyleSheet(stop_style)
            b_stop.clicked.connect(partial(self._stop_cue_at, row))
            layout.addWidget(b_stop)

            b_pause = QPushButton("||")
            b_pause.setFixedSize(20, 20)
            b_pause.setStyleSheet(pause_style)
            b_pause.setToolTip("Pause")
            b_pause.clicked.connect(partial(self._pause_cue_at, row))
            layout.addWidget(b_pause)

            # B toggle: purple = fade from black ON, gray = fade OFF (frame 1)
            has_fade = cue.fadein_duration > 0
            b_on  = "QPushButton { background-color: #7B1FA2; color: #fff; border: 1px solid #9C27B0; border-radius: 3px; padding: 0px 3px; font-size: 10px; font-weight: bold; } QPushButton:hover { background-color: #8E24AA; }"
            b_off = "QPushButton { background-color: #333; color: #555; border: 1px solid #444; border-radius: 3px; padding: 0px 3px; font-size: 10px; } QPushButton:hover { background-color: #555; color: #aaa; }"
            b_fade = QPushButton("B")
            b_fade.setFixedSize(20, 20)
            b_fade.setStyleSheet(b_on if has_fade else b_off)
            b_fade.setToolTip("Fade from Black: ON" if has_fade else "Fade from Black: OFF (instant)")
            b_fade.clicked.connect(partial(self._toggle_cue_fade, row))
            layout.addWidget(b_fade)

            self._table.setIndexWidget(self._table_model.index(row, CueTableModel.COL_ACTIONS), container)

        # Force row heights after all widgets are set
        for r in range(self._table_model.rowCount()):
            self._table.setRowHeight(r, 30)

    def _play_cue_at(self, row: int):
        cue = self._cue_model.cue_at(row)
        if cue:
            if cue.state & CueState.Pause:
                cue.execute(CueAction.Resume)
            else:
                self._launch_with_transition(row)
            self._do_refresh_buttons()
    def _probe_media_info(self, cue: MediaCue):
        try:
            from pymediainfo import MediaInfo
            path = cue.media.uri
            if not os.path.exists(path):
                return
            mi = MediaInfo.parse(path)
            container_format = ""
            video_codec = ""
            audio_codec = ""
            has_video = False
            is_image = False
            for track in mi.tracks:
                if track.track_type == 'General':
                    container_format = track.format or ""
                elif track.track_type == 'Video':
                    has_video = True
                    w = track.width or 0
                    h = track.height or 0
                    fps = track.frame_rate or 0
                    video_codec = track.codec_id or track.format or ""
                    if isinstance(fps, str):
                        try: fps = float(fps)
                        except: fps = 0
                    if w > 0 and h > 0 and w < 10000 and h < 10000:
                        if 0 < fps < 120:
                            cue.media.resolution = f"{w}x{h}@{fps:.0f}fps"
                        elif fps == 0 and w > 0:
                            cue.media.resolution = f"{w}x{h}"
                        else:
                            cue.media.resolution = f"{w}x{h}"
                elif track.track_type == 'Audio':
                    has_audio = True
                    fmt = track.format or ""
                    info = track.codec_id_info or ""
                    sr = track.sampling_rate or 0
                    ch = getattr(track, 'channel_s', 0) or getattr(track, 'channels', 0) or 0
                    if info and info != fmt:
                        audio_codec = f"{info}"
                    elif fmt:
                        audio_codec = fmt
                    if sr > 0:
                        audio_codec += f" {int(sr/1000)}kHz"
                    if ch > 0:
                        audio_codec += f" {ch}ch"
                elif track.track_type == 'Image':
                    is_image = True
                    fmt = track.format or ""
                    if fmt:
                        cue.media.codec = fmt.upper()
            if is_image:
                pass
            elif has_video:
                prefix = f"{container_format} " if container_format else ""
                codec_str = f"{prefix}{video_codec}"
                if audio_codec:
                    cue.media.codec = f"{codec_str} / {audio_codec}"
                else:
                    cue.media.codec = f"{codec_str} / No Audio"
            if hasattr(mi, 'close'):
                mi.close()
        except Exception:
            pass

    def _stop_cue_at(self, row: int):
        cue = self._cue_model.cue_at(row)
        if cue: cue.execute(CueAction.Stop); self._table_model.refresh_row(row); self._do_refresh_buttons()

    def _pause_cue_at(self, row: int):
        cue = self._cue_model.cue_at(row)
        if cue: cue.execute(CueAction.Pause); self._table_model.refresh_row(row); self._do_refresh_buttons()

    def _toggle_cue_fade(self, row: int):
        cue = self._cue_model.cue_at(row)
        if cue is None:
            return
        if cue.fadein_duration > 0:
            cue.fadein_duration = 0
        else:
            cue.fadein_duration = 3000
        self._do_refresh_buttons()

    def _on_undo(self):
        text = self._undo_stack.undo()
        self._table_model.refresh()

    def _on_redo(self):
        text = self._undo_stack.redo()
        self._table_model.refresh()

    def _on_go(self):
        if self._pending_go:
            return
        cue = self._cue_model.cue_at(self._standby_index)
        if cue is None:
            return
        self._pending_go = True

        if self._current_cue and self._current_cue.state & CueState.IsRunning:
            if self._current_cue.priority <= cue.priority:
                self._current_cue.execute(CueAction.Stop)
            else:
                self._pending_go = False
                return

        self._play_cue(cue, self._standby_index)
        self._pending_go = False

    def _on_cue_ended(self):
        if self._current_cue is not None:
            try:
                self._current_cue.end.disconnect(self._on_cue_ended)
                self._current_cue.changed.disconnect(self._on_cue_changed)
            except Exception:
                pass

        old_row = self._current_row
        old_cue = self._current_cue

        if old_cue and old_cue.next_action == NextAction.PauseKeepLast:
            self._progress_timer.stop()
            self._table_model.current_position = old_cue.duration if old_cue.duration > 0 else 0
            self._table_model.refresh_row(old_row)
            self._table.viewport().update()
            return

        self._progress_timer.stop()
        self._table_model.current_position = 0

        if not self._video_manager.has_external_display:
            self._video_manager.hide_video()

        self._current_cue = None
        self._current_row = -1

        if old_row >= 0:
            self._table_model.refresh_row(old_row)
        self._table_model.refresh_row(self._standby_index)

        if old_cue and old_cue.next_action == NextAction.Loop:
            self._current_cue = old_cue
            self._current_row = old_row
            old_cue.execute(CueAction.Start)
        elif old_cue and old_cue.next_action == NextAction.NextCue:
            self._advance_standby()
            self._on_go()
        elif old_cue and old_cue.next_action == NextAction.PreviousCue:
            self._standby_index = max(0, self._standby_index - 1)
            self._on_go()

    def _on_cue_changed(self, name, value):
        if name == "state" and self._current_row >= 0:
            self._table_model.refresh_row(self._current_row)

    def _update_progress(self):
        has_running = False
        for row in range(len(self._cue_model)):
            cue = self._cue_model.cue_at(row)
            if cue is None:
                continue
            if cue.state & CueState.Running and isinstance(cue, MediaCue):
                has_running = True
                self._table_model.refresh_row_cell(row, CueTableModel.COL_REMAINING)
        if has_running:
            self._table.viewport().update()
        else:
            self._progress_timer.stop()

    def _on_stop(self):
        cue = self._cue_model.cue_at(self._standby_index)
        if cue:
            try:
                cue.end.disconnect(self._on_cue_ended)
            except Exception:
                pass
            try:
                cue.next.disconnect(self._on_go)
            except Exception:
                pass
            cue.execute(CueAction.Stop)
            self._progress_timer.stop()
            self._table_model.current_position = 0
            if not self._video_manager.has_external_display:
                self._video_manager.hide_video()
            if cue is self._current_cue:
                self._current_cue = None
                self._current_row = -1
            self._table_model.refresh_row(self._standby_index)

    def _on_pause(self):
        cue = self._cue_model.cue_at(self._standby_index)
        if cue:
            if cue.state == CueState.Pause:
                cue.execute(CueAction.Resume)
                self._pause_btn.setText("PAUSE")
                self._pause_btn.setStyleSheet(STYLE_WARN)
                self._progress_timer.start()
            else:
                cue.execute(CueAction.Pause)
                self._pause_btn.setText("RESUME")
                self._pause_btn.setStyleSheet(STYLE_INFO)
                self._progress_timer.stop()
            self._table_model.refresh_row(self._standby_index)

    def _on_stop_all(self):
        self._cue_model.stop_all()
        self._progress_timer.stop()
        self._table_model.current_position = 0
        if not self._video_manager.has_external_display:
            self._video_manager.hide_video()
        self._current_cue = None
        self._current_row = -1
        self._table_model.refresh()

    def _on_add_media(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Media Files", "", MEDIA_FILTER
        )
        if not files:
            return

        for filepath in files:
            cue = CueFactory.create("MediaCue")
            cue.name = os.path.basename(filepath)
            cue.media.uri = filepath
            # Set file info
            if os.path.exists(filepath):
                cue.media.file_size = os.path.getsize(filepath)
            self._cue_model.add(cue)
            self._undo_stack.push(LambdaCommand(
                f"Add {cue.name}",
                undo_fn=lambda cid=cue.id: self._cue_model.remove(cid),
                redo_fn=lambda data=cue.to_dict(), idx=len(self._cue_model)-1: self._redo_add(data, idx)
            ))

            # Probe resolution immediately
            self._probe_media_info(cue)

            temp_player = QMediaPlayer()
            temp_player.setSource(QUrl.fromLocalFile(filepath))
            def _make_loaded_handler(p, c):
                def _on_loaded(status):
                    if status == QMediaPlayer.MediaStatus.LoadedMedia:
                        c.duration = p.duration()
                        try:
                            md = p.metaData()
                            # Try to get resolution
                            for key in md.keys():
                                if 'frame' in str(key).lower() or 'width' in str(key).lower():
                                    pass  # QMediaMetaData doesn't expose these easily
                        except Exception:
                            pass
                        self._probe_media_info(c)
                        self._table_model.refresh()
                        p.deleteLater()
                return _on_loaded
            temp_player.mediaStatusChanged.connect(
                _make_loaded_handler(temp_player, cue)
            )

        self._table_model.refresh()

    def _redo_add(self, data: dict, index: int):
        cue = CueFactory.from_dict(data)
        self._cue_model.add(cue, index)

    def _on_remove(self):
        indexes = self._table.selectionModel().selectedRows()
        if not indexes:
            return
        row = indexes[0].row()
        cue = self._cue_model.cue_at(row)
        if cue is None:
            return

        cue_data = cue.to_dict()
        cue_index = cue.index

        if cue is self._current_cue:
            cue.execute(CueAction.Stop)
            self._progress_timer.stop()
            self._table_model.current_position = 0
            if not self._video_manager.has_external_display:
                self._video_manager.hide_video()
            self._current_cue = None
            self._current_row = -1

        self._cue_model.remove(cue.id)
        self._undo_stack.push(LambdaCommand(
            f"Remove {cue.name}",
            undo_fn=lambda data=cue_data, idx=cue_index: self._redo_add(data, idx),
            redo_fn=lambda cid=cue.id: self._cue_model.remove(cid)
        ))

        self._table_model.refresh()
        if self._standby_index >= len(self._cue_model):
            self._standby_index = max(0, len(self._cue_model) - 1)
        self._editor_panel.set_cue(None)

    def _on_cue_clicked(self, index):
        row = index.row()
        col = index.column()
        cue = self._cue_model.cue_at(row)
        if cue is None:
            return

        if col == CueTableModel.COL_ACTIONS:
            return

        # Single click: select only (no launch)
        self._standby_index = row
        self._table.selectRow(row)
        self._editor_panel.set_cue(cue)

    def _on_cue_double_clicked(self, index):
        col = index.column()
        if col != CueTableModel.COL_INDEX:
            return
        row = index.row()
        self._launch_with_transition(row)

    def _launch_with_transition(self, row: int):
        cue = self._cue_model.cue_at(row)
        if cue is None:
            return
        # Route video first
        if isinstance(cue, MediaCue) and self._is_video_file(cue.media.uri):
            if self._display_enabled:
                widget = self._video_manager.video_widget_for(cue.output_target)
                cue.set_video_output(widget)

        # Stop old cues on same output immediately (no fade)
        for other in self._cue_model.cues():
            if other is not cue and other.output_target == cue.output_target:
                if other.state & (CueState.Running | CueState.Pause):
                    if hasattr(other, 'stop_immediate'):
                        other.stop_immediate()
                    else:
                        other.execute(CueAction.Stop)

        # Start new cue immediately
        self._start_cue_delayed(row)

    def _start_cue_delayed(self, row: int):
        cue = self._cue_model.cue_at(row)
        if cue is None:
            return
        cue.execute(CueAction.Start)
        self._current_cue = cue
        self._current_row = row
        self._table_model.refresh_row(row)
        self._refresh_action_buttons()
        if not self._progress_timer.isActive():
            self._progress_timer.start()

    def _play_cue(self, cue, row: int):
        # Route video output for the new cue first
        if isinstance(cue, MediaCue) and self._is_video_file(cue.media.uri):
            if self._display_enabled:
                widget = self._video_manager.video_widget_for(cue.output_target)
                cue.set_video_output(widget)
            else:
                cue.set_video_output(None)

        # Find running cues on same output to fade out
        cues_to_stop = []
        for r, other in enumerate(self._cue_model.cues()):
            if other is not cue:
                if other.state & (CueState.Running | CueState.Pause) and other.output_target == cue.output_target:
                    cues_to_stop.append(other)

        # Transition: fade out old cues, then start new
        if cues_to_stop:
            self._transition_start(cue, row, cues_to_stop)
        else:
            cue.execute(CueAction.Start)
            self._current_cue = cue
            self._current_row = row
            self._table_model.refresh_row(row)
            self._refresh_action_buttons()
            if not self._progress_timer.isActive():
                self._progress_timer.start()

    def _transition_start(self, new_cue, row: int, old_cues: list):
        # Fade out all old cues simultaneously
        max_fade = 0
        for old in old_cues:
            old.execute(CueAction.Stop)
            if isinstance(old, MediaCue) and old.fadeout_duration > max_fade:
                max_fade = old.fadeout_duration

        # Start new cue after fade out completes + small buffer
        delay = max_fade + 100 if max_fade > 0 else 300
        from PySide6.QtCore import QTimer
        QTimer.singleShot(delay, lambda: self._start_new_cue(new_cue, row))

    def _start_new_cue(self, cue, row: int):
        cue.execute(CueAction.Start)
        self._current_cue = cue
        self._current_row = row
        self._table_model.refresh_row(row)
        self._refresh_action_buttons()
        if not self._progress_timer.isActive():
            self._progress_timer.start()

    def _on_volume_changed(self, value):
        self._vol_label.setText(f"{value}%")
        for cue in self._cue_model.cues():
            if isinstance(cue, MediaCue) and cue.state & CueState.Running:
                cue.set_volume(value / 100.0)

    def _advance_standby(self):
        self._standby_index += 1
        if self._standby_index >= len(self._cue_model):
            self._standby_index = 0

    def standby_cue(self):
        return self._cue_model.cue_at(self._standby_index)

    def standby_index(self):
        return self._standby_index
