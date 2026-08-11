from __future__ import annotations

from .cue import Cue, CueState, CueAction, NextAction
from .media import Media
from ..core.properties import Property


class MediaCue(Cue):
    _type_ = Property(default="MediaCue")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._media = Media()
        self._player = None
        self._audio_output = None
        self._video_output = None
        self.currentPositionMs = 0

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
            self._player.positionChanged.connect(self._on_position_changed)
        if self.media.uri:
            self._player.setSource(QUrl.fromLocalFile(self.media.uri))

    def _do_start(self):
        self._setup_player()
        if self._player is not None:
            self._player.setPosition(0)
            self._player.play()
            if self.fadein_duration > 0 and self._audio_output is not None:
                from PySide6.QtCore import QPropertyAnimation, QEasingCurve
                target_vol = self._audio_output.volume()
                if target_vol <= 0:
                    target_vol = 0.8
                self._audio_output.setVolume(0)
                self._fadein_anim = QPropertyAnimation(self._audio_output, b"volume")
                self._fadein_anim.setDuration(self.fadein_duration)
                self._fadein_anim.setStartValue(0.0)
                self._fadein_anim.setEndValue(float(target_vol))
                self._fadein_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
                self._fadein_anim.start()

    def _do_stop(self):
        if self.fadeout_duration > 0 and self._audio_output is not None:
            from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QTimer
            target_vol = self._audio_output.volume()
            self._fadeout_anim = QPropertyAnimation(self._audio_output, b"volume")
            self._fadeout_anim.setDuration(self.fadeout_duration)
            self._fadeout_anim.setStartValue(float(target_vol))
            self._fadeout_anim.setEndValue(0.0)
            self._fadeout_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
            self._fadeout_anim.start()
            QTimer.singleShot(self.fadeout_duration + 50, self._stop_now)
        else:
            self._stop_now()

    def stop_immediate(self):
        """Stop without fade - for quick transitions"""
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
                self._player.pause()
                dur = self._player.duration()
                from PySide6.QtCore import QTimer
                QTimer.singleShot(50, lambda: self._player.setPosition(max(0, dur - 100)))
                self.state = CueState.Pause
                self.paused.emit()
                self.end.emit()
            else:
                self._do_stop()

    def _on_position_changed(self, position):
        self.currentPositionMs = position

    def set_volume(self, volume: float):
        if self._audio_output is not None:
            self._audio_output.setVolume(max(0.0, min(1.0, volume)))

    def to_dict(self) -> dict:
        return {**super().to_dict(), "media": self.media.to_dict()}

    @classmethod
    def from_dict(cls, data: dict) -> MediaCue:
        media_data = data.pop("media", {})
        cue = super().from_dict(data)
        cue.media = Media.from_dict(media_data)
        return cue
