from __future__ import annotations

from .cue import Cue, CueState, CueAction, NextAction
from .media import Media
from ..core.properties import Property
from ..core.fader import FadeType


class MediaCue(Cue):
    _type_ = Property(default="MediaCue")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._media = Media()
        self._player = None
        self._audio_output = None
        self._video_output = None
        self._video_sink = None

    @property
    def media(self) -> Media:
        return self._media

    @media.setter
    def media(self, value: Media):
        self._media = value

    @property
    def player(self):
        return self._player

    def set_video_output(self, video_widget):
        self._video_output = video_widget
        if self._player is not None and video_widget is not None:
            self._player.setVideoOutput(video_widget)

    def _setup_player(self):
        from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
        from PySide6.QtCore import QUrl
        if self._player is None:
            self._player = QMediaPlayer()
            self._audio_output = QAudioOutput()
            self._player.setAudioOutput(self._audio_output)
            self._audio_output.setVolume(
                self.media.volume / 100.0 if self.media.volume > 1 else self.media.volume
            )
            if self._video_output is not None:
                self._player.setVideoOutput(self._video_output)
            self._player.mediaStatusChanged.connect(self._on_media_status)
            self._player.playbackStateChanged.connect(self._on_playback_state)
            self._player.positionChanged.connect(self._on_position_changed)
        if self.media.uri:
            self._player.setSource(QUrl.fromLocalFile(self.media.uri))

    def _do_start(self):
        self._setup_player()
        if self._player is not None:
            self._player.setPosition(0)
            self._player.play()
        # Reconnect position monitoring for PauseKeepLast
        try:
            self._player.positionChanged.disconnect(self._on_position_changed)
        except Exception:
            pass
        if self.next_action == NextAction.PauseKeepLast:
            self._player.positionChanged.connect(self._on_position_changed)

    def _do_stop(self):
        if self._player is not None:
            self._player.stop()
        super()._do_stop()

    def _do_pause(self):
        if self._player is not None:
            self._player.pause()
        super()._do_pause()

    def _do_resume(self):
        if self._player is not None:
            self._player.play()
        super()._do_resume()

    def _on_media_status(self, status):
        from PySide6.QtMultimedia import QMediaPlayer
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            loop_active = self.media.loop or self.next_action == NextAction.Loop
            keep_last = self.next_action == NextAction.PauseKeepLast
            if loop_active:
                self._player.setPosition(0)
                self._player.play()
            elif keep_last:
                # Already handled by position monitoring
                pass
            else:
                self._do_stop()

    def _on_position_changed(self, position):
        if self.next_action != NextAction.PauseKeepLast:
            return
        dur = self._player.duration()
        if dur > 0 and position >= dur - 150:
            self._player.pause()
            from PySide6.QtCore import QTimer
            QTimer.singleShot(50, lambda: self._player.setPosition(dur - 100))
            self.state = CueState.Pause
            self.paused.emit()
            self.end.emit()

    def _on_playback_state(self, state):
        pass

    def set_volume(self, volume: float):
        if self._audio_output is not None:
            self._audio_output.setVolume(max(0.0, min(1.0, volume)))

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["media"] = self.media.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> MediaCue:
        media_data = data.pop("media", {})
        cue = super().from_dict(data)
        cue.media = Media.from_dict(media_data)
        return cue
