from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDialogButtonBox,
    QTabWidget, QWidget, QLabel, QTextEdit
)
from PySide6.QtCore import Qt

from ..cues.cue import Cue, NextAction
from ..cues.media_cue import MediaCue
from ..core.fader import FadeType


class CueSettingsDialog(QDialog):
    def __init__(self, cue: Cue, parent=None):
        super().__init__(parent)
        self._cue = cue
        self.setWindowTitle(f"Cue Settings: {cue.name}")
        self.setMinimumWidth(500)
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        tabs.addTab(self._build_general_tab(), "General")
        if isinstance(self._cue, MediaCue):
            tabs.addTab(self._build_media_tab(), "Media")
        tabs.addTab(self._build_appearance_tab(), "Appearance")
        layout.addWidget(tabs)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _build_general_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)

        self._name_edit = QLineEdit()
        form.addRow("Name:", self._name_edit)

        self._desc_edit = QTextEdit()
        self._desc_edit.setMaximumHeight(80)
        form.addRow("Description:", self._desc_edit)

        self._pre_wait = QDoubleSpinBox()
        self._pre_wait.setRange(0, 999)
        self._pre_wait.setDecimals(1)
        self._pre_wait.setSuffix(" s")
        form.addRow("Pre-Wait:", self._pre_wait)

        self._post_wait = QDoubleSpinBox()
        self._post_wait.setRange(0, 999)
        self._post_wait.setDecimals(1)
        self._post_wait.setSuffix(" s")
        form.addRow("Post-Wait:", self._post_wait)

        self._next_action = QComboBox()
        for na in NextAction:
            self._next_action.addItem(na.value, na)
        form.addRow("Next Action:", self._next_action)

        self._fadein_dur = QSpinBox()
        self._fadein_dur.setRange(0, 60000)
        self._fadein_dur.setSuffix(" ms")
        form.addRow("Fade In:", self._fadein_dur)

        self._fadeout_dur = QSpinBox()
        self._fadeout_dur.setRange(0, 60000)
        self._fadeout_dur.setSuffix(" ms")
        form.addRow("Fade Out:", self._fadeout_dur)

        self._fadein_type = QComboBox()
        self._fadeout_type = QComboBox()
        for ft in FadeType:
            self._fadein_type.addItem(ft.value, ft)
            self._fadeout_type.addItem(ft.value, ft)
        form.addRow("Fade In Curve:", self._fadein_type)
        form.addRow("Fade Out Curve:", self._fadeout_type)

        return w

    def _build_media_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)

        self._media_uri = QLabel(self._cue.media.uri or "(none)")
        self._media_uri.setWordWrap(True)
        form.addRow("File:", self._media_uri)

        self._media_loop = QComboBox()
        self._media_loop.addItem("No Loop", False)
        self._media_loop.addItem("Loop", True)
        form.addRow("Loop:", self._media_loop)

        self._media_volume = QSpinBox()
        self._media_volume.setRange(0, 100)
        self._media_volume.setSuffix(" %")
        form.addRow("Volume:", self._media_volume)

        dur_ms = self._cue.media.duration
        mins, secs = divmod(dur_ms / 1000, 60) if dur_ms else (0, 0)
        form.addRow("Duration:", QLabel(f"{int(mins):02d}:{secs:05.2f}"))

        return w

    def _build_appearance_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)

        self._stylesheet = QTextEdit()
        self._stylesheet.setMaximumHeight(60)
        self._stylesheet.setPlaceholderText("color: red; font-weight: bold;")
        form.addRow("Style:", self._stylesheet)

        return w

    def _load_values(self):
        self._name_edit.setText(self._cue.name)
        self._desc_edit.setPlainText(self._cue.description)
        self._pre_wait.setValue(self._cue.pre_wait)
        self._post_wait.setValue(self._cue.post_wait)
        self._fadein_dur.setValue(self._cue.fadein_duration)
        self._fadeout_dur.setValue(self._cue.fadeout_duration)

        for i in range(self._next_action.count()):
            if self._next_action.itemData(i) == self._cue.next_action:
                self._next_action.setCurrentIndex(i)
                break

        for i in range(self._fadein_type.count()):
            if self._fadein_type.itemData(i) == self._cue.fadein_type:
                self._fadein_type.setCurrentIndex(i)
                break

        for i in range(self._fadeout_type.count()):
            if self._fadeout_type.itemData(i) == self._cue.fadeout_type:
                self._fadeout_type.setCurrentIndex(i)
                break

        if isinstance(self._cue, MediaCue):
            self._media_loop.setCurrentIndex(1 if self._cue.media.loop else 0)
            self._media_volume.setValue(int(self._cue.media.volume))

    def _on_accept(self):
        self._cue.name = self._name_edit.text()
        self._cue.description = self._desc_edit.toPlainText()
        self._cue.pre_wait = self._pre_wait.value()
        self._cue.post_wait = self._post_wait.value()
        self._cue.fadein_duration = self._fadein_dur.value()
        self._cue.fadeout_duration = self._fadeout_dur.value()
        self._cue.next_action = self._next_action.currentData()
        self._cue.fadein_type = self._fadein_type.currentData()
        self._cue.fadeout_type = self._fadeout_type.currentData()

        if isinstance(self._cue, MediaCue):
            self._cue.media.loop = self._media_loop.currentData()
            self._cue.media.volume = self._media_volume.value()

        self.accept()
