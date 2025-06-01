#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    目のハイライトオブジェクトを一つ一つ手動で制御するためのコントローラを
    作成するための機能を提供するモジュール。
    このモジュールを使用する場合、eyeBallリグモジュールが自動的に作成されるため、
    頭部ジョイントの直下には
    eye_jnt_L/R
    という名前のジョイントを直接配置しておく
    （これはリグモジュールのジョイントではなく、手動で作成したジョイント）
    
    Dates:
        date:2025/06/01 16:58 Eske Yoshinob[eske3g@gmail.com]
        update:2025/06/01 16:58 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2025 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from collections import OrderedDict
from ... import node, func
from ...tools import jointEditor


class EyeHighlightSetup(object):
    ColorData = {
        'L':(0.044, 0.011, 0.88),
        'R':(0.973, 0.02, 0.115),
    }
    def __init__(
        self, highlightGroup, parentJoint, constructor, parentCtrlName
    ):
        r"""
            Args:
                constructor (constructors.BasicConstructor):
                parentJoints (str): 目のリグの親となるジョイント名
                constructor (constructors.BasicConstructor):
                parentCtrlName (str):
        """
        grp = node.asObject(highlightGroup)
        self.highlights = OrderedDict()
        self.__parent_joint = node.asObject(parentJoint)
        self.__eye_joints = {}
        self.parent_ctrl_name = parentCtrlName
        self.constructor = constructor
        self.isValid = False
        if not grp or not self.__parent_joint:
            return
        self.isValid = True
        for geo in grp.children():
            self.highlights[geo] = {}

    def parentJoint(self):
        r"""
            目のリグの親おとなるジョイント。

            Returns:
                node.Joint:
        """
        return self.__parent_joint

    def preSetup(self):
        for s in func.SuffixIter():
            if not cmds.objExists('eye_jnt'*s):
                return

        head_jnt = self.parentJoint()
        end_jnt = head_jnt.children()[0]
        head_len = (
            node.MVector(end_jnt.position()) - node.MVector(head_jnt.position())
        ).length()
        creator = core.createJoint('eyeBallRig', 'eyeBall', 'C', parent=head_jnt)
        unit = creator.unit()
        
        # ルートの位置を頭部の位置に合わせる。
        root = unit.getMember('root')
        root.setPosition(head_jnt.position())
        for s in func.SuffixIter():
            keys = 'eye'+s, 'target'+s
            eye = unit.getMember(keys[0])
            cmds.delete(eye)
            jnt = node.asObject('eye_jnt'*s)
            jnt('ssc', 0)
            jnt('ssc', 0.2)
            target_jnt = jnt.children()[0]
            target_jnt('ssc', 0.05)
            unit.addMember(keys[0], jnt)
            unit.addMember(keys[1], target_jnt)
            root.addChild(jnt)

            pos = node.MVector(jnt.position())
            eye_vec = (node.MVector(target_jnt.position()) - pos).normal()
            eye_vec = eye_vec * head_len * 2
            eye_vec[0] = eye_vec[0] * 0.25
            new_pos = pos + eye_vec
            target_jnt.setPosition(new_pos)
            jointEditor.fixOrientation(jnt)
            
            self.__eye_joints[s] = jnt

    def createBaseJoint(self):
        if not self.isValid or not self.highlights or not self.__eye_joints:
            return {}
        om = jointEditor.OrientationModifier()
        om.setSecondaryAxis('+Y')
        om.setTargetUpAxis('+Y')
        om.setSecondaryMode('vector')
        parent_list = {}

        parents = {}
        positions = list(self.__eye_joints.keys())
        positions.sort()
        for s in positions:
            jnt = self.__eye_joints[s]
            name = func.Name(jnt)
            name.setSuffix('Hl')
            name.setNodeType('posProxy')
            parents[s] = node.createNode('transform', n=name(), p=jnt.parent())
            parents[s].fitTo(jnt)
            p = parents[s].addMessageAttr('sourceJoint')
            jnt.attr('m') >> p

        self.__eye_joints = parents

        for hl, data in self.highlights.items():
            with node.editFreezedShape(hl) as fhl:
                bb = cmds.polyEvaluate(fhl(), b=True)
                sizes = [x-n for n, x in bb ]
                center = [(x+n)*0.5 for n, x in bb]
            data['size'] = max(sizes)
            data['center'] = center
            name = func.Name(hl)
            name.setNodeType('jnt')
            jnt = node.createNode(
                'joint', n=name(), p=parents[name.position()]
            )
            jnt.setPosition(data['center'])
            jnt.setRadius(data['size']*0.3)
            jnt('ssc', 0)
            data['joint'] = jnt

            # 末端ジョイントを作成する。
            name.setSuffix('End')
            end_jnt = node.createNode('joint', n=name(), p=jnt)
            end_jnt.setPosition(
                [x+y for x, y in zip(data['center'], (0, 0, data['size']))]
            )
            end_jnt.setRadius(data['size']*0.15)
            om.execute(jnt)
            parent_list[jnt] = [hl]
        return parent_list

    def createControllers(self):
        if not self.isValid or not self.highlights:
            return
        cst = self.constructor
        sc = cst.shapeCreator()
        sc.setCurveType('box')

        ctrl_grps = {}
        positions = list(self.__eye_joints.keys())
        positions.sort()
        
        ctrl_parent = node.createNode(
            'transform', n='eyeHighlight_ctrlRoot', p=self.parent_ctrl_name
        )
        ctrl_parent.fitTo(self.__eye_joints[positions[0]].parent())
        ctrl_parent.lockTransform()

        for s in positions:
            jnt = self.__eye_joints[s]
            src = jnt.attr('sourceJoint').source()
            grp = node.createNode(
                'transform', n='eyeHighLightCtrl_grp'*s, p=ctrl_parent
            )
            decmtx = node.createUtil(
                'decomposeMatrix', n='eyeHighLightCtrl_decmtx'*s
            )
            src.attr('matrix') >> decmtx/'inputMatrix'
            for attr in ('t', 'r', 's', 'sh'):
                ~decmtx.attr('o'+attr) >> ~grp.attr(attr)
            for attr in 'trs':
                ~grp.attr(attr) >> ~jnt.attr(attr)

            # 表示アトリビュートの追加。---------------------------------------
            # -----------------------------------------------------------------
            main_ctrl = node.asObject('eyeBallEyeAim_ctrl'*s)
            p = main_ctrl.addDisplayAttr(
                'highlight', default=False, cb=True, k=False
            )
            p >> grp/'v'
            # -----------------------------------------------------------------
            
            # 眼への追従を制御するアトリビュートの追加。-----------------------
            p = main_ctrl.addFloatAttr('followHighlight', default=1)
            func.blendSelfConnection(grp, p, blendMode=1)
            grp.lockTransform()
            ctrl_grps[s] = grp
            # -----------------------------------------------------------------

        for hl, data in self.highlights.items():
            jnt = data['joint']
            n = func.Name(jnt)
            pos = n.position()
            sc.setColorIndex(self.ColorData[pos])
            sc.setSize(data['size'])
            cst.toController(jnt, 'eyeHighlight')
            cst.connectController(jnt, ctrl_grps[pos], sc)
