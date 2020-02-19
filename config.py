#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from PySide2.QtGui import QColor

DEFAULT_SQUARE_SIZE = 80
DEFAULT_ANIMATION_SPEED = 24  # frames per second
DEFAULT_MOVE_ANIMATION_SPEED = 1000 # ms
TILES_PATH = os.path.join(os.path.abspath(os.path.curdir), 'resource/tiles')
SPRITES_PATH = 'resource/sprites'
OVERLAYS_PATH = 'resource/overlays'
MAPS_PATH = os.path.join(os.path.abspath(os.path.curdir), 'maps')
NL_LITERAL = '\n'
TAB_LITERAL = '\t'
SPACE_LITERAL = ' '

PASSABLE_CELL_OVERLAY_COLOR = QColor(50, 150, 50, 75)
IMPASSABLE_CELL_OVERLAY_COLOR = QColor(150, 0, 50, 75)
SELECTION_CURSOR_COLOR = QColor(255,255,255,200)