#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ここに説明文を記入
    
    Dates:
        date:2017/07/06 5:35[Eske](eske3g@gmail.com)
        update:2020/10/12 15:09 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3.tools import hardsurfaceModeler
from gris3.uilib import mayaUIlib
from gris3 import lib, uilib, node
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore
Exec_Color = (64, 72, 150)

class BridgePipeGroup(uilib.ClosableGroup):
    def __init__(self, parent=None):
        super(BridgePipeGroup, self).__init__('Bridge Pipe', parent)
        label = QtWidgets.QLabel('Divisions')
        self.__div_spiner = uilib.Spiner()
        self.__div_spiner.setValue(3)
        self.__div_spiner.setMinimum(1)
        self.__div_spiner.setMinimumWidth(100)
        btn = uilib.OButton(uilib.IconPath('uiBtn_play'))
        btn.clicked.connect(self.execBridge)
        
        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.__div_spiner)
        layout.addWidget(btn)
        layout.addStretch()

    def execBridge(self):
        div = self.__div_spiner.value()
        with node.DoCommand():
            hardsurfaceModeler.bridgePipe(divisions=div)

class Hardsurfacer(QtWidgets.QWidget):
    r"""
        モデルデータの作成、チェックを行う機能を提供するクラス
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(Hardsurfacer, self).__init__(parent)
        self.setWindowTitle('+Hardsurface Modeler')
        
        bridge_grp = BridgePipeGroup()
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(bridge_grp)
        layout.addStretch()

class MainGUI(uilib.AbstractSeparatedWindow):
    r"""
        メインとなるGUIを提供するクラス
    """
    def centralWidget(self):
        r"""
            中心となるメインウィジェットを作成して返す
            
            Returns:
                Hardsurfacer:
        """
        return Hardsurfacer()

def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。
        
        Returns:
            QtWidgets.QWidget:
    """
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(450, 450)
    widget.show()
    return widget
