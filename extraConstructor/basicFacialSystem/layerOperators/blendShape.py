#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ブレンドシェイプによるフェイシャル用制御レイヤを提供するLayerOperator。
    
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
from .... import node, func
from .. import layer
cmds = node.cmds


class BlendShape(layer.LayerOperator):
    r"""
        ブレンドシェイプによるフェイシャル用制御レイヤを提供するクラス。
    """
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
                if not p_key in specials:
                    print('  ! Skip special process for {}'.format(p_key))
                    continue
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
        ctrl = node.parent(self.FacialCtrlRoot, self.ctrlParent())[0]
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
                sc.setColorIndex(
                    layer.ColorData.get(pos, layer.ColorData['C'])
                )
                sc.create(shape+pos, parentNode=ctrl)

