
from enum import Enum

from PySide2.QtCore import QSize
from PySide2.QtGui import QPixmap, QPainter

import resources as rc

class PaintOrder(Enum):
    prev = 0
    post = 1

class OverlayEnums:
    class Cursors(Enum):
        selected = 0
        move = 1
        target = 2

class Overlay:
    def __init__(self, resource: str, size: QSize, order: PaintOrder):
        self._sprite = QPixmap(rc.get_overlay(resource)).scaled(size.width(), size.height())
        self._order = order

    @property
    def order(self) -> PaintOrder:
        return self._order

    @property
    def sprite(self) -> QPixmap:
        return self._sprite

    def draw(self, painter: QPainter, x: int = 0, y: int = 0):
        painter.drawPixmap(x, y, self.sprite)

# Overlay(Cursors.selected.name, self.size(), Render.post)