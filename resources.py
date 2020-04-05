import os
from typing import Optional

from PySide2.QtGui import QColor, QPen, QBrush, Qt

from models import Directions
from core import UnitState
import config

FIELD_BACKGROUND_COLOR = QColor(30, 30, 30)
PASSABLE_CURSOR_COLOR = QColor(100, 200, 100, 50)
IMPASSABLE_CURSOR_COLOR = QColor(150, 150, 150, 50)
PATH_PEN = QPen(QColor(255, 255, 255, 100), 10, Qt.SolidLine)
RUBBER_BAND_BRUSH = QBrush(QColor(100, 100, 100))

def get_resource(path: str) -> str:
    result = os.path.normpath(path)
    if not os.path.isfile(result):
        raise FileNotFoundError(f'resource file "{result}" not found')

    return result

def get_tile(name: str) -> str:
    return get_resource(os.path.join(config.TILES_PATH, f'{name}.svg'))

def get_overlay(name: str):
    return get_resource(os.path.join(config.OVERLAYS_PATH, f'{name}.svg'))

def get_animated_sprite(name: str, state: UnitState,
                        from_: Optional[Directions], to: Directions) -> str:

    template = (f'{state.name}_{to.name}.png' if not from_
                else f'{state.name}_from_{from_.name}_to_{to.name}.png')

    return get_resource(os.path.join(config.SPRITES_PATH, f'{name}',
                                           'animated', template))

def test():
    print(get_tile('sand-001'))

if __name__ == '__main__':
    test()
