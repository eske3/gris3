#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ファイル情報を表示、編集する機能を提供するモジュール。

    Dates:
        date:2017/07/08 23:48[Eske](eske3g@gmail.com)
        update:2026/05/16 19:12 eske yoshinob[eske3g@gmail.com]

    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import time
from .. import uilib, fileInfoManager
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class DiscardedFileManager(QtWidgets.QWidget):
    r"""
        廃棄されたファイルを復帰するための管理ウィジェット。
    """
    fileRestored = QtCore.Signal()

    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(DiscardedFileManager, self).__init__(parent)
        self.setWindowTitle('Discarded File Manager')

        icon_size = 32

        # 廃棄ファイルの一覧UI。===============================================
        self.__view = QtWidgets.QTreeView()
        self.__view.setAlternatingRowColors(True)
        self.__view.setRootIsDecorated(False)
        self.__view.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )
        
        model = QtGui.QStandardItemModel(0, 2)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'File Name')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Discarded Date')
        self.__view.setModel(model)
        self.__view.setColumnWidth(0, 360)
        # =====================================================================
        
        # 廃棄ファイルの復帰ボタン。===========================================
        restore_btn = uilib.OButton()
        restore_btn.setIcon(uilib.IconPath('uiBtn_export'))
        restore_btn.setToolTip('Restore selected files.')
        restore_btn.setSize(icon_size)
        restore_btn.setBgColor(32, 145, 178)
        restore_btn.clicked.connect(self.restoreSelectedFiles)
        
        restore_label = QtWidgets.QLabel('Restore selected')
        # =====================================================================

        # 削除ボタン。
        del_btn = uilib.OButton()
        del_btn.setIcon(uilib.IconPath('uiBtn_trush'))
        del_btn.setToolTip('Delete selected files.')
        del_btn.setSize(icon_size)
        del_btn.clicked.connect(self.deleteSelectedFiles)

        toolbar = QtWidgets.QGroupBox('Operations')
        layout = QtWidgets.QFormLayout(toolbar)
        layout.addRow('Restore selected', restore_btn)
        layout.addRow('Delete selected', del_btn)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.__view)
        layout.addWidget(toolbar)

        self.__manager = fileInfoManager.FileDiscarder()
        self.__cached_datalist = []
        self.__workdir = ''

    def manager(self):
        r"""
            ファイル管理を行うマネージャーオブジェクトを返す。

            Returns:
                fileInfoManager.FileDiscarder:
        """
        return self.__manager

    def setWorkdir(self, workdir):
        r"""
            作業ディレクトリパスを設定する。

            Args:
                workdir (str):
        """
        model = self.__view.model()
        model.removeRows(0, model.rowCount())

        manager = self.manager()
        manager.setWorkdir(workdir)
        datalist = manager.listMovedFiles()
        row = 0
        for file, data in datalist.items():
            f_item = QtGui.QStandardItem(data['filename'])
            f_item.setData(file)
            
            moved_time = time.strftime(
                '%Y/%m/%d %H:%M:%S', time.localtime(data['movedTime'])
            )
            t_item = QtGui.QStandardItem(moved_time)
            t_item.setData(data['movedTime'])
            
            model.setItem(row, 0, f_item)
            model.setItem(row, 1, t_item)
            row += 1
        self.__cached_datalist = datalist
        self.__workdir = workdir

    def workdir(self):
        r"""
            作業ディレクトリパスを返す。

            Returns:
                str:
        """
        return self.__workdir

    def listSelectedFiles(self):
        r"""
            選択されたファイル名のリストを返す。

            Returns:
                list:
        """
        filename_list = []
        for index in [
            x for x in self.__view.selectedIndexes() if x.column() == 0
        ]:
            filename_list.append(index.data(QtCore.Qt.UserRole+1))
        return filename_list

    def restoreSelectedFiles(self):
        r"""
            選択されたファイルをリストアし通常ファイルに戻す。
        """
        filename_list = self.listSelectedFiles()
        manager = self.manager()
        for key in [x for x in filename_list if x in self.__cached_datalist]:
            try:
                manager.restore(key, self.__cached_datalist[key])
            except fileInfoManager.FileExistingError as e:
                print(e)
        manager.cleanup()
        self.setWorkdir(self.workdir())
        self.fileRestored.emit()

    def deleteSelectedFiles(self):
        filename_list = self.listSelectedFiles()
        manager = self.manager()
        manager.removeFiles(filename_list)
        self.setWorkdir(self.workdir())
        self.fileRestored.emit()


class MainGUI(uilib.AbstractSeparatedWindow):
    def centralWidget(self):
        r"""
            Returns:
                DiscardedFileManager:
        """
        return DiscardedFileManager()


def showWindow(parent=None):
    r"""
        GUI表示用のエントリ関数。

        Args:
            parent(QtWidgets.QWidget): 親ウィジェット
        Returns:
            MainGUI:
    """
    if parent is None:
        from ..uilib import mayaUIlib
        parent = mayaUIlib.MainWindow
    w = MainGUI(parent)
    w.resize(520, 400)
    w.show()
    return w
