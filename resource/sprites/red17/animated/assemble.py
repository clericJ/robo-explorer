#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
from PySide2.QtCore import QSize, QPoint
from PySide2.QtWidgets import QApplication
from PySide2.QtGui import QPixmap, QPainter, QColor


def abs_path(directory: str) -> str:
    return os.path.join(os.path.abspath(os.curdir), directory)

def get_assembled_image_size(directory: str) -> QSize:
    files = os.listdir(directory)
    if files:
        picture = QPixmap(os.path.join(directory, files[0]))
        return QSize(picture.size().width() * len(files), picture.size().height())
    else:
        raise FileNotFoundError(f'image files not found in {directory} folder')

def assemble_image(path: str) -> QPixmap:
    assembled_image_size = get_assembled_image_size(path)
    assembled_image = QPixmap(assembled_image_size)
    assembled_image.fill(QColor(0,0,0,0))

    painter = QPainter()
    painter.begin(assembled_image)
    for i, image_file in enumerate(os.listdir(path)):
        image = QPixmap(os.path.join(path, image_file))
        painter.drawPixmap(QPoint(image.width() * i-1 ,0), image)


    painter.end()
    return assembled_image


def main(argv):
    app = QApplication(argv)
    for entry in os.listdir():
        if os.path.isdir(entry):
            path = abs_path(entry)
            result = assemble_image(path)
            result.save(f'{entry}.png', 'png')
            print(f'Animation "{entry}" assembled. Result in file "{entry}.png"')


    #return app.exec_()

if __name__ == '__main__':
    main(sys.argv)