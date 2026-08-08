from __future__ import annotations

from typing import Any

from .cue import Cue, CueAction
from .cue_model import CueModel
from ..core.properties import Property


class CollectionCue(Cue):
    _type_ = Property(default="CollectionCue")
    target_ids = Property(default=[])
    target_action = Property(default=CueAction.Start)

    def __init__(self, cue_model: CueModel | None = None, **kwargs):
        super().__init__(**kwargs)
        self._cue_model = cue_model

    def set_cue_model(self, model: CueModel):
        self._cue_model = model

    def _do_start(self):
        if self._cue_model:
            for cue_id in self.target_ids:
                cue = self._cue_model.get(cue_id)
                if cue:
                    cue.execute(self.target_action)
        super()._do_start()

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["target_ids"] = self.target_ids
        data["target_action"] = self.target_action.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> CollectionCue:
        target_ids = data.pop("target_ids", [])
        action_val = data.pop("target_action", "Start")
        try:
            action = CueAction[action_val]
        except KeyError:
            action = CueAction.Start
        cue = super().from_dict(data)
        cue.target_ids = target_ids
        cue.target_action = action
        return cue
