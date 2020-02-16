#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from typing import Optional

from PySide2.QtCore import QObject, QRectF, QPointF, QPropertyAnimation, QEventLoop, Qt, QRect, Signal
from PySide2.QtGui import QPainter, QBrush, QTransform
from PySide2.QtWidgets import QGraphicsScene, QGraphicsItem, QGraphicsSceneMouseEvent, QGraphicsSceneHoverEvent, \
    QStyleOptionGraphicsItem, QWidget

import config
import models
import resources as rc
from core import Coordinate, Directions, UnitState
from graphics import SVGTile, AnimatedSprite


class Unit(AnimatedSprite):

    def __init__(self, model: models.Unit, size=config.DEFAULT_SQUARE_SIZE,
                 parent: Optional[QGraphicsItem] = None):
        super().__init__(parent)

        self.model = model
        self.model.moved.subscribe(self._move)
        self.model.turned.subscribe(self._turn)
        self._sprite_size = size

        self.setPos(model.x * size, model.y * size)
        self.load_states(self.model.name, 48, self._sprite_size)
        self.switch_state(UnitState.stand, None, self.model.direction)
        self.run_animation()

        self._moving_animation = QPropertyAnimation(self, bytearray('pos', 'utf-8'))
        self._moving_animation.setDuration(500)
        self._wait_loop = QEventLoop()
        self._moving_animation.finished.connect(self._wait_loop.quit)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._sprite_size, self._sprite_size)

    def _move(self, direction: Directions):
        if self._wait_loop.isRunning():
            print('running')
            self._moving_animation.stop()
            self._wait_loop.exit()

        self.switch_state(UnitState.move, None, direction)

        self._moving_animation.setStartValue(self.pos())
        self._moving_animation.setEndValue(QPointF(
            self.model.x * self._sprite_size,
            self.model.y * self._sprite_size))

        self._moving_animation.start()
        if not self._wait_loop.isRunning():
            self._wait_loop.exec_()

        self.switch_state(UnitState.stand, None, direction)

    def _turn(self, from_: Directions, to: Directions):
        return
        self.switch_state(UnitState.turn, from_, to)

        self.animation_loop_ended.connect(self._wait_loop.quit)
        self._wait_loop.exec_()
        self.animation_loop_ended.disconnect(self._wait_loop.quit)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() == Qt.LeftButton:
            print('unit')

class Cell(SVGTile):

    def __init__(self, model: models.Cell, tile: str, size=config.DEFAULT_SQUARE_SIZE,
                 parent: Optional[QGraphicsItem] = None):
        super().__init__(tile, parent)
        self.setAcceptHoverEvents(True)
        self.model = model
        self._size = size
        self._tile = tile
        self._hover_entered = False

    @property
    def element_size(self) -> int:
        return self._size

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._size, self._size)

    def __repr__(self) -> str:
        return f'views.Cell({self.model.surface.name})'

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        self._hover_entered = True
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        self._hover_entered = False
        super().hoverEnterEvent(event)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget):
        super().paint(painter, option, widget)
        if self._hover_entered:
            painter.save()
            painter.setRenderHint(painter.Antialiasing)
            if self.model.surface.passable:
                painter.setBrush(QBrush(config.PASSABLE_CELL_OVERLAY_COLOR))
            else:
                painter.setBrush(QBrush(config.IMPASSABLE_CELL_OVERLAY_COLOR))
            painter.setPen(Qt.NoPen)

            bounding_rect = self.boundingRect()
            rect = QRect(1, 1, bounding_rect.width() - 2, bounding_rect.height() - 2)
            painter.drawRoundedRect(rect, 10.0, 10.0)
            painter.restore()

class Field(QGraphicsScene):

    cell_activated = Signal(Coordinate)

    def __init__(self, model: models.Field, parent: Optional[QObject] = None):
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

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() == Qt.LeftButton:
            if item := self.itemAt(event.scenePos(), QTransform()):
                self.cell_activated.emit(item.model.position)

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        item = self.itemAt(event.scenePos(), QTransform())
        if item:
            pass
            #coord = self._translate_coordinates(item)
            #print(f'{coord.x}, {coord.y}')

        #print(f'move {self.itemAt(event.scenePos(), QTransform())}')
        super().mouseMoveEvent(event)

def test(argv):
    from PySide2.QtWidgets import QWidget, QApplication, QGridLayout, QGraphicsView, QPushButton

    class Window(QWidget):

        def __init__(self, parent=None):
            super().__init__(parent)

            self.setMouseTracking(True)
            field_model = models.Field(10, 10)
            field_model.load(open('maps/test.txt', 'r'))
            self.field_scene = Field(field_model, parent=self)
            self.field_scene.cell_activated.connect(self.move_to)

            self.scene_view = QGraphicsView(self)
            self.scene_view.setScene(self.field_scene)
            self.start_button = QPushButton('Start', self)
            self.start_button.clicked.connect(self.start_game)

            layout = QGridLayout()
            layout.addWidget(self.scene_view)
            layout.addWidget(self.start_button)

            self.red17 = Unit(models.Unit('red17', self.field_scene.model,
                Coordinate(0, 1), direction=Directions.east))

            self.field_scene.addItem(self.red17)
            self.setLayout(layout)

        def start_game(self):
            pass

        # FIXME проблема с кликом по области если движение уже началось
        def move_to(self, position: Coordinate):
            path = self.red17.model.get_path(position)

            if path:
                for next_step in path:
                    self.red17.model.move(next_step)


    app = QApplication(argv)
    window = Window()
    window.showMaximized()
    return app.exec_()

if __name__ == '__main__':
    sys.exit(test(sys.argv))
