#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from typing import Optional
from PySide2.QtGui import QPixmap
from PySide2.QtCore import QObject, QRectF, QPointF, QPropertyAnimation, QTimer, QEventLoop
from PySide2.QtWidgets import QGraphicsScene, QGraphicsItem

import config
import models
import resources as rc
from core import Coordinate, Directions, UnitState
from graphics import SVGTile, AnimatedSprite

class Unit(AnimatedSprite):

    def __init__(self, model: models.Unit, size=config.DEFAULT_SQUARE_SIZE,
        parent: Optional[QGraphicsItem]=None):
        super().__init__(parent)

        self.model = model
        self.model.moved.subscribe(self._move)
        self.model.turned.subscribe(self._turn)
        self._sprite_size = size

        self.setPos(model.x * size, model.y * size)
        self.load_states(self.model.name, config.DEFAULT_ANIMATION_SPEED, self._sprite_size)
        self.switch_state(UnitState.stand, None, self.model.direction)
        self.run_animation()

        self._moving_animation = QPropertyAnimation(self, bytearray('pos', 'utf-8'))
        self._moving_animation.setDuration(1000)
        self._wait_loop = QEventLoop()
        self._moving_animation.finished.connect(self._wait_loop.quit)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._sprite_size, self._sprite_size)

    def _move(self, direction: Directions):
        self.switch_state(UnitState.move, None, self.model.direction)

        self._moving_animation.setStartValue(self.pos())
        self._moving_animation.setEndValue(QPointF(
            self.model.x * self._sprite_size,
            self.model.y * self._sprite_size))

        self._moving_animation.start()
        self._wait_loop.exec_()
        self.switch_state(UnitState.stand, None, self.model.direction)

    def _turn(self, from_: Directions, to: Directions):
        self.switch_state(UnitState.turn, from_, to)

        self.animation_loop_ended.connect(self._wait_loop.quit)
        self._wait_loop.exec_()
        self.animation_loop_ended.disconnect(self._wait_loop.quit)

class Cell(SVGTile):

    def __init__(self, model: models.Cell, tile: str, size=config.DEFAULT_SQUARE_SIZE,
        parent: Optional[QGraphicsItem]=None):

        super().__init__(tile, parent)
        self.model = model
        self._size = size
        self._tile = tile

    @property
    def element_size(self) -> int:
        return self._size

    def boundingRect(self) -> QRectF:
        return QRectF(0,0, self._size, self._size)

    def __repr__(self) -> str:
        return self.model.surface.name

class Field(QGraphicsScene):

    def __init__(self, model: models.Field, parent: Optional[QObject]=None):
        super().__init__(parent)
        self.model = model
        self._cell_matrix = []

        for y in range(self.model.height):
            self._cell_matrix.append([])
            for x in range(self.model.width):
                cell_model = self.model.at(x, y)
                tile = rc.get_tile(cell_model.surface.name)

                cell_view = Cell(cell_model, tile)
                self.addItem(cell_view)
                cell_view.setPos(cell_view.element_size * x, cell_view.element_size * y)

                self._cell_matrix[y].append(cell_view)

        def at(self, x: int, y: int) -> Optional[Cell]:
            return self._cell_matrix[y][x]

def test(argv):
    from PySide2.QtWidgets import QWidget, QApplication, QGridLayout, QGraphicsView, QPushButton

    class Window(QWidget):

        def __init__(self, parent=None):
            super().__init__(parent)
            field_model = models.Field(10,10)
            field_model.load(open('maps/test.txt', 'r'))
            self.field_scene = Field(field_model, parent=self)

            self.scene_view = QGraphicsView(self)
            self.scene_view.setScene(self.field_scene)
            self.start_button = QPushButton('Start', self)
            self.start_button.clicked.connect(self.start_game)

            layout = QGridLayout()
            layout.addWidget(self.scene_view)
            layout.addWidget(self.start_button)

            self.red17 = Unit(models.Unit('red17', self.field_scene.model,
                Coordinate(0,1), direction = Directions.east))

            self.field_scene.addItem(self.red17)
            self.setLayout(layout)

        def start_game(self):
            path = self.red17.model.get_path(Coordinate(7,9))

            if path:
                for next_step in path:
                    self.red17.model.move(next_step)

    app = QApplication(argv)
    window = Window()
    window.showMaximized()
    return app.exec_()

if __name__ == '__main__':
    sys.exit(test(sys.argv))
