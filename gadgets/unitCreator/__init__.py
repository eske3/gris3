# -*- coding: utf-8 -*-
r'''
    @brief    ここに説明文を記入
    @date        2017/01/22 0:04[Eske](eske3g@gmail.com)
    @update      2017/09/09 11:18[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
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