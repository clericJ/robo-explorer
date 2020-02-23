#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations
from enum import Enum
from typing import Iterable, Any, Iterator, Hashable, Optional

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
        self._listeners = []

    def subscribe(self, listener):
        if listener not in self._listeners:
            self._listeners.append(listener)

    def unsubscribe(self, listener) -> bool:
        result = True
        try:
            self._listeners.remove(listener)
        except ValueError:
            result = False
        return result

    def notify(self, *args):
        for listener in self._listeners:
            listener(*args)

class MutableIterator(Iterable):
    def __init__(self, sequence: Iterable=None):
        self._sequence = sequence if sequence is not None else ()
        self._index = 0

    def set(self, path: Iterable):
        self._sequence = path
        self._index = 0

    def is_empty(self) -> bool:
        return len(self._sequence) == 0

    def __next__(self) -> Any:
        try:
            item = self._sequence[self._index]
        except IndexError:
            self._sequence = ()
            raise StopIteration

        self._index += 1
        return item

    def __iter__(self) -> Iterator:
        return self

class StateMachine:
    switched = None # (previous: Any, next: Any)

    def __init__(self):
        self.switched = Event()
        self._current = None
        self._states = {}

    def add(self, state: Hashable, action: Any):
        self._states[state] = action

    def remove(self, state: Hashable):
        del self._states[state]

    def switch(self, state: Hashable) -> Any:
        previous = self.action()
        self._current = state
        self.switched.notify(previous, self.action())

        return self._states[state]

    def action(self) -> Any:
        if self._current:
            if self._current not in self._states:
                raise KeyError(f'Action for state: {self._current} not found')
            return self._states[self._current]

    def state(self) -> Optional[Hashable]:
        return self._current