#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    顎の開閉を行うためのフェイシャル用制御レイヤを提供するモジュール。
    
    Dates:
        date:2017/02/25 13:10[Eske](eske3g@gmail.com)
        update:2025/06/01 22:19 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from collections import OrderedDict
from .... import node, func
from .. import layer
cmds = node.cmds


class JawOpener(layer.LayerOperator):
    r"""
        顎の開閉を行うためのフェイシャル用制御レイヤを提供するLayerOperator。
    """
    def prefix(self):
        return 'jaw'

    def createSetupParts(self, parentGrp):
        r"""
            このレイヤを機能させるための必要構成を作成する補助メソッド。

            Args:
                parentGrp (gris3.node.Transform):
        """
        jntdata = OrderedDict()
        jntdata['facialJawRoot_jnt_C'] = {
            't':(0, 142.5, 1.35),
            'jo':(0, -57, -90),
            'radius':0.8,
        }
        jntdata['facialJawRootEnd_jnt_C'] = {
            't':(8.2, 0, 0),
            'radius':0.5,
        }
        parent = parentGrp
        for name, data in jntdata.items():
            jnt = node.createNode('joint', n=name, p=parent)
            for attr, value in data.items():
                jnt(attr, value)
            parent = jnt

    def preSetup(self):
        cst = self.constructor()
        jaw_root = node.asObject('facialJawRoot_jnt_C')
        if not jaw_root:
            return
        self.jaw_root = node.parent(jaw_root, self.rootGroup())[0]
        # Static bind joint の作成。
        cst.createStaticJoint()

    def setup(self):
        if not hasattr(self, 'jaw_root'):
            return

        cst = self.constructor()
        # コントローラの作成。
        ctrl_root = self.ctrlParent()
        grp = node.createNode(
            'transform', n='facialJawSetup_grp_C', p=self.rootGroup()
        )
        grp.fitTo(ctrl_root)
        grp.lockTransform()

        end_jnt = self.jaw_root.children()
        if  not end_jnt:
            return
        end_jnt = end_jnt[0]
        ik, ee = node.createIkHandle(
            'facialJaw_ik', parent=grp, sj=self.jaw_root, ee=end_jnt,
            sol='ikRPsolver'
        )
        pv = func.createPoleVector(ik)[0]
        grp.addChild(pv)
        pv.rename('facialJaw_pv')
        ctrl_proxy = node.createNode(
            'transform', n='facialJaw_ctrlProxy', p=grp
        )
        ctrl_proxy.fitTo(end_jnt)
        ctrl_proxy.addChild(ik)

        ctrl = node.createNode('transform', n='facialJaw_ctrl', p=ctrl_root)
        ctrl('offsetParentMatrix', ctrl_proxy.matrix(False), type='matrix')
        mltmtx = node.createUtil('multMatrix', n='facialJawPos_mltmtx')
        ctrl.attr('matrix') >> mltmtx/'matrixIn[0]'
        mltmtx('matrixIn[1]', ctrl('offsetParentMatrix'), type='matrix')
        mltmtx.attr('matrixSum') >> ctrl_proxy/'offsetParentMatrix'
        for at, v in zip('trs', (0, 0, 1)):
            ctrl_proxy(at, [v for x in range(3)])
        ctrl.lockTransform()
        ctrl.editAttr(['t:a'], l=False, k=True)

        jaw_vec = (
            node.MVector(end_jnt.position())
            -node.MVector(self.jaw_root.position())
        )
        sc = cst.shapeCreator()
        sc.setRotation((0.0, 0.0, -90.0))
        sc.setSize(jaw_vec.length()*0.2)
        sc.setColorIndex((0.655, 0.887, 0.242))
        sc.create('arrowFour', parentNode=ctrl)
        self.animSet().addChild(ctrl)
        self.addHiddenCtrl(ctrl)


