from __future__ import annotations

from typing import Any
from .properties import Property
from .signal import Signal


class HasProperties:
    def __init__(self, **kwargs):
        super().__init__()
        for name, value in kwargs.items():
            if hasattr(type(self), name):
                setattr(self, name, value)

    @property
    def changed(self) -> Signal:
        if not hasattr(self, "_changed_signal"):
            object.__setattr__(self, "_changed_signal", Signal())
        return self._changed_signal

    def properties(self) -> dict[str, Any]:
        result = {}
        for cls in type(self).__mro__:
            if cls is HasProperties or cls is object:
                break
            for attr_name in dir(cls):
                attr = getattr(cls, attr_name, None)
                if isinstance(attr, Property):
                    result[attr_name] = getattr(self, attr_name)
        return result

    def update_properties(self, props: dict[str, Any]):
        for name, value in props.items():
            if hasattr(type(self), name) and isinstance(getattr(type(self), name), Property):
                setattr(self, name, value)
