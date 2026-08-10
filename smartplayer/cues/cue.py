from __future__ import annotations

import uuid
from enum import IntFlag, Enum, auto
from ..core.has_properties import HasProperties
from ..core.properties import Property
from ..core.signal import Signal
from ..core.fader import Fader, FadeType


class CueState(IntFlag):
    Stop = 1
    Running = 2
    Pause = 4
    PreWait = 8
    PostWait = 16
    Error = 32

    IsRunning = Running | PreWait | PostWait
    IsPaused = Pause


class CueAction(Enum):
    Default = auto()
    Start = auto()
    Stop = auto()
    Pause = auto()
    Resume = auto()
    Interrupt = auto()
    FadeIn = auto()
    FadeOut = auto()
    FadeInStart = auto()
    FadeInResume = auto()
    FadeOutStop = auto()
    FadeOutPause = auto()
    FadeOutInterrupt = auto()
    DoNothing = auto()


class NextAction(Enum):
    NextCue = "NextCue"
    PreviousCue = "PreviousCue"
    StopEndOut = "StopEndOut"
    PauseKeepLast = "PauseKeepLast"
    Loop = "Loop"


class Cue(HasProperties):
    id = Property(default="")
    _type_ = Property(default="Cue")
    name = Property(default="New Cue")
    description = Property(default="")
    index = Property(default=0)
    pre_wait = Property(default=0.0)
    post_wait = Property(default=0.0)
    duration = Property(default=0)
    next_action = Property(default=NextAction.StopEndOut)
    fadein_type = Property(default=FadeType.Linear)
    fadeout_type = Property(default=FadeType.Linear)
    fadein_duration = Property(default=500)
    fadeout_duration = Property(default=500)
    priority = Property(default=3)
    color = Property(default="")

    def __init__(self, cue_id: str | None = None, **kwargs):
        super().__init__(**kwargs)
        if self.id == "":
            self.id = cue_id or str(uuid.uuid4())
        if self._type_ == "Cue":
            self._type_ = type(self).__name__
        object.__setattr__(self, "_state", CueState.Stop)
        self.started = Signal()
        self.stopped = Signal()
        self.paused = Signal()
        self.interrupted = Signal()
        self.error = Signal()
        self.end = Signal()
        self.next = Signal()
        self._pre_wait_timer = None
        self._post_wait_timer = None
        self._fade_timer = None

    @property
    def state(self) -> CueState:
        return self._state

    @state.setter
    def state(self, value: CueState):
        self._state = value
        self.changed.emit("state", value)

    def execute(self, action: CueAction = CueAction.Default):
        if action == CueAction.Default:
            if self.state in (CueState.Stop, CueState.Error):
                action = CueAction.Start
            elif self.state in CueState.IsRunning:
                action = CueAction.Stop
            elif self.state in CueState.IsPaused:
                action = CueAction.Resume

        action_map = {
            CueAction.Start: self._execute_start,
            CueAction.Stop: self._execute_stop,
            CueAction.Pause: self._execute_pause,
            CueAction.Resume: self._execute_resume,
            CueAction.Interrupt: self._execute_interrupt,
            CueAction.FadeIn: self._execute_fadein,
            CueAction.FadeOut: self._execute_fadeout,
        }

        handler = action_map.get(action, lambda: None)
        if self._pre_wait_timer is not None:
            self._kill_timer(self._pre_wait_timer)
            self._pre_wait_timer = None
        if self._post_wait_timer is not None:
            self._kill_timer(self._post_wait_timer)
            self._post_wait_timer = None
        handler()

    def _execute_start(self):
        if self.state in (CueState.Pause,):
            self._execute_resume()
            return
        if self.pre_wait > 0:
            self.state = CueState.PreWait
            self._schedule_prewait()
        else:
            self.__start__()

    def _schedule_prewait(self):
        from PySide6.QtCore import QTimer
        self._pre_wait_timer = QTimer()
        self._pre_wait_timer.setSingleShot(True)
        self._pre_wait_timer.timeout.connect(self.__start__)
        self._pre_wait_timer.start(int(self.pre_wait * 1000))

    def __start__(self):
        if self.fadein_duration > 0:
            self._start_fadein()
        self.state = CueState.Running
        self._do_start()
        self.started.emit()

    def _execute_stop(self):
        self._cancel_fade()
        if self.fadeout_duration > 0:
            self._start_fadeout_and_stop()
        else:
            self._do_stop()

    def _execute_pause(self):
        self._cancel_fade()
        if self.fadeout_duration > 0:
            self._start_fadeout_and_pause()
        else:
            self._do_pause()

    def _execute_resume(self):
        self._do_resume()
        self.started.emit()

    def _execute_interrupt(self):
        self._cancel_fade()
        self._do_stop()
        self.interrupted.emit()

    def _execute_fadein(self):
        self._start_fadein()

    def _execute_fadeout(self):
        self._cancel_fade()
        self._start_fadeout_only()

    def _do_start(self):
        pass

    def _do_stop(self):
        self.state = CueState.Stop
        self.stopped.emit()
        self._check_postwait_and_next()

    def _do_pause(self):
        self.state = CueState.Pause
        self.paused.emit()

    def _do_resume(self):
        self.state = CueState.Running

    def _check_postwait_and_next(self):
        if self.post_wait > 0:
            self.state = CueState.PostWait
            from PySide6.QtCore import QTimer
            self._post_wait_timer = QTimer()
            self._post_wait_timer.setSingleShot(True)
            self._post_wait_timer.timeout.connect(self._emit_end)
            self._post_wait_timer.start(int(self.post_wait * 1000))
        else:
            self._emit_end()

    def _emit_end(self):
        self.end.emit()
        if self.next_action == NextAction.Loop:
            self.next.emit()

    def _start_fadein(self):
        pass

    def _start_fadeout_and_stop(self):
        from PySide6.QtCore import QTimer
        self._fade_timer = QTimer()
        self._fade_timer.setSingleShot(True)
        self._fade_timer.timeout.connect(self._do_stop)
        self._fade_timer.start(self.fadeout_duration)

    def _start_fadeout_and_pause(self):
        from PySide6.QtCore import QTimer
        self._fade_timer = QTimer()
        self._fade_timer.setSingleShot(True)
        self._fade_timer.timeout.connect(self._do_pause)
        self._fade_timer.start(self.fadeout_duration)

    def _start_fadeout_only(self):
        from PySide6.QtCore import QTimer
        self._fade_timer = QTimer()
        self._fade_timer.setSingleShot(True)
        self._fade_timer.timeout.connect(self._on_fadeout_end)
        self._fade_timer.start(self.fadeout_duration)

    def _on_fadeout_end(self):
        pass

    def _cancel_fade(self):
        if self._fade_timer is not None:
            self._fade_timer.stop()
            self._fade_timer = None

    def _kill_timer(self, timer):
        try:
            timer.stop()
        except Exception:
            pass

    def to_dict(self) -> dict:
        data = {}
        for name, value in self.properties().items():
            if name in ("_type_", "id"):
                data[name] = value
            elif isinstance(value, Enum):
                data[name] = value.value
            elif isinstance(value, uuid.UUID):
                data[name] = str(value)
            elif name == "id":
                data[name] = str(value)
            else:
                data[name] = value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> Cue:
        cue = cls(cue_id=data.pop("id", None))
        for key, value in data.items():
            if key == "_type_":
                continue
            prop = getattr(type(cue), key, None)
            if isinstance(prop, Property):
                if isinstance(value, str):
                    try:
                        if prop.default is not None:
                            if isinstance(prop.default, Enum):
                                enum_type = type(prop.default)
                                value = enum_type(value)
                    except (ValueError, TypeError):
                        pass
                setattr(cue, key, value)
        return cue
