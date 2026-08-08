from __future__ import annotations

import os
from typing import Any
from ..core.has_properties import HasProperties
from ..core.properties import Property
from ..core.fader import Fader, FadeType


class Media(HasProperties):
    uri = Property(default="")
    loop = Property(default=False)
    duration = Property(default=0)
    start_time = Property(default=0)
    stop_time = Property(default=0)
    volume = Property(default=1.0)

    def __init__(self, uri: str = "", **kwargs):
        super().__init__(**kwargs)
        self.uri = uri

    @property
    def name(self) -> str:
        return os.path.basename(self.uri) if self.uri else ""

    def to_dict(self) -> dict:
        return {
            "uri": self.uri,
            "loop": self.loop,
            "duration": self.duration,
            "start_time": self.start_time,
            "stop_time": self.stop_time,
            "volume": self.volume,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Media:
        return cls(**data)
