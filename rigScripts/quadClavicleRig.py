#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    四足歩行動物用の鎖骨リグ機能を提供するモジュール。

    Dates:
        date:2020/11/16 00:48 eske yoshinob[eske3g@gmail.com]
        update:2020/11/16 00:48 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2020 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3.tools import jointEditor
from gris3 import rigScripts, func, node
cmds = func.cmds

Category = 'Quads'

class JointCreator(rigScripts.JointCreator):
    def process(self):
        name = self.basenameObject()
        parent = self.parent()
        
        if self.position() == 'R':
            xFactor = -1
        else:
            xFactor = 1

        # Base Clavicle.
        name.setName('clavicleBase')
        clavicle_base = node.createNode('joint', n=name(), p=parent)
        clavicle_base.setPosition((xFactor * 5, 86, 31))
        clavicle_base.setRadius(1)
        
        name.setName('clavicle')
        clavicle = node.createNode('joint', n=name(), p=clavicle_base)
        clavicle.setPosition((xFactor * 27, 93, 26))
        clavicle.setRadius(1)
        
        func.controlChannels(
            (clavicle_base, clavicle), ['v'], k=False, l=False
        )

        # Uparm proxy.
        name.setName('uparm')
        uparm = node.createNode('joint', n=name(), p=clavicle)
        uparm.setPosition((xFactor * 31, 75, 33))
        uparm.setRadius(1.4)

        # Fix orientation.-----------------------------------------------------
        om = jointEditor.OrientationModifier()
        om.setSecondaryMode('vector')
        if xFactor < 0:
            om.setPrimaryAxis('-X')
            om.setTargetUpAxis('-Z')
        else:
            om.setPrimaryAxis('+X')
            om.setTargetUpAxis('+Z')
        om.execute([clavicle_base, clavicle, uparm])
        # ---------------------------------------------------------------------

        # Unit setting.--------------------------------------------------------
        unit = self.unit()
        unit.addMember('clavicleBase', clavicle_base)
        unit.addMember('clavicle', clavicle)
        cmds.delete(uparm)
        # ---------------------------------------------------------------------
        
        self.asRoot(clavicle_base)
        clavicle.select()

    def finalize(self):
        pass


class RigCreator(rigScripts.RigCreator):
    def process(self):
        unit = self.unit()
        unitname = func.Name(self.unitName())
        basename = unitname.name()
        side = unit.position()
        anim_set = self.animSet()

        if side == 'R':
            xFactor = -1
            rotFactor = 180
        else:
            xFactor = 1
            rotFactor = 0

        claviclebase_jnt = unit.getMember('clavicleBase')
        clavicle_jnt = unit.getMember('clavicle')

        # ルートノードを作成する。=============================================
        # リグの親代理ノードを作成する。
        parent_proxy = self.createRigParentProxy(
            claviclebase_jnt, name=basename
        )
        
        # コントローラの親代理ノードを作成する。
        ctrl_parent_proxy = self.createCtrlParentProxy(
            claviclebase_jnt, basename
        )

        parent_matrix = self.createParentMatrixNode(claviclebase_jnt.parent())
        decmtx = func.createDecomposeMatrix(
            ctrl_parent_proxy, ['%s.matrixSum' % parent_matrix],
            withMultMatrix=False
        )
        self.addLockedList(ctrl_parent_proxy)
        # =====================================================================
        
        # IKシステムにセットするための代理ジョイントを元からコピーする。=======
        ik_rig_joints = []
        parent = parent_proxy
        for jnt in [claviclebase_jnt, clavicle_jnt]:
            parent = func.copyNode(jnt, 'ikJnt', parent)
            ik_rig_joints.append(parent)

        end_jnts = clavicle_jnt.children()
        if end_jnts:
            unitname.setName(basename + 'IkEnd')
            unitname.setNodeType('ikJnt')
            ik_rig_joints.append(
                node.rename(
                    func.copyNode(end_jnts[0], 'ikJnt', parent), unitname()
                )
            )
        # =====================================================================

        # それぞれのジョイントの長さを求める。=================================
        vectors = [func.Vector(x.rotatePivot()) for x in ik_rig_joints]
        start_to_end = vectors[-1] - vectors[0]

        if len(vectors) > 2:
            # このユニットのジョイント下にさらに小ジョイントがいる場合は、出来る
            # 三角形の頂点方向を向くベクトルを算出する。
            a = vectors[0] - vectors[1]
            b = vectors[2] - vectors[1]
            pedal_vector = vectors[1] - (a | b) * 1.5
        else:
            # 小ジョイントがない場合は根本のジョイントのY軸を向くベクトルを返す。
            mtx = func.FMatrix(claviclebase_jnt.matrix())
            pedal_vector = (
                func.Vector(mtx.columns()[1][:3]) *
                xFactor *
                start_to_end.length()
            )
        # =====================================================================

        # コントローラとその代理ノードを作成する。=============================
        ctrls, aim_ctrls = {}, {}
        for key, parent in zip(
            ('', 'Proxy'), (ctrl_parent_proxy, parent_proxy)
        ):
            unitname.setName(basename)
            unitname.setNodeType('ctrlSpace' + key)
            space = node.createNode('transform', n=unitname())
            space.fitTo(ik_rig_joints[-1], 0b1000)
            space = node.parent(space, parent)[0]
            self.addLockedList(space)

            unitname.setNodeType('ctrl' + key)
            ctrl = node.createNode('transform', n=unitname(), p=space)
            ctrl.lockTransform()
            ctrl.editAttr(['t:a'], k=True, l=False)
            ctrls[key] = ctrl
            
            unitname.setName(basename + 'Aim' + key)
            unitname.setNodeType('ctrlSpace' + key)
            space = node.createNode('transform', n=unitname(), p=ctrl)
            space.setPosition(
                (pedal_vector[0], pedal_vector[1], pedal_vector[2])
            )

            unitname.setNodeType('ctrl' + key)
            ctrl = node.createNode('transform', n=unitname(), p=space)
            ctrl.lockTransform()
            ctrl.editAttr(['t:a'], k=True, l=False)
            aim_ctrls[key] = ctrl
            self.addLockedList(space)
        # =====================================================================

        # IKシステムをセットアップする。=======================================
        unitname.setNodeType('ik')
        clavicle_ik = cmds.ikHandle(
            n=unitname(), sj=ik_rig_joints[0], ee=ik_rig_joints[-1],
            sol='ikRPsolver'
        )
        clavicle_ik = node.parent(clavicle_ik[0], ctrls['Proxy'])[0]
        aim_cst = cmds.poleVectorConstraint(aim_ctrls['Proxy'], clavicle_ik)
        # =====================================================================

        # 代理ジョイントから元ジョイントへ接続する。===========================
        for proxy, jnt in zip(ik_rig_joints, (claviclebase_jnt, clavicle_jnt)):
            func.connectKeyableAttr(proxy, jnt)
        func.connectKeyableAttr(ctrls[''], ctrls['Proxy'])
        func.connectKeyableAttr(aim_ctrls[''] , aim_ctrls['Proxy'])
        # =====================================================================

        # /////////////////////////////////////////////////////////////////////
        # 全てのコントローラにシェイプを追加する。                           //
        # /////////////////////////////////////////////////////////////////////
        creator = func.PrimitiveCreator()
        creator.setSize(start_to_end.length() * 0.1)
        creator.setColorIndex(self.colorIndex('main'))
        creator.setCurveType('pyramid')
        creator.create(parentNode=ctrls[''])

        creator.setSize(start_to_end.length() * 0.1)
        creator.setCurveType('box')
        creator.create(parentNode=aim_ctrls[''])
        # ---------------------------------------------------------------------
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////

        # /////////////////////////////////////////////////////////////////////
        # 後処理。                                                           //
        # /////////////////////////////////////////////////////////////////////
        # コントローラをアニムセットに追加する。===============================
        anim_set.addChild(ctrls[''])
        anim_set.addChild(aim_ctrls[''])
        # =====================================================================
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////