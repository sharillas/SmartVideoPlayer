from __future__ import annotations

from collections import OrderedDict
from .cue import Cue, CueAction
from ..core.signal import Signal


class CueModel:
    def __init__(self):
        self._cues: OrderedDict[str, Cue] = OrderedDict()
        self.item_added = Signal()
        self.item_removed = Signal()
        self.model_reset = Signal()

    def __len__(self):
        return len(self._cues)

    def __iter__(self):
        return iter(self._cues.items())

    def __contains__(self, cue_id: str) -> bool:
        return cue_id in self._cues

    def __getitem__(self, cue_id: str) -> Cue:
        return self._cues[cue_id]

    def add(self, cue: Cue, index: int | None = None):
        if index is not None:
            items = list(self._cues.items())
            items.insert(index, (cue.id, cue))
            self._cues = OrderedDict(items)
            for i, (_, c) in enumerate(self._cues.items()):
                c.index = i
        else:
            cue.index = len(self._cues)
            self._cues[cue.id] = cue
        self.item_added.emit(cue.id)

    def remove(self, cue_id: str):
        if cue_id in self._cues:
            cue = self._cues[cue_id]
            cue.execute(CueAction.Stop)
            del self._cues[cue_id]
            for i, (_, c) in enumerate(self._cues.items()):
                c.index = i
            self.item_removed.emit(cue_id)

    def clear(self):
        for cue in list(self._cues.values()):
            cue.execute(CueAction.Stop)
        self._cues.clear()
        self.model_reset.emit()

    def get(self, cue_id: str) -> Cue | None:
        return self._cues.get(cue_id)

    def cues(self) -> list[Cue]:
        return list(self._cues.values())

    def ids(self) -> list[str]:
        return list(self._cues.keys())

    def cue_at(self, index: int) -> Cue | None:
        cues = list(self._cues.values())
        if 0 <= index < len(cues):
            return cues[index]
        return None

    def index_of(self, cue_id: str) -> int:
        return list(self._cues.keys()).index(cue_id) if cue_id in self._cues else -1

    def move(self, cue_id: str, new_index: int):
        if cue_id not in self._cues:
            return
        items = list(self._cues.items())
        old_index = self.index_of(cue_id)
        item = items.pop(old_index)
        items.insert(new_index, item)
        self._cues = OrderedDict(items)
        for i, (_, c) in enumerate(self._cues.items()):
            c.index = i

    def stop_all(self):
        for cue in self._cues.values():
            if cue.state in Cue.CueState.IsRunning or cue.state in Cue.CueState.IsPaused:
                cue.execute(CueAction.Stop)

    def update_indices(self):
        for i, (_, c) in enumerate(self._cues.items()):
            c.index = i
