#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    選択オブジェクトにアサインされているマテリアルを一覧、変種するための
    機能を提供するガジェット。

    Dates:
        date:2017/05/30 5:36[Eske](eske3g@gmail.com)
        update:2025/11/11 11:40 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import uilib
from ..uilib import mayaUIlib
from ..tools import surfaceMaterialUtil as smu
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class MaterialLister(QtWidgets.QWidget):
    r"""
        選択ノードがアサインされているマテリアルを一覧する
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(MaterialLister, self).__init__(parent)
        self.__update_selection = True
        self.__nodelist = []
        self.setWindowTitle('+Material Lister')

        model = QtGui.QStandardItemModel(0, 1)
        sel_model = QtCore.QItemSelectionModel(model)

        self.__material_list = QtWidgets.QListView()
        self.__material_list.setVerticalScrollMode(
            QtWidgets.QListView.ScrollPerPixel
        )
        self.__material_list.setEditTriggers(QtWidgets.QListView.NoEditTriggers)
        self.__material_list.setAlternatingRowColors(True)
        self.__material_list.setModel(model)
        self.__material_list.setSelectionModel(sel_model)
        self.__material_list.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.__material_list.customContextMenuRequested.connect(
            self.assingMaterial
        )
        self.__material_list.clicked.connect(self.doAction)
        
        note = QtWidgets.QLabel(
            'Note:Click by right button to assign material.\n'
            'Shift + click button to select assigned faces.'
        )
        
        ref_btn = uilib.OButton(uilib.IconPath('uiBtn_reset'))
        ref_btn.setToolTip('Reload from selected.')
        ref_btn.setSize(48)
        ref_btn.clicked.connect(self.updateList)

        layout =  QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.addWidget(self.__material_list)
        layout.addWidget(note)
        layout.addWidget(ref_btn)
        layout.setAlignment(ref_btn, QtCore.Qt.AlignCenter)

    def updateList(self):
        r"""
            リストを更新する
        """
        model = self.__material_list.model()
        self.__update_selection = False
        model.removeRows(0, model.rowCount())
        self.__update_selection = True

        matdata = smu.listMaterials()
        if not matdata:
            return
        materials, self.__nodelist = matdata
        for row, mat in enumerate(materials):
            item = QtGui.QStandardItem(mat.name())
            item.setSizeHint(QtCore.QSize(item.sizeHint().width(), 32))
            model.setItem(row, 0, item)

    def selectMaterial(self, index):
        r"""
            リストで選択されているマテリアルを選択する
            
            Args:
                index (QtCore.QModelIndex):
        """
        if (
            QtWidgets.QApplication.mouseButtons() == QtCore.Qt.RightButton
            or not self.__update_selection
        ):
            return
        mayaUIlib.select([index.data()])

    def selectAssignedFaces(self, index):
        r"""
            indexのマテリアル名でアサインされている面を選択する
            
            Args:
                index (QtCore.QModelIndex):
        """
        mat = index.data()
        faces = smu.listMaterialMembers([mat], self.__nodelist)
        if not faces:
            return
        mayaUIlib.select(faces)

    def doAction(self, index):
        r"""
            リストをクリックしたときのアクションを行う
            
            Args:
                index (QtCore.QModelIndex):
        """
        if (
            QtWidgets.QApplication.keyboardModifiers()
            == QtCore.Qt.ShiftModifier
        ):
            self.selectAssignedFaces(index)
        else:
            self.selectMaterial(index)

    def assingMaterial(self, pos):
        r"""
            選択オブジェクトに対してマテリアルをアサインする
            
            Args:
                pos (QtCore.QPoint):
        """
        item = self.__material_list.indexAt(pos)
        material = item.data()
        if not material:
            return
        smu.assignMaterialToSelected(material)


class MainWidget(uilib.AbstractSeparatedWindow):
    r"""
        MaterialListerの単独ウィンドウを提供するクラス。
    """
    def centralWidget(self):
        r"""
            MaterialListerを作成して返す。
            
            Returns:
                MaterialLister:
        """
        return MaterialLister(self)

    def show(self, nodelist=[]):
        r"""
            Args:
                nodelist (list):
        """
        self.resize(250, 320)
        main = self.main()
        main.updateList()
        super(MainWidget, self).show()


def showWindow():
    r"""
        選択ノードの数に応じて最適なリネーマーを表示する
        
        Returns:
            MainWidget:
    """
    w = MainWidget(mayaUIlib.MainWindow)
    w.show()
    return w