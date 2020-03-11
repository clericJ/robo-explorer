#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

DEFAULT_SQUARE_SIZE = 200
DEFAULT_ANIMATION_SPEED = 24  # frames per second
DEFAULT_MOVE_ANIMATION_SPEED = 1000 # ms
TILES_PATH = os.path.join(os.path.abspath(os.path.curdir), 'resource/tiles')
SPRITES_PATH = 'resource/sprites'
OVERLAYS_PATH = 'resource/overlays'
MAPS_PATH = os.path.join(os.path.abspath(os.path.curdir), 'maps')
NL_LITERAL = '\n'
TAB_LITERAL = '\t'
SPACE_LITERAL = ' '
MAIN_VIEW_INDEX = 0