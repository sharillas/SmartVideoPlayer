from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QTabWidget,
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
    QLabel, QTextEdit, QPushButton, QHBoxLayout,
    QColorDialog
)
from PySide6.QtCore import Qt

from ..cues.cue import Cue, NextAction
from ..cues.media_cue import MediaCue
from ..core.fader import FadeType


class CueEditorPanel(QWidget):
    def __init__(self, undo_stack=None, parent=None):
        super().__init__(parent)
        self._cue = None
        self._undo_stack = undo_stack
        self._save_callback = None
        self.setMinimumWidth(280)
        self.setMaximumWidth(380)
        self._build_ui()
        self._show_empty()

    def set_save_callback(self, callback):
        self._save_callback = callback

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._title_label = QLabel("No cue selected")
        self._title_label.setStyleSheet("color: #888; font-size: 14px; font-weight: bold; padding: 8px;")
        layout.addWidget(self._title_label)

        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.TabPosition.North)

        self._general_tab = self._build_general_tab()
        self._media_tab = self._build_media_tab()
        self._fade_tab = self._build_fade_tab()

        self._tabs.addTab(self._general_tab, "Cue Settings")
        self._tabs.addTab(self._fade_tab, "Fade")
        self._tabs.addTab(self._media_tab, "Media")

        layout.addWidget(self._tabs)
        self._tabs.hide()

        self._save_btn = QPushButton("SAVE")
        self._save_btn.setMinimumHeight(34)
        self._save_btn.setStyleSheet(
            "QPushButton { background-color: #1565C0; color: #fff; border: none; "
            "border-radius: 3px; padding: 6px 16px; font-size: 12px; font-weight: bold; } "
            "QPushButton:hover { background-color: #1976D2; }"
        )
        self._save_btn.clicked.connect(self._on_save)
        self._save_btn.hide()
        layout.addWidget(self._save_btn)

    def _build_general_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setContentsMargins(8, 12, 8, 8)
        form.setSpacing(8)

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Cue name...")
        self._name_edit.textChanged.connect(self._on_name_changed)
        form.addRow("Name:", self._name_edit)

        self._priority_spin = QSpinBox()
        self._priority_spin.setRange(1, 5)
        self._priority_spin.setValue(3)
        self._priority_spin.setToolTip("1=Lowest, 5=Highest. Higher priority cues can interrupt lower ones.")
        self._priority_spin.valueChanged.connect(self._on_changed)
        form.addRow("Priority:", self._priority_spin)

        color_layout = QHBoxLayout()
        self._color_btn = QPushButton()
        self._color_btn.setFixedSize(24, 24)
        self._color_btn.setStyleSheet("background-color: #555; border: 1px solid #777; border-radius: 3px;")
        self._color_btn.clicked.connect(self._on_color_pick)
        self._color_label = QLabel(" No tag")
        self._color_label.setStyleSheet("color: #888;")
        color_layout.addWidget(self._color_btn)
        color_layout.addWidget(self._color_label)
        color_layout.addStretch()
        form.addRow("Color:", color_layout)

        self._output_target = QSpinBox()
        self._output_target.setRange(1, 8)
        self._output_target.setValue(1)
        self._output_target.setToolTip("Which output screen this cue plays on (1=primary, 2=secondary, etc.)")
        self._output_target.valueChanged.connect(self._on_changed)
        form.addRow("Output:", self._output_target)

        self._next_action = QComboBox()
        self._next_action.addItem("Next Cue", NextAction.NextCue)
        self._next_action.addItem("Previous Cue", NextAction.PreviousCue)
        self._next_action.addItem("Stop at end & out", NextAction.StopEndOut)
        self._next_action.addItem("Pause and keep Last Frame", NextAction.PauseKeepLast)
        self._next_action.addItem("Loop", NextAction.Loop)
        self._next_action.currentIndexChanged.connect(self._on_changed)
        form.addRow("Next Action:", self._next_action)

        return w

    def _build_media_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setContentsMargins(8, 12, 8, 8)
        form.setSpacing(8)

        self._media_uri = QLabel("(none)")
        self._media_uri.setWordWrap(True)
        self._media_uri.setStyleSheet("color: #888; font-size: 11px;")
        form.addRow("File:", self._media_uri)

        self._media_loop = QComboBox()
        self._media_loop.addItem("No Loop", False)
        self._media_loop.addItem("Loop", True)
        self._media_loop.currentIndexChanged.connect(self._on_changed)
        form.addRow("Loop:", self._media_loop)

        self._media_volume = QSpinBox()
        self._media_volume.setRange(0, 100)
        self._media_volume.setSuffix(" %")
        self._media_volume.valueChanged.connect(self._on_changed)
        form.addRow("Volume:", self._media_volume)

        self._media_duration = QLabel("00:00:00")
        self._media_duration.setStyleSheet("color: #888;")
        form.addRow("Duration:", self._media_duration)

        self._media_start = QDoubleSpinBox()
        self._media_start.setRange(0, 99999)
        self._media_start.setDecimals(1)
        self._media_start.setSuffix(" s")
        self._media_start.valueChanged.connect(self._on_changed)
        form.addRow("Start At:", self._media_start)

        self._media_stop = QDoubleSpinBox()
        self._media_stop.setRange(0, 99999)
        self._media_stop.setDecimals(1)
        self._media_stop.setSuffix(" s")
        self._media_stop.valueChanged.connect(self._on_changed)
        form.addRow("Stop At:", self._media_stop)

        return w

    def _build_fade_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        form.setContentsMargins(8, 12, 8, 8)
        form.setSpacing(8)

        self._fadein_dur = QSpinBox()
        self._fadein_dur.setRange(0, 60000)
        self._fadein_dur.setSuffix(" ms")
        self._fadein_dur.valueChanged.connect(self._on_changed)
        form.addRow("Fade In:", self._fadein_dur)

        self._fadein_type = QComboBox()
        for ft in FadeType:
            self._fadein_type.addItem(ft.value, ft)
        self._fadein_type.currentIndexChanged.connect(self._on_changed)
        form.addRow("In Curve:", self._fadein_type)

        self._fadeout_dur = QSpinBox()
        self._fadeout_dur.setRange(0, 60000)
        self._fadeout_dur.setSuffix(" ms")
        self._fadeout_dur.valueChanged.connect(self._on_changed)
        form.addRow("Fade Out:", self._fadeout_dur)

        self._fadeout_type = QComboBox()
        for ft in FadeType:
            self._fadeout_type.addItem(ft.value, ft)
        self._fadeout_type.currentIndexChanged.connect(self._on_changed)
        form.addRow("Out Curve:", self._fadeout_type)

        return w

    def set_cue(self, cue: Cue | None):
        self._cue = cue
        if cue is None:
            self._show_empty()
            return
        self._show_editor()
        self._load_cue(cue)

    def _show_empty(self):
        self._title_label.setText("No cue selected")
        self._title_label.show()
        self._tabs.hide()
        self._save_btn.hide()

    def _show_editor(self):
        self._title_label.hide()
        self._tabs.show()
        self._save_btn.show()

    def _load_cue(self, cue: Cue):
        self._updating = True

        self._name_edit.setText(cue.name)
        self._priority_spin.setValue(cue.priority)
        self._output_target.setValue(cue.output_target + 1)

        if cue.color:
            self._color_btn.setStyleSheet(f"background-color: {cue.color}; border: 1px solid #777; border-radius: 3px;")
            self._color_label.setText(f" {cue.color}")
        else:
            self._color_btn.setStyleSheet("background-color: #555; border: 1px solid #777; border-radius: 3px;")
            self._color_label.setText(" No tag")

        for i in range(self._next_action.count()):
            if self._next_action.itemData(i) == cue.next_action:
                self._next_action.setCurrentIndex(i)
                break

        self._fadein_dur.setValue(cue.fadein_duration)
        self._fadeout_dur.setValue(cue.fadeout_duration)

        for i in range(self._fadein_type.count()):
            if self._fadein_type.itemData(i) == cue.fadein_type:
                self._fadein_type.setCurrentIndex(i)
                break

        for i in range(self._fadeout_type.count()):
            if self._fadeout_type.itemData(i) == cue.fadeout_type:
                self._fadeout_type.setCurrentIndex(i)
                break

        if isinstance(cue, MediaCue):
            self._tabs.setTabVisible(2, True)
            self._media_uri.setText(cue.media.uri or "(none)")
            self._media_loop.setCurrentIndex(1 if cue.media.loop else 0)
            self._media_volume.setValue(int(cue.media.volume))
            dur = cue.media.duration
            if dur > 0:
                total_sec = int(dur / 1000)
                h, m, s = total_sec // 3600, (total_sec % 3600) // 60, total_sec % 60
                self._media_duration.setText(f"{h:02d}:{m:02d}:{s:02d}")
            else:
                self._media_duration.setText("00:00:00")
            self._media_start.setValue(cue.media.start_time / 1000.0)
            self._media_stop.setValue(cue.media.stop_time / 1000.0)
        else:
            self._tabs.setTabVisible(2, False)

        self._updating = False

    def _on_name_changed(self, text):
        if self._cue is None or getattr(self, '_updating', True):
            return
        self._cue.name = text

    def _on_changed(self, *args):
        if self._cue is None or getattr(self, '_updating', True):
            return
        cue = self._cue
        cue.name = self._name_edit.text()
        cue.priority = self._priority_spin.value()
        cue.output_target = self._output_target.value() - 1
        cue.next_action = self._next_action.currentData()
        cue.fadein_duration = self._fadein_dur.value()
        cue.fadeout_duration = self._fadeout_dur.value()
        cue.fadein_type = self._fadein_type.currentData()
        cue.fadeout_type = self._fadeout_type.currentData()

        if isinstance(cue, MediaCue):
            cue.media.loop = self._media_loop.currentData()
            cue.media.volume = self._media_volume.value()
            cue.media.start_time = int(self._media_start.value() * 1000)
            cue.media.stop_time = int(self._media_stop.value() * 1000)

    def _on_color_pick(self):
        color = QColorDialog.getColor()
        if color.isValid():
            hex_color = color.name()
            self._cue.color = hex_color
            self._color_btn.setStyleSheet(f"background-color: {hex_color}; border: 1px solid #777; border-radius: 3px;")
            self._color_label.setText(f" {hex_color}")

    def _on_save(self):
        self._on_changed()
        self._save_btn.setText("SAVED")
        self._save_btn.setStyleSheet(
            "QPushButton { background-color: #2E7D32; color: #A5D6A7; border: none; "
            "border-radius: 3px; padding: 6px 16px; font-size: 12px; font-weight: bold; } "
        )
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1500, self._restore_save_btn)
        if self._save_callback:
            self._save_callback()

    def _restore_save_btn(self):
        self._save_btn.setText("SAVE")
        self._save_btn.setStyleSheet(
            "QPushButton { background-color: #1565C0; color: #fff; border: none; "
            "border-radius: 3px; padding: 6px 16px; font-size: 12px; font-weight: bold; } "
            "QPushButton:hover { background-color: #1976D2; }"
        )

