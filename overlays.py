from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Tuple, Optional, Hashable

from PySide2.QtCore import QSize, QLineF, QRectF
from PySide2.QtGui import QPixmap, QPainter, Qt, QPicture, QColor, QBrush

import resources as rc
from core import Directions

IMMORTAL = -1


# TODO: возможно переписать оверлеи, отнаследовав их от QGraphicsEffect

class PaintOrder(Enum):
    prev = 0
    post = 1


class Names(Enum):
    cursor_selected = 0
    cursor_move = 1
    cursor_target = 2


@dataclass
class PathDirections:
    from_: Optional[Directions]
    to: Optional[Directions]


class Overlay(ABC):

    def __init__(self, order: PaintOrder, lifetime=IMMORTAL):
        self._lifetime = lifetime
        self._order = order

    @property
    @abstractmethod
    def id(self) -> Hashable:
        pass

    @property
    def order(self) -> PaintOrder:
        return self._order

    @property
    def lifetime(self) -> int:
        return self._lifetime

    @lifetime.setter
    def lifetime(self, value: int):
        if value != IMMORTAL and value < 0:
            raise ValueError

        self._lifetime = value

    def is_immortal(self) -> bool:
        return self._lifetime == IMMORTAL

    @abstractmethod
    def draw(self, painter: QPainter, x: int = 0, y: int = 0) -> bool:
        pass


class Backlight(Overlay):
    def __init__(self, color: QColor, rect: QRectF, order: PaintOrder, lifetime=IMMORTAL):
        super().__init__(order, lifetime)
        self._color = color
        self._rect = rect

    def id(self):
        return id(self)

    def draw(self, painter: QPainter, x: int = 0, y: int = 0) -> bool:
        result = False

        if self._lifetime == IMMORTAL or self._lifetime > 0:
            painter.setPen(Qt.NoPen)
            painter.setRenderHint(painter.Antialiasing)
            painter.setBrush(QBrush(self._color))
            painter.drawRoundedRect(self._rect, 45, 45)
            result = True

            if self._lifetime != IMMORTAL:
                self._lifetime -= 1

        return result


class Path(Overlay):
    def __init__(self, path: PathDirections, size: QSize, order: PaintOrder, lifetime=IMMORTAL):
        super().__init__(order, lifetime)
        self._path = path
        self._size = size
        self._picture = QPicture()
        self._paint_path()

    @property
    def id(self) -> Hashable:
        if self._path.to:
            if self._path.from_:
                result = self._path.from_.name + self._path.to.name
            else:
                result = self._path.to.name
        elif self._path.from_:
            result = self._path.from_.name
        else:
            raise ValueError('PathDirections empty')
        return result

    def draw(self, painter: QPainter, x: int = 0, y: int = 0) -> bool:
        result = False

        if self._lifetime == IMMORTAL or self._lifetime > 0:
            painter.drawPicture(0, 0, self._picture)
            result = True

            if self._lifetime != IMMORTAL:
                self._lifetime -= 1

        return result

    def _paint_path(self):
        width, height = self._size.width(), self._size.height()
        lines = {Directions.north: QLineF(width / 2, 0, width / 2, height / 2),
                 Directions.south: QLineF(width / 2, height, width / 2, height / 2),
                 Directions.east: QLineF(width, height / 2, width / 2, height / 2),
                 Directions.west: QLineF(0, height / 2, width / 2, height / 2)}

        painter = QPainter()
        painter.begin(self._picture)

        painter.setRenderHint(painter.Antialiasing)
        painter.setPen(rc.PATH_PEN)

        if self._path.from_:
            painter.drawLine(lines[self._path.from_])
        else:
            width, height = self._size.width(), self._size.height()
            painter.drawEllipse(width // 4, height // 4, width // 2, height // 2)
        if self._path.to:
            painter.drawLine(lines[self._path.to])
        else:
            width, height = self._size.width(), self._size.height()
            painter.drawEllipse(width // 4, height // 4, width // 2, height // 2)
        painter.end()


# class Cursor(QGraphicsEffect):
#
#     def __init__(self, resource: Names, parent: Optional[QObject]=None):
#         super().__init__(parent)
#         self._scaled = False
#         self._pixmap = QPixmap(rc.get_overlay(resource.name))
#
#     def draw(self, painter: QPainter):
#
#         if not self._scaled:
#             rect = self.sourceBoundingRect()
#             self._pixmap = self._pixmap.scaled(rect.width(), rect.height(), mode=Qt.SmoothTransformation)
#             self._scaled = True
#
#         self.drawSource(painter)
#         painter.drawPixmap(0, 0, self._pixmap)
#
#     def boundingRectFor(self, rect: QRectF):
#         return rect
#
# class Backlight(QGraphicsEffect):
#
#     def __init__(self, parent: Optional[QObject]=None):
#         super().__init__(parent)
#         self._color: Optional[QColor] = None
#
#     def set_color(self, color: QColor):
#         self._color = color
#
#     def draw(self, painter: QPainter):
#         self.drawSource(painter)
#
#         painter.save()
#         painter.setPen(Qt.NoPen)
#         painter.setBrush(QBrush(self._color))
#
#         painter.drawRoundedRect(self.sourceBoundingRect(), 45, 45)
#         painter.restore()
#
#     def boundingRectFor(self, rect: QRectF):
#         return rect

class Pixmap(Overlay):

    def __init__(self, resource: Names, size: QSize, order: PaintOrder, lifetime=IMMORTAL):
        super().__init__(order, lifetime)
        self._name = resource

        self._sprite = QPixmap(rc.get_overlay(
            resource.name)).scaled(size.width(), size.height(), mode=Qt.SmoothTransformation)

    @property
    def id(self) -> Hashable:
        return self._name

    @property
    def sprite(self) -> QPixmap:
        return self._sprite

    def draw(self, painter: QPainter, x: int = 0, y: int = 0) -> bool:
        result = False

        if self._lifetime == IMMORTAL or self._lifetime > 0:
            painter.drawPixmap(x, y, self.sprite)
            result = True

            if self._lifetime != IMMORTAL:
                self._lifetime -= 1

        return result


class Map:
    def __init__(self):
        self._overlays: Dict[Tuple[Hashable, PaintOrder], Overlay] = {}

    def add(self, overlay: Overlay) -> Hashable:
        key = (overlay.id, overlay.order)

        if key not in self._overlays:
            self._overlays[key] = overlay
        else:
            exist = self._overlays[key]
            if not exist.is_immortal():
                if not overlay.is_immortal():
                    exist.lifetime += overlay.lifetime
                else:
                    exist.lifetime = IMMORTAL
            elif not overlay.is_immortal():
                exist.lifetime = overlay.lifetime
        return key

    def get(self, overlay_id: Hashable, order: Optional[PaintOrder] = None) -> Optional[Overlay]:
        result = None
        if order:
            result = self._overlays.get((overlay_id, order))
        else:
            for order in PaintOrder:
                if (overlay_id, order) in self._overlays:
                    result = self._overlays[(overlay_id, order)]
                    break
        return result

    def remove(self, overlay: Overlay) -> bool:
        if overlay and (overlay.id, overlay.order) in self._overlays:
            del self._overlays[(overlay.id, overlay.order)]
            return True
        return False

    def remove_by_type(self, overlay_type: type(Overlay)):
        to_remove = []
        for overlay in self._overlays.values():
            if isinstance(overlay, overlay_type):
                to_remove.append(overlay)

        for overlay in to_remove:
            self.remove(overlay)

    def clear(self):
        self._overlays = {}

    def draw(self, painter: QPainter, order: PaintOrder):
        to_draw = []
        for overlay in self._overlays.values():
            if overlay.order == order:
                to_draw.append(overlay)

        for overlay in to_draw:
            if not overlay.draw(painter):
                self.remove(overlay)
