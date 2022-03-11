from __future__ import annotations

from enum import Enum
from typing import Any, Hashable, Optional, Callable, List, Generic, TypeVar

from PySide2.QtCore import QObject, Signal


class Coordinate:
    __slots__ = ('_x', '_y')

    def __init__(self, x: int, y: int):
        self._x = x
        self._y = y

    @property
    def x(self) -> int:
        return self._x

    @property
    def y(self) -> int:
        return self._y

    def equals(self, other: Coordinate) -> bool:
        return self._x == other.x and self._y == other.y

    def __add__(self, other: Coordinate):
        return Coordinate(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Coordinate):
        return Coordinate(self.x - other.x, self.y - other.y)

    def __mul__(self, other: Coordinate):
        return Coordinate(self.x * other.x, self.y * other.y)

    def __floordiv__(self, other: Coordinate):
        return Coordinate(self.x // other.x, self.y // other.y)

    def __div__(self, other: Coordinate):
        return Coordinate(int(self.x / other.x), int(self.y / other.y))

    def __repr__(self):
        return f'Coordinate({self.x}, {self.y})'


class Directions(Enum):
    north = Coordinate(0, -1)
    south = Coordinate(0, 1)
    east = Coordinate(1, 0)
    west = Coordinate(-1, 0)

    def __repr__(self):
        return self.name


class UnitState(Enum):
    # (id, requires_prev_direction flag)
    stand = (1, False)
    move = (2, False)
    turn = (3, True)  # при анимации необходимо знать из какого положения был поворот

    @property
    def requires_prev_direction(self):
        return self.value[1]

    def __repr__(self):
        return self.name


class Event:
    def __init__(self):
        self._listeners: List[Callable] = []

    def subscribe(self, listener: Callable):
        if listener not in self._listeners:
            self._listeners.append(listener)

    def unsubscribe(self, listener: Callable) -> bool:
        result = True
        try:
            self._listeners.remove(listener)
        except ValueError:
            result = False
        return result

    def notify(self, *args):
        for listener in self._listeners:
            listener(*args)


class StateMachine:
    switched = None  # (previous: Any, next: Any)

    def __init__(self):
        self.switched = Event()
        self._current = None
        self._states = {}

    def add(self, state: Hashable, action: Any):
        self._states[state] = action

    def remove(self, state: Hashable):
        del self._states[state]

    def switch(self, state: Hashable) -> Any:
        previous = self.get_action()
        self._current = state
        self.switched.notify(previous, self.get_action())

        return self._states[state]

    def get_action(self) -> Any:
        if self._current:
            if self._current not in self._states:
                raise KeyError(f'Action for state: {self._current} not found')
            return self._states[self._current]

    def state(self) -> Optional[Hashable]:
        return self._current


class AutoDisconnector(QObject):
    def __init__(self, finished: Signal, before: Callable, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._before = before
        self._finished_signal = finished
        self._finished_signal.connect(self.final)

    def final(self):
        self._before()
        self._finished_signal.disconnect(self.final)


T = TypeVar('T')


class Container(Generic[T]):
    placed = None  # T
    removed = None  # T

    def __init__(self):
        self._item: Optional[T] = None
        self.removed = Event()
        self.placed = Event()

    @property
    def item(self) -> Optional[T]:
        return self._item

    def is_empty(self) -> bool:
        return self._item is None

    def put(self, item: T):
        if self.item:
            raise ValueError

        self._item = item
        self.placed.notify(item)

    def remove(self) -> T:
        if not self._item:
            raise ValueError

        item = self._item
        self._item = None
        self.removed.notify(item)

        return item
