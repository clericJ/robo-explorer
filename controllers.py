import sys
from typing import Optional, Iterator, Callable, Iterable

from PySide2.QtCore import QObject, QTimer

import models
import views
from core import Coordinate, MutableIterator

class ActionChain(QObject):

    def __init__(self, action: Callable=None, data: Iterable=None):
        super().__init__()
        self._data = data
        self._action = action
        self._interrupt_flag = False

    def interrupt(self):
        self._interrupt_flag = True

    def set_data(self, data):
        self._data = data

    def set_action(self, action):
        self._action = action

    def run(self):
        try:
            self._action(next(self._data))
        except StopIteration:
            pass
        else:
            if not self._interrupt_flag:
                QTimer.singleShot(0, lambda : self.run())
            else:
                self._data = ()
                self._action = None

class Unit:

    def __init__(self, model: models.Unit):
        self._moving_path = MutableIterator()
        self.action = ActionChain()
        self._interrupt_flag = False
        self.model = model
        self.view = None

    def set_view(self, view: views.Unit):
        self.view = view

    def interrupt_action(self):
        self._interrupt_flag = True

    # FIXME: проблема с паралельной анимацией нескольких юнитов
    # вызванная тем что выполнение кода останавливается здесь
    # processEvents не может переключить выполнение на этот код
    def move(self, position: Coordinate):
        # если метод вызван во второй раз, во время того как не завершился первый вызов
        # путь меняется на текущий, второй вызов завершается, а первый отпрабатывает новый путь
        if path := self.model.get_path(position):
            first_call = self._moving_path.is_empty()
            self._moving_path.set(path)

            if first_call:
                ActionChain(self.model.move, self._moving_path).run()
                # for next_step in self._moving_path:
                #     if self._interrupt_flag:
                #         self._interrupt_flag = False
                #         break
                #
                #     self.model.move(next_step)

class Field:
    def __init__(self, model: models.Field):
        self._selected_unit = None
        self.model = model
        self.view = None

    def set_view(self, view: views.Field):
        view.unit_selected.connect(self._unit_selected)
        view.cell_activated.connect(self._cell_activated)
        view.selection_cleared.connect(self._clear_selection)
        self.view = view

    def add_unit(self, model: models.Unit):
        controller = Unit(model)
        view = views.Unit(model, controller)
        controller.set_view(view)
        self.view.addItem(view)

    def get_selected(self) -> Optional[views.Unit]:
        return self._selected_unit

    def _cell_activated(self, cell: views.Cell):
        if unit := self.get_selected():
            unit.controller.move(cell.model.position)

    def _unit_selected(self, unit: views.Unit):
        self._selected_unit = unit

    def _clear_selection(self):
        self._selected_unit = None

def test(argv):
    from PySide2.QtWidgets import QWidget, QApplication, QGridLayout, QGraphicsView

    class Window(QWidget):

        def __init__(self, parent=None):
            super().__init__(parent)

            self.setMouseTracking(True)
            field_model = models.Field(10, 10)
            field_model.load(open('maps/test.txt', 'r'))
            field_controller = Field(field_model)
            self.field_scene = views.Field(field_model, field_controller, parent=self)
            field_controller.set_view(self.field_scene)

            self.scene_view = QGraphicsView(self)
            self.scene_view.setScene(self.field_scene)

            red17 = models.Unit('red17', self.field_scene.model,
                                Coordinate(0, 1), models.Speed.middle)
            field_controller.add_unit(red17)
            red17_2 = models.Unit('red17', self.field_scene.model,
                                Coordinate(4, 4), models.Speed.middle)
            field_controller.add_unit(red17_2)

            layout = QGridLayout()
            layout.addWidget(self.scene_view)
            self.setLayout(layout)


    app = QApplication(argv)
    window = Window()
    window.showMaximized()
    return app.exec_()

if __name__ == '__main__':
    sys.exit(test(sys.argv))
