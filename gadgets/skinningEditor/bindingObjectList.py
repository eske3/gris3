#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    スキニングに関する便利機能を提供するガジェット
    
    Dates:
        date:2017/06/15 16:35[Eske](eske3g@gmail.com)
        update:2020/07/29 13:04 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from ...tools import skinUtility
from ... import uilib, node
from ...uilib import extendedUI
from . import bindUtilityWidget, valueEditor
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class BindingListView(QtWidgets.QTreeView):
    def __init__(self, parent=None):
        super(BindingListView, self).__init__(parent)
        self.setIconSize(QtCore.QSize(32, 32))
        self.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
        self.setVerticalScrollMode(QtWidgets.QTreeView.ScrollPerPixel)
        self.setHorizontalScrollMode(QtWidgets.QTreeView.ScrollPerPixel)
        self.setSelectionMode(QtWidgets.QTreeView.ExtendedSelection)

    def drawBranches(self, painter, option, index):
        if index.parent().row() == -1:
            super(BindingListView, self).drawBranches(painter, option, index)


class BindingLister(extendedUI.FilteredView):
    def __init__(self, parent=None):
        super(BindingLister, self).__init__(parent)
        self.view().selectionModel().selectionChanged.connect(
            self.selectNode
        )
        self.view().setColumnWidth(0, 300)

    def createView(self):
        view = BindingListView()
        return view

    def createModel(self):
        model = QtGui.QStandardItemModel(0, 2)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Node Name')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Skin Cluster')
        return model

    def updateList(self, targetJoints=None):
        proxy = self.view().model()
        model = proxy.sourceModel()
        model.removeRows(0, model.rowCount())

        joints = node.selected(targetJoints, type='joint')
        jnt_icon = QtGui.QIcon(uilib.IconPath('uiBtn_skeleton'))
        row = 0
        for jnt in joints:
            skins = skinUtility.listSkinFromInfluence(jnt)
            if not skins:
                continue
            jnt_item = QtGui.QStandardItem(jnt())
            jnt_item.setIcon(jnt_icon)
            model.setItem(row, 0, jnt_item)
            c_row = 0
            for sc, geo in skins:
                geo_item = QtGui.QStandardItem(geo())
                sc_item = QtGui.QStandardItem(sc)
                jnt_item.setChild(c_row, 0, geo_item)
                jnt_item.setChild(c_row, 1, sc_item)
                c_row += 1
            row += 1
        if row == 1:
            self.view().expandAll()

    def selectNode(self, selected, deselected):
        sel_model = self.view().selectionModel()
        selections = []
        for index in sel_model.selectedIndexes():
            if index.column() != 0:
                continue
            selections.append(index.data())
        node.cmds.select(selections, ne=True)


class BindingObjectList(QtWidgets.QWidget):
    r"""
        インフルエンスがバインドしているジオメトリの一覧を表示するウィジェット。
    """
    def __init__(self, parent=None):
        super(BindingObjectList, self).__init__(parent)
        self.setWindowTitle('Binding Object List')
        
        rel_btn = uilib.OButton(uilib.IconPath('uiBtn_reset'))
        rel_btn.clicked.connect(self.updateList)
        self.__view = BindingLister()
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(rel_btn)
        layout.addWidget(self.__view)

    def view(self):
        return self.__view

    def updateList(self, targetJoints=None):
        self.view().updateList(targetJoints)


class MainGUI(uilib.AbstractSeparatedWindow):
    r"""
        独立ウィンドウ式のSkinningEditorを提供する。
    """
    def centralWidget(self):
        r"""
            Returns:
                SkinningEditor:
        """
        return BindingObjectList()


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。
        
        Returns:
            QtWidgets.QWidget:
    """
    from ...uilib import mayaUIlib
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(500, 600)
    widget.show()
    widget.main().updateList()
    return widget
