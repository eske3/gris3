#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2025/05/11 01:47 Eske Yoshinob[eske3g@gmail.com]
        update:2025/05/11 01:47 Eske Yoshinob[eske3g@gmail.com]

    License:
        Copyright 2025 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from . import creator, editor
from ... import factoryModules, uilib

QtWidgets, QtGui, QtCore = (
    factoryModules.QtWidgets, factoryModules.QtGui, factoryModules.QtCore
)


class Manager(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        super(Manager, self).__init__(parent)
        self.addTab(creator.Creator(), 'Creator')
        self.addTab(editor.Editor(), 'Editor')
        self.currentChanged.connect(self.updateState)

    def updateState(self, index):
        if index == 1:
            self.widget(index).refreshList()


class MainGUI(uilib.AbstractSeparatedWindow):
    def centralWidget(self):
        r"""
            Returns:
                Manager:
        """
        return Manager()


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。

        Returns:
            MainGUI:
    """
    from ...uilib import mayaUIlib
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(400, 600)
    widget.show()
    return widget