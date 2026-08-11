from __future__ import annotations

import os
import json
import subprocess
import tempfile
import time

from .cue import Cue, CueState, CueAction, NextAction
from .media import Media
from ..core.properties import Property


MPV_EXE = os.environ.get("MPV_PATH", "C:/Program Files/MPV Player/mpv.exe")


def _vol(mpct: float) -> int:
    return max(0, min(100, int(mpct * 100)))


class MediaCue(Cue):
    _type_ = Property(default="MediaCue")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._media = Media()
        self._proc = None
        self._ipc = None
        self._wid = None
        self.currentPositionMs = 0

    @property
    def media(self) -> Media:
        return self._media

    @media.setter
    def media(self, value: Media):
        self._media = value

    @property
    def player(self):
        return self

    def set_video_output(self, widget):
        self._wid = int(widget.winId()) if widget else None

    def _ipc_send(self, *args):
        if self._ipc is None:
            return
        try:
            cmd = {"command": list(args)}
            with open(self._ipc, 'w') as f:
                f.write(json.dumps(cmd) + '\n')
        except Exception:
            pass

    def _ipc_set(self, prop, value):
        self._ipc_send("set_property", prop, value)

    def _setup_player(self):
        if self._proc is not None or not self.media.uri or not os.path.exists(self.media.uri):
            return
        fd, self._ipc = tempfile.mkstemp(suffix='.ipc', prefix='svp_')
        os.close(fd)
        try:
            os.unlink(self._ipc)
        except OSError:
            pass
        cmd = [MPV_EXE, f'--input-ipc-server={self._ipc}', '--idle=yes',
               '--no-terminal', '--no-input-default-bindings', '--osc=no', '--osd-level=0']
        if self._wid:
            cmd.append(f'--wid={self._wid}')
        self._proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.3)

    def _do_start(self):
        self._setup_player()
        if self._proc is not None:
            vol = _vol(self.media.volume / 100.0 if self.media.volume > 1 else self.media.volume)
            self._ipc_send("loadfile", self.media.uri.replace('\\', '/'))
            self._ipc_set("loop-file", "inf" if self.media.loop else "no")
            if self.fadein_duration > 0:
                from PySide6.QtCore import QTimer
                steps, dur = 15, self.fadein_duration
                self._ipc_set("volume", 0)
                for i in range(1, steps + 1):
                    v = int(vol * i / steps)
                    QTimer.singleShot(i * (dur // steps), lambda v=v: self._ipc_set("volume", v))
            else:
                self._ipc_set("volume", vol)

    def _do_stop(self):
        if self._proc is not None:
            if self.fadeout_duration > 0:
                from PySide6.QtCore import QTimer
                cur = _vol(self.media.volume / 100.0 if self.media.volume > 1 else self.media.volume)
                steps, dur = 10, self.fadeout_duration
                for i in range(steps):
                    v = max(0, cur - int(cur * (i + 1) / steps))
                    QTimer.singleShot(i * (dur // steps), lambda v=v: self._ipc_set("volume", v))
                QTimer.singleShot(dur + 50, self._destroy_player)
            else:
                self._destroy_player()
        else:
            super()._do_stop()

    def _destroy_player(self):
        self._ipc_send("quit")
        self._proc = None
        try:
            if self._ipc:
                os.unlink(self._ipc)
        except OSError:
            pass
        self._ipc = None
        super()._do_stop()

    def _do_pause(self):
        self._ipc_send("set_property", "pause", True)
        super()._do_pause()

    def _do_resume(self):
        self._ipc_send("set_property", "pause", False)
        super()._do_resume()

    def set_volume(self, vol: float):
        self._ipc_send("set_property", "volume", _vol(vol))

    def to_dict(self) -> dict:
        return {**super().to_dict(), "media": self.media.to_dict()}

    @classmethod
    def from_dict(cls, data: dict) -> MediaCue:
        cue = super().from_dict(data)
        cue.media = Media.from_dict(data.pop("media", {}))
        return cue
