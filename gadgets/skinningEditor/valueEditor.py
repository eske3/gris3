#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    バインド操作を助ける機能郡を提供するGUI。
    
    Dates:
        date:2017/06/15 16:35[Eske](eske3g@gmail.com)
        update:2020/07/29 13:04 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from ...tools import paintSkinUtility
from ... import lib, uilib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class ValueEditor(uilib.ConstantWidget):
    r"""
        ペイントのOpacityを編集するウィジェット
    """
    def buildUI(self):
        r"""
            GUIの構築を行う。
        """
        margin = 40
        self.setHiddenTrigger(self.HideByCursorOut)
        self.setScalable(False)
        self.resize(300, 150)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.__skincluster = None
        self.__operation = None

        from ... import style
        title = QtWidgets.QLabel('+ Edit Value')
        title.setStyleSheet(style.TitleLabel)
        self.setTitle = title.setText
        
        label = QtWidgets.QLabel('Opacity')
        editor = QtWidgets.QDoubleSpinBox()
        editor.setRange(0, 1)
        editor.setSingleStep(0.02)
        editor.valueChanged.connect(self.updateOpacity)
        self.setValue = editor.setValue
        self.selectField = editor.selectAll
        
        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(20)
        layout.addWidget(title, 0, 0, 1, 2)
        layout.addWidget(label, 1, 0, 1, 1, QtCore.Qt.AlignRight)
        layout.addWidget(editor, 1, 1, 1, 1)
        layout.setRowStretch(2, 1)

    def setup(self, skinCluster, operation):
        r"""
            編集対象をセットする
            
            Args:
                skinCluster (str):スキンクラスタ名
                operation (str):操作タイプ
        """
        self.__skincluster = skinCluster
        self.__operation = operation
        self.setTitle('+ Edit %s Value' % lib.title(operation))
        self.setValue(
            paintSkinUtility.getOperationOpacity(operation, skinCluster)
        )

    def updateOpacity(self, value):
        r"""
            Args:
                value (float):
        """
        paintSkinUtility.changeOperationOpacity(
            self.__operation, value, self.__skincluster
        )

    def show(self):
        r"""
            スキンクラスタと操作タイプが設定されている時だけ表示する
        """
        if not self.__skincluster or not self.__operation:
            return
        self.selectField()
        super(ValueEditor, self).show()

    def paintEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        painter = QtGui.QPainter(self)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(0, 20, 55, 190))
        painter.drawRoundedRect(self.rect(), 8, 8)


class PaintValueButton(QtWidgets.QPushButton):
    r"""
        右ボタンをクリックされた事を検知する拡張ボタン
    """
    rightButtonPressed = QtCore.Signal()
    def __init__(self, *args, **keywords):
        r"""
            Args:
                *args (tuple):QPushButtonに渡す引数と同じ
                **keywords (dict):QPushButtonに渡す引数と同じ
        """
        super(PaintValueButton, self).__init__(*args, **keywords)
        self.setToolTip(
            'Hit by right button then show an editor to change a value.'
        )
        self.__is_right_clicked = False

    def mousePressEvent(self, event):
        r"""
            Args:
                event (QtCore.QEVent):
        """
        self.__is_right_clicked = event.button() == QtCore.Qt.RightButton
        if self.__is_right_clicked:
            self.rightButtonPressed.emit()
        super(PaintValueButton, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        r"""
            Args:
                event (QtCore.QEVent):
        """
        if not self.__is_right_clicked:
            super(PaintValueButton, self).mouseReleaseEvent(event)

