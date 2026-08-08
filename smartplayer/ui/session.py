from __future__ import annotations

import json
import os
from ..cues.cue_model import CueModel
from ..cues.cue_factory import CueFactory


class Session:
    def __init__(self, filepath: str | None = None):
        self._filepath = filepath
        self._cue_model = CueModel()
        self._layout_type = "ListLayout"
        self._version = "0.1.0"

    @property
    def cue_model(self) -> CueModel:
        return self._cue_model

    @property
    def filepath(self) -> str | None:
        return self._filepath

    def save(self, filepath: str | None = None):
        path = filepath or self._filepath
        if path is None:
            return
        self._filepath = path
        data = {
            "meta": {"version": self._version},
            "session": {"layout_type": self._layout_type},
            "cues": [cue.to_dict() for cue in self._cue_model.cues()],
        }
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self, filepath: str) -> bool:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return False

        self._filepath = filepath
        self._cue_model.clear()

        for cue_data in data.get("cues", []):
            cue = CueFactory.from_dict(cue_data)
            self._cue_model.add(cue)

        self._layout_type = data.get("session", {}).get("layout_type", "ListLayout")
        return True

    def close(self):
        self._cue_model.clear()
        self._filepath = None
