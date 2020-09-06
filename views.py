import math
from typing import Optional, Iterable, List

from PySide2.QtCore import QObject, QRectF, QPointF, QPropertyAnimation, Qt, Signal, QByteArray
from PySide2.QtGui import QPainter, QPixmap, QBrush, QTransform, QPainterPath
from PySide2.QtWidgets import QGraphicsItem, QGraphicsSceneHoverEvent, \
    QStyleOptionGraphicsItem, QWidget, QGraphicsScene, QGraphicsSceneMouseEvent

import config
import models
import overlays
import resources as rc
from core import Directions, UnitState, AutoDisconnector, Coordinate, Event
from graphics import Tile, AnimatedSprite

class Unit(AnimatedSprite):
    animation_ended = None

    def __init__(self, model: models.Unit, resource: str, controller, size, parent: Optional[QGraphicsItem]=None):
        super().__init__(parent)
        self.setFlag(Unit.ItemIsSelectable)

        self.model = model
        self.controller = controller
        self.animation_ended = Event()

        self.model.path_completed.subscribe(self._stand)
        self.model.turned.subscribe(self._turn)
        self.model.moved.subscribe(self._move)

        self.overlays = overlays.Map()
        self._sprite_size = size
        self._path_list: Optional[List[QPainterPath]] = []
        self._selected = False
        self._resource = resource

        self.setPos(model.x * size, model.y * size)
        self.load_states(self.resource, config.DEFAULT_ANIMATION_SPEED * model.speed.value, self._sprite_size)
        self._stand()

    @property
    def resource(self) -> str:
        return self._resource

    @property
    def element_size(self) -> int:
        return self._sprite_size

    @property
    def selected(self) -> bool:
        return self._selected

    def select(self):
        self.model.route_calculated.subscribe(self.draw_path)

        size = self.boundingRect().size()
        overlay = overlays.Pixmap(overlays.Names.cursor_selected, size, overlays.PaintOrder.prev)
        self.overlays.add(overlay)
        self._selected = True

    def clear_selection(self):
        if self._selected:
            self._selected = False
            self.overlays.remove(self.overlays.get(overlays.Names.cursor_selected))
            self.model.route_calculated.unsubscribe(self.draw_path)
            self.clear_path()

    def draw_path(self, start: Coordinate, finish: Coordinate, route: Iterable[Directions]):
        self.clear_path()
        path = self._get_graphic_path(start, finish, route)
        self._path_list.append(path)
        self.scene().add_unit_path(path)

    def clear_path(self):
        for path in self._path_list:
            self.scene().remove_unit_path(path)

        self._path_list = []

    def _get_graphic_path(self, start: Coordinate, finish: Coordinate, route: Iterable[Directions]) -> QPainterPath:
        def generate_half_size_rect(point):
            return QRectF(point.x() + self._sprite_size / 4, point.y() + self._sprite_size / 4,
                          self._sprite_size / 2, self._sprite_size / 2)

        start_point = QPointF(start.x * self._sprite_size, start.y * self._sprite_size)
        finish_point = QPointF(finish.x * self._sprite_size, finish.y * self._sprite_size)

        path = QPainterPath()
        path.addEllipse(generate_half_size_rect(start_point))

        prev_point = QPointF(start_point.x() + self._sprite_size/2,
                             start_point.y() + self._sprite_size/2)
        for step in route:
            next_point = QPointF(prev_point.x() + step.value.x * self._sprite_size,
                                 prev_point.y() + step.value.y * self._sprite_size)

            path.moveTo(prev_point)
            path.lineTo(next_point)
            prev_point = next_point

        path.addEllipse(generate_half_size_rect(finish_point))
        return path

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._sprite_size, self._sprite_size)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget]=None):
        self.overlays.draw(painter, overlays.PaintOrder.prev)
        super().paint(painter, option, widget)
        self.overlays.draw(painter, overlays.PaintOrder.post)

    def _move(self, direction: Directions):
        moving = QPropertyAnimation(self, QByteArray(bytes('pos', 'utf-8')), self)
        moving.setDuration(math.ceil(config.DEFAULT_MOVE_ANIMATION_SPEED / self.model.speed.value))
        moving.setStartValue(self.pos())
        moving.setEndValue(QPointF(self.model.x * self._sprite_size, self.model.y * self._sprite_size))
        moving.finished.connect(self.animation_ended.notify)

        moving.start(QPropertyAnimation.DeleteWhenStopped)
        self.animations.switch((UnitState.move, None, direction))

    def _turn(self, old: Directions, new: Directions):
        animation = self.animations.switch((UnitState.turn, old, new))
        AutoDisconnector(animation.finished, self.animation_ended.notify, self)

    def _stand(self):
        self.animations.switch((UnitState.stand, None, self.model.direction))
        self.clear_path()

class Cell(Tile):
    def __init__(self, model: models.Cell, size: int, parent: Optional[QGraphicsItem]=None):

        filename = config.SURFACE_NAME_TEMPLATE.format(model.surface.resource, model.surface.id)
        tile = QPixmap(rc.get_tile(filename)).scaledToHeight(size, mode=Qt.SmoothTransformation)
        super().__init__(tile, size, parent)

        self.setAcceptHoverEvents(True)
        self.overlays = overlays.Map()
        self.model = model

    def hoverEnterEvent(self, event: QGraphicsSceneHoverEvent):
        color = rc.PASSABLE_CURSOR_COLOR if self.model.passable else rc.IMPASSABLE_CURSOR_COLOR
        self.overlays.add(overlays.Backlight(color, self.boundingRect(), overlays.PaintOrder.post))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: QGraphicsSceneHoverEvent):
        self.overlays.remove_by_type(overlays.Backlight)
        super().hoverEnterEvent(event)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget]=None):
        self.overlays.draw(painter, overlays.PaintOrder.prev)
        super().paint(painter, option, widget)
        self.overlays.draw(painter, overlays.PaintOrder.post)

    def __repr__(self) -> str:
        return f'views.Cell({self.model.surface.name})'

class Field(QGraphicsScene):
    cell_activated = Signal(Cell)
    units_selected = Signal(list)
    selection_cleared = Signal()

    def __init__(self, model: models.Field, controller, elements_size: int, parent: Optional[QObject]=None):
        super().__init__(parent)
        self.setBackgroundBrush(QBrush(rc.FIELD_BACKGROUND_COLOR))

        self._units_path: List[QPainterPath] = []
        self._elements_size = elements_size
        self.controller = controller
        self.model = model

        self._load_cells()

    @property
    def elements_size(self):
        return self._elements_size

    def add_unit(self, unit: Unit):
        self.addItem(unit)

    def add_unit_path(self, path: QPainterPath):
        self._units_path.append(path)

    def remove_unit_path(self, path: QPainterPath):
        index = self._units_path.index(path)
        del self._units_path[index]

    def drawForeground(self, painter: QPainter, rect: QRectF):
        painter.setRenderHint(painter.Antialiasing)
        painter.setPen(rc.PATH_PEN)

        for path in self._units_path:
            painter.drawPath(path)

        super().drawForeground(painter, rect)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent):
        if event.button() == Qt.LeftButton:
            if units := self.selectedItems():

                self.remove_selection()
                for unit in units:
                    unit.select()

                self.units_selected.emit(units)

            elif item := self.itemAt(event.scenePos(), QTransform()):
                if isinstance(item, Cell):
                    self.cell_activated.emit(item)

        elif event.button() == Qt.RightButton:
            self.remove_selection()

        super().mouseReleaseEvent(event)

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

                self.addItem(cell_view)
                cell_view.setPos(cell_view.element_size * x, cell_view.element_size * y)