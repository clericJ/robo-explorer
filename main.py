import sys

from PySide2.QtWidgets import QApplication
import models, controllers, graphics, views
import config
from core import Coordinate


def main(argv):
    app = QApplication(argv)
    field_model = models.Field(10, 10)

    with open('maps/test3.txt', 'r') as fo:
        field_model.load(fo)

    field_controller = controllers.Field(field_model)

    main_view = graphics.GameGraphicsView()
    scene = views.Field(field_model, field_controller, config.DEFAULT_SQUARE_SIZE)
    field_controller.set_view(scene)
    main_view.setScene(scene)

    red17 = models.Unit('red17', scene.model, Coordinate(0, 1), models.Speed.medium)
    red17_2 = models.Unit('red17', scene.model, Coordinate(4, 4), models.Speed.fast)
    field_controller.add_unit(red17, 'red17')
    field_controller.add_unit(red17_2, 'red17')

    # main_view.showFullScreen()
    main_view.show()
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main(sys.argv))
