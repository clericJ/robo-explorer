# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'gamewindow.ui'
#
# Created by: PyQt5 UI code generator 5.14.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_GameWindow(object):
    def setupUi(self, GameWindow):
        GameWindow.setObjectName("GameWindow")
        GameWindow.resize(896, 627)
        self.centralwidget = QtWidgets.QWidget(GameWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.mainSceneView = QtWidgets.QGraphicsView(self.centralwidget)
        self.mainSceneView.setAutoFillBackground(True)
        self.mainSceneView.setObjectName("mainSceneView")
        self.gridLayout.addWidget(self.mainSceneView, 1, 0, 1, 1)
        GameWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(GameWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 896, 25))
        self.menubar.setObjectName("menubar")
        GameWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(GameWindow)
        self.statusbar.setObjectName("statusbar")
        GameWindow.setStatusBar(self.statusbar)

        self.retranslateUi(GameWindow)
        QtCore.QMetaObject.connectSlotsByName(GameWindow)

    def retranslateUi(self, GameWindow):
        pass
