# -*- coding:utf-8 -*-

from ..tools import operationHelper
from .. import uilib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

class SelectionMemoryWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(SelectionMemoryWidget, self).__init__(parent)
        self.setWindowTitle('+Selection Memory')

        # 一覧表示するビューの作成。==========================================
        model = QtGui.QStandardItemModel(0, 1)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Node List')
        
        sel_model = QtCore.QItemSelectionModel(model)
        sel_model.selectionChanged.connect(self.select)

        view = QtWidgets.QTreeView()
        view.setAlternatingRowColors(True)
        view.setEditTriggers(view.NoEditTriggers)
        view.setSelectionMode(view.ExtendedSelection)
        view.setModel(model)
        view.setSelectionModel(sel_model)
        view.setHeaderHidden(True)
        view.expanded.connect(self.updateChildren)
        # ====================================================================

        # 各種ボタン。========================================================
        add_btn = uilib.OButton(uilib.IconPath('uiBtn_plus'))
        add_btn.clicked.connect(self.add)

        rel_btn = uilib.OButton(uilib.IconPath('uiBtn_reload'))
        rel_btn.clicked.connect(self.refresh)
        # ====================================================================

        layout = QtWidgets.QGridLayout(self)
        layout.setSpacing(1)
        layout.addWidget(add_btn, 0, 0, 1, 1)
        layout.addWidget(rel_btn, 0, 1, 1, 1)
        layout.addWidget(view, 1, 0, 1, 3)
        layout.setColumnStretch(2, 1)

        self.__view = view

    def add(self):
        operationHelper.SelectionMemory().add()
        self.refresh()

    def refresh(self):
        model = self.__view.model()
        model.removeRows(0, model.rowCount())
        for nodelist in operationHelper.SelectionMemory():
            parent_item = QtGui.QStandardItem()
            model.setItem(model.rowCount(), 0, parent_item)
            namelist = []
            count = 0
            for n in nodelist:
                name = n.rsplit('|', 1)[-1]
                namelist.append(name)
                count += len(name)
                if count > 45:
                    count = -1
                    break
            name = ', '.join(namelist)[:45]
            if count == -1:
                name += '...'
            parent_item.setText(name)
            
            null_item = QtGui.QStandardItem()
            null_item.setData('!')
            parent_item.setChild(0, 0, null_item)

    def updateChildren(self, index):
        parent_item = index.model().itemFromIndex(index)
        child = parent_item.child(0, 0)
        if child.data() != '!':
            # 更新済みの場合は何もしない
            return
        parent_item.removeRows(0, parent_item.rowCount())
        for row, name in enumerate(
            operationHelper.SelectionMemory()[index.row()]
        ):
            item = QtGui.QStandardItem(name.rsplit('|', 1)[-1])
            item.setData(name)
            parent_item.setChild(row, 0, item)

    def select(self, selected, deselected):
        sel_model = self.__view.selectionModel()
        rows = []
        for index in sel_model.selectedIndexes():
            parent = index.parent()
            model = parent.model()
            if model:
                continue
            rows.append(index.row())
        operationHelper.SelectionMemory().select(rows, ne=True)
        

class MainGUI(uilib.AbstractSeparatedWindow):
    r'''
        @brief       ここに説明文を記入
        @inheritance uilib.AbstractSeparatedWindow
        @date        2017/06/27 18:31[s_eske](eske3g@gmail.com)
        @update      2018/02/01 13:24[eske](eske3g@gmail.com)
    '''
    def centralWidget(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return SelectionMemoryWidget()

def showWindow():
    r'''
        @brief  ウィンドウを作成するためのエントリ関数。
        @return QtWidgets.QWidget
    '''
    from gris3.uilib import mayaUIlib
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(300, 450)
    widget.show()
    return widget