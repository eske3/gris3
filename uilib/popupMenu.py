#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ここに説明文を記入
    
    Dates:
        date:2017/01/21 23:58[Eske](eske3g@gmail.com)
        update:2021/04/23 09:58 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import uilib, desktop
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

class PopupMenuManager(QtWidgets.QWidget):
    r"""
        ここに説明文を記入
    """
    def __init__(self, parent):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(PopupMenuManager, self).__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint
        )

    def show(self, pos):
        r"""
            表示する
            
            Args:
                pos (QtCore.QPoint):
        """
        desktop_rect = desktop.DesktopInfo().getAvailableGeometry()
        self.setGeometry(desktop_rect)
        super(PopupMenuManager, self).show()
        self.activateWindow()

    def mousePressEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        super(PopupMenuManager, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        super(PopupMenuManager, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        self.close()


class PopupButton(uilib.OButton):
    r"""
        ボタン上でクリックするとポップアップメニューを表示するGUI
    """
    def __init__(self, icon=None):
        r"""
            Args:
                icon (str):ボタンに表示するアイコンのパス
        """
        super(PopupButton, self).__init__(icon)
        self.__popup_menu_manager = PopupMenuManager(self)

    def mousePressEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        self.__popup_menu_manager.show(event.globalPos())
        self.__popup_menu_manager.mousePressEvent(event)
