from __future__ import annotations

import io
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, List

import config
import surfaces
from core import Coordinate, Directions, Event, Container


class HavingPosition(ABC):
    @property
    @abstractmethod
    def position(self) -> Coordinate:
        pass

    @property
    @abstractmethod
    def x(self) -> int:
        pass

    @property
    @abstractmethod
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
    route_calculated = None  # (start: Coordinate, finish: Coordinate, route: Iterable[Directions])
    path_completed = None  # ()

    def __init__(self, name: str, field: Field, position: Coordinate,
                 speed: Speed = Speed.medium, direction: Directions = Directions.east):
        self.moved = Event()
        self.turned = Event()
        self.route_calculated = Event()
        self.path_completed = Event()
        self._original_speed = speed
        self._direction = direction
        self._position = position
        self._field = field
        self._speed = speed
        self._name = name

        self.field.at_point(position).unit_container.put(self)

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
        turned = False
        previous = self._direction
        if previous != direction:
            self._direction = direction
            self.turned.notify(previous, direction)
            turned = True

        return turned

    @property
    def field(self) -> Field:
        return self._field

    def move(self, direction: Directions) -> bool:
        moved = False

        new_position: Coordinate = self.position + direction.value
        destination: Cell = self.field.at_point(new_position)

        if destination and destination.passable:
            self.field.at_point(self.position).unit_container.remove()
            self._speed = self._original_speed

            destination.unit_container.put(self)
            if destination.surface.speed != 0:
                self._speed = (self._speed.speed_up()
                               if destination.surface.speed > 0 else self._speed.slow_down())

            self._position = new_position
            self.moved.notify(direction)
            moved = True
        else:
            self.path_completed.notify()

        return moved

    def generate_path(self, destination: Coordinate) -> Optional[List[Directions]]:
        result = None
        map_ = []
        for y in range(self.field.width):
            map_.append([])
            for x in range(self.field.height):
                cell = self.field.at(x, y)
                map_[y].append(0 if cell.passable else -1)

        # начальная точка маршрута
        map_[self.y][self.x] = 1

        if self._find_path(map_, destination):
            result = self._generate_path(map_, destination)
            self.route_calculated.notify(self.position, destination, result)

        return result

    @staticmethod
    def _find_path(map_: List[List[int]], destination: Coordinate) -> bool:
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

    @staticmethod
    def _generate_path(map_: List[List], destination: Coordinate) -> List[Directions]:
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


class Structure:

    def __init__(self, name: str, place: List[Coordinate],
                 passable: bool, direction: Directions = Directions.east):

        self._start_pos: Optional[Coordinate] = None
        self._direction = direction
        self._passable = passable
        self._is_placed = False
        self._place = place
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def direction(self) -> Directions:
        return self._direction

    @property
    def passable(self) -> bool:
        return self._passable

    def is_placed(self):
        return self._is_placed

    def place(self, field: Field, position: Coordinate, direction: Directions) -> bool:
        if self._is_placed:
            raise ValueError

        result = False

        for point in self._place:
            cell = field.at_point(point + position)

            if not cell.can_build:
                break
        else:
            for point in self._place:
                cell = field.at_point(point + position)
                cell.struct_container.put(self)

            self._is_placed = True
            self._direction = direction
            self._start_pos = position
            result = True

        return result

    def destroy(self, field: Field) -> Optional[Item]:
        for point in self._place:
            cell = field.at_point(self._start_pos + point)
            cell.struct_container.remove()

        return None


class Item:

    def __init__(self, name: str, quantity: int = 1):
        self._quantity = quantity
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @property
    def quantity(self) -> int:
        return self._quantity


class Cell(HavingPosition):

    def __init__(self, surface: surfaces.Surface, position: Coordinate):
        super().__init__()
        self.struct_container: Container[Structure] = Container()
        self.unit_container: Container[Unit] = Container()
        self.item_container: Container[Item] = Container()
        self._position = position
        self._surface = surface

    @property
    def surface(self):
        return self._surface

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
        return (self.surface.passable
                and self.unit_container.is_empty()
                and (self.struct_container.is_empty() or not self.struct_container.item.passable))

    @property
    def can_build(self) -> bool:
        return (self.surface.type == surfaces.Type.hard
                and self.struct_container.is_empty()
                and self.item_container.is_empty()
                and self.unit_container.is_empty())

    def __repr__(self):
        return f'Cell({self.surface.resource})'


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
                name, id_ = cell_name.strip().split(config.SURFACE_NAME_DELIMITER)
                surface = surfaces.BY_RESOURCE_NAME[name]
                surface.id = int(id_)

                self._matrix[y][x] = Cell(surface, Coordinate(x, y))

    def dump(self, stream: io.TextIOBase):
        for y in range(self.height):
            stream.write(config.TAB_LITERAL.join(
                config.SURFACE_NAME_TEMPLATE.format(i.surface.name, i.surface.id) for i in self._matrix[y]))

            stream.write(config.NL_LITERAL)

    @staticmethod
    def _create_empty_matrix(width: int, height: int) -> List[List]:
        return [[Cell(surfaces.empty, Coordinate(i, j)) for i in range(width)] for j in range(height)]
