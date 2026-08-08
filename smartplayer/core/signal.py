from __future__ import annotations

import weakref
from typing import Callable, Any


class Signal:
    def __init__(self):
        self._slots: list[tuple[int, weakref.ref, weakref.WeakMethod | None]] = []

    def connect(self, slot: Callable):
        if hasattr(slot, "__self__"):
            obj_id = id(slot.__self__)
            ref = weakref.ref(slot.__self__)
            method = weakref.WeakMethod(slot)
        else:
            obj_id = id(slot)
            ref = weakref.ref(slot)
            method = None
        self._slots.append((obj_id, ref, method))

    def disconnect(self, slot: Callable):
        slot_id = id(slot.__self__) if hasattr(slot, "__self__") else id(slot)
        self._slots = [s for s in self._slots if s[0] != slot_id]

    def emit(self, *args, **kwargs):
        active = []
        for obj_id, ref, method in self._slots:
            if ref() is None:
                continue
            active.append((obj_id, ref, method))
            if method is not None:
                fn = method()
                if fn is not None:
                    fn(*args, **kwargs)
            else:
                f = ref()
                if f is not None:
                    f(*args, **kwargs)
        self._slots = active
