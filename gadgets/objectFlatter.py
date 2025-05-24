#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2020/10/02 12:03 eske yoshinob[eske3g@gmail.com]
        update:2020/12/22 17:49 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2020 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3.tools import flatter
from gris3 import node

from gris3.uilib import directionPlane, mayaUIlib
from gris3 import uilib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

class VertexFlatter(directionPlane.DirectionScreen):
    r"""
        頂点を接続されたエッジの沿って、任意のフェース上に添わせる。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(VertexFlatter, self).__init__(parent)
        self.__camera = None

    def show(self):
        self.__camera = flatter.CameraInfo()
        if not self.__camera.isValid():
            return
        super(VertexFlatter, self).show()

    def execute(self, newVector, start, end, mouseButton, modifiers):
        r"""
            Args:
                newVector (list):
                start (QtCore.QPoint):
                end (QtCore.QPoint):
                mouseButton (int):
                modifiers (int):
        """
        if not self.__camera:
            return
        camera = self.__camera
        self.__camera = None
        with node.DoCommand():
            camera.flat(newVector, start, end)

def showFlatterContext():
    r"""
        フラットツールを起動し、そのGUIオブジェクトを返す。
        Returns:
            VertexFlatter:
    """
    w = VertexFlatter(mayaUIlib.MainWindow)
    w.show()
    return w    

class ObjectFlatter(QtWidgets.QWidget):
    r"""
        頂点をフラットにするための機能を提供するウィジェット。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ObjectFlatter, self).__init__(parent)
        self.setWindowTitle('Object Flatter')
        
        by_face = uilib.OButton(uilib.IconPath('uiBtn_extractFace'))
        by_face.clicked.connect(self.flatByFace)
        by_face.setToolTip(
            'Flat objects or components to selected face.\n'
        )
        by_face.setSize(42)
        
        along_edge = uilib.OButton(uilib.IconPath('uiBtn_alignVertsAlongEdge'))
        along_edge.clicked.connect(self.alignVertsAlongEdge)
        along_edge.setToolTip(
            "Flat vertex to selected face along vertex's edge.\n"
        )
        along_edge.setSize(42)
        
        by_context = uilib.OButton(uilib.IconPath('uiBtn_select'))
        by_context.clicked.connect(self.flatByContext)
        by_context.setToolTip('Flat objects or components by context.')
        by_context.setSize(42)

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel('Object Flatter'))
        layout.addWidget(along_edge)
        layout.addWidget(by_face)
        layout.addWidget(by_context)
        layout.addStretch()

    def flatByFace(self):
        with node.DoCommand():
            flatter.fitVertsToFace()

    def alignVertsAlongEdge(self):
        from gris3.tools import modelingSupporter
        with node.DoCommand():
            modelingSupporter.fitVertsToFace()

    def flatByContext(self):
        w = showFlatterContext()
        return w
