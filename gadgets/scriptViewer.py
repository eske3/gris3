#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2024/04/29 13:57 Eske Yoshinob[eske3g@gmail.com]
        update:2024/04/30 13:36 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
from ..tools import scriptManager
from .. import lib, uilib, node, verutil
from ..uilib import mayaUIlib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class FunctionList(QtWidgets.QWidget):
    selectionChanged = QtCore.Signal(verutil.BaseString)

    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget): 親ウィジェット
        """
        super(FunctionList, self).__init__(parent)
        view = QtWidgets.QListView()
        model = QtGui.QStandardItemModel(0, 1)
        sel_model = QtCore.QItemSelectionModel(model)
        sel_model.selectionChanged.connect(self.__emit_selected_items)
        view.setModel(model)
        view.setSelectionModel(sel_model)

        l = QtWidgets.QLabel('Functions')
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(l)
        layout.addWidget(view)
        
        self.__view = view

    def view(self):
        return self.__view

    def addItems(self, itemlist):
        model = self.view().model()
        model.removeRows(0, model.rowCount())
        for row, data in enumerate(itemlist):
            item = QtGui.QStandardItem(data)
            item.setData(item)
            model.setItem(row, 0, item)

    def selectedItem(self):
        sel_model = self.view().selectionModel()
        items = []
        for index in sel_model.selectedIndexes():
            items.append(index.data())
        return items[0] if items else ''

    def __emit_selected_items(self, selected, deselected):
        self.selectionChanged.emit(self.selectedItem())



class ArgEditorStyle(QtWidgets.QStyledItemDelegate):
    def paint(self, painter, option, index):
        super(ArgEditorStyle, self).paint(painter, option, index)
        if index.column() == 0:
            return

        text = index.data(QtCore.Qt.DisplayRole)
        data = index.data(QtCore.Qt.UserRole + 1)
        if text or not data:
            return
        pen = QtGui.QPen(QtGui.QColor(130, 130, 130), 1)
        painter.setPen(pen)
        painter.drawText(
            option.rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
            '{} - Default Value'.format(data)
        )


class ArgList(QtWidgets.QWidget):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget): 親ウィジェット
        """
        super(ArgList, self).__init__(parent)
        view = QtWidgets.QTreeView()
        view.setRootIsDecorated(False)
        view.setEditTriggers(view.AllEditTriggers)
        view.setItemDelegate(ArgEditorStyle())
        
        model = QtGui.QStandardItemModel(0, 2)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Arg Name')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Value')
        
        view.setModel(model)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(view)
        self.__view = view

    def view(self):
        return self.__view

    def setArgList(self, arglist):
        model = self.view().model()
        model.removeRows(0, model.rowCount())
        row = 0
        for argname, default in arglist.items():
            name_item = QtGui.QStandardItem(argname)
            name_item.setData(argname)
            name_item.setEditable(False)
            model.setItem(row, 0, name_item)
            
            def_item = QtGui.QStandardItem()
            def_item.setData(default)
            model.setItem(row, 1, def_item)
            row += 1

    def castDefaultValue(self, value):
        if value == "''":
            return ''
        return value

    def listArgs(self):
        model = self.view().model()
        from collections import OrderedDict
        results = OrderedDict()
        for row in range(model.rowCount()):
            item = model.item(row, 0)
            arg = item.text()
            item = model.item(row, 1)
            value = item.text()
            if not value:
                value = self.castDefaultValue(item.data())
            results[arg] = value
        return results
            


class ScriptViewer(QtWidgets.QWidget):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ScriptViewer, self).__init__(parent)
        self.setWindowTitle('ScriptViewer')
        
        self.__manager = scriptManager.ScriptManager()

        file_l = QtWidgets.QLabel('File  ')
        self.__file = QtWidgets.QLineEdit()
        self.__file.returnPressed.connect(self.updateGui)
        
        f_widget = QtWidgets.QWidget()
        f_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        layout =  QtWidgets.QHBoxLayout(f_widget)
        layout.addWidget(file_l)
        layout.addWidget(self.__file)
        layout.setStretchFactor(self.__file, 1)
        
        self.__f_list = FunctionList()
        self.__f_list.selectionChanged.connect(self.updateArgList)
        self.__args = ArgList()
        splitter = QtWidgets.QSplitter()
        splitter.addWidget(self.__f_list)
        splitter.addWidget(self.__args)
        splitter.setStretchFactor(1, 1)
        
        exec_btn = uilib.OButton(uilib.IconPath('uiBtn_play'))
        exec_btn.setToolTip('Execute this python script')
        exec_btn.setSize(32)
        exec_btn.clicked.connect(self.executeScript)

        play_btn = uilib.OButton(uilib.IconPath('uiBtn_play'))
        play_btn.setToolTip('Execute selected function')
        play_btn.setSize(32)
        play_btn.clicked.connect(self.execute)

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(f_widget, 0, 0, 1, 1)
        layout.addWidget(exec_btn, 0, 1, 1, 1, QtCore.Qt.AlignBottom)
        layout.addWidget(splitter, 1, 0, 1, 1)
        layout.addWidget(play_btn, 1, 1, 1, 1, QtCore.Qt.AlignBottom)

    def functionList(self):
        return self.__f_list

    def argList(self):
        return self.__args

    def manager(self):
        return self.__manager

    def updateGui(self):
        python_path = self.getTargetModulePath()
        m = self.manager()
        m.setTargetModule(python_path)
        m.analyzeModule()
        m.load()
        functions = m.listFunctions()
        f_list = self.functionList()
        f_list.addItems(functions)

    def updateArgList(self, functionName):
        m = self.manager()
        function = m.getFunction(functionName)
        arglist = scriptManager.listArgs(function)
        self.argList().setArgList(arglist)

    def setTargetModule(self, pythonPath):
        r"""
            Pythonモジュールを設定する

            Args:
                pythonPath (str):
        """
        self.__file.setText(pythonPath)
        self.updateGui()

    def getTargetModulePath(self):
        r"""
            設定されたPythonモジュールパスを返す。
            設定されているパスが存在しない場合は空文字列を返す。

            Returns:
                str:
        """
        filepath = self.__file.text()
        filepath =  filepath if os.path.exists(filepath) else ''
        return filepath

    def execute(self):
        m = self.manager()
        funcname = self.functionList().selectedItem()
        f = m.getFunction(funcname)
        args = self.argList().listArgs()
        f(**args)

    def executeScript(self):
        python_path = self.getTargetModulePath()
        verutil.execfile(python_path)
        

class MainGUI(uilib.AbstractSeparatedWindow):
    r"""
        独立ウィンドウ式のScriptViewerを提供する。
    """
    def centralWidget(self):
        r"""
            Returns:
                AnimSupporter:
        """
        return ScriptViewer()


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。
        
        Returns:
            QtWidgets.QWidget:
    """
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(600*uilib.hires, 330*uilib.hires)
    widget.show()
    return widget

