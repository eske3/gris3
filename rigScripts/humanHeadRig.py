# -*- coding:utf-8 -*-
r'''
    @file     unityHeadRig.py
    @brief    UNITY用の頭部を作成するための機能を提供するモジュール。
    @class    JointCreator : ここに説明文を記入
    @class    RigCreator : ここに説明文を記入
    @date        2017/02/01 1:04[Eske](eske3g@gmail.com)
    @update      2017/02/01 1:04[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
import string

from ..tools import jointEditor
from .. import rigScripts, node, verutil
func = rigScripts.func
cmds = func.cmds

Category = 'Basic Human'
BaseName = 'head'

class Option(rigScripts.Option):
    r'''
        @brief       作成時に表示するUI用のクラス。
        @inheritance rigScripts.Option
        @date        2017/02/04 18:52[Eske](eske3g@gmail.com)
        @update      2017/07/01 1:26[Eske](eske3g@gmail.com)
    '''
    def define(self):
        r'''
            @brief  オプション内容を定義する
            @return None
        '''
        self.addBoolOption('bendCtrl', True)
        self.addIntOption('numberOfJoints', default=3, min=1, max=26)

class JointCreator(rigScripts.JointCreator):
    r'''
        @brief       頭部のジョイント作成機能を提供するクラス。
        @inheritance rigScripts.JointCreator
        @date        2017/02/01 1:04[Eske](eske3g@gmail.com)
        @update      2017/02/01 1:04[Eske](eske3g@gmail.com)
    '''
    def createUnit(self):
        super(JointCreator, self).createUnit()
        unit = self.unit()
        options = self.options()
        unit.addBoolAttr('bendCtrl', options.get('bendCtrl', True))
        unit.addIntAttr(
            'numberOfJoints', default=options.get('numberOfJoints', 3),
            min=1, max=26
        )

    def process(self):
        r'''
            @brief  ジョイント作成プロセスとしてコールされる。
            @return None
        '''
        name = self.basenameObject()
        parent = self.parent()

        # Neck joint.
        name.setName('neck')
        neck = node.createNode('joint', n=name(), p=parent)
        neck.setPosition((-0.0, 156.8, -2.5))
        neck.setRadius(1.5)

        # Head.
        name.setName('head')
        head = node.createNode('joint', n=name(), p=neck)
        head.setPosition((-0.0, 168.8, -0.2))
        head.setRadius(2)

        # Head end.
        name.setName('headEnd')
        headEnd = node.createNode('joint', n=name(), p=head)
        headEnd.setPosition((-0.0, 186.8, -0.2))

        # Fix joint orient.
        om = jointEditor.OrientationModifier()
        om.setSecondaryMode('vector')
        om.setApplyToChildren(False)
        om.setTargetUpAxis('-Z')
        om.execute((neck, head, headEnd))

        # Unit setting.--------------------------------------------------------
        unit = self.unit()
        unit.addMember('neck', neck)
        unit.addMember('head', head)
        unit.addMember('headEnd', headEnd)
        # ---------------------------------------------------------------------
        
        self.asRoot(neck)
        head.select()

    def finalize(self):
        r'''
            @brief  ジョイントのファイナライズ時にコールされる。
            @return None
        '''
        unit = self.unit()
        if_bent = unit('bendCtrl') if unit.hasAttr('bendCtrl') else True
        if not if_bent:
            return
        name = func.Name(unit())
        name.setSuffix(self.suffix())
        name.setNodeType('jnt')
        num = unit('numberOfJoints') if unit.hasAttr('numberOfJoints') else 3

        neck = unit.getMember('neck')
        head = unit.getMember('head')
        length = (
            node.MVector(head.position()) - node.MVector(neck.position())
        ).length() * 0.125

        joints = jointEditor.splitJoint(num, head)[0]
        for joint, char in zip(joints, verutil.LOWERCASE):
            name.setName('neckTwst%s' % char)
            joint.setRadius(length)
            joint.rename(name())

class RigCreator(rigScripts.RigCreator):
    r'''
        @brief       ここに説明文を記入
        @inheritance rigScripts.RigCreator
        @date        2017/02/01 1:04[Eske](eske3g@gmail.com)
        @update      2017/02/01 1:04[Eske](eske3g@gmail.com)
    '''
    def process(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        unit = self.unit()
        unitname = self.unitName()
        basename = unitname.name()
        side = unit.positionIndex()
        anim_set = self.animSet()
        # 過去バージョンへの対策用。
        is_bent = unit('bendCtrl') if unit.hasAttr('bendCtrl') else True

        neck_jnt = unit.getMember('neck')
        head_jnt = unit.getMember('head')
        headend_jnt = unit.getMember('headEnd')
        neck_chain = func.listNodeChain(neck_jnt, head_jnt)
        necks_jnt = neck_chain[1:-1]

        # ---------------------------------------------------------------------
        start_vector = func.Vector(neck_jnt.position())
        end_vector = func.Vector(head_jnt.position())
        head_end_vector = func.Vector(headend_jnt.position())
        
        head_matrix = cmds.getAttr('%s.worldMatrix' % head_jnt)
        head_aim_vector = func.Vector(head_matrix[8:11]).norm()
        head_aim_vector *= -1
        
        start_to_end = end_vector - start_vector
        head_to_end = head_end_vector - end_vector
        param_vector = head_to_end * 1.5 + end_vector

        up_ctrl_vector = head_to_end * 2.2
        # ---------------------------------------------------------------------

        # Create root nodes.===================================================
        # リグ用の代理ジョイントを作成。
        parent_proxy = self.createRigParentProxy(neck_jnt, basename)
        # エイムリグ用の代理親ノードを作成。
        aim_parent_proxy = self.createRigParentProxy(neck_jnt, basename+'Aim')
        # 逆親となる代理ノードを作成。
        inv_parent_proxy = self.createRigParentProxy(neck_jnt, basename+'Inv')

        # コントローラー用の代理親を作成。
        ctrl_parent_proxy = self.createCtrlParentProxy(neck_jnt, basename)
        # 頭部のエイムコントローラーを作成。
        aim_ctrl_parent_proxy = self.createCtrlParentProxy(
            neck_jnt, basename+'Aim'
        )
        # =====================================================================

        # リグ用の首～頭部ジョイントをコピーする。-----------------------------
        neck_rigJnt = []
        parent = parent_proxy
        for joint in [neck_jnt, head_jnt, headend_jnt]:
            neck_rigJnt.append(func.copyNode(joint, 'rigJnt', parent))
            parent = neck_rigJnt[-1]
        # ---------------------------------------------------------------------

        # 首のジョイントチェーンから代理ジョイントを作成する。-----------------
        neck_joint_proxies = []
        parent = parent_proxy
        for joint in neck_chain:
            neck_joint_proxies.append(func.copyNode(joint, 'jntProxy', parent))
            parent = neck_joint_proxies[-1]

        head_rot_rigJnt = func.copyNode(
            head_jnt, 'rotProxy', neck_joint_proxies[-2]
        )
        head_aim_jnt = func.copyNode(
            head_jnt, 'aimProxy', neck_joint_proxies[-2]
        )
        # ---------------------------------------------------------------------

        # Fkコントローラ用の首位置を表すノードを作成する。---------------------
        head_rotation_pos = func.copyNode(
            head_jnt, 'worldPos', inv_parent_proxy
        )
        head_rotation_pos.lockTransform()
        # ---------------------------------------------------------------------
        # =====================================================================

        # コントローラとその代理ノードを作成する。=============================
        neck_ctrlspace = {}
        neck_ctrl = {}
        head_ctrlspace = {}
        head_ctrl = {}
        neck_bend_ctrlspace = {}
        neck_bend_ctrl = {}
        
        aim_ctrlspace = {}
        aim_ctrl = {}
        up_ctrlspace = {}
        up_ctrl = {}
        for key, root_parent, aim_parent in zip(
                ['', 'Proxy'],
                [ctrl_parent_proxy, parent_proxy],
                [aim_ctrl_parent_proxy, aim_parent_proxy]
            ):
            # 首のコントローラと位置合わせ用スペースノードを作成する。---------
            unitname.setName(basename+'Neck')
            unitname.setNodeType('ctrlSpace' + key)
            neck_ctrlspace[key] = node.createNode(
                'transform', n=unitname(), p=root_parent
            )
            neck_ctrlspace[key].fitTo(neck_jnt)
            neck_ctrlspace[key].lockTransform()

            unitname.setNodeType('ctrl' + key)
            neck_ctrl[key] = node.createNode(
                'transform', n=unitname(), p=neck_ctrlspace[key]
            )
            # -----------------------------------------------------------------

            # 頭のコントローラと位置合わせ用スペースノードを作成する。---------
            unitname.setName(basename)
            unitname.setNodeType('ctrlSpace' + key)
            head_ctrlspace[key] = func.copyNode(
                head_jnt, ('ctrlSpace' + key), neck_ctrl[key]
            )
            head_ctrlspace[key]('drawStyle', 2)

            unitname.setNodeType('ctrl' + key)
            head_ctrl[key] = node.createNode(
                'transform', n=unitname(), p=head_ctrlspace[key]
            )
            # -----------------------------------------------------------------

            # 首のベンドコントローラーを作成する。-----------------------------
            if is_bent:
                unitname.setName(basename + 'Bend')
                unitname.setNodeType('ctrlSpace' + key)
                neck_bend_ctrlspace[key] = node.createNode(
                    'transform', n=unitname(), p=root_parent
                )
                neck_bend_ctrlspace[key].fitTo(neck_jnt)

                unitname.setNodeType('ctrl' + key)
                neck_bend_ctrl[key] = node.createNode(
                    'transform', n=unitname(), p=neck_bend_ctrlspace[key]
                )
                neck_bend_ctrl[key].lockTransform()
                neck_bend_ctrl[key].editAttr(['t:a'], k=True, l=False)
            # -----------------------------------------------------------------
            
            # エイムコントローラーの作成。-------------------------------------
            unitname.setName(basename + 'Aim')
            unitname.setNodeType('ctrlSpace' + key)
            aim_ctrlspace[key] = node.createNode(
                'transform', n=unitname(), p=aim_parent
            )
            aim_ctrlspace[key].setMatrix(head_matrix)
            pos = end_vector + (head_aim_vector * head_to_end.length() * 5)
            aim_ctrlspace[key].setPosition(pos)

            unitname.setNodeType('ctrl' + key)
            aim_ctrl[key] = node.createNode(
                'transform', n=unitname(), p=aim_ctrlspace[key]
            )

            # Create an up controller.
            unitname.setName(basename + 'Up' + key)
            unitname.setNodeType('ctrlSpace')
            up_ctrlspace[key] = node.createNode(
                'transform', n=unitname(), p=aim_parent
            )
            up_ctrlspace[key].setMatrix(head_matrix)
            pos = end_vector + up_ctrl_vector
            up_ctrlspace[key].setPosition(pos)

            unitname.setNodeType('ctrl' + key)
            up_ctrl[key] = node.createNode(
                'transform', n=unitname(), p=up_ctrlspace[key]
            )

            func.lockTransform(
                [
                    aim_ctrlspace[key], aim_ctrl[key],
                    up_ctrlspace[key], up_ctrl[key]
                ]
            )
            func.controlChannels(
                [aim_ctrl[key], up_ctrl[key]],
                ['t:a'], isKeyable=True, isLocked=False
            )
            # -----------------------------------------------------------------

            func.controlChannels(
                [neck_ctrl[key], head_ctrl[key]], ['v'],
                isKeyable=False, isLocked=False
            )
        head_world_attr, aim_world_attr = [
            x.addFloatAttr('world') for x in (head_ctrl[''], aim_ctrl[''])
        ]

        # Connect controller to proxy.
        for couple in [
                neck_ctrl, head_ctrl, neck_bend_ctrl, aim_ctrl, up_ctrl
            ]:
            if not couple:
                continue
            func.connectKeyableAttr(couple[''], couple['Proxy'])

        for couple in [head_ctrlspace, neck_bend_ctrlspace]:
            if not couple:
                continue
            func.connectKeyableAttr(couple['Proxy'], couple[''])
            self.addLockedList((couple['Proxy'], couple['']))

        # Create parameter controller.
        unitname.setName(basename + 'Param')
        unitname.setNodeType('ctrl')
        param_ctrl = node.createNode(
            'transform', n=unitname(), p=ctrl_parent_proxy
        )
        param_ctrl.editAttr(('t:a', 'r:a', 's:a', 'v'), k=False, l=False)
        param_ctrl.setMatrix(head_matrix)
        param_ctrl.setPosition(param_vector)
        aim_ctrl_attr = param_ctrl.addFloatAttr('aimControl', default=0)
        # =====================================================================


        # /////////////////////////////////////////////////////////////////////
        # リグジョイントから代理ジョイントへの接続。                         //
        # /////////////////////////////////////////////////////////////////////
        # ベンドコントローラーを首のジョイントチェーンへ追加する。
        # (この処理完了後、代理ジョイントはリグジョイントから接続される)
        if is_bent:
            neck_bend_ctrls = func.createBendControl(
                neck_rigJnt[0], neck_rigJnt[1],
                neck_joint_proxies[0], neck_joint_proxies[-1],
                neck_rigJnt[0], False, self.vectorX()
            )
        else:
            # ~neck_rigJnt[1].attr('t') >> ~neck_joint_proxies[-1].attr('t')
            # ~neck_rigJnt[0].attr('r') >> ~neck_joint_proxies[0].attr('r')
            mltmtx = node.createUtil('multMatrix')
            pmm = node.createUtil('pointMatrixMult')
            neck_rigJnt[0].attr('matrix') >> mltmtx/'matrixIn[0]'
            neck_joint_proxies[0].attr('im') >> mltmtx/'matrixIn[1]'
            mltmtx.attr('matrixSum') >> pmm/'inMatrix'
            ~neck_rigJnt[1].attr('t') >> ~pmm.attr('ip')
            ~pmm.attr('o') >> ~neck_joint_proxies[-1].attr('t')

            func.localConstraint(
                cmds.aimConstraint, neck_rigJnt[1], neck_joint_proxies[0],
                w=1, aimVector=self.vectorX(), upVector=(0, 1, 0),
                worldUpType='objectrotation', worldUpVector=(0, 1, 0),
                worldUpObject=neck_rigJnt[0],
                parents=[[neck_rigJnt[0]/'matrix']]
            )

        # Connects the foot joint from combined to proxy.
        for joint in [neck_joint_proxies[-1], neck_rigJnt[1]]:
            (
                ~head_ctrl['Proxy'].attr('s') >> ~joint.attr('s')
            )
        const = cmds.orientConstraint if is_bent else cmds.parentConstraint
        const(head_ctrl['Proxy'], neck_rigJnt[1])
        const(head_ctrl['Proxy'], head_rot_rigJnt)
        # ---------------------------------------------------------------------
        # =====================================================================
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////

        # /////////////////////////////////////////////////////////////////////
        # Setup controllers.                                                 //
        # /////////////////////////////////////////////////////////////////////
        (
            ~neck_ctrl['Proxy'].attr('s') >> ~head_ctrlspace[''].attr('s')
        )
        for proxy in neck_joint_proxies[:-1]:
            (
                ~neck_ctrl['Proxy'].attr('s') >> ~proxy.attr('s')
            )

        # Setup head controller.===============================================
        # Create head automatic rotation system.-------------------------------
        func.unlockTransform([head_ctrlspace['Proxy']])
        cst = func.asObject(
            cmds.orientConstraint(
                head_rotation_pos, head_ctrlspace['Proxy']
            )[0]
        )
        pb = func.createUtil('pairBlend')
        pb('rotInterpolation', 1)
        head_ctrl[''].attr('world') >> pb.attr('weight')
        ~cst.attr('cr') >> ~pb.attr('ir2')
        for axis in func.Axis:
            value = head_rotation_pos('r'+axis)
            pb('ir%s1' % axis, value, l=True)
        ~pb.attr('or') >> ~head_ctrlspace['Proxy'].attr('r')
        head_ctrlspace['Proxy'].lockTransform()
        # ---------------------------------------------------------------------

        # Create connections from the neck controller to the neck joint.-------
        cmds.orientConstraint(neck_ctrl['Proxy'], neck_rigJnt[0])
        # ---------------------------------------------------------------------

        # Make connetions between head control to bend controller.-------------
        if is_bent:
            neck_bend_ctrls['btmCtrlSpace'].unlockTransform()
            ctrl_proxy_matrxies = func.listNodeChain(
                neck_ctrlspace['Proxy'], head_ctrlspace['Proxy']
            )
            ctrl_proxy_matrxies.reverse()
            ctrl_proxy_matrxies = [x + '.matrix' for x in ctrl_proxy_matrxies]
            neck_inverse_matrixes = func.listNodeChain(
                neck_rigJnt[0], neck_bend_ctrls['btmCtrlSpace']
            )
            neck_inverse_matrixes = [
                x + '.inverseMatrix' for x in neck_inverse_matrixes[:-1]
            ]
            ctrl_proxy_matrxies.extend(neck_inverse_matrixes)

            func.createTranslateConnection(
                '%s.t' % head_ctrl['Proxy'], ctrl_proxy_matrxies,
                '%s.t' % neck_bend_ctrls['btmCtrlSpace']
            )
            
            neck_bend_ctrls['btmCtrlSpace'].lockTransform()
        # ---------------------------------------------------------------------
        # =====================================================================

        # ベンドコントローラーの接続。-----------------------------------------
        if is_bent:
            neck_bend_ctrlspace['Proxy'].unlockTransform()
            func.createTranslateConnection(
                '%s.t' % neck_bend_ctrls['midCtrlSpace'],
                [x + '.matrix' for x in [
                        neck_bend_ctrls['root'], neck_rigJnt[0],
                    ]
                ],
                '%s.t' % neck_bend_ctrlspace['Proxy']
            )
            func.lockTransform(
                [neck_bend_ctrlspace[''], neck_bend_ctrlspace['Proxy']]
            )
            (
                ~neck_bend_ctrl['Proxy'].attr('t')
                >> ~neck_bend_ctrls['midCtrl'].attr('t')
            )
        # ---------------------------------------------------------------------
        
        # Blends rotation joint and aim joint to proxy joint for the head.-----
        func.blendTransform(
            head_rot_rigJnt, head_aim_jnt, neck_joint_proxies[-1],
            '%s.aimControl' % param_ctrl,
            skipTranslate=True, skipScale=True, blendMode=1
        )
        for joint in [head_rot_rigJnt, head_aim_jnt]:
            ~neck_joint_proxies[-1].attr('t') >> ~joint.attr('t')
        # ---------------------------------------------------------------------
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////
        
        # /////////////////////////////////////////////////////////////////////
        # Setup the head aim controller.                                     //
        # /////////////////////////////////////////////////////////////////////
        aim_cst = cmds.aimConstraint(
            aim_ctrl['Proxy'], head_aim_jnt,
            aimVector=[0, 0, -1], upVector=[1, 0, 0],
            worldUpType='object', worldUpObject=up_ctrl['Proxy']
        )

        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////

        # /////////////////////////////////////////////////////////////////////
        # Connect proxy joints to original joints.                           //
        # /////////////////////////////////////////////////////////////////////
        for proxy, orig in zip(neck_joint_proxies, neck_chain):
            func.connectKeyableAttr(proxy, orig)
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////


        # /////////////////////////////////////////////////////////////////////
        # Add shapes to the all controllers.                                 //
        # /////////////////////////////////////////////////////////////////////
        # Adds shape to the neck fk controllers.-------------------------------
        creator = func.PrimitiveCreator()
        size = start_to_end.length()
        creator.setSizes([size, size, size])
        creator.setColorIndex(self.colorIndex('main'))
        creator.setCurveType('circleArrow')
        creator.setRotation([0, 0, 90])
        creator.create(parentNode=head_ctrl[''])
        creator.create(parentNode=neck_ctrl[''])
        # ---------------------------------------------------------------------

        # Add shapes to the aim and up controller.-----------------------------
        size = head_to_end.length() * 0.5
        creator.setSizes([size, size, size])
        creator.setRotation([90, 0, -90])
        creator.setColorIndex(self.colorIndex('key'))
        creator.setCurveType('faceA')
        creator.create(parentNode=aim_ctrl[''])

        size *= 0.5
        creator.setSizes([size, size, size])
        creator.setCurveType('pyramid')
        creator.create(parentNode=up_ctrl[''])
        # ---------------------------------------------------------------------

        # Adds shape to the neck bend controller.------------------------------
        size = head_to_end.length() * 1.5
        creator.setSizes([size, size, size])
        creator.setRotation([0, 0, 90])
        creator.setCurveType('crossArrow')
        creator.setColorIndex(self.colorIndex('sub'))
        if neck_bend_ctrl:
            creator.create(parentNode=neck_bend_ctrl[''])
        # ---------------------------------------------------------------------

        size *= 0.25
        creator.setSizes([size, size, size])
        creator.setRotation([90, 0, 0])
        creator.setCurveType('cross')
        creator.setColorIndex(self.colorIndex('special'))
        creator.create(parentNode=param_ctrl)
        # ---------------------------------------------------------------------
        # ---------------------------------------------------------------------
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////
        
        # /////////////////////////////////////////////////////////////////////
        # Post precesses.                                                    //
        # /////////////////////////////////////////////////////////////////////
        # Connect aimControl attribute of the param controller to the 
        # aim controller visibility.
        aim_ctrl_attr >> aim_ctrl_parent_proxy/'v'
        
        # コントローラの親ノードから代理親への接続を行う。
        parent_matrix = self.createParentMatrixNode(
            cmds.listRelatives(neck_jnt, p=True, pa=True)[0]
        )
        if parent_matrix:
            parent_decmtx = func.createDecomposeMatrix(
                ctrl_parent_proxy, ['%s.matrixSum' % parent_matrix],
                withMultMatrix=False
            )[0]
            # -----------------------------------------------------------------
            # Connect iverse matrix to inv parent proxy.
            inv_matrix_nodes = cmds.listConnections(
                '%s.matrixIn' % parent_matrix, s=True, d=False
            )
            inv_matrix_nodes.reverse()
            inv_matrix_nodes = [x + '.inverseMatrix' for x in inv_matrix_nodes]
            inv_matrix_nodes.insert(0, '%s.matrix' % parent_proxy)
            inv_matrix_nodes.append('%s.matrix' % parent_proxy)
            inv_decmtx, mltmtx = func.createDecomposeMatrix(
                inv_parent_proxy, inv_matrix_nodes
            )
            inv_matrix_nodes = cmds.listConnections(
                '%s.matrixIn' % mltmtx, s=True, d=False, p=True
            )
            for i in [0, len(inv_matrix_nodes) - 1]:
                target_plug = '%s.matrixIn[%s]' % (mltmtx, i)
                cmds.disconnectAttr(inv_matrix_nodes[i], target_plug)
                matrix = cmds.getAttr(inv_matrix_nodes[i])
                cmds.setAttr(target_plug, matrix, type='matrix')
            # -----------------------------------------------------------------
        else:
            parent_decmtx, inv_decmtx = [
                node.createUtil('decomposeMatrix') for x in range(2)
            ]

        # Setup for the aim controller.----------------------------------------
        for parent, target_parent, decmtx, indexes in zip(
                [parent_proxy, ctrl_parent_proxy],
                [aim_parent_proxy, aim_ctrl_parent_proxy],
                [inv_decmtx, parent_decmtx],
                [[1, 2], [2, 1]],
            ):
            pb_tr, pb_s = func.blendTransform(
                parent, parent, target_parent,
                '%s.world' % aim_ctrl[''], blendMode=1
            )
            for attr, pb in zip(['t', 'r', 's'], [pb_tr, pb_tr, pb_s]):
                if attr == 's':
                    pb_attr = 't'
                else:
                    pb_attr = attr
                for ax in func.Axis:
                    cmds.disconnectAttr(
                        '%s.%s%s' % (parent, attr, ax),
                        '%s.i%s%s%s' % (pb, pb_attr, ax, indexes[0])
                    )
                    cmds.connectAttr(
                        '%s.o%s%s' % (decmtx, attr, ax),
                        '%s.i%s%s%s' % (pb, pb_attr, ax, indexes[1]),
                        f=True
                    )
        # ---------------------------------------------------------------------

        func.lockTransform(
            [
                parent_proxy, aim_parent_proxy, inv_parent_proxy,
                ctrl_parent_proxy, aim_ctrl_parent_proxy
            ]
        )

        # Add controller to the anim set.======================================
        anim_set.addChild(
            *[
                x[''] for x in [
                    head_ctrl, neck_ctrl, aim_ctrl, up_ctrl, neck_bend_ctrl
                ]
                if x
            ]
        )
        anim_set.addChild(param_ctrl)
        # =====================================================================
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////
