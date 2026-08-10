from __future__ import annotations

from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QGuiApplication
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl

from .video_output_window import VideoOutputWindow

RESOLUTION_PRESETS = {
    "480p (SD)": (854, 480),
    "720p (HD)": (1280, 720),
    "1080p (Full HD)": (1920, 1080),
    "1440p (2K)": (2560, 1440),
    "2160p (4K)": (3840, 2160),
    "800x600 (Default)": (800, 600),
}


class VideoOutputManager:
    def __init__(self):
        self._window: VideoOutputWindow | None = None
        self._pattern_player = None
        self._pattern_audio = None
        self._screen_count = len(QGuiApplication.screens())
        self._output_screen_index = 1 if self._screen_count > 1 else 0
        self._output_mode = "fullscreen"  # fullscreen | windowed | custom
        self._custom_width = 1920
        self._custom_height = 1080
        self._custom_x = 0
        self._custom_y = 0

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

    @property
    def output_mode(self) -> str:
        return self._output_mode

    @output_mode.setter
    def output_mode(self, value: str):
        self._output_mode = value

    @property
    def custom_resolution(self) -> tuple[int, int]:
        return (self._custom_width, self._custom_height)

    @custom_resolution.setter
    def custom_resolution(self, value: tuple[int, int]):
        self._custom_width, self._custom_height = value

    @property
    def custom_position(self) -> tuple[int, int]:
        return (self._custom_x, self._custom_y)

    @custom_position.setter
    def custom_position(self, value: tuple[int, int]):
        self._custom_x, self._custom_y = value

    def active_widget(self) -> QVideoWidget:
        self._ensure_window()
        return self._window.video_widget

    def show_video(self):
        self._ensure_window()
        if self.has_external_display:
            if self._output_mode == "custom":
                self._window.go_custom_windowed(
                    self._output_screen_index,
                    self._custom_width, self._custom_height,
                    self._custom_x, self._custom_y
                )
            else:
                self._window.go_fullscreen_on_screen(self._output_screen_index)
        else:
            w, h = self._custom_width, self._custom_height
            self._window.show_as_window(w, h)

    def hide_video(self):
        if not self.has_external_display:
            if self._window is not None:
                self._window.hide()

    def stop_pattern(self):
        if self._pattern_player is not None:
            self._pattern_player.stop()

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
        if self._pattern_player is not None:
            self._pattern_player.stop()
        if self.has_external_display:
            if self._output_mode == "custom":
                self._window.go_custom_windowed(
                    self._output_screen_index,
                    self._custom_width, self._custom_height,
                    self._custom_x, self._custom_y
                )
            else:
                self._window.go_fullscreen_on_screen(self._output_screen_index)

    def show_test_pattern(self, filepath: str):
        self._ensure_window()
        if self.has_external_display:
            if self._output_mode == "custom":
                self._window.go_custom_windowed(
                    self._output_screen_index,
                    self._custom_width, self._custom_height,
                    self._custom_x, self._custom_y
                )
            else:
                self._window.go_fullscreen_on_screen(self._output_screen_index)
        else:
            self._window.show_as_window(self._custom_width, self._custom_height)

        if not hasattr(self, '_pattern_player') or self._pattern_player is None:
            self._pattern_player = QMediaPlayer()
            self._pattern_audio = QAudioOutput()
            self._pattern_player.setAudioOutput(self._pattern_audio)
            self._pattern_audio.setVolume(0)

        self._pattern_player.setVideoOutput(self._window.video_widget)
        self._pattern_player.setSource(QUrl.fromLocalFile(filepath))
        self._pattern_player.setLoops(QMediaPlayer.Loops.Infinite)
        self._pattern_player.play()

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
                "width": geo.width(),
                "height": geo.height(),
                "is_primary": i == 0,
            })
        return result

    def status_text(self) -> str:
        if self.has_external_display:
            if self._output_mode == "custom":
                return f"Video: {self._custom_width}x{self._custom_height} on Display {self._output_screen_index}"
            return f"Video: Ext. Display {self._output_screen_index} (fullscreen)"
        else:
            return f"Video: Window {self._custom_width}x{self._custom_height}"

    @staticmethod
    def resolution_presets() -> dict:
        return RESOLUTION_PRESETS
