#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    カメラ設定を簡易的に行うための機能を提供する。
    
    Dates:
        date:2018/10/31 6:24[Eske](eske3g@gmail.com)
        update:2022/05/21 09:57 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2018 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import uilib, style, node, lib
from gris3.uilib import mayaUIlib, colorPicker
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

class ClipplaneSelector(QtWidgets.QGroupBox):
    r"""
        カメラのclippingPlaneのプリセットGUI
    """
    def __init__(self, parent=None):
        r"""
            クリッピングプレーンのプリセット値の設定を行う。
            
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ClipplaneSelector, self).__init__(
            'Clipping Plane Preset', parent
        )
        layout = QtWidgets.QGridLayout(self)
        layout.setSpacing(1)

        row = 0
        for which, values in (
            ('near', (0.1, 1, 10, 100)),
            ('far', (1000, 10000, 100000, 1000000)),
        ):
            layout.addWidget(QtWidgets.QLabel(which.title()), row, 0, 1, 1)
            for i, value in enumerate(values, 1):
                btn = QtWidgets.QPushButton(str(value))
                btn.value = value
                btn.which = which
                btn.clicked.connect(self.setClippingPlane)

                layout.addWidget(btn, row, i, 1, 1)
            row += 1

    def setClippingPlane(self):
        r"""
            シグナル転送元のボタンの値をクリッピングプレーンにセットする
        """
        camera = node.asObject(mayaUIlib.getActiveCamera())
        if not camera:
            return
        btn = self.sender()
        camera('%sClipPlane'%btn.which, btn.value)


class CameraDisplaySettings(QtWidgets.QGroupBox):
    r"""
        カメラの表示に関わる設定GUIを提供する
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(CameraDisplaySettings, self).__init__('Camera Display Settings')
        layout = QtWidgets.QFormLayout(self)
        
        self.__double_ui = []
        for attr, min_max, factor in (
            ('focalLength', (2.5, 100000.0), 1),
            ('overscan', (0.0, 100000.0), 0.1),
            ('displayGateMaskOpacity', (0.0, 1.0), 0.1),
        ):
            ui = uilib.DoubleSpiner()
            ui.attrName = attr
            ui.setRange(*min_max)
            ui.valueChanged.connect(self.setCameraAttr)
            ui.setSingleStep(factor)
            ui.ButtonFactor = {
                QtCore.Qt.LeftButton : 1.0*factor,
                QtCore.Qt.MiddleButton : 10.0*factor,
                QtCore.Qt.RightButton  : 100.0*factor,
            }
            ui.setPressedCallback(mayaUIlib.beginCommand)
            ui.setReleasedCallback(mayaUIlib.endCommand)
            self.__double_ui.append(ui)
            layout.addRow(lib.title(attr), ui)

        self.__color_picker = colorPicker.ColorPickerWidget()
        self.__color_picker.colorIsSet.connect(self.setGateMaskColor)
        layout.addRow(lib.title('displayGateMaskColor'), self.__color_picker)
        

    def setCameraAttr(self, value):
        r"""
            カメラのアトリビュートを変更する
            
            Args:
                value (float):変更後の値
        """
        camera = node.asObject(mayaUIlib.getActiveCamera())
        if not camera:
            return
        ui = self.sender()
        camera(ui.attrName, value)

    def setGateMaskColor(self, r, g, b):
        camera = node.asObject(mayaUIlib.getActiveCamera())
        if not camera:
            return
        camera('displayGateMaskColor', [x/255.0 for x in (r, g, b)])

    def setup(self, camera):
        r"""
            引数のカメラの設定をGUIに反映させる
            
            Args:
                camera (node.Transform):
        """
        for ui in self.__double_ui:
            ui.setValue(camera(ui.attrName))
        self.__color_picker.setColorRgb(camera('displayGateMaskColor')[0])


class MainGUI(QtWidgets.QWidget):
    r"""
        メインとなるGUI
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(MainGUI, self).__init__(parent)
        margin = 25
        self.setStyleSheet(style.styleSheet())
        clip_plane = ClipplaneSelector()
        disp_settings = CameraDisplaySettings()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.addWidget(clip_plane)
        layout.addWidget(disp_settings)
        layout.addStretch()
        
        self.__updater = [disp_settings]

    def setup(self):
        r"""
            アクティブカメラを特定し、そのカメラの設定をGUIに反映する。
            アクティブカメラが特定出来なかった場合はFalseを返し何もしない。
            
            Returns:
                bool:
        """
        camera = node.asObject(mayaUIlib.getActiveCamera())
        if not camera:
            return False
        for w in self.__updater:
            w.setup(camera)
        return True

class SeparatedWindow(uilib.AbstractSeparatedWindow):
    r"""
        単独使用用の独立ウィンドウを提供するクラス
    """
    def centralWidget(self):
        r"""
            メインとなるウィジェットを返す。
            
            Returns:
                MainGUI:
        """
        self.setHiddenTrigger(self.HideByFocusOut)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        return MainGUI()

    def paintEvent(self, event):
        r"""
            paintEventの再実装メソッド
            
            Args:
                event (QtCore.QEvent):
        """
        painter = QtGui.QPainter(self)
        painter.setRenderHints(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0)))
        painter.setBrush(QtGui.QColor(60, 60, 60))
        painter.drawRect(self.rect())

    def show(self):
        r"""
            表示のオーバーライド。
            表示前にメインGUIのセットアップを行う
        """
        gui = self.main()
        if not gui.setup():
            return
        super(SeparatedWindow, self).show()


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。
        
        Returns:
            SeparatedWindow:
    """
    from gris3.uilib import mayaUIlib
    widget = SeparatedWindow(mayaUIlib.MainWindow)
    widget.resize(400, 600)
    widget.show()
    return widget