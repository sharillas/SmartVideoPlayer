from __future__ import annotations

from typing import Type
from .cue import Cue
from .media_cue import MediaCue
from .command_cue import CommandCue
from .stop_all_cue import StopAllCue
from .collection_cue import CollectionCue
from .playlist_cue import PlaylistCue


class CueFactory:
    _factories: dict[str, Type[Cue]] = {}

    @classmethod
    def register(cls, cue_type: str, cue_class: Type[Cue]):
        cls._factories[cue_type] = cue_class

    @classmethod
    def create(cls, cue_type: str, **kwargs) -> Cue:
        cue_class = cls._factories.get(cue_type, MediaCue)
        return cue_class(**kwargs)

    @classmethod
    def available_types(cls) -> list[str]:
        return list(cls._factories.keys())

    @classmethod
    def from_dict(cls, data: dict) -> Cue:
        cue_type = data.get("_type_", "MediaCue")
        cue_class = cls._factories.get(cue_type, MediaCue)
        return cue_class.from_dict(data)


CueFactory.register("MediaCue", MediaCue)
CueFactory.register("CommandCue", CommandCue)
CueFactory.register("StopAllCue", StopAllCue)
CueFactory.register("CollectionCue", CollectionCue)
CueFactory.register("PlaylistCue", PlaylistCue)
