#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import io
import os
from enum import Enum
from typing import Optional, List
from abc import ABC, abstractproperty

import config
import surfaces
from core import Coordinate, Directions, Event

class HavingPosition(ABC):
    @abstractproperty
    def position(self) -> Coordinate:
        pass

    @abstractproperty
    def x(self) -> int:
        pass

    @abstractproperty
    def y(self) -> int:
        pass

class Speed(Enum):
    slow = 1
    medium = 2
    fast = 3

    def slow_down(self):
        return Speed.slow if self == Speed.medium else Speed.medium if self == Speed.fast else Speed.slow

    def speed_up(self):
        return Speed.fast if self == Speed.medium else Speed.medium if self == Speed.slow else Speed.fast

class Unit(HavingPosition):
    moved: Event = None  # (destination: Directions)
    turned: Event = None  # (from: Directions, to: Directions)
    route_calculated = None # (start: Coordinate, finish: Coordinate, route: Iterable)
    path_completed = None # ()

    def __init__(self, name: str, field: Field, position: Coordinate,
                 speed: Speed = Speed.medium, direction: Directions = Directions.east):
        self.moved = Event()
        self.turned = Event()
        self.route_calculated = Event()
        self.path_completed = Event()
        self._direction = direction
        self._position = position
        self._field = field
        self._speed = speed
        self._name = name

        self.field.at_point(position).put(self)

    @property
    def name(self) -> str:
        return self._name

    @property
    def x(self) -> int:
        return self._position.x

    @property
    def y(self) -> int:
        return self._position.y

    @property
    def position(self) -> Coordinate:
        return self._position

    @property
    def direction(self) -> Directions:
        return self._direction

    @property
    def speed(self) -> Speed:
        return self._speed

    @speed.setter
    def speed(self, speed: Speed):
        self._speed = speed

    def turn(self, direction: Directions):
        previous = self._direction
        if previous != direction:
            self._direction = direction
            self.turned.notify(previous, direction)

    @property
    def field(self) -> Field:
        return self._field

    def move(self, direction: Directions) -> bool:
        result = False

        new_position: Coordinate = self.position + direction.value
        destination: Cell = self.field.at_point(new_position)

        if destination and destination.passable:
            self.field.at_point(self.position).remove()
            destination.put(self)

            self._position = new_position
            if self._direction != direction:
                self.turn(direction)

            self.moved.notify(direction)
            result = True
        else:
            self.path_completed.notify()

        return result

    def step_to(self, destination: Coordinate) -> bool:
        result = False
        if path := self.get_path(destination):
            result = self.move(path[0])
        return result

    def get_path(self, destination: Coordinate) -> Optional[List[Directions]]:
        result = None
        map_ = []
        for y in range(self.field.width):
            map_.append([])
            for x in range(self.field.height):
                cell = self.field.at(x, y)
                map_[y].append(0 if cell.surface.passable and not cell.unit else -1)

        # начальная точка маршрута
        map_[self.y][self.x] = 1

        if (self.x != destination.x or self.y != destination.y) and self._find_path(map_, destination):
            result = self._generate_path(map_, destination)
            self.route_calculated.notify(self.position, destination, result)
        else:
            self.path_completed.notify()
        return result

    def _find_path(self, map_: List[List[int]], destination: Coordinate) -> bool:
        weight = 1
        for i in range(len(map_) * len(map_[0])):
            weight += 1

            for y in range(len(map_)):
                for x in range(len(map_[y])):
                    if map_[y][x] == (weight - 1):
                        if y > 0 and map_[y - 1][x] == 0:
                            map_[y - 1][x] = weight

                        if y < (len(map_) - 1) and map_[y + 1][x] == 0:
                            map_[y + 1][x] = weight

                        if x > 0 and map_[y][x - 1] == 0:
                            map_[y][x - 1] = weight

                        if x < (len(map_[y]) - 1) and map_[y][x + 1] == 0:
                            map_[y][x + 1] = weight

                        if (abs(y - destination.y) + abs(x - destination.x)) == 1:
                            map_[destination.y][destination.x] = weight
                            return True
        return False

    def _generate_path(self, map_: List[List], destination: Coordinate) -> List[Directions]:
        y = destination.y
        x = destination.x

        weight = map_[y][x]
        result = list(range(weight))
        while weight:
            weight -= 1
            if y > 0 and map_[y - 1][x] == weight:
                result[weight] = Directions.south
                y -= 1
            elif y < (len(map_) - 1) and map_[y + 1][x] == weight:
                result[weight] = Directions.north
                y += 1
            elif x > 0 and map_[y][x - 1] == weight:
                result[weight] = Directions.east
                x -= 1
            elif x < (len(map_[y]) - 1) and map_[y][x + 1] == weight:
                result[weight] = Directions.west
                x += 1

        return result[1:]

class Cell(HavingPosition):
    placed: Event = None  # unit: Unit
    removed: Event = None  # unit: Unit

    def __init__(self, surface: surfaces.Surface, position: Coordinate):
        self.placed = Event()
        self.removed = Event()
        self._surface = surface
        self._position = position
        self._original_bot_speed = None
        self._bot = None

    @property
    def surface(self):
        return self._surface

    @property
    def is_occupied(self) -> bool:
        return self._bot is not None

    @property
    def x(self) -> int:
        return self._position.x

    @property
    def y(self) -> int:
        return self._position.y

    @property
    def position(self) -> Coordinate:
        return self._position

    @property
    def passable(self) -> bool:
        result = True
        if not self.surface.passable or self.is_occupied:
            result = False
        return result

    @property
    def unit(self) -> Optional[Unit]:
        return self._bot

    def put(self, unit: Unit):
        if self.is_occupied:
            raise ValueError

        if self.surface.speed != 0:
            self._original_bot_speed = unit.speed
            unit.speed = unit.speed.speed_up() if self.surface.speed > 0 else unit.speed.slow_down()

        self._bot = unit
        self.placed.notify(unit)

    def remove(self) -> Unit:
        if not self.is_occupied:
            raise ValueError

        unit = self._bot
        if self.surface.speed != 0:
            unit.speed = self._original_bot_speed

        self._bot = None
        self.removed.notify(unit)

        return unit

    def __repr__(self):
        return f'Cell({self.surface.name})'

class Field:
    def __init__(self, width: int, height: int):
        self._matrix = self._create_empty_matrix(width, height)
        self._width = width
        self._height = height

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def at(self, x: int, y: int) -> Optional[Cell]:
        if (0 <= x < self._width) and (0 <= y < self._height):
            return self._matrix[y][x]
        return None

    def at_point(self, point: Coordinate) -> Cell:
        return self.at(point.x, point.y)

    def load(self, stream: io.TextIO):
        lines = [l for l in stream]

        self._height = len(lines)
        self._width = len(lines[0].split(config.TAB_LITERAL))
        self._matrix = self._create_empty_matrix(self._width, self._height)

        for y, line in enumerate(lines):
            for x, cell_name in enumerate(line.split(config.TAB_LITERAL)):
                self._matrix[y][x] = Cell(surfaces.BY_NAME[cell_name.strip()], Coordinate(x, y))

    def dump(self, stream: io.TextIOBase):
        for y in range(self.height):
            stream.write(config.TAB_LITERAL.join(i.surface.name for i in self._matrix[y]))
            stream.write(config.NL_LITERAL)

    def _create_empty_matrix(self, width: int, height: int) -> List[List]:
        return [[Cell(surfaces.empty, Coordinate(i, j)) for i in range(width)] for j in range(height)]


def test():
    from PySide2.QtCore import QObject

    class BotView:

        direction_sprites = {
            Directions.south: 'v',
            Directions.north: '^',
            Directions.east: '>',
            Directions.west: '<'}

        def __init__(self, unit: Unit):
            self._unit = unit

        def get_sprite(self):
            return self.direction_sprites[self._unit.direction]

    class FieldView:

        def __init__(self, field: Field):
            self._field = field

        @property
        def field(self):
            return self._field

        def update(self):
            QObject().thread().usleep(1000 * 1000 * 1)
            os.system('cls')

            line = []
            for y in range(self.field.height):
                for x in range(self.field.width):
                    if self.field.at(x, y).is_occupied:
                        line.append(BotView.direction_sprites[self.field.at(x, y).unit.direction])
                    else:
                        line.append(str(int(not self.field.at(x, y).surface.passable)))

                print(config.SPACE_LITERAL.join(line))
                line.clear()

    os.system('cls')

    field = Field(10, 10)
    field_view = FieldView(field)
    # field.dump(open('maps/test.txt', 'w'))
    field.load(open('maps/test.txt', 'r'))

    player = Unit('player', field, Coordinate(0, 1))
    player.moved.subscribe(lambda x: print(f'moved to {x.name}'))
    player.turned.subscribe(lambda x, y: print(f'turned from {x.name} to {y.name}'))
    path = player.get_path(Coordinate(8, 5))

    field_view.update()
    if path:
        for next_step in path:
            player.move(next_step)
            field_view.update()
            # print(next_step)


if __name__ == '__main__':
    test()
