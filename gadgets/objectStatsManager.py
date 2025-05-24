#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2024/08/28 16:34 Eske Yoshinob[eske3g@gmail.com]
        update:2024/08/28 17:06 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from ..tools import objStatsManager
from ..uilib import mayaUIlib
from .. import uilib, node
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class TargetEditor(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(TargetEditor, self).__init__(parent)
        
        def __add_group_and_buttons(group_name, button_info):
            grp = QtWidgets.QGroupBox(group_name)
            layout = QtWidgets.QVBoxLayout(grp)
            for label, method in button_info:
                btn = QtWidgets.QPushButton(label)
                layout.addWidget(btn)
                setattr(self, method + 'ButtonClicked', btn.clicked)
            return grp
        
        layout = QtWidgets.QVBoxLayout(self)
        rel_btn = uilib.OButton(uilib.IconPath('uiBtn_reset'))
        self.reloadButtonClicked = rel_btn.clicked
        layout.addWidget(rel_btn)
        layout.setAlignment(rel_btn, QtCore.Qt.AlignLeft)
        
        grp = __add_group_and_buttons(
            'Selection', [('Select all targets', 'selectAll')]
        )
        layout.addWidget(grp)

        grp = __add_group_and_buttons(
            'Edit', [
                ('Remove Selected', 'remove'),
                ('Remove all current tag', 'removeAllTag')
            ]
        )
        layout.addWidget(grp)
        layout.addStretch()


class TargetViewer(QtWidgets.QGroupBox):
    guiUpdatingRequested = QtCore.Signal()

    def __init__(self, parent=None):
        super(TargetViewer, self).__init__('Edit targets', parent)
        self.__current_tag = None
        model = QtGui.QStandardItemModel(0, 1)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Target Object')
        sel_model = QtCore.QItemSelectionModel(model)

        self.__view = QtWidgets.QTreeView()
        self.__view.setModel(model)
        self.__view.setSelectionModel(sel_model)
        self.__view.setRootIsDecorated(False)
        self.__view.setEditTriggers(self.__view.NoEditTriggers)
        self.__view.setVerticalScrollMode(self.__view.ScrollPerPixel)
        self.__view.setHorizontalScrollMode(self.__view.ScrollPerPixel)
        self.__view.setIconSize(QtCore.QSize(32, 32))
        self.__view.setSelectionMode(self.__view.ExtendedSelection)
        
        editor = TargetEditor()
        # editor.reloadButtonClicked.connect(self.updateGui)
        editor.reloadButtonClicked.connect(self.guiUpdatingRequested.emit)
        editor.selectAllButtonClicked.connect(self.selectAllTargets)
        editor.removeButtonClicked.connect(self.removeSelectedItems)
        editor.removeAllTagButtonClicked.connect(self.removeCurrentTagAll)

        splitter = QtWidgets.QSplitter()
        splitter.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        splitter.addWidget(self.__view)
        splitter.addWidget(editor)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(splitter)
    
    def view(self):
        return self.__view

    def setCurrentTag(self, tag):
        self.__current_tag = tag

    def currentTag(self):
        return self.__current_tag

    def updateGui(self):
        view = self.view()
        model = view.model()
        model.removeRows(0, model.rowCount())
        stored_groups = objStatsManager.listStoredGroup()
        std_icon = uilib.Icon('unit')
        err_icon = uilib.Icon('error')
        for i, str_grp in enumerate(stored_groups):
            target, target_name = str_grp.target(withName=True)
            label = target_name
            item = QtGui.QStandardItem(label)
            item.setData(str_grp())
            item.setData(0, QtCore.Qt.UserRole + 2)
            model.setItem(i, 0, item)
            if not target:
                item.setForeground(QtGui.QColor(200, 24, 82))
                item.setText(label + '  (Not found)')
                item.setIcon(err_icon)
                continue
            item.setIcon(std_icon)
            for j, tag in enumerate(str_grp.listTags()):
                tag_item = QtGui.QStandardItem(tag)
                tag_item.setData(tag)
                tag_item.setData(1, QtCore.Qt.UserRole + 2)
                item.setChild(j, 0, tag_item)
        view.expandAll()

    def selectAllTargets(self):
        model = self.view().model()
        str_grp = []
        for row in range(model.rowCount()):
            item = model.item(row, 0)
            str_grp.append(item.data(QtCore.Qt.UserRole + 1))
        with node.DoCommand():
            objStatsManager.selectTargetByStoredGroup(str_grp)

    def removeSelectedItems(self):
        sel_model = self.view().selectionModel()
        grplist = []
        taglist = []
        for index in sel_model.selectedIndexes():
            data_type = index.data(QtCore.Qt.UserRole + 2)
            if data_type == 0:
                str_grp = index.data(QtCore.Qt.UserRole + 1)
                grplist.append(str_grp)
                continue
            grp = index.parent().data(QtCore.Qt.UserRole + 1)
            tag = index.data(QtCore.Qt.UserRole + 1)
            data = grp + '->' + tag
            taglist.append(data)
        
        with node.DoCommand():
            objStatsManager.removeStored(taglist, grplist)
        self.updateGui()
        self.guiUpdatingRequested.emit()

    def removeCurrentTagAll(self):
        tag = self.currentTag()
        with node.DoCommand():
            objStatsManager.removeTagAll(tag)
        self.updateGui()
        self.guiUpdatingRequested.emit()


class ObjectStatsManager(QtWidgets.QWidget):
    r"""
        モデルデータの作成、チェックを行う機能を提供するクラス
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ObjectStatsManager, self).__init__(parent)
        self.setWindowTitle('+Object Stats Manager')
        reg_btn = QtWidgets.QPushButton('Register Selected')
        reg_btn.clicked.connect(self.register)

        self.__taglist = QtWidgets.QComboBox()
        self.__taglist.setLineEdit(QtWidgets.QLineEdit())
        store_btn = QtWidgets.QPushButton('Store as selected tag')
        store_btn.clicked.connect(self.storeToSelectedTag)
        restore_btn = QtWidgets.QPushButton('Restore selected tag')
        restore_btn.clicked.connect(self.restore)
        
        op_grp = QtWidgets.QGroupBox('Operation')
        layout = QtWidgets.QGridLayout(op_grp)
        layout.addWidget(self.__taglist, 0, 0, 1, 1)
        layout.addWidget(restore_btn, 0, 1, 1, 1)
        layout.addWidget(store_btn, 1, 1, 1, 1)

        self.__target_view = TargetViewer()
        self.__taglist.currentTextChanged.connect(
            self.__target_view.setCurrentTag
        )
        self.__target_view.guiUpdatingRequested.connect(self.updateGui)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(reg_btn)
        layout.addWidget(op_grp)
        layout.addWidget(self.__target_view)

    def updateGui(self):
        self.__taglist.clear()
        self.__taglist.addItems(objStatsManager.listTags())
        self.__target_view.updateGui()

    def currentTag(self):
        return self.__taglist.currentText()
    
    def register(self):
        with node.DoCommand():
            objStatsManager.store()
        self.updateGui()

    def storeToSelectedTag(self):
        tag = self.currentTag()
        with node.DoCommand():
            objStatsManager.storeToRegistered(tag)
        self.updateGui()
    
    def restore(self):
        tag = self.currentTag()
        with node.DoCommand():
            objStatsManager.restore(tag)


class MainGUI(uilib.AbstractSeparatedWindow):
    r"""
        メインとなるGUIを提供するクラス
    """
    def centralWidget(self):
        r"""
            中心となるメインウィジェットを作成して返す
            
            Returns:
                ModelSetupWidget:
        """
        return ObjectStatsManager()


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。
        
        Returns:
            QtWidgets.QWidget:
    """
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(uilib.hires(380), uilib.hires(400))
    widget.main().updateGui()
    widget.show()
    return widget
