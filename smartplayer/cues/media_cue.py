from __future__ import annotations

import logging
from .cue import Cue, CueState, CueAction, NextAction
from .media import Media
from ..core.properties import Property

log = logging.getLogger(__name__)


class MediaCue(Cue):
    _type_ = Property(default="MediaCue")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._media = Media()
        self._player = None
        self._audio_output = None
        self._video_output = None
        self.currentPositionMs = 0
        self._load_error = False
        self._elapsed_timer = None

    @property
    def media(self) -> Media:
        return self._media

    @media.setter
    def media(self, value: Media):
        self._media = value

    @property
    def player(self):
        return self._player

    @property
    def has_error(self) -> bool:
        return self._load_error

    def set_video_output(self, video_widget):
        self._video_output = video_widget
        try:
            if self._player is not None and video_widget is not None:
                self._player.setVideoOutput(video_widget)
        except Exception as e:
            log.error(f"setVideoOutput failed: {e}")

    # ─── Player setup with error handling ───

    def _setup_player(self):
        if self._player is not None:
            return
        if not self.media.uri:
            self._load_error = True
            log.warning(f"Cue '{self.name}': no media URI")
            return

        try:
            from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
            from PySide6.QtCore import QUrl
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
            self._player.errorOccurred.connect(self._on_player_error)
            self._player.setSource(QUrl.fromLocalFile(self.media.uri))
            self._load_error = False
        except Exception as e:
            log.error(f"Cue '{self.name}': player setup failed: {e}")
            self._load_error = True
            self._player = None

    def _on_player_error(self, error, error_string):
        log.error(f"Cue '{self.name}': playback error: {error_string}")
        self._load_error = True
        if self.state == CueState.Running:
            self._do_stop()

    # ─── State machine with explicit transitions ───

    def _do_start(self):
        try:
            self._setup_player()
        except Exception as e:
            log.error(f"Cue '{self.name}': _setup_player crashed: {e}")
            self._load_error = True
            return

        if self._player is None or self._load_error:
            log.warning(f"Cue '{self.name}': cannot start - player not ready")
            return

        try:
            self._player.setPosition(0)
            self._player.play()
            self._load_error = False

            # Frame-accurate timing - use QElapsedTimer
            from PySide6.QtCore import QElapsedTimer
            self._elapsed_timer = QElapsedTimer()
            self._elapsed_timer.start()

            # Audio fade in
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
        except Exception as e:
            log.error(f"Cue '{self.name}': start failed: {e}")
            self._load_error = True

    def _do_stop(self):
        try:
            if self.fadeout_duration > 0 and self._audio_output is not None:
                from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QTimer
                target_vol = self._audio_output.volume()
                self._fadeout_anim = QPropertyAnimation(self._audio_output, b"volume")
                self._fadeout_anim.setDuration(self.fadeout_duration)
                self._fadeout_anim.setStartValue(float(target_vol))
                self._fadeout_anim.setEndValue(0.0)
                self._fadeout_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
                self._fadeout_anim.start()
                QTimer.singleShot(self.fadeout_duration + 50, self._stop_player)
            else:
                self._stop_player()
        except Exception as e:
            log.error(f"Cue '{self.name}': stop fade failed: {e}")
            self._stop_player()

    def stop_immediate(self):
        """CasparCG-style: instant stop for transitions"""
        try:
            self._stop_player()
        except Exception:
            pass

    def _stop_player(self):
        try:
            if self._player is not None:
                self._player.stop()
        except Exception as e:
            log.error(f"Cue '{self.name}': player.stop() failed: {e}")
        finally:
            self._elapsed_timer = None
            super()._do_stop()

    def _do_pause(self):
        try:
            if self._player is not None:
                self._player.pause()
        except Exception as e:
            log.error(f"Cue '{self.name}': pause failed: {e}")
        super()._do_pause()

    def _do_resume(self):
        try:
            if self._player is not None:
                self._player.play()
        except Exception as e:
            log.error(f"Cue '{self.name}': resume failed: {e}")
        super()._do_resume()

    # ─── Media status with graceful handling ───

    def _on_media_status(self, status):
        try:
            from PySide6.QtMultimedia import QMediaPlayer
            if status == QMediaPlayer.MediaStatus.LoadedMedia:
                self._load_error = False
                self.duration = self._player.duration() or 0
            elif status == QMediaPlayer.MediaStatus.EndOfMedia:
                self._handle_end_of_media()
            elif status == QMediaPlayer.MediaStatus.InvalidMedia:
                log.warning(f"Cue '{self.name}': invalid media")
                self._load_error = True
        except Exception as e:
            log.error(f"Cue '{self.name}': media status error: {e}")

    def _handle_end_of_media(self):
        if self.media.loop or self.next_action == NextAction.Loop:
            try:
                self._player.setPosition(0)
                self._player.play()
            except Exception:
                self._do_stop()
        elif self.next_action == NextAction.PauseKeepLast:
            try:
                self._player.pause()
                dur = self._player.duration()
                from PySide6.QtCore import QTimer
                if dur > 100:
                    QTimer.singleShot(50, lambda: self._player.setPosition(max(0, dur - 100)))
            except Exception:
                pass
            self.state = CueState.Pause
            self.paused.emit()
            self.end.emit()
        else:
            self._do_stop()

    def _on_position_changed(self, position):
        self.currentPositionMs = position

    # ─── Volume control ───

    def set_volume(self, volume: float):
        try:
            if self._audio_output is not None:
                self._audio_output.setVolume(max(0.0, min(1.0, volume)))
        except Exception:
            pass

    # ─── Serialization ───

    def to_dict(self) -> dict:
        return {**super().to_dict(), "media": self.media.to_dict()}

    @classmethod
    def from_dict(cls, data: dict) -> MediaCue:
        media_data = data.pop("media", {})
        cue = super().from_dict(data)
        cue.media = Media.from_dict(media_data)
        return cue
