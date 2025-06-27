#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    シーンのクリーンナップするための補助ツール
    
    Dates:
        date:2017/07/06 5:35[Eske](eske3g@gmail.com)
        update:2021/04/24 02:43 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3.tools import modelChecker
from gris3 import uilib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class CleanupPlugins(QtWidgets.QGroupBox):
    r"""
        プラグインに関するクリーンナップ機能を提供するクラス
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(CleanupPlugins, self).__init__('Cleanup Plugins', parent)
        from gris3.tools import cleanup

        del_unknowns = QtWidgets.QPushButton('Delete All unknonw nodes')
        del_unknowns.clicked.connect(cleanup.deleteAllUnknownNodes)
        rem_info_btn = QtWidgets.QPushButton('Remove all plugin info')
        rem_info_btn.clicked.connect(cleanup.removeUnknownPlugins)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(1)
        layout.addWidget(del_unknowns)
        layout.addWidget(rem_info_btn)
        layout.addStretch()


class CleanupObject(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(CleanupObject, self).__init__('Cleanup Object', parent)
        self.__check = []
        layout = QtWidgets.QVBoxLayout(self)

        for label in (
            'Delete IO', 'Delete User Defined Attrs', 'Unlock Transform',
            'Default Render Stats'
        ):
            cb = QtWidgets.QCheckBox(label)
            cb.setChecked(True)
            layout.addWidget(cb)
            self.__check.append(cb)
        btn = QtWidgets.QPushButton('Clean up')
        btn.clicked.connect(self.doCleanup)
        layout.addWidget(btn)

    def doCleanup(self):
        from gris3.tools import cleanup
        from gris3 import func
        methods = [
            cleanup.deleteUnusedIO, cleanup.deleteUnusedUserDefinedAttr,
            func.unlockTransform, func.setRenderStats
        ]
        with func.Do:
            nodelist = func.node.selected()
            for cb, m in zip(self.__check, methods):
                if not cb.isChecked():
                    continue
                m(nodelist)


class CleanupMesh(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(CleanupMesh, self).__init__('Cleanup Mesh', parent)
        self.__check = []
        layout = QtWidgets.QGridLayout(self)

        self.__th_field = QtWidgets.QDoubleSpinBox()
        self.__th_field.setRange(0, 1.0)
        self.__th_field.setDecimals(4)
        self.__th_field.setValue(0.995)
        self.__th_field.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        
        btn = QtWidgets.QPushButton('Convert hardedge to hardedge  info')
        btn.clicked.connect(self.convHardedge)
        
        layout.addWidget(btn, 0, 0, 1, 1)
        layout.addWidget(self.__th_field, 0, 1, 1, 1)

    def convHardedge(self):
        from gris3.tools import modelingSupporter
        from gris3 import func
        with func.Do:
            modelingSupporter.unlockAndSetNormal(
                threshold=self.__th_field.value()
            )


class BasicNameLister(QtWidgets.QWidget):
    r"""
        重複した名前のノードを検出する機能を提供するクラス
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(BasicNameLister, self).__init__(parent)
        # modelの設定
        model = self.createNodel()
        # selectionModelの設定。
        sel_model = QtCore.QItemSelectionModel(model)
        sel_model.selectionChanged.connect(self.selectSelectedItems)

        self.__view = QtWidgets.QTreeView()
        self.__view.setModel(model)
        self.__view.setSelectionModel(sel_model)
        self.__view.setAlternatingRowColors(True)
        self.__view.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.__view.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )
        
        rel_btn = uilib.OButton()
        rel_btn.setSize(28)
        rel_btn.setIcon(uilib.IconPath('uiBtn_reload'))
        rel_btn.clicked.connect(self.updateList)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(1)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.addWidget(rel_btn)
        layout.setAlignment(rel_btn, QtCore.Qt.AlignLeft)
        layout.addWidget(self.__view)

    def createNodel(self):
        model = QtGui.QStandardItemModel(0, 1)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Node Name')
        return model

    def view(self):
        return self.__view

    def updateList(self):
        pass

    def selectSelectedItems(self, selected, deselected):
        r"""
            Args:
                selected (any):
                deselected (any):
        """
        nodelist = []
        for index in self.view().selectionModel().selectedIndexes():
            nodelist.append(index.data(QtCore.Qt.UserRole+1))
        print(nodelist)
        modelChecker.selectNodeByName(nodelist)


class DuplicatedNameLister(BasicNameLister):
    r"""
        重複した名前のノードを検出する機能を提供するクラス
    """
    def updateList(self):
        model = self.view().model()
        model.removeRows(0, model.rowCount())

        duplicated_names = modelChecker.listDuplicateName()
        compiled_names = {}
        for name in duplicated_names:
            parent, key = name.rsplit('|', 1)
            if key in compiled_names:
                compiled_names[key].append(name)
            else:
                compiled_names[key] = [name]
        keylist = list(compiled_names.keys())
        keylist.sort()
        for i, key in enumerate(keylist):
            # 共通名を持つ親アイテムを作成する。
            item = QtGui.QStandardItem(key)
            item.setData(item)
            model.setItem(model.rowCount(), 0, item)
            index = model.indexFromItem(item)

            for j, child in enumerate(compiled_names[key]):
                c_item = QtGui.QStandardItem(child)
                c_item.setData(child)
                item.setChild(j, 0, c_item)

        
class IntermediateObjectLister(BasicNameLister):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(IntermediateObjectLister, self).__init__(parent)
        view = self.view()
        view.setRootIsDecorated(False)
        view.setColumnWidth(0, 20)
        view.setColumnWidth(1, 200)
        view.setColumnWidth(2, 20)

    def createNodel(self):
        r"""
            Returns:
                QtGui.QStandardItemModel:
        """
        model = QtGui.QStandardItemModel(0, 3)
        for i, l in enumerate(('in', 'Node Name', 'out')):
            model.setHeaderData(i, QtCore.Qt.Horizontal, l)
        return model

    def updateList(self):
        model = self.view().model()
        model.removeRows(0, model.rowCount())
        for lst, markers in zip(
            modelChecker.listIntermediates(), 
            (('', ''), ('->', ''), ('', '->'), ('->', '->'))
        ):
            for n in lst:
                row = model.rowCount()
                item = QtGui.QStandardItem(n)
                in_item = QtGui.QStandardItem(markers[0])
                out_item = QtGui.QStandardItem(markers[1])
                model.setItem(row, 0, in_item)
                model.setItem(row, 1, item)
                model.setItem(row, 2, out_item)
        view = self.view()

    def selectSelectedItems(self, selected, deselected):
        r"""
            Args:
                selected (any):
                deselected (any):
        """
        nodelist = []
        for index in [
            x for x in self.view().selectionModel().selectedIndexes()
            if x.column() == 1
        ]:
            nodelist.append(index.data())
        modelChecker.selectNodeByName(nodelist)


class InstanceLister(BasicNameLister):
    r"""
        シーン内のインスタンスオブジェクトをリストする。
    """
    def createModel(self):
        model = QtGui.QStandardItemModel(0, 1)
        for i, l in enumerate(['Instanced Objects']):
            model.setHeaderData(i, QtCore.Qt.Horizontal, l)
        return model
    
    def updateList(self):
        model = self.view().model()
        model.removeRows(0, model.rowCount())
        i = 0
        for i, data in enumerate(modelChecker.listInstances()):
            shape_name, objects = data
            item = QtGui.QStandardItem(shape_name)
            item.setData(shape_name)
            model.setItem(i, 0, item)
            for j, o in enumerate(objects):
                child = QtGui.QStandardItem(o())
                child.setData(o())
                item.setChild(j, 0, child)


class ModelChecker(QtWidgets.QTabWidget):
    r"""
        モデルのチェックを行うためのツール群を提供するクラス
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ModelChecker, self).__init__(parent)
        self.addTab(DuplicatedNameLister(), 'Duplicated Name')
        self.addTab(IntermediateObjectLister(), 'Intermediates')
        self.addTab(InstanceLister(), 'Instance')


class CleanupToolWidget(QtWidgets.QWidget):
    r"""
        モデルデータの作成、チェックを行う機能を提供するクラス
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(CleanupToolWidget, self).__init__(parent)
        self.setWindowTitle('+Cleaup Tools')
        
        # Mult-Renamer起動ボタン。=============================================
        from gris3 import gadgets
        btn = uilib.OButton()
        btn.setSize(32)
        btn.setBgColor(64, 160, 96)
        btn.setIcon(uilib.IconPath('uiBtn_rename'))
        btn.setToolTip('Show multi - renamer.')
        btn.clicked.connect(gadgets.showRenamer)
        
        a_ren_btn = uilib.OButton()
        a_ren_btn.setSize(32)
        a_ren_btn.setBgColor(190, 28, 65)
        a_ren_btn.setIcon(uilib.IconPath('uiBtn_rename'))
        a_ren_btn.setToolTip('Show Auto Renamer for joint.')
        a_ren_btn.clicked.connect(gadgets.showAutoRenamer)
        
        renamers = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(renamers)
        layout.addWidget(btn)
        layout.addWidget(a_ren_btn)
        layout.addStretch()
        # =====================================================================

        # オブジェクトのクリーンナップ。
        cleanup_obj = CleanupObject()
        # メッシュのクリーンナップ。
        cleanup_mesh = CleanupMesh()
        # データのクリーンナップ。
        plugins = CleanupPlugins()
        
        # モデルチェッカー
        model_checker = ModelChecker()

        layout = QtWidgets.QGridLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.addWidget(renamers, 0, 0, 1, 2)
        layout.addWidget(cleanup_obj, 1, 0, 2, 1)
        layout.addWidget(cleanup_mesh, 1, 1, 1, 1)
        layout.addWidget(plugins, 2, 1, 1, 1)
        layout.addWidget(model_checker, 3, 0, 1, 2)
        layout.setRowStretch(3, 1)


class MainGUI(uilib.AbstractSeparatedWindow):
    def centralWidget(self):
        r"""
            Returns:
                CleanupToolWidget:
        """
        return CleanupToolWidget()


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。
        
        Returns:
            MainGUI:
    """
    from gris3.uilib import mayaUIlib
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(uilib.hiRes(300), uilib.hires(450))
    widget.show()
    return widget