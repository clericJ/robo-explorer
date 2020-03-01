#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from typing import Optional

from models import Directions
from core import UnitState
import config


def get_resource(path: str):
    result = os.path.normpath(path)
    if not os.path.isfile(result):
        raise FileNotFoundError('resource file "{result}" not found')

    return result

def get_tile(name: str) -> str:
    return get_resource(os.path.join(config.TILES_PATH, f'{name}.svg'))

def get_overlay(name: str):
    return get_resource(os.path.join(config.OVERLAYS_PATH, f'{name}.svg'))

def get_animated_sprite(name: str, state: UnitState,
                        from_: Optional[Directions], to: Directions) -> str:

    template = (f'{state.name}_{to.name}.png' if not from_
                else f'{state.name}_from_{from_.name}_to_{to.name}.png')

    result = os.path.normpath(os.path.join(config.SPRITES_PATH, f'{name}',
                                           'animated', template))

    if not os.path.isfile(result):
        raise FileNotFoundError(f'resource file "{result}" not found')

    return result

def test():
    print(get_tile('sand-001'))

if __name__ == '__main__':
    test()
