from typing import Optional

from PySide2.QtCore import QRect, QTimer, Qt, QPoint, Signal, QObject
from PySide2.QtGui import QPixmap, QPainter
from PySide2.QtSvg import QSvgRenderer
from PySide2.QtWidgets import QGraphicsItem, QWidget, QStyleOptionGraphicsItem, QGraphicsObject

import config
import resources as rc
from core import Directions, UnitState, StateMachine

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

    def __init__(self, sprite: QPixmap, frames_per_second: int = config.DEFAULT_ANIMATION_SPEED,
                 parent: Optional[QObject] = None):

        super().__init__(parent)
        self._sprite = sprite
        self._current_frame = 0
        self._frame_count = self._sprite.width() // self._sprite.height()
        self._frames_per_second = frames_per_second
        self._animation_timer = QTimer()
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
        if self.this_last_frame():
            self.finished.emit()
            self._current_frame = 0
        else:
            self._current_frame += 1

    def this_last_frame(self) -> bool:
        return self._current_frame >= self._frame_count - 1

    def reset(self):
        self._current_frame = 0

    def is_running(self) -> bool:
        return self._animation_timer.isActive()

    def run(self, frame: int = 0, frames_per_second = None):
        if not self.is_running():
            self._current_frame = frame
            self._frames_per_second = frames_per_second or self.frames_per_second
            self._animation_timer.start(1000 // self.frames_per_second)

    def stop(self):
        if self.is_running():
            self._animation_timer.stop()

    def draw(self, painter: QPainter):
        size = self.sprite.height()
        x = size * self.get_current_frame()
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
        return self.animations.action()

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
        if animation := self.animations.action():
            animation.draw(painter)

    def _update_animations(self, previous: Optional[FrameAnimation], next_: FrameAnimation):
        if previous:
            previous.frame_updated.disconnect(self.update)
            previous.stop()
        next_.frame_updated.connect(self.update)
        next_.run()
