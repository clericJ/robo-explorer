#!/usr/bin/env python
# -*- coding: utf-8 -*-

from typing import Optional

from PySide2.QtCore import QObject, QRectF, QPointF, QPropertyAnimation, QEventLoop, Qt, Signal, QByteArray
from PySide2.QtGui import QPainter, QTransform, QPixmap
from PySide2.QtWidgets import QGraphicsScene, QGraphicsItem, QGraphicsSceneMouseEvent, QGraphicsSceneHoverEvent, \
    QStyleOptionGraphicsItem, QWidget, QApplication

import config
import models
import overlays
import resources as rc
from core import Coordinate, Directions, UnitState
from graphics import SVGTile, AnimatedSprite

class Unit(AnimatedSprite):

    def __init__(self, model: models.Unit, size=config.DEFAULT_SQUARE_SIZE,
                 parent: Optional[QGraphicsItem] = None):
        super().__init__(parent)

        self.model = model
        self.model.moved.subscribe(self._move)
        self._sprite_size = size
        self._selected = False

        self.setPos(model.x * size, model.y * size)
        self.load_states(self.model.name, config.DEFAULT_ANIMATION_SPEED * model.speed.value, self._sprite_size)
        self.switch_state(UnitState.stand, None, self.model.direction)
        self.run_animation()

        self._moving_animation = QPropertyAnimation(self, QByteArray(bytes('pos', 'utf-8')))
        self._moving_animation.setDuration(config.DEFAULT_MOVE_ANIMATION_SPEED / model.speed.value)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._sprite_size, self._sprite_size)

    def select(self):
        self._selected = True

    def clear_selection(self):
        self._selected = False

    @property
    def selected(self) -> bool:
        return self._selected

    def _move(self, direction: Directions):
        self.switch_state(UnitState.move, None, direction)

        self._moving_animation.setStartValue(self.pos())
        self._moving_animation.setEndValue(QPointF(
            self.model.x * self._sprite_size,
            self.model.y * self._sprite_size))

        self._moving_animation.start()
        while self._moving_animation.state() == QPropertyAnimation.Running:
            QApplication.processEvents()

        self.switch_state(UnitState.stand, None, direction)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget):
        if self.selected:
            painter.setRenderHint(painter.Antialiasing)
            painter.drawPixmap(0, 0, QPixmap(rc.get_overlay(overlays.Cursors.selected_cursor.name)
                                            ).scaledToHeight(int(self.boundingRect().height())))
        super().paint(painter, option, widget)

class Cell(SVGTile):

    def __init__(self, model: models.Cell, tile: str, size=config.DEFAULT_SQUARE_SIZE,
                 parent: Optional[QGraphicsItem] = None):
        super().__init__(tile, parent)
        self.setAcceptHoverEvents(True)
        self._hover_entered = False
        self._size = size
        self._tile = tile
        self.model = model

    @property
    def element_size(self) -> int:
        return self._size

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._size, self._size)

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        self._hover_entered = True
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        self._hover_entered = False
        super().hoverEnterEvent(event)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget):
        super().paint(painter, option, widget)
        if not self._hover_entered:
            return

        painter.drawPixmap(0, 0, QPixmap(rc.get_overlay(overlays.Cursors.move_cursor.name)
                                        ).scaledToHeight(int(self.boundingRect().height())))

    def __repr__(self) -> str:
        return f'views.Cell({self.model.surface.name})'

class Field(QGraphicsScene):

    cell_activated = Signal(Coordinate)
    unit_selected = Signal(Coordinate)
    clear_selection = Signal()

    def __init__(self, model: models.Field, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.model = model

        for y in range(self.model.height):
            for x in range(self.model.width):
                cell_model = self.model.at(x, y)
                cell_view = Cell(cell_model, rc.get_tile(cell_model.surface.name))

                self.addItem(cell_view)
                cell_view.setPos(cell_view.element_size * x, cell_view.element_size * y)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() == Qt.LeftButton:
            if item := self.itemAt(event.scenePos(), QTransform()):
                if isinstance(item, Cell):
                    self.cell_activated.emit(item.model.position)
                elif isinstance(item, Unit):
                    item.select()
                    self.unit_selected.emit(item.model.position)

        elif event.button() == Qt.RightButton:
            for item in self.items():
                if isinstance(item, Unit):
                    item.clear_selection()

            self.clear_selection.emit()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent):
        item = self.itemAt(event.scenePos(), QTransform())
        if item:
            pass
            #coord = self._translate_coordinates(item)
            #print(f'{coord.x}, {coord.y}')

        #print(f'move {self.itemAt(event.scenePos(), QTransform())}')
        super().mouseMoveEvent(event)
