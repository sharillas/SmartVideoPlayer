from __future__ import annotations

from typing import Callable, Any


class UndoCommand:
    def __init__(self, text: str = ""):
        self._text = text or "Unknown"

    def undo(self):
        raise NotImplementedError

    def redo(self):
        raise NotImplementedError

    def description(self) -> str:
        return self._text


class UndoStack:
    def __init__(self, max_size: int = 100):
        self._undo_stack: list[UndoCommand] = []
        self._redo_stack: list[UndoCommand] = []
        self._max_size = max_size

    def push(self, command: UndoCommand):
        self._redo_stack.clear()
        self._undo_stack.append(command)
        if len(self._undo_stack) > self._max_size:
            self._undo_stack.pop(0)

    def undo(self) -> str:
        if self._undo_stack:
            cmd = self._undo_stack.pop()
            self._redo_stack.append(cmd)
            cmd.undo()
            return cmd.description()
        return ""

    def redo(self) -> str:
        if self._redo_stack:
            cmd = self._redo_stack.pop()
            self._undo_stack.append(cmd)
            cmd.redo()
            return cmd.description()
        return ""

    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def undo_text(self) -> str:
        if self._undo_stack:
            return f"Undo: {self._undo_stack[-1].description()}"
        return "Undo"

    def redo_text(self) -> str:
        if self._redo_stack:
            return f"Redo: {self._redo_stack[-1].description()}"
        return "Redo"

    def clear(self):
        self._undo_stack.clear()
        self._redo_stack.clear()


class LambdaCommand(UndoCommand):
    def __init__(self, text: str, undo_fn: Callable, redo_fn: Callable):
        super().__init__(text)
        self._undo_fn = undo_fn
        self._redo_fn = redo_fn

    def undo(self):
        self._undo_fn()

    def redo(self):
        self._redo_fn()
