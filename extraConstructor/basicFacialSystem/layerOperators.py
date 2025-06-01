#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    aiToolsのマスターモデルと連動したフェイシャルセットアップを行うための
    ExtraConstructor。
    
    Dates:
        date:2017/02/25 13:10[Eske](eske3g@gmail.com)
        update:2025/06/01 22:19 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import re
from collections import OrderedDict
from ... import node, func
from . import layer
cmds = node.cmds

__all__ = [
    'BlendShape', 'JawOpenner', 'Tweaked'
]

from . import tweakData, bodyCombiner
class ColorData(object):
    L = (0.044, 0.011, 0.88)
    R = (0.973, 0.02, 0.115)
    C = (0.7, 0.873, 0.207)


class BlendShape(layer.LayerOperator):
    FacialTargetGroup = 'facial_grp'
    BlendShapeName = 'facial_bs'
    FacialCategoryPattern = '([a-zA-Z\d]+?)_([a-zA-Z\d]+?)_facialGrp(_[A-Z]$|$)'
    FacialCtrlRoot = 'facial_ctrlSpace'
    MouthUpName = 'mouth_up_facialGrp_C'
    MouthDownName = 'mouth_down_facialGrp_C'
    MouthSlideNameL = 'mouth_slide_facialGrp_L'
    MouthSlideNameR = 'mouth_slide_facialGrp_R'
    BrowUpName = 'brow_up_facialGrp'
    BrowDownName = 'brow_down_facialGrp'
    BrowSlideNameL = 'brow_slideL_facialGrp'
    BrowSlideNameR = 'brow_slideR_facialGrp'
    Categories = OrderedDict([
        ('eye', {'pos':'LR', 'shape':'facialEye'}),
        (
            'brow', {
                'pos':'LR', 'shape':'facialBrow',
                'special':[
                    BrowUpName, BrowDownName, BrowSlideNameL, BrowSlideNameR
                ]
            }
        ),
        ('nose', {'shape':'facialNose'}),
        (
            'mouth', {
                'shape':'facialMouth',
                'special':[
                    MouthUpName, MouthDownName,
                    MouthSlideNameL, MouthSlideNameR
                ]
            }
        ),
        ('extra', {'shape':'facialOther'}),
    ])

    def preSetup(self):
        cst = self.constructor()
        anim_set = self.animSet()
        tgt_objects = self.targetObjects()

        target_grp = node.asObject(self.FacialTargetGroup)
        if not target_grp:
            self.out(
                'No target group "%s" was not found.' % self.FacialTargetGroup
            )
            return
        target_grp = node.parent(target_grp, self.rootGroup())[0]
        categry_ptn = re.compile(self.FacialCategoryPattern)
        # facialTarget_grp内の直下のグループ名からカテゴリ分けを行う。 ========
        # Categoriesに該当しない命名規則のものが検出された場合はエラーを返す。
        datatable = {}
        failed_formats = []
        for child in target_grp.children():
            cat = categry_ptn.search(child())
            if not cat:
                failed_formats.append(child())
                continue

            category = (
                cat.group(1) if cat.group(1) in self.Categories else 'extra'
            )
            partlist =  []
            name = cat.group(2)
            if cat.group(3):
                pos = cat.group(3)[1:]
            else:
                pos = ''
            datatable.setdefault(category, []).append((name, pos, child))

        if failed_formats:
            # 不正な名前ルールのグループがあった場合は列挙した上で例外を出す。
            print('! Invalid target names.'.ljust(80, '!'))
            print(
                '!     Facial target name pattern -> {}'.format(
                    self.FacialCategoryPattern
                )
            )
            for ff in failed_formats:
                print('    {}'.format(ff))
            print('!'*80)
            raise RuntimeError(
                'These group name are invalid format name above.'
            )
        # =====================================================================

        # =====================================================================
        # ブレンドシェイプを作成する
        bs = node.blendShape(tgt_objects[0], n=self.BlendShapeName)[0]
        bs('ihi', 0)
        # =====================================================================

        index = 0
        specials = {}
        for cat, data in self.Categories.items():
            if cat not in datatable:
                continue
            # カテゴリ用に該当する名前のコントローラを探す。
            for position in data.get('pos', ['']):
                special_node_list = {}
                special_nodes = data.get('special', [])
                specials[cat+position] = {'nodelist':special_node_list}
                if position:
                    special_nodes = [x+'_'+position for x in special_nodes]
                ctrl_name = self.createCtrlName(cat, position)
                ctrl = node.asObject(ctrl_name)
                if not ctrl:
                    raise RuntimeError(
                        self.out(
                            'Facial controller for "%s" does not exist : %s' % (
                                cat, ctrl_name
                            )
                        )
                    )
                ctrl.lockTransform()
                specials[cat+position]['ctrl'] = ctrl

                partlist = datatable[cat]
                anim_set.addChild(ctrl)
                for name, pos, target in partlist:
                    if position and pos not in position:
                        continue
                    pos = '_'+pos if not position and pos in 'LR' else ''
                    cmds.blendShape(
                        bs, e=True, t=(tgt_objects[0], index, target, 1.0)
                    )
                    bs_attr = bs.attr('weight[{}]'.format(index))
                    if target in special_nodes:
                        special_node_list[target] = bs_attr
                    else:
                        plug = ctrl.addFloatAttr(
                            name+pos, min=-2, max=3, smn=0, smx=1, default=0
                        )
                        plug >> bs_attr
                    index += 1

        # 口・眉用の特殊処理。=================================================
        for key, limitlist in [
            ('mouth', (0.1, -0.1, 0.25, -0.25)),
            ('brow', (0.25, -0.25, 0.1, -0.1))
        ]:
            for position in self.Categories[key].get('pos', ['']):
                p_key = key + position
                nodelist = specials[p_key].get('nodelist')
                if not nodelist:
                    continue

                ctrl = specials[p_key]['ctrl']
                limits = {}
                for name, attr, limit in zip(
                    self.Categories[key]['special'],
                    ('ty', 'ty', 'tx', 'tx'),
                    limitlist
                ):
                    if position:
                        name += '_' + position
                    bs_attr = nodelist.get(name)
                    if not bs_attr:
                        continue
                    ctrl.editAttr([attr], k=True, l=False)
                    for v, dv in enumerate((0, limit)):
                        cmds.setDrivenKeyframe(
                            bs_attr(), currentDriver=ctrl/attr, v=v, dv=dv,
                            ott='linear', itt='linear'
                        )
                    limits.setdefault(attr, []).append(limit)
                
                indices = {'x':0, 'y':1, 'z':2}
                at_lim_list = {
                    't':([0, 0, 0], [0, 0, 0]),
                    'r':([0, 0, 0], [0, 0, 0]),
                    's':([0, 0, 0], [0, 0, 0]),
                }
                for attr, values in limits.items():
                    at, ax = attr
                    min_val = min(values)
                    max_val = max(values)
                    for val, f, pfx, vlist in zip(
                        (min_val, max_val),
                        (lambda x: x < 0, lambda x: x > 0),
                        ('m', 'x'),
                        at_lim_list[at],
                    ):
                        if not f(val):
                            continue
                        ctrl('{}{}{}e'.format(pfx, at, ax), 1)
                        vlist[indices[ax]] = val
                for at, val_list in at_lim_list.items():
                    ctrl('mn{}l'.format(at), val_list[0])
                    ctrl('mx{}l'.format(at), val_list[1])
        # =====================================================================

    def prefix(self):
        return 'blended'

    def createCtrlName(self, cat, pos):
        r"""
            Args:
                cat (str):
                pos (str):
        """
        n = func.Name()
        n.setName('facial')
        n.setSuffix(cat[0].upper()+cat[1:])
        n.setNodeType('ctrl')
        n.setPosition(pos if pos else 'None')
        return n()

    def postProcess(self):
        if not cmds.objExists(self.FacialCtrlRoot):
            return
        cst = self.constructor()
        ctrl = node.parent(self.FacialCtrlRoot, self.parentCtrl())[0]
        ctrl.lockTransform()
        self.addHiddenCtrl(ctrl)

    def createSetupParts(self, parentGrp):
        r"""
            Args:
                parentGrp (gris3.node.Transform):
        """
        sc = self.constructor().shapeCreator()
        ctrl_space = node.createNode(
            'transform', n=self.FacialCtrlRoot, p=parentGrp
        )
        for cat, data in self.Categories.items():
            shape = data.get('shape', 'facialOther')
            for pos in data.get('pos', ['']):
                ctrl_name = self.createCtrlName(cat, pos)
                ctrl = node.createNode('transform', n=ctrl_name, p=ctrl_space)
                ctrl.lockTransform()
                sc.setColorIndex(ColorData.get(pos, ColorData['C']))
                sc.create(shape+pos, parentNode=ctrl)


class JawOpenner(layer.LayerOperator):
    def prefix(self):
        return 'jaw'

    def createSetupParts(self, parentGrp):
        r"""
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
        ctrl_root = self.parentCtrl()
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


class Tweaked(layer.LayerOperator):
    JointData = tweakData.TweakJointData
    StackFaceName = {
        'face':None, 'faceParts':('facialBrowJnt_grp',),
        'tongue':('facialInnerMouthJnt_grp',),
    }
    def prefix(self):
        return 'tweek'

    def createSetupParts(self, parentGrp):
        r"""
            Args:
                parentGrp (gris3.node.Transform):
        """
        def createJoint(data, parent):
            r"""
                Args:
                    data (dict):
                    parent (str): 親ノード
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
            'transform', n='facialTweakJnt_grp', p=parentGrp
        )
        root_grp.lockTransform()
        for grp_name, joint_data in self.JointData.items():
            grp = node.createNode('transform', n=grp_name, p=root_grp)
            grp.lockTransform()
            createJoint(joint_data, grp)

    def preSetup(self):
        cst = self.constructor()
        anim_set = self.animSet()
        tweak_grp = node.asObject('facialTweakJnt_grp')
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
        self.jointlist = []
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
            self.jointlist.extend(f.fit(joints))

    def setup(self):
        if not hasattr(self, 'jointlist'):
            return
        if not self.jointlist:
            return

        cst = self.constructor()
        sc = cst.shapeCreator()
        sc.setColorIndex((0.476, 0.097, 1.0))

        # コントローラの作成。
        ctrl_root = self.parentCtrl()
        ctrl_grp = node.createNode(
            'transform', n='facialTweakCtrl_grp', p=ctrl_root
        )
        ctrl_grp.lockTransform()
        anim_set = cst.createAnimSet('facialTweak')
        for jnt, spacer in self.jointlist:
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
            'facialTweakCtrlVis', default=False, cb=True, k=False
        )
        plug >> ctrl_grp/'v'

    def postProcess(self):
        index_ptn = re.compile('\[(\d+)\]')
        def setBindPrematrix(jnt, parent_mtx_plug):
            r"""
                Args:
                    jnt (any):
                    parent_mtx_plug (any):
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


def listAllLayerOperators():
    r"""
        このモジュールの全てのLayerOperatorを返す。

        Returns:
            list(layer.LayerOperator):
    """
    return [JawOpenner, BlendShape, Tweaked]

