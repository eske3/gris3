#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    標準的な人の足を作成するための機能を提供するモジュール。
    
    Dates:
        date:2017/02/01 1:27[Eske](eske3g@gmail.com)
        update:2025/07/17 20:01 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import string

from gris3.rigScripts import humanBaseLimbsRig
# reload(humanBaseLimbsRig)
from gris3.tools import jointEditor
from gris3 import rigScripts, func, node
cmds = func.cmds

Category = 'Basic Human'
BaseName = 'leg'

NAMERULEOBJ = humanBaseLimbsRig.BlockNameRule(
    'Leg', 'Foot', 'thigh', 'lowleg', 'foot'
)


class Option(humanBaseLimbsRig.Option):
    r"""
        作成時に表示するUI用のクラス。
    """
    BlockNameRule = NAMERULEOBJ


class JointCreator(humanBaseLimbsRig.JointCreator):
    r"""
        足のジョイント作成機能を提供するクラス。
    """
    BlockNameRule = NAMERULEOBJ
    def process(self):
        r"""
            ジョイント作成プロセスとしてコールされる。
        """
        namerule = self.BlockNameRule
        name = self.basenameObject()
        parent = self.parent()
        
        if self.position() == 'R':
            xFactor = -1
        else:
            xFactor = 1

        # ジョイントの作成。---------------------------------------------------
        # 太もも
        name.setName('thigh')
        thigh = func.node.createNode('joint', n=name(), p=parent)
        thigh.setPosition((xFactor * 9.7, 101.7, 1.3))

        # 下足
        name.setName('lowleg')
        lowleg = func.node.createNode('joint', n=name(), p=thigh)
        lowleg.setPosition((xFactor * 9.7, 55.1, 2.1))

        # 足首
        name.setName('foot')
        foot = func.node.createNode('joint', n=name(), p=lowleg)
        foot.setPosition((xFactor * 9.7, 12.0, -1.0))

        # 足首のエンドジョイント
        name.setName('footEnd')
        footEnd = node.createNode('joint', n=name(), p=foot)
        footEnd.setPosition((xFactor * 9.7, 1.1, -1.0))

        # つま先
        name.setName('toe')
        toe = func.node.createNode('joint', n=name(), p=foot)
        toe.setPosition((xFactor * 9.7, 4.4, 10.9))
        toe.setRadius(1.3)

        # つま先のエンドジョイント
        name.setName('toeEnd')
        toeEnd = func.node.createNode('joint', n=name(), p=toe)
        toeEnd.setPosition((xFactor * 9.7, 4.4, 17.2))
        # ---------------------------------------------------------------------

        # マーカーの作成。-----------------------------------------------------
        name.setNodeType('marker')
        name.setName('toe')
        toe_marker = func.createLocator(n=name(), p='world_trs')
        toe_marker.setPosition((xFactor * 9.7, 0, 22))
        
        name.setName('heel')
        heel_marker = func.createLocator(n=name(), p='world_trs')
        heel_marker.setPosition((xFactor * 9.7, 0, -6))
        # ---------------------------------------------------------------------

        # ジョイント軸の調整。.------------------------------------------------
        om = jointEditor.OrientationModifier()
        om.setSecondaryMode('vector')
        if xFactor < 0:
            om.setPrimaryAxis('-X')
            om.setTargetUpAxis('-Z')
        else:
            om.setPrimaryAxis('+X')
            om.setTargetUpAxis('+Z')
        om.execute((thigh, lowleg, foot, footEnd))
        
        om.setTargetUpAxis('-Y' if xFactor < 0 else '+Y')
        om.execute((toe, toeEnd))
        # ---------------------------------------------------------------------

        # Unit setting.--------------------------------------------------------
        unit = self.unit()
        unit.addMember(namerule.upblock, thigh)
        unit.addMember(namerule.lowblock, lowleg)
        unit.addMember(namerule.endblock, foot)
        unit.addMember('toe', toe)
        unit.addMember('toeEnd', toeEnd)
        unit.addMember('toeMarker', toe_marker)
        unit.addMember('heelMarker', heel_marker)
        # ---------------------------------------------------------------------
        
        self.asRoot(thigh)
        toe.select()


class RigCreator(humanBaseLimbsRig.RigCreator):
    r"""
        足のリグを作成するためのクラス。
    """
    BlockNameRule = NAMERULEOBJ
    def getXFactor(self, positonIndex):
        r"""
            左右で変化するX軸の値の係数を返す。
            
            Args:
                positonIndex (int):位置を表す数字
                
            Returns:
                int: 左側であれば1，右側であれば-1を返す。
        """
        return -1 if positonIndex != 3 else 1

    def customPreRigging(self):
        unit = self.unit()
        self.extrajoints = [unit.getMember('toe'), unit.getMember('toeEnd')]
        self.isConstrainingDmyIk = False

    def customRigging(self):
        unit = self.unit()
        unitname = self.unitName()
        basename = unitname.name()
        side = unit.positionIndex()
        anim_set = self.animSet()
        namerule = self.BlockNameRule

        x_factor = self.getXFactor(side)

        toe_jnt = self.extrajoints[0]
        toeend_jnt = self.extrajoints[1]
        toe_marker = unit.getMember('toeMarker')
        heel_marker = unit.getMember('heelMarker')

        # 四肢のパーツのベクトルを取得。=======================================
        toe_vector = func.Vector(toeend_jnt.position())
        foot_to_toe = toe_vector - self.endblock_vector
        # =====================================================================

        # コントローラとその代理ノードを作成する。=============================
        # ピボットの移動可能な回転コントローラ。
        toeroll_ik_ctrlspace = {}
        toeroll_ik_ctrl = {}
        sole_rev_space = {}

        # 踵の回転ノード。
        heel_rot_space = {}

        # 足の回転コントローラ。
        foot_rot_space = {}
        foot_rot_ctrl = {}

        step_ctrlspace = {}
        step_ctrl = {}
        toe_ik_ctrlspace = {}
        toe_ik_ctrl = {}

        for key in ['', 'Proxy']:
            # つま先の回転コントローラの作成。---------------------------------
            unitname.setName(basename + 'ToeRotation')
            unitname.setNodeType('ctrlSpace' + key)
            toeroll_ik_ctrlspace[key] = node.createNode(
                'transform', p=self.limbs_ik_ctrl[key], n=unitname()
            )
            toeroll_ik_ctrlspace[key].setPosition(toe_marker.position())

            unitname.setNodeType('ctrl' + key)
            toeroll_ik_ctrl[key] = node.createNode(
                'transform', p=toeroll_ik_ctrlspace[key], n=unitname()
            )
            func.lockTransform(
                [toeroll_ik_ctrlspace[key], toeroll_ik_ctrl[key]]
            )
            toeroll_ik_ctrl[key].editAttr(['t:a', 'r:a'], k=True, l=False)
            # -----------------------------------------------------------------

            # 足の底の移動相殺ノードの作成。-----------------------------------
            unitname.setName(basename + 'SoleRev')
            unitname.setNodeType('trs' + key)
            sole_rev_space[key] = node.createNode(
                'transform', p=toeroll_ik_ctrl[key], n=unitname()
            )
            sole_rev_space[key].lockTransform()
            sole_rev_space[key].editAttr(['t:a'], k=True, l=False)
            # -----------------------------------------------------------------

            # 踵の自動回転ノードの作成。---------------------------------------
            unitname.setName(basename + 'HeelRotation')
            heel_rot_space[key] = node.createNode(
                'transform', p=sole_rev_space[key], n=unitname()
            )
            heel_rot_space[key].setPosition(heel_marker.position())
            heel_rot_space[key].lockTransform()
            heel_rot_space[key].editAttr(['r:a'], k=True, l=False)
            # -----------------------------------------------------------------
            
            # 足の回転コントローラの作成。.------------------------------------
            unitname.setName(basename + 'Rot')
            unitname.setNodeType('ctrlSpace' + key)
            foot_rot_space[key] = node.createNode(
                'transform', n=unitname(), p=heel_rot_space[key]
            )
            foot_rot_space[key].fitTo(self.limbs_ik_ctrl[key])

            unitname.setNodeType('ctrl' + key)
            foot_rot_ctrl[key] = node.createNode(
                'transform', n=unitname(), p=foot_rot_space[key]
            )
            func.lockTransform([foot_rot_space[key], foot_rot_ctrl[key]])
            foot_rot_ctrl[key].editAttr(['r:a'], k=True, l=False)
            # -----------------------------------------------------------------

            # ステップ用のコントローラとその代理ノードの作成。-----------------
            unitname.setName(basename + 'Step')
            unitname.setNodeType('ctrlSpace' + key)
            step_ctrlspace[key] = node.createNode(
                'transform',  n=unitname(), p=foot_rot_ctrl[key]
            )
            step_ctrlspace[key].fitTo(toe_jnt)

            unitname.setNodeType('ctrl' + key)
            step_ctrl[key] = node.createNode(
                'transform', n=unitname(), p=step_ctrlspace[key]
            )
            func.lockTransform([step_ctrlspace[key], step_ctrl[key]])
            step_ctrl[key].editAttr(['ry'], k=True, l=False)
            # -----------------------------------------------------------------

            # つま先のコントローラとその代理ノードの作成。---------------------
            unitname.setName(basename + 'Toe')
            unitname.setNodeType('ctrlSpace' + key)
            toe_ik_ctrlspace[key] = node.createNode(
                'transform',  n=unitname(), p=foot_rot_ctrl[key]
            )
            toe_ik_ctrlspace[key].fitTo(toe_jnt)

            unitname.setNodeType('ctrl' + key)
            toe_ik_ctrl[key] = node.createNode(
                'transform', n=unitname(), p=toe_ik_ctrlspace[key]
            )
            func.lockTransform([toe_ik_ctrlspace[key], toe_ik_ctrl[key]])
            toe_ik_ctrl[key].editAttr(['r:a'], k=True, l=False)
            # -----------------------------------------------------------------
        # =====================================================================

        # 足の裏の移動相殺のセットアップ。-------------------------------------
        md = func.createUtil('multiplyDivide')
        ~toeroll_ik_ctrl['Proxy'].attr('t') >> ~md.attr('i1')
        md('i2', (-1, -1, -1))
        ~md.attr('o') >> ~sole_rev_space['Proxy'].attr('t')
        # ---------------------------------------------------------------------

        # 四肢のIKシステムのセットアップ。=====================================
        # コントローラから代理ノードへの接続を行う。---------------------------
        for couple in (
            toeroll_ik_ctrl, toe_ik_ctrl, step_ctrl, foot_rot_ctrl
        ):
            func.connectKeyableAttr(couple[''], couple['Proxy'])

        for couple in (
            sole_rev_space, heel_rot_space
        ):
            func.connectKeyableAttr(couple['Proxy'], couple[''])

        cndt = func.createUtil('condition')
        cndt('operation', 2)
        for attr in ('secondTerm', 'colorIfFalseR', 'colorIfTrueG'):
            cndt(attr, 0)
        step_ctrl[''].attr('ry') >> [
            cndt.attr(x) for x in (
                'firstTerm', 'colorIfTrueR', 'colorIfFalseG'
            )
        ]
        cndt.attr('outColorR') >> step_ctrl['Proxy'].attr('ry')
        cndt.attr('outColorG') >> heel_rot_space['Proxy'].attr('rx')
        # =====================================================================

        # 四肢のIKシステムのセットアップ。=====================================
        # コントローラから代理ノードへの接続を行う。---------------------------
        (
            ~self.limbs_ik_ctrl[''].attr('r')
            >> ~self.limbs_ik_ctrl['Proxy'].attr('r')
        )
        (
            self.limbs_ik_ctrl[''].attr('ro')
            >> self.limbs_ik_ctrl['Proxy'].attr('ro')
        )
        # =====================================================================

        # IKコントローラとそのシステムの作成。=================================
        # つま先のIKシステムのセットアップ。
        unitname.setNodeType('ik')
        unitname.setName(basename + 'Toe')
        toe_ik = cmds.ikHandle(n=unitname(),
            sj=self.extra_rigJnts[0]['ikJnt'],
            ee=self.extra_rigJnts[1]['ikJnt'],
            sol='ikSCsolver'
        )[0]
        toe_ik = cmds.parent(toe_ik, toe_ik_ctrl['Proxy'])[0]

        # アーチのIKシステムのセットアップ。
        unitname.setName(basename + 'Arch')
        arch_ik = cmds.ikHandle(n=unitname(),
            sj=self.endblock_rigJnt['ikJnt'],
            ee=self.extra_rigJnts[0]['ikJnt'], sol='ikRPsolver'
        )[0]
        arch_ik = cmds.parent(arch_ik, step_ctrl['Proxy'])[0]
        
        # ダミーIKの親替え。
        foot_rot_space['Proxy'].addChild(self.limbs_dmyik)
        
        self.limbs_ik_pos.unlockTransform()
        step_ctrl['Proxy'].addChild(self.limbs_ik_pos)
        self.limbs_ik_pos.lockTransform()
        # =====================================================================
        
        # IKのスケール用コントローラを作成する。===============================
        self.limbs_ik_ctrl[''].editAttr(['s:a'], l=False)
        self.limbs_ik_ctrl['Proxy'].editAttr(['s:a'], l=False)
        (
            ~self.limbs_ik_ctrl['Proxy'].attr('s')
            >> ~self.limbs_ik_ctrl[''].attr('s')
        )
        self.limbs_ik_ctrl[''].editAttr(['s:a'], k=False, l=True)

        (
            ~self.ik_scale_ctrls[-2].attr('s')
            >> ~self.limbs_ik_ctrl['Proxy'].attr('s')
        )
        # =====================================================================
        
        if self.isBending:
            # 結合ジョイントを代理ジョイントへ接続する。=======================
            # 足の結合ジョイントから代理ジョイントへの接続を行う。-------------
            unitname.setName(basename + 'FootProxy')
            unitname.setNodeType('ik')
            foot_ik = cmds.ikHandle(
                sj=self.endblock_proxy, ee=self.extrajoint_proxies[0],
                sol='ikRPsolver'
            )
            foot_ik = cmds.rename(
                cmds.parent(foot_ik[0], self.endblock_rigJnt['combJnt'])[0],
                unitname()
            )

            unitname.setNodeType('ikPv')
            ik_pv = func.createPoleVector([foot_ik])[0]
            cmds.rename(
                cmds.parent(ik_pv, self.endblock_rigJnt['combJnt'])[0],
                unitname()
            )
            (
                ~self.endblock_rigJnt['combJnt'].attr('s')
                >> ~self.endblock_proxy.attr('s')
            )
            # -----------------------------------------------------------------

            # つま先の結合ジョイントから代理ジョイントへの接続を行う。---------
            func.connectKeyableAttr(
                self.extra_rigJnts[0]['combJnt'], self.extrajoint_proxies[0]
            )
            # =================================================================
        else:
            # つま先の結合ジョイントからオリジナルジョイントへの接続を行う。
            func.connectKeyableAttr(
                self.extra_rigJnts[0]['combJnt'], self.extrajoints[0]
            )

        # 全てのコントローラにシェイプを追加する。=============================
        self.creator.setRotation()
        # 足裏の回転コントローラへシェイプ追加。
        size = foot_to_toe.length() * 0.1
        self.creator.setSize(size)
        self.creator.create('cross', toeroll_ik_ctrl[''])

        # 踏み込み用とつま先用のコントローラにシェイプ追加。
        size = foot_to_toe.length() * 0.5
        self.creator.setSize(size)
        self.creator.setColorIndex(self.colorIndex('sub'))
        shape = self.creator.create('circle', step_ctrl[''])

        size *= 0.8
        self.creator.setSize(size)
        shape = self.creator.create('circle', toe_ik_ctrl[''])

        # 足の回転用コントローラにシェイプ追加。
        size = foot_to_toe.length() * 0.45
        self.creator.setSize(size)
        self.creator.setColorIndex(self.colorIndex('sub'))
        shape = self.creator.create('sphere', foot_rot_ctrl[''])
        # =====================================================================

        # コントローラをanimセットに登録する。=================================
        anim_set.addChild(
            *(
                toeroll_ik_ctrl[''], step_ctrl[''],
                toe_ik_ctrl[''], foot_rot_ctrl[''],
            )
        )
        # =====================================================================

        self.limbs_ik_ctrl['']('world', 1)
        # 余分な末端jointの削除。
        cmds.delete(
            [self.extra_rigJnts[1][x] for x in ('fkJnt', 'combJnt')]
        )
