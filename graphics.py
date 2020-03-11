import math
from typing import Optional

from PySide2.QtCore import QRect, QTimer, Qt, QPoint, Signal, QObject, QRectF, QPointF, QTimeLine
from PySide2.QtGui import QPixmap, QPainter, QWheelEvent, QMouseEvent, QSurfaceFormat
from PySide2.QtOpenGL import QGL, QGLWidget, QGLFormat
from PySide2.QtSvg import QSvgRenderer
from PySide2.QtWidgets import QGraphicsItem, QWidget, QStyleOptionGraphicsItem, QGraphicsObject, QGraphicsView, \
    QOpenGLWidget

import resources as rc
from core import Directions, UnitState, StateMachine

class Tile(QGraphicsItem):
    def __init__(self, sprite: QPixmap, size, parent: Optional[QGraphicsItem]=None):
        super().__init__(parent)
        self.sprite = sprite
        self._size = size

    @property
    def element_size(self) -> int:
        return self._size

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._size, self._size)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget]=None):
        painter.setRenderHint(painter.SmoothPixmapTransform)
        painter.drawPixmap(QPoint(0, 0), self.sprite, QRect(0, 0, self._size, self._size))

class SVGTile(QGraphicsItem):
    def __init__(self, tile: str, parent: Optional[QGraphicsItem] = None):
        super().__init__(parent)
        self._tile = tile

        self.renderer = QSvgRenderer(tile)
        self.renderer.repaintNeeded.connect(self.update)

    @property
    def tile_filename(self) -> str:
        return self._tile

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget]=None):
        self.renderer.render(painter, self.boundingRect())

class FrameAnimation(QObject):
    frame_updated = Signal()
    finished = Signal()

    def __init__(self, sprite: QPixmap, frames_per_second: int, parent: Optional[QObject] = None):

        super().__init__(parent)
        self._sprite = sprite
        self._current_frame = 0
        self._frame_count = self._sprite.width() // self._sprite.height()
        self._frames_per_second = frames_per_second
        self._animation_timer = QTimer()
        self._animation_timer.setTimerType(Qt.PreciseTimer)
        self._animation_timer.timeout.connect(self._update_frame)

    @property
    def frame_count(self) -> int:
        return self._frame_count

    @property
    def frames_per_second(self) -> int:
        return self._frames_per_second

    @property
    def sprite(self) -> QPixmap:
        return self._sprite

    def get_current_frame(self) -> int:
        return self._current_frame

    def increment_frame(self):
        if self.is_last_frame():
            self.finished.emit()
            self._current_frame = 0
        else:
            self._current_frame += 1

    def is_last_frame(self) -> bool:
        return self._current_frame >= self._frame_count - 1

    def reset(self):
        self._current_frame = 0

    def is_running(self) -> bool:
        return self._animation_timer.isActive()

    def run(self, frame: int = 0, frames_per_second = None):
        if not self.is_running():
            self._current_frame = frame
            self._frames_per_second = frames_per_second or self.frames_per_second
            self._animation_timer.start(math.ceil(1000 / self.frames_per_second))

    def stop(self):
        if self.is_running():
            self._animation_timer.stop()

    def draw(self, painter: QPainter):
        size = self.sprite.height()
        x = size * self.get_current_frame()
        painter.setRenderHint(painter.SmoothPixmapTransform)
        painter.drawPixmap(QPoint(0, 0), self.sprite, QRect(x, 0, size, size))

    @classmethod
    def load(cls, name: str, state: UnitState, from_: Optional[Directions],
             to: Directions, frames_per_second: int, size: int):
        return cls(QPixmap(rc.get_animated_sprite(name, state, from_, to)
                    ).scaledToHeight(size, mode=Qt.SmoothTransformation), frames_per_second)

    def _update_frame(self):
        self.increment_frame()
        self.frame_updated.emit()

class AnimatedSprite(QGraphicsObject):

    def __init__(self, parent: Optional[QGraphicsItem] = None):
        super().__init__(parent)
        self.animations = StateMachine()
        self.animations.switched.subscribe(self._update_animations)

    @property
    def current_animation(self) -> Optional[FrameAnimation]:
        return self.animations.get_action()

    def load_states(self, name: str, frames_per_second: int, size: int):
        for state in UnitState:
            for direction in Directions:
                if state.requires_prev_direction:
                    other_directions = set(Directions)
                    other_directions.discard(direction)
                    for from_ in other_directions:
                        animation = FrameAnimation.load(name, state, from_, direction, frames_per_second, size)
                        self.animations.add((state, from_, direction), animation)
                else:
                    animation = FrameAnimation.load(name, state, None, direction, frames_per_second, size)
                    self.animations.add((state, None, direction), animation)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget]=None):
        if animation := self.animations.get_action():
            animation.draw(painter)

    def _update_animations(self, previous: Optional[FrameAnimation], next_: FrameAnimation):
        if previous:
            previous.frame_updated.disconnect(self.update)
            previous.stop()
        next_.frame_updated.connect(self.update)
        next_.run()

# TODO: переписать реализацию, отказаться от таймера слежения за мыщью
class CursorTrackedScrollGraphicsView(QGraphicsView):
    def __init__(self, parent: Optional[QWidget]=None):
        super().__init__(parent)

        self._visible_region: Optional[QRectF] = None
        self._mouse_position: Optional[QPointF] = None
        self._mouse_tracking_timer = QTimer()
        self._mouse_tracking_timer.timeout.connect(self._scroll_area)

    def _scroll_area(self):
        sensitive_area = 30 # in points

        hscroll = self.horizontalScrollBar()
        vscroll = self.verticalScrollBar()

        x, y = self._visible_region.x(), self._visible_region.y()
        width, height = self._visible_region.width(), self._visible_region.height()

        if self._mouse_position.x() >= width - width // sensitive_area:
            hscroll.setValue(hscroll.value() + -(width - self._mouse_position.x() - width // sensitive_area))

        if self._mouse_position.y() >= height - height // sensitive_area:
            vscroll.setValue(vscroll.value() + -(height - self._mouse_position.y() - height // sensitive_area))

        if self._mouse_position.x() - width // sensitive_area <= x:
            hscroll.setValue(hscroll.value() - -(self._mouse_position.x() - width // sensitive_area))

        if self._mouse_position.y() - height // sensitive_area <= y:
            vscroll.setValue(vscroll.value() - -(self._mouse_position.y() - height // sensitive_area))

    def mouseMoveEvent(self, event: QMouseEvent):
        self._mouse_position = event.pos()
        self._visible_region = QRectF(self.viewport().geometry())

        if not self._mouse_tracking_timer.isActive():
            self._mouse_tracking_timer.start(10)
        else:
            self._scroll_area()

        super().mouseMoveEvent(event)

class ScalableGraphicsView(QGraphicsView):
    def __init__(self, parent: Optional[QWidget]=None):
        super().__init__(parent)

        self.setResizeAnchor(QGraphicsView.NoAnchor)
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._scheduled_scalings = 0
        self._mouse_position = None

    def wheelEvent(self, event: QWheelEvent):
        self._mouse_position = event.pos()
        degrees = event.delta() / 8
        number_of_steps = degrees / 15
        
        self._scheduled_scalings += number_of_steps
        if self._scheduled_scalings * number_of_steps < 0:
            self._scheduled_scalings = number_of_steps

        timeline = QTimeLine(100, self)
        timeline.setUpdateInterval(10)
        timeline.valueChanged.connect(self._scale)

        timeline.start()

    def _scale(self, _: float):
        old = self.mapToScene(self._mouse_position)
        scale_factor = 1.0 + self._scheduled_scalings / 300.0

        factor = self.transform().scale(scale_factor, scale_factor).mapRect(QRectF(0, 0, 1, 1)).width()
        if 0.3 <= factor <= 1.4:
            self.scale(scale_factor, scale_factor)
            delta = self.mapToScene(self._mouse_position) - old
            self.translate(delta.x(), delta.y())

class UserControlledGraphicsView(CursorTrackedScrollGraphicsView, ScalableGraphicsView):
    pass

class OpenGLGraphicsView(QGraphicsView):
    def __init__(self, parent: Optional[QWidget]=None):
        super().__init__(parent)
        format_ = QSurfaceFormat()
        format_.setDepthBufferSize(24)
        format_.setStencilBufferSize(8)
        format_.setVersion(3, 2)
        format_.setProfile(QSurfaceFormat.CoreProfile)
        ogl_widget = QOpenGLWidget()
        ogl_widget.setFormat(format_)

        self.setViewport(ogl_widget)
        self.setViewportUpdateMode(UserControlledGraphicsView.FullViewportUpdate)

# QGLWidget помечен как устаревший но QOpenGLWidget тормозит на этой версии Qt
class OGLGraphicsView(QGraphicsView):
    def __init__(self, parent: Optional[QWidget]=None):
        super().__init__(parent)
        self.setViewport(QGLWidget(QGLFormat(QGL.SampleBuffers)))
        self.setViewportUpdateMode(UserControlledGraphicsView.FullViewportUpdate)

class GameGraphicsView(OGLGraphicsView, UserControlledGraphicsView):
    pass