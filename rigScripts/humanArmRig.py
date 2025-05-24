# -*- coding:utf-8 -*-
r'''
    @file     unityArmRig.py
    @brief    UNITY用の腕を作成するための機能を提供するモジュール。
    @class    Option : 作成時に表示するUI用のクラス。
    @class    JointCreator : 腕のジョイント作成機能を提供するクラス。
    @class    RigCreator : 腕のコントローラを作成する機能を提供するクラス。
    @date        2017/02/01 1:01[Eske](eske3g@gmail.com)
    @update      2017/02/07 23:56[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
import string

from gris3.rigScripts import humanBaseLimbsRig
from gris3.tools import jointEditor
from gris3 import rigScripts, func, node
cmds = func.cmds
Category = 'Basic Human'
BaseName = 'arm'

class Option(humanBaseLimbsRig.Option):
    r'''
        @brief       作成時に表示するUI用のクラス。
        @inheritance humanBaseLimbsRig.Option
        @date        2017/02/04 18:52[Eske](eske3g@gmail.com)
        @update      2017/02/07 23:56[Eske](eske3g@gmail.com)
    '''
    pass

class JointCreator(humanBaseLimbsRig.JointCreator):
    r'''
        @brief       腕のジョイント作成機能を提供するクラス。
        @inheritance humanBaseLimbsRig.JointCreator
        @date        2017/02/01 1:01[Eske](eske3g@gmail.com)
        @update      2017/02/07 23:56[Eske](eske3g@gmail.com)
    '''
    def process(self):
        r'''
            @brief  ジョイント作成プロセスとしてコールされる。
            @return None
        '''
        namerule = self.BlockNameRule
        name = self.basenameObject()
        parent = self.parent()

        if self.position() == 'R':
            x_factor = -1
        else:
            x_factor = 1

        # Uparm.
        name.setName('uparm')
        uparm = node.createNode('joint', n=name(), p=parent)
        uparm.setPosition((x_factor * 18.2, 151.4, -4.7))
        uparm.setRadius(1.4)

        # Lowarm.
        name.setName('lowarm')
        lowarm = node.createNode('joint', n=name(), p=uparm)
        lowarm.setPosition((x_factor * 38.4, 132.1, -4.2))

        # Hand.
        name.setName('hand')
        hand = node.createNode('joint', n=name(), p=lowarm)
        hand.setPosition((x_factor * 57.4, 113.9, -1.7))
        hand.setRadius(0.5)

        # Hand end.
        name.setName('handEnd')
        handEnd = node.createNode('joint', n=name(), p=hand)
        handEnd.setPosition((x_factor * 78.9, 93.2, 1.3))

        # Fix orientation.-----------------------------------------------------
        om = jointEditor.OrientationModifier()
        om.setSecondaryMode('vector')
        om.setApplyToChildren(False)
        if x_factor < 0:
            om.setPrimaryAxis('-X')
            om.setTargetUpAxis('+Z')
        else:
            om.setPrimaryAxis('+X')
            om.setTargetUpAxis('-Z')
        om.execute((uparm, lowarm, hand, handEnd))
        # ---------------------------------------------------------------------

        # Unit setting.--------------------------------------------------------
        unit = self.unit()
        unit.addMember(namerule.upblock, uparm)
        unit.addMember(namerule.lowblock, lowarm)
        unit.addMember(namerule.endblock, hand)
        unit.addMember('handEnd', handEnd)
        # ---------------------------------------------------------------------
        
        self.asRoot(uparm)
        hand.select()


class RigCreator(humanBaseLimbsRig.RigCreator):
    r'''
        @brief       腕のコントローラを作成する機能を提供するクラス。
        @inheritance humanBaseLimbsRig.RigCreator
        @date        2017/02/01 1:01[Eske](eske3g@gmail.com)
        @update      2017/02/07 23:56[Eske](eske3g@gmail.com)
    '''
    AimZFactor = -1
    def customRigging(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        unit = self.unit()
        unitname = self.unitName()
        basename = unitname.name()
        side = unit.positionIndex()
        namerule = self.BlockNameRule

        handend_jnt = unit.getMember('handEnd')

        # 手首用のジョイントを作成する。=======================================
        unitname.setName(basename + 'HandRot')
        unitname.setNodeType('ikJnt')
        endblockrot_rigJnt = {
            'ikJnt':func.copyNode(
                self.endblock_jnt, 'testProxy', self.lowblock_rigJnt['ikJnt']
            )
        }
        endblockrot_rigJnt['ikJnt'] = node.rename(
            endblockrot_rigJnt['ikJnt'], unitname()
        )
        
        unitname.setName(basename + 'HandIkRot')
        endblockIkRot_rigJnt = {
            'ikJnt':func.copyNode(
                self.endblock_jnt, 'testProxy', self.lowblock_rigJnt['ikJnt']
            )
        }
        endblockIkRot_rigJnt['ikJnt'] = node.rename(
            endblockIkRot_rigJnt['ikJnt'], unitname()
        )

        unitname.setName(basename + 'HandIkRotEnd')
        endblockIkRotEnd_rigJnt = {
            'ikJnt':func.copyNode(
                handend_jnt, 'testProxy', endblockIkRot_rigJnt['ikJnt']
            )
        }
        endblockIkRotEnd_rigJnt['ikJnt'] = node.rename(
            endblockIkRotEnd_rigJnt['ikJnt'], unitname()
        )
        # =====================================================================

        # 手首用の代理ジョイントを作成する。===================================
        if self.isBending:
            handend_proxy = func.copyNode(
                handend_jnt, 'jntProxy', self.endblock_proxy
            )
        # =====================================================================

        # コントローラとその代理ノードを作成する。=============================
        follow_attr = self.limbs_ik_ctrl[''].addFloatAttr(
            'followHand', default=1
        )

        # 手首の回転コントローラの作成。---------------------------------------
        endblockrot_ik_ctrlspace = {}
        endblockrot_ik_ctrl = {}

        unitname.setName(basename + 'HandRot')
        unitname.setNodeType('ctrlSpace')
        endblockrot_ik_ctrlspace[''] = node.createNode(
            'transform', p=self.ctrl_parent_proxy, n=unitname()
        )
        decmtx, mltmtx = func.createDecomposeMatrix(
            endblockrot_ik_ctrlspace[''],
            [
                '%s.matrix' % x['ikJnt']
                for x in [
                    self.endblock_rigJnt, self.lowblock_rigJnt,
                    self.upblock_rigJnt
                ]
            ]
        )
        func.setAttrFromConnected('%s.matrixIn[0]' % mltmtx)

        unitname.setNodeType('ctrl')
        endblockrot_ik_ctrl[''] = node.createNode(
            'transform', p=endblockrot_ik_ctrlspace[''], n=unitname()
        )
        func.lockTransform(
            [endblockrot_ik_ctrlspace[''], endblockrot_ik_ctrl['']]
        )
        endblockrot_ik_ctrl[''].editAttr(['r:a', 'ro'], k=True, l=False)
        
        (
            ~endblockrot_ik_ctrl[''].attr('r')
            >> ~endblockrot_rigJnt['ikJnt'].attr('r')
        )
        (
            endblockrot_ik_ctrl[''].attr('ro')
            >> endblockrot_rigJnt['ikJnt'].attr('ro')
        )
        # ---------------------------------------------------------------------
        # =====================================================================

        # 四肢のIKシステムのセットアップ。=====================================
        # 手首回転用のノードを作成し、四肢のIKコントローラから接続する。
        unitname.setName(basename + 'HandRot')
        unitname.setNodeType('rotProxy')
        endblock_ikrot_ctrlproxy = node.createNode(
                'transform', n=unitname(), p=self.limbs_ik_ctrl['Proxy']
        )
        (
            ~self.limbs_ik_ctrl[''].attr('r')
            >> ~endblock_ikrot_ctrlproxy.attr('r')
        )
        (
            self.limbs_ik_ctrl[''].attr('ro')
            >> endblock_ikrot_ctrlproxy.attr('ro')
        )
        endblock_ikrot_ctrlproxy.lockTransform()
        # =====================================================================

        # IKコントローラとそのシステムの作成。=================================
        # 手首の回転ジョイントを混ぜ合わせTえIKリグジョイントに接続する。
        func.blendTransform(
            endblockrot_rigJnt['ikJnt'], endblockIkRot_rigJnt['ikJnt'],
            self.endblock_rigJnt['ikJnt'],
            '%s.followHand' % self.limbs_ik_ctrl[''],
            skipScale=True
        )

        # 手首用のIKを作成する。
        unitname.setName(basename + namerule.endpartname)
        endblock_ik = cmds.ikHandle(n=unitname(),
            sj=endblockIkRot_rigJnt['ikJnt'],
            ee=endblockIkRotEnd_rigJnt['ikJnt'],
            sol='ikRPsolver'
        )[0]
        endblock_ik = func.asObject(
            cmds.parent(endblock_ik, endblock_ikrot_ctrlproxy)[0]
        )
        # =====================================================================

        # 結合ジョイントを代理ジョイントへ接続する。===========================
        if self.isBending:
            # 末端ジョイントの結合ジョイントから代理ジョイントへの接続。-------
            unitname.setName(basename + namerule.endpartname + 'Proxy')
            unitname.setNodeType('ik')
            endblock_ik = cmds.ikHandle(
                sj=self.endblock_proxy, ee=handend_proxy, sol='ikRPsolver'
            )
            endblock_ik = func.asObject(
                cmds.rename(
                    cmds.parent(endblock_ik[0],
                    self.endblock_rigJnt['combJnt'])[0],
                    unitname()
                )
            )

            unitname.setNodeType('ikPv')
            ik_pv = func.createPoleVector([endblock_ik])[0]
            cmds.rename(
                cmds.parent(ik_pv, self.endblock_rigJnt['combJnt'])[0],
                unitname()
            )
            (
                ~self.endblock_rigJnt['combJnt'].attr('s')
                >> ~self.endblock_proxy.attr('s')
            )
            # -----------------------------------------------------------------
        # =====================================================================
        
        # 全てのコントローラにシェイプを追加する。=============================
        # 末端コントローラへのシェイプ追加。
        size = self.limbs_vector.length() * 0.25
        self.creator.setSize(size)
        self.creator.setColorIndex(self.colorIndex('special'))
        self.creator.create('sphere', endblockrot_ik_ctrl[''])
        # =====================================================================

        # 後処理。=============================================================
        follow_attr >> self.vis_rev_node/'inputY'
        (
            self.vis_rev_node.attr('outputY')
            >> endblockrot_ik_ctrlspace['']/'v'
        )

        self.animSet().addChild(endblockrot_ik_ctrl[''])
        # =====================================================================
