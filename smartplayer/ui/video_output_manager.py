from __future__ import annotations

from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QGuiApplication

from .video_output_window import VideoOutputWindow


class VideoOutputManager:
    def __init__(self):
        self._window: VideoOutputWindow | None = None
        self._screen_count = len(QGuiApplication.screens())
        self._output_screen_index = 1 if self._screen_count > 1 else 0

    @property
    def screen_count(self) -> int:
        return self._screen_count

    @property
    def has_external_display(self) -> bool:
        return self._screen_count > 1

    @property
    def output_screen_index(self) -> int:
        return self._output_screen_index

    @output_screen_index.setter
    def output_screen_index(self, value: int):
        screens = QGuiApplication.screens()
        if 0 <= value < len(screens):
            self._output_screen_index = value

    def active_widget(self) -> QVideoWidget:
        self._ensure_window()
        return self._window.video_widget

    def show_video(self):
        self._ensure_window()
        if self.has_external_display:
            self._window.go_fullscreen_on_screen(self._output_screen_index)
        else:
            self._window.show_as_window()

    def hide_video(self):
        if not self.has_external_display:
            if self._window is not None:
                self._window.hide()

    def force_hide(self):
        if self._window is not None:
            self._window.exit_fullscreen()
            self._window.hide()

    def close_all(self):
        if self._window is not None:
            self._window.exit_fullscreen()
            self._window.hide()
            self._window.close()

    def show_black_screen(self):
        self._ensure_window()
        if self.has_external_display:
            self._window.go_fullscreen_on_screen(self._output_screen_index)

    def _ensure_window(self):
        if self._window is None:
            self._window = VideoOutputWindow()
            self._window.set_target_screen(self._output_screen_index)

    def available_screens(self) -> list[dict]:
        screens = QGuiApplication.screens()
        result = []
        for i, s in enumerate(screens):
            geo = s.geometry()
            result.append({
                "index": i,
                "name": s.name(),
                "resolution": f"{geo.width()}x{geo.height()}",
                "is_primary": i == 0,
            })
        return result

    def status_text(self) -> str:
        if self.has_external_display:
            return f"Video: Ext. Display {self._output_screen_index} (fullscreen)"
        else:
            return "Video: Separate Window (800x600)"
