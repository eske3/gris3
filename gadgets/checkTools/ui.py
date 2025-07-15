#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2024/05/09 18:03 Eske Yoshinob[eske3g@gmail.com]
        update:2024/05/22 13:40 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from . import core, util
from ... import uilib
from ...tools import checkUtil
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class ResultLister(QtWidgets.QTreeView):
    ErrorColor = QtGui.QColor(198, 25, 28)
    WarningColor = QtGui.QColor(240, 140, 20)
    nodeWasSelected = QtCore.Signal(list)
    checkedResultSelected = QtCore.Signal(list)

    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ResultLister, self).__init__(parent)
        self.setHeaderHidden(True)
        self.setRootIsDecorated(False)
        self.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
        self.setVerticalScrollMode(QtWidgets.QTreeView.ScrollPerPixel)
        self.setHorizontalScrollMode(QtWidgets.QTreeView.ScrollPerPixel)
        self.clicked.connect(self.emit_selection_changed)
        self.setExpandsOnDoubleClick(False)
        model = QtGui.QStandardItemModel(0, 1)
        sel_model = QtCore.QItemSelectionModel(model)
        self.setModel(model)
        self.setSelectionModel(sel_model)

    def clearResults(self):
        model = self.model()
        model.removeRows(0, model.rowCount())

    def addResult(self, nodeName, nodePath, checkedResults):
        r"""
            Args:
                nodeName (str):
                nodePath (str):
                checkedResults (list):gris3.checkUtil.CheckedResultのリスト
        """
        model = self.model()
        node_item = QtGui.QStandardItem(nodeName)
        node_item.setData(nodePath)
        node_item.setData('nodeName', QtCore.Qt.UserRole+2)
        model.setItem(model.rowCount(), 0, node_item)
        for row, r in enumerate(checkedResults):
            item = QtGui.QStandardItem(r.message)
            item.setData(r.processId)
            item.setData('checkedResult', QtCore.Qt.UserRole+2)
            node_item.setChild(row, 0, item)
            if r.status == checkUtil.CheckedResult.Error:
                item.setForeground(QtGui.QColor(240, 240, 240))
                item.setBackground(self.ErrorColor)
            elif r.status == checkUtil.CheckedResult.Warning:
                item.setForeground(self.WarningColor)

    def emit_selection_changed(self, index):
        r"""
            Args:
                index (QtCore.QModelIndex): クリック位置のMIndex
        """
        if not index.isValid():
            return
        data_type = index.data(QtCore.Qt.UserRole+2)
        if data_type == 'checkedResult':
            p_index = index.parent()
            self.checkedResultSelected.emit(
                [
                    p_index.data(QtCore.Qt.UserRole+1),
                    index.data(QtCore.Qt.UserRole+1)
                ]
            )
            return
        self.nodeWasSelected.emit(
            [index.data(QtCore.Qt.UserRole+1), index.data()]
        )
        self.checkedResultSelected.emit(['', -1])


class OperatorPage(QtWidgets.QScrollArea):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(OperatorPage, self).__init__(parent)
        self.__is_built = False
        self.__process_id = -1
        self.setWidgetResizable(True)
        parent = QtWidgets.QWidget()
        parent.setObjectName('__gris_check_tool_option_widget__')
        parent.setStyleSheet(
            (
                'QWidget#__gris_check_tool_option_widget__'
                '{background: transparent;}'
            )
        )
        self.setWidget(parent)

    def setProcessId(self, index):
        self.__process_id = int(index)

    def processId(self):
        return self.__process_id

    def buildUI(self, parent):
        pass

    def updateUI(self, info):
        pass

    def createUI(self):
        if self.__is_built:
            return
        self.__is_built = True
        self.buildUI(self.widget())


class Operator(QtWidgets.QStackedWidget):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(Operator, self).__init__(parent)
        no_op = QtWidgets.QLabel('No operation')
        no_op.setAlignment(QtCore.Qt.AlignCenter)
        self.addWidget(no_op)

    def listProcessIds(self):
        results = {}
        for i in range(1, self.count()):
            op = self.widget(i)
            results[op.processId()] = op
        return results

    def addWidget(self, operatorPage):
        if hasattr(operatorPage, 'processId'):
            pid = operatorPage.processId()
            if pid in self.listProcessIds():
                raise AttributeError(
                    (
                        'A process id "{}" of the given operator page is '
                        'unavailable.'
                    ).format(pid)
                )
        super(Operator, self).addWidget(operatorPage)

    def setIndexByProcessId(self, processId, targetInfo):
        for i in range(1, self.count()):
            op = self.widget(i)
            if op.processId() == processId:
                op.createUI()
                op.updateUI(targetInfo)
                self.setCurrentIndex(i)
                return
        self.setCurrentIndex(0)


class NodeResultViewer(QtWidgets.QSplitter):
    r"""
        ノードベースのチェックを行うチェッカーの結果表示用GUIを提供するクラス。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(NodeResultViewer, self).__init__(parent)
        self.__lister = ResultLister()
        self.__lister.nodeWasSelected.connect(self.selectNode)
        self.__lister.checkedResultSelected.connect(self.showOperator)
        self.__operator = Operator()
        self.addWidget(self.__lister)
        self.addWidget(self.__operator)
        self.setStretchFactor(0, 1)
        self.setSizes([300, 300])
        self.setOperatorHidden(True)

    def lister(self):
        return self.__lister
    
    def operator(self):
        return self.__operator

    def setOperatorHidden(self, state):
        self.operator().setHidden(bool(state))

    def addOperatorPage(self, operatorPage, processId):
        self.setOperatorHidden(False)
        operatorPage.setProcessId(processId)
        self.operator().addWidget(operatorPage)

    def setResults(self, checkedResults):
        r"""
            Args:
                checkedResults (gris3.checkUtil.CheckedResult):
        """
        lister = self.lister()
        lister.clearResults()
        for r in checkedResults:
            if hasattr(r[0], 'shortName'):
                lister.addResult(r[0].shortName(), r[0], r[1])
            else:
                lister.addResult(r[0], r[0], r[1])
        lister.expandAll()

    def selectNode(self, selectedNodeInfo):
        r"""
            Args:
                selectedNodeInfo (list):
        """
        cmds = checkUtil.node.cmds
        if not cmds.objExists(selectedNodeInfo[0]):
            return
        cmds.select(selectedNodeInfo[0], r=True, ne=True)

    def showOperator(self, selectedInfo):
        self.operator().setIndexByProcessId(selectedInfo[1], [selectedInfo[0]])



class CategoryList(QtWidgets.QWidget):
    selectionChanged = QtCore.Signal(int)
    IconSize = QtCore.QSize(32, 32)

    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(CategoryList, self).__init__(parent)
        self.__emit_selection_signal = True
        title = QtWidgets.QLabel('Check Category')
        title.setStyleSheet('font-size: 14pt;')
        item = QtGui.QStandardItem()
        self.__default_bg = item.background()

        self.__view = QtWidgets.QTreeView()
        self.__view.setHeaderHidden(True)
        self.__view.setRootIsDecorated(False)
        model = QtGui.QStandardItemModel(0, 2)
        sel_model = QtCore.QItemSelectionModel(model)
        sel_model.selectionChanged.connect(self.emit_selected_index)
        self.__view.setModel(model)
        self.__view.setSelectionModel(sel_model)
        self.__view.setColumnWidth(0, self.IconSize.width())
        self.__view.setIconSize(self.IconSize)
        
        check_all_btn = uilib.SqButton(uilib.IconPath('uiBtn_play'))
        check_all_btn.setToolTip('Do checking all.')
        self.checkAllButtonClicked = check_all_btn.clicked
        
        all_label = QtWidgets.QLabel('Do checking all')

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(title, 0, 0, 1, 2)
        layout.addWidget(check_all_btn, 1, 0, 1, 1)
        layout.addWidget(all_label, 1, 1, 1, 1, QtCore.Qt.AlignLeft)
        layout.addWidget(self.__view, 2, 0, 1, 2)

    def view(self):
        return self.__view
    
    def updateIcon(self, id, result):
        r"""
            Args:
                id (int):
                result (int):
        """
        model = self.view().model()
        item = model.item(id, 0)
        if result == core.AbstractCategoryOption.OK:
            bg = QtGui.QColor(42, 225, 98)
            icon = uilib.Icon('uiBtn_check')
        elif result == core.AbstractCategoryOption.Warning:
            bg = QtGui.QColor(235, 148, 28)
            icon = uilib.Icon('uiBtn_warning')
        elif result == core.AbstractCategoryOption.Error:
            bg = QtGui.QColor(210, 25, 46)
            icon = uilib.Icon('uiBtn_x')
        else:
            bg = self.__default_bg
            icon = uilib.Icon('uiBtn_plus')
        item.setBackground(bg)
        item.setIcon(icon)

    def addCategory(self, categoryOption):
        r"""
            カテゴリを追加する。

            Args:
                categoryOption (gadgets.checkTools.core.AbstractCategoryOption):
        """
        model = self.view().model()
        icon_item = QtGui.QStandardItem()
        icon_item.setIcon(uilib.Icon('uiBtn_plus'))
        icon_item.setSelectable(False)
        
        item = QtGui.QStandardItem(categoryOption.category())
        row = model.rowCount()
        model.setItem(row, 0, icon_item)
        model.setItem(row, 1, item)
        categoryOption.setId(row)
        categoryOption.checkingWasFinished.connect(self.updateIcon)
        if row != 0:
            return
        sel_model = self.view().selectionModel()
        sel_model.select(
            model.indexFromItem(item),
            QtCore.QItemSelectionModel.ClearAndSelect | 
            QtCore.QItemSelectionModel.Rows
        )

    def selectedData(self):
        r"""
            選択アイテムの番号と名前のリストを返す。

            Returns:
                list:(選択アイテムのインデックス、選択アイテムのData)
        """
        sel_model = self.view().selectionModel()
        result = []
        for index in sel_model.selectedIndexes():
            if index.column() == 0:
                continue
            result.append([index.row(), index.data()])
        return result

    def emit_selected_index(self, selected, deselected):
        r"""
            アイテムが選択された際にselectionChangedシグナルを送出する。
            シグナルには選択アイテムのインデックスが送られる。

            Args:
                selected (list):
                deselected (list):
        """
        if not self.__emit_selection_signal:
            return
        selected = self.selectedData()
        if not selected:
            return
        self.selectionChanged.emit(selected[0][0])

    def clearSelection(self):
        r"""
            選択を解除する。
        """
        sel_model = self.view().selectionModel()
        sel_model.clearSelection()

    def clear(self):
        r"""
            追加されたカテゴリー一覧をすべて削除する。
        """
        self.__emit_selection_signal = False
        model = self.view().model()
        model.removeRows(0, model.rowCount())
        self.__emit_selection_signal = True


class Framework(QtWidgets.QWidget):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(Framework, self).__init__(parent)
        self.setWindowTitle('Check Tools')
        
        # from importlib import reload
        # reload(core)
        self.__manager = core.CategoryManager()
        
        self.__catlist = CategoryList()
        self.__catlist.checkAllButtonClicked.connect(self.checkAll)
        self.__opt = uilib.ScrolledStackedWidget()
        self.__opt.setOrientation(QtCore.Qt.Vertical)
        self.__opt.beforeMovingTab.connect(self.updateOptionUI)
        self.__catlist.selectionChanged.connect(self.__opt.moveTo)

        splitter = QtWidgets.QSplitter()
        splitter.addWidget(self.__catlist)
        splitter.addWidget(self.__opt)
        splitter.setStretchFactor(1, 1)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(splitter)

    def manager(self):
        return self.__manager

    def optionTab(self):
        r"""
            オプション

            Returns:
                OptionTab:
        """
        return self.__opt

    def categoryList(self):
        r"""
            カテゴリ一覧の制御GUIを返す。

            Returns:
                CategoryList:
        """
        return self.__catlist

    def updateOptionUI(self, widget):
        r"""
            引数widget（AbstractCategoryOption）のcreateUIメソッドをコールして
            UI生成を促す。

            Args:
                widget (core.AbstractCategoryOption):
        """
        widget.createUI()

    def addCategory(self, moduleName, prefix=core.DefaultPrefix):
        r"""
            カテゴリを追加する。
            moduleNameで指定するモジュールは
            core.CategoryManager.ObjectNameに格納されている名前と同じ名前の、
            core.AbstractCategoryOptionを継承したサブクラスを持つ必要がある。
            また、引数prefixを指定しな場合は本モジュールと並列に設定されている
            checkModulesパッケージ内のモジュールが参照される。

            Args:
                moduleName (str): モジュール名
                prefix (str): モジュールのプレフィックス
        """
        manager = self.manager()
        key = manager.install(moduleName, prefix)
        mod = manager.getCategoryObject(key)()
        opt_tab = self.optionTab()
        opt_tab.addTab(mod)
        catlist = self.categoryList()
        catlist.addCategory(mod)
        return mod

    def clearAllCategories(self):
        opt_tab = self.optionTab()
        catlist = self.categoryList()
        opt_tab.clear()
        catlist.clear()

    def checkAll(self):
        opt_tab = self.optionTab()
        catlist = self.categoryList()
        catlist.clearSelection()
        for w in opt_tab.allWidgets():
            w.createUI()
            w.doCheck()
    
    def setCategoryFromData(self, data):
        if not data.get('dataType') == util.DataType:
            raise AttributeError(
                'The given data is not type of "{}"'.format(util.DataType)
            )
        d_pfx = data.get('defaultModulePrefix', '-default')
        if d_pfx == '-default':
            d_pfx = core.DefaultPrefix
        catlist = data.get('categoryList', [])
        self.clearAllCategories()
        for cat in catlist:
            mod_name = cat.get('moduleName')
            mod_pfx = cat.get('modulePrefix', d_pfx)
            if mod_pfx == '-default':
                mod_pfx = core.DefaultPrefix
            opt = cat.get('options', {})
            mod = self.addCategory(mod_name, mod_pfx)
            mod.setOptions(**opt)

        #GUIが変になるので強制更新。
        size = self.size()
        for i in (-1, 1):
            size.setWidth(size.width() - i)
            self.resize(size)

    def setCategoryFromFile(self, filepath):
        import json
        with open(filepath, 'r') as f:
            data = json.loads(f.read())
        self.setCategoryFromData(data)

