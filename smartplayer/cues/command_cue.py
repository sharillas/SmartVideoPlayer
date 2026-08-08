from __future__ import annotations

import subprocess
from ..cues.cue import Cue, CueAction
from ..core.properties import Property


class CommandCue(Cue):
    _type_ = Property(default="CommandCue")
    command = Property(default="")

    def _do_start(self):
        if self.command:
            try:
                subprocess.Popen(self.command, shell=True)
            except Exception:
                pass
        super()._do_start()

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["command"] = self.command
        return data

    @classmethod
    def from_dict(cls, data: dict) -> CommandCue:
        command = data.pop("command", "")
        cue = super().from_dict(data)
        cue.command = command
        return cue
