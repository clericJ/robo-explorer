import sys
from typing import Optional, Callable, Iterable

import config
import models
import views
import commands
from core import Coordinate

class Unit:
    def __init__(self, model: models.Unit):
        self.view: Optional[views.Unit] = None
        self.model = model
        self._command: Optional[commands.TriggerBasedNode] = None
        self._chain = commands.Chain()

    def set_view(self, view: views.Unit):
        self.view = view

    def move(self, position: Coordinate):
        self._execute_commands([lambda: self.model.step_to(position)])

    def _execute_commands(self, command_list: Iterable[Callable]):
        if self._chain.is_running():
            self._chain.interrupt()
        else:
            self._chain.clear()
        for command in command_list:
            node = commands.TriggerBasedNode(command, self.view.animation_ended)
            self._chain.add(node)

        if not self._chain.is_running():
            self._chain.execute()

class Field:
    def __init__(self, model: models.Field):
        self._selected_unit: Optional[views.Unit] = None
        self.view: Optional[views.Field] = None
        self.model = model

    def set_view(self, view: views.Field):
        view.unit_selected.connect(self._unit_selected)
        view.cell_activated.connect(self._cell_activated)
        view.selection_cleared.connect(self._clear_selection)
        self.view = view

    def add_unit(self, model: models.Unit):
        controller = Unit(model)
        view = views.Unit(model, controller, self.view.elements_size)
        controller.set_view(view)
        self.view.scene().addItem(view)

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
    from PySide2.QtWidgets import QWidget, QApplication, QGridLayout, QGraphicsScene

    class Window(QWidget):

        def __init__(self, parent=None):
            super().__init__(parent)

            self.setMouseTracking(True)
            field_model = models.Field(10, 10)
            field_model.load(open('maps/test.txt', 'r'))
            field_controller = Field(field_model)
            self.scene_view = views.Field(field_model, field_controller, config.DEFAULT_SQUARE_SIZE, parent=self)
            field_controller.set_view(self.scene_view)
            self.scene_view.setScene(QGraphicsScene())

            red17 = models.Unit('red17', self.scene_view.model, Coordinate(0, 1), models.Speed.medium)
            red17_2 = models.Unit('red17', self.scene_view.model, Coordinate(4, 4), models.Speed.medium)
            field_controller.add_unit(red17)
            #field_controller.add_unit(red17_2)

            layout = QGridLayout()
            layout.addWidget(self.scene_view)
            self.setLayout(layout)

    app = QApplication(argv)
    window = Window()
    window.showMaximized()

    # field_model = models.Field(10, 10)
    # field_model.load(open('maps/test.txt', 'r'))
    # field_controller = Field(field_model)
    # scene_view = views.Field(field_model, field_controller, config.DEFAULT_SQUARE_SIZE)
    # field_controller.set_view(scene_view)
    # scene_view.setScene(QGraphicsScene())
    #
    # red17 = models.Unit('red17',  scene_view.model, Coordinate(0, 1), models.Speed.medium)
    # red17_2 = models.Unit('red17', scene_view.model, Coordinate(4, 4), models.Speed.medium)
    # field_controller.add_unit(red17)
    # field_controller.add_unit(red17_2)
    #
    # scene_view.showMaximized()
    # scene_view.windowHandle().setFlags(Qt.FramelessWindowHint)
    # scene_view.windowHandle().showFullScreen()

    return app.exec_()

if __name__ == '__main__':
    sys.exit(test(sys.argv))
