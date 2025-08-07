#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    任意の構造のフェイシャルデータを元に、フェイシャルセットアップを行うための
    ExtraConstructor。
    
    Dates:
        date:2017/02/25 13:10[Eske](eske3g@gmail.com)
        update:2025/06/01 17:10 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import re
from collections import OrderedDict
from ... import extraConstructor, node, func, uilib
from ...extraConstructor import ui
from . import layer, layerOperators, eyeHighlightRig
cmds = node.cmds
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

from . import tweakData, bodyCombiner
class ColorData(object):
    L = (0.044, 0.011, 0.88)
    R = (0.973, 0.02, 0.115)
    C = (0.7, 0.873, 0.207)


class FacialPartsMaker(ui.ExtraConstructorUtil):
    construtor = None
    extraConstructor = None
    def __init__(self, groupName, extraConstructor, parent=None):
        super(FacialPartsMaker, self).__init__(parent)
        self.__ext_const = extraConstructor
        self.__grp_name = groupName
        self.__layers = []

    def extraConstructor(self):
        return self.__ext_const

    def label(self):
        return 'Facial Parts Maker'

    def setGroupName(self, groupName):
        self.__grp_name = groupName

    def groupName(self):
        return self.__grp_name

    def buildUI(self):
        btn = QtWidgets.QPushButton('Create facial parts')
        btn.clicked.connect(self.createFacialParts)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(btn)
    
    def createFacialParts(self):
        ext_cst = self.extraConstructor()
        cst = ext_cst.constructor()

        with node.DoCommand():
            grp = node.createNode('transform', n=self.groupName())
            grp.lockTransform()
            for l in ext_cst.layerManager().layers():
                lo = l(cst, ext_cst, None, None)
                lo.createSetupParts(grp)
            cmds.select(grp, r=True)


class ExtraConstructor(extraConstructor.ExtraConstructor):
    r"""
        フェイシャルセットアップを行うためのクラス。
    """
    FacialGroup = 'face_grp'
    FaceGeo = 'face_geo'
    FaceCage = 'face_cage'
    PartsGroup = 'facialSetupParts_grp'
    FacialCategoryPattern = '(.*?)FacialTarget_grp'
    Parent = 'head_ctrl_C'
    EyeHighlightGeoGroup = 'eyeHighLight_grp'
    LayerInitMethod = 'initFacialLayerOperator'
    EyeBallUnit = None
    IsSetup = False
    DefaultLayerOperatorList = ['BlendShape', 'JawOpener', 'Tweaked']

    def __init__(self, const):
        r"""
            Args:
                const (gris3.constructors.BasicExtractor):
        """
        super(ExtraConstructor, self).__init__(const)
        self.__layer_manager = layer.LayerManager(const, self)
        self.__eye_highlight_system = None
        self.__eye_joints = {}
        self.__combined_objects = []
        self.__combined_cages = []
        self.disp_ctrl = None
        const.combineBody = self.combineBody

    def createEyeHighlightSystem(self):
        r"""
            目のハイライトのセットアップ用オブジェクトを作成して返す。

            Returns:
                const (eyeHighlightRig.EyeHighlightSetup):
        """
        return eyeHighlightRig.EyeHighlightSetup(
            self.EyeHighlightGeoGroup, self.constructor(), self.Parent,
            self.EyeBallUnit
        )

    def initializeEyeHighlightSystem(self):
        self.__eye_highlight_system = self.createEyeHighlightSystem()

    def defaultLayerOperators(self):
        layers = layerOperators.listAllLayerOperators()
        return [layers[x] for x in self.DefaultLayerOperatorList]

    def layerManager(self):
        r"""
            レイヤー管理オブジェクトを返す。
            
            Returns:
                layer.LayerManager:
        """
        return self.__layer_manager

    def eyeHighlightSystem(self):
        return self.__eye_highlight_system

    def setCombinedObjects(self, *objects):
        r"""
            フェイシャル用の顔と胴体を結合するためのメッシュを登録する。
            
            Args:
                *objects (str):
        """
        self.__combined_objects = list(objects)

    def setCombinedCages(self, *cages):
        r"""
            フェイシャル用の顔と胴体を結合するためのケージを登録する。

            Args:
                *cages (str):
        """
        self.__combined_cages = list(cages)

    def combineBody(self, wraplist=None):
        r"""
            フェイシャル用の顔メッシュと胴体を結合する。
            引数wraplistは、StandardConstrcutorのテンプレートで使用されている
            WrapList(辞書オブジェクト)を渡す。
            WrapListは結合処理後、結合したメッシュ名で上書きする。

            Args:
                wraplist (dict): 
        """
        cst = self.constructor()
        geo, cage = None, None
        if self.__combined_objects:
            parent = cst.modelGroup()
            geo = bodyCombiner.combineFace(
                self.FaceGeo, self.__combined_objects, parent
            )
        if self.__combined_cages:
            parent = cst.root().setupGroup().cageGroup()
            cage = bodyCombiner.combineFaceCage(
                self.FaceCage, self.__combined_cages, parent
            )
        if not cage or wraplist is None:
            return
        geolist = wraplist.setdefault(cage, [])
        if not geo in geolist and geo is not None:
            geolist.append(geo)

        # face_cageでラップしていたオブジェクトを新しいcageに移す。
        wrapped_by_face = wraplist.get(self.FaceCage, [])
        if not isinstance(wrapped_by_face, (list, tuple)):
            wrapped_by_face = [wrapped_by_face]
        if wrapped_by_face:
            for g in wrapped_by_face:
                if not cmds.objExists(g):
                    continue
                geolist.append(g)
            del wraplist[self.FaceCage]

    def createSetupParts(self):
        r"""
            layerOperatorごとに必要なノード郡を作成するための便利メソッド。
        """
        grp = node.createNode('transform', n='facialSetupParts_grp')
        grp.lockTransform()
        self.layerManager().createSetupParts(grp)
        cmds.select(grp, r=True)

    def _preSetup(self):
        r"""
            preSetup前に行う処理
        """
        self.initializeEyeHighlightSystem()
        cst = self.constructor()
        self.disp_ctrl = cst.ctrlGroup().displayCtrl()
        
        # 眼のセットアップ準備を行う。
        highlight_system = self.eyeHighlightSystem()
        highlight_system.initialize()
        highlight_system.preSetup()

        # フェイシャルグループと、ターゲットのグループがあるかの確認。=========
        facial_grp = node.asObject(self.FacialGroup)
        if not facial_grp:
            return
        self.IsSetup = True
        # =====================================================================

        root_grp = node.createNode(
            'transform', n='facialSetup_grp', p=cst.setupGroup()
        )
        root_grp.lockTransform()
        cage_grp = cst.setupGroup().cageGroup()
        anim_set = cst.createAnimSet('facial')

        # FacialGroupをセットアップ用にグループごと複製。======================
        if hasattr(cst, self.LayerInitMethod):
            init_method = getattr(cst, self.LayerInitMethod)
        else:
            init_method = None
        l_manager = self.layerManager()
        facial_targets, copied_list = l_manager.setup(
            facial_grp, root_grp, cage_grp, self.Parent, anim_set,
            init_method
        )

        print('# Copied from facial group.'.ljust(80, '='))
        for c in copied_list:
            print('  + {}'.format(c))
        print('=' * 80)

        if copied_list:
            cst.FacialWrapList = {
                x: [y] for x, y in zip(copied_list[-1][2:], facial_targets)
            }
        else:
            cst.FacialWrapList = {}
        # =====================================================================

        # 目のハイライトの処理。===============================================
        cst.FacialParentList = highlight_system.createBaseJoint()
        # =====================================================================

        l_manager.preSetupLayers()

    def preSetup(self):
        r"""
            preSetup後に行う処理
        """
        self.layerManager().postPreSetupLayers()

    def setup(self):
        self.layerManager().setupLayers()
        self.eyeHighlightSystem().createControllers()

    def _postProcess(self):
        r"""
            セットアップ後、ポスト処理前に実行されるメソッド
        """
        if not self.IsSetup:
            return
        self.layerManager().postProcessLayers()

        cst = self.constructor()
        plug = self.disp_ctrl.addDisplayAttr(
            'facialCtrlVis', default=False, cb=True, k=False
        )
        self.layerManager().connectVisibility(plug)

    def setupUtil(self):
        w = FacialPartsMaker(self.PartsGroup, self)
        return w
