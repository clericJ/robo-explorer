from dataclasses import dataclass

@dataclass
class Surface:
    passable: bool
    name: str
    id: int

empty = Surface(True, 'empty', 1)
sand = Surface(True, 'sand', 2)
dune = Surface(True, 'dune', 3)
rock = Surface(False, 'rock', 4)

ALL = (sand, dune, rock)
BY_NAME = {empty.name: empty,
           sand.name: sand,
           dune.name: dune,
           rock.name: rock}