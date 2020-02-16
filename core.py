#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations
from enum import Enum

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
