#!/usr/bin/env python
# -*- coding: utf-8 -*-
from typing import Optional

from PySide2.QtCore import QObject, QRectF, QPointF, QPropertyAnimation, Qt, Signal, QByteArray
from PySide2.QtGui import QPainter, QPixmap, QMouseEvent, QBrush
from PySide2.QtWidgets import QGraphicsItem, QGraphicsSceneHoverEvent, \
    QStyleOptionGraphicsItem, QWidget, QGraphicsScene

import config
import models
import resources as rc
from core import Directions, UnitState
from graphics import AnimatedSprite, Tile, UserControlledGraphicsView
from overlays import OverlayEnums


# TODO: придумать что нибудь с overlay

class Overlappable(AnimatedSprite):

    def set_overlay(self, overlay):
        self._overlays.append(overlay)

    def remove_overlay(self, overlay):
        index = self._overlays.index(overlay)
        del self._overlays[index]

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget]=None):
        prev = []
        post = []
        for overlay in self._overlays:
            if overlay.order == PaintOrder.prev:
                prev.append(overlay)
            else:
                post.append(overlay)

        for overlay in prev:
            overlay.draw(painter)

        super().paint(painter, option, widget)

        for overlay in post:
            overlay.draw(painter)

class Unit(AnimatedSprite):
    animation_ended = Signal()

    def __init__(self, model: models.Unit, controller, size, parent: Optional[QGraphicsItem] = None):
        super().__init__(parent)

        self.model = model
        self.controller = controller
        self.model.turned.subscribe(self._turn)
        self.model.moved.subscribe(self._move)
        self._sprite_size = size
        self._selected = False

        self.setPos(model.x * size, model.y * size)
        self.load_states(self.model.name, config.DEFAULT_ANIMATION_SPEED * model.speed.value, self._sprite_size)
        self.animations.switch((UnitState.stand, None, self.model.direction))
        self._moving: Optional[QPropertyAnimation] = None

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._sprite_size, self._sprite_size)

    def select(self):
        self._selected = True

    def clear_selection(self):
        self._selected = False

    @property
    def sprite_size(self):
        return self._sprite_size

    @property
    def selected(self) -> bool:
        return self._selected

    # привязать смену кадров анимации к действию (напрю изменению QPropertyAnimation)
    def _move(self, direction: Directions):
        self._moving = QPropertyAnimation(self, QByteArray(bytes('pos', 'utf-8')))
        self._moving.setDuration(config.DEFAULT_MOVE_ANIMATION_SPEED // self.model.speed.value)
        self._moving.setEndValue(QPointF(self.model.x * self._sprite_size, self.model.y * self._sprite_size))
        self._moving.setStartValue(self.pos())
        self._moving.finished.connect(self.animation_ended.emit)
        self._moving.finished.connect(lambda: self.animations.switch((UnitState.stand, None, self.model.direction)))
        self._moving.start(QPropertyAnimation.DeleteWhenStopped)
        self.animations.switch((UnitState.move, None, direction))

    def _turn(self, old: Directions, new: Directions):
        animation = self.animations.switch((UnitState.turn, old, new))
        animation.finished.connect(self.animation_ended.emit)
        animation.finished.connect(lambda: self.animations.switch((UnitState.stand, None, self.model.direction)))

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget]=None):
        if self.selected:
            painter.drawPixmap(0, 0, QPixmap(rc.get_overlay(OverlayEnums.Cursors.selected.name)
                                            ).scaledToHeight(int(self.boundingRect().height())))
        super().paint(painter, option, widget)

class Cell(Tile):
    def __init__(self, model: models.Cell, size, parent: Optional[QGraphicsItem] = None):

        tile = QPixmap(rc.get_tile(model.surface.name)).scaledToHeight(size, mode=Qt.SmoothTransformation)
        super().__init__(tile, size, parent)
        self.setAcceptHoverEvents(True)
        self._hover_entered = False
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

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget]=None):
        super().paint(painter, option, widget)
        if not self._hover_entered:
            return
        # painter.setPen(Qt.NoPen)
        # painter.setRenderHint(painter.Antialiasing)
        # painter.setBrush(QBrush(rc.PASSABLE_CURSOR_COLOR if self.model.passable else rc.IMPASSABLE_CURSOR_COLOR))
        # painter.drawRoundedRect(self.boundingRect(), 45, 45)

    def __repr__(self) -> str:
        return f'views.Cell({self.model.surface.name})'

class Field(UserControlledGraphicsView):
    cell_activated = Signal(Cell)
    unit_selected = Signal(Unit)
    selection_cleared = Signal()

    def __init__(self, model: models.Field, controller, elements_size: int, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.setBackgroundBrush(QBrush(rc.FIELD_BACKGROUND_COLOR))
        self._elements_size = elements_size
        self.controller = controller
        self.model = model

    @property
    def elements_size(self):
        return self._elements_size

    def setScene(self, scene: QGraphicsScene):
        super().setScene(scene)
        self._load_cells()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            if item := self.itemAt(event.pos()):
                if isinstance(item, Cell):
                    self.cell_activated.emit(item)

                elif isinstance(item, Unit):
                    self.remove_selection()
                    item.select()
                    self.unit_selected.emit(item)

        elif event.button() == Qt.RightButton:
            self.remove_selection()

        super().mouseReleaseEvent(event)

    # TODO: перенести оверлеи сюда
    def mouseMoveEvent(self, event: QMouseEvent):
        if item := self.itemAt(event.pos()):
            pass
        super().mouseMoveEvent(event)

    def remove_selection(self):
        cleared = False
        for item in self.items():
            if isinstance(item, Unit):
                if item.selected:
                    item.clear_selection()
                    cleared = True
        if cleared:
            self.selection_cleared.emit()

    def _load_cells(self):
        for y in range(self.model.height):
            for x in range(self.model.width):
                cell_model = self.model.at(x, y)
                cell_view = Cell(cell_model, self._elements_size)

                self.scene().addItem(cell_view)
                cell_view.setPos(cell_view.element_size * x, cell_view.element_size * y)