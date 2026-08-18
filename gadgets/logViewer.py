#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    テキストベースのログを表示するためのガジェットを提供するクラス。

    Dates:
        date:2017/07/06 5:35[Eske](eske3g@gmail.com)
        update:2020/10/12 15:09 eske yoshinob[eske3g@gmail.com]

    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from ..uilib import mayaUIlib
from .. import uilib, style
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


Viewer = None


class LogViewer(uilib.BlackoutDisplay):
    def __init__(self, parent=None):
        super().__init__(parent)
        font_size = 14
        self.setStyleSheet(style.styleSheet())
        self.__message_stack = []

        self.__main_widget = QtWidgets.QWidget(self)

        label = QtWidgets.QLabel('Log')
        font = label.font()
        font.setPointSize(font_size)
        label.setFont(font)

        msg = QtWidgets.QLabel('See detail in the Script Editor.')

        self.__text_field = QtWidgets.QTextEdit()
        self.__text_field.setReadOnly(True)
        font = self.__text_field.font()
        font.setPointSize(font_size)
        self.__text_field.setFont(font)

        close_btn = uilib.OButton(uilib.IconPath('uiBtn_x'))
        close_btn.setSize(32)
        close_btn.clicked.connect(self.hide)

        layout = QtWidgets.QVBoxLayout(self.__main_widget)
        layout.addWidget(label)
        layout.addWidget(msg)
        layout.addWidget(self.__text_field)
        layout.addWidget(close_btn)
        layout.setAlignment(close_btn, QtCore.Qt.AlignCenter)

    def addMessage(self, message):
        r"""
        メッセージをビューワに追加する。
        その際print関数が呼ばれるため、ログにもメッセージ内容が残る。

        Args:
            message(str):
        """
        self.__message_stack.append(message)
        print(message)

    def clearMessage(self):
        r"""
        スタックされたメッセージ内容をすべてクリアする。
        """
        self.__message_stack.clear()

    def mainWidget(self):
        return self.__main_widget

    def show(self):
        self.__text_field.setText('\n'.join(self.__message_stack))
        super().show()

        rect = self.rect()
        height = int(rect.height() * 0.8)
        width = int(height * 0.75)
        rect.setWidth(width)
        rect.setHeight(height)
        rect.moveCenter(self.rect().center())
        self.mainWidget().setGeometry(rect)


def getViewer(withClear=True):
    r"""
        シングルトンのログビューワーを返す。

    Args:
        withClear(bool):ビューワ取得時に、ビューワ内のログをクリアするかどうか

    Returns:
        LogViewer
    """
    global Viewer
    if Viewer is None:
        Viewer = LogViewer(mayaUIlib.MainWindow)
    if withClear:
        Viewer.clearMessage()
    return Viewer