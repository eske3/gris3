#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Factory開始時の設定を決めるUIを提供するモジュール。
    
    Dates:
        date:2017/01/21 12:39[Eske](eske3g@gmail.com)
        update:2021/04/23 10:54 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
from gris3 import uilib, factory
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

class FileHistoryView(QtWidgets.QTreeView):
    r"""
        プロジェクトをセットした履歴を表示するビュー
    """
    itemSelected = QtCore.Signal(str)
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(FileHistoryView, self).__init__(parent)
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setRootIsDecorated(False)

        model = QtGui.QStandardItemModel(0, 4)
        for i, label in enumerate(
            ('Project', 'Asset', 'Asset Type', 'FilePath')
        ):
            model.setHeaderData(i, QtCore.Qt.Horizontal, label)
        self.setModel(model)
        for i, width in enumerate((120, 150, 60)):
            self.setColumnWidth(i, uilib.hires(width))

        sel_model = QtCore.QItemSelectionModel(model)
        sel_model.selectionChanged.connect(self.updateSelection)
        self.setSelectionModel(sel_model)

    def setPathList(self, pathlist):
        r"""
            パスのリストをセットしてビューを更新する。
            
            Args:
                pathlist (list):
        """
        pathlist.reverse()
        model = self.model()
        model.removeRows(0, model.rowCount())
        fd = factory.FactoryData()
        for row, path in enumerate(pathlist):
            if not os.path.isdir(path):
                continue
            fd.setRootPath(path)
            p_item = QtGui.QStandardItem(fd.project(False))
            a_item = QtGui.QStandardItem(fd.assetName(False))
            t_item = QtGui.QStandardItem(fd.assetType(False))
            f_item = QtGui.QStandardItem(path)

            for col, item in enumerate((p_item, a_item, t_item, f_item)):
                model.setItem(row, col, item)

    def updateSelection(self, selected, deselected):
        r"""
            選択が変更されるとitemSelectedシグナルを送出する。
            
            Args:
                selected (QItemSelection):
                deselected (QItemSelection):
        """
        path = [x.data() for x in selected.indexes() if x.column() == 3]
        super(FileHistoryView, self).selectionChanged(selected, deselected)
        if path:
            self.itemSelected.emit(path[0])

    def select(self, row):
        r"""
            任意の行のアイテムを選択する。
            
            Args:
                row (int):行番号
        """
        sel_model = self.selectionModel()
        model = self.model()
        if row >= model.rowCount():
            return
        index = model.indexFromItem(model.item(row, 0))
        sel_model.select(
            index,
            (
                QtCore.QItemSelectionModel.ClearAndSelect
                | QtCore.QItemSelectionModel.Rows
            )
        )

class ProjectSelector(uilib.BlackoutPopup):
    r"""
        プロジェクトパスを設定するUIを提供するクラス。
    """
    projectDecided = QtCore.Signal(str)
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):
        """
        super(ProjectSelector, self).__init__(parent)
        self.setCenterSize(0.95, 0.9, False)

        # ラベル及びクローズボタン。===========================================
        label = QtWidgets.QLabel('+ Project Selector')
        label.setStyleSheet('QLabel{font-size : %spx;}'%uilib.hires(20))
        label.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )
        
        self.__status_line = QtWidgets.QLabel()
        self.__status_line.setStyleSheet('QLabel{color:#e00000;}')

        close_btn = uilib.OButton()
        close_btn.setToolTip('Cancel')
        close_btn.setIcon(uilib.IconPath('uiBtn_x'))
        close_btn.setActiveBgColor(180, 42, 80)
        close_btn.clicked.connect(self.closeDialog)

        label_layout = QtWidgets.QHBoxLayout()
        label_layout.addWidget(label)
        label_layout.addSpacing(20)
        label_layout.addWidget(self.__status_line)
        label_layout.setAlignment(
            self.__status_line, QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom
        )
        label_layout.addWidget(close_btn)
        # =====================================================================
        
        self.__project_path = QtWidgets.QLineEdit()
        apply_btn = uilib.OButton()
        apply_btn.setIcon(uilib.IconPath('uiBtn_setProject'))
        apply_btn.setToolTip('Set project')
        apply_btn.setSize(64)
        apply_btn.clicked.connect(self.setProject)

        # 履歴ビューの構築。===================================================
        history_label = QtWidgets.QLabel('Histories')
        limit_label = QtWidgets.QLabel('Number of limit')
        self.__limit =  uilib.Spiner()
        self.__limit.setRange(1, 99)
        self.__view = FileHistoryView()
        self.__view.itemSelected.connect(self.__project_path.setText)
        self.__view.doubleClicked.connect(self.setProject)
        # =====================================================================
        
        layout = QtWidgets.QGridLayout(self.centerWidget())
        layout.addLayout(label_layout, 0, 0, 1, 4)
        layout.addWidget(QtWidgets.QLabel('Path'), 1, 0, 1, 1)
        layout.addWidget(self.__project_path, 1, 1, 1, 2)
        layout.addWidget(apply_btn, 1, 3, 2, 1)
        layout.addWidget(history_label, 2, 0, 1, 1)
        layout.addWidget(limit_label, 2, 1, 1, 1)
        layout.setAlignment(limit_label, QtCore.Qt.AlignRight)
        layout.addWidget(self.__limit, 2, 2, 1, 1)
        layout.addWidget(self.__view, 3, 0, 1, 4)
        layout.setColumnStretch(0, 0)
        layout.setColumnStretch(1, 2)
        layout.setColumnStretch(2, 1)

    def pref(self):
        r"""
            プロジェクト設定オブジェクトを返す。
            
            Returns:
                settings.ProjectHistory:
        """
        from .. import settings
        return settings.GlobalPref().subPref('projectHistory')

    def error(self, message=''):
        r"""
            ステータスラインにエラーメッセージを表示する。
            
            Args:
                message (str):
        """
        self.__status_line.setText(message)

    def setProject(self):
        r"""
            あたえられたパスをプロジェクトとしてセットする
        """
        project_path = self.__project_path.text()
        if not project_path:
            self.error('No directory is not specified.')
            return

        if not os.path.isdir(project_path):
            self.error('The specified path is not directory.')
            return
    
        limit = self.__limit.value()
        from gris3 import settings
        settings.addPathToHistory(project_path, limit)
        self.closeDialog()
        self.projectDecided.emit(project_path)

    def loadSettings(self):
        r"""
            設定ファイルをロードする。
        """
        self.error()
        pref = self.pref()
        self.__limit.setValue(pref.limit())
        self.__view.setPathList(pref.pathes())

    def showDialog(self, projectPath=''):
        r"""
            ダイアログを表示する。
            
            Args:
                projectPath (str):
        """
        self.loadSettings()
        self.__project_path.setText(projectPath)
        super(ProjectSelector, self).showDialog()
