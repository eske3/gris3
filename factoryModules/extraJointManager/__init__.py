#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    サブ骨を作成、編集、書き出しをするための機能を提供するクラス。
    
    Dates:
        date:2017/01/22 0:04[Eske](eske3g@gmail.com)
        update:2025/05/25 09:46 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
from ... import factoryModules, uilib, core, lib, system
from ...tools import extraJoint
from ...gadgets import extraJointEditor
from ...exporter import extraJointExporter
from ...uilib import factoryUI
QtWidgets, QtGui, QtCore = (
    factoryModules.QtWidgets, factoryModules.QtGui, factoryModules.QtCore
)

class ContextOption(factoryUI.ContextOption):
    Keys = ['basename', 'nodeTypeLabel', 'side', 'nodeType', 'parent']
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ContextOption, self).__init__(parent)
        
        model = QtGui.QStandardItemModel(0, len(self.Keys))
        for i, l in enumerate(self.Keys):
            model.setHeaderData(i, QtCore.Qt.Horizontal, lib.title(l))
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
        model = self.__view.model()
        model.removeRows(0, model.rowCount())
        files = self.fileNames()
        file = os.path.join(self.path(), files[0])
        if not os.path.exists(file):
            return
        datalist = extraJointExporter.loadExtraJointData(file)
        for row, data in enumerate(datalist):
            for col, key in enumerate(self.Keys):
                d = data[key]
                item = QtGui.QStandardItem(str(d))
                item.setData(d)
                model.setItem(row, col, item)

    def selectNodesFromView(self, selected, deselected):
        r"""
            Args:
                selected (QtCore.QItemSelection):
                deselected (QtCore.QItemSelection):
        """
        from ...tools import selectionUtil
        sel_model = self.__view.selectionModel()
        selection_list = {}
        for index in sel_model.selectedIndexes():
            col = index.column()
            if col > 3:
                continue
            d = selection_list.setdefault(index.row(), {})
            d[self.Keys[col]] = index.data(QtCore.Qt.UserRole+1)
        if not selection_list:
            return

        name = system.GlobalSys().nameRule()()
        selection_nodes = []
        for data in selection_list.values():
            name.setName(data[self.Keys[0]])
            name.setNodeType(data[self.Keys[1]])
            name.setPosition(int(data[self.Keys[2]]))
            selection_nodes.append(name())
        selectionUtil.selectNodes(selection_nodes)

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
        

class ExtraJointExporter(QtWidgets.QWidget):
    r"""
        DrivenKeyを書き出すための補助ツールとエクスポーターを提供するクラス。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ExtraJointExporter, self).__init__(parent)
        
        sel_btn = QtWidgets.QPushButton('Select Extra Joints')
        sel_btn.clicked.connect(self.selectExtraJoint)

        view = factoryUI.FileView()
        view.browser().setExtraContext(ContextOption)
        view.setExtensions(['json'])
        view.exportButtonClicked.connect(self.export)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addWidget(sel_btn)
        layout.addWidget(view)

        self.__view = view

    def setRootPath(self, path):
        r"""
            エクスポーターで表示するディレクトリを指定するメソッド。
            
            Args:
                path (str):ディレクトリパス
        """
        self.__view.setRootPath(path)

    def selectExtraJoint(self):
        r"""
            選択ノード下のExtraジョイントが入っているノードを選択する。
        """
        with core.Do:
            extraJoint.selectExtraJoint(core.selected())

    def export(self, rootpath, filename):
        r"""
            選択ノードについているDrivenキーをエクスポートする。
            
            Args:
                rootpath (str):書き出し先のディレクトリパス
                filename (str):ファイル名
        """
        from gris3 import exporter
        exporter.exportExtraJointScripts(
            rootpath, filename, self.__view.isOverwrite()
        )


class ExtraJointManager(factoryModules.AbstractDepartmentGUI):
    r"""
        ベースジョイントの編集・保存などのUIを提供するクラス。
    """
    def init(self):
        tab = factoryUI.ToolTabWidget()
        self.editor = extraJointEditor.ExtraJointEditor()
        self.editor.setPositionList()
        btn = tab.addTab(
            self.editor, uilib.IconPath('uiBtn_toolBox.png'),
            'Extra Joint Creator'
        )
        btn.setBgColor(*tab.ToolColor)

        view = ExtraJointExporter()
        view.setRootPath(self.workspaceDir())
        btn = tab.addTab(
            view, uilib.IconPath('folder.png'), 'Export Extra Joints'
        )
        btn.setBgColor(*tab.SaveColor)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(tab)

    def refreshState(self):
        self.editor.updateTagList()


class Department(factoryModules.AbstractDepartment):
    def init(self):
        self.setDirectoryName('extraJointScripts')

    def label(self):
        r"""
            表示するラベルを返す。
            
            Returns:
                str:
        """
        return 'Extra Joints'

    def priority(self):
        r"""
            表示順序のプライオリティを返す
            
            Returns:
                int:
        """
        return 7

    def GUI(self):
        r"""
            GUIを返す。
            
            Returns:
                ExtraJointManager:
        """
        return ExtraJointManager
