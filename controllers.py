from typing import Optional, Iterable, List

import commands
import models
import views
from core import Coordinate


class Unit:
    def __init__(self, model: models.Unit):
        self._command_chain = commands.Chain()
        self.view: Optional[views.Unit] = None
        self.model = model

    def set_view(self, view: views.Unit):
        self.view = view

    def move(self, position: Coordinate, interrupt: bool = True):
        self._execute_commands([commands.UnitMove(self.model, position, self.view.animation_ended)], interrupt)

    def _execute_commands(self, command_list: Iterable, interrupt_next_commands: bool = True):
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
        self._active_units: List[views.Unit] = []
        self.view: Optional[views.Field] = None
        self.model = model

    def set_view(self, view: views.Field):
        view.units_selected.connect(self.set_active_units)
        view.cell_activated.connect(self.activate_cell)
        view.selection_cleared.connect(self.clear_active_units)
        self.view = view

    def add_unit(self, model: models.Unit, resource: str):
        controller = Unit(model)
        view = views.Unit(model, resource, controller, self.view.elements_size)
        controller.set_view(view)
        self.view.add_unit(view)

    def get_active_units(self) -> List[views.Unit]:
        return self._active_units

    def set_active_units(self, units: List[views.Unit]):
        self._active_units = units

    def clear_active_units(self):
        self._active_units = []

    def activate_cell(self, cell: views.Cell):
        for unit in self.get_active_units():
            unit.controller.move(cell.model.position)
