from __future__ import annotations

from copy import deepcopy
from weakref import WeakKeyDictionary


class Property:
    def __init__(self, default=None):
        self.default = default
        self._values = WeakKeyDictionary()

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return self._values.get(instance, deepcopy(self.default))

    def __set__(self, instance, value):
        self._values[instance] = value
        instance.changed.emit(self.name, value)
