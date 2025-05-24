# -*- coding:utf-8 -*-
from ..tools import jointEditor
from .. import rigScripts, func, node, verutil
cmds = func.cmds

Category = 'Quads'

class Option(rigScripts.Option):
    r"""
        作成時に表示するUI用のクラス。
    """
    AttrList = ('numberOfUparm', 'numberOfLowarm')
    def define(self):
        for attr in self.AttrList:
            self.addIntOption(attr, default=3, min=1, max=26)

class JointCreator(rigScripts.JointCreator):
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
        
        if self.position() == 'R':
            xFactor = -1
        else:
            xFactor = 1

        # Creates joints.------------------------------------------------------
        # Uparm.
        name.setName('uparm')
        uparm = node.createNode('joint', n=name(), p=parent)
        uparm.setPosition((xFactor * 31, 75, 33))

        # Low Arm.
        name.setName('lowarm')
        lowarm = node.createNode('joint', n=name(), p=uparm)
        lowarm.setPosition((xFactor * 31, 45, 19))

        # Wrist.
        name.setName('wrist')
        wrist = node.createNode('joint', n=name(), p=lowarm)
        wrist.setPosition((xFactor * 31, 16, 23))

        # Wrist end.
        name.setName('wristEnd')
        wrist_end = node.createNode('joint', n=name(), p=wrist)
        wrist_end.setPosition((xFactor * 31, 8, 23))

        # Hand
        name.setName('hand')
        hand = node.createNode('joint', n=name(), p=wrist)
        hand.setPosition((xFactor * 31, 9, 36))

        # Hand  end.
        name.setName('handEnd')
        hand_end = node.createNode('joint', n=name(), p=hand)
        hand_end.setPosition((xFactor * 31, 9, 60))
        # ---------------------------------------------------------------------

        # Creates markers.-----------------------------------------------------
        name.setNodeType('marker')
        name.setName('handTip')
        handtip_marker = func.createLocator(n=name(), p='world_trs')
        handtip_marker.setPosition((xFactor * 31, 0, 61))
        
        name.setName('handEnd')
        handend_marker = func.createLocator(n=name(), p='world_trs')
        handend_marker.setPosition((xFactor * 31, 0, 12))
        # ---------------------------------------------------------------------

        # Fix orientation.-----------------------------------------------------
        om = jointEditor.OrientationModifier()
        om.setSecondaryMode('vector')
        if xFactor < 0:
            om.setPrimaryAxis('-X')
            om.setTargetUpAxis('-Z')
        else:
            om.setPrimaryAxis('+X')
            om.setTargetUpAxis('+Z')
        om.execute([uparm, lowarm, wrist, wrist_end, hand])

        if xFactor < 0:
            om.setTargetUpAxis('-Y')
        else:
            om.setTargetUpAxis('+Y')
        om.execute([hand, hand_end])
        # ---------------------------------------------------------------------

        # Unit setting.--------------------------------------------------------
        unit = self.unit()
        unit.addMember('uparm', uparm)
        unit.addMember('lowarm', lowarm)
        unit.addMember('wrist', wrist)
        unit.addMember('hand', hand)
        unit.addMember('handEnd', hand_end)
        unit.addMember('handtipMarker', handtip_marker)
        unit.addMember('handendMarker', handend_marker)
        # ---------------------------------------------------------------------
        
        self.asRoot(uparm)
        hand.select()

    def finalize(self):
        unit = self.unit()
        name = func.Name(unit())
        name.setSuffix(self.suffix())
        name.setNodeType('jnt')

        num_up = unit('numberOfUparm')
        num_low = unit('numberOfLowarm')

        lowarm = unit.getMember('lowarm')
        wrist = unit.getMember('wrist')

        uparmjoints = jointEditor.splitJoint(num_up, lowarm)[0]
        lowjoints = jointEditor.splitJoint(num_low, wrist)[0]
        charlist = list(verutil.LOWERCASE)
        for joints, key in zip(
                [uparmjoints, lowjoints],
                ['uparmTwst', 'lowarmTwst', 'wristTwst']
            ):
            for joint, char in zip(joints, charlist):
                name.setName('%s%s' % (key, char))
                cmds.rename(joint, name())


class RigCreator(rigScripts.RigCreator):
    def process(self):
        unit = self.unit()
        unitname = func.Name(self.unitName())
        basename = unitname.name()
        side = unit.position()
        anim_set = self.animSet()

        uparm_jnt = unit.getMember('uparm')
        lowarm_jnt = unit.getMember('lowarm')
        wrist_jnt = unit.getMember('wrist')
        hand_jnt = unit.getMember('hand')
        handend_jnt = unit.getMember('handEnd')
        handtip_marker = unit.getMember('handtipMarker')
        handend_marker = unit.getMember('handendMarker')

        # ポールベクターの方向を上腕と前腕のベクトルから取得する。
        uparm_vector = func.Vector(
            cmds.xform(uparm_jnt, q=True, ws=True, rp=True)
        )
        lowarm_vector = func.Vector(
            cmds.xform(lowarm_jnt, q=True, ws=True, rp=True)
        )
        wrist_vector = func.Vector(
            cmds.xform(wrist_jnt, q=True, ws=True, rp=True)
        )
        hand_vector = func.Vector(
            cmds.xform(handend_jnt, q=True, ws=True, rp=True)
        )
        handtip_marker_vector = func.Vector(
            cmds.xform(handtip_marker, q=True, ws=True, rp=True)
        )
        handend_marker_vector = func.Vector(
            cmds.xform(handend_marker, q=True, ws=True, rp=True)
        )
        heel_to_handtip = handtip_marker_vector - handend_marker_vector

        uparm_to_wrist = wrist_vector - uparm_vector
        wrist_to_hand = hand_vector - wrist_vector
        h = wrist_to_hand * uparm_to_wrist / uparm_to_wrist.length()
        pv_dir_vector = -wrist_to_hand - (uparm_to_wrist.norm() * h)

        # ルートノードを作成する。=============================================
        # リグ用の代理親ノードの作成。
        parent_proxy = self.createRigParentProxy(uparm_jnt, name=basename)
        
        # ikコントローラ用の代理親ノードの作成。
        ikctrl_parent_proxy = self.createCtrlParentProxy(
            uparm_jnt, basename+'Ik'
        )
        ctrl_parent_proxy = self.createCtrlParentProxy(uparm_jnt, basename)

        # ブレンドを行うための親ノードを作成。
        unitname.setName(basename + 'Ik')
        unitname.setNodeType('parentBlender')
        parent_blender = self.createParentProxy(uparm_jnt, name=unitname())
        # =====================================================================

        # リグ用のジョイントをオリジナルからコピーする。=======================
        # IK用、FK用、そして合成用のジョイントをオリジナルからコピー。---------
        uparm_rigJnt, lowarm_rigJnt, wrist_rigJnt, hand_rigJnt = {}, {}, {}, {}
        for key in ('ikJnt', 'fkJnt', 'combJnt'):
            uparm_rigJnt[key] = func.copyNode(
                uparm_jnt, key, parent_proxy
            )
            lowarm_rigJnt[key] = func.copyNode(
                lowarm_jnt, key, uparm_rigJnt[key]
            )
            wrist_rigJnt[key] = func.copyNode(
                wrist_jnt, key, lowarm_rigJnt[key]
            )
            hand_rigJnt[key] = func.copyNode(
                hand_jnt, key, wrist_rigJnt[key]
            )
        handend_rigJnt = {
            'ikJnt':func.copyNode(handend_jnt, 'ikJnt', hand_rigJnt['ikJnt'])
        }
        # ---------------------------------------------------------------------

        # ツイストの角度を取るためのangleDriverノードを作成。==================
        unitname.setName(basename + 'uparmAglDrv')
        unitname.setNodeType('trs')
        uparm_agl_drv = func.createAngleDriverNode(
            uparm_rigJnt['combJnt'], name=unitname(), parent=parent_proxy,
        )

        unitname.setName(basename + 'wristAglDrv')
        wrist_agl_drv = func.createAngleDriverNode(
            wrist_rigJnt['combJnt'], name=unitname(), parent=parent_proxy,
        )
        # ---------------------------------------------------------------------

        # 元のジョイントから代理ジョイントを作成する。=========================
        uparm_twists = func.listNodeChain(uparm_jnt, lowarm_jnt)[1:-1]
        lowarm_twists= func.listNodeChain(lowarm_jnt, wrist_jnt)[1:-1]

        uparm_twist_proxies = []
        lowarm_twist_proxies = []
        uparm_proxy = func.copyNode(uparm_jnt, 'jntProxy', parent_proxy)
        parent = uparm_proxy
        for uparm_joint in uparm_twists:
            uparm_twist_proxies.append(
                func.copyNode(uparm_joint, 'jntProxy', parent)
            )
            parent = uparm_twist_proxies[-1]

        lowarm_proxy = func.copyNode(lowarm_jnt, 'jntProxy', parent)
        parent = lowarm_proxy
        for lowarm_joint in lowarm_twists:
            lowarm_twist_proxies.append(
                func.copyNode(lowarm_joint, 'jntProxy', parent)
            )
            parent = lowarm_twist_proxies[-1]

        wrist_proxy = func.copyNode(wrist_jnt, 'jntProxy', parent)
        hand_proxy = func.copyNode(hand_jnt, 'jntProxy', wrist_proxy)
        # ---------------------------------------------------------------------
        
        # IKロール用のダミージョイントを作成する。=============================
        uparm_ikdmy = func.copyNode(uparm_jnt, 'ikDmy', parent_proxy)
        uparmend_ikdmy = func.copyNode(wrist_jnt, 'ikDmy', uparm_ikdmy)
        
        orientation_mod = jointEditor.OrientationModifier()
        orientation_mod.setPrimaryAxis(self.axisX())
        orientation_mod.execute([uparm_ikdmy, uparmend_ikdmy])
        # ---------------------------------------------------------------------
        # =====================================================================
        
        # コントローラとその代理ノードを作成する。=============================
        # Ik leg controller.
        arm_ik_ctrlspace = {}
        arm_ik_ctrl = {}

        # Movable rotation controller.
        handroll_ik_ctrlspace = {}
        handroll_ik_ctrl = {}
        sole_rev_space = {}

        # Heel rotation node.
        hand_rot_space = {}

        # Foot rotation controller.
        wrist_rot_space = {}
        wrist_rot_ctrl = {}

        step_ctrlspace = {}
        step_ctrl = {}
        hand_ik_ctrlspace = {}
        hand_ik_ctrl = {}

        for key, root_parent in zip(
                ['', 'Proxy'], [ikctrl_parent_proxy, parent_blender]
            ):
            # 足のスペーサーとコントローラ-------------------------------------
            unitname.setName(basename+'Ik')
            unitname.setNodeType('ctrlSpace' + key)
            arm_ik_ctrlspace[key] = node.createNode('transform', n=unitname())
            arm_ik_ctrlspace[key] = node.parent(
                arm_ik_ctrlspace[key], root_parent
            )[0]
            arm_ik_ctrlspace[key].fitTo(wrist_jnt, 0b1000)

            unitname.setNodeType('ctrl' + key)
            arm_ik_ctrl[key] = node.createNode(
                'transform', n=unitname(), p=arm_ik_ctrlspace[key]
            )
            func.lockTransform([arm_ik_ctrlspace[key], arm_ik_ctrl[key]])
            arm_ik_ctrl[key].editAttr(['t:a', 'r:a'], k=True, l=False)
            # -----------------------------------------------------------------

            # つま先の回転コントローラ。---------------------------------------
            unitname.setName(basename + 'ToeRotation')
            unitname.setNodeType('ctrlSpace' + key)
            handroll_ik_ctrlspace[key] = node.createNode(
                'transform', p=arm_ik_ctrl[key], n=unitname()
            )
            handroll_ik_ctrlspace[key].fitTo(handtip_marker, 0b1000)

            unitname.setNodeType('ctrl' + key)
            handroll_ik_ctrl[key] = node.createNode(
                'transform', p=handroll_ik_ctrlspace[key], n=unitname()
            )
            func.lockTransform(
                [handroll_ik_ctrlspace[key], handroll_ik_ctrl[key]]
            )
            handroll_ik_ctrl[key].editAttr(['t:a', 'r:a'], k=True, l=False)
            # -----------------------------------------------------------------

            # 足の裏の移動相殺機能。-------------------------------------------
            unitname.setName(basename + 'SoleRev')
            unitname.setNodeType('trs' + key)
            sole_rev_space[key] = node.createNode(
                'transform', p=handroll_ik_ctrl[key], n=unitname()
            )
            sole_rev_space[key].lockTransform()
            sole_rev_space[key].editAttr(['t:a'], k=True, l=False)
            # -----------------------------------------------------------------

            # 踵の自動回転機能。-----------------------------------------------
            unitname.setName(basename + 'HeelRotation')
            hand_rot_space[key] = node.createNode(
                'transform', p=sole_rev_space[key], n=unitname()
            )
            hand_rot_space[key].fitTo(handend_marker, 0b1000)
            hand_rot_space[key].lockTransform()
            hand_rot_space[key].editAttr(['r:a'], k=True, l=False)
            # -----------------------------------------------------------------
            
            # 手首の回転コントローラ。------------------------------------------
            unitname.setName(basename + 'Rot')
            unitname.setNodeType('ctrlSpace' + key)
            wrist_rot_space[key] = node.createNode(
                'transform', n=unitname(), p=hand_rot_space[key]
            )
            wrist_rot_space[key].fitTo(arm_ik_ctrl[key])

            unitname.setNodeType('ctrl' + key)
            wrist_rot_ctrl[key] = node.createNode(
                'transform', n=unitname(), p=wrist_rot_space[key]
            )
            func.lockTransform([wrist_rot_space[key], wrist_rot_ctrl[key]])
            wrist_rot_ctrl[key].editAttr(['r:a'], k=True, l=False)
            # -----------------------------------------------------------------

            # 踏み込み用コントローラとその代理ノード。-------------------------
            unitname.setName(basename + 'Step')
            unitname.setNodeType('ctrlSpace' + key)
            step_ctrlspace[key] = node.createNode(
                'transform',  n=unitname(), p=wrist_rot_ctrl[key]
            )
            step_ctrlspace[key].fitTo(hand_jnt)

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
            hand_ik_ctrlspace[key] = node.createNode(
                'transform',  n=unitname(), p=wrist_rot_ctrl[key]
            )
            hand_ik_ctrlspace[key].fitTo(hand_jnt)

            unitname.setNodeType('ctrl' + key)
            hand_ik_ctrl[key] = node.createNode(
                'transform', n=unitname(), p=hand_ik_ctrlspace[key]
            )
            func.lockTransform([hand_ik_ctrlspace[key], hand_ik_ctrl[key]])
            hand_ik_ctrl[key].editAttr(['r:a'], k=True, l=False)
            # -----------------------------------------------------------------

        stretch_plug = arm_ik_ctrl[''].addFloatAttr('stretch', default=0)
        softik_plug =  arm_ik_ctrl[''].addFloatAttr(
            'softIk', min=0, max=100, default=0, smx=1
        )
        world_plug = arm_ik_ctrl[''].addFloatAttr('world', default=1)

        # IKシステムの構築。---------------------------------------------------
        # 足の裏の移動相殺機能のセットアップ。
        md = node.createUtil('multiplyDivide')
        for axis in self.Axises:
            axis = axis.lower()
            handroll_ik_ctrl['Proxy'].attr('t'+axis) >> '%s.i1%s'%(md, axis)
            md('i2'+axis, -1)
            md.attr('o'+axis) >> '%s.t%s'%(sole_rev_space['Proxy'], axis)
        # ---------------------------------------------------------------------
            
        # コントローラから内裏ノードへの接続を行う。---------------------------
        for couple in (
            arm_ik_ctrl, handroll_ik_ctrl, hand_ik_ctrl, step_ctrl,
            wrist_rot_ctrl
        ):
            func.connectKeyableAttr(couple[''], couple['Proxy'])

        for couple in (
            sole_rev_space, hand_rot_space
        ):
            func.connectKeyableAttr(couple['Proxy'], couple[''])

        step_rot_attr = step_ctrl[''].attr('ry')
        cndt = node.createUtil('condition')
        cndt('operation', 2)
        cndt('secondTerm', 0)
        cndt('colorIfFalseR', 0)
        cndt('colorIfTrueG', 0)
        step_rot_attr >> cndt/'firstTerm'
        step_rot_attr >> cndt/'colorIfTrueR'
        step_rot_attr >> cndt/'colorIfFalseG'

        heelrot_plug = step_ctrl[''].addFloatAttr('useHeelRotation', default=0)
        step_blenders = []
        for i in range(2):
            step_blenders.append(node.createUtil('blendTwoAttr'))
            heelrot_plug >> step_blenders[-1]/'attributesBlender'
        step_rot_attr >> step_blenders[0]/'input[0]'
        cndt.attr('outColorR') >> step_blenders[0]/'input[1]'
        step_blenders[0].attr('o') >> step_ctrl['Proxy']/'ry'

        step_blenders[1]('input[0]', 0)
        cndt.attr('outColorG') >> step_blenders[1]/'input[1]'
        step_blenders[1].attr('o') >> hand_rot_space['Proxy']/'rx'
        # ---------------------------------------------------------------------
        # =====================================================================

        # /////////////////////////////////////////////////////////////////////
        # IKコントローラとシステムを作成する。                               //
        # /////////////////////////////////////////////////////////////////////
        # IKシステムの構築。===================================================
        unitname.setNodeType('ik')
        # For the toe ik system.
        unitname.setName(basename + 'Hand')
        hand_ik = cmds.ikHandle(n=unitname(),
            sj=hand_rigJnt['ikJnt'], ee=handend_rigJnt['ikJnt'],
            sol='ikSCsolver'
        )[0]
        hand_ik = node.parent(hand_ik, hand_ik_ctrl['Proxy'])[0]

        # For the leg ik system.
        unitname.setName(basename + 'Arm')
        arm_ik = node.ikHandle(n=unitname(),
            sj=uparm_rigJnt['ikJnt'], ee=wrist_rigJnt['ikJnt'], sol='ikRPsolver'
        )[0]
        
        unitname.setName(basename + 'Wrist')
        wrist_ik = cmds.ikHandle(n=unitname(),
            sj=wrist_rigJnt['ikJnt'], ee=hand_rigJnt['ikJnt'], sol='ikRPsolver'
        )[0]
        wrist_ik = node.parent(wrist_ik, step_ctrl['Proxy'])[0]
        
        unitname.setName(basename + 'ArmDmy')
        arm_dmyik = cmds.ikHandle(n=unitname(),
            sj=uparm_ikdmy, ee=uparmend_ikdmy, sol='ikSCsolver'
        )[0]
        arm_dmyik = node.parent(arm_dmyik, wrist_rot_space['Proxy'])[0]

        unitname.setName(basename+'IkPos')
        unitname.setNodeType('pos')
        arm_ik_pos = node.createNode(
            'transform', n=unitname(), p=step_ctrl['Proxy']
        )
        arm_ik_pos.fitTo(arm_ik)
        arm_ik = node.parent(arm_ik, arm_ik_pos)[0]
        # =====================================================================
        
        # ストレッチシステムの構築。===========================================
        result_node = func.createScaleStretchSystem(
            uparm_rigJnt['ikJnt'], wrist_rigJnt['ikJnt']
        )
        unitname.setNodeType('loc')
        unitname.setName(basename + 'Start')
        start_loc = unitname()
        
        unitname.setName(basename + 'End')
        end_loc = unitname()

        unitname.setName(basename + 'RotationSetup')
        unitname.setNodeType('grp')
        dist_node = unitname()

        start_loc = node.parent(
            cmds.rename(result_node['start'], start_loc), parent_proxy
        )[0]
        end_loc = node.parent(
            cmds.rename(result_node['end'], end_loc), step_ctrl['Proxy']
        )[0]
        dist_node = node.parent(
            cmds.rename(result_node['result'], dist_node), uparm_ikdmy
        )[0]

        arm_ik_ctrl[''].attr('stretch') >> dist_node/'stretch'
        # =====================================================================

        # ソフトIKシステムを構築する。=========================================
        cmds.aimConstraint(
            start_loc, arm_ik_pos,
            aimVector=[1, 0, 0], upVector=[0, 1, 0], worldUpType='none'
        )
        self.addLockedList(arm_ik_pos)
        func.createSoftIkFromStretchNode(
            arm_ik_ctrl['']/'softIk', dist_node, arm_ik
        )
        # =====================================================================

        # 自動ポールベクター追従システムの作成。===============================
        # システムの作成。-----------------------------------------------------
        unitname.setName(basename + 'IkPv')
        unitname.setNodeType('trs')

        ik_roll_ctrlproxy = cmds.pointConstraint(
            start_loc, end_loc, dist_node
        )[0]
        cmds.setAttr('%s.r' % dist_node, 0, 0, 0)

        cst_vector = func.Vector(
            cmds.xform(ik_roll_ctrlproxy, q=True, ws=True, rp=True)
        )
        pv_pos = cst_vector + pv_dir_vector

        pv_locator = node.createNode(
            'transform', n=unitname(), p=ik_roll_ctrlproxy
        )
        pv_locator.setPosition((pv_pos.x, pv_pos.y, pv_pos.z))
        self.addLockedList(pv_locator)

        cmds.poleVectorConstraint(pv_locator, arm_ik)
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
            x + '.matrix' for x in [dist_node, uparm_ikdmy, parent_proxy]
        ]
        inputMatrices.append(ikctrl_parent_proxy + '.inverseMatrix')
        decmtx, mltmtx = func.createDecomposeMatrix(
            ikrole_ctrlspace, inputMatrices
        )
        self.addLockedList(ikrole_ctrlspace)
        func.connectKeyableAttr(ikrole_ctrl, ik_roll_ctrlproxy)
        # ---------------------------------------------------------------------
        # =====================================================================

        # IKスケール用コントローラの作成。=====================================
        parent = ctrl_parent_proxy
        ik_scale_spaces = []
        ik_scale_ctrls = []
        for part in [uparm_rigJnt, lowarm_rigJnt, wrist_rigJnt, hand_rigJnt]:
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

            input = node.listConnections(
                part['ikJnt']/'sx', s=True, d=False, p=True
            )
            if not input:
                sx_plug = ctrl.attr('sx')
            else:
                input = input[0]
                # Reconnect scaleX of the ik joint.
                mdl = node.createUtil('multDoubleLinear')
                input >> (mdl/'input1', space/'sx')
                ctrl.attr('sx') >> mdl/'input2'
                sx_plug = mdl.attr('output')

            sx_plug >> part['ikJnt']/'sx'
            ctrl.attr('sy') >> part['ikJnt']/'sy'
            ctrl.attr('sz') >> part['ikJnt']/'sz'

            func.lockTransform([space, ctrl])
            ctrl.editAttr(['s:a'], k=True, l=False)

        for ax in func.Axis:
            scale_attr = arm_ik_ctrl[''].attr('s'+ax)
            scale_attr.setLock(False)
            arm_ik_ctrl['Proxy'].attr('s'+ax) >> arm_ik_ctrl[''].attr('s'+ax)
            scale_attr.setLock(True)
            
            scale_attr = arm_ik_ctrl['Proxy'].attr('s'+ax)
            scale_attr.setLock(False)
            ik_scale_ctrls[-2].attr('s'+ax) >> arm_ik_ctrl['Proxy'].attr('s'+ax)
            scale_attr.setLock(True)
        # =====================================================================
        
        # IKのルートコントローラを作成する。===================================
        unitname.setName(basename + 'IkRoot')
        unitname.setNodeType('ctrl')
        armIkRoot_ctrl = unitname()
        
        unitname.setNodeType('ctrlSpace')
        armIkRoot_space = unitname()
        armIkRoot_ctrl, armIkRoot_space = func.createFkController(
            target=uparm_rigJnt['ikJnt'], parent=ctrl_parent_proxy,
            name=armIkRoot_ctrl, spaceName=armIkRoot_space,
            skipTranslate=False, skipRotate=True, skipScale=True,
            isLockTransform=True
        )
        armIkRoot_ctrl.lockTransform()
        armIkRoot_ctrl.editAttr(['t:a'], k=True, l=False)
        pmm = armIkRoot_ctrl.attr('tx').destinations()[0]
        for n in [uparm_ikdmy, start_loc]:
            ~pmm.attr('o') >> ~n.attr('t')
        # ---------------------------------------------------------------------
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////


        # /////////////////////////////////////////////////////////////////////
        # FKコントローラの作成。                                             //
        # /////////////////////////////////////////////////////////////////////
        unitname.setName(basename + 'UparmFK')
        unitname.setNodeType('ctrl')
        uparm_fkCtrl = unitname()

        # A fk controller for the thigh.---------------------------------------
        unitname.setNodeType('ctrlSpace')
        uparm_fkroot = unitname()
        uparm_fkCtrl, uparm_fkroot = func.createFkController(
            uparm_rigJnt['fkJnt'], ctrl_parent_proxy,
            uparm_fkCtrl, uparm_fkroot, skipTranslate=False,
            isLockTransform=False, calculateWithSpace=True
        )
        world_plug = uparm_fkCtrl.addFloatAttr('world', 0, 1, 0)

        ctrl_space = uparm_fkCtrl.parent()
        mltmtx = node.createUtil('multMatrix')
        mltmtx('matrixIn[0]', ctrl_space.matrix(), type='matrix')
        ctrl_parent_proxy.attr('im') >> mltmtx/'matrixIn[1]'
        decmtx = node.createUtil('decomposeMatrix')
        mltmtx.attr('matrixSum') >> decmtx/'inputMatrix'

        ~decmtx.attr('or') >> ~ctrl_space.attr('r')
        func.blendSelfConnection(
            ctrl_space, blendControlAttr=uparm_fkCtrl+'.world',
            skipTranslate=True, skipScale=True, blendMode=1
        )
        self.addLockedList(ctrl_space)
        # ---------------------------------------------------------------------

        # A fk controller for the lowleg.
        unitname.setName(basename + 'LowarmFk')
        unitname.setNodeType('ctrlSpace')
        fk_ctrlspace = unitname()
        
        unitname.setNodeType('ctrl')
        lowarm_fkCtrl = func.createFkController(
            lowarm_rigJnt['fkJnt'], uparm_fkCtrl, unitname(), fk_ctrlspace,
            skipTranslate=False
        )[0]
        
        # A fk controller for the wrist.
        unitname.setName(basename + 'WristFk')
        unitname.setNodeType('ctrlSpace')
        fk_ctrlspace = unitname()
        
        unitname.setNodeType('ctrl')
        wrist_fkCtrl = func.createFkController(
            wrist_rigJnt['fkJnt'], lowarm_fkCtrl, unitname(), fk_ctrlspace,
            skipTranslate=False
        )[0]
        
        # Adds ik/fk switch target.
        unitname.setName(basename + 'IkFkSwitchTgt')
        target = node.createNode(
            'transform', n=unitname(), p=wrist_rigJnt['fkJnt']
        )
        target.fitTo(arm_ik_ctrl[''])
        target.lockTransform()
        cmds.addAttr(arm_ik_ctrl[''], ln='ikFkSwitchTarget', at='message')
        target.attr('message') >> arm_ik_ctrl['']/'ikFkSwitchTarget'

        # A fk controller for the toe.
        unitname.setName(basename + 'HandFk')
        unitname.setNodeType('ctrlSpace')
        fk_ctrlspace = unitname()
        
        unitname.setNodeType('ctrl')
        hand_fkCtrl = func.createFkController(
            hand_rigJnt['fkJnt'], wrist_fkCtrl, unitname(), fk_ctrlspace,
            skipTranslate=False
        )[0]

        controllers = [lowarm_fkCtrl, wrist_fkCtrl, hand_fkCtrl]
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
        param_ctrl.lockTransform(l=False)
        ikblend_plug = param_ctrl.addFloatAttr('ikBlend', default=1)
        scale_vis_plug = param_ctrl.addDisplayAttr(
            'ikScalingController', default=False, cb=True
        )
        bendvis_plug = param_ctrl.addDisplayAttr(
            'bendCtrlVisibility', default=False, cb=True
        )
        up_keep_plug = param_ctrl.addFloatAttr(
            'upKeepVolume', default=0, min=-2, max=2, smn=-1, smx=1
        )
        low_keep_plug = param_ctrl.addFloatAttr(
            'lowKeepVolume', default=0, min=-2, max=2, smn=-1, smx=1
        )

        if side == 'L':
            horizontalVector = (
                (pv_pos - wrist_vector) ** (cst_vector - wrist_vector)
            )
        else:
            horizontalVector = (
                (cst_vector - wrist_vector) ** (pv_pos - wrist_vector)
            )
            
        param_ctrl_vector = (
            horizontalVector.norm()
            * uparm_to_wrist.length() * 0.35
            + cst_vector
        )
        param_ctrl.setPosition(
            (param_ctrl_vector.x, param_ctrl_vector.y, param_ctrl_vector.z)
        )
        # Connects visibility from the ikBlend attr to the ik controllers
        # and the fk controllers.
        ikblend_plug >> [
            x/'v' for x in [arm_ik_ctrlspace[''], ikrole_ctrl, armIkRoot_space]
        ]
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////



        # /////////////////////////////////////////////////////////////////////
        # Connects combined joints to proxy joints.                          //
        # /////////////////////////////////////////////////////////////////////
        # Adds bend controller to the thigh and the lowleg joint chain.
        # (After finish this process, the proxy joints will be connected
        # from a combined joints.)
        uparm_bend_ctrls = func.createBendTwistControl(
            uparm_rigJnt['combJnt'], lowarm_rigJnt['combJnt'],
            uparm_proxy, lowarm_proxy, uparm_ikdmy, aimVector=self.vectorX()
        )
        up_keep_plug >> uparm_bend_ctrls['scaleInfo']/'volumeScale'
        lowarm_bend_ctrls = func.createBendTwistControl(
            lowarm_rigJnt['combJnt'], wrist_rigJnt['combJnt'],
            lowarm_proxy, wrist_proxy, lowarm_rigJnt['combJnt'],
            False, self.vectorX()
        )
        low_keep_plug >> lowarm_bend_ctrls['scaleInfo']/'volumeScale'

        # Connects the wrist joint from combined to proxy.----------------------
        unitname.setName(basename + 'WristProxy')
        unitname.setNodeType('ik')
        wrist_ik = cmds.ikHandle(
            sj=wrist_proxy, ee=hand_proxy, sol='ikRPsolver'
        )
        wrist_ik = node.rename(
            cmds.parent(wrist_ik[0], wrist_rigJnt['combJnt'])[0],
            unitname()
        )

        unitname.setNodeType('ikPv')
        ik_pv = func.createPoleVector([wrist_ik])[0]
        cmds.rename(
            cmds.parent(ik_pv, wrist_rigJnt['combJnt'])[0],
            unitname()
        )
        ~wrist_rigJnt['combJnt'].attr('s') >> ~wrist_proxy.attr('s')
        # ---------------------------------------------------------------------
        
        # Connects the toe joint from combined to proxy.
        func.connectKeyableAttr(hand_rigJnt['combJnt'], hand_proxy)
        
        # Creates controller to control a bend system.=========================
        # Create parent proxy for bend controllers.----------------------------
        unitname.setName(basename + 'UparmBendCtrl')
        unitname.setNodeType('parentProxy')
        uparm_bend_parentproxy = func.createSpaceNode(
            n=unitname(), p=ctrl_parent_proxy
        )
        func.connectKeyableAttr(
            uparm_rigJnt['combJnt'], uparm_bend_parentproxy
        )
        (
            ~uparm_rigJnt['combJnt'].attr('jo')
            >> ~uparm_bend_parentproxy.attr('jo')
        )
        
        unitname.setName(basename + 'LowarmBendCtrl')
        lowarm_bend_parentproxy = func.createSpaceNode(
            n=unitname(), p=uparm_bend_parentproxy
        )
        func.connectKeyableAttr(
            lowarm_rigJnt['combJnt'], lowarm_bend_parentproxy
        )
        (
            ~lowarm_rigJnt['combJnt'].attr('jo')
            >> ~lowarm_bend_parentproxy.attr('jo')
        )
        self.addLockedList([uparm_bend_parentproxy, lowarm_bend_parentproxy])
        # ---------------------------------------------------------------------

        # Create bend controllers.---------------------------------------------
        bend_ctrls = []
        bend_ctrlspace = []

        # Create thigh bend controller.
        unitname.setName(basename + 'UparmBendCtrl')
        unitname.setNodeType('ctrl')
        ctrl = unitname()
        
        unitname.setNodeType('ctrlSpace')
        space = unitname()
    
        ctrl, space = func.createFkController(
            uparm_bend_ctrls['midCtrl'], uparm_bend_parentproxy,
            ctrl, space,
            skipTranslate=True, skipRotate=True, skipScale=True,
        )
        bend_ctrls.append(ctrl)
        bend_ctrlspace.append(space)

        decmtx, mltmtx = func.createDecomposeMatrix(
            uparm_bend_ctrls['midCtrl'], [x + '.matrix' for x in (ctrl, space)]
        )
        mltmtx('matrixIn[2]', space('im'), type='matrix')

        # Create knee and lowleg bend controller.
        for block_name, targets in zip(
                ['Knee', 'Lowleg'],
                [
                    [
                        uparm_bend_ctrls['btmCtrl'],
                        lowarm_bend_ctrls['topCtrl']
                    ],
                    [
                        lowarm_bend_ctrls['midCtrl']
                    ]
                ]
            ):
            unitname.setName(basename + '%sBendCtrl' % block_name)
            unitname.setNodeType('ctrl')
            ctrl = unitname()

            unitname.setNodeType('ctrlSpace')
            space = unitname()
            
            ctrl, space = func.createFkController(
                targets[0], lowarm_bend_parentproxy,
                ctrl, space,
                skipTranslate=True, skipRotate=True, skipScale=True,
            )
            bend_ctrls.append(ctrl)
            bend_ctrlspace.append(space)

            for target in targets:
                decmtx, mltmtx = func.createDecomposeMatrix(
                    target, [x + '.matrix' for x in (ctrl, space)]
                )
                mltmtx('matrixIn[2]', space('im'), type='matrix')

        # Create blend controller twist connections.---------------------------
        for val, driver, ctrl in zip(
            (0.5, -0.5),
            (uparm_agl_drv, wrist_agl_drv),
            (bend_ctrlspace[0], bend_ctrlspace[-1])
        ):
            mdl = func.createUtil('multDoubleLinear')
            cmds.setAttr(mdl + '.input2', val)
            cmds.connectAttr(driver + '.twistX', mdl + '.input1')
            func.fConnectAttr(mdl + '.output', ctrl + '.rx')
        # ---------------------------------------------------------------------

        func.lockTransform(bend_ctrls)
        func.controlChannels(
            bend_ctrls, ['t:a', 'r:a'], isKeyable=True, isLocked=False
        )
        
        bendvis_plug >> uparm_bend_parentproxy/'v'
        # ---------------------------------------------------------------------
        # =====================================================================
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////


        # /////////////////////////////////////////////////////////////////////
        # Connect proxy joints to original joints.                           //
        # /////////////////////////////////////////////////////////////////////
        proxy_joints  = [uparm_proxy, lowarm_proxy, wrist_proxy, hand_proxy]
        origin_joints = [uparm_jnt, lowarm_jnt, wrist_jnt, hand_jnt]
        for proxy, orig in zip(proxy_joints, origin_joints):
            func.connectKeyableAttr(proxy, orig)

        for proxy_list, orig_list in zip(
            (uparm_twist_proxies, lowarm_twist_proxies),
            (uparm_twists, lowarm_twists)
        ):
            for proxy, orig in zip(
                proxy_list, orig_list, 
            ):
                ~proxy.attr('t') >> ~orig.attr('t')
                ~proxy.attr('r') >> ~orig.attr('r')
                proxy.attr('sx') >> orig.attr('sx')
                func.transferConnection(proxy + '.sy', orig + '.sy')
                func.transferConnection(proxy + '.sz', orig + '.sz')

        all_joints = [uparm_proxy]
        all_joints.extend(uparm_twists)
        all_joints.append(lowarm_proxy)
        all_joints.extend(lowarm_twists)
        all_joints.append(wrist_proxy)
        length_ratios = func.listLengthRatio(all_joints)
        for j, r in zip(all_joints[:-1], length_ratios):
            r = func.math.sin(func.math.pi * r)
            md = node.listConnections(
                j + '.sy', s=True, d=False, type='multiplyDivide'
            )[0]
            src_plug = md.attr('input2Y').source(p=True)
            blender = node.createUtil('blendTwoAttr')
            blender('input[0]', 1)
            src_plug >> blender/'input[1]'
            blender('attributesBlender', r)
            blender.attr('output') >> (md/'i2y', md/'i2z')
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////


        # /////////////////////////////////////////////////////////////////////
        # Setup parent proxy and blender nodes.                              //
        # /////////////////////////////////////////////////////////////////////
        parent_matrix = self.createParentMatrixNode(
            cmds.listRelatives(uparm_jnt, p=True, pa=True)[0]
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
            '%s.world' % arm_ik_ctrl[''],
            skipScale=True
        )
        self.addLockedList(
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
        size = uparm_to_wrist.length() * 0.5
        creator = func.PrimitiveCreator()
        creator.setSizes([size, size, size])
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
        shape = creator.create(parentNode=ikrole_ctrl)
        if side == 'R':
            shape.setRotate(180, 0, 0)
        creator.setRotation()
        
        # Adds shape to ik root controller to move a root of ik joint.
        size = uparm_to_wrist.length() * 0.1
        creator.setSize(size)
        creator.create('box', armIkRoot_ctrl)

        # Adds shape to the sole rotation controller.
        size = wrist_to_hand.length() * 0.1
        creator.setSizes([size, size, size])
        creator.create('cross', handroll_ik_ctrl[''])

        # Adds shape to the ik step and toe controller.
        size = wrist_to_hand.length() * 0.5
        creator.setSizes([size, size, size])
        creator.setColorIndex(self.colorIndex('sub'))
        shape = creator.create('circle', step_ctrl[''])

        size *= 0.8
        creator.setSizes([size, size, size])
        shape = creator.create('circle', hand_ik_ctrl[''])

        # Adds shape to the leg ik controller.
        size = heel_to_handtip.length() * 1.25
        creator.setSize(size)
        creator.setTranslation(
            (heel_to_handtip * 0.5) + handend_marker_vector - wrist_vector
        )
        creator.setColorIndex(self.colorIndex('main'))
        shape = creator.create('foot%s' % side, arm_ik_ctrl[''])
        creator.setTranslation()

        # Adds shape to the ik scaling controller.
        size = uparm_to_wrist.length() * 0.2
        creator.setSizes([size, size, size])
        creator.setColorIndex(16)
        creator.setRotation([0, 0, 90])
        for ctrl in ik_scale_ctrls:
            creator.create('scalePlane', ctrl)
        
        size *= 0.5
        creator.setSizes([size, size, size])
        creator.setColorIndex(self.colorIndex('sub'))
        shape = creator.create('circle', wrist_rot_ctrl[''])

        # Adds shape to the parameter controller.
        size = uparm_to_wrist.length() * 0.1
        creator.setSizes([size, size, size])
        creator.setRotation([90, 0, 0])
        shape = creator.create('cross', param_ctrl)
        creator.setRotation()
        # ---------------------------------------------------------------------
        
        # Add shapes to the fk controllers.------------------------------------
        size = uparm_to_wrist.length() * 0.1
        creator.setSizes([size, size, size])
        creator.setCurveType('sphere')
        creator.setColorIndex(self.colorIndex('key'))

        for fk_ctrl in [uparm_fkCtrl, lowarm_fkCtrl, wrist_fkCtrl, hand_fkCtrl]:
            shape = creator.create(parentNode=fk_ctrl)
        # ---------------------------------------------------------------------
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////
        
        
        
        # /////////////////////////////////////////////////////////////////////
        # Post precesses.                                                    //
        # /////////////////////////////////////////////////////////////////////
        # Blend ik joints and fk joints to the combined joints.
        for joint in [uparm_rigJnt, lowarm_rigJnt, wrist_rigJnt, hand_rigJnt]:
            func.blendTransform(
                joint['fkJnt'], joint['ikJnt'], joint['combJnt'],
                '%s.ikBlend' % param_ctrl, blendMode=1
            )
        scale_vis_plug >> ik_scale_spaces[0]/'v'

        rev_node = node.createUtil('reverse')
        ikblend_plug >> rev_node/'inputX'
        rev_node.attr('outputX') >> uparm_fkroot/'v'

        # Add controller to the anim set.======================================
        anim_set.addChild(
            [
                armIkRoot_ctrl, handroll_ik_ctrl[''], step_ctrl[''],
                hand_ik_ctrl[''], arm_ik_ctrl[''], wrist_rot_ctrl[''],
                ikrole_ctrl, param_ctrl
            ]
        )
        anim_set.addChild(bend_ctrls)
        
        anim_set.addChild(
            [uparm_fkCtrl, lowarm_fkCtrl, wrist_fkCtrl, hand_fkCtrl]
        )
        
        anim_set.addChild(ik_scale_ctrls)
        # =====================================================================
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////