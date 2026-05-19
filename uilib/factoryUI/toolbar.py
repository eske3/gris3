#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Factory用のツールバーを提供するモジュール。

    Dates:
        date:2017/01/21 23:48[Eske](eske3g@gmail.com)
        update:2026/05/16 19:13 eske yoshinob[eske3g@gmail.com]

    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import time
from ... import uilib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class ToolBar(QtWidgets.QScrollArea):
    r"""
        ドラッグによるスクロール可能なツールバー機能を提供する
    """
    buttonClicked = QtCore.Signal(int)

    def __init__(self, parent=None, isButtonGrouped=False):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
                isButtonGrouped (bool):ボタンをグループ化するかどうか
        """
        super(ToolBar, self).__init__(parent)
        self.setStyleSheet(
            'QScrollArea{'
            'background:transparent; border:none;'
            'margin : 0px;'
            '}'
        )
        self.setWidgetResizable(True)
        self.setContentsMargins(0, 0, 0, 0)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        self.__prepos = None
        self.__ismoved = False
        self.__pressed_time = 0

        widget = QtWidgets.QWidget()
        widget.setStyleSheet(
            'QWidget{background:transparent;}'
        )
        self.__layout = QtWidgets.QHBoxLayout(widget)
        self.__layout.setSpacing(2)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.__layout.addStretch()

        self.setWidget(widget)
        self.setButtonSize(32)

        self.__btn_grp = None
        if isButtonGrouped:
            self.__btn_grp = QtWidgets.QButtonGroup()
            self.__btn_grp.buttonClicked.connect(self.emitButtonGroupClicking)

    def setAlighment(self, alignment):
        r"""
            ツールバーのボタン配置の整列方向を指定する

            Args:
                alignment (QtCore.Qt.Alignment):
        """
        self.__layout.setAlignment(alignment)

    def scroll(self, moveValues):
        r"""
            このウィジェットのビューポートをスクロールさせるメソッド。

            Args:
                moveValues (list):
        """
        h_scroll = self.horizontalScrollBar()
        v_scroll = self.verticalScrollBar()
        for scroll, value in zip(
                [h_scroll, v_scroll], [moveValues.x(), moveValues.y()]
        ):
            scroll.setValue(scroll.value() - value)

    def mousePressEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        button = event.button()
        self.__prepos = event.pos()
        super(ToolBar, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        if not self.__prepos:
            super(ToolBar, self).mouseMoveEvent(event)
            return
        current_pos = event.pos()
        delta = current_pos - self.__prepos
        self.__prepos = current_pos
        self.scroll(delta)

    def mouseReleaseEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        self.__prepos = None
        super(ToolBar, self).mouseReleaseEvent(event)

    def setButtonSize(self, size):
        r"""
            ボタンの大きさを指定する

            Args:
                size (int):
        """
        self.__size = size
        self.setMaximumHeight(uilib.hires(size + 2))

    def addButton(self, icon=None, toolTip=''):
        r"""
            ボタンを追加する

            Args:
                icon (str):ボタンに配置するアイコン
                toolTip (str):ボタンに付けるツールチップ

            Returns:
                uilib.OButton:
        """
        btn = uilib.OButton(icon)
        btn.setSize(self.__size)
        btn.setToolTip(toolTip)
        btn.installEventFilter(self)
        index = self.__layout.count() - 1
        self.__layout.insertWidget(index, btn)
        if self.__btn_grp:
            self.__btn_grp.addButton(btn, index)
            btn.setCheckable(True)
            if index == 0:
                btn.setChecked(True)
        else:
            btn.clicked.connect(self.clickedCallback)
        return btn

    def clickedCallback(self):
        r"""
            ボタンをクリックされた時に呼ばれるコールバック
        """
        index = self.__layout.indexOf(self.sender())
        self.buttonClicked.emit(index)

    def emitButtonGroupClicking(self, button):
        index = self.__btn_grp.id(button)
        self.buttonClicked.emit(index)

    def eventFilter(self, object, event):
        r"""
            Args:
                object (QtCore.QObject):
                event (QtCore.QEvent):
        """
        event_type = event.type()
        if event_type == QtCore.QEvent.MouseButtonPress:
            self.mousePressEvent(event)
            self.__ismoved = False
            self.__pressed_time = time.time()
            return False
        elif event_type == QtCore.QEvent.MouseMove:
            self.mouseMoveEvent(event)
            self.__ismoved = True
            return True
        elif event_type == QtCore.QEvent.MouseButtonRelease:
            if self.__ismoved:
                hold_time = time.time() - self.__pressed_time
                self.__ismoved = False
                self.mouseReleaseEvent(event)

                if hold_time > 0.4:
                    return True
            return False
        else:
            return False


class ToolTabWidget(QtWidgets.QWidget):
    r"""
        ツールバー付きのタブ機能を提供するクラス。
    """
    SaveColor = (62, 79, 210)
    ToolColor = (48, 156, 102)

    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ToolTabWidget, self).__init__(parent)

        self.__tab = uilib.ScrolledStackedWidget(self)
        self.__toolbar = ToolBar(self, True)
        self.__toolbar.buttonClicked.connect(self.__tab.moveTo)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.__toolbar)
        layout.addWidget(self.__tab)

        self.setCurrentIndex = self.__tab.setCurrentIndex

    def setToolBarSize(self, size):
        r"""
            ツールバーのボタンサイズを設定する。

            Args:
                size (int):
        """
        self.__toolbar.setButtonSize(size)

    def addTab(self, widget, icon=None, toolTip=''):
        r"""
            タブを追加する。

            Args:
                widget (QtWidgets.QWidget):
                icon (str):アイコンのパス
                toolTip (str):ツールチップ

            Returns:
                uilib.OButton:
        """
        btn = self.__toolbar.addButton(icon, toolTip)
        self.__tab.addTab(widget)
        return btn

