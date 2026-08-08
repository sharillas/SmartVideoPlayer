from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QComboBox, QPushButton, QGroupBox, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt

from .video_output_manager import VideoOutputManager


class DisplaySettingsDialog(QDialog):
    def __init__(self, video_manager: VideoOutputManager, parent=None):
        super().__init__(parent)
        self._vm = video_manager
        self.setWindowTitle("Display Configuration")
        self.setMinimumWidth(450)
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        group = QGroupBox("Video Output")
        form = QFormLayout(group)

        self._info_label = QLabel()
        self._info_label.setWordWrap(True)
        self._info_label.setStyleSheet("color: #888888; font-size: 11px;")

        screens = self._vm.available_screens()
        self._screen_combo = QComboBox()
        for s in screens:
            label = f"Screen {s['index']}: {s['name']} ({s['resolution']})"
            if s["is_primary"]:
                label += " [PRIMARY - Control]"
            else:
                label += " [OUTPUT]"
            self._screen_combo.addItem(label, s["index"])

        if self._vm.has_external_display:
            self._info_label.setText(
                "External display detected. Video will open fullscreen on the selected output screen.\n"
                "Control window stays on the primary screen."
            )
        else:
            self._info_label.setText(
                "No external display detected. Video will open in a separate 800x600 window.\n"
                "Connect a second monitor and restart for fullscreen external display support."
            )

        form.addRow("Output screen:", self._screen_combo)
        form.addRow("", self._info_label)
        layout.addWidget(group)

        shortcuts = QGroupBox("Shortcuts (in video window)")
        sform = QFormLayout(shortcuts)
        sform.addRow("Esc:", QLabel("Exit fullscreen / Close window"))
        sform.addRow("F / F11:", QLabel("Toggle fullscreen"))
        layout.addWidget(shortcuts)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_values(self):
        for i in range(self._screen_combo.count()):
            if self._screen_combo.itemData(i) == self._vm.output_screen_index:
                self._screen_combo.setCurrentIndex(i)
                break

    def _on_accept(self):
        screen_idx = self._screen_combo.currentData()
        self._vm.output_screen_index = screen_idx
        self.accept()
