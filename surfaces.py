from dataclasses import dataclass
from enum import Enum
from typing import Dict


class Type(Enum):
    quick = 1
    hard = 2

@dataclass(eq=True)
class Surface:
    name: str
    resource: str
    id: int
    type: Type
    passable: bool
    speed: int

empty = Surface(    name='empty', resource='empty',    id=1,   type=Type.quick,    passable=False, speed=0)
sand = Surface(     name='sand',  resource='sand',     id=1,   type=Type.quick,    passable=True,  speed=0)
dune = Surface(     name='dune',  resource='dune',     id=1,   type=Type.quick,    passable=True,  speed=-1)
rock = Surface(     name='rock',  resource='rock',     id=1,   type=Type.hard,     passable=False, speed=0)

ALL = (sand, dune, rock)

BY_RESOURCE_NAME: Dict[str, Surface] = {
    empty.resource: empty,
    sand.resource: sand,
    dune.resource: dune,
    rock.resource: rock}
