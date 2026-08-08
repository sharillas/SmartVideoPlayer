from __future__ import annotations

from enum import Enum
from typing import Callable
from math import log10, sqrt
from .signal import Signal


class FadeType(Enum):
    Linear = "Linear"
    Quadratic = "Quadratic"
    Exponential = "Exponential"
    Logarithmic = "Logarithmic"
    SCurve = "SCurve"


_fade_functions: dict[FadeType, Callable] = {}

def _register_fade(ftype: FadeType, fn: Callable):
    _fade_functions[ftype] = fn

def get_fade_function(ftype: FadeType) -> Callable:
    return _fade_functions.get(ftype, _fade_functions[FadeType.Linear])


_register_fade(FadeType.Linear, lambda t: t)
_register_fade(FadeType.Quadratic, lambda t: t * t)
_register_fade(FadeType.Exponential, lambda t: (2.71828 ** (t * log10(10))) / 10 if t > 0 else 0)
_register_fade(FadeType.Logarithmic, lambda t: log10(1 + 9 * t))
_register_fade(FadeType.SCurve, lambda t: t * t * (3 - 2 * t))


class Fader:
    def __init__(self, target, property_name: str, fade_type: FadeType = FadeType.Linear):
        self._target = target
        self._property_name = property_name
        self._fade_type = fade_type
        self._timer_id = None
        self._start_value = 0.0
        self._end_value = 1.0
        self._elapsed = 0
        self._duration = 0
        self._interval = 30
        self.finished = Signal()
        self._running = False

    def start(self, from_value: float, to_value: float, duration_ms: int):
        self.stop()
        self._start_value = from_value
        self._end_value = to_value
        self._elapsed = 0
        self._duration = duration_ms
        self._running = True
        self._timer_id = self._target.startTimer(self._interval)

    def stop(self):
        if self._timer_id is not None:
            self._target.killTimer(self._timer_id)
            self._timer_id = None
        self._running = False

    def timerEvent(self, event):
        if not self._running:
            return
        self._elapsed += self._interval
        progress = min(self._elapsed / self._duration, 1.0)
        curve_fn = get_fade_function(self._fade_type)
        curved = curve_fn(progress)
        value = self._start_value + (self._end_value - self._start_value) * curved
        setattr(self._target, self._property_name, value)
        if self._elapsed >= self._duration:
            setattr(self._target, self._property_name, self._end_value)
            self.stop()
            self.finished.emit()
