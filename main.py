#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
import random
from typing import Optional, Union
from enum import Enum
from pprint import pformat

from typing import Iterable, Callable
from PyQt5.QtWidgets import (QWidget, QApplication, QGraphicsScene, QGraphicsView,
    QMainWindow, QGraphicsItem)

from PyQt5.QtCore import (pyqtSignal, QRect, QObject, QRectF, QPoint,
    Qt, QTimer, QEvent)

from PyQt5.QtGui import QColor, QBrush, QPixmap, QPainter
from PyQt5.QtSvg import QSvgRenderer

from ui.gamewindow import Ui_GameWindow

import config
from animation import Sprite

DEFAULT_SQUARE_SIZE = 80

class Direction(Enum):
    NORTH   = 1
    SOUTH   = 2
    EAST    = 3
    WEST    = 4

class Surface:

    def __init__(self):
        raise RuntimeError('Class cannot be instantiated')

    passable: bool = NotImplemented
    name: str = NotImplemented


class EmptySurface(Surface):
    passable = False
    name     = 'empty'

class SandSurface(Surface):
    passable = True
    name     = 'sand'

class DuneSurface(Surface):
    passable = True
    name     = 'dune'

class RockSurface(Surface):
    passable = False
    name     = 'rock'

ALL_SURFACE_TYPES = (SandSurface, DuneSurface, RockSurface)


class SVGGraphicsObject(QGraphicsItem):
    ''' Унаследованный от QGraphicsItem класс, представляет базовый класс
        для графических элементов игры
        Отображает SVG графику и анимацию
    '''

    def __init__(self, tile: str, parent: Optional[QGraphicsItem]=None):
        ''' Конструктор
            tile - имя файла тайла формата svg
        '''
        super().__init__(parent)
        self._tile = tile

        self._svg_renderer = QSvgRenderer(os.path.join(config.TILES_PATH, tile))
        self._svg_renderer.repaintNeeded.connect(lambda: self.update())


    def paint(self, painter: QPainter, option, widget: QWidget):
        ''' Событие прорисовки (унаследованное)
        '''
        self._svg_renderer.render(painter, self.boundingRect())


class CellView(SVGGraphicsObject):
    ''' Элемент игрового поля, представляет из себя квадрат размера size*size
    '''

    def __init__(self, tile: str, surface=EmptySurface,
        size: int=DEFAULT_SQUARE_SIZE, parent: Optional[QGraphicsItem]=None):
        ''' Конструктор
            tile - имя файла формата svg
            size - размер квадрата
            surface - тип поверхности
        '''
        super().__init__(tile, parent)

        self._size = size
        self._surface = surface


    def boundingRect(self) -> QRectF:
        ''' Метод возвращает площать графического представления (унаследованное)
        '''
        return QRectF(0,0, self._size, self._size)


    @property
    def element_size(self) -> int:
        ''' Возвращает размер квадрата
        '''
        return self._size


    @property
    def surface(self) -> Surface:
        ''' Возвращает True если по квадрату возможно пройти, иначе False
        '''
        return self._surface


    def __repr__(self) -> str:
        ''' Возвращает X если квадрат не проходим или O если
            на квадрат можно наступать
        '''
        return self._surface.name[0]


class Bot:
    ''' Игровой персонаж управляемый игроком или компьютером
    '''

    def __init__(self, sprite: str, position: QPoint, direction: Direction=Direction.EAST):
        ''' Конструктор
        '''
        self._position = position
        self._direction = direction


    @property
    def x(self) -> int:
        ''' Возвращает значение координаты по горизонтали
        '''

    @property
    def y(self) -> int:
        ''' Возвращает значение координаты по вертикали
        '''

    @property
    def position(self) -> QPoint:
        ''' Возвращает позицию объекта
        '''

    @position.setter
    def position(self, coordinates: QPoint):
        ''' Установка позиции объекта
        '''

    @property
    def direction(self):
        ''' Свойство определяет направление в котором повёрнут персонаж
        '''
        return self._direction


    @direction.setter
    def direction(self, new):
        ''' Свойство определяет направление в котором повёрнут персонаж
        '''


    def move(self, field, direction: Direction) -> bool:
        ''' Передвижение бота на один квадрат на поле field в направлении direction
            если перемещение успешно, возвращаемое значение True
            если перемещение в данном направлении
            по тем или иным причинам невозможно то False
        '''


class Map:
    ''' Игровое поле состаящее из квадратов
    '''

    def __init__(self, width: int, height: int, parent: QObject=None):
        ''' Конструктор
            width и height задают размер игрового поля
        '''
        self.scene = QGraphicsScene(parent)
        self.matrix = [[CellView('empty.svg') for i in range(0, width)] for j in range(0, height)]
        self._width = width
        self._height = height


    def fill(self, generator: Callable):
        ''' Заполнение поля квадратами, для всех квадратов на поле вызывается
            объект generator в который передаюся текущие координаты квадрата
            для заполнения а так же размерность поля. Возвращаемое значение
            вызываемого объекта должно быть объектом класса CellView, оно будет
            присвоено элементу матрицы с данными координатами
        '''

    def generate(self):
        ''' Заполнение поля случайными квадратами
        '''
        def rand_surface_and_tile() -> (str, Surface):
            tiles = {SandSurface: 'sand-001.svg', DuneSurface: 'dune-001.svg', RockSurface: 'rock-001.svg'}
            surface = ALL_SURFACE_TYPES[random.randrange(0, len(ALL_SURFACE_TYPES))]
            return (tiles[surface], surface)

        self.matrix = [[CellView( *rand_surface_and_tile() ) for i in range(0, self._width)] for j in range(0, self._height)]

        for x in range(0, self._width):
            for y in range(0, self._height):
                cell = self.matrix[y][x]
                self.scene.addItem(cell)
                cell.setPos(cell.element_size * x, cell.element_size * y)


    @property
    def width(self) -> int:
        ''' Возвращает ширину поля в квадратах
        '''
        return self._width


    @property
    def height(self) -> int:
        ''' Возвращает высоту поля в квадратах
        '''
        return self._height


    def update(self):
        ''' Обновление графического представления поля
            перерисовывает поле, нужно вызывать после действий с матрицей
        '''
        self.scene.update(self.scene.sceneRect())


    def __repr__(self):
        ''' Возвращает двухмерную матрицу
        '''
        return pformat(self.matrix)


class MainWindow(QMainWindow):

    def __init__(self, parent: Optional[QObject]=None):
        ''' Конструктор
        '''
        super().__init__(parent)
        self.ui = Ui_GameWindow()
        self.ui.setupUi(self)

        self.game_map = Map(10, 10, self)
        self.ui.mainSceneView.setScene(self.game_map.scene)
        self.game_map.generate()
        sprite = QPixmap('resource\\sprites\\red17\\animated\\walk_forward.png').scaledToHeight(DEFAULT_SQUARE_SIZE, mode=Qt.SmoothTransformation)
        self.bot_wait_anim = Sprite()
        self.bot_wait_anim.set_animation(sprite)
        self.bot_wait_anim.start()
        self.game_map.scene.addItem(self.bot_wait_anim)
        self.bot_wait_anim.setPos(10,10)

        self.startTimer(30)
        print(self.game_map)
        self.frame = 0

    def timerEvent(self, event):
        self.bot_wait_anim.setPos(self.frame, 10)
        self.frame += 3
        if self.frame > 1000:
            self.stopTimer()


class KeyFilter(QObject):
    ''' Фильтр событий предназначенный для перехвата нажатия клавиш
        и вызова соотвествующих сигналов
    '''
    # сигналы активируются при нажатии соотвествующей клавиши
    key_left_pressed = pyqtSignal()
    key_right_pressed = pyqtSignal()
    key_down_pressed = pyqtSignal()
    key_up_pressed = pyqtSignal()

    def __init__(self, parent: Optional[QObject]=None):
        ''' Конструктор
        '''
        super().__init__(parent)


    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        ''' Унаследованный метод, служит для перехвата событий
        '''
        keymap = {  Qt.Key_Left:  self.key_left_pressed,
                    Qt.Key_Right: self.key_right_pressed,
                    Qt.Key_Down:  self.key_down_pressed,
                    Qt.Key_Up: self.key_up_pressed}

        if event.type() == QEvent.KeyPress:
            if event.key() in keymap:
                keymap[event.key()].emit()
                return True

        return QObject.eventFilter(self, obj, event)


def main(argv):

    app = QApplication(argv)
    kfilter = KeyFilter()
    app.installEventFilter(kfilter)
    main_window = MainWindow()

    #kfilter.key_left_pressed.connect(main_window.move_figure_left)
    #kfilter.key_right_pressed.connect(main_window.move_figure_right)
    #kfilter.key_down_pressed.connect(main_window.move_figure_down)
    #kfilter.key_up_pressed.connect(main_window.rotate_figure)

    main_window.showMaximized()
    return app.exec_()


if __name__ == '__main__':
    sys.exit( main(sys.argv) )
