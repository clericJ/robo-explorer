import contextlib
from abc import ABC, abstractmethod
from typing import Optional, List, Callable, Any

import models
from core import Coordinate, Event

class Command(ABC):
    finished = NotImplemented

    @abstractmethod
    def interrupt(self):
        pass

    @abstractmethod
    def execute(self):
        pass

    @abstractmethod
    def finish(self):
        pass

class TriggerBased(Command):
    finished = None # ()

    def __init__(self, action: Callable[[], bool], trigger: Event):
        self.finished = Event()
        self._subscribed = False
        self._interrupt = False
        self._trigger = trigger
        self._action = action

    def interrupt(self):
        self._interrupt = True

    def is_running(self) -> bool:
        return self._subscribed

    def execute(self):
        if self._subscribed:
            self._trigger.unsubscribe(self.execute)
            self._subscribed = False

        if self._interrupt:
            self._interrupt = False
            self.finish()

        elif self._action():
            self._trigger.subscribe(self.execute)
            self._subscribed = True
        else:
            self.finish()

    def finish(self):
        self.finished.notify()

class Waitable(Command):
    finished = None # ()

    def __init__(self, action: Callable[[Any], bool], waitable: Event, *params):
        self.finished = Event()
        self._subscribed = False
        self._waitable = waitable
        self._action = action
        self._params = params

    def execute(self):
        if self._subscribed:
            self._waitable.unsubscribe(self.finish)

        if self._action(*self._params):
            self._waitable.subscribe(self.finish)
            self._subscribed = True
        else:
            self.finish()

    def interrupt(self):
        pass

    def finish(self):
        if self._subscribed:
            self._waitable.unsubscribe(self.finish)
            self._subscribed = False

        self.finished.notify()

    def __repr__(self):
        return f'WaitableCommand({self._action}({self._params})'

class UnitMove(Command):
    finished = None # ()

    def __init__(self, unit: models.Unit, destination: Coordinate, animation_ended: Event):
        self._animation_ended = animation_ended
        self._destination = destination
        self.finished = Event()
        self._interrupt = False
        self._subscribed = False
        self._unit = unit

    def interrupt(self):
        self._interrupt = True

    def execute(self):
        if self._subscribed:
            self._animation_ended.unsubscribe(self.execute)
            self._subscribed = False

        if self._interrupt or self._unit.position.equals(self._destination):
            self._interrupt = False
            self.finish()

        elif path := self._unit.generate_path(self._destination):
            prev_direction = self._unit.direction
            new_direction = path[0]

            if prev_direction != new_direction:
                self._unit.turn(new_direction)
                self._animation_ended.subscribe(self.execute)
                self._subscribed = True

            elif self._unit.move(new_direction):
                self._animation_ended.subscribe(self.execute)
                self._subscribed = True
            else:
                self.finish()
        else:
            self.finish()

    def finish(self):
        self._unit.path_completed.notify()
        self.finished.notify()

    def __repr__(self):
        return f'UnitMoveCommand({self._unit}({self._destination})'

class Chain:
    def __init__(self):
        self._commands: List[Command] = []
        self._current_index = 0
        self._running = False

    def add(self, command: Command):
        command.finished.subscribe(self._next)
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
        self.current().finished.unsubscribe(self._next)
        try:
            next_ = self._commands[self._current_index + 1]
            self._current_index += 1
            next_.execute()

        except LookupError:
            self._running = False

    def __repr__(self):
        return f'CommandChain(running={self._running}, {self._commands})'