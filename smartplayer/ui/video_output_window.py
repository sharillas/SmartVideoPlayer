from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeyEvent, QScreen, QGuiApplication


class VideoOutputWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SmartPlayer - Video Output")
        self.setStyleSheet("background-color: #000000;")
        self._video_widget = QVideoWidget()
        self.setCentralWidget(self._video_widget)
        self._is_fullscreen = False
        self._target_screen_index = -1
        self._status_bar = None

    @property
    def video_widget(self) -> QVideoWidget:
        return self._video_widget

    def set_target_screen(self, index: int):
        self._target_screen_index = index

    def show_as_window(self):
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setWindowTitle("SmartPlayer - Video Output")
        self.resize(800, 600)
        self.showNormal()

    def go_fullscreen_on_screen(self, screen_index: int):
        screens = QGuiApplication.screens()
        if 0 <= screen_index < len(screens):
            self._target_screen_index = screen_index
            target_screen = screens[screen_index]
            geo = target_screen.geometry()

            self.setWindowFlags(
                Qt.WindowType.FramelessWindowHint |
                Qt.WindowType.WindowStaysOnTopHint
            )
            self.setGeometry(geo)
            self.showFullScreen()
            self._is_fullscreen = True

    def exit_fullscreen(self):
        if self._is_fullscreen:
            self._video_widget.setFullScreen(False)
            self._is_fullscreen = False
            self.hide()

    def toggle_fullscreen(self):
        if self._is_fullscreen:
            self.exit_fullscreen()
        else:
            self.go_fullscreen_on_screen(self._target_screen_index)

    def show_windowed(self):
        self.exit_fullscreen()
        self.show_as_window()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        elif event.key() in (Qt.Key.Key_F, Qt.Key.Key_F11):
            if self._is_fullscreen:
                self.exit_fullscreen()
            else:
                self.show_windowed()
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self.exit_fullscreen()
        self.hide()
        event.ignore()
