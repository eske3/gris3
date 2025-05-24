#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    プレファレンスを設定するGUIを提供するモジュール
    
    Dates:
        date:2017/01/21 12:39[Eske](eske3g@gmail.com)
        update:2023/11/13 14:08 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
from gris3 import uilib, settings
# return settings.GlobalPref().subPref('projectHistory')
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class AppRelationWidget(QtWidgets.QScrollArea):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(AppRelationWidget, self).__init__(parent)


class MainWidget(QtWidgets.QWidget):
    r"""
        プレファレンスのメインGUIを提供するクラス
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(MainWindow, self).__init__(parent)


class MainGUI(uilib.AbstractSeparatedWindow):
    r"""
        単独表示するウィンドウを提供するクラス
    """
    def centralWidget(self):
        r"""
            メインウィジェットを作成して返す
            
            Returns:
                MainWidget:
        """
        return MainWidget()


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。
        
        Returns:
            MainGUI:
    """
    from gris3.uilib import mayaUIlib
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(300, 450)
    widget.show()
    return widget