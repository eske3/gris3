#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    四足歩行動物用の後ろ足リグ機能を提供するモジュール。
    
    Dates:
        date:2018/01/13 19:59[Eske](eske3g@gmail.com)
        update:2020/11/15 22:53 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2018 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from ..tools import jointEditor
from .. import rigScripts, func, node, verutil
cmds = func.cmds

Category = 'Quads'
BaseName = 'quadBackLeg'

class Option(rigScripts.Option):
    r"""
        作成時に表示するUI用のクラス。
    """
    AttrList = ('numberOfThigh', 'numberOfLowleg', 'numberOfFoot')
    def define(self):
        for attr in self.AttrList:
            self.addIntOption(attr, default=3, min=1, max=26)

class JointCreator(rigScripts.JointCreator):
    r"""
        四足の後ろ足のジョイント作成機能を提供するクラス
    """
    def createUnit(self):
        r"""
            ユニット作成のオーバーライド。
        """
        super(JointCreator, self).createUnit()
        unit = self.unit()
        options = self.options()
        for attr in Option.AttrList:
            value = options.get(attr, 3)
            attr = unit.addIntAttr(attr, min=1, max=26, default=1)
            attr.set(value)

    def process(self):
        name = self.basenameObject()
        parent = self.parent()
        
        xFactor = -1 if self.positionIndex() == 3 else 1

        # ジョイントの作成。---------------------------------------------------
        # 太もも
        name.setName('thigh')
        thigh = node.createNode('joint', n=name(), p=parent)
        thigh.setPosition((xFactor * 9.7, 101.7, 1.3))

        # 下足
        name.setName('lowleg')
        lowleg = node.createNode('joint', n=name(), p=thigh)
        lowleg.setPosition((xFactor * 9.7, 65, 6.6))

        # 足首
        name.setName('foot')
        foot = node.createNode('joint', n=name(), p=lowleg)
        foot.setPosition((xFactor * 9.7, 36, -5.2))

        # 指の付け根
        name.setName('ball')
        ball = node.createNode('joint', n=name(), p=foot)
        ball.setPosition((xFactor * 9.7, 5.7, -3.7))

        # 指の付け根のエンドジョイント
        name.setName('ballEnd')
        ball_end = node.createNode('joint', n=name(), p=ball)
        ball_end.setPosition((xFactor * 9.7, 2.0, -3.7))

        # つま先
        name.setName('toe')
        toe = node.createNode('joint', n=name(), p=ball)
        toe.setPosition((xFactor * 9.7, 1.7, 7.5))
        toe.setRadius(1.3)

        # つま先のエンドジョイント
        name.setName('toeEnd')
        toeEnd = node.createNode('joint', n=name(), p=toe)
        toeEnd.setPosition((xFactor * 9.7, 1.7, 18))
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
        om.execute((thigh, lowleg, foot, ball))
        
        om.setTargetUpAxis('-Y' if xFactor < 0 else '+Y')
        om.execute((toe, toeEnd))
        # ---------------------------------------------------------------------

        # ユニットの設定。-----------------------------------------------------
        unit = self.unit()
        unit.addMember('thigh', thigh)
        unit.addMember('lowleg', lowleg)
        unit.addMember('foot', foot)
        unit.addMember('ball', ball)
        unit.addMember('toe', toe)
        unit.addMember('toeEnd', toeEnd)
        unit.addMember('toeMarker', toe_marker)
        unit.addMember('heelMarker', heel_marker)
        # ---------------------------------------------------------------------

        self.asRoot(thigh)
        toe.select()

    def finalize(self):
        unit = self.unit()
        name = func.Name(unit())
        name.setSuffix(self.suffix())
        name.setNodeType('jnt')

        num_up = unit('numberOfThigh')
        num_low = unit('numberOfLowleg')
        num_foot = unit('numberOfFoot')

        lowleg = unit.getMember('lowleg')
        foot = unit.getMember('foot')
        ball = unit.getMember('ball')

        upjoints = jointEditor.splitJoint(num_up, lowleg)[0]
        lowjoints = jointEditor.splitJoint(num_low, foot)[0]
        footjoints = jointEditor.splitJoint(num_foot, ball)[0]
        for joints, key in zip(
                [upjoints, lowjoints, footjoints],
                ['thighTwst', 'lowlegTwst', 'footTwst']
            ):
            for joint, char in zip(joints, verutil.LOWERCASE):
                name.setName('%sTwist%s' % (key, char))
                joint.rename(name())


class RigCreator(rigScripts.RigCreator):
    r"""
        リグ作成機能を提供するクラス
    """
    def process(self):
        unit = self.unit()
        unitname = self.unitName()
        basename = unitname.name()
        side = unit.positionIndex()
        side_str  = unit.position()
        anim_set = self.animSet()

        thigh_jnt = unit.getMember('thigh')
        lowleg_jnt = unit.getMember('lowleg')
        foot_jnt = unit.getMember('foot')
        ball_jnt = unit.getMember('ball')
        toe_jnt = unit.getMember('toe')
        toeend_jnt = unit.getMember('toeEnd')
        toe_marker = unit.getMember('toeMarker')
        heel_marker = unit.getMember('heelMarker')

        position = unitname.position()
        getfactor = lambda x : {'R' : -1}.get(x, 1)

        # Get a pole vector direction from the thigh to foot vector
        # perpendicular to the foot to toe vector.
        thigh_vector = func.Vector(thigh_jnt.position())
        lowleg_vector = func.Vector(lowleg_jnt.position())
        foot_vector = func.Vector(foot_jnt.position())
        ball_vector = func.Vector(ball_jnt.position())
        toe_vector = func.Vector(toeend_jnt.position())
        toe_marker_vector = func.Vector(toe_marker.position())
        heel_marker_vector = func.Vector(heel_marker.position())
        heel_to_toe = toe_marker_vector - heel_marker_vector

        thigh_to_foot = foot_vector - thigh_vector
        foot_to_ball = ball_vector - lowleg_vector
        ball_to_toe = toe_vector - ball_vector
        foot_to_toe = toe_vector - foot_vector
        h = foot_to_toe * thigh_to_foot / thigh_to_foot.length()
        pv_dir_vector = foot_to_toe - (thigh_to_foot.norm() * h)

        # ルートノードの作成。=================================================
        # リグ用の代理親ノードの作成。
        parent_proxy = self.createRigParentProxy(thigh_jnt, name=basename)

        # ikコントローラ用の代理親ノードの作成。
        ikctrl_parent_proxy = self.createCtrlParentProxy(
            thigh_jnt, basename+'Ik'
        )
        ctrl_parent_proxy = self.createCtrlParentProxy(thigh_jnt, basename)

        # ブレンドを行うための親ノードを作成。
        unitname.setName(basename + 'Ik')
        unitname.setNodeType('parentBlender')
        parent_blender = self.createParentProxy(thigh_jnt, name=unitname())
        # =====================================================================

        # リグ用のジョイントをオリジナルからコピーする。=======================
        # IK用、FK用、そして合成用のジョイントをオリジナルからコピー。---------
        thigh_rigJnt, lowleg_rigJnt, foot_rigJnt, ball_rigJnt, toe_rigJnt = [
            {} for x in range(5)
        ]
        for key in ('ikJnt', 'fkJnt', 'combJnt'):
            thigh_rigJnt[key] = func.copyNode(thigh_jnt, key, parent_proxy)
            lowleg_rigJnt[key] = func.copyNode(
                lowleg_jnt, key, thigh_rigJnt[key]
            )
            foot_rigJnt[key] = func.copyNode(foot_jnt, key, lowleg_rigJnt[key])
            ball_rigJnt[key] = func.copyNode(ball_jnt, key, foot_rigJnt[key])
            toe_rigJnt[key] = func.copyNode(toe_jnt, key, ball_rigJnt[key])
        toeend_rigJnt = {
            'ikJnt':func.copyNode(toeend_jnt, 'ikJnt', toe_rigJnt['ikJnt'])
        }
        # ---------------------------------------------------------------------

        # ツイストの角度を取るためのangleDriverノードを作成。==================
        unitname.setName(basename + 'thighAglDrv')
        unitname.setNodeType('trs')
        thigh_agl_drv = func.createAngleDriverNode(
            thigh_rigJnt['combJnt'], name=unitname(), parent=parent_proxy,
        )

        unitname.setName(basename + 'footAglDrv')
        foot_agl_drv = func.createAngleDriverNode(
            foot_rigJnt['combJnt'], name=unitname(), parent=parent_proxy,
        )
        
        unitname.setName(basename + 'ballAglDrv')
        ball_agl_drv = func.createAngleDriverNode(
            ball_rigJnt['combJnt'], name=unitname(), parent=parent_proxy,
        )
        # =====================================================================

        # 元のジョイントから代理ジョイントを作成する。=========================
        thigh_twists = func.listNodeChain(thigh_jnt, lowleg_jnt)[1:-1]
        lowleg_twists = func.listNodeChain(lowleg_jnt, foot_jnt)[1:-1]
        foot_twists = func.listNodeChain(foot_jnt, ball_jnt)[1:-1]

        thigh_twist_proxies = []
        lowleg_twist_proxies = []
        foot_twist_proxies = []
        thigh_proxy = func.copyNode(thigh_jnt, 'jntProxy', parent_proxy)
        parent = thigh_proxy
        for twist_joint in thigh_twists:
            thigh_twist_proxies.append(
                func.copyNode(twist_joint, 'jntProxy', parent)
            )
            parent = thigh_twist_proxies[-1]

        lowleg_proxy = func.copyNode(lowleg_jnt, 'jntProxy', parent)
        parent = lowleg_proxy
        for twist_joint in lowleg_twists:
            lowleg_twist_proxies.append(
                func.copyNode(twist_joint, 'jntProxy', parent)
            )
            parent = lowleg_twist_proxies[-1]

        foot_proxy = func.copyNode(foot_jnt, 'jntProxy', parent)
        parent = foot_proxy
        for twist_joint in foot_twists:
            foot_twist_proxies.append(
                func.copyNode(twist_joint, 'jntProxy', parent)
            )
            parent = foot_twist_proxies[-1]

        ball_proxy = func.copyNode(ball_jnt, 'jntProxy', parent)
        toe_proxy = func.copyNode(toe_jnt, 'jntProxy', ball_proxy)
        # =====================================================================

        # IKロール用のダミージョイントを作成する。=============================
        thigh_ikdmy = func.copyNode(thigh_jnt, 'ikDmy', parent_proxy)
        thighend_ikdmy = func.copyNode(ball_jnt, 'ikDmy', thigh_ikdmy)

        orientation_mod = jointEditor.OrientationModifier()
        orientation_mod.setPrimaryAxis(self.axisX())
        orientation_mod.execute([thigh_ikdmy, thighend_ikdmy])
        # =====================================================================

        # コントローラとその代理ノードを作成する。=============================
        # Ik leg controller.
        leg_ik_ctrlspace = {}
        leg_ik_ctrl = {}

        # Movable rotation controller.
        toeroll_ik_ctrlspace = {}
        toeroll_ik_ctrl = {}
        sole_rev_space = {}

        # Heel rotation node.
        heel_rot_space = {}
        
        scale_space = {}

        step_ctrlspace = {}
        step_ctrl = {}
        toe_ik_ctrlspace = {}
        toe_ik_ctrl = {}
        
        ball_ik_ctrl = {}
        ball_ik_ctrlspace = {}
        
        lockedlist = []
        
        for key, root_parent in zip(
                ['', 'Proxy'], [ikctrl_parent_proxy, parent_blender]
            ):
            # 足のスペーサーとコントローラ-------------------------------------
            unitname.setName(basename+'Ik')
            unitname.setNodeType('ctrlSpace' + key)
            leg_ik_ctrlspace[key] = node.createNode('transform', n=unitname())
            root_parent.addChild(leg_ik_ctrlspace[key])
            leg_ik_ctrlspace[key].fitTo(ball_jnt, flags=0b1000)

            unitname.setNodeType('ctrl' + key)
            leg_ik_ctrl[key] =node.createNode(
                'transform', n=unitname(), p=leg_ik_ctrlspace[key]
            )
            func.lockTransform((leg_ik_ctrlspace[key], leg_ik_ctrl[key]))
            leg_ik_ctrl[key].editAttr(['t:a', 'r:a'], k=True,l=False)
            # -----------------------------------------------------------------

            # つま先の回転コントローラ。---------------------------------------
            unitname.setName(basename + 'ToeRotation')
            unitname.setNodeType('ctrlSpace' + key)
            toeroll_ik_ctrlspace[key] = node.createNode(
                'transform', p=leg_ik_ctrl[key], n=unitname()
            )
            toeroll_ik_ctrlspace[key].fitTo(toe_marker, flags=0b1000)

            unitname.setNodeType('ctrl' + key)
            toeroll_ik_ctrl[key] = node.createNode(
                'transform', p=toeroll_ik_ctrlspace[key], n=unitname()
            )
            func.lockTransform(
                [toeroll_ik_ctrlspace[key], toeroll_ik_ctrl[key]]
            )
            toeroll_ik_ctrl[key].editAttr(['t:a', 'r:a'], k=True, l=False)
            # -----------------------------------------------------------------

            # 足の裏の移動相殺機能。-------------------------------------------
            unitname.setName(basename + 'SoleRev')
            unitname.setNodeType('trs' + key)
            sole_rev_space[key] = node.createNode(
                'transform', p=toeroll_ik_ctrl[key], n=unitname()
            )
            sole_rev_space[key].lockTransform()
            sole_rev_space[key].editAttr(['t:a'], k=True, l=False)
            lockedlist.append(sole_rev_space[key])
            # -----------------------------------------------------------------

            # 踵の自動回転機能。-----------------------------------------------
            unitname.setName(basename + 'HeelRotation')
            heel_rot_space[key] = node.createNode(
                'transform', p=sole_rev_space[key], n=unitname()
            )
            heel_rot_space[key].fitTo(heel_marker, flags=0b1000)
            heel_rot_space[key].lockTransform()
            heel_rot_space[key].editAttr(['r:a'], k=True, l=False)
            lockedlist.append(heel_rot_space[key])
            # -----------------------------------------------------------------

            unitname.setName(basename + 'CtrlScale')
            unitname.setNodeType('space' + key)
            scale_space[key] = node.createNode(
                'transform',  n=unitname(), p=heel_rot_space[key]
            )
            scale_space[key].fitTo(ball_jnt)
            
            # 踏み込み用コントローラとその代理ノード。-------------------------
            unitname.setName(basename + 'Step')
            unitname.setNodeType('ctrlSpace' + key)
            step_ctrlspace[key] = node.createNode(
                'transform',  n=unitname(), p=scale_space[key]
            )
            step_ctrlspace[key].fitTo(toe_jnt)

            unitname.setNodeType('ctrl' + key)
            step_ctrl[key] = node.createNode(
                'transform', n=unitname(), p=step_ctrlspace[key]
            )
            func.lockTransform([step_ctrlspace[key], step_ctrl[key]])
            step_ctrl[key].editAttr(['ry'], k=True, l=False)
            # -----------------------------------------------------------------

            # つま先のコントローラとその代理ノード。---------------------------
            unitname.setName(basename + 'Toe')
            unitname.setNodeType('ctrlSpace' + key)
            toe_ik_ctrlspace[key] = func.createSpaceNode(
                n=unitname(), p=scale_space[key]
            )
            toe_ik_ctrlspace[key].fitTo(toe_jnt)

            unitname.setNodeType('ctrl' + key)
            toe_ik_ctrl[key] = node.createNode(
                'transform', n=unitname(), p=toe_ik_ctrlspace[key]
            )
            self.addLockedList([toe_ik_ctrlspace[key]])
            toe_ik_ctrl[key].lockTransform()
            toe_ik_ctrl[key].editAttr(['r:a'], k=True, l=False)
            # -----------------------------------------------------------------

            # A ball controller and the it's proxy.----------------------------
            unitname.setName(basename + 'Ball')
            unitname.setNodeType('ctrlSpace' + key)
            ball_ik_ctrlspace[key] = func.createSpaceNode(
                n=unitname(), p=step_ctrl[key]
            )
            ball_ik_ctrlspace[key].fitTo(ball_jnt)
            ball_ik_ctrlspace[key].fitTo(foot_jnt, flags=0b0100)

            unitname.setNodeType('ctrl' + key)
            ball_ik_ctrl[key] = node.createNode(
                'transform', n=unitname(), p=ball_ik_ctrlspace[key]
            )
            ball_ik_ctrl[key].lockTransform()
            ball_ik_ctrl[key].editAttr(['r:a', 'sx'],k=True, l=False)
            # -----------------------------------------------------------------

        stretch_attr = leg_ik_ctrl[''].addFloatAttr('stretch', default=0)
        softik_attr = leg_ik_ctrl[''].addFloatAttr(
            'softIk', min=0, max=100, default=0, smx=1
        )
        world_attr = leg_ik_ctrl[''].addFloatAttr('world', default=1)
        footaim_attr = leg_ik_ctrl[''].addFloatAttr('footAiming', default=0.3)

        # IKシステムの構築。---------------------------------------------------
        # 足の裏の移動相殺機能のセットアップ。
        md = node.createUtil('multiplyDivide')
        for axis in self.Axises:
            axis = axis.lower()
            toeroll_ik_ctrl['Proxy'].attr('t'+axis) >> '%s.i1%s' % (md, axis)
            md('i2'+axis, -1)
            md.attr('o'+axis) >> '%s.t%s' % (sole_rev_space['Proxy'], axis)
        # ---------------------------------------------------------------------
            
        # Make connections from controller to proxy.---------------------------
        for couple in (
            leg_ik_ctrl, toeroll_ik_ctrl, toe_ik_ctrl, step_ctrl,
            ball_ik_ctrl,
        ):
            func.connectKeyableAttr(couple[''], couple['Proxy'])

        for couple in (
            sole_rev_space, heel_rot_space, ball_ik_ctrlspace,
        ):
            func.connectKeyableAttr(couple['Proxy'], couple[''])

        cndt = node.createUtil('condition')
        cndt('operation' , 2)
        cndt('secondTerm', 0)
        cndt('colorIfFalseR', 0)
        cndt('colorIfTrueG', 0)
        step_ctrl[''].attr('ry') >> cndt/'firstTerm'
        step_ctrl[''].attr('ry') >> cndt/'colorIfTrueR'
        step_ctrl[''].attr('ry') >> cndt/'colorIfFalseG'
        cndt.attr('outColorR') >>  step_ctrl['Proxy']/'ry'
        cndt.attr('outColorG') >>  heel_rot_space['Proxy']/'rx'
        # ---------------------------------------------------------------------
        # =====================================================================

        # /////////////////////////////////////////////////////////////////////
        # IKコントローラとシステムを作成する。                               //
        # /////////////////////////////////////////////////////////////////////
        # IKシステムの構築。===================================================
        unitname.setNodeType('ik')
        # For the toe ik system.
        unitname.setName(basename + 'Toe')
        toe_ik = node.ikHandle(n=unitname(),
            sj=toe_rigJnt['ikJnt'], ee=toeend_rigJnt['ikJnt'],
            sol='ikSCsolver'
        )[0]
        toe_ik_ctrl['Proxy'].addChild(toe_ik)

        # For the leg ik system.
        unitname.setName(basename + 'Leg')
        leg_ik =node.ikHandle(n=unitname(),
            sj=thigh_rigJnt['ikJnt'], ee=foot_rigJnt['ikJnt'], sol='ikRPsolver'
        )[0]

        # For the foot ik system.
        unitname.setName(basename + 'Foot')
        foot_ik = node.ikHandle(n=unitname(),
            sj=foot_rigJnt['ikJnt'], ee=ball_rigJnt['ikJnt'], sol='ikRPsolver'
        )[0]
        step_ctrl['Proxy'].addChild(foot_ik)

        # アーチ部分のIKの設定。
        unitname.setName(basename + 'Arch')
        arch_ik = node.ikHandle(n=unitname(),
            sj=ball_rigJnt['ikJnt'], ee=toe_rigJnt['ikJnt'], sol='ikRPsolver'
        )[0]
        unitname.setName(basename+'ArchScale')
        arch_scaler = node.createNode(
            'transform', n=unitname(), p=scale_space['Proxy']
        )
        arch_scaler.addChild(arch_ik)
        # heel_rot_space['Proxy'].addChild(arch_ik)

        unitname.setName(basename + 'LegDmy')
        leg_dmyik = node.ikHandle(n=unitname(),
            sj=thigh_ikdmy, ee=thighend_ikdmy, sol='ikSCsolver'
        )[0]
        heel_rot_space['Proxy'].addChild(leg_dmyik)

        unitname.setName(basename+'IkPos')
        unitname.setNodeType('pos')
        leg_ik_pos = node.createNode(
            'transform', n=unitname(), p=ball_ik_ctrl['Proxy']
        )
        leg_ik_pos.fitTo(leg_ik)
        leg_ik_pos.addChild(leg_ik)
        # =====================================================================
        
        # ストレッチシステムの構築。===========================================
        result_node = func.createScaleStretchSystem(
            thigh_rigJnt['ikJnt'], ball_rigJnt['ikJnt']
        )
        unitname.setNodeType('loc')
        unitname.setName(basename + 'Start')
        start_loc = unitname()
        
        unitname.setName(basename + 'End')
        end_loc = unitname()

        unitname.setName(basename + 'RotationSetup')
        unitname.setNodeType('grp')
        dist_node = unitname()

        start_loc = node.asObject(
            cmds.parent(
                cmds.rename(result_node['start'], start_loc), parent_proxy
            )[0]
        )
        end_loc = node.asObject(
            cmds.parent(
                cmds.rename(result_node['end'], end_loc),
                step_ctrl['Proxy']()
            )[0]
        )
        dist_node = node.asObject(
            cmds.parent(
                cmds.rename(result_node['result'], dist_node), thigh_ikdmy
            )[0]
        )
        stretch_attr >> dist_node.attr('stretch')
        # =====================================================================
    
        # =====================================================================
        parent_matrixes = [
            x + '.inverseMatrix' for x in func.listNodeChain(
                leg_ik_ctrlspace['Proxy'], step_ctrl['Proxy']
            )
        ]

        src_rot_values = ball_ik_ctrlspace['Proxy']('r')[0]
        aim_cst = func.localConstraint(
            cmds.aimConstraint, start_loc, ball_ik_ctrlspace['Proxy'],
            mo=True,
            aimVector=(getfactor(position), 0, 0),
            upVector=(0, 0, getfactor(position)), worldUpType='none',
            targetParents=parent_matrixes, parents=[[parent_proxy + '.matrix']]
        )
        pb = node.createUtil('pairBlend')
        pb('inRotate1', src_rot_values)
        pb('rotInterpolation', 1)
        ~aim_cst.attr('cr') >> ~pb.attr('ir2')
        leg_ik_ctrl[''].attr('footAiming') >> pb/'weight'
        ~pb.attr('or') >> ~ball_ik_ctrlspace['Proxy'].attr('r')        
        self.addLockedList(
            [ball_ik_ctrlspace[x] for x in ball_ik_ctrlspace]
        )
        # =====================================================================

        # ソフトIKシステムを構築する。=========================================
        cmds.aimConstraint(
            start_loc, leg_ik_pos,
            aimVector=[1, 0, 0], upVector=[0, 1, 0], worldUpType='none'
        )
        leg_ik_pos.lockTransform()
        func.createSoftIkFromStretchNode(
            leg_ik_ctrl['']/'softIk', dist_node, leg_ik
        )
        # =====================================================================

        # 自動ポールベクター追従システムの作成。===============================
        # システムの作成。-----------------------------------------------------
        unitname.setName(basename + 'IkPv')
        unitname.setNodeType('trs')

        ik_roll_ctrlproxy = node.asObject(
            cmds.pointConstraint(
                start_loc, end_loc, dist_node
            )[0]
        )
        cmds.setAttr(dist_node+'.r', 0, 0, 0)

        cst_vector = func.Vector(ik_roll_ctrlproxy.position())
        pv_pos = cst_vector + pv_dir_vector

        pv_locator = node.createNode(
            'transform', n=unitname(), p=ik_roll_ctrlproxy
        )
        pv_locator.setPosition((pv_pos.x, pv_pos.y, pv_pos.z))
        pv_locator.lockTransform()

        cmds.poleVectorConstraint(pv_locator, leg_ik)
        # ---------------------------------------------------------------------

        # ロール用コントローラの作成。-----------------------------------------
        unitname.setName(basename + 'IkRole')
        unitname.setNodeType('ctrlSpace')
        ikrole_ctrlspace = node.createNode(
            'transform', n=unitname(), p=ikctrl_parent_proxy
        )
        ikrole_ctrlspace.editAttr(
                ['s:a', 'shxy', 'shxz', 'shyz'], k=False, l=True
        )

        unitname.setNodeType('ctrl')
        ikrole_ctrl = node.createNode(
            'transform', n=unitname(), p=ikrole_ctrlspace
        )
        ikrole_ctrl.lockTransform()
        ikrole_ctrl.editAttr(['rx'], k=True, l=False)
        # ---------------------------------------------------------------------

        # システムとコントローラを接続する。-----------------------------------
        inputMatrices = [
            x + '.matrix' for x in [dist_node, thigh_ikdmy, parent_proxy]
        ]
        inputMatrices.append(ikctrl_parent_proxy + '.inverseMatrix')
        decmtx, mltmtx = func.createDecomposeMatrix(
            ikrole_ctrlspace, inputMatrices
        )
        ikrole_ctrlspace.lockTransform()
        func.connectKeyableAttr(ikrole_ctrl, ik_roll_ctrlproxy)
        # ---------------------------------------------------------------------
        # =====================================================================

        # IKスケール用コントローラの作成。=====================================
        parent = ctrl_parent_proxy
        ik_scale_spaces = []
        ik_scale_ctrls = []
        scale_ctrls = []
        for part in [
            thigh_rigJnt, lowleg_rigJnt, foot_rigJnt, ball_rigJnt, toe_rigJnt,
        ]:
            name = func.Name(part['ikJnt'])
            name.setName(name.name() + 'Scale')
            name.setNodeType('ctrlSpace')
            space = func.createSpaceNode(p=parent, n=name())
            if ik_scale_ctrls and ik_scale_spaces:
                md = node.createUtil('multiplyDivide')
                ik_scale_spaces[-1].attr('s') >> md.attr('i1')
                ik_scale_ctrls[-1].attr('s') >> md.attr('i2')
                md.attr('o') >> space.attr('inverseScale')

            for attr in 'tr':
                ~part['ikJnt'].attr(attr) >> ~space.attr(attr)
            for ax in func.Axis:
                space('jo'+ax, part['ikJnt']('jo'+ax))

            name.setNodeType('ctrl')
            ctrl = node.createNode('transform', n=name(), p=space)
            ik_scale_spaces.append(space)
            ik_scale_ctrls.append(ctrl)
            parent = ctrl

            sxattr = part['ikJnt'].attr('sx')
            if not sxattr.isDst():
                sx_plug = ctrl.attr('sx')
            else:
                # Reconnect scaleX of the ik joint.
                mdl = node.createUtil('multDoubleLinear')
                input = sxattr.source(p=True)
                input >> mdl.attr('input1')
                input, space.attr('sx')
                ctrl.attr('sx') >> mdl.attr('input2')
                sx_plug = mdl.attr('output')

            sx_plug >> part['ikJnt'].attr('sx')
            ctrl.attr('sy') >> part['ikJnt'].attr('sy')
            ctrl.attr('sz') >> part['ikJnt'].attr('sz')

            func.lockTransform([space, ctrl])
            ctrl.editAttr(['s:a'], k=True, l=False)
            scale_ctrls.append(ctrl)
       
        ik_scale_ctrls[2].attr('sx') >> ball_ik_ctrl['Proxy']/'sx'
        
        ik_scale_ctrls[-2].attr('s') >> arch_scaler/'s'
        fbf = node.createUtil('fourByFourMatrix')
        for s, d in zip('xyz', ('00', '11', '22')):
            ik_scale_ctrls[3].attr('s'+s) >> fbf/('in'+d)
        mlt_mtx = node.createUtil('multMatrix')
        mlt_mtx(
            'matrixIn[0]', toe_ik_ctrlspace['Proxy']('matrix'),
            type='matrix'
        )
        fbf.attr('output') >> mlt_mtx/'matrixIn[1]'
        dec_mtx = node.createUtil('decomposeMatrix')
        mlt_mtx.attr('matrixSum') >> dec_mtx/'inputMatrix'
        dec_mtx.attr('outputScale') >> toe_ik_ctrlspace['Proxy']/'is'
        dec_mtx.attr('outputScale') >> toe_ik_ctrlspace['']/'is'
        func.makeDecomposeMatrixConnection(
            dec_mtx, [toe_ik_ctrlspace['Proxy'], toe_ik_ctrlspace['']]
        )

        # @Mod : スケールに関する仕組みで修正する可能性あり。
        # humanBaseLimbsRigの822行目付近参照
        for ax in func.Axis:
            scale_attr = leg_ik_ctrl[''].attr('s'+ax)
            scale_attr.setLock(False)
            leg_ik_ctrl['Proxy'].attr('s'+ax) >> scale_attr
            scale_attr.setLock(True)
            ik_scale_ctrls[-2].attr('s'+ax) >> scale_space['']/('s'+ax)
        for n in scale_space.values():
            n.lockTransform()
        # =====================================================================

        # IKのルートコントローラを作成する。===================================
        unitname.setName(basename + 'IkRoot')
        unitname.setNodeType('ctrl')
        legIkRoot_ctrl = unitname()
        
        unitname.setNodeType('ctrlSpace')
        legIkRoot_space = unitname()
        legIkRoot_ctrl, legIkRoot_space = func.createFkController(
            target=thigh_rigJnt['ikJnt'], parent=ctrl_parent_proxy,
            name=legIkRoot_ctrl, spaceName=legIkRoot_space,
            skipTranslate=False, skipRotate=True, skipScale=True,
            isLockTransform=True
        )
        legIkRoot_ctrl.lockTransform()
        legIkRoot_ctrl.editAttr(['t:a'], k=True, l=False)
        pmm = legIkRoot_ctrl.attr('tx').destinations()[0]
        for n in [thigh_ikdmy, start_loc]:
            ~pmm.attr('o') >> ~n.attr('t')
        # =====================================================================
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////


        # /////////////////////////////////////////////////////////////////////
        # FKコントローラの作成。                                             //
        # /////////////////////////////////////////////////////////////////////
        fk_ctrls = []
        unitname.setName(basename + 'ThighFK')
        unitname.setNodeType('ctrl')
        thigh_fkCtrl = unitname()

        # A fk controller for the thigh.---------------------------------------
        unitname.setNodeType('ctrlSpace')
        thigh_fkroot = unitname()
        thigh_fkCtrl, thigh_fkroot = func.createFkController(
            thigh_rigJnt['fkJnt'], ctrl_parent_proxy,
            thigh_fkCtrl, thigh_fkroot, skipTranslate=False,
            isLockTransform=False, calculateWithSpace=True
        )
        fk_world_attr = thigh_fkCtrl.addFloatAttr('world', default=0)

        ctrl_space = thigh_fkCtrl.parent()
        mltmtx = node.createUtil('multMatrix')
        mltmtx('matrixIn[0]', ctrl_space('worldMatrix'), type='matrix')
        ctrl_parent_proxy.attr('inverseMatrix') >> mltmtx/'matrixIn[1]'

        decmtx = node.createUtil('decomposeMatrix')
        mltmtx.attr('matrixSum') >> decmtx/'inputMatrix'

        ~decmtx.attr('or') >> ~ctrl_space.attr('r')
        func.blendSelfConnection(
            ctrl_space, blendControlAttr=thigh_fkCtrl + '.world',
            skipTranslate=True, skipScale=True, blendMode=1
        )
        ctrl_space.lockTransform()
        fk_ctrls.append(thigh_fkCtrl)
        # ---------------------------------------------------------------------

        # A fk controller for the lowleg.
        unitname.setName(basename + 'LowlegFk')
        unitname.setNodeType('ctrlSpace')
        fk_ctrlspace = unitname()
        
        unitname.setNodeType('ctrl')
        lowleg_fkCtrl = func.createFkController(
            lowleg_rigJnt['fkJnt'], thigh_fkCtrl, unitname(), fk_ctrlspace,
            skipTranslate=False
        )[0]
        fk_ctrls.append(lowleg_fkCtrl)
        
        # A fk controller for the foot.
        unitname.setName(basename + 'FootFk')
        unitname.setNodeType('ctrlSpace')
        fk_ctrlspace = unitname()
        
        unitname.setNodeType('ctrl')
        foot_fkCtrl = func.createFkController(
            foot_rigJnt['fkJnt'], lowleg_fkCtrl, unitname(), fk_ctrlspace,
            skipTranslate=False
        )[0]
        fk_ctrls.append(foot_fkCtrl)

        # A fk controller for the ball.
        unitname.setName(basename + 'BallFk')
        unitname.setNodeType('ctrlSpace')
        fk_ctrlspace = unitname()
        
        unitname.setNodeType('ctrl')
        ball_fkCtrl = func.createFkController(
            ball_rigJnt['fkJnt'], foot_fkCtrl, unitname(), fk_ctrlspace,
            skipTranslate=False
        )[0]
        fk_ctrls.append(ball_fkCtrl)
        
        # IK/FKスイッチのターゲットを追加する。--------------------------------
        unitname.setName(basename + 'IkFkSwitchTgt')
        target = node.createNode(
            'transform', n=unitname(), p=ball_rigJnt['fkJnt']
        )
        target.fitTo(leg_ik_ctrl[''])
        target.lockTransform()
        switch_tgt_attr = leg_ik_ctrl[''].addMessageAttr('ikFkSwitchTarget')
        target/'message' >> switch_tgt_attr
        # ---------------------------------------------------------------------

        # A fk controller for the toe.
        unitname.setName(basename + 'ToeFk')
        unitname.setNodeType('ctrlSpace')
        fk_ctrlspace = unitname()
        
        unitname.setNodeType('ctrl')
        toe_fkCtrl = func.createFkController(
            toe_rigJnt['fkJnt'], ball_fkCtrl, unitname(), fk_ctrlspace,
            skipTranslate=False
        )[0]
        fk_ctrls.append(toe_fkCtrl)
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////


        # /////////////////////////////////////////////////////////////////////
        # Combine ik joints with fk joints.                                  //
        # /////////////////////////////////////////////////////////////////////
        # Create a parameter controller.
        unitname.setName(basename + 'Param')
        unitname.setNodeType('ctrl')
        param_ctrl = node.createNode(
            'transform', n=unitname(), p=ikrole_ctrlspace
        )
        param_ctrl.editAttr(['t:a', 'r:a', 's:a', 'v'], k=False, l=False)
        ikblend_attr = param_ctrl.addFloatAttr('ikBlend', default=1.0)
        ikscl_vis_attr = param_ctrl.addDisplayAttr(
            'ikScalingController', default=0, cb=True
        )
        bend_vis_attr = param_ctrl.addDisplayAttr(
            'bendCtrlVisibility', default=0, cb=True
        )
        for name in ('upKeepVolume', 'lowKeepVolume', 'footKeepVolume'):
            param_ctrl.addFloatAttr(name,
                default=0, min=-2, max=2, smn=-1, smx=1
            )

        horizontal_vector = (
            (cst_vector - foot_vector) ** (pv_pos - foot_vector)
            if side != 3
            else (pv_pos - foot_vector) ** (cst_vector - foot_vector)
        )
           
        param_ctrl_vector = (
            horizontal_vector.norm()
            * thigh_to_foot.length() * 0.35
            + cst_vector
        )
        param_ctrl.setPosition(
            (param_ctrl_vector.x, param_ctrl_vector.y, param_ctrl_vector.z)
        )
        # Connects visibility from the ikBlend attr to the ik controllers
        # and the fk controllers.
        for ctrl in [leg_ik_ctrlspace[''], ikrole_ctrl, legIkRoot_space]:
            ikblend_attr >> ctrl/'v'
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////


        # /////////////////////////////////////////////////////////////////////
        # Connects combined joints to proxy joints.                          //
        # /////////////////////////////////////////////////////////////////////
        # Adds bend controller to the thigh and the lowleg joint chain.
        # (After finish this process, the proxy joints will be connected
        # from a combined joints.)
        thigh_bend_ctrls = func.createBendTwistControl(
            thigh_rigJnt['combJnt'], lowleg_rigJnt['combJnt'],
            thigh_proxy, lowleg_proxy, thigh_ikdmy, aimVector=self.vectorX()
        )
        (
            param_ctrl.attr('upKeepVolume')
            >> thigh_bend_ctrls['scaleInfo']/'volumeScale'
        )

        lowleg_bend_ctrls = func.createBendTwistControl(
            lowleg_rigJnt['combJnt'], foot_rigJnt['combJnt'],
            lowleg_proxy, foot_proxy, lowleg_rigJnt['combJnt'],
            False, self.vectorX()
        )
        (
            param_ctrl.attr('lowKeepVolume')
            >> lowleg_bend_ctrls['scaleInfo']/'volumeScale'
        )

        foot_bend_ctrls = func.createBendTwistControl(
            foot_rigJnt['combJnt'], ball_rigJnt['combJnt'],
            foot_proxy, ball_proxy, foot_rigJnt['combJnt'],
            False, self.vectorX()
        )
        (
            param_ctrl.attr('footKeepVolume')
            >> foot_bend_ctrls['scaleInfo']/'volumeScale'
        )

        # Connects the foot joint from combined to proxy.----------------------
        unitname.setName(basename + 'BallProxy')
        unitname.setNodeType('ik')
        ball_ik = node.ikHandle(
            sj=ball_proxy, ee=toe_proxy, sol='ikRPsolver'
        )[0]
        ball_rigJnt['combJnt'].addChild(ball_ik)
        ball_ik.rename(unitname())

        unitname.setNodeType('ikPv')
        ik_pv = func.createPoleVector([ball_ik()])[0]
        node.asObject(
            cmds.rename(
                cmds.parent(ik_pv, ball_rigJnt['combJnt'])[0],
                unitname()
            )
        )
        ~ball_rigJnt['combJnt'].attr('s') >> ~ball_proxy.attr('s')
        # ---------------------------------------------------------------------

        # Connects the toe joint from combined to proxy.
        func.connectKeyableAttr(toe_rigJnt['combJnt'], toe_proxy)
        
        # Creates controller to control a bend system.=========================
        # Create parent proxy for bend controllers.----------------------------
        unitname.setName(basename + 'ThighBendCtrl')
        unitname.setNodeType('parentProxy')
        thigh_bend_parentproxy = func.createSpaceNode(
            n=unitname(), p=ctrl_parent_proxy
        )
        func.connectKeyableAttr(
            thigh_rigJnt['combJnt'], thigh_bend_parentproxy
        )
        (
            ~thigh_rigJnt['combJnt'].attr('jo')
            >> ~thigh_bend_parentproxy.attr('jo')
        )
        
        unitname.setName(basename + 'LowlegBendCtrl')
        lowleg_bend_parentproxy = func.createSpaceNode(
            n=unitname(), p=thigh_bend_parentproxy
        )
        func.connectKeyableAttr(
            lowleg_rigJnt['combJnt'], lowleg_bend_parentproxy
        )
        (
            ~lowleg_rigJnt['combJnt'].attr('jo')
            >> ~lowleg_bend_parentproxy.attr('jo')
        )

        unitname.setName(basename + 'FootBendCtrl')
        foot_bend_parentproxy = func.createSpaceNode(
            n=unitname(), p=lowleg_bend_parentproxy
        )
        func.connectKeyableAttr(
            foot_rigJnt['combJnt'], foot_bend_parentproxy
        )
        ~foot_rigJnt['combJnt'].attr('jo') >> ~foot_bend_parentproxy.attr('jo')

        func.lockTransform(
            (
                thigh_bend_parentproxy, lowleg_bend_parentproxy,
                foot_bend_parentproxy
            )
        )
        # ---------------------------------------------------------------------

        # Create bend controllers.---------------------------------------------
        bend_ctrls = []
        bend_ctrlspace = []

        # Create thigh bend controller.
        unitname.setName(basename + 'ThighBendCtrl')
        unitname.setNodeType('ctrl')
        ctrl = unitname()
        
        unitname.setNodeType('ctrlSpace')
        space = unitname()
    
        ctrl, space = func.createFkController(
            thigh_bend_ctrls['midCtrl'], thigh_bend_parentproxy,
            ctrl, space,
            skipTranslate=True, skipRotate=True, skipScale=True,
        )
        bend_ctrls.append(ctrl)
        bend_ctrlspace.append(space)
        
        decmtx, mltmtx = func.createDecomposeMatrix(
            thigh_bend_ctrls['midCtrl'], [x + '.matrix' for x in (ctrl, space)]
        )
        mltmtx('matrixIn[2]',  space('inverseMatrix'), type='matrix')

        # Create knee and lowleg bend controller.
        for block_name, targets, parent in zip(
                ('Knee', 'Lowleg', 'Foot', 'Ball'),
                (
                    (
                        thigh_bend_ctrls['btmCtrl'],
                        lowleg_bend_ctrls['topCtrl']
                    ),
                    (
                        lowleg_bend_ctrls['midCtrl'],
                    ),
                    (
                        lowleg_bend_ctrls['btmCtrl'],
                        foot_bend_ctrls['topCtrl'],
                    ),
                    (
                        foot_bend_ctrls['midCtrl'],
                    )
                ),
                (
                    lowleg_bend_parentproxy, lowleg_bend_parentproxy,
                    foot_bend_parentproxy, foot_bend_parentproxy,
                )
            ):
            unitname.setName(basename + '%sBendCtrl' % block_name)
            unitname.setNodeType('ctrl')
            ctrl = unitname()

            unitname.setNodeType('ctrlSpace')
            space = unitname()
            
            ctrl, space = func.createFkController(
                targets[0], parent, ctrl, space,
                skipTranslate=True, skipRotate=True, skipScale=True,
            )
            bend_ctrls.append(ctrl)
            bend_ctrlspace.append(space)

            for target in targets:
                decmtx, mltmtx = func.createDecomposeMatrix(
                    target, [x + '.matrix' for x in (ctrl, space)]
                )
                mltmtx('matrixIn[2]',  space('inverseMatrix'), type='matrix')

        # Create blend controller twist connections.---------------------------
        for val, driver, ctrl in zip(
            (0.5, -0.5, 0.5),
            (thigh_agl_drv, foot_agl_drv, ball_agl_drv),
            (bend_ctrlspace[0], bend_ctrlspace[2], bend_ctrlspace[-1])
        ):
            mdl = node.createUtil('multDoubleLinear')
            mdl('input2', val)
            driver.attr('twistX') >> mdl/'input1'

            ctrl_rx_attr = ctrl.attr('rx')
            ctrl_rx_attr.setLock(False)
            mdl.attr('output') >> ctrl_rx_attr
            ctrl_rx_attr.setLock(True)
        func.lockTransform(bend_ctrls)
        func.controlChannels(
            bend_ctrls, ['t:a', 'r:a'], isKeyable=True, isLocked=False
        )
        # ---------------------------------------------------------------------        
        bend_vis_attr >> thigh_bend_parentproxy/'v'
        # ---------------------------------------------------------------------
        # =====================================================================
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////


        # /////////////////////////////////////////////////////////////////////
        # Connect proxy joints to original joints.                           //
        # /////////////////////////////////////////////////////////////////////
        proxy_joints  = [
            thigh_proxy, lowleg_proxy, foot_proxy, ball_proxy, toe_proxy
        ]
        origin_joints = [
            thigh_jnt, lowleg_jnt, foot_jnt, ball_jnt, toe_jnt
        ]
        for proxy, orig in zip(proxy_joints, origin_joints):
            func.connectKeyableAttr(proxy, orig)

        for proxy_list, orig_list in zip(
            (thigh_twist_proxies, lowleg_twist_proxies, foot_twist_proxies),
            (thigh_twists, lowleg_twists, foot_twists)
        ):
            for proxy, orig in zip(
                proxy_list, orig_list, 
            ):
                ~proxy.attr( 't') >> ~orig.attr('t')
                ~proxy.attr('r') >> ~orig.attr('r')
                func.fConnectAttr(proxy + '.sx', orig + '.sx')
                func.transferConnection(proxy + '.sy', orig + '.sy')
                func.transferConnection(proxy + '.sz', orig + '.sz')

        all_joints = [thigh_proxy]
        all_joints.extend(thigh_twists)
        all_joints.append(lowleg_proxy)
        all_joints.extend(lowleg_twists)
        all_joints.append(foot_proxy)
        all_joints.extend(foot_twists)
        all_joints.append(ball_proxy)
        length_ratios = func.listLengthRatio(all_joints)
        for j, r in zip(all_joints[:-1], length_ratios):
            r = func.math.sin(func.math.pi * r)
            md = j.attr('sy').source(type='multiplyDivide')
            src_plug = md.attr('input2Y').source(p=True)
            blender = node.createUtil('blendTwoAttr')
            blender('input[0]', 1)
            cmds.connectAttr(src_plug, blender + '.input[1]')
            blender('attributesBlender', r)
            cmds.connectAttr(blender/'output', md/'i2y', f=True)
            cmds.connectAttr(blender/'output', md/'i2z', f=True)
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////


        # /////////////////////////////////////////////////////////////////////
        # Setup parent proxy and blender nodes.                              //
        # /////////////////////////////////////////////////////////////////////
        parent_matrix = self.createParentMatrixNode(
            cmds.listRelatives(thigh_jnt, p=True, pa=True)[0]
        )
        decmtx = func.createDecomposeMatrix(
            parent_proxy, ['%s.matrixSum' % parent_matrix],
            withMultMatrix=False
        )[0]
        func.makeDecomposeMatrixConnection(
            decmtx, [ctrl_parent_proxy]
        )

        func.blendTransform(
            parent_proxy, None, [parent_blender, ikctrl_parent_proxy],
            '%s.world' % leg_ik_ctrl[''],
            skipScale=True
        )

        func.lockTransform(
            [
                parent_proxy, parent_blender,
                ctrl_parent_proxy, ikctrl_parent_proxy
            ]
        )
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////


        # /////////////////////////////////////////////////////////////////////
        # Add shapes to the all controllers.                                 //
        # /////////////////////////////////////////////////////////////////////
        # Adds shape to the bend controllers.----------------------------------
        size = thigh_to_foot.length() * 0.5
        creator = func.PrimitiveCreator()
        creator.setSize(size)
        creator.setColorIndex(self.colorIndex('special'))
        creator.setCurveType('crossArrow')
        creator.setRotation([0, 0, 90])
        for ctrl in bend_ctrls:
            creator.create(parentNode=ctrl)
        # ---------------------------------------------------------------------
        
        # Adds shape to the ik controllers.------------------------------------
        # Adds shape to the ik rotation controller.
        size *= 0.6
        creator.setSizes([size, size, size])
        creator.setRotation([0, 0, -90])
        creator.setCurveType('circleArrow')
        creator.setColorIndex(self.colorIndex('extra'))
        shape = creator.create(parentNode=ikrole_ctrl())
        if side == 3:
            shape.setRotate(180, 0, 0)
        creator.setRotation()
        
        # Adds shape to ik root controller to move a root of ik joint.
        size = thigh_to_foot.length() * 0.1
        creator.setSize(size)
        creator.create('box', legIkRoot_ctrl())

        # Adds shape to the sole rotation controller.
        size = foot_to_toe.length() * 0.1
        creator.setSize(size)
        creator.create('cross', toeroll_ik_ctrl['']())

        # Adds shape to the ik step and toe controller.
        size = foot_to_toe.length() * 0.5
        creator.setSize(size,)
        creator.setColorIndex(self.colorIndex('sub'))
        shape = creator.create('circle', step_ctrl['']())

        size *= 0.8
        creator.setSize(size)
        shape = creator.create('circle', toe_ik_ctrl['']())

        # Adds shape to the leg ik controller.
        size = heel_to_toe.length() * 1.25
        creator.setSize(size)
        creator.setTranslation(
            (heel_to_toe * 0.5) + heel_marker_vector - ball_vector
        )
        creator.setColorIndex(self.colorIndex('main'))
        shape_side = side_str if side_str in 'LR' else 'C'
        shape = creator.create('foot%s' % shape_side, leg_ik_ctrl['']())
        creator.setTranslation()

        # Adds shape to the foot ik controller.
        creator.setSize(ball_vector.length() * 0.25)
        creator.setColorIndex(self.colorIndex('extra'))
        shape = creator.create('sphere', ball_ik_ctrl['']())

        # Adds shape to the ik scaling controller.
        size = thigh_to_foot.length() * 0.2
        creator.setSize(size)
        creator.setColorIndex(16)
        creator.setRotation([0, 0, 90])
        for ctrl in ik_scale_ctrls:
            creator.create('scalePlane', ctrl)

        # Adds shape to the parameter controller.
        size = thigh_to_foot.length() * 0.1
        creator.setSizes([size, size, size])
        creator.setColorIndex(self.colorIndex('sub'))
        creator.setRotation([90, 0, 0])
        shape = creator.create('cross', param_ctrl)
        creator.setRotation()
        # ---------------------------------------------------------------------
        
        # Add shapes to the fk controllers.------------------------------------
        size = thigh_to_foot.length() * 0.1
        creator.setSizes([size, size, size])
        creator.setCurveType('sphere')
        creator.setColorIndex(self.colorIndex('key'))

        for fk_ctrl in fk_ctrls:
            shape = creator.create(parentNode=fk_ctrl)
        # ---------------------------------------------------------------------
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////
        
        
        # /////////////////////////////////////////////////////////////////////
        # Post precesses.                                                    //
        # /////////////////////////////////////////////////////////////////////
        # Blend ik joints and fk joints to the combined joints.
        for joint in [
            thigh_rigJnt, lowleg_rigJnt, foot_rigJnt, ball_rigJnt, toe_rigJnt
        ]:
            func.blendTransform(
                joint['fkJnt'], joint['ikJnt'], joint['combJnt'],
                '%s.ikBlend' % param_ctrl, blendMode=1
            )
        cmds.connectAttr(
            '%s.ikScalingController' % param_ctrl,
            '%s.v' % ik_scale_spaces[0]
        )
        

        rev_node = node.createUtil('reverse')
        cmds.connectAttr(
            '%s.ikBlend' % param_ctrl, '%s.inputX' % rev_node
        )
        cmds.connectAttr('%s.outputX' % rev_node, '%s.v' % thigh_fkroot)

        func.lockTransform(lockedlist)

        # Add controller to the anim set.======================================
        anim_set.addChild(
            [
                legIkRoot_ctrl, toeroll_ik_ctrl[''], step_ctrl[''],
                toe_ik_ctrl[''], leg_ik_ctrl[''], ball_ik_ctrl[''],
                ikrole_ctrl, param_ctrl
            ]
        )
        anim_set.addChild(bend_ctrls)
        
        anim_set.addChild(
            [thigh_fkCtrl, lowleg_fkCtrl, foot_fkCtrl, ball_fkCtrl, toe_fkCtrl]
        )
        
        anim_set.addChild(ik_scale_ctrls)
        # =====================================================================
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////