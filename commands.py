import contextlib
from typing import Optional, List, Callable, Any

from PySide2.QtCore import Signal, QObject

import models
from core import Coordinate

class Command(QObject):
    finished = NotImplemented

    def interrupt(self):
        raise NotImplementedError

    def execute(self):
        raise NotImplementedError

    def finish(self):
        raise NotImplementedError

class TriggerBased(Command):
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
            self.finish()

        elif self._action():
            self._trigger.connect(self.execute)
            self._connected = True
        else:
            self.finish()

    def finish(self):
        self.finished.emit()

class Waitable(Command):
    finished = Signal()

    def __init__(self, action: Callable[[Any], bool], waitable: Signal, *params, parent: Optional[QObject]=None):
        super().__init__(parent)
        self._connected = False
        self._waitable = waitable
        self._action = action
        self._params = params

    def execute(self):
        if self._connected:
            self._waitable.disconnect(self.finish)

        if self._action(*self._params):
            self._waitable.connect(self.finish)
            self._connected = True
        else:
            self.finish()

    def interrupt(self):
        pass

    def finish(self):
        if self._connected:
            self._waitable.disconnect(self.finish)
            self._connected = False

        self.finished.emit()

    def __repr__(self):
        return f'WaitableCommand({self._action}({self._params})'

class UnitMove(Command):
    finished = Signal()

    def __init__(self, unit: models.Unit, destination: Coordinate, animation_ended: Signal,
        parent: Optional[QObject]=None):

        super().__init__(parent)
        self._animation_ended = animation_ended
        self._destination = destination
        self._interrupt = False
        self._connected = False
        self._unit = unit

    def interrupt(self):
        self._interrupt = True

    def execute(self):
        if self._connected:
            self._animation_ended.disconnect(self.execute)
            self._connected = False

        if self._interrupt or self._unit.position.equals(self._destination):
            self._interrupt = False
            self.finish()

        elif path := self._unit.generate_path(self._destination):
            prev_direction = self._unit.direction
            new_direction = path[0]

            if prev_direction != new_direction:
                self._unit.turn(new_direction)
                self._animation_ended.connect(self.execute)
                self._connected = True

            elif self._unit.move(new_direction):
                self._animation_ended.connect(self.execute)
                self._connected = True
            else:
                self.finish()
        else:
            self.finish()

    def finish(self):
        self._unit.path_completed.notify()
        self.finished.emit()

    def __repr__(self):
        return f'UnitMoveCommand({self._unit}({self._destination})'

class Chain:
    def __init__(self):
        self._commands: List[Command] = []
        self._current_index = 0
        self._running = False

    def add(self, command: Command):
        command.finished.connect(self._next)
        self._commands.append(command)

    def is_running(self) -> bool:
        return self._running

    def clear(self):
        if self.is_running():
            self.interrupt()
            self._next()

        self._current_index = 0
        self._commands = []

    def first(self) -> Optional[Command]:
        with contextlib.suppress(LookupError):
            return self._commands[0]

    def last(self) -> Optional[Command]:
        with contextlib.suppress(LookupError):
            return self._commands[-1]

    def current(self) -> Optional[Command]:
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

    def __repr__(self):
        return f'CommandChain(running={self._running}, {self._commands})'