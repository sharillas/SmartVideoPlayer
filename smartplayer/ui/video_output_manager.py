from __future__ import annotations

import os

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
        self._windows: dict[int, VideoOutputWindow] = {}
        self._pattern_player: QMediaPlayer | None = None
        self._pattern_audio: QAudioOutput | None = None
        self._last_pattern: str | None = None
        self._screen_count = len(QGuiApplication.screens())
        self._output_screen_index = 1 if self._screen_count > 1 else 0
        self._output_mode = "fullscreen"
        self._custom_width = 1920
        self._custom_height = 1080
        self._custom_x = 0
        self._custom_y = 0

        # Default test pattern (bundled)
        bundled_pattern = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "resources", "grid_pattern.png"
        )
        if os.path.exists(bundled_pattern):
            self._last_pattern = bundled_pattern

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
        if 0 <= value < len(QGuiApplication.screens()):
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

    def _get_window(self, screen_index: int) -> VideoOutputWindow:
        if screen_index not in self._windows:
            win = VideoOutputWindow()
            win.set_target_screen(screen_index)
            self._windows[screen_index] = win
        return self._windows[screen_index]

    def video_widget_for(self, screen_index: int) -> QVideoWidget:
        win = self._get_window(screen_index)
        self._show_window(win, screen_index)
        return win.video_widget

    def _show_window(self, win: VideoOutputWindow, screen_index: int):
        if self.has_external_display:
            if self._output_mode == "custom":
                win.go_custom_windowed(
                    screen_index,
                    self._custom_width, self._custom_height,
                    self._custom_x, self._custom_y
                )
            else:
                win.go_fullscreen_on_screen(screen_index)
        else:
            win.show_as_window(self._custom_width, self._custom_height)

    def show_black_screen(self):
        for screen_index in range(self._screen_count):
            if screen_index > 0 or not self.has_external_display:
                self._get_window(screen_index)
                self._show_window(self._windows[screen_index], screen_index)

    def force_hide(self):
        for win in self._windows.values():
            win.exit_fullscreen()
            win.hide()

    def close_all(self):
        if self._pattern_player:
            self._pattern_player.stop()
        for win in self._windows.values():
            win.exit_fullscreen()
            win.hide()
            win.close()
        self._windows.clear()

    def show_test_pattern(self, filepath: str):
        self._last_pattern = filepath
        target = self._output_screen_index
        win = self._get_window(target)
        self._show_window(win, target)

        if self._pattern_player is None:
            self._pattern_player = QMediaPlayer()
            self._pattern_audio = QAudioOutput()
            self._pattern_player.setAudioOutput(self._pattern_audio)
            self._pattern_audio.setVolume(0)

        self._pattern_player.setVideoOutput(win.video_widget)
        self._pattern_player.setSource(QUrl.fromLocalFile(filepath))
        self._pattern_player.setLoops(QMediaPlayer.Loops.Infinite)
        self._pattern_player.play()

    def stop_pattern(self):
        if self._pattern_player is not None:
            self._pattern_player.stop()

    def is_pattern_playing(self) -> bool:
        if self._pattern_player is not None:
            return self._pattern_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
        return False

    def has_test_pattern(self) -> bool:
        return self._last_pattern is not None

    def show_last_pattern(self):
        if self._last_pattern:
            self.show_test_pattern(self._last_pattern)

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
            return f"Video: Ext. Display {self._output_screen_index} (fullscreen)"
        return f"Video: Window {self._custom_width}x{self._custom_height}"

    @staticmethod
    def resolution_presets() -> dict:
        return RESOLUTION_PRESETS
