# -*- coding: utf-8 -*-
r'''
    @file     surfaceMaterialTools.py
    @brief    リネームに関するウィジェットを提供するモジュール。
    @class    MaterialLister : 選択ノードがアサインされているマテリアルを一覧する
    @class    MainWidget : SimpleRenamerの単独ウィンドウを提供するクラス。
    @function showWindow : 選択ノードの数に応じて最適なリネーマーを表示する
    @date        2017/05/30 5:36[Eske](eske3g@gmail.com)
    @update      2019/03/24 11:39[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
from gris3 import uilib
from gris3.uilib import mayaUIlib
from gris3.tools import surfaceMaterialUtil as smu
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

class MaterialLister(QtWidgets.QWidget):
    r'''
        @brief       選択ノードがアサインされているマテリアルを一覧する
        @inheritance QtWidgets.QWidget
        @date        2018/03/29 12:02[Eske](eske3g@gmail.com)
        @update      2019/03/24 11:39[Eske](eske3g@gmail.com)
    '''
    def __init__(self, parent=None):
        r'''
            @brief  初期化を行う。
            @param  parent(None) : [QtWidgets.QWidget]
            @return None
        '''
        super(MaterialLister, self).__init__(parent)
        self.__update_selection = True
        self.__nodelist = []
        self.setWindowTitle('+Material Lister')

        model = QtGui.QStandardItemModel(0, 1)
        sel_model = QtCore.QItemSelectionModel(model)
        # sel_model.selectionChanged.connect(self.doAction)

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
        r'''
            @brief  リストを更新する
            @return None
        '''
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
        r'''
            @brief  リストで選択されているマテリアルを選択する
            @param  index : [QtCore.QModelIndex]
            @return None
        '''
        if (
            QtWidgets.QApplication.mouseButtons() == QtCore.Qt.RightButton
            or not self.__update_selection
        ):
            return
        mayaUIlib.select([index.data()])

    def selectAssignedFaces(self, index):
        r'''
            @brief  indexのマテリアル名でアサインされている面を選択する
            @param  index : [QtCore.QModelIndex]
            @return None
        '''
        mat = index.data()
        faces = smu.listMaterialMembers([mat], self.__nodelist)
        if not faces:
            return
        mayaUIlib.select(faces)

    def doAction(self, index):
        r'''
            @brief  リストをクリックしたときのアクションを行う
            @param  index : [QtCore.QModelIndex]
            @return None
        '''
        if (
            QtWidgets.QApplication.keyboardModifiers()
            == QtCore.Qt.ShiftModifier
        ):
            self.selectAssignedFaces(index)
        else:
            self.selectMaterial(index)

    def assingMaterial(self, pos):
        r'''
            @brief  選択オブジェクトに対してマテリアルをアサインする
            @param  pos : [QtCore.QPoint]
            @return None
        '''
        item = self.__material_list.indexAt(pos)
        material = item.data()
        if not material:
            return
        smu.assignMaterialToSelected(material)

class MainWidget(uilib.AbstractSeparatedWindow):
    r'''
        @brief       SimpleRenamerの単独ウィンドウを提供するクラス。
        @inheritance uilib.AbstractSeparatedWindow
        @date        2017/03/17 3:14[Eske](eske3g@gmail.com)
        @update      2019/03/24 11:39[Eske](eske3g@gmail.com)
    '''
    def centralWidget(self):
        r'''
            @brief  UIの作成を行う。
            @return None
        '''
        return MaterialLister(self)

    def show(self, nodelist=[]):
        r'''
            @brief  ここに説明文を記入
            @param  nodelist([]) : [edit]
            @return None
        '''
        self.resize(250, 320)
        main = self.main()
        main.updateList()
        super(MainWidget, self).show()

def showWindow():
    r'''
        @brief  選択ノードの数に応じて最適なリネーマーを表示する
        @return None
    '''
    w = MainWidget(mayaUIlib.MainWindow)
    w.show()
    return w