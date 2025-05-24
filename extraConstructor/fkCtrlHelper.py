#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    FKコントローラの作成を補助するヘルパーモジュール。
    親子付けやFKコントローラの作成を自動で行う。
    
    Dates:
        date:2022/04/22 16:40 eske yoshinob[eske3g@gmail.com]
        update:2022/04/22 17:13 noriyoshi tsujimoto[tensoftware@hotmail.co.jp]
        
    License:
        Copyright 2022 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import extraConstructor, node, func
cmds = node.cmds


class ExtraConstructor(extraConstructor.ExtraConstructor):
    ConstGroupName = 'ctrlCst_grp'
    def __init__(self, const):
        r"""
            Args:
                const (constructors.Constructor):
        """
        super(ExtraConstructor, self).__init__(const)
        const.setJointAsFkController = self.setJointAsFkController
        self.fk_members = {}

    def setJointAsFkController(
        self, joints, parent, setName, side=None,
        shapeCreator=None, ctrlArgs=None, connectArgs=None,
        expandChildren=False
    ):
        r"""
            Args:
                joints (str or list or tuple):FK化するジョイントのリスト
                parent (str):親ノード名
                setName (str):コントローラのセット名
                side (str):コントローラの方向を表す文字列
                ctrlArgs (dict):toControllerメソッドに渡す引数
                connectArgs (dict):connectControllerメソッドに渡す引数
                expandChildren (bool):引数jointsで指定したグループの子を使用するかどうか
        """
        members = self.fk_members.setdefault(parent, [])
        joints = joints if isinstance(joints, (list, tuple)) else [joints]
        if expandChildren:
            joint_members = []
            for jnt in joints:
                joint_members.extend(node.asObject(jnt).children())
        else:
            joint_members = joints

        members.append(
            {
                'joints':joint_members, 'setName':setName, 'side':side,
                'sc':shapeCreator,
                'ctrlArgs':ctrlArgs, 'connectArgs':connectArgs
            }
        )

    def _preSetup(self):
        for parent, members in self.fk_members.items():
            for info in members:
                info['joints'] = node.parent(info['joints'], parent)

    def _setup(self):
        cst = self.constructor()
        default_sc = cst.shapeCreator()
        for parent, members in self.fk_members.items():
            base_name = func.Name(parent)
            ctrl_root = cst.createCtrlRoot(
                base_name.name(), base_name.position(), parent
            )
            for info in members:
                ctrl_args = info['ctrlArgs'] if info['ctrlArgs'] else {}
                con_args = info['connectArgs'] if info['connectArgs'] else {}
                sc = info['sc'] if info['sc'] else default_sc
                side = info['side'] if info['side'] else 'None'
                for jnt in info['joints']:
                    cst.toController(
                        jnt, info['setName'], side, **ctrl_args
                    )
                    cst.connectController(
                        jnt, ctrl_root, sc, **con_args
                    )
