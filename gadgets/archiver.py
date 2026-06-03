#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Factory用のコンテクストメニューを提供するクラス。

    Dates:
        date:2020/04/07 15:10 eske yoshinob[eske3g@gmail.com]
        update:2026/05/19 22:33 eske yoshinob[eske3g@gmail.com]

    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
import re

from ..uilib import factoryUI
from .. import uilib

QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


def coordinateArchives(files, extensions, extFormat):
    r"""
    ScriptManagerに表示するファイルのフィルタ用関数。

    Args:
        files (list):ファイル操作する対象のパスリスト
        extensions (list):フィルタをかける拡張子のリスト
        extFormat (str):バージョン表記となる箇所を特定する正規表現

    Returns:
        dict:
    """
    reobj = re.compile(extFormat % '|'.join(extensions))
    matched_files = {}
    files = [os.path.basename(x) for x in files]
    files.sort()
    for file in files:
        r = reobj.search(file)
        if not r:
            continue
        data = {
            'ver':r.group(3) if r.group(3) else 'cur',
            'sep':r.group(2), 'name':file, 'ext':r.group(3),
            'simpleName':reobj.sub(r'\1\2\3', file),
            'isLinker': False
        }
        if r.group(1) in matched_files:
            matched_files[r.group(1)].append(data)
        else:
            matched_files[r.group(1)] = [data]
    return matched_files


class ArchiveDataView(QtWidgets.QWidget):
    r"""
    アーカイブを行うためのUIを提供するクラス。
    """
    def __init__(self, parent=None):
        r"""
        Args:
            parent(QtWidgets.QWidget): 親ウィジェット
        """
        super(ArchiveDataView, self).__init__()
        label = QtWidgets.QLabel('Archive')
        arc_btn = uilib.OButton(uilib.IconPath('uiBtn_save'))
        arc_btn.setSize(64)
        arc_btn.setBgColor(166, 49, 32)
        self.buttonClicked = arc_btn.clicked

        self.__view = factoryUI.ModuleBrowserWidget()
        self.__view.setExtensions('zip')
        self.__view.setCoordinator(coordinateArchives)
        self.__view.setVersionFormat('^(.*?)(\.|)(v\d+|)\.(%s)$')

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(arc_btn, 1, 0, 1, 1, QtCore.Qt.AlignRight)
        layout.addWidget(
            label, 2, 0, 1, 1, QtCore.Qt.AlignTop|QtCore.Qt.AlignHCenter
        )
        layout.addWidget(self.__view, 0, 1, 4, 1)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(0, 1)
        layout.setRowStretch(3, 1)

    def view(self):
        r"""
        ファイル一覧表示用のウィジェットを返す

        Returns:
            factoryUI.ModuleBrowserWidget:
        """
        return self.__view


class ArchiveProgressWidget(QtWidgets.QWidget):
    r"""
    アーカイブ経過表示ウィジェット
    """
    def __init__(self, parent=None):
        r"""
        Args:
            parent(QtWidgets) : 親ウィジェット:
        """
        super(ArchiveProgressWidget, self).__init__(parent)
        self.__message = QtWidgets.QLabel('Processing...')
        self.__progress = QtWidgets.QProgressBar()
        cancel_btn = uilib.OButton(uilib.IconPath('uiBtn_x'))
        cancel_btn.setToolTip('Cancel archiving')
        cancel_btn.setBgColor(180, 32, 58)
        cancel_btn.setSize(32)

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(self.__progress, 0, 0, 1, 2)
        layout.addWidget(self.__message, 1, 0, 1, 1)
        layout.addWidget(cancel_btn, 1, 1, 1, 1)
        layout.setColumnStretch(0, 1)
        layout.setRowStretch(2, 1)

        self.buttonClicked = cancel_btn.clicked

    def setup(self, minValue, maxValue):
        r"""
        プログレスバーの最小・最大値を設定する

        Args:
            minValue(int): 最小値
            maxValue(int): 最大値
        """
        self.__progress.setRange(minValue, maxValue)
        self.__progress.setValue(minValue)

    def setMessage(self, message):
        r"""
        ステータス進行表示用メッセージを設定する

        Args:
            message(str):
        """
        self.__message.setText(message)

    def goNext(self, message=None):
        r"""
        プログレスバーを次のステップへ進める

        Args:
            message(str): プログレスバーに変更を加えるメッセージ
        """
        self.__progress.setValue(self.__progress.value()+1)
        if message:
            self.__progress.setFormat('%p% : '+message)


class RigDataArchiver(uilib.ClosableGroup):
    r"""
    リグデータをアーカイブするための機能を提供するGUIクラス。
    """
    def __init__(self, parent=None):
        r"""
        Args:
            parent(QtWidgets.QWidget): 親ウィジェット
        """
        super(RigDataArchiver, self).__init__('Archive Rig Project')
        self.setIcon(uilib.IconPath('uiBtn_save'))

        self.__stacked = QtWidgets.QStackedWidget()
        self.__dataview = ArchiveDataView()
        self.__dataview.buttonClicked.connect(self.archive)

        self.__progress = ArchiveProgressWidget()
        self.__progress.buttonClicked.connect(self.cancel)
        
        self.__stacked.addWidget(self.__dataview)
        self.__stacked.addWidget(self.__progress)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.__stacked)

        from .. import qtArchive
        self.__archiver = qtArchive.ArchiverThread(self)
        self.__archiver.StageChanged.connect(self.updateProgress)
        self.__archiver.MessageSent.connect(self.__progress.setMessage)
        self.__archiver.NumberOfStepsDecided.connect(self.setupProgress)
        self.__archiver.finished.connect(self.finished)
        self.__progress.setup(0, 0)

        self.setExpanding(False)

    def view(self):
        r"""
        ファイル一覧表示用のウィジェットを返す

        Returns:
            factoryUI.ModuleBrowserWidget:
        """
        return self.__dataview.view()

    def refreshView(self):
        r"""
        ファイルビューワの更新を行う
        """
        self.view().refresh()

    def setupProgress(self, numberOfSteps):
        r"""
        プログレスバーの初期状態を変更する

        Args:
            numberOfSteps(int): 総ステップ数
        """
        self.__progress.setup(0, numberOfSteps)

    def updateProgress(self, stage, message):
        r"""
        プログレスバーの状況を更新する

        Args:
            stage(int): ステップ数
            message(str): 表示するメッセージ
        """
        self.__progress.goNext(message)

    def finished(self):
        r"""
        アーカイブ終了時のUI更新処理
        """
        self.__stacked.setCurrentIndex(0)
        self.refreshView()

    def archive(self):
        r"""
        アーカイブを実行する
        """
        self.__archiver.setup()
        self.__archiver.start()
        self.__stacked.setCurrentIndex(1)

    def cancel(self):
        r"""
        アーカイブ処理を中断する。
        """
        self.__archiver.stop()
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.__archiver.wait()
        self.__stacked.setCurrentIndex(0)
        self.refreshView()
        QtWidgets.QApplication.restoreOverrideCursor()


class MainGUI(uilib.AbstractSeparatedWindow):
    def centralWidget(self):
        r"""
        Returns:
            RigDataArchiver:
        """
        return RigDataArchiver()


def showWindow(parent=None):
    r"""
    ウィンドウを作成するためのエントリ関数。

    Returns:
        MainGUI:
    """
    if parent is None:
        from ..uilib import mayaUIlib
        parent = mayaUIlib.MainWindow
    widget = MainGUI(parent)
    widget.resize(480, 320)
    widget.show()
    return widget