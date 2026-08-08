from __future__ import annotations

import json
import os
from copy import deepcopy
from .signal import Signal


class Configuration:
    def __init__(self, data: dict | None = None):
        self._data = data or {}
        self.changed = Signal()

    def get(self, path: str, default=None):
        keys = path.split(".")
        node = self._data
        for key in keys:
            if isinstance(node, dict) and key in node:
                node = node[key]
            else:
                return default
        return node

    def set(self, path: str, value):
        keys = path.split(".")
        node = self._data
        for key in keys[:-1]:
            if key not in node:
                node[key] = {}
            node = node[key]
        node[keys[-1]] = value
        self.changed.emit(path, value)

    def to_dict(self) -> dict:
        return deepcopy(self._data)

    def update(self, data: dict):
        self._data.update(data)


class JSONFileConfiguration(Configuration):
    def __init__(self, filepath: str, defaults: dict | None = None):
        super().__init__()
        self._filepath = filepath
        self._defaults = defaults or {}
        self.read()

    def read(self):
        if os.path.exists(self._filepath):
            with open(self._filepath, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        else:
            self._data = deepcopy(self._defaults)
            self.write()

    def write(self):
        os.makedirs(os.path.dirname(self._filepath), exist_ok=True)
        with open(self._filepath, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
