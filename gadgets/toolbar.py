#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    GRIS用ツールバーを提供するモジュール
    
    Dates:
        date:2018/01/30 18:14[eske](eske3g@gmail.com)
        update:2025/08/02 12:20 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2018 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import time
from gris3.uilib import mayaUIlib
from gris3 import lib, uilib, node
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


# /////////////////////////////////////////////////////////////////////////////
# ツールバーに追加するプリセット。                                           //
# /////////////////////////////////////////////////////////////////////////////
CLEANUP_TOOL = (
        'gris3.gadgets.cleanupTools.CleanupToolWidget',
        (128, 128, 128),
        uilib.IconPath('uiBtn_option')
)
MODELING_TOOL = (
        'gris3.gadgets.modelSetupWidget.ModelSetupWidget',
        (36, 80, 180),
        uilib.IconPath('unit')
)
SIM_TOOL = (
        'gris3.gadgets.simUtility.ui.MainWidget',
        (36, 80, 180),
        uilib.IconPath('uiBtn_stop')
)
POSE_TOOL = (
        'gris3.gadgets.animLibrary.ui.MainWidget',
        (36, 80, 180),
        uilib.IconPath('uiBtn_squareLayout')
)

STANDALONE_TOOLBAR = [
    CLEANUP_TOOL,
    None,
    MODELING_TOOL,
    None,
    (
        'gris3.gadgets.jointEditorWidget.JointEditor',
        (48, 96, 180),
        uilib.IconPath('uiBtn_skeleton')
    ),
    None,
    (
        'gris3.gadgets.drivenManager.DrivenUtility',
        (160, 25, 59),
        uilib.IconPath('uiBtn_drivenKey'),
        True
    ),
    None,
    (
        'gris3.gadgets.ctrlShapeEditor.ControllerShapeEditor',
        (141, 182, 99),
        uilib.IconPath('uiBtn_ctrl'),
        True
    ),
    None,
    SIM_TOOL,
    POSE_TOOL,
    (
        'gris3.gadgets.gadgetsLauncher.Launcher',
        (180, 96, 15),
        uilib.IconPath('uiBtn_view'),
    ),
]

FACTORY_TOOLBAR = [
    CLEANUP_TOOL,
    MODELING_TOOL,
    None,
    SIM_TOOL,
    POSE_TOOL
]
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////


class ToolbarView(QtWidgets.QWidget):
    r"""
        ツールバー下部にUIを表示するための機能を提供するクラス。
    """
    ButtonSize = uilib.hires(38)

    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ToolbarView, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.__tab = QtWidgets.QStackedWidget()
        self.__lock = False
        self.__hide_timer_id = None
        self.__entered_time = None
        self.__wait_time = 0.5
        self.__pre_parent_pos = None
        self.__gradient = QtGui.QLinearGradient()
        self.__gradient.setColorAt(0, QtGui.QColor(22, 42, 68, 240))
        self.__gradient.setColorAt(1, QtGui.QColor(0, 0, 0, 175))

        layout = QtWidgets.QVBoxLayout(self)
        layout.addSpacing(self.ButtonSize)
        layout.addWidget(self.__tab)

    def addWidget(self, widget, withStretch=False):
        r"""
            タブを追加する。
            withStretchがTrueの場合、追加ウィジェットの下にストレッチ領域を
            追加する。
            
            Args:
                widget (QtWidgets.QWidget):
                withStretch (bool):追加ウィジェットの下にストレッチを追加するか
        """
        p = QtWidgets.QWidget()
        p.setObjectName('scrolled_baseWidget')
        s = QtWidgets.QScrollArea()
        s.setWidgetResizable(True)
        s.setWidget(p)
        layout = QtWidgets.QVBoxLayout(p)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        label = widget.windowTitle()
        if label:
            label_widget = QtWidgets.QLabel(label)
            label_widget.setStyleSheet(
                'QLabel{font-size:%spx;}'%(uilib.hires(20))
            )
            layout.addWidget(label_widget)
        layout.addWidget(widget)
        if withStretch:
            layout.addStretch()
        self.__tab.addWidget(s)

    def setCurrentIndex(self, index):
        r"""
            任意の番号のタブに切り替える。
            
            Args:
                index (int):任意のタブ番号
        """
        if not (-1 < index < self.__tab.count()):
            return
        self.__tab.setCurrentIndex(index)

    def startToHide(self, count=100):
        r"""
            引き数count ms秒経過したら自身を非表示にするタイマーを開始する
            
            Args:
                count (int):
        """
        if self.__hide_timer_id:
            self.killTimer(self.__hide_timer_id)
        self.__hide_timer_id = self.startTimer(count)

    def show(self):
        self.__entered_time = time.time()
        self.__lock = False
        if self.parent():
            p = self.parent()
            self.__pre_parent_pos = p.mapToGlobal(p.pos())
        else:
            self.__pre_parent_pos = None
        super(ToolbarView, self).show()

    def hide(self):
        self.__lock = False
        self.__entered_time = None
        self.__pre_parent_pos = None
        super(ToolbarView, self).hide()

    def setWaitTime(self, t):
        r"""
            マウスがウィジェットに侵入してから自動非表示機能を無効にするまでの
            ウェイト時間を設定する。

            Args:
                t (float):
        """
        self.__wait_time = t

    def waitTime(self):
        r"""
            マウスがウィジェットに侵入してから自動非表示機能を無効にするまでの
            ウェイト時間を返す。

            Returns:
                float:
        """
        return self.__wait_time

    def timerEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        if event.timerId() == self.__hide_timer_id:
            self.killTimer(self.__hide_timer_id)
            self.hide()

    def enterEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        if self.__pre_parent_pos:
            p = self.parent()
            if p.mapToGlobal(p.pos()) != self.__pre_parent_pos:
                self.hide()
                return
        parent = self.parent()
        while(parent):
            if not parent.isVisible():
                self.hide()
                return
            parent = parent.parent()

        if self.__hide_timer_id:
            self.killTimer(self.__hide_timer_id)
        self.__hide_timer_id = None
        self.__entered_time = time.time()

    def leaveEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        if (
            self.__entered_time
            and time.time() - self.__entered_time > self.waitTime()
        ):
            self.__lock = True
        if self.__lock:
            return
        self.hide()

    def paintEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        painter = QtGui.QPainter(self)
        rect = self.rect()
        rect.setTop(self.ButtonSize)

        self.__gradient.setFinalStop(0, rect.height())
        painter.setBrush(QtGui.QBrush(self.__gradient))
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0)))
        painter.drawRect(rect)


class ToolbarButton(uilib.OButton):
    r"""
        タブ式のウィジェットを表示するためのボタン。
        ボタンだが、マウスオーバーした時に反応するようになっている点が
        通常のボタンと違う点。
    """
    mouseEntered = QtCore.Signal(QtWidgets.QWidget)
    commandRequested = QtCore.Signal(QtWidgets.QWidget)
    DelayedTime = 150
    def __init__(self, icon=None):
        r"""
            Args:
                icon (str):使用するアイコンのパス
        """
        super(ToolbarButton, self).__init__(icon)
        self.__no_delay = False
        self.__signal_emission_timer = None

    def setNoDelay(self, state):
        r"""
            マウスオーバーした際にcommandRequestedを遅れて送出しない
            かどうかを指定する
            
            Args:
                state (bool):
        """
        self.__no_delay = bool(state)

    def stopEmissionTimer(self):
        r"""
            commandRequestedを発行するタイマーを停止する。
        """
        if self.__signal_emission_timer is None:
            return
        self.killTimer(self.__signal_emission_timer)
        self.__signal_emission_timer = None

    def enterEvent(self, event):
        r"""
            マウスオーバーした際にcommandRequestedシグナルを送出する
            
            Args:
                event (QtCore.QEvent):
        """
        super(ToolbarButton, self).enterEvent(event)
        if self.__no_delay:
            self.stopEmissionTimer()
            self.commandRequested.emit(self)
        else:
            self.mouseEntered.emit(self)
            self.__signal_emission_timer = self.startTimer(self.DelayedTime)

    def leaveEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        super(ToolbarButton, self).leaveEvent(event)
        self.stopEmissionTimer()

    def timerEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        super(ToolbarButton, self).timerEvent(event)
        if event.timerId() == self.__signal_emission_timer:
            self.commandRequested.emit(self)
            self.killTimer(self.__signal_emission_timer)
            self.__signal_emission_timer = None


class Toolbar(QtWidgets.QWidget):
    r"""
        ボタンが並んだツールバーを提供するウィジェット。
    """
    ButtonSize = 28
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QObject):親ウィジェット
        """
        super(Toolbar, self).__init__(parent)
        self.setWindowTitle('+Tool Bar - GRIS')
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        layout.addSpacing(self.ButtonSize)
        layout.addStretch()
        self.__widget_count = 0
        self.__btnlist = []
        self.__attached_view = ToolbarView(self)
        self.__attached_view.ButtonSize = self.ButtonSize

    def addSeparator(self):
        r"""
            セパレーターを追加する
        """
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.VLine)
        separator.setLineWidth(1)
        p = separator.palette()
        p.setColor(QtGui.QPalette.WindowText, QtGui.QColor(255, 255, 255))
        p.setColor(QtGui.QPalette.Window, QtGui.QColor(255, 255, 255))
        separator.setPalette(p)
        self.layout().insertWidget(
            self.layout().count() - (1 + self.__widget_count), separator
        )

    def addButton(self, widgetType, color=None, icon=None, withStretch=False):
        r"""
            ウィジェットと呼び出すボタンを追加する。
            引き数widgetTypeにはビューに追加したウィジェットを表す文字列を
            追加する。
            gris.tools.modelSetupWidgetのModelSetupWidgetクラスが必要な場合は
            gris.tools.modelSetupWidget.ModelSetupWidgetと記述する。
            
            Args:
                widgetType (str):QWidgetのサブクラスの場所を表す文字列
                color (tuple):R,G,Bの３つを持つタプル
                icon (str):ボタンに表示するアイコンパス。
                withStretch (bool):
        """
        module_name, class_name = widgetType.rsplit('.', 1)
        import importlib
        module = importlib.import_module(module_name)
        type_obj = getattr(module, class_name)

        tb = ToolbarButton()
        tb.setSize(self.ButtonSize)
        if isinstance(color, tuple):
            tb.setBgColor(*color)
        if icon:
            tb.setIcon(icon)
        tb.mouseEntered.connect(self.setupButtons)
        tb.commandRequested.connect(self.showView)
        self.layout().insertWidget(
            self.layout().count() - (1 + self.__widget_count), tb
        )
        self.__btnlist.append(tb)
        
        self.__attached_view.addWidget(type_obj(), withStretch)

    def addPreset(self, preset):
        r"""
            プリセットを追加する
            
            Args:
                preset (list):
        """
        for data in preset:
            if not isinstance(data, (tuple, list)):
                self.addSeparator()
                continue
            s = data[3] if len(data) == 4 else False
            self.addButton(data[0], data[1], data[2], s)

    def showView(self, widget):
        r"""
            ビューを表示する。
            
            Args:
                widget (ToolbarButton):
        """
        if not widget in self.__btnlist:
            return
        index = self.__btnlist.index(widget)
        rect = self.rect()
        rect.moveTopLeft(self.mapToGlobal(rect.topLeft()))
        rect.setHeight(uilib.hires(500))
        self.__attached_view.setGeometry(rect)
        self.__attached_view.setCurrentIndex(index)
        self.__attached_view.show()

    def setupButtons(self, widget):
        r"""
            全てのボタンのsetNoDelayをTrueに変更する。
            
            Args:
                widget (ToolbarButton):
        """
        for btn in self.__btnlist:
            btn.setNoDelay(True)

    def addWidget(self, widget):
        r"""
            ツールバーの末端にウィジェットを追加する。
            
            Args:
                widget (QtWidgets.QWidget):追加するウィジェット
        """
        self.layout().addWidget(widget)
        self.__widget_count += 1

    def leaveEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        super(Toolbar, self).leaveEvent(event)
        self.__attached_view.startToHide()
        for btn in self.__btnlist:
            btn.setNoDelay(False)


class MainGUI(uilib.AbstractSeparatedWindow):
    r"""
        メインとなるGUIを提供するクラス
    """
    def centralWidget(self):
        r"""
            Returns:
                Toolbar:
        """
        self.setScalable(QtCore.Qt.Horizontal)
        toolbar = Toolbar()
        toolbar.addPreset(STANDALONE_TOOLBAR)
        return toolbar


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。
        
        Returns:
            MainGUI:
    """
    from gris3.uilib import mayaUIlib
    widget = MainGUI(mayaUIlib.MainWindow)
    m = uilib.hires(2)
    widget.layout().setContentsMargins(m, m, m, m)
    widget.resize(uilib.hires(600), uilib.hires(30))
    widget.show()
    return widget

