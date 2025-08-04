#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    UIライブラリ
    
    Dates:
        date:2017/01/21 23:57[Eske](eske3g@gmail.com)
        update:2025/06/06 14:01 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
import re
import time
import math
import threading
import platform
from abc import ABCMeta, abstractmethod
from ..pyside_module import *

from .. import globalpath, style, verutil

class Color(object):
    ExecColor = (64, 72, 150)
    DebugColor = (130, 105, 150)

FocusedColor = QtGui.QColor(60, 140, 220)

# デスクトップの大きさに関わる情報の収集。=====================================
WidgetMargins = QtCore.QMargins(
    *[style.DesktopLongestEdge/1000 for x in range(4)]
)
ZeroMargins = QtCore.QMargins(0, 0, 0, 0)

hires = style.hires
# =============================================================================

def accelarate(ratio, power):
    r"""
        加速処理を行う関数。
        
        Args:
            ratio (float):加速比率。
            power (float):加速の乗数。
            
        Returns:
            float:
    """
    return 1 - pow((1 - math.sin(math.pi * 0.5 * ratio)), power)
    

def clearLayout(layout):
    r"""
        引数layout無いのアイテムを削除して、QLayoutをクリアする便利関数。

        Args:
            layout (QtWidgets.QLayout):
    """
    for i in range(layout.count()):
        item = layout.itemAt(i)
        if item.isEmpty():
            layout.removeItem(item)
            continue
        widget = item.widget()
        if widget:
            widget.deleteLater()


IsMac = True if platform.system() == 'Darwin' else False

# Defines alphabet key list of QtCore's namespace./////////////////////////////
QtAlphabetKeys = {}
for char in verutil.UPPERCASE:
    QtAlphabetKeys[getattr(QtCore.Qt, 'Key_' + char)] = char
for char in range(10):
    QtAlphabetKeys[getattr(QtCore.Qt, 'Key_%s' % char)] = str(char)

QtAlphabetKeys[QtCore.Qt.Key_Underscore] = '_'
QtAlphabetKeys[QtCore.Qt.Key_Period] = '.'
QtAlphabetKeys[QtCore.Qt.Key_Bar] = '-'
# /////////////////////////////////////////////////////////////////////////////


# /////////////////////////////////////////////////////////////////////////////
# シングルトン処理用クラス。                                                 //
# /////////////////////////////////////////////////////////////////////////////
class QtSingletonMeta(type(QtCore.QObject)):
    r"""
        Qtのシングルトン処理を行うためのメタクラス。
    """
    _singleton = None
    def __new__(cls, classname, objects=None, dict=None):
        r"""
            Args:
                classname (any):
                objects (any):
                dict (any):
        """
        objects = objects if isinstance(objects, tuple) else (objects,)
        dict = dict or {}
        return super(QtSingletonMeta, cls).__new__(
            cls, classname, objects, dict
        )

    def __init__(self, classname, objects=None, dict=None):
        r"""
            Args:
                classname (any):
                objects (any):
                dict (any):
        """
        objects = objects if isinstance(objects, tuple) else (objects,)
        dict = dict or {}
        super(QtSingletonMeta, self).__init__(classname, objects, dict)

    def __call__(self, *args, **keywords):
        r"""
            Args:
                *args (tuple):
                **keywords (dict):
                
            Returns:
                any:生成されたオブジェクト
        """
        if not self._singleton:
            self._singleton = super(QtSingletonMeta, self).__call__(
                *args, **keywords
            )
        return self._singleton
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////



# /////////////////////////////////////////////////////////////////////////////
# 便利クラス集。                                                             //
# /////////////////////////////////////////////////////////////////////////////
class IconPath(str):
    r"""
        gris3内のアイコンのフルパスを保持する
    """
    def __new__(cls, filename):
        r"""
            Args:
                filename (str):gris3/icons内のファイル名（拡張子無し）
                
            Returns:
                IconPath:
        """
        path = globalpath.getIconPath(filename)
        if not os.path.isfile(path):
            path = globalpath.getIconPath('default.png')

        return super(IconPath, cls).__new__(cls, path)

class Icon(QtGui.QIcon):
    r"""
        gris3内のアイコンをQIconとして作成する
    """
    def __init__(self, imagepath):
        r"""
            Args:
                imagepath (str):gris3/icons内のファイル名（拡張子無し）
        """
        super(Icon, self).__init__(IconPath(imagepath))

class FileIconManager(
    QtSingletonMeta('FileIconManager', QtWidgets.QFileIconProvider)
):
    r"""
        ファイルに紐付いたアイコンを返す仕組みを統括するクラス
    """
    def __new__(cls):
        r"""
            Returns:
                FileIconManager:
        """
        if hasattr(cls, '__instance__'):
            return cls.__instance__
        obj = super(FileIconManager, cls).__new__(cls)
        obj.__instance__ = obj
        obj.__iconlist = {}
        return obj

    def fileIcon(self, filepath):
        r"""
            ファイルパスのタイプに該当するアイコンオブジェクトを返す
            
            Args:
                filepath (str):検査するファイルパス
                
            Returns:
                QtGui.QIcon:
        """
        ext = os.path.splitext(filepath)
        icon = self.__iconlist.get(ext)
        if icon:
            return icon

        if filepath.find('<') > -1:
            return QtGui.QIcon(IconPath('uiBtn_sequence'))
        if os.path.isdir(filepath):
            return QtGui.QIcon(IconPath('folder'))

        icon = self.icon(QtCore.QFileInfo(filepath))
        self.__iconlist[ext] = icon
        return icon


class RGB(tuple):
    r"""
        RGBを表すint３つを持つタプル。
        色の変更を行う拡張メソッドを持つ。
    """
    def __new__(cls, values):
        r"""
            Args:
                values (tuple):RGBの3つのintを持つtuple
                
            Returns:
                RGB:
        """
        if not 2 < len(values) < 5:
            raise ValueError(
                '%s requires tuple type object includes 3 int value.' % (
                    cls.__class__
               )
           )

        fixedValues = []
        for color in values:
            newColor = color
            if newColor > 255:
                newColor = 255
            elif newColor < 0:
                newColor = 0
            fixedValues.append(newColor)
        fixedValues = tuple(fixedValues)

        return super(RGB, cls).__new__(cls, tuple(fixedValues))

    def __add__(self, other):
        r"""
            RGBオブジェクトどうしの加算処理を行う。
            
            Args:
                other (RGB):
                
            Returns:
                RGB:
        """
        if isinstance(other, RGB):
            return RGB([ x + y for x, y in zip(self, other) ])
        else:
            return RGB([ x + other for x in self ])

    def __mul__(self, other):
        r"""
            RGBオブジェクトどうしの乗算処理を行う。
            
            Args:
                other (RGB):
                
            Returns:
                RGB:
        """
        return RGB([ int(x * other) for x in self ])
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////



# /////////////////////////////////////////////////////////////////////////////
# There are classes that is a basic                                          //
# /////////////////////////////////////////////////////////////////////////////
class ConstantWidget(QtWidgets.QDialog):
    r"""
        GRISGUIのベースとなるウィジェットを提供するクラス
    """
    FeedoutTime = 0.2
    AnimTime = 0.2
    DeactiveTime = 0.5
    WindowOffset = QtCore.QPoint(10, 10)
    HideNormaly, HideByCursorOut, HideByFocusOut = range(3)
    #FocusedColor = QtGui.QColor(180, 180, 180)
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ConstantWidget, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        self.__interlock=threading.Lock()
        self.__cursor_count_timer = None
        self.setModal(False)
        if IsMac:
            self.setProperty('saveWindowPref', False)

        self.__from_close_command = False
        self.__isMovable = True
        self.__isScalable   = QtCore.Qt.Horizontal | QtCore.Qt.Vertical
        self.__modified = False
        self.__hidden_trigger = self.HideNormaly
        self.__showOnCursor = True
        self.__pos = None
        self.__pressed_time = 0
        self.__delta = [0, 0]
        self.__openTimerId  = None
        self.__closeTimerId = None
        self.__openTime     = 0.0
        self.__closeTime    = 1.0
        self.__isClose = False
        self.__autoFadeOutTimer = None
        self.__is_closed_by_right_button = False

        self.__activated_pre_state = self.isActiveWindow()
        self.__activated_timerid = None
        self.__activated_time = None
        self.__activated_opacity = 0

        self.__releaseFullScreenFlag = 0
        self.__currentRect = None
        self.__maximizeRect = None
        self.__maximizeMinimizeTimerId = None
        self.__maximizeMinimizeStartTime = 0
        self.__animTime = self.AnimTime

        self.setWindowOpacity(0.0)
        self.buildUI()
        self.installEventFilter(self)

    def setClosedByRightButton(self, state):
        r"""
            ウィジェット上で右クリックした場合に閉じる設定を行う
            
            Args:
                state (bool):Trueの場合、右クリックでウィジェットを閉じる
        """
        self.__is_closed_by_right_button = bool(state)

    def isClosedByRightButton(self):
        r"""
            ウィジェット上で右クリックした場合に閉じるかどうか
            
            Returns:
                bool:
        """
        return self.__is_closed_by_right_button

    def setShowOnCursor(self, state):
        r"""
            ウィジェットを表示時にマウスカーソルの上に表示する設定する
            
            Args:
                state (bool):
        """
        self.__showOnCursor = bool(state)

    def isShowOnCursor(self):
        r"""
            ウィジェットを表示時にマウスカーソルの上に表示するかどうか
            
            Returns:
                bool:
        """
        return self.__showOnCursor

    def moveOnCursor(self):
        r"""
            ウィジェトをマウスカーソル上に移動する
        """
        # Move the window automaticaly to position pinted by mouse cursor.=====
        pos = QtGui.QCursor.pos()
        drect = style.screenRect(pos)
        dwidth = drect.width()
        dheight = drect.height()
        
        rect = self.geometry()

        posX = (
            pos.x() - (rect.width() / 2) - drect.x() - self.WindowOffset.x()
       )
        posY = (
            pos.y() - (rect.height() / 4) - drect.y() - self.WindowOffset.y()
       )
        width = rect.width()
        height = rect.height()
        limitMaxX = dwidth - width
        limitMaxY = dheight - height

        # Decide x position.---------------------------------------------------
        if posX < 0:
            posX = 0
        elif posX > limitMaxX:
            posX = dwidth - width
        # ---------------------------------------------------------------------

        # Decide y position.---------------------------------------------------
        if posY < 0:
            posY = 0
        elif posY > limitMaxY:
            posY = dheight - height
        # ---------------------------------------------------------------------

        pos.setX(posX + drect.x())
        pos.setY(posY + drect.y())

        self.move(pos)
        # =====================================================================

    def setScalable(self, state):
        r"""
            ウィンドウがスケール可能かどうかを設定する
            
            Args:
                state (bool):
        """
        if state is True:
            self.__isScalable = QtCore.Qt.Horizontal | QtCore.Qt.Vertical
            return
        elif state in (
            False, QtCore.Qt.Horizontal, QtCore.Qt.Vertical,
            (QtCore.Qt.Horizontal | QtCore.Qt.Vertical)
        ):
            self.__isScalable = state

    def isScalable(self):
        r"""
            ウインドウがスケール可能下どうか
            
            Returns:
                bool:
        """
        return self.__isScalable

    def setIsMovable(self, state):
        r"""
            ウィンドウを動かすことができるかを設定する
            
            Args:
                state (bool):
        """
        self.__isMovable = bool(state)

    def isMovable(self):
        r"""
            ウィンドウを動かすことができるかを返す
            
            Returns:
                bool:
        """
        return self.__isMovable

    def __prepareWindowShown(self):
        r"""
            ウィンドウ表示前に行う処理。(内部使用専用)
        """
        if self.isShowOnCursor():
            self.moveOnCursor()
        self.setDisabled(False)
        self.__openTimerId = self.startTimer(10)
        self.__openTime = time.time()

    def show(self):
        r"""
            ウィンドウを表示すうｒ
        """
        if self.isMinimized():
            self.showNormal()
        self.__prepareWindowShown()
        super(ConstantWidget, self).show()

    def exec_(self):
        r"""
            ダイアログとしてウィンドウを表示する
            
            Returns:
                bool:
        """
        self.__prepareWindowShown()
        return super(ConstantWidget, self).exec_()

    def setHiddenTrigger(self, mode):
        r"""
            ウィンドウを非表示にするトリガー動作を設定する。
            HideNormaly : 通常モード
            HideByCursorOut : カーソルがウィジェットからはずれた場合
            HideByFocusOut : フォーカスがほかへ移った場合
            
            Args:
                mode (int):HideByCursorOut / HideByFocusOut
        """
        mode = int(mode)
        self.__hidden_trigger = mode
        with self.__interlock:  #timerのインターロック
            if self.__cursor_count_timer:
                self.killTimer(self.__cursor_count_timer)
                self.__cursor_count_timer=None
        if mode == self.HideByFocusOut:
            self.setWindowFlags(QtCore.Qt.Popup)
        else:
            self.setWindowFlags(
                QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint
            )
        if mode == self.HideByCursorOut:
            with self.__interlock:  #timerのインターロック
                if self.__cursor_count_timer:
                    self.killTimer(self.__cursor_count_timer)
                self.__cursor_count_timer = self.startTimer(500)

    def hiddenTrigger(self):
        r"""
            ウィンドウを非表示にするトリガー動作のモードを返す。
            
            Returns:
                int:
        """
        return self.__hidden_trigger

    def fadeOut(self):
        r"""
            ウィンドウをフェードアウトして非表示にする
        """
        if self.__closeTimerId:
            self.killTimer(self.__closeTimerId)

        self.__closeTime = time.time()
        self.__closeTimerId = self.startTimer(10)
        self.setDisabled(True)

    def closeEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        if not self.__from_close_command:
            event.ignore()
            self.fadeOut()
        else:
            self.__from_close_command = False

    def stopAutoFadeOut(self):
        r"""
            フェードアウトを中断する
        """
        if not self.__autoFadeOutTimer:
            return
        self.killTimer(self.__autoFadeOutTimer)
        self.__autoFadeOutTimer = None

    def startAutoFadeOut(self, sleepTime=150):
        r"""
            フェードアウトを開始する
            
            Args:
                sleepTime (int):フェードアウトまでの待機時間
        """
        self.stopAutoFadeOut()
        self.__autoFadeOutTimer = self.startTimer(sleepTime)

    # =========================================================================
    # ウィンドウサイズに関するメソッド。                                     ==
    # =========================================================================
    def getRectInfo(self):
        r"""
            現在のGUIとデスクトップの矩形情報を返すメソッド。
            
            Returns:
                tuple(QRect, QRect):
        """
        rect = self.geometry()
        return (rect, style.screenRect(rect.center()))

    def currentRect(self):
        r"""
            現在のウィジェットの矩形情報を返す
            
            Returns:
                tuple(QtCore.QRect):
        """
        return self.__currentRect

    def storeWidgetSizeInfo(self):
        r"""
            現在のGUIの矩形情報を保持するメソッド。
        """
        self.__currentRect, self.__maximizeRect = self.getRectInfo()

    def changeWindowSize(self, startRect, goalRect):
        r"""
            ウィンドウサイズ変更アニメーションを開始するメソッド。
            
            Args:
                startRect (QRect):
                goalRect (QRect):
        """
        if not self.__isScalable:
            return

        self.__startRect = startRect
        self.__goalRect = goalRect

        self.__subRect = QtCore.QRect(
            *[
                getattr(goalRect, x)() - getattr(startRect, x)()
                for x in ['x', 'y', 'width', 'height']
            ]
       )
        if self.__maximizeMinimizeTimerId:
            self.killTimer(self.__maximizeMinimizeTimerId)
        self.__maximizeMinimizeStartTime = time.time()
        self.__maximizeMinimizeTimerId = self.startTimer(10)

    def isFullScreen(self):
        r"""
            ウィジェットがフルスクリーンかどうか
            
            Returns:
                bool:
        """
        rects = self.getRectInfo()
        return rects[0] == rects[1]

    def maximize(self):
        r"""
            ウィンドウを最大化する
        """
        self.storeWidgetSizeInfo()
        self.__animTime = self.AnimTime
        self.changeWindowSize(self.__currentRect, self.__maximizeRect)

    def normalize(self):
        r"""
            ウィンドウを標準サイズに戻す
        """
        rects = self.getRectInfo()
        self.__animTime = self.AnimTime
        self.changeWindowSize(rects[0], self.__currentRect)

    def moveToCursor(self):
        r"""
            マウスカーソルの上にウィジェットを動かすメソッド。
            moveOnCursorと違い、こちらはアニメーション付き。
        """
        pos = QtGui.QCursor.pos()
        rect = self.geometry()
        if self.__releaseFullScreenFlag == 3 or self.isFullScreen():
            new_rect = self.__currentRect
        else:
            new_rect = QtCore.QRect(rect)

        new_rect.moveCenter(pos)
        self.__animTime = self.AnimTime
        self.changeWindowSize(rect, new_rect)

    def setDesktopSide(self, which):
        r"""
            ウィンドウを左右どちらかにフィットさせる。
            引数が０の場合左側、１の場合は右側にフィットさせる。
            
            Args:
                which (bool):
        """
        half_width = self.__maximizeRect.width() / 2
        top_left = self.__maximizeRect.topLeft()
        half_size = QtCore.QSize(half_width, self.__maximizeRect.height())
        top_left = (
            QtCore.QPoint(top_left.x() + half_width, top_left.y())
            if which else top_left
       )
        rect = QtCore.QRect(top_left, half_size)
        
        self.__releaseFullScreenFlag = 3

        self.__animTime = self.AnimTime
        self.changeWindowSize(self.geometry(), rect)

    def toggleFullScreen(self):
        r"""
            フルスクリーンと通常のトグルスイッチ。
        """
        rect, drect = self.getRectInfo()
        if rect == drect:
            self.normalize()
        else:
            self.maximize()

    # There are methods to overload protected functions.========================
    def enterEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        super(ConstantWidget, self).enterEvent(event)
        self.stopAutoFadeOut()

    def leaveEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        if self.hiddenTrigger() != self.HideByCursorOut:
            return
        if self.isHidden():
            return
        pos         = QtGui.QCursor.pos()
        rect        = self.geometry()
        topLeft     = rect.topLeft()
        bottomRight = rect.bottomRight()

        if (
            pos.x() < topLeft.x() or pos.x() > bottomRight.x() or
            pos.y() < topLeft.y() or  pos.y() > bottomRight.y()
       ):
            self.startAutoFadeOut()
        super(ConstantWidget, self).leaveEvent(event)

    def mousePressEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        self.__modified = False
        if self.__releaseFullScreenFlag < 3:
            self.__releaseFullScreenFlag = 1 if self.isFullScreen() else 0
        
        if not self.__releaseFullScreenFlag:
            self.storeWidgetSizeInfo()

        if self.__isMovable:
            self.__pos = [event.globalX(), event.globalY()]
        else:
            self.__pos = None

        self.__pressed_time = time.time()
        super(ConstantWidget, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        if not self.__pos:
            super(ConstantWidget, self).mouseMoveEvent(event)
            return

        cur = [event.globalX(), event.globalY()]
        pos = [self.pos().x(), self.pos().y()]
        self.__delta = [x - y for x, y in zip(cur, self.__pos)]
        rects = self.getRectInfo()
        y_ratio = abs(self.__delta[1] / float(rects[1].height()))

        if self.__releaseFullScreenFlag > 2 and y_ratio < 0.005:
            self.__pos[1] = cur[1]
        elif self.__releaseFullScreenFlag:
            self.__releaseFullScreenFlag = 2

        is_scalable = self.isScalable()
        if (
            event.buttons() in (QtCore.Qt.RightButton, QtCore.Qt.MiddleButton)
            and is_scalable
       ):
            moveValue = [x - y for x, y in zip(cur, self.__pos)]
            rect = self.geometry()
            if is_scalable & QtCore.Qt.Horizontal:
                rect.setWidth(rect.width() + moveValue[0])
            if is_scalable & QtCore.Qt.Vertical:
                rect.setHeight(rect.height() + moveValue[1])
            self.setGeometry(rect)
        else:
            moveValue = [
                z + y - x for x, y, z in zip(self.__pos, cur, pos)
            ]
            self.move(moveValue[0], moveValue[1])

        self.__pos = cur
        self.__modified = True
        super(ConstantWidget, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        if (
            self.isClosedByRightButton() and
            event.button() == QtCore.Qt.RightButton and
            not self.__modified
       ):
            self.fadeOut()
            return

        super(ConstantWidget, self).mouseReleaseEvent(event)

        rects = self.getRectInfo()
        delta_ratio = self.__delta[0] / float(rects[1].width())
        moved_time = time.time() - self.__pressed_time
        self.__pos = None

        if abs(delta_ratio) >= 0.01 and moved_time < 0.12:
            self.setDesktopSide(1 if delta_ratio > 0 else 0)
            return

        if self.__releaseFullScreenFlag == 2:
            self.__releaseFullScreenFlag = 0
            self.normalize()

    def mouseDoubleClickEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        self.toggleFullScreen()

    def keyPressEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        if event.key() == QtCore.Qt.Key_Escape:
            self.fadeOut()
        else:
            super(ConstantWidget, self).keyPressEvent(event)
    
    def timerEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        curtime = time.time()
        timer_id = event.timerId()

        if timer_id== self.__openTimerId:
            t = curtime - self.__openTime
            opacity = t / self.FeedoutTime
            if opacity >= 1.0:
                opacity = 1.0
                self.killTimer(self.__openTimerId)
                self.__openTimerId = None
            self.setWindowOpacity(opacity)
        elif timer_id == self.__closeTimerId:
            t = curtime - self.__closeTime
            opacity = 1 - t / self.FeedoutTime
            if opacity <= 0.0:
                opacity = 0.0
                self.killTimer(self.__closeTimerId)
                self.__closeTimerId = None
                if self.isModal():
                    self.reject()
                self.hide()
                self.__from_close_command = True
                self.close()
            self.setWindowOpacity(opacity)
        elif timer_id == self.__maximizeMinimizeTimerId:
            ratio = (
                (time.time() - self.__maximizeMinimizeStartTime) /
                self.__animTime
           )
            if ratio > 1:
                ratio = 1
                self.killTimer(self.__maximizeMinimizeTimerId)
                self.__maximizeMinimizeTimerId = None
                goal_rect = self.__goalRect
            else:
                ratio = accelarate(ratio, 2)
                goal_rect = QtCore.QRect(
                    *[   
                        getattr(self.__startRect, x)() +
                        getattr(self.__subRect, x)() * ratio
                        for x in ['x', 'y', 'width', 'height']
                    ]
               )
            self.setGeometry(goal_rect)

        elif timer_id == self.__autoFadeOutTimer:
            self.stopAutoFadeOut()
            self.fadeOut()
            return False

        elif timer_id == self.__activated_timerid:
            sub_value = 1.0 if self.isActiveWindow() else 0.0
            ratio = (
                (time.time() - self.__activated_time) / self.DeactiveTime
           )
            if ratio > 1:
                self.killTimer(self.__activated_timerid)
                self.__activated_timerid = None
                self.__activated_opacity = 1.0 - sub_value
            else:
                self.__activated_opacity = abs(
                    sub_value - accelarate(ratio, 2)
               )
            self.update()
    # =========================================================================

    def followMouseOperation(self, widget):
        r"""
            指定されたウィジェットのマウス操作をこのウィジェットに
            合わせる。
            
            Args:
                widget (QtWidgets.QWidget):
        """
        widget.mousePressEvent = self.mousePressEvent
        widget.mouseMoveEvent = self.mouseMoveEvent
        widget.mouseReleaseEvent = self.mouseReleaseEvent

    def paintEvent(self, event):
        r"""
            paintEventのオーバーライド
            
            Args:
                event (QtCore.QEvent):
        """
        super(ConstantWidget, self).paintEvent(event)
        is_active_window = self.isActiveWindow()
        painter = QtGui.QPainter(self)

        if is_active_window:
            painter.setPen(QtGui.QPen(FocusedColor, 2))
        else:
            painter.setPen(QtCore.Qt.NoPen)

        if self.__activated_pre_state != is_active_window:
            if self.__activated_timerid:
                self.killTimer(self.__activated_timerid)
            self.__activated_opacity = 1 if self.isActiveWindow() else 0
            self.__activated_time = time.time()
            self.__activated_timerid = self.startTimer(10)

        if not is_active_window or self.__activated_timerid:
            painter.setBrush(
                QtGui.QColor(0, 0, 0, 60 * self.__activated_opacity)
           )
        painter.drawRect(self.rect())
       
        self.__activated_pre_state = is_active_window

    def buildUI(self):
        r"""
            GUI生成コードを書くためのオーバーライドメソッド。
        """
        pass


class SingletonWidget(QtSingletonMeta('SingletonWidget', ConstantWidget)):
    r"""
        シングルトン機能を持つウィジェット
    """
    pass
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////


class AbstractSeparatedWindow(SingletonWidget):
    r"""
        単体表示用のウィンドウを生成するクラス。
    """
    def buildUI(self):
        r"""
            UI作成。
        """
        self.setStyleSheet(style.styleSheet())
        self.__titlebar = TitleBarWidget(self)
        main = self.centralWidget()
        self.__titlebar.setTitle(main.windowTitle())
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.addWidget(self.__titlebar)
        layout.addWidget(main)
        self.__main = main

    @abstractmethod
    def centralWidget(self):
        r"""
            配置されるウィジェットを返す。
            
            Returns:
                QtWidgets.QWidget:
        """
        pass

    def titlebar(self):
        return self.__titlebar

    def keyPressEvent(self, event):
        r"""
            Enterキーが押された時に表示が消えてしまう処理に対処。
            
            Args:
                event (QtCore.QEvent):
        """
        if event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            return
        super(AbstractSeparatedWindow, self).keyPressEvent(event)

    def main(self):
        r"""
            エンジン部となるウィジェットMainGUIを返す。
            
            Returns:
                MainGUI:
        """
        return self.__main

class BlackoutPopup(QtWidgets.QWidget):
    r"""
        引数parentで指定したウィジェットを暗転させ、代わりに任意の
        ウィジェットを表示させるGUIを提供するクラス。
    """
    AnimTime = 0.3
    BgOpacity = 180
    BgOpacityMultiplyer = 1.0
    def __init__(self, parent):
        r"""
            初期化関数。引数parentは必須となる。
            
            Args:
                parent (QWidget):親ウィジェット。
        """
        super(BlackoutPopup, self).__init__(parent)
        if parent:
            parent.installEventFilter(self)
        self.__show_close_timerid = None
        self.__show_close_starttime = 0.0
        self.__close_postcommand = None
        self.__center_widget_size = None

        self.__center_widget = QtWidgets.QFrame(self)
        self.__center_widget.setObjectName('blackoutpopupWidget')
        self.__center_widget.setStyleSheet(
            'QFrame{'
            'background:#303030;'
            '}'
            '#blackoutpopupWidget{'
            'border : 1px solid #000000;'
            'border-radius : 8px;'
            '}'
       )
        self.__center_widget.resize(300, 300)

    def setCenterSize(self, width, height, isAbsolute=True):
        r"""
            センターウィジェットのサイズを設定するメソッド。
            
            Args:
                width (int):
                height (int):
                isAbsolute (True):[bool]
        """
        if isAbsolute:
            self.__center_widget.resize(width, height)
            self.__center_widget_size = None
        else:
            self.__center_widget_size = (
                width if width < 1.0 else 1.0,
                height if height < 1.0 else 1.0
           )
            self.resizeCenterWidget()

    def centerWidget(self):
        r"""
            中心に配置されているウィジェットのインスタンスを返すメソッド。
            
            Returns:
                QtWidgets.QWidget:
        """
        return self.__center_widget

    def resizeCenterWidget(self):
        r"""
            センターウィジェットを中心に再配置するメソッド。
        """
        if not self.__center_widget_size:
            return
        rect = self.rect()
        rect.setWidth(self.width() * self.__center_widget_size[0] - 10)
        rect.setHeight(self.height() * self.__center_widget_size[1] - 10)
        self.__center_widget.setGeometry(rect)

    def updatePosition(self):
        r"""
            現在の位置情報を元にセンターウィジェットを中心へ移動
            させるメソッド。
        """
        self.setGeometry(self.parent().rect())
        self.resizeCenterWidget()
        
        rect = self.__center_widget.rect()
        rect.moveCenter(self.rect().center())
        self.__center_widget.setGeometry(rect)

    def stopShowing(self):
        r"""
            表示アニメーションを中断させるメソッド。
        """
        if self.__show_close_timerid:
            self.killTimer(self.__show_close_timerid)
            self.__show_close_timerid = None

    def showDialog(self):
        r"""
            ダイアログを表示させるメソッド。
        """
        if not self.isHidden():
            return
        self.updatePosition()
        self.stopShowing()
        self.BgOpacityMultiplyer = 0.0
        self.centerWidget().show()
        self.show()

        self.__close_postcommand = None
        self.__show_close_starttime = time.time()
        self.__show_close_timerid = self.startTimer(10)

    def closeDialog(self):
        r"""
            ダイアログを非表示にするメソッド。
        """
        if self.isHidden():
            return
        self.stopShowing()
        self.BgOpacityMultiplyer = 1.0
        self.centerWidget().hide()

        self.__close_postcommand = self.hide
        self.__show_close_starttime = time.time()
        self.__show_close_timerid = self.startTimer(10)

    def timerEvent(self, event):
        r"""
            Args:
                event (QEvent):
        """
        timer_id = event.timerId()
        if timer_id == self.__show_close_timerid:
            goal_opacity = 0.0 if self.__close_postcommand else 1.0
            time_ratio = (
                (time.time() - self.__show_close_starttime) / self.AnimTime
           )
            if time_ratio >= 1.0:
                opacity = goal_opacity
                self.stopShowing()
                if self.__close_postcommand:
                    self.__close_postcommand()
            else:
                opacity = abs(1 - goal_opacity - time_ratio)
            self.BgOpacityMultiplyer = opacity
            self.update()

    def eventFilter(self, obj, event):
        r"""
            Args:
                obj (QtCore.QObject):
                event (QtCore.QEvent):
                
            Returns:
                bool:
        """
        parent = self.parent()
        if parent == obj and event.type() == QtCore.QEvent.Resize:
            self.updatePosition()
            return False
        return False

    def paintEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        painter = QtGui.QPainter(self)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(
            QtGui.QColor(0, 0, 0, self.BgOpacity * self.BgOpacityMultiplyer)
       )
        painter.drawRect(self.rect())


class BlackoutDisplay(QtWidgets.QDialog):
    r"""
        全画面を暗転表示させる機構を提供するクラス。
        このウィジェットは最前面に描画される。
    """
    AnimTime = 0.25
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):
        """
        super(BlackoutDisplay, self).__init__(parent)
        self.__show_close_timerid = None
        self.__is_showing = True
        self.setWindowFlags(
            QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint
       )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.__gradient = self.createBgGradient()

    def createBgGradient(self):
        r"""
            背景描画用のグラデーションを生成して返す
            
            Returns:
                QtGui.QLinearGradient:
        """
        g = QtGui.QLinearGradient(0, 0, 0, 0)
        g.setColorAt(0.0,  QtGui.QColor(0,  0,  0,  255))
        g.setColorAt(0.1, QtGui.QColor(0,  0,  0,  255))
        g.setColorAt(0.75, QtGui.QColor(0,  20, 40, 200))
        g.setColorAt(1.0,  QtGui.QColor(46,208,237, 70))
        return g

    def stopShowing(self):
        r"""
            表示の更新を止めるメソッド。
        """
        if self.__show_close_timerid:
            self.killTimer(self.__show_close_timerid)

    def show(self):
        r"""
            ディスプレイ表示するためのメソッド。
        """
        desktop = QtWidgets.QApplication.desktop()
        number = desktop.screenNumber(QtGui.QCursor().pos())
        rect = desktop.availableGeometry(number)
        self.setGeometry(rect)

        self.stopShowing()
        self.__is_showing = True
        self.setWindowOpacity(0)
        super(BlackoutDisplay, self).show()
        self.__show_close_starttime = time.time()
        self.__show_close_timerid = self.startTimer(10)

    def hide(self):
        r"""
            非表示にするためのメソッド。
        """
        self.stopShowing()
        self.__is_showing = False
        self.setWindowOpacity(1)

        self.__show_close_starttime = time.time()
        self.__show_close_timerid = self.startTimer(10)

    def paintEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        rect = self.rect()
        self.__gradient.setFinalStop(0, rect.height())

        painter = QtGui.QPainter(self)
        painter.setPen(None)
        painter.setBrush(self.__gradient)
        painter.drawRect(rect)

    def timerEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        timer_id = event.timerId()
        if timer_id == self.__show_close_timerid:
            goal_opacity = 1.0 if self.__is_showing else 0.0
            time_ratio = (
                (time.time() - self.__show_close_starttime) / self.AnimTime
           )
            if time_ratio >= 1.0:
                opacity = goal_opacity
                self.stopShowing()
                do_command = True
            else:
                opacity = accelarate(abs(1 - goal_opacity - time_ratio), 2)
                do_command = False
            self.setWindowOpacity(opacity)

            if do_command:
                if self.__is_showing:
                    self.activateWindow()
                else:
                    super(BlackoutDisplay, self).hide()

    def mouseReleaseEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        if event.button() == QtCore.Qt.RightButton:
            self.hide()
            return
        super(BlackoutDisplay, self).mouseReleaseEvent(event)



# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////
class ImageViewerWidget(QtWidgets.QWidget):
    r"""
        イメージを表示するためのウィジェット。
    """
    def __init__(self, pixmap=None, parent=None):
        r"""
            Args:
                pixmap (QtGui.QPixmap or str):表示するイメージのパス
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ImageViewerWidget, self).__init__(parent)
        self.__pixmap = None
        self.setImage(pixmap)

    def setImage(self, pixmap):
        r"""
            表示するイメージを設定する。
            
            Args:
                pixmap (QtGui.QPixmap or str):
        """
        if isinstance(pixmap, QtGui.QPixmap):
            self.__pixmap = image
            return
        self.__pixmap = QtGui.QPixmap(pixmap)
        self.update()

    def image(self):
        r"""
            設定された表示イメージのPixmapを返す。
            
            Returns:
                QtGui.QPixmap:
        """
        return self.__pixmap

    def paintEvent(self, event):
        r"""
            Args:
                event (any):
        """
        pixmap = self.image()
        if not pixmap or pixmap.isNull():
            return
        painter = QtGui.QPainter(self)
        painter.setRenderHints(QtGui.QPainter.Antialiasing)
        rect = self.rect()
        drawed = pixmap.scaled(
            rect.size(),
            QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
        )
        d_rect = drawed.rect()
        d_rect.moveCenter(rect.center())
        painter.drawPixmap(d_rect, drawed)


class ListComboBox(QtWidgets.QComboBox):
    r"""
        リスト表示用カスタムComboBox
    """
    ItemHeight = 28
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ListComboBox, self).__init__(parent)
        
        model = QtGui.QStandardItemModel()
        self.setModel(model)
        
        view = QtWidgets.QListView()
        view.setAlternatingRowColors(True)
        self.setView(view)

    def addItems(self, itemlist):
        r"""
            アイテムを追加する
            
            Args:
                itemlist (list):
        """
        super(ListComboBox, self).addItems(itemlist)

        model = self.model()
        for i in range(model.rowCount()):
            item = model.item(i, 0)
            item.setSizeHint(
                QtCore.QSize(item.sizeHint().width(), self.ItemHeight)
           )

    def clear(self):
        r"""
            登録アイテムをクリアする
        """
        model = self.model()
        model.removeRows(0, model.rowCount())


class StarndardSpinerObject(QtCore.QObject):
    r"""
        Max風スピナーのUI機能を持つクラス。
        QSpinBox内でインスタンスを作成し、_setupメソッドにQSpinBoxを渡して
        使用する。
    """
    ButtonFactor = {
        QtCore.Qt.LeftButton : 1,
        QtCore.Qt.MiddleButton : 10,
        QtCore.Qt.RightButton  : 100,
    }
    def _setup(self, spinBox):
        r"""
            初期化を行う。
        """
        self.__Y = 0
        self.__pressed = None
        self.__moved = False
        self.__pressed_callback = None
        self.__moved_callback = None
        self.__released_callback = None
        self.__target = spinBox
        self.__target.installEventFilter(self)
        for m in (
            'setPressedCallback', 'setMovedCallback', 'setReleasedCallback'
        ):
            setattr(self.__target, m, getattr(self, m))

    def eventFilter(self, obj, event):
        r"""
            イベントをフィルタリングする。
            
            Args:
                obj (QtCore.QObject):対象オブジェクト
                event (QtCore.QEvent):イベントオブジェクト
                
            Returns:
                bool:
        """
        event_type = event.type()
        if event_type == QtCore.QEvent.MouseButtonPress:
            self._orMousePressEvent(event)
            return True
        elif event_type == QtCore.QEvent.MouseMove:
            self._orMouseMoveEvent(event)
            return True
        elif event_type == QtCore.QEvent.MouseButtonRelease:
            self._orMouseReleaseEvent(event)
            return True
        else:
            return False

    def repositionCursor(self, y):
        r"""
            カーソルが画面外まで移動した時の挙動を制御する
            
            Args:
                y (int):現在のY座標
        """
        currentScreenRect = QtWidgets.QApplication.desktop().screenGeometry(
            QtWidgets.QApplication.desktop().screenNumber(
                QtGui.QCursor().pos()
            )
        )
        lowerLimit = currentScreenRect.y()
        upperLimit = currentScreenRect.height() + lowerLimit - 1
        if y <= lowerLimit:
            posY = upperLimit - 1
        elif y >= upperLimit:
            posY = lowerLimit + 1
        else:
            self.__Y = y
            return
        QtGui.QCursor().setPos(QtGui.QCursor().pos().x(), posY)
        self.__Y = posY

    def setPressedCallback(self, callback):
        r"""
            ボタンを押す前に呼び出されるコールバックをセットする
            
            Args:
                callback (function):引数の無い関数
        """
        self.__pressed_callback = callback

    def setMovedCallback(self, callback):
        r"""
            マウスドラッグ中に呼び出されるコールバックをセットする
            
            Args:
                callback (function):引数の無い関数
        """
        self.__moved_callback = callback

    def setReleasedCallback(self, callback):
        r"""
            ボタンを押した後に呼び出されるコールバックをセットする
            
            Args:
                callback (function):引数の無い関数
        """
        self.__released_callback = callback
         
    def _orMousePressEvent(self, event):
        r"""
            マウスボタンを押した時の挙動のオーバーライド
            
            Args:
                event (QtCore.QEvent):
        """
        if self.__pressed_callback:
            self.__pressed_callback()
        # マウスカーソルの現在位置を取得し、クラス内変数へ保存する。
        self.__Y = event.globalY()
        # クリックされたボタンを記憶。
        self.__pressed = event.button()
        self.__moved = False
  
    def _orMouseMoveEvent(self, event):
        r"""
            マウス移動時の挙動のオーバーライド
            
            Args:
                event (QtCore.QEvent):
        """
        if self.__moved_callback:
            self.__moved_callback()
        # マウスカーソルの現在位置を取得し、最後に記録されたマウスカーソル位置
        # との差分を取得。
        posY = event.globalY()
        delta = self.__Y - posY
        if(
            not self.__moved and
            abs(delta) < QtWidgets.QApplication.startDragDistance()
        ):
            return
        movedValue = self.__target.singleStep() * (1 if delta>0 else -1)
        self.__Y = posY
         
        # マウスの押されたボタンに応じて加算される数字に倍率をかける。
        # 真中ボタンなら×１０、右ボタンなら×１００される。
        if self.__pressed in self.ButtonFactor:
            movedValue *= self.ButtonFactor[self.__pressed]
 
        # 差分を現在のスピンボックスの値に加算してからセットする。
        value = self.__target.value() + movedValue
        if self.__target.minimum() < value < self.__target.maximum():
            self.__target.setValue(value)
        self.repositionCursor(posY)
 
    def _orMouseReleaseEvent(self, event):
        r"""
            マウスボタンを離した時の挙動のオーバーライド
            
            Args:
                event (QtCore.QEvent):
        """
        if self.__released_callback:
            self.__released_callback()
        if not self.__moved:
            self.__target.mousePressEvent(event)
            self.__target.mouseReleaseEvent(event)
        self.__moved = False


class Spiner(QtWidgets.QSpinBox):
    r"""
        Max風スピナーUI(int)を提供するクラス
    """
    def __init__(self, *args, **keywords):
        r"""
            Args:
                *args (tuple):
                **keywords (dict):
        """
        super(Spiner, self).__init__(*args, **keywords)
        StarndardSpinerObject()._setup(self)


class DoubleSpiner(QtWidgets.QDoubleSpinBox):
    r"""
        Max風スピナーUI(double)を提供するクラス
    """
    ButtonFactor = {
        QtCore.Qt.LeftButton : 0.1,
        QtCore.Qt.MiddleButton : 1,
        QtCore.Qt.RightButton  : 10,
    }
    def __init__(self, *args, **keywords):
        r"""
            Args:
                *args (tuple):
                **keywords (dict):
        """
        super(DoubleSpiner, self).__init__(*args, **keywords)
        StarndardSpinerObject()._setup(self)


class ClosableGroup(QtWidgets.QGroupBox):
    r"""
        展開・折込可能なグループを提供するクラス。
    """
    expanded = QtCore.Signal(bool)
    IconRect = QtCore.QRect(0, 0, style.scaled(40), style.scaled(40))
    BgColor = QtGui.QColor(0, 0, 0, 80)
    PenColor = QtGui.QPen(QtGui.QColor(0, 0, 0))
    TextColor = QtGui.QPen(QtGui.QColor(200, 200, 200))
    def __init__(self, *args, **keywords):
        r"""
            Args:
                *args (tuple):
                **keywords (dict):
        """
        super(ClosableGroup, self).__init__(*args, **keywords)
        self.__is_closed = False
        self.__do_closing = True
        self.__start_pos = None
        self.__icon = None
        self.__showed_size_policy = self.sizePolicy()

    def setIcon(self, iconPath):
        r"""
            折込時に表示するアイコンのパスをセットする。。
            
            Args:
                iconPath (str):
        """
        pixmap = QtGui.QPixmap(iconPath)
        self.__icon = pixmap.scaled(
            self.IconRect.size(),
            QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
        )

    def minimumSizeHint(self):
        s = super(ClosableGroup, self).minimumSizeHint()
        if self.__is_closed:
            return QtCore.QSize(
                style.scaled(s.width()), style.scaled(s.height())
            )
        return s

    def icon(self):
        r"""
            折込時に表示するアイコンを返す。
            
            Returns:
                QtGui.QPixmap:
        """
        return self.__icon

    def setExpanding(self, show):
        r"""
            グループを展開するかどうかを設定する。
            
            Args:
                show (bool):
        """
        def toggleVisibiliy(layout, show):
            r"""
                レイアウト内で再帰的に表示・非表示を設定するローカル関数。
                
                Args:
                    layout (QLayout):
                    show (bool):
            """
            if not layout:
                return
            for i in range(layout.count()):
                item = layout.itemAt(i)
                w = item.widget()
                if w:
                    w.setVisible(show)
                l = item.layout()
                if l:
                    toggleVisibiliy(l)
        toggleVisibiliy(self.layout(), show)
        for child in self.children():
            if isinstance(child, QtWidgets.QWidget):
                child.setVisible(show)
        if show:
            self.setSizePolicy(self.__showed_size_policy)
        else:
            self.__showed_size_policy = self.sizePolicy()
            self.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
            )
        self.update()
        self.__is_closed = show == False
        self.expanded.emit(show)

    def isExpanding(self):
        r"""
            グループが展開されているかどうか返す。
            
            Returns:
                bool:
        """
        return self.__is_closed == False

    def mousePressEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        super(ClosableGroup, self).mousePressEvent(event)
        self.__start_pos = event.pos()
        self.__do_closing = True

    def mouseMoveEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        super(ClosableGroup, self).mouseMoveEvent(event)
        if not self.__start_pos:
            return
        if (
            (event.pos() - self.__start_pos).manhattanLength()
            > QtWidgets.QApplication.startDragDistance()
        ):
            self.__do_closing = False

    def mouseReleaseEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        super(ClosableGroup, self).mouseReleaseEvent(event)
        if self.__do_closing:
            self.setExpanding(self.__is_closed)
        self.__do_closing = True

    def paintEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        if self.__is_closed:
            size = style.scaled(8)
            painter = QtGui.QPainter(self)
            painter.setRenderHints(QtGui.QPainter.Antialiasing)
            painter.setBrush(self.BgColor)
            painter.setPen(self.PenColor)
            painter.drawRoundedRect(self.rect(), size, size)

            painter.setPen(self.TextColor)
            icon = self.icon()
            text_rect = self.rect()
            if icon:
                painter.drawPixmap(self.IconRect, self.icon())
                text_rect.setX(self.IconRect.width()+size)
            else:
                text_rect.setX(size)
                
            painter.drawText(
                text_rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                self.title()
            )
        else:
            super(ClosableGroup, self).paintEvent(event)


# メインウィンドウのクラス
class MainWindow(QtWidgets.QWidget):
    r"""
        メインウィンドウとして機能するウィジェットクラス
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(MainWindow, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
         
        # Max風スピナを作成し、初期化。----------------------------------------
        spiner = Spiner()
        spiner.setMinimum(-100000)    # スピンボックスの下限値を設定。
        spiner.setMaximum(100000)     # スピンボックスの上限値を設定。
        # ---------------------------------------------------------------------
         
        layout.addWidget(spiner)


class OButton(QtWidgets.QPushButton):
    r"""
        丸いボタンを提供するクラス。
        ラベルは表示されず、アイコンのみ。
    """
    AnimationTime = 0.08
    IconMaxRatio  = 0.9
    IconMinRatio  = 0.7
    def __init__(self, icon=None, parent=None):
        r"""
            Args:
                icon (str):セットするアイコンパス
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(OButton, self).__init__(parent)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
       )
        self.setSize(25)
        self.setBgColor(96, 96, 96)
        self.setPenColor(32, 32, 32)

        self.setIcon(icon)
        self.__penWidth       = 1
        self.__iconScaleRatio = self.IconMinRatio
        self.__enterTimerId   = None
        self.__leaveTimerId   = None
        self.__startTime      = 0.0

        self.__aBgStart = None
        self.__aBgEnd = None

    def setSize(self, size):
        r"""
            ボタンのサイズを設定する
            
            Args:
                size (int):縦横の大きさ
        """
        scaled_size = style.scaled(size)
        self.setMaximumSize(scaled_size, scaled_size)
        self.setMinimumSize(scaled_size, scaled_size)

    def sizeHint(self):
        return self.maximumSize()

    def size(self):
        r"""
            ボタンのサイズを返す
            
            Returns:
                int:
        """
        return self.maximumSize().x()

    def setBgColor(self, *rgba):
        r"""
            背景色を指定する
            
            Args:
                *rgba (tuple):RGBの3つのintを持つtuple
                
            Returns:
                any:
        """
        rgba = rgba if rgba else (96, 96, 96)
        color = RGB(rgba)
        self.__bgStart = color
        self.__bgEnd   = color + 60

        self.__bgGradient = (
            QtGui.QColor(*self.__bgStart),
            QtGui.QColor(*self.__bgEnd)
       )

    def setActiveBgColor(self, *rgba):
        r"""
            アクティブになったときの背景色を設定する
            
            Args:
                *rgba (tuple):RGBの3つのintを持つtuple
        """
        if not rgba:
            self.__aBgStart = None
            self.__aBgEnd = None
            return

        color = RGB(rgba)
        self.__aBgStart = color
        self.__aBgEnd = color + 60

    def setPenColor(self, *rgba):
        r"""
            ペンの描画色を設定する
            
            Args:
                *rgba (tuple):RGBの3つのintを持つtuple
                
            Returns:
                any:
        """
        self.__fgColor = RGB(rgba)
        self.__penColor = QtGui.QColor(*self.__fgColor)

    def setPenWidth(self, width):
        r"""
            ペンの描画幅を設定する
            
            Args:
                width (int):
        """
        self.__penWidth = int(width)

    def setIcon(self, iconPath=None):
        r"""
            ボタンに表示するアイコンのパスを設定する
            
            Args:
                iconPath (str):
        """
        self.__icon = iconPath

    def icon(self):
        r"""
            セットされているアイコンを返す
            
            Returns:
                QtGui.QImage:
        """
        if not self.__icon:
            return

        if self.isEnabled():
            return QtGui.QImage(self.__icon)
        else:
            pixmap = QtGui.QPixmap(self.__icon)
            icon = QtGui.QIcon(pixmap)
            pixmap = icon.pixmap(
                pixmap.width(), pixmap.height(), QtGui.QIcon.Disabled
           )
            return pixmap.toImage()

    def enterEvent(self, event):
        r"""
            マウスが領域内に入った時の挙動のオーバーライド
            
            Args:
                event (QtCore.QEvent):
        """
        if not self.isEnabled():
            return

        if self.isChecked():
            self.__bgGradient = (
                QtGui.QColor(*self.__bgStart),
                QtGui.QColor(*self.__bgEnd)
           )
        else:
            if not self.__aBgStart:
                self.__bgGradient = (
                    QtGui.QColor(*(self.__bgStart * 1.5)),
                    QtGui.QColor(*(self.__bgEnd   * 1.5))
               )
            else:
                self.__bgGradient = (
                    QtGui.QColor(*self.__aBgStart),
                    QtGui.QColor(*self.__aBgEnd)
               )

        self.__penColor = QtGui.QColor(*(self.__fgColor * 1.8))
        self.__iconScaleRatio = self.IconMinRatio
        
        if self.__leaveTimerId:
            self.killTimer(self.__leaveTimerId)
            self.__leaveTimerId = None
        if self.__enterTimerId:
            self.killTimer(self.__enterTimerId)

        self.__enterTimerId = self.startTimer(10)
        self.__startTime = time.time()

    def leaveEvent(self, event):
        r"""
            マウスが領域外へ出た時の挙動のオーバーライド
            
            Args:
                event (QtCore.QEvent):
        """
        if not self.isEnabled():
            return

        self.__bgGradient = (
            QtGui.QColor(*self.__bgStart),
            QtGui.QColor(*self.__bgEnd)
       )
        self.__penColor = QtGui.QColor(*self.__fgColor)
        self.__iconScaleRatio = self.IconMaxRatio
        
        if self.__enterTimerId:
            self.killTimer(self.__enterTimerId)
            self.__enterTimerId = None
        if self.__leaveTimerId:
            self.killTimer(self.__leaveTimerId)

        self.__leaveTimerId = self.startTimer(10)
        self.__startTime = time.time()

    def drawBackground(self, painter, rect):
        r"""
            背景を描画する際に呼ばれるオーバーライド用メソッド
            
            Args:
                painter (QtGui.QPainter):
                rect (QtCore.QRect):
        """
        painter.drawEllipse(rect)

    def paintEvent(self, event):
        r"""
            paintEventのオーバーライド
            
            Args:
                event (QtCore.QEVent):
        """
        rect = self.rect()
        rect.setSize(rect.size() - QtCore.QSize(2, 2))
        rect.setTopLeft(QtCore.QPoint(2, 2))
        is_checked = self.isChecked()

        painter = QtGui.QPainter(self)
        painter.setRenderHints(
            QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform
       )

        # Setup a pen and background color.------------------------------------
        pen_width = self.__penWidth
        if self.isEnabled():
            gradient = QtGui.QLinearGradient(0.0, 0.0, 0.0, rect.height())
            if is_checked:
                start, end = [x.lighter() for x in self.__bgGradient]
            else:
                start, end = [x for x in self.__bgGradient]
            gradient.setColorAt(0.0, start)
            gradient.setColorAt(1.0, end)
            brush    = QtGui.QBrush(gradient)

            penColor = self.__penColor
            if self.isDown() and not self.isCheckable():
                pen_width = self.__penWidth + 1
                penColor = QtGui.QColor(200, 200, 200)
            elif is_checked:
                penColor = penColor.lighter()
        else:
            brush    = QtGui.QColor(168, 168, 168)
            penColor = QtGui.QColor(96, 96, 96)

        pen = QtGui.QPen(penColor)
        pen.setWidth(pen_width)
        pen.setJoinStyle(QtCore.Qt.RoundJoin)
        # ---------------------------------------------------------------------

        painter.setBrush(brush)
        painter.setPen(pen)
        self.drawBackground(painter, rect)

        icon = self.icon()
        if not icon:
            return

        width  = rect.width()
        height = rect.height()
        if self.isDown() or is_checked:
            rect.setWidth(int(width * 0.75))
            rect.setHeight(int(height * 0.75))
        else:
            rect.setWidth(int(width * self.__iconScaleRatio))
            rect.setHeight(int(height * self.__iconScaleRatio))
        offset = QtCore.QPoint(
            rect.x() + (width - rect.width()) / 2,
            rect.y() + (height - rect.height()) / 2,
       )
        rect.moveTopLeft(offset)
        icon = icon.scaled(
            width, height, QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
       )
        painter.drawImage(rect, icon)

    def timerEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        passTime = time.time() - self.__startTime
        timerId  = event.timerId()
        div      = self.IconMaxRatio - self.IconMinRatio

        if timerId == self.__enterTimerId:
            if passTime > self.AnimationTime:
                self.__iconScaleRatio = self.IconMaxRatio
                self.killTimer(self.__enterTimerId)
                self.__enterTimerId = None
            else:
                self.__iconScaleRatio = (
                    self.IconMinRatio + div * passTime / self.AnimationTime
               )
            self.update()

        elif timerId == self.__leaveTimerId:
            if passTime > self.AnimationTime:
                self.__iconScaleRatio = self.IconMinRatio
                self.killTimer(self.__leaveTimerId)
                self.__leaveTimerId = None
            else:
                self.__iconScaleRatio = (
                    self.IconMaxRatio - div * passTime / self.AnimationTime
               )
            self.update()
        else:
            super(OButton, self).timerEvent(event)


class SqButton(OButton):
    r"""
        四角いボタンを提供するクラス。
        ラベルは表示されず、アイコンのみ。
    """
    def drawBackground(self, painter, rect):
        r"""
            背景を描画する際に呼ばれるオーバーライド用メソッド
            
            Args:
                painter (QtGui.QPainter):
                rect (QtCore.QRect):
        """
        painter.drawRoundedRect(rect, 4, 4)


class TitleBarWidget(QtWidgets.QWidget):
    r"""
        タイトルバー機能を提供するクラス。
    """
    StartColor = QtGui.QColor(50, 56, 161)
    EndColor = QtGui.QColor(62, 65, 190)
    TitleColorAnim = 0.8
    def __init__(self, widget, title=None):
        r"""
            引数titleは師弟がない場合はwidgetのwindowTitleを使用する。
            
            Args:
                widget (QtWidgets.QWidget):
                title (str):
        """
        super(TitleBarWidget, self).__init__(widget)
        self.__startcolor_id = None
        self.__startcolor_time = 0.0
        self.__color_opacity = 0
        self.__is_active = False
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(10, 2, 2, 2)

        label = QtWidgets.QLabel(title if title else widget.windowTitle())
        label.setStyleSheet('QLabel{font-size:16px;}')
        #label.setFont(font)
        label.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
       )
        label.mousePressEvent = self.mousePressEvent
        label.mouseMoveEvent = self.mouseMoveEvent
        label.mouseReleaseEvent = self.mouseReleaseEvent

        closeBtn = OButton()
        closeBtn.setSize(24)
        closeBtn.setBgColor(180, 42, 80, 60)
        closeBtn.setActiveBgColor(180, 42, 80)
        closeBtn.setPenWidth(1)
        closeBtn.setIcon(IconPath('uiBtn_x'))
        closeBtn.clicked.connect(self.closeWidget)

        layout.addWidget(label)
        layout.addStretch()
        layout.addWidget(closeBtn)

        self.__widget = widget
        self.__layout = layout
        self.__label  = label

    def setTitle(self, text):
        r"""
            ウィンドウタイトル名を変更する
            
            Args:
                text (str):
        """
        self.__label.setText(text)

    def title(self):
        r"""
            ウィンドウタイトル名を返す。
            
            Returns:
                str:
        """
        return self.__label.text()

    def widget(self):
        r"""
            セットさているウィジェットを返す
            
            Returns:
                QtWidgets.QWidget:
        """
        return self.__widget

    def closeWidget(self):
        r"""
            登録されているウィジェットを隠す
        """
        self.__widget.close()

    def addWidget(self, widget):
        r"""
            タイトルバーの部位にウィジェットを追加する
            
            Args:
                widget (QtWidgets.QWidget):
        """
        self.__layout.insertWidget(
            self.__layout.count()-2, widget
       )

    def addWidgetToEnd(self, widget):
        r"""
            タイトルバーの最後部にウィジェットを追加する
            
            Args:
                widget (QtWidgets.QWidget):
        """
        self.__layout.insertWidget(
            self.__layout.count()-1, widget
       )

    def addLayout(self, layout):
        r"""
            タイトルバーの部位にレイアウトを追加する
            
            Args:
                layout (QtWidgets.QLayout):
        """
        self.__layout.insertLayout(
            self.__layout.count()-2, layout
       )

    def addStretch(self):
        r"""
            タイトルバーの部位に伸縮ウィジェットを追加する
        """
        self.__layout.insertStretch(self.__layout.count()-2)

    def addSpacing(self, size):
        r"""
            固定サイズのスペースを追加する
            
            Args:
                size (int):サイズ
        """
        self.__layout.insertSpacing(
            self.__layout.count()-2, size
       )

    def setSpacing(self, size):
        r"""
            タイトルバー内のウィジェト同士の隙間の幅を設定する
            
            Args:
                size (int):スペースのサイズ
        """
        self.__layout.setSpacing(size)

    def setAlignment(self, widget, direction):
        r"""
            任意のウィジェットのアライメントを設定する
            
            Args:
                widget (QtWidgets.QWidget):追加済みウィジェット
                direction (QtCore.Qt.Alignment):
        """
        self.__layout.setAlignment(
            widget, direction
       )

    def __startChangingTitleColor(self, opacity):
        r"""
            タイトルバ－の色変更を開始する。
            
            Args:
                opacity (float):目標となる透明度
        """
        if self.__startcolor_id:
            self.killTimer(self.__startcolor_id)
        self.__is_active = True
        self.__startcolor_time = time.time()
        self.__color_opacity = opacity
        self.__startcolor_id = self.startTimer(10)

    def enterEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        self.__startChangingTitleColor(1)

    def leaveEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        self.__startChangingTitleColor(0)

class ScrolledStackedWidget(QtWidgets.QWidget):
    r"""
        スクロールして表示される拡張タブ機能を提供するクラス。
    """
    MotionTime = 0.5
    beforeMovingTab = QtCore.Signal(QtWidgets.QWidget)
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ScrolledStackedWidget, self).__init__(parent)
        self.__tabs = []
        self.__currentIndex = None

        self.__movedWidgets = []    
        self.__startTimerId = None
        self.__startTime = 0.0
        self.__direction = -1
        self.__orientation = QtCore.Qt.Horizontal

    def setOrientation(self, orientation):
        r"""
            スクロール方向を指定する
            
            Args:
                orientation (QtCore.Qt.Orientation):
        """
        self.__orientation = orientation

    def addTab(self, widget, setCurrentIndex=True):
        r"""
            タブを追加するメソッド。
            
            Args:
                widget (QtWidgets.QWidget):() :
                setCurrentIndex (bool):
        """
        widget.hide()
        widget.setParent(self)
        self.__tabs.append(widget)
        
        if len(self.__tabs) == 1 and setCurrentIndex:
            self.setCurrentIndex(0)

    def removeTab(self, widget):
        r"""
            タブを削除するメソッド。
            
            Args:
                widget (QtWidgets.QWidget):
        """
        if not widget in self.__tabs:
            return
        index = self.__tabs.index(widget)
        widget = self.__tabs.pop(index)
        widget.deleteLater()

    def clear(self):
        r"""
            すべてのタブをクリアするメソッド。
        """
        for i in range(len(self.__tabs), 0, -1):
            self.removeTab(self.__tabs[i-1])

    def count(self):
        r"""
            タブの数を返す。
            
            Returns:
                int:
        """
        return len(self.__tabs)

    def currentWidget(self):
        r"""
            現在アクティブなウィジェットを返す。
            
            Returns:
                QtWidgets.QWidget:
        """
        if self.__currentIndex is None:
            return
        return self.widgetFromIndex(self.__currentIndex)

    def currentIndex(self):
        r"""
            現在アクティブなタブのインデックスを返す。
            
            Returns:
                int:
        """
        return self.__currentIndex

    def setCurrentIndex(self, index):
        r"""
            指定したインデックスのタブへ移動する。
            
            Args:
                index (int):
        """
        if index < 0 and index > self.count() - 1:
            raise ValueError('The given index is out of range.')
        self.__currentIndex = index
        self.hideAllWidgets()
        current = self.currentWidget()
        self.beforeMovingTab.emit(current)
        current.show()

    def widgetFromIndex(self, index):
        r"""
            任意の番号のウィジェットを返す
            
            Args:
                index (int):
                
            Returns:
                QtWidgets.QWidget:
        """
        if not self.__tabs:
            return
        if index >= len(self.__tabs):
            return self.__tabs[0]
        return self.__tabs[index]

    def indexOf(self, widget):
        r"""
            任意のウィジェットの登録番号を返す
            
            Args:
                widget (QtWidgets.QWidget):
                
            Returns:
                int:
        """
        if widget in self.__tabs:
            return self.__tabs.index(widget)
        return None

    def isStart(self):
        r"""
            現在のタブが最初かどうか
            
            Returns:
                bool:
        """
        return (self.currentIndex() == 0)
        
    def isLast(self):
        r"""
            現在のタブが最後かどうか
            
            Returns:
                bool:
        """
        return (self.currentIndex() == len(self.__tabs) - 1)

    def __initializeAnim(self):
        r"""
            アニメーションの初期化を行なう
        """
        if self.__startTimerId:
            self.killTimer(self.__startTimerId)
            self.__startTimerId = None
        self.__movedWidgets = []

    def setWidgetsLayout(self):
        r"""
            self.__movedWidgetsの0番と1番に入っているウィジェットを
            このウィジェット上に配置するメソッド。
            0番目のウィジェットはこのウィジェットと同じサイズ・位置に
            配置され、1番目のウィジェットはその横（不可視領域）に
            配置される。
        """
        if not self.__movedWidgets:
            return

        for widget in self.__movedWidgets:
            widget.show()

        rect = self.rect()
        self.__movedWidgets[0].setGeometry(rect)

        rect.moveLeft(rect.x() + self.__direction * rect.width())
        self.__movedWidgets[1].setGeometry(rect)

    def allWidgets(self):
        r"""
            このウィジェットにタブとして格納されているすべての
            ウィジェットを返すメソッド。
            
            Returns:
                list:
        """
        return self.__tabs

    def hideAllWidgets(self):
        r"""
            すべてのタブを隠すメソッド。
        """
        for widget in self.__tabs:
            widget.hide()

    def next(self):
        r"""
            次のタブに移動するメソッド。
        """
        if self.isLast():
            return

        self.hideAllWidgets()
        currentIndex = self.currentIndex()
        self.__initializeAnim()
        self.__movedWidgets = [
            self.widgetFromIndex(x + currentIndex) for x in range(2)
        ]
        self.__direction = -1
        self.setCurrentIndex(currentIndex + 1)
        self.setWidgetsLayout()

        self.beforeMovingTab.emit(self.currentWidget())

        self.__startTime = time.time()
        self.__startTimerId = self.startTimer(10)

    def pre(self):
        r"""
            一つ前のタブに移動するメソッド。
        """
        if self.isStart():
            return

        self.hideAllWidgets()
        currentIndex = self.currentIndex()
        self.__initializeAnim()
        self.__movedWidgets = [
            self.widgetFromIndex(currentIndex - x) for x in range(2)
        ]
        self.__direction = 1
        self.setCurrentIndex(currentIndex - 1)
        self.setWidgetsLayout()

        self.beforeMovingTab.emit(self.currentWidget())

        self.__startTime = time.time()
        self.__startTimerId = self.startTimer(10)

    def moveTo(self, index):
        r"""
            任意のインデックスのタブに移動するメソッド。
            
            Args:
                index (int):
        """
        if index == -1:
            index = len(self.__tabs) - 1
        elif index < 0 or index >len(self.__tabs):
            raise ValueError('The given index is out of range.')
        currentIndex = self.currentIndex()
        if currentIndex == index:
            for widget in self.allWidgets():
                if not widget.isHidden():
                    return
        if index < currentIndex:
            self.__direction = 1
        else:
            self.__direction = -1

        self.hideAllWidgets()
        self.__initializeAnim()
        self.__movedWidgets = [
            self.widgetFromIndex(currentIndex), self.widgetFromIndex(index)
        ]
        self.setCurrentIndex(index)
        self.setWidgetsLayout()

        self.beforeMovingTab.emit(self.currentWidget())

        self.__startTime = time.time()
        self.__startTimerId = self.startTimer(10)

    def switchTo(self, index):
        r"""
            任意の番号のウィジェットを表示するメソッド。
            moveToと違いタブ切り替えアニメーションはしない。
            
            Args:
                index (int):
        """
        self.hideAllWidgets()
        self.__initializeAnim()
        self.setCurrentIndex(index)
        self.resizeEvent(None)

    def resizeEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        currentWidget = self.currentWidget()
        if not currentWidget:
            return
        currentWidget.setGeometry(self.rect())

    def timerEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        if event.timerId() == self.__startTimerId:
            timeRatio = (time.time() - self.__startTime) / self.MotionTime

            if timeRatio >= 1.0:
                if self.__movedWidgets[0] != self.__movedWidgets[1]:
                    self.__movedWidgets[0].hide()
                self.__initializeAnim()
                self.resizeEvent(None)
            else:
                rect = self.rect()
                preRect = self.__movedWidgets[0].rect()
                postRect = self.__movedWidgets[1].rect()
                if self.__orientation == QtCore.Qt.Horizontal:
                    dx = rect.width() * accelarate(timeRatio, 2)
                    preRect.moveLeft(dx * self.__direction)
                    postRect.moveLeft((dx - rect.width()) * self.__direction)
                else:
                    dy = rect.height() * accelarate(timeRatio, 2)
                    preRect.moveTop(dy * self.__direction)
                    postRect.moveTop((dy - rect.height()) * self.__direction)
                self.__movedWidgets[0].setGeometry(preRect)
                self.__movedWidgets[1].setGeometry(postRect)

    def keyPressEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
                
            Returns:
                any:
        """
        key = event.key()
        mod = event.modifiers()
        qt = QtCore.Qt

        if mod == qt.ControlModifier and key == qt.Key_Right:
            self.next()
        elif mod == qt.ControlModifier and key == qt.Key_Left:
            self.pre()
        else:
            super(ScrolledStackedWidget, self).keyPressEvent(event)

class FilteredLineEdit(QtWidgets.QLineEdit):
    r"""
        正規表現に’基づいて入力の制限を行うLineEditを提供する。
    """
    textFiltered = QtCore.Signal(verutil.String)
    def __init__(self, *args, **keywords):
        r"""
            Args:
                *args (tuple):
                **keywords (dict):
        """
        super(FilteredLineEdit, self).__init__(*args, **keywords)
        self.__filter = ''
        self.__compiled_obj = None
        self.textEdited.connect(self.updateText)
        self.textEdited = self.textFiltered

    def setFilter(self, filter):
        r"""
            フィルタを行う正規表現を設定する。
            
            Args:
                filter (str):
        """
        self.__filter = filter
        if not filter:
            self.__compiled_obj = None
        else:
            self.__compiled_obj = re.compile(filter)

    def filterObject(self):
        r"""
            フィルタを行う正規表現オブジェクトを返す。
            
            Returns:
                _sre.SRE_Pattern:
        """
        return self.__compiled_obj

    def filtering(self, text, result):
        r"""
            フィルタリングを行った結果を返す。
            
            Args:
                text (str):
                result (_sre.SRE_Match):
        """
        return result.group(0) if result else ''
    
    def updateText(self):
        r"""
            入力フィールドの更新を行う。
        """
        if not self.__compiled_obj:
            return

        text = self.text()
        cursor_pos = self.cursorPosition()

        result = self.__compiled_obj.search(text)
        newtext = self.filtering(text, result)
        self.setText(newtext)
        self.setCursorPosition(cursor_pos)
        self.textEdited.emit(newtext)

class FlatScrollArea(QtWidgets.QScrollArea):
    r"""
        フラットなスクロールエリアを提供するクラス
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(FlatScrollArea, self).__init__(parent)
        self.__pre_pos = None
        self.__pre_pos = None
        self.__moved = False

        widget = QtWidgets.QWidget()
        widget.setObjectName('ScrollAreaTopWidget')
        widget.setStyleSheet(
            'QWidget #ScrollAreaTopWidget{background:transparent;}'
        )
        self.buildUI(widget)
        self.setWidget(widget)
        self.setWidgetResizable(True)
        widget.installEventFilter(self)

    def buildUI(self, parent):
        r"""
            UIを作成するための記述を行うオーバーライド用メソッド
            
            Args:
                parent (QtWidgets.QWidget):
        """
        pass

    def eventFilter(self, obj, event):
        r"""
            Args:
                obj (QtCore.QObject):
                event (QtCore.QEvent):
                
            Returns:
                bool:
        """
        event_type = event.type()
        if event_type == QtCore.QEvent.MouseButtonPress:
            self.__moved = False
            self.__pre_pos = event.globalPos()
            return True
        elif event_type == QtCore.QEvent.MouseMove:
            pos = event.globalPos()
            sub = self.__pre_pos - pos
            if not self.__moved:
                if (
                    sub.manhattanLength() < 
                    QtWidgets.QApplication.startDragDistance()
                ):
                    return False
                self.setCursor(QtGui.QCursor(QtCore.Qt.ClosedHandCursor))
                self.__moved = True
            self.__pre_pos = pos
            for scl, p in zip(
                (self.verticalScrollBar(), self.horizontalScrollBar()),
                (sub.y(), sub.x())
            ):
                scl.setValue(scl.value()+p)
            return True
        elif event_type == QtCore.QEvent.MouseButtonRelease:
            self.setCursor(QtGui.QCursor())
            if self.__moved:
                return True
            else:
                return False
        return False