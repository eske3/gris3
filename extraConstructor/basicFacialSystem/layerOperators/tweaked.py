#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    顔のツイーク制御を行うためのフェイシャル用制御レイヤを提供するモジュール。
    
    Dates:
        date:2017/02/25 13:10[Eske](eske3g@gmail.com)
        update:2025/06/22 04:32 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import re
from .. import layer, tweakData
from .... import node, func
cmds = node.cmds


class Tweaked(layer.LayerOperator):
    r"""
        顔のツイーク制御を行うためのフェイシャル用制御レイヤを提供するクラス。
    """
    JointData = tweakData.TweakJointData
    JointGroupName = 'facialTweakJnt_grp'
    CtrlGroupName = 'facialTweakCtrl_grp'
    DisplayAttrName = 'facialTweakCtrlVis'
    StackFaceName = {
        'face':None, 'faceParts':('facialBrowJnt_grp',),
        'tongue':('facialInnerMouthJnt_grp',),
    }
    def prefix(self):
        return 'tweek'

    def createSetupParts(self, parentGrp):
        r"""
            このレイヤを機能させるための必要構成を作成する補助メソッド。

            Args:
                parentGrp (gris3.node.Transform):
        """
        def createJoint(data, parent):
            r"""
                Args:
                    data (dict):
                    parent (str):親ノード
            """
            for j_name, data in data.items():
                jnt = node.createNode('joint', n=j_name, p=parent)
                has_children = False
                for attr, value in data.items():
                    if attr == 'children':
                        has_children = True
                        continue
                    jnt(attr, value)
                if has_children:
                    createJoint(data['children'], jnt)

        root_grp = node.createNode(
            'transform', n=self.JointGroupName, p=parentGrp
        )
        root_grp.lockTransform()
        for grp_name, joint_data in self.JointData.items():
            grp = node.createNode('transform', n=grp_name, p=root_grp)
            grp.lockTransform()
            createJoint(joint_data, grp)

    def preSetup(self):
        cst = self.constructor()
        anim_set = self.animSet()
        tweak_grp = node.asObject(self.JointGroupName)
        root_group = self.rootGroup()
        if not tweak_grp:
            return
        # Static bind joint の作成。
        cst.createStaticJoint()
        
        tgt_objects = self.targetObjects()
        all_children = tgt_objects[0].allChildren()
        fitter = {}
        for part, targets in self.StackFaceName.items():
            name = '{}_{}Mesh'.format(part, self.prefix())
            strack_face = [x for x in all_children if x == name]
            if not strack_face:
                continue
            src = cmds.listConnections(strack_face[0]+'.inMesh', s=True, d=False)
            if not src:
                continue
            fitter[targets] = func.SurfaceFitter(src[0])
        if not fitter:
            return
        self.jointlist = {}
        for grp in tweak_grp.children():
            grp = node.parent(grp, root_group)[0]
            joints = grp.children(type='joint')
            if not joints:
                continue
            for targets, ft in fitter.items():
                if targets and grp in targets:
                    f = ft
                    break
            else:
                f = fitter[None]
            fit_joints = f.fit(joints)
            for jnts in fit_joints: 
                self.jointlist[jnts] = jnts[0].matrix()

    def postPreSetup(self):
        r"""
            コマンド実行でウェイトを読み込むと何故かジョイントの位置がずれるため
            修正パッチとして実行。
        """
        for joints, matrix in self.jointlist.items():
            joints[0].setMatrix(matrix)

    def setup(self):
        if not hasattr(self, 'jointlist'):
            return
        if not self.jointlist:
            return

        cst = self.constructor()
        sc = cst.shapeCreator()
        sc.setColorIndex((0.476, 0.097, 1.0))

        # コントローラの作成。
        ctrl_root = self.ctrlParent()
        ctrl_grp = node.createNode(
            'transform', n=self.CtrlGroupName, p=ctrl_root
        )
        ctrl_grp.lockTransform()
        anim_set = cst.createAnimSet('facialTweak')
        for jnt, spacer in self.jointlist.keys():
            name = func.Name(jnt)
            ctrl = node.createNode(
                'transform', n=name.convertType('ctrl')(), p=ctrl_grp
            )
            ctrl.editAttr(['v'], k=False, l=False)
            mltmtx = node.createUtil(
                'multMatrix', n=name.convertType('mltmtx')()
            )
            mltmtx('matrixIn[0]', jnt('matrix'), type='matrix')
            spacer.attr('matrix') >> mltmtx/'matrixIn[1]'
            mltmtx('matrixIn[2]', ctrl_grp('wim'), type='matrix')
            mltmtx.attr('matrixSum') >> ctrl/'offsetParentMatrix'
            sc.setSize(jnt('radius'))
            sc.create('sphere', parentNode=ctrl)

            jnt('offsetParentMatrix', jnt('matrix'), type='matrix')
            for attr, val in zip(['t','r','s','jo'], (0 , 0, 1, 0)):
                jnt(attr, [val for x in range(3)])
            for attr in 'trs':
                ~ctrl.attr(attr) >> ~jnt.attr(attr)
            anim_set.addChild(ctrl)
            
            # 子のコントローラを作成する。
            for child in jnt.children():
                chain = child.allChildren()
                chain.append(child)
                for c in chain:
                    c.setInverseScale()
                child('ssc', 0)
                cst.toController(
                    child, 'facialTweak', option=cst.ChainCtrl|cst.IgnoreEndCtrl
                )
                cst.connectController(
                    child, ctrl, sc, option=cst.ChainCtrl|cst.IgnoreEndCtrl
                )
        self.animSet().addChild(anim_set)

        cst = self.constructor()
        plug = self.extraConstructor().disp_ctrl.addDisplayAttr(
            self.DisplayAttrName, default=False, cb=True, k=False
        )
        plug >> ctrl_grp/'v'

    def postProcess(self):
        index_ptn = re.compile('\[(\d+)\]')
        def setBindPrematrix(jnt, parent_mtx_plug):
            r"""
                Args:
                    jnt (node.Joint):
                    parent_mtx_plug (node.Attribute):
            """
            skin_clusters = node.listConnections(
                jnt/'worldMatrix', d=True, s=False, p=True, type='skinCluster'
            )
            if not skin_clusters:
                return

            mltmtx = node.createUtil('multMatrix')
            parent_mtx_plug >> mltmtx/'matrixIn[0]'
            mltmtx('matrixIn[1]', jnt('im'), type='matrix')
            for sc in skin_clusters:
                r = index_ptn.search(sc())
                if not r:
                    continue
                index = r.group(1)
                mltmtx.attr('matrixSum') >> '{}.bindPreMatrix[{}]'.format(
                    sc.nodeName(), index
                )
            for c in jnt.children():
                setBindPrematrix(c, mltmtx.attr('matrixSum'))

        if not hasattr(self, 'jointlist'):
            return
        if not self.jointlist:
            return
        for jnt, spacer in self.jointlist:
            skin_clusters = node.listConnections(
                jnt/'worldMatrix', d=True, s=False, p=True, type='skinCluster'
            )
            if not skin_clusters:
                continue
            name = func.Name(jnt)
            name.setSuffix('ScRev')
            name.setNodeType('mltmtx')
            p_mtx = node.MMatrix(jnt('offsetParentMatrix'))
            mltmtx = node.createUtil('multMatrix', n=name())
            jnt.parent().attr('wim') >> mltmtx/'matrixIn[0]'
            mltmtx('matrixIn[1]', list(p_mtx.inverse()), type='matrix')
            for sc in skin_clusters:
                r = index_ptn.search(sc())
                if not r:
                    continue
                index = r.group(1)
                mltmtx.attr('matrixSum') >> '{}.bindPreMatrix[{}]'.format(
                    sc.nodeName(), index
                )
            for c in jnt.children():
                setBindPrematrix(c, mltmtx.attr('matrixSum'))

