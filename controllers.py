import sys
from typing import Optional, Iterable

import commands
import config
import models
import views
from core import Coordinate
from graphics import GameGraphicsView

class Unit:
    def __init__(self, model: models.Unit):
        self._command_chain = commands.Chain()
        self.view: Optional[views.Unit] = None
        self.model = model

    def set_view(self, view: views.Unit):
        self.view = view

    def move(self, position: Coordinate, interrupt: bool=True):
        self._execute_commands([commands.UnitMove(self.model, position, self.view.animation_ended)], interrupt)

    def _execute_commands(self, command_list: Iterable, interrupt_next_commands: bool=True):
        if self._command_chain.is_running() and interrupt_next_commands:
            self._command_chain.interrupt()
        else:
            self._command_chain.clear()
        for command in command_list:
            self._command_chain.add(command)

        if not self._command_chain.is_running():
            self._command_chain.execute()

class Field:
    def __init__(self, model: models.Field):
        self._active_unit: Optional[views.Unit] = None
        self.view: Optional[views.Field] = None
        self.model = model

    def set_view(self, view: views.Field):
        view.unit_selected.connect(self.set_active_unit)
        view.cell_activated.connect(self.activate_cell)
        view.selection_cleared.connect(self.clear_active_unit)
        self.view = view

    def add_unit(self, model: models.Unit):
        controller = Unit(model)
        view = views.Unit(model, controller, self.view.elements_size)
        controller.set_view(view)
        self.view.add_unit(view)

    def get_active_unit(self) -> Optional[views.Unit]:
        return self._active_unit

    def set_active_unit(self, unit: views.Unit):
        self._active_unit = unit

    def clear_active_unit(self):
        self._active_unit = None

    def activate_cell(self, cell: views.Cell):
        if unit := self.get_active_unit():
            unit.controller.move(cell.model.position)

def test(argv):
    from PySide2.QtWidgets import QApplication

    app = QApplication(argv)
    field_model = models.Field(10, 10)
    field_model.load(open('maps/test2.txt', 'r'))
    field_controller = Field(field_model)

    main_view = GameGraphicsView()
    scene = views.Field(field_model, field_controller, config.DEFAULT_SQUARE_SIZE)
    field_controller.set_view(scene)
    main_view.setScene(scene)

    red17 = models.Unit('red17',  scene.model, Coordinate(0, 1), models.Speed.medium)
    red17_2 = models.Unit('red17', scene.model, Coordinate(4, 4), models.Speed.medium)
    field_controller.add_unit(red17)
    field_controller.add_unit(red17_2)

    #main_view.showFullScreen()
    main_view.show()
    return app.exec_()

if __name__ == '__main__':
    sys.exit(test(sys.argv))
