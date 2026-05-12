#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2025/05/13 14:20 Eske Yoshinob[eske3g@gmail.com]
        update:2025/05/13 14:22 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2025 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from collections import OrderedDict
from maya import cmds, mel

from ..uilib import mayaUIlib
from .. import uilib, node
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


def listSESelectedItems():
    r"""
        ShapeEditorで選択されているブレンドシェイプアトリビュートの一覧を返す。
        戻り値はブレンドシェイプ名をキーとし、選択されているアトリビュートの
        リストを値とするOrderedDict。

        Returns:
            OrderedDict:
    """
    selected = mel.eval('getShapeEditorTreeviewSelection 24') or []
    targets = {}
    for s in selected:
        bs, index = s.split('.')
        targets.setdefault(bs, []).append(int(index))
    results = OrderedDict()
    for bs, indices in targets.items():
        bs_n = node.asObject(bs)
        attrs = bs_n.listAttrNames()
        results[bs_n] = [attrs[x] for x in indices]
    return results


class ValueChangeButton(QtWidgets.QPushButton):
    clicked = QtCore.Signal(float)
    def __init__(self, value, withSign=False, parent=None):
        label = str(value)
        if withSign:
            if value > 0:
                label = '+' + label
        super(ValueChangeButton, self).__init__(label, parent)
        self.__pen_color = None
        self.__bg_color = None
        self.__entered = False
        self.__value = value
        self.setMinimumWidth(20)
        self.setPenColor(200, 200, 200)
        self.setBgColor(68, 82, 220, 128)
        super(ValueChangeButton, self).clicked.connect(self._emit_clicked)

    def setPenColor(self, r, g, b):
        self.__pen_color = QtGui.QColor(r, g, b)

    def penColor(self):
        return self.__pen_color
    
    def setBgColor(self, r, g, b, a=255):
        self.__bg_color = QtGui.QColor(r, g, b, a)
    
    def bgColor(self):
        return self.__bg_color
    
    def _emit_clicked(self):
        self.clicked.emit(self.__value)

    def mousePressEvent(self, event):
        mod = event.modifiers()
        if mod == QtCore.Qt.ControlModifier:
            val = min(1, max(0, self.__value + 0.05))
            self.clicked.emit(val)
            return
        super(ValueChangeButton, self).mousePressEvent(event)

    def enterEvent(self, event):
        self.__entered = True
    
    def leaveEvent(self, event):
        self.__entered = False

    def paintEvent(self, event):
        label = self.text()
        rect = event.rect()
        painter = QtGui.QPainter(self)
        painter.setRenderHints(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setPen(QtGui.QPen(self.penColor(), 1))

        if self.__entered:
            painter.setBrush(self.bgColor())
            painter.drawRect(rect)

        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawText(rect, QtCore.Qt.AlignCenter, label)


class ShapeEditorUtil(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(ShapeEditorUtil, self).__init__(parent)
        self.setWindowTitle('+Shape Editor Util')

        # 値を絶対値で変更するGUI。
        abs_btns = QtWidgets.QGroupBox('Change Selected Values(Absolute)')
        layout = QtWidgets.QHBoxLayout(abs_btns)
        layout.setSpacing(2)
        for i in range(11):
            i = round(i * 0.1, 1)
            btn = ValueChangeButton(i)
            btn.clicked.connect(self.changeAbsoluteAttr)
            layout.addWidget(btn)

        # 値を相対値で変更するGUI。
        rel_btns = QtWidgets.QGroupBox('Change Selected Values(Relative)')
        layout = QtWidgets.QHBoxLayout(rel_btns)
        layout.setSpacing(2)
        vlist = [0.025, 0.05, 0.075, 0.1]
        for value in [-x for x in reversed(vlist)] + vlist:
            btn = ValueChangeButton(value, True)
            btn.clicked.connect(self.changeRelativeAttr)
            layout.addWidget(btn)
            
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(abs_btns)
        layout.addWidget(rel_btns)
    
    def changeAbsoluteAttr(self, value):
        selected = listSESelectedItems()
        with node.DoCommand():
            for bs, attrs in selected.items():
                for attr in attrs:
                    bs(attr, value)

    def changeRelativeAttr(self, value):
        selected = listSESelectedItems()
        with node.DoCommand():
            for bs, attrs in selected.items():
                for attr in attrs:
                    v = min(1, max(0, bs(attr) + value))
                    bs(attr, v)
        

class MainGUI(uilib.AbstractSeparatedWindow):
    r"""
        メインとなるGUIを提供するクラス
    """
    def centralWidget(self):
        r"""
            中心となるメインウィジェットを作成して返す
            
            Returns:
                FacialExpressionManager:
        """
        return ShapeEditorUtil()


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。
        
        Returns:
            QtWidgets.QWidget:
    """
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(uilib.hires(300), uilib.hires(450))
    widget.show()
    return widget

