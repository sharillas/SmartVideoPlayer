from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QGuiApplication


class VideoOutputWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SmartPlayer - Video Output")
        self.setStyleSheet("background-color: #000000;")
        self._render_widget = QWidget()
        self._render_widget.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        self._render_widget.setAttribute(Qt.WidgetAttribute.WA_DontCreateNativeAncestors, True)
        self.setCentralWidget(self._render_widget)
        self._is_fullscreen = False
        self._target_screen_index = -1
        self._custom_width = 800
        self._custom_height = 600

    @property
    def render_widget(self) -> QWidget:
        return self._render_widget

    def set_target_screen(self, index: int):
        self._target_screen_index = index

    def show_as_window(self, width: int = 800, height: int = 600):
        self._custom_width = width
        self._custom_height = height
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.resize(width, height)
        self.showNormal()

    def go_fullscreen_on_screen(self, screen_index: int):
        screens = QGuiApplication.screens()
        if 0 <= screen_index < len(screens):
            self._target_screen_index = screen_index
            geo = screens[screen_index].geometry()
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
            self.setGeometry(geo)
            self.showFullScreen()
            self._is_fullscreen = True

    def go_custom_windowed(self, screen_index: int, w: int, h: int, x: int = 0, y: int = 0):
        screens = QGuiApplication.screens()
        if 0 <= screen_index < len(screens):
            geo = screens[screen_index].geometry()
            self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
            self.setGeometry(geo.x() + x, geo.y() + y, w, h)
            self.showNormal()

    def exit_fullscreen(self):
        if self._is_fullscreen:
            self._is_fullscreen = False
            self.hide()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self.exit_fullscreen()
        self.hide()
        event.ignore()
