from dataclasses import dataclass

@dataclass
class Surface:
    passable: bool
    name: str
    id: int

empty = Surface(True, 'empty', 1)
sand = Surface(True, 'sand', 1)
dune = Surface(True, 'dune', 1)
rock = Surface(False, 'rock', 1)

ALL = (sand, dune, rock)
BY_NAME = {empty.name: empty,
           sand.name: sand,
           dune.name: dune,
           rock.name: rock}