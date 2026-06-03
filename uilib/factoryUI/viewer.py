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
from ... import uilib, fileUtil
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class ModuleBrowserWidget(QtWidgets.QWidget):
    r"""
        ModuleBrowserの上位互換ウィジェット。
        リフレッシュボタンやエクスプローラーで開くボタンなどが追加されている他、
        メソッド的にもほぼModuleBrowserを踏襲している。
    """

    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget): 親ウィジェット。
        """
        super(ModuleBrowserWidget, self).__init__(parent)

        self.__browser = browser.ModuleBrowser()
        # ブラウザのメソッドをそのまま移植する。===============================
        for cmd in (
                'setLabel', 'installCustomFilter', 'customFilter',
                'setCoordinator', 'coordinate', 'refresh', 'setPath', 'path',
                'setExtensions', 'selectedPathes', 'selectedItems',
                'openInExplorer', 'showContext', 'setBrowserContext', 'clicked',
                'doubleClicked', 'setExtraContext',
                'versionFormat', 'setVersionFormat', 'extensionVisibles',
                'setExtensionVisibles'
        ):
            setattr(self, cmd, getattr(self.__browser, cmd))
        # =====================================================================

        # ツールバー。=========================================================
        refresh_btn = QtWidgets.QPushButton()
        refresh_btn.setFlat(True)
        refresh_btn.setIcon(uilib.Icon('uiBtn_reload'))
        refresh_btn.setToolTip('Refresh Browser')
        refresh_btn.clicked.connect(self.refresh)

        open_exp_btn = QtWidgets.QPushButton()
        open_exp_btn.setFlat(True)
        open_exp_btn.setIcon(uilib.Icon('uiBtn_directory'))
        open_exp_btn.setToolTip('Open Directory in Explorer...')
        open_exp_btn.clicked.connect(self.openRootDir)

        tool_layout = QtWidgets.QHBoxLayout()
        tool_layout.setContentsMargins(0, 0, 0, 0)
        tool_layout.setSpacing(2)
        tool_layout.setDirection(QtWidgets.QBoxLayout.RightToLeft)

        icon_size = uilib.hires(20)
        max_size = uilib.hires(24)
        for btn in (refresh_btn, open_exp_btn):
            btn.setIconSize(QtCore.QSize(icon_size, icon_size))
            btn.setMaximumSize(QtCore.QSize(max_size, max_size))
            tool_layout.addWidget(btn)
        tool_layout.addStretch()
        # =====================================================================

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        layout.addLayout(tool_layout)
        layout.addWidget(self.__browser)

    def browser(self):
        r"""
            セットされているブラウザオブジェクトを返すメソッド。

            Returns:
                ModuleBrowser:
        """
        return self.__browser

    def openRootDir(self):
        r"""
            ルートパスをExplorerで開くメソッド。
        """
        fileUtil.openDir(self.path())

    def copyPath(self):
        r"""
            選択ファイルのパスのリストをクリップボードへコピーする
        """
        QtWidgets.QApplication.clipboard().setText(
            '\n'.join(self.selectedPathes())
        )

    def keyPressEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        key = event.key()
        mod = event.modifiers()
        if mod == QtCore.Qt.ControlModifier:
            if key == QtCore.Qt.Key_C:
                self.copyPath()
                return
        super(ModuleBrowserWidget, self).keyPressEvent(event)


class FileView(QtWidgets.QWidget):
    r"""
        ファイルの一覧および保存をするためのUIを提供するクラス。
    """
    exportButtonClicked = QtCore.Signal(str, str)

    def __init__(self):
        super(FileView, self).__init__()

        brs = ModuleBrowserWidget()
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
        selected = self.browser().selectedPathes()
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
