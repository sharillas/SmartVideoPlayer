from __future__ import annotations

from .cue import Cue, CueAction
from .cue_model import CueModel
from ..core.properties import Property


class StopAllCue(Cue):
    _type_ = Property(default="StopAllCue")
    target_action = Property(default=CueAction.Stop)

    def __init__(self, cue_model: CueModel | None = None, **kwargs):
        super().__init__(**kwargs)
        self._cue_model = cue_model

    def set_cue_model(self, model: CueModel):
        self._cue_model = model

    def _do_start(self):
        if self._cue_model:
            self._cue_model.stop_all()
        super()._do_start()

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["target_action"] = self.target_action.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> StopAllCue:
        action_val = data.pop("target_action", "Stop")
        try:
            action = CueAction[action_val]
        except KeyError:
            action = CueAction.Stop
        cue = super().from_dict(data)
        cue.target_action = action
        return cue
