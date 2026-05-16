#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ファイル表示用のビューワ機能を提供するモジュール。

    Dates:
        date:2017/01/21 23:48[Eske](eske3g@gmail.com)
        update:2026/05/16 19:13 eske yoshinob[eske3g@gmail.com]

    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
from . import browser
from ... import uilib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

class FileView(QtWidgets.QWidget):
    r"""
        ファイルの一覧および保存をするためのUIを提供するクラス。
    """
    exportButtonClicked = QtCore.Signal(str, str)

    def __init__(self):
        super(FileView, self).__init__()

        brs = browser.ModuleBrowserWidget()
        brs.installCustomFilter(browser.ModuleBrowser.removeCurFilter)
        brs.clicked.connect(self.updateBasename)
        self.setBrowserContext = brs.setBrowserContext

        # ファイルパスに関するUI。=============================================
        basename_label = QtWidgets.QLabel('Basename')
        self.__basename = self.createBasenameEditor()

        self.__isOverwrite = QtWidgets.QCheckBox('Overwrite to latest')
        self.__isOverwrite.setChecked(False)

        exp_button = uilib.OButton()
        exp_button.setIcon(uilib.IconPath('uiBtn_export'))
        exp_button.setBgColor(48, 138, 158)
        exp_button.setSize(48)
        exp_button.clicked.connect(self.execute)

        grp = QtWidgets.QGroupBox()
        grp_layout = QtWidgets.QGridLayout(grp)
        grp_layout.setContentsMargins(2, 2, 2, 2)
        grp_layout.addWidget(basename_label, 0, 0, 1, 1)
        grp_layout.addWidget(self.__basename, 0, 1, 1, 1)
        grp_layout.addWidget(self.__isOverwrite, 1, 0, 1, 2)
        grp_layout.addWidget(exp_button, 0, 2, 2, 1)
        # =====================================================================

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(1)
        layout.addWidget(brs)
        layout.addWidget(grp)

        self.__browser = brs
        self.__button = exp_button

        self.addOptionWidget = grp_layout.addWidget
        self.addOptionLayout = grp_layout.addLayout

    def createBasenameEditor(self):
        r"""
            ベースネームを編集するウィジェットを作成し返す。
            返すウィジェットはsetTextとtextメソッドを持つ必要がある。

            Returns:
                QtWidgets.QWidget:
        """
        return QtWidgets.QLineEdit()

    def setExtensions(self, extensions):
        r"""
            ブラウザが対応する拡張子をセットする。

            Args:
                extensions (list):
        """
        self.browser().setExtensions(extensions)

    def browser(self):
        r"""
            ブラウザを返すメソッド。

            Returns:
                ModuleBrowserWidget:
        """
        return self.__browser

    def basenameEdit(self):
        r"""
            ベースネームをセットするためのウィジェットを返す。

            Returns:
                QtWidgets.QLineEdit:
        """
        return self.__basename

    def setBrowserLabel(self, label):
        r"""
            ブラウザのラ・ベルを設定する。

            Args:
                label (str):
        """
        self.browser().setLabel(label)

    def setButtonIcon(self, iconPath):
        r"""
            ボタンのアイコンを変更する。

            Args:
                iconPath (str):
        """
        self.__button.setIcon(iconPath)

    def setButtonLabel(self, label):
        r"""
            ボタンのツールチップを変更する。

            Args:
                label (str):
        """
        self.__button.setToolTip(label)

    def updateBasename(self):
        r"""
            ファイルのベースの名前を更新する
        """
        selected = self.browser().selectedItems()
        if not selected:
            return
        name = os.path.basename(selected[0])
        self.__basename.setText(name)

    def setRootPath(self, path):
        r"""
            ルートディレクトリのパスをセットする

            Args:
                path (str):
        """
        brs = self.browser()
        brs.setPath(path)
        path = brs.path()
        self.setEnabled(bool(path))

    def path(self):
        r"""
            ルートディレクトリのパスを返す。

            Returns:
                str:
        """
        return self.browser().path()

    def filename(self):
        r"""
            ファイルネームを返す

            Returns:
                str:
        """
        return self.__basename.text()

    def isOverwrite(self):
        r"""
            上書きするかどうかを返すメソッド。

            Returns:
                bool:
        """
        return self.__isOverwrite.isChecked()

    def execute(self):
        r"""
            入力されている名前をexportButtonClickedシグナルで送出する
        """
        rootpath = self.path()
        filename = self.filename()
        if not filename:
            raise ValueError('The file name is empty.')

        if not os.path.isdir(rootpath):
            raise ValueError(
                'The parent directory was not found : %s' % rootpath
            )
        self.exportButtonClicked.emit(rootpath, filename)
        self.__isOverwrite.setChecked(False)
        self.browser().refresh()
