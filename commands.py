import contextlib
from typing import Optional, List, Callable

from PySide2.QtCore import Signal, QObject

class TriggerBasedNode(QObject):
    finished = Signal()

    def __init__(self, action: Callable[[], bool], trigger: Signal, parent: Optional[QObject]=None):
        super().__init__(parent)
        self._connected = False
        self._interrupt = False
        self._trigger = trigger
        self._action = action

    def interrupt(self):
        self._interrupt = True

    def is_running(self) -> bool:
        return self._connected

    def execute(self):
        if self._connected:
            self._trigger.disconnect(self.execute)
            self._connected = False

        if self._interrupt:
            self._interrupt = False
            self.finished.emit()

        elif self._action():
            print('new_action')
            self._trigger.connect(self.execute)
            self._connected = True
        else:
            self.finished.emit()

class Chain:
    def __init__(self):
        self._commands: List[TriggerBasedNode] = []
        self._current_index = 0
        self._running = False

    def add(self, command: TriggerBasedNode):
        command.finished.connect(self._next)
        self._commands.append(command)

    def is_running(self) -> bool:
        return self._running

    def clear(self):
        self._current_index = 0
        self._commands = []

    def first(self) -> Optional[TriggerBasedNode]:
        with contextlib.suppress(LookupError):
            return self._commands[0]

    def last(self) -> Optional[TriggerBasedNode]:
        with contextlib.suppress(LookupError):
            return self._commands[-1]

    def current(self) -> Optional[TriggerBasedNode]:
        with contextlib.suppress(LookupError):
            return self._commands[self._current_index]

    def execute(self):
        if first := self.first():
            self._running = True
            first.execute()

    def interrupt(self):
        if current := self.current():
            if self._current_index + 1 < len(self._commands):
                index = self._commands.index(current)
                del self._commands[index+1:]
            current.interrupt()

    def _next(self):
        self.current().finished.disconnect(self._next)
        try:
            next_ = self._commands[self._current_index + 1]
            self._current_index += 1
            next_.execute()

        except LookupError:
            self._running = False