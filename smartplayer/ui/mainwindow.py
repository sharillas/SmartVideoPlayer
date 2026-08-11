from __future__ import annotations

import os

from PySide6.QtWidgets import (
    QMainWindow, QMenuBar, QMenu, QToolBar, QStatusBar,
    QFileDialog, QMessageBox, QLabel, QWidget, QVBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence, QIcon

from .cue_list_view import CueListView
from .session import Session
from .video_output_manager import VideoOutputManager
from .display_settings import DisplaySettingsDialog
from .undo_stack import UndoStack


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SmartPlayer - Cue Player for Stage Productions")
        self.resize(1100, 650)
        self._session = Session()
        self._cue_view = None
        self._video_manager = VideoOutputManager()
        self._undo_stack = UndoStack()
        self._build_menus()
        self._build_ui()
        self._update_title()
        if self._video_manager.has_external_display:
            self._video_manager.show_black_screen()

    def _build_menus(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")

        new_action = QAction("&New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self._on_new)
        file_menu.addAction(new_action)

        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self._on_open)
        file_menu.addAction(open_action)

        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self._on_save)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self._on_save_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        edit_menu = menu_bar.addMenu("&Edit")

        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self._on_undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self._on_redo)
        edit_menu.addAction(redo_action)

        settings_menu = menu_bar.addMenu("&Settings")

        display_action = QAction("&Display Configuration...", self)
        display_action.triggered.connect(self._on_display_settings)
        settings_menu.addAction(display_action)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(4, 4, 4, 4)

        self._cue_view = CueListView(
            self._session.cue_model, self._video_manager, self._undo_stack
        )
        layout.addWidget(self._cue_view)

        self._status_bar = QStatusBar()
        self._status_bar.showMessage("Ready  |  Space=GO  Esc=Stop  Ctrl+Z=Undo  Ctrl+Y=Redo")
        self.setStatusBar(self._status_bar)

    def _replace_cue_view(self):
        central = self.centralWidget()
        if central is None or central.layout() is None:
            return
        old_layout = central.layout()
        while old_layout.count():
            item = old_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._undo_stack.clear()
        self._cue_view = CueListView(
            self._session.cue_model, self._video_manager, self._undo_stack
        )
        self._cue_view._editor_panel.set_save_callback(self._on_save)
        old_layout.addWidget(self._cue_view)

    def load_session(self, filepath: str):
        self._session.close()
        self._session = Session()
        if self._session.load(filepath):
            self._replace_cue_view()
            self._update_title()
            self._status_bar.showMessage(f"Loaded: {filepath}")
        else:
            self._status_bar.showMessage("Failed to load session")

    def _on_new(self):
        self._session.close()
        self._session = Session()
        self._replace_cue_view()
        self._update_title()
        self._status_bar.showMessage("New session created")

    def _on_open(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open Session", "", "SmartPlayer Sessions (*.sps);;All Files (*.*)"
        )
        if filepath:
            self.load_session(filepath)

    def _on_save(self):
        if self._session.filepath:
            self._session.save()
            self._status_bar.showMessage(f"Saved: {self._session.filepath}")
        else:
            self._on_save_as()

    def _on_save_as(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Session", "session.sps", "SmartPlayer Sessions (*.sps);;All Files (*.*)"
        )
        if filepath:
            self._session.save(filepath)
            self._update_title()
            self._status_bar.showMessage(f"Saved: {filepath}")

    def _on_undo(self):
        if self._cue_view is not None:
            self._cue_view._on_undo()

    def _on_redo(self):
        if self._cue_view is not None:
            self._cue_view._on_redo()

    def _on_display_settings(self):
        dlg = DisplaySettingsDialog(self._video_manager, self)
        dlg.exec()
        if self._cue_view:
            self._cue_view.refresh_pattern_btn()

    def _update_title(self):
        fname = os.path.basename(self._session.filepath) if self._session.filepath else "Untitled"
        self.setWindowTitle(f"SmartPlayer - {fname}")

    def closeEvent(self, event):
        self._video_manager.close_all()
        self._session.close()
        event.accept()
