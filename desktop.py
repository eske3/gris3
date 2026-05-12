#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    デスクトップ情報を取得するためのモジュール。
    PySideのバージョンによってApplicationからデスクトップにアクセスする方法が
    違うのと、アクセスが煩雑なため簡易アクセス関数を実装。
    
    Dates:
        date:2025/11/04 11:57 Eske Yoshinob[eske3g@gmail.com]
        update:2025/11/04 18:09 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2025 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .pyside_module import *


class AbstractDesktopInfo(object):
    def getPosition(self, pos=None):
        r"""
            Args:
                pos (QtCore.QPoint):
        """
        return QtGui.QCursor().pos() if pos is None else pos


class DesktopInfo6(AbstractDesktopInfo):
    def __init__(self):
        self.__screens = QtWidgets.QApplication.screens()

    def screens(self):
        return self.__screens

    def getScreen(self, pos=None):
        r"""
            Args:
                pos (QtCore.QPoint):
        """
        pos = self.getPosition(pos)
        for scrn in self.screens():
            rect = scrn.geometry()
            if rect.contains(pos):
                return scrn
    
    def getAvailableGeometry(self, pos=None):
        r"""
            任意の座標上のスクリーンの有効矩形範囲を返す。
            引数posがNoneの場合は、マウスカーソル上の座標を用いる。
            
            Args:
                pos (QtCore.QPoint):
                
            Returns:
                QtCore.QRect:
        """
        screen = self.getScreen(pos)
        if not screen:
            return
        return screen.availableGeometry()

    def getGeometry(self, pos=None):
        r"""
            任意の座標上のスクリーン全体の矩形範囲を返す。
            引数posがNoneの場合は、マウスカーソル上の座標を用いる。
            
            Args:
                pos (QtCore.QPoint):
                
            Returns:
                QtCore.QRect:
        """
        screen = self.getScreen(pos)
        if not screen:
            return
        return screen.geometry()

    def grabWindow(self, rect):
        r"""
            任意の矩形で指定する範囲をキャプチャしてQPixmapとして返す。
            
            Args:
                rect (QtCore.QRect):
                
            Returns:
                QtGui.QPixmap:
        """
        screen = self.getScreen()
        return screen.grabWindow(
            0, rect.x(), rect.y(), rect.width(), rect.height()
        )


class DesktopInfoLess2(AbstractDesktopInfo):
    def __init__(self):
        self.__desktop = QtWidgets.QApplication.desktop()
    
    def desktop(self):
        return self.__desktop

    def getScreenNumber(self, pos=None):
        r"""
            Args:
                pos (QtCore.QPoint):
        """
        pos = self.getPosition(pos)
        return self.desktop().screenNumber(pos)

    def getAvailableGeometry(self, pos=None):
        r"""
            任意の座標上のスクリーンの有効矩形範囲を返す。
            引数posがNoneの場合は、マウスカーソル上の座標を用いる。
            
            Args:
                pos (QtCore.QPoint):
                
            Returns:
                QtCore.QRect:
        """
        return self.desktop().availableGeometry(self.getScreenNumber(pos))

    def getGeometry(self, pos=None):
        r"""
            任意の座標上のスクリーン全体の矩形範囲を返す。
            引数posがNoneの場合は、マウスカーソル上の座標を用いる。
            
            Args:
                pos (QtCore.QPoint):
                
            Returns:
                QtCore.QRect:
        """
        return self.desktop().screenGeometry(self.getScreenNumber(pos))

    def grabWindow(self, rect):
        r"""
            任意の矩形で指定する範囲をキャプチャしてQPixmapとして返す。
            
            Args:
                rect (QtCore.QRect):
                
            Returns:
                QtGui.QPixmap:
        """
        return QtGui.QPixmap.grabWindow(
            QtWidgets.QApplication.desktop().winId(),
            rect.x(), rect.y(), rect.width(), rect.height()
        )


DesktopInfo = DesktopInfo6
if Version < 2:
    DesktopInfo = DesktopInfoLess2

