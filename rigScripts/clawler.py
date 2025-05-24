#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    クローラ（キャタピラ）を実現するリグモジュール。
    
    Dates:
        date:2017/02/01 1:01[Eske](eske3g@gmail.com)
        update:2022/09/27 23:58 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import string

from .. import rigScripts, func, node, verutil
from ..tools import jointEditor
cmds = func.cmds

Category = 'Vehicle'
BaseName = 'clawler'


class JointCreator(rigScripts.JointCreator):
    r"""
        腕のジョイント作成機能を提供するクラス。
        
        Inheritance:
            rigScripts:.JointCreator
    """
    def createUnit(self):
        r"""
            ユニット作成のオーバーライド。
        """
        super(JointCreator, self).createUnit()
        unit = self.unit()
        unit.addMessageAttr('baseCurve')
        unit.addMessageAttr('upCurve')

    def process(self):
        r"""
            ジョイント作成プロセスとしてコールされる。
        """
        unit = self.unit()
        name = self.basenameObject()
        parent = self.parent()

        # ルートを作成.
        name.setName('clawler')
        base = node.createNode('transform', n=name(), p=parent)

        # Unit setting.--------------------------------------------------------
        unit = self.unit()
        unit.addMember('rootGroup', base)
        # ---------------------------------------------------------------------

        self.asRoot(base)
        base.select()

class RigCreator(rigScripts.RigCreator):
    def process(self):
        r"""
            実処理部分。
        """
        def createMotionPath(joint, curve, upCurve=None):
            m_path = node.createUtil('motionPath')
            m_path('fractionMode', True)
            m_path('frontAxis', 0)
            m_path('upAxis', 2)
            curve.attr('local') >> m_path/'geometryPath'
            ~m_path.attr('allCoordinates') >> ~joint.attr('t')
            ~m_path.attr('rotate') >> ~joint.attr('r')
            m_path.attr('rotateOrder') >> joint.attr('ro')
            
            if not upCurve:
                m_path('worldUpType', 4)
                return
            m_path('worldUpType', 1)
            u_path = node.createUtil('motionPath')
            u_path('fractionMode', True)
            m_path.attr('uValue') >> u_path/'uValue'
            upCurve.attr('local') >> u_path/'geometryPath'
            u_mtx = node.createUtil('fourByFourMatrix')
            ~u_path.attr('allCoordinates') >> [
                '{}.in3{}'.format(u_mtx, x) for x in range(3)
            ]
            u_mtx.attr('output') >> m_path/'worldUpMatrix'

        unit = self.unit()
        unitname = self.unitName()
        basename = unitname.name()
        side = unit.positionIndex()
        anim_set = self.animSet()

        group = unit.getMember('rootGroup')
        base_crv = unit.getMember('baseCurve')
        up_crv = unit.getMember('upCurve')
        
        target_joints = group.children(type='transform')
        if not base_crv:
            poslist = [x.position() for x in target_joints]
            crv = node.asObject(cmds.curve(d=1, p=poslist))

        rig_root = self.createRigParentProxy(group, basename)
        rig_root.fitTo(group)
        base_crv = node.parent(base_crv, rig_root)[0]
        up_crv = node.parent(up_crv, rig_root)[0]
        
        for jnt in target_joints:
            proxy = func.copyNode(jnt, 'jntProxy', rig_root)
            createMotionPath(proxy, base_crv, up_crv)
        
        return
        startend_vec = (
            func.Vector(end.position()) - func.Vector(base.position())
        )
        
        x_factor = -1 if base.isOpposite() else -1

        # ルートノードの作成。=================================================
        # リグ用の代理親ノードの作成。
        parent_proxy = self.createRigParentProxy(base, name=basename)

        # コントローラ用の代理親ノードの作成。
        ctrl_parent_proxy = self.createCtrlParentProxy(base, basename)
        parent_matrix = self.createParentMatrixNode(base.parent())
        decmtx = func.createDecomposeMatrix(
            ctrl_parent_proxy, ['%s.matrixSum' % parent_matrix],
            withMultMatrix=False
        )
        ctrl_parent_proxy.lockTransform()
        # =====================================================================

        # リグ用のジョイントをオリジナルからコピーする。=======================
        base_proxy = func.copyNode(base, None, parent_proxy, 'Ctrl')
        end_proxy = func.copyNode(end, None, base_proxy, 'Ctrl')

        joint_chain = func.listNodeChain(base, end)
        proxy_chain = []
        parent = parent_proxy
        for joint in joint_chain:
            proxy_chain.append(func.copyNode(joint, None, parent, 'Proxy'))
            parent = proxy_chain[-1]
        # =====================================================================
        
        # ルートコントローラの作成。===========================================
        unitname.setName(basename+'Root')
        unitname.setNodeType('ctrlSpace')
        root_ctrlspace = node.createNode(
            'transform', n=unitname(), p=ctrl_parent_proxy
        )
        root_ctrlspace.fitTo(base)
        self.addLockedList(root_ctrlspace)
        
        unitname.setNodeType('ctrl')
        root_ctrl = node.createNode(
            'transform', n=unitname(), p=root_ctrlspace
        )
        root_ctrl.editAttr(['v'], k=False)
        func.createTranslateConnection(root_ctrl/'t', [], base_proxy/'t')
        ~root_ctrl.attr('r') >> ~base_proxy.attr('r')
        ~root_ctrl.attr('s') >> ~base_proxy.attr('s')
        # =====================================================================

        # ツイストの角度を取るためのangleDriverノードを作成。==================
        unitname.setName(basename + 'AglDrv')
        unitname.setNodeType('trs')
        agl_drv = func.createAngleDriverNode(
            end_proxy, name=unitname(), parent=parent_proxy,
        )
        # =====================================================================
        
        # ベンドシステムの作成。===============================================
        bend_ctrls = func.createBendTwistControl(
            base_proxy, end_proxy, proxy_chain[0], proxy_chain[-1],
            base_proxy, aimVector=[x_factor, 0, 0]
        )

        # ベンドコントローラ用の代理親ノードを作成する。
        unitname.setName(basename + 'BendCtrl')
        bend_parentproxy = func.createSpaceNode(
            n=unitname(), p=ctrl_parent_proxy
        )
        func.connectKeyableAttr(base_proxy, bend_parentproxy)
        (
            base_proxy.attr('jo') >> bend_parentproxy.attr('jo')
        )
        bend_parentproxy.lockTransform()

        # コントローラの作成。-------------------------------------------------
        controllers = []
        ctrlspaces = []
        unitname.setName(basename + 'BendCtrl')
        unitname.setNodeType('ctrl')
        ctrl = unitname()

        unitname.setNodeType('ctrlSpace')
        space = unitname()
        
        ctrl, space = func.createFkController(
            bend_ctrls['midCtrl'], root_ctrl, ctrl, space,
            skipTranslate=True, skipRotate=True, skipScale=True,
        )
        controllers.append(ctrl)
        ctrlspaces.append(space)

        mltmtx = node.createUtil('multMatrix')
        ctrl.attr('matrix') >> mltmtx/'matrixIn[0]'
        space.attr('matrix') >> mltmtx/'matrixIn[1]'
        mltmtx('matrixIn[2]', space('inverseMatrix'), type='matrix')
        for plug in bend_ctrls['midCtrl'].attr('matrix').destinations(p=True):
            mltmtx/'matrixSum' >> plug
        bend_ctrls['midCtrl'].delete()
        # ---------------------------------------------------------------------

        mdl = node.createUtil('multDoubleLinear')
        mdl('input2', 0.5)
        agl_drv.attr('twistX') >> mdl.attr('input1')

        func.fConnectAttr(mdl + '.output', space + '.rx')
        func.lockTransform(controllers)
        func.controlChannels(
            controllers, ['t:a', 'r:a'], isKeyable=True, isLocked=False
        )
        # =====================================================================

        # 代理骨を本体に接続する。=============================================
        for proxy, joint in zip(proxy_chain, joint_chain):
            func.connectKeyableAttr(proxy, joint)
        # =====================================================================

        # 全てのコントローラにシェイプを追加する。=============================
        # ベンドコントローラへのシェイプ追加。---------------------------------
        size = startend_vec.length()
        creator = func.PrimitiveCreator()
        creator.setSize(size*0.5)
        creator.setColorIndex(self.colorIndex('special'))
        creator.setCurveType('crossArrow')
        creator.setRotation([0, 0, 90])
        for ctrl in controllers:
            creator.create(parentNode=ctrl)
        # ---------------------------------------------------------------------
        
        # ルートコントローラにシャイエプを追加。-------------------------------
        creator.setCurveType('box')
        creator.setSizes([size, size*0.25, size*0.25])
        creator.setTranslation([x_factor*size*-0.5, 0, 0])
        creator.setColorIndex(self.colorIndex('main'))
        creator.create(parentNode=root_ctrl)
        # ---------------------------------------------------------------------
        # =====================================================================

        # コントローラをanimSetに追加する。====================================
        anim_set.addChild(root_ctrl)
        anim_set.addChild(*controllers)
        # =====================================================================