#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    コントローラに関する編集や書き出しなどを行う機能を提供するモジュール。
    
    Dates:
        date:2017/01/22 0:03[Eske](eske3g@gmail.com)
        update:2025/05/25 09:40 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from ... import factoryModules, exporter, uilib
from ...gadgets import ctrlShapeEditor
from ...exporter import curveExporter
from ...uilib import factoryUI
QtWidgets, QtGui, QtCore = (
    factoryModules.QtWidgets, factoryModules.QtGui, factoryModules.QtCore
)


class ContextOption(factoryUI.ContextOption):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ContextOption, self).__init__(parent)
        
        model = QtGui.QStandardItemModel(0, 1)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Shape Name')
        sel_model = QtCore.QItemSelectionModel(model)
        sel_model.selectionChanged.connect(self.selectNodesFromView)
        self.__view = QtWidgets.QTreeView()
        self.__view.setAlternatingRowColors(True)
        self.__view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.__view.setRootIsDecorated(False)
        self.__view.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )
        self.__view.setModel(model)
        self.__view.setSelectionModel(sel_model)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.__view)

    def refresh(self):
        import re
        import os
        model = self.__view.model()
        model.removeRows(0, model.rowCount())
        files = self.fileNames()
        file = os.path.join(self.path(), files[0])
        if not os.path.exists(file):
            return

        shapelist = curveExporter.listCtrls(file)
        for row, shape in enumerate(shapelist):
            item = QtGui.QStandardItem(shape)
            item.setData(shape )
            model.setItem(row, 0, item)

    def selectNodesFromView(self, selected, deselected):
        r"""
            Args:
                selected (QtCore.QItemSelection):
                deselected (QtCore.QItemSelection):
        """
        from ...tools import selectionUtil
        sel_model = self.__view.selectionModel()
        selection_list = []
        for index in sel_model.selectedIndexes():
            selection_list.append(index.data())
        if not selection_list:
            return
        selectionUtil.selectNodes(selection_list)

    def isScalable(self):
        r"""
            スケール可能かどうかを返すオーバーライド用メソッド。
            
            Returns:
                bool:
        """
        return True

    def contextSize(self):
        r"""
            コンテキストのサイズを返すオーバーライド用メソッド
            
            Returns:
                tuple:
        """
        return (640, 480)


class ControllerManager(factoryModules.AbstractDepartmentGUI):
    r"""
        ベースジョイントの編集・保存などのUIを提供するクラス。
    """
    def init(self):
        # カーブのエクスポーターGUIの作成。====================================
        self.__view = factoryUI.FileView()
        self.__view.setRootPath(self.workspaceDir())
        self.__view.setBrowserContext(factoryUI.MayaAsciiBrowserContext)
        self.__view.browser().setExtraContext(ContextOption)
        self.__view.exportButtonClicked.connect(self.export)
        # =====================================================================

        # タブを作成。=========================================================
        tab = factoryUI.ToolTabWidget()
        btn = tab.addTab(
            ctrlShapeEditor.ControllerShapeEditor(),
            uilib.IconPath('uiBtn_toolBox'), 'Edit Curves'
        )
        btn.setBgColor(*tab.ToolColor)

        btn = tab.addTab(
            self.__view, uilib.IconPath('folder.png'),
            'Export Curves as Controller'
        )
        btn.setBgColor(*tab.SaveColor)
        # =====================================================================

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(tab)

    def export(self, rootpath, filename):
        r"""
            カーブを書き出す
            
            Args:
                rootpath (str):書き出し先のディレクトリパス
                filename (str):書き出し先のファイル名
        """
        exporter.exportSelectedCurves(
            rootpath, filename, self.__view.isOverwrite()
        )


class Department(factoryModules.AbstractDepartment):
    r"""
        ベースジョイントにまつわる機能を管理するためのクラス。
    """
    def init(self):
        self.setDirectoryName('controlCurves')

    def label(self):
        r"""
            Factoryのタブに表示するラベルを返す。

            Returns:
                str:
        """
        return 'Ctrl Exporter'

    def priority(self):
        r"""
            表示優先順位を返す。

            Returns:
                int:
        """
        return 0

    def GUI(self):
        r"""
            Factoryのタブに表示するUIを定義するクラスを返す。
            
            Returns:
                ControllerManager:
        """
        return ControllerManager
