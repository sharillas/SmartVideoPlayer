from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QComboBox, QPushButton, QGroupBox, QDialogButtonBox, QMessageBox,
    QSpinBox, QCheckBox, QFileDialog
)
from PySide6.QtCore import Qt

from .video_output_manager import VideoOutputManager


class DisplaySettingsDialog(QDialog):
    def __init__(self, video_manager: VideoOutputManager, parent=None):
        super().__init__(parent)
        self._vm = video_manager
        self.setWindowTitle("Display Configuration")
        self.setMinimumWidth(480)
        self._build_ui()
        self._load_values()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # ── Output screen ──
        screen_group = QGroupBox("Output Display")
        sform = QFormLayout(screen_group)

        self._info_label = QLabel()
        self._info_label.setWordWrap(True)
        self._info_label.setStyleSheet("color: #888; font-size: 11px;")

        screens = self._vm.available_screens()
        self._screen_combo = QComboBox()
        for s in screens:
            label = f"Screen {s['index']}: {s['name']} ({s['resolution']})"
            if s["is_primary"]:
                label += " [CTRL]"
            else:
                label += " [OUT]"
            self._screen_combo.addItem(label, s["index"])

        if self._vm.has_external_display:
            self._info_label.setText(
                "External display detected. Select output screen and mode."
            )
        else:
            self._info_label.setText(
                "No external display. Video will open in a separate window.\n"
                "Connect a second monitor and restart for fullscreen support."
            )

        sform.addRow("Screen:", self._screen_combo)
        sform.addRow("", self._info_label)
        layout.addWidget(screen_group)

        # ── Output mode ──
        mode_group = QGroupBox("Output Mode & Format")
        mform = QFormLayout(mode_group)

        self._mode_combo = QComboBox()
        self._mode_combo.addItem("Fullscreen (native resolution)", "fullscreen")
        self._mode_combo.addItem("Windowed (custom resolution)", "custom")
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mform.addRow("Mode:", self._mode_combo)

        # Resolution preset
        self._preset_combo = QComboBox()
        presets = self._vm.resolution_presets()
        for name, (w, h) in presets.items():
            self._preset_combo.addItem(f"{name} ({w}x{h})", (w, h))
        self._preset_combo.addItem("Custom...", None)
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        mform.addRow("Resolution:", self._preset_combo)

        # Custom width/height
        res_layout = QHBoxLayout()
        self._width_spin = QSpinBox()
        self._width_spin.setRange(320, 7680)
        self._width_spin.setValue(1920)
        self._width_spin.setSuffix(" px")
        res_layout.addWidget(QLabel("W:"))
        res_layout.addWidget(self._width_spin)

        self._height_spin = QSpinBox()
        self._height_spin.setRange(240, 4320)
        self._height_spin.setValue(1080)
        self._height_spin.setSuffix(" px")
        res_layout.addWidget(QLabel("H:"))
        res_layout.addWidget(self._height_spin)
        mform.addRow("Custom:", res_layout)

        # Position offset
        pos_layout = QHBoxLayout()
        self._x_spin = QSpinBox()
        self._x_spin.setRange(0, 7680)
        self._x_spin.setSuffix(" px")
        pos_layout.addWidget(QLabel("X:"))
        pos_layout.addWidget(self._x_spin)

        self._y_spin = QSpinBox()
        self._y_spin.setRange(0, 4320)
        self._y_spin.setSuffix(" px")
        pos_layout.addWidget(QLabel("Y:"))
        pos_layout.addWidget(self._y_spin)
        mform.addRow("Offset:", pos_layout)

        layout.addWidget(mode_group)

        # Test buttons
        test_group = QGroupBox("Output Preview / Test Patterns")
        test_layout = QVBoxLayout(test_group)

        row1 = QHBoxLayout()
        self._test_btn = QPushButton("Black Output")
        self._test_btn.clicked.connect(self._on_test_black)
        row1.addWidget(self._test_btn)

        self._pattern_btn = QPushButton("Load Test Pattern...")
        self._pattern_btn.clicked.connect(self._on_load_pattern)
        row1.addWidget(self._pattern_btn)
        test_layout.addLayout(row1)

        row2 = QHBoxLayout()
        self._pattern_label = QLabel("No pattern loaded")
        self._pattern_label.setStyleSheet("color: #888; font-size: 11px;")
        self._pattern_label.setWordWrap(True)
        row2.addWidget(self._pattern_label, 1)

        self._show_pattern_btn = QPushButton("Show Pattern")
        self._show_pattern_btn.setEnabled(False)
        self._show_pattern_btn.clicked.connect(self._on_show_pattern)
        row2.addWidget(self._show_pattern_btn)

        self._hide_btn = QPushButton("Hide Output")
        self._hide_btn.clicked.connect(self._on_hide_test)
        row2.addWidget(self._hide_btn)
        test_layout.addLayout(row2)

        layout.addWidget(test_group)

        layout.addSpacing(8)

        shortcuts = QGroupBox("Shortcuts (Video Window)")
        sform2 = QFormLayout(shortcuts)
        sform2.addRow("Esc:", QLabel("Close window"))
        sform2.addRow("F / F11:", QLabel("Toggle fullscreen"))
        layout.addWidget(shortcuts)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_mode_changed(self):
        mode = self._mode_combo.currentData()
        is_custom = (mode == "custom")
        self._preset_combo.setEnabled(is_custom)
        self._width_spin.setEnabled(is_custom)
        self._height_spin.setEnabled(is_custom)
        self._x_spin.setEnabled(is_custom)
        self._y_spin.setEnabled(is_custom)

    def _on_preset_changed(self):
        data = self._preset_combo.currentData()
        if data is not None:
            w, h = data
            self._width_spin.setValue(w)
            self._height_spin.setValue(h)

    def _on_test_black(self):
        self._apply_to_manager()
        self._vm.show_black_screen()

    def _on_load_pattern(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Test Pattern",
            "",
            "Images & Video (*.png *.jpg *.jpeg *.tiff *.tif *.bmp *.gif *.mp4 *.avi *.mov *.wmv *.webm);;All Files (*.*)"
        )
        if filepath:
            self._pattern_path = filepath
            import os
            self._pattern_label.setText(os.path.basename(filepath))
            self._show_pattern_btn.setEnabled(True)

    def _on_show_pattern(self):
        self._apply_to_manager()
        if hasattr(self, '_pattern_path') and self._pattern_path:
            self._vm.show_test_pattern(self._pattern_path)

    def _on_test(self):
        self._apply_to_manager()
        self._vm.show_black_screen()

    def _on_hide_test(self):
        self._vm.force_hide()

    def _load_values(self):
        for i in range(self._screen_combo.count()):
            if self._screen_combo.itemData(i) == self._vm.output_screen_index:
                self._screen_combo.setCurrentIndex(i)
                break

        for i in range(self._mode_combo.count()):
            if self._mode_combo.itemData(i) == self._vm.output_mode:
                self._mode_combo.setCurrentIndex(i)
                break

        w, h = self._vm.custom_resolution
        self._width_spin.setValue(w)
        self._height_spin.setValue(h)
        x, y = self._vm.custom_position
        self._x_spin.setValue(x)
        self._y_spin.setValue(y)

        self._on_mode_changed()

    def _apply_to_manager(self):
        self._vm.output_screen_index = self._screen_combo.currentData()
        self._vm.output_mode = self._mode_combo.currentData()
        self._vm.custom_resolution = (self._width_spin.value(), self._height_spin.value())
        self._vm.custom_position = (self._x_spin.value(), self._y_spin.value())

    def _on_accept(self):
        self._apply_to_manager()
        self.accept()
