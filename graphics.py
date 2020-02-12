from typing import Optional, Tuple, Dict

from PySide2.QtCore import QRect, QTimer, Qt, QPoint, Signal
from PySide2.QtGui import QPixmap, QPainter
from PySide2.QtSvg import QSvgRenderer
from PySide2.QtWidgets import QGraphicsItem, QWidget, QStyleOptionGraphicsItem, QGraphicsObject

import config
import resources as rc
from core import Directions, UnitState


class SVGTile(QGraphicsItem):

    def __init__(self, tile: str, parent: Optional[QGraphicsItem] = None):
        super().__init__(parent)
        self._tile = tile

        self.renderer = QSvgRenderer(tile)
        self.renderer.repaintNeeded.connect(lambda: self.update())

    @property
    def tile_filename(self) -> str:
        return self._tile

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget):
        self.renderer.render(painter, self.boundingRect())


class Animation:

    def __init__(self, sprite: QPixmap, frames_per_second: int = config.DEFAULT_ANIMATION_SPEED,
                 frame_number: int = 0, size=config.DEFAULT_SQUARE_SIZE, name=''):

        self._sprite = sprite.scaledToHeight(size, mode=Qt.SmoothTransformation)
        self._frame_count = self._sprite.width() / self._sprite.height()
        self._frames_per_second = frames_per_second
        self._current_frame = frame_number
        self._debug_name = name

    @property
    def frame_count(self) -> int:
        return self._frame_count

    @property
    def frames_per_second(self) -> int:
        return self._frames_per_second

    def reset(self):
        self._current_frame = 0

    @property
    def sprite(self) -> QPixmap:
        return self._sprite

    def get_current_frame(self) -> int:
        return self._current_frame

    def increment_frame(self):
        if self.this_last_frame():
            self._current_frame = 0
        else:
            self._current_frame += 1

    def this_last_frame(self) -> bool:
        return self._current_frame >= self._frame_count - 1

    def __repr__(self):
        return f'Animation({self._debug_name})' if self._debug_name else super().__repr__()


class AnimationState:
    def __init__(self, animations: Dict[Tuple[Optional[Directions], Directions], Animation],
                 state: UnitState):
        self._animations = animations
        self._state = state

    @property
    def state(self) -> UnitState:
        return self._state

    def get_animation(self, from_: Optional[Directions], to: Directions) -> Animation:
        return self._animations[(from_, to)]

    def __repr__(self):
        return f'AnimationState({self._state})'


class AnimatedSprite(QGraphicsObject):
    animation_loop_ended = Signal()

    def __init__(self, parent: Optional[QGraphicsItem] = None):
        super().__init__(parent)
        self._animation_states = {}
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self._update_frame)
        self._current = None

    @property
    def current_animation(self) -> Optional[Animation]:
        return self._current

    def is_running(self) -> bool:
        return self._animation_timer.isActive()

    def add_state(self, state: AnimationState):
        self._animation_states[state.state] = state

    def switch_state(self, state: UnitState, from_: Optional[Directions], to: Directions):
        self._current = self._animation_states[state].get_animation(from_, to)
        self._current.reset()

    def run_animation(self):
        if not self.is_running():
            self._animation_timer.start(int(1000 / self.current_animation.frames_per_second))

    def stop_animation(self):
        if self.is_running():
            self._animation_timer.stop()

    def load_states(self, name: str, frames_per_second: int, size: int):
        for state in UnitState:
            animations = {}
            for direction in Directions:
                if state.requires_prev_direction:
                    other_directions = set(Directions)
                    other_directions.discard(direction)
                    for from_ in other_directions:
                        animations[from_, direction] = Animation(QPixmap(
                            rc.get_animated_sprite(name, state, from_, direction)),
                            frames_per_second, size)
                else:
                    animations[None, direction] = Animation(QPixmap(
                        rc.get_animated_sprite(name, state, None, direction)),
                        frames_per_second, size)

            animation_state = AnimationState(animations, state)
            self.add_state(animation_state)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget):
        if self.current_animation:
            ssize = self.current_animation.sprite.height()
            x = ssize * self.current_animation.get_current_frame()

            painter.drawPixmap(QPoint(0, 0), self.current_animation.sprite,
                               QRect(x, 0, ssize, ssize))

    def _update_frame(self):
        if self.current_animation:
            if self.current_animation.this_last_frame():
                self.current_animation.reset()
                self.animation_loop_ended.emit()
            else:
                self.current_animation.increment_frame()
            self.update()

##class AnimatedSprite(QGraphicsObject):
##
##    def __init__(self, default: Animation=None, parent: Optional[QGraphicsItem]=None):
##        super().__init__(parent)
##
##        self._animation_timer = QTimer()
##        self._animation_timer.timeout.connect(self._update_frame)
##        self._animations = []
##        self._default = default
##        self._current = None
##
##    @property
##    def current_animation(self) -> Optional[Animation]:
##        return self._current
##
##    def add_animation(self, animation: Animation):
##        self._animations.append(animation)
##
##    def clear_animations_queue(self):
##        self._animations = []
##
##    def get_animations(self) -> Tuple[Animation]:
##        return ((self._current, ) if self._current else tuple()) + tuple(self._animations)
##
##    def switch_to_next_animation(self) -> bool:
##        self._current = (self._animations.pop(0) if len(self._animations) else None)
##        return self.current_animation is not None
##
##    def is_running(self) -> bool:
##        return self._animation_timer.isActive()
##
##    def run_animations(self):
##        if not self.is_running():
##            animation = (self.current_animation or self.switch_to_next_animation()
##                or self.get_default_animation())
##
##            if animation:
##                self._animation_timer.start(int(1000 / animation.frames_per_second))
##
##    def stop_animations(self):
##        if self.is_running():
##            self._animation_timer.stop()
##
##    def set_default_animation(self, animation: Animation):
##        self._default = animation
##
##    def get_default_animation(self) -> Optional[Animation]:
##        return self._default
##
##    def boundingRect(self) -> QRectF:
##        return QRectF(0,0, self._sprite.height(), self._sprite.height())
##
##    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget):
##        if self.current_animation:
##            ssize = self.current_animation.sprite.height()
##            x = ssize * self.current_animation.get_current_frame()
##
##            painter.drawPixmap(QPoint(0, 0), self.current_animation.sprite,
##                QRect(x, 0, ssize, ssize))
##
##    def _update_frame(self):
##        if self.current_animation or self.switch_to_next_animation():
##            if self.current_animation.this_last_frame():
##                if not self.switch_to_next_animation():
##                    if self._default:
##                        self._default.reset()
##                        self._current = self._default
##                    else:
##                        self.stop_animations()
##            else:
##                self.current_animation.increment_frame()
##            self.update()
