# -*- coding: utf-8 -*-
r'''
    @file     frameworkGenerator.py
    @brief    フレームワークを作成するUIを提供するモジュール。現在は使用しない。
    @class    WorldCtrlSizeModifier : ここに説明文を記入
    @class    Generator : メインGUI。
    @date        2017/01/21 23:59[Eske](eske3g@gmail.com)
    @update      2017/01/21 23:59[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
import gris3
from gris3 import func, uilib, factoryModules
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

class WorldCtrlSizeModifier(QtWidgets.QSlider):
    r'''
        @brief       ここに説明文を記入
        @inheritance QtWidgets.QSlider
        @date        2017/01/21 23:59[Eske](eske3g@gmail.com)
        @update      2017/01/21 23:59[Eske](eske3g@gmail.com)
    '''
    def __init__(self, parent=None):
        r'''
            @brief  ここに説明文を記入
            @param  parent(None) : [edit]
            @return None
        '''
        super(WorldCtrlSizeModifier, self).__init__(parent)
        self.setOrientation(QtCore.Qt.Horizontal)
        self.setRange(-100, 100)
        self.__modifier = ''
        self.__shapes = []
        #self.__preselection = []
        self.sliderPressed.connect(self.setup)
        self.sliderMoved.connect(self.scaling)
        self.sliderReleased.connect(self.postProcess)

    def setup(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        self.__modifier = ''
        self.__shapes = []
        self.__preselection = []
        cmds = func.cmds
        controllers = [
            'world_ctrl','worldOffset_ctrl','local_ctrl','localOffset_ctrl'
        ]
        for ctrl in controllers:
            if not cmds.objExists(ctrl):
                return

        cmds.undoInfo(openChunk=True)
        preselection = cmds.ls(sl=True)

        self.__shapes = [
            cmds.listRelatives(x, shapes=True, type='nurbsCurve')[0]
            for x in controllers
            if cmds.listRelatives(x, shapes=True, type='nurbsCurve')
        ]
        cluster, handle = cmds.cluster(self.__shapes)
        cmds.setAttr(handle + '.io', True)
        cmds.xform(handle, ws=True, sp=(0, 0, 0))
        self.__modifier = handle

        if preselection:
            cmds.select(preselection, r=True, ne=True)
        else:
            cmds.select(cl=True)

    def scaling(self, value):
        r'''
            @brief  ここに説明文を記入
            @param  value : [edit]
            @return None
        '''
        ratio = 1 + (float(value) - self.value()) / 100
        cmds = func.cmds
        if not cmds.objExists(self.__modifier):
            return
        attr = self.__modifier + '.s'
        cmds.setAttr(attr, *[x * ratio for x in cmds.getAttr(attr)[0]])

    def postProcess(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        cmds = func.cmds
        self.__shapes = [x for x in self.__shapes if cmds.objExists(x)]
        cmds.delete(self.__shapes, ch=True)
        if cmds.objExists(self.__modifier):
            cmds.delete(self.__modifier)
        self.__shapes = []
        self.__modifier = ''
        cmds.undoInfo(closeChunk=True)

        self.setValue(0)
        

#class Generator(QtWidgets.QWidget, factoryModules.AbstractFactoryTab):
class Generator(QtWidgets.QWidget):
    r'''
        @brief       メインGUI。
        @inheritance QtWidgets.QWidget
        @date        2017/01/21 23:59[Eske](eske3g@gmail.com)
        @update      2017/01/21 23:59[Eske](eske3g@gmail.com)
    '''
    def __init__(self, parent=None):
        r'''
            @brief  初期化関数。
            @param  parent(None) : [QWidget]
            @return None
        '''
        super(Generator, self).__init__(parent)
        #self.customInit()

        flayout = QtWidgets.QFormLayout()
        
        label = QtWidgets.QLabel('World Ctrl Size')
        self.__worldctrlsize = QtWidgets.QDoubleSpinBox()
        self.__worldctrlsize.setRange(0.01, 100000)
        self.__worldctrlsize.setValue(100)
        flayout.addRow(label, self.__worldctrlsize)

        # 編集モードのUIを作成。===============================================
        edit_grp = QtWidgets.QGroupBox('Edit')
        elayout = QtWidgets.QFormLayout(edit_grp)
        
        label = QtWidgets.QLabel('Edit Ctrl Size')
        slider = WorldCtrlSizeModifier()
        elayout.addRow(label, slider)
        # =====================================================================

        btn = QtWidgets.QPushButton('Create')
        btn.clicked.connect(self.createRoot)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(flayout)
        layout.addWidget(edit_grp)
        layout.addStretch()
        layout.addWidget(btn)

    def ctrlSize(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return self.__worldctrlsize.value()

    def createRoot(self):
        r'''
            @brief  ルートノードを作成する。
            @return None
        '''
        fs = factoryModules.FactorySettings()
        with func.Do:
            gris3.createRoot(
                fs.assetName(), fs.project(), fs.assetType(),
                self.ctrlSize()
            )

