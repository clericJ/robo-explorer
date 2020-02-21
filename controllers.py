import sys
from typing import Optional

from PySide2.QtCore import QObject

import models
import views
from core import Coordinate, MutableIterator

class Field(QObject):
    def __init__(self, model: models.Field,  parent: Optional[QObject] = None):
        super().__init__(parent)
        self._selected_unit = None
        self.model = model
        self.view = None

    def set_view(self, view: views.Field):
        view.unit_selected.connect(self._unit_selected)
        view.cell_activated.connect(self._cell_activated)
        view.clear_selection.connect(self._clear_selection)
        self.view = view

    def add_unit(self, unit: models.Unit):
        unit_view = views.Unit(unit)
        self.view.addItem(unit_view)

    def get_selected(self) -> Optional[views.Unit]:
        return self._selected_unit

    def _move_unit(self, position: Coordinate):
        self.__dict__.setdefault('_static_path', MutableIterator())
        unit = self.get_selected()

        if path := unit.get_path(position):
            not_empty = not self._static_path.is_empty()
            self._static_path.set(path)
            if not_empty:
                return

            for next_step in self._static_path:
                unit.move(next_step)

        # # TODO: переписать, реализовать прерывание текущего действия
        # if second_call:
        #     self._renew_path = True
        #     return
        #
        # if self._path:
        #     while True:
        #         for next_step in self._path:
        #             if self._renew_path:
        #                 self._renew_path = False
        #                 break
        #             unit.move(next_step)
        #         else:
        #             break
        #
        # self._path = []

    def _cell_activated(self, position: Coordinate):
        if self.get_selected():
            self._move_unit(position)

    def _unit_selected(self, position: Coordinate):
        self._selected_unit = self.model.at_point(position).unit

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
            self.field_scene = views.Field(field_model, parent=self)
            self.scene_view = QGraphicsView(self)
            self.scene_view.setScene(self.field_scene)

            self.controller = Field(field_model, self)
            self.controller.set_view(self.field_scene)
            red17 = models.Unit('red17', self.field_scene.model,
                                Coordinate(0, 1))
            self.controller.add_unit(red17)

            layout = QGridLayout()
            layout.addWidget(self.scene_view)

            self.setLayout(layout)

    app = QApplication(argv)
    window = Window()
    window.showMaximized()
    return app.exec_()

if __name__ == '__main__':
    sys.exit(test(sys.argv))
