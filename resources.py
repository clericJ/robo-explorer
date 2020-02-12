#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from models import Directions
from core import UnitState
import config


def get_tile(name: str) -> str:
    result = os.path.normpath(os.path.join(config.TILES_PATH, f'{name}.svg'))
    if not os.path.isfile(result):
        raise FileNotFoundError('resource file "{result}" not found')

    return result

def get_animated_sprite(name: str, state: UnitState, from_: Directions, to: Directions) -> str:
    template = (f'{state.name}_{to.name}.png' if not from_
                else f'{state.name}_from_{from_.name}_to_{to.name}.png')

    result = os.path.normpath(os.path.join(config.SPRITES_PATH, f'{name}',
                                           'animated', template))

    if not os.path.isfile(result):
        raise FileNotFoundError(f'resource file "{result}" not found')

    return result

##def get_animated_sprite(name: str, state: UnitState, direction: Directions) -> str:
##    result = os.path.normpath(os.path.join(config.SPRITES_PATH, f'{name}',
##        'animated', f'{state.name}_{direction.name}.png'))
##
##    if not os.path.isfile(result):
##        raise FileNotFoundError(f'resource file "{result}" not found')
##
##    return result

##def get_animated_turn_sprite(name: str, from_: Directions, to: Directions) -> str:
##    result = os.path.normpath(os.path.join(config.SPRITES_PATH, f'{name}',
##        'animated', f'turn_from_{from_.name}_to_{to.name}.png'))
##
##    if not os.path.isfile(result):
##        raise FileNotFoundError(f'resource file "{result}" not found')
##
##    return result


##def get_surface_tile(surface: Surface) -> Optional[str]:
##    result = os.path.normpath(os.path.join(config.TILES_PATH, f'{surface.name}.svg'))
##    if not os.path.isfile(result):
##        result = None
##
##    return result

def test():
    print(get_tile('sand-001'))

if __name__ == '__main__':
    test()
