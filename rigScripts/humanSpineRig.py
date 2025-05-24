# -*- coding:utf-8 -*-
r'''
    @file     unitySpineRig.py
    @brief    UNITY用の背骨を作成するための機能を提供するモジュール。
    @class    JointCreator : 背骨のジョイント作成機能を提供するクラス。
    @class    RigCreator : ここに説明文を記入
    @date        2017/02/01 1:03[Eske](eske3g@gmail.com)
    @update      2017/02/01 1:04[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
from .. import rigScripts, node
func = rigScripts.func
cmds = func.cmds

Category = 'Basic Human'
BaseName = 'spine'

class JointCreator(rigScripts.JointCreator):
    r'''
        @brief       背骨のジョイント作成機能を提供するクラス。
        @inheritance rigScripts.JointCreator
        @date        2017/02/01 1:03[Eske](eske3g@gmail.com)
        @update      2017/02/01 1:04[Eske](eske3g@gmail.com)
    '''
    def process(self):
        r'''
            @brief  ジョイント作成プロセスとしてコールされる。
            @return None
        '''
        from gris3.tools import jointEditor
        name = self.basenameObject()
        parent = self.parent()
        options = self.options()

        # Hip.
        name.setName('hip')
        hip = node.createNode('joint', n=name(), p=parent)
        hip.setPosition((0.0, 101.0, 1.2))
        hip.setRadius(2)

        # SpineA.
        name.setName('spineA')
        spineA = node.createNode('joint', n=name(), p=hip)
        spineA.setPosition((0.0, 114.0, 3.7))

        # SpineB
        name.setName('spineB')
        spineB = node.createNode('joint', n=name(), p=spineA)
        spineB.setPosition((0.0, 126.0, 2.6))

        # SpineC.
        name.setName('spineC')
        spineC = node.createNode('joint', n=name(), p=spineB)
        spineC.setPosition((-0.0, 137.0, 0.1))
        
        # Fix joint orient.
        om = jointEditor.OrientationModifier()
        om.setSecondaryMode('vector')
        om.setApplyToChildren(False)
        om.setTargetUpAxis('-Z')
        om.execute((hip, spineA, spineB, spineC))

        # Unit setting.--------------------------------------------------------
        unit = self.unit()
        unit.addMember('hip', hip)
        unit.addMember('spineEnd', spineC)
        # ---------------------------------------------------------------------
        
        self.asRoot(hip)
        spineC.select()



class RigCreator(rigScripts.RigCreator):
    r'''
        @brief       ここに説明文を記入
        @inheritance rigScripts.RigCreator
        @date        2017/02/01 1:03[Eske](eske3g@gmail.com)
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
        anim_set = self.animSet()

        spine_start_jnt = unit.getMember('hip')
        spine_end_jnt = unit.getMember('spineEnd')

        # 背骨の末端ジョイントに子がいれば、それを子として扱う。
        if spine_end_jnt.hasChild():
            spine_end_jnt = spine_end_jnt.children()[0]

        spines_chain = func.listNodeChain(spine_start_jnt, spine_end_jnt)
        spines_jnt = spines_chain[1:-1]

        # ベクトルを予め取得しておく。-----------------------------------------
        start_vector = func.Vector(spine_start_jnt.rotatePivot())
        end_vector = func.Vector(spine_end_jnt.rotatePivot())
        start_to_end = end_vector - start_vector
        # ---------------------------------------------------------------------

        # 各種ルートノードの作成。=============================================
        # リグ用の親代理ノードを作成する。
        rig_parent_proxy = self.createRigParentProxy(spine_start_jnt, basename)

        # コントローラ用の親代理ノードを作成する。
        ctrl_parent_proxy = self.createCtrlParentProxy(spine_start_jnt, basename)
        
        # IK用のセットアップグループを作成する。
        unitname.setName(basename + 'IkSetup')
        unitname.setNodeType('parentProxy')
        ik_setup_grp = node.createNode(
            'transform', n=unitname(), p=rig_parent_proxy
        )
        # =====================================================================

        # オリジナルのジョイントから背骨リグ用の骨をコピーする。===============
        spines_rigJnt = {}

        unitname.setName(basename+'End')
        for key in ('ikJnt', 'fkJnt', 'combJnt'):
            # Copy a spine chains.
            parent = rig_parent_proxy
            chains_list = []
            for joint in spines_chain:
                chains_list.append(func.copyNode(joint, key, parent))
                parent = chains_list[-1]
            parent.rename(unitname.convertType(key)())
            spines_rigJnt[key] = chains_list
        func.controlChannels(
            [spines_rigJnt['combJnt'][0]], ['s:a'],
            isKeyable=False, isLocked=True
        )
        # =====================================================================

        # コントローラとその代理ノードの作成。=================================
        hip_ctrl = {}
        hip_ik_ctrlspace = {}
        hip_ik_ctrl = {}
        spine_ik_ctrlspace = {}
        spine_ik_ctrl = {}

        # 腰コントローラの作成。-----------------------------------------------
        unitname.setName(basename+'Hip')
        unitname.setNodeType('ctrlSpace')
        hip_ctrl_space = node.createNode(
            'transform', n=unitname(), p=ctrl_parent_proxy
        )
        hip_ctrl_space.fitTo(spine_start_jnt, 0b1011)
        hip_ctrl_space.fitTo(rig_parent_proxy, 0b0100)
        hip_ctrl_space.lockTransform()

        unitname.setNodeType('ctrl')
        hip_ctrl[''] = node.createNode(
            'transform', n=unitname(), p=hip_ctrl_space
        )
        hip_ctrl['Proxy'] = func.copyNode(
            spine_start_jnt, 'ctrlProxy', rig_parent_proxy
        )
        func.fixConstraint(
            cmds.parentConstraint, hip_ctrl[''], hip_ctrl['Proxy'],
            mo=True
        )
        func.lockTransform([hip_ctrl[''], hip_ctrl['Proxy']])
        hip_ctrl[''].editAttr(('t:a', 'r:a'), k=True, l=False)
        # ---------------------------------------------------------------------
    
        for key, root_parent in zip(
                ['', 'Proxy'], [hip_ctrl[''], ik_setup_grp]
            ):
            # ヒップのコントローラを作成。
            unitname.setName(basename+'HipIk')
            unitname.setNodeType('ctrlSpace' + key)
            hip_ik_ctrlspace[key] = node.createNode(
                'transform', n=unitname(), p=root_parent
            )
            hip_ik_ctrlspace[key].setPosition(spine_start_jnt.position())
            hip_ik_ctrlspace[key].fitTo(rig_parent_proxy, 0b0100)

            unitname.setNodeType('ctrl' + key)
            hip_ik_ctrl[key] = node.createNode(
                'transform', n=unitname(), p=hip_ik_ctrlspace[key]
            )
            func.lockTransform(
                [hip_ik_ctrlspace[key], hip_ik_ctrl[key]]
            )
            hip_ik_ctrl[key].editAttr(('t:a', 'r:a'), k=True, l=False)

            # ヒップのIK用コントローラを作成。
            unitname.setName(basename+'Ik')
            unitname.setNodeType('ctrlSpace' + key)
            spine_ik_ctrlspace[key] = node.createNode(
                'transform', n=unitname(), p=root_parent
            )
            spine_ik_ctrlspace[key].setPosition(spine_end_jnt.position())
            spine_ik_ctrlspace[key].fitTo(rig_parent_proxy, 0b0100)

            unitname.setNodeType('ctrl' + key)
            spine_ik_ctrl[key] = node.createNode(
                'transform', n=unitname(), p=spine_ik_ctrlspace[key]
            )
            func.lockTransform(
                [spine_ik_ctrlspace[key], spine_ik_ctrl[key]]
            )
            spine_ik_ctrl[key].editAttr(('t:a', 'r:a'), k=True, l=False)
            # -----------------------------------------------------------------

        hip_twist_attr, spine_twist_attr = [
            x.addFloatAttr('twist', min=None, max=None, default=0)
            for x in (hip_ik_ctrl[''], spine_ik_ctrl[''])
        ]

        #コントローラから代理ノードへの接続。
        for couple in [hip_ik_ctrl, spine_ik_ctrl]:
            func.connectKeyableAttr(couple[''], couple['Proxy'])

        # 背骨制御用のパラメータコントローラの追加。---------------------------
        unitname.setName(basename + 'Param')
        unitname.setNodeType('ctrl')
        param = node.createNode('transform', n=unitname(), p=hip_ctrl[''])
        stretch_attr, shrink_attr, keep_attr = [
            param.addFloatAttr(x, default=0)
            for x in ('stretch', 'shrink', 'keepVolume')
        ]
        
        pma = func.createUtil('plusMinusAverage')
        mdl = func.createUtil('multiplyDivide')
        mdl('input2', (0.5, 0.5, 0.5))
        index = 0
        for n in [
            hip_ik_ctrlspace, hip_ik_ctrl, spine_ik_ctrlspace, spine_ik_ctrl
        ]:
            cmds.connectAttr(n[''] + '.t', '%s.input3D[%s]' % (pma, index))
            index += 1
        pma.attr('output3D') >> mdl.attr('input1')
        mdl.attr('output') >> param.attr('t')
        param.lockTransform()
        # ---------------------------------------------------------------------
        # =====================================================================

        # /////////////////////////////////////////////////////////////////////
        # ikコントローラとその仕組の作成。                                   //
        # /////////////////////////////////////////////////////////////////////
        # IKの仕組みを作成。===================================================
        # ikスプラインカーブと、そのカーブに制御されるikの作成。---------------
        unitname.setName(basename + 'Ik')
        unitname.setNodeType('crv')
        chain_positions = [x.position() for x in spines_chain]
        ik_curve = cmds.rename(
            cmds.curve(d=1, p=chain_positions), unitname()
        )
        ik_curve = func.asObject(cmds.parent(ik_curve, ik_setup_grp)[0])
        ik_curve.freeze()
        ik_curve.setPivot((0, 0, 0))

        # IKスプラインの作成。
        ik = cmds.ikHandle(
            sj=spines_rigJnt['ikJnt'][0], ee=spines_rigJnt['ikJnt'][-1](),
            c=ik_curve, sol='ikSplineSolver', ccv=False, pcv=False
        )[0]
        unitname.setName(basename)
        unitname.setNodeType('ik')
        ik = cmds.rename(ik, unitname())
        ik = func.asObject(cmds.parent(ik, ik_setup_grp)[0])
        # ---------------------------------------------------------------------

        # Create transform to modify the curve shape.--------------------------
        index = 0
        cv_top_modifier_proxies = []
        cv_btm_modifier_proxies = []
        for joint in spines_rigJnt['ikJnt']:
            top_space = node.createNode('transform', p=spine_ik_ctrl['Proxy'])
            top_space.setPosition(joint.position())
            top_space.fitTo(rig_parent_proxy, 0b0100)

            btm_space = func.asObject(
                cmds.parent(
                    cmds.duplicate(top_space)[0], hip_ik_ctrl['Proxy']
                )[0]
            )
            cv_top_modifier_proxies.append(top_space)
            cv_btm_modifier_proxies.append(btm_space)
        ratio_list = func.createMovementWeightList(cv_top_modifier_proxies)

        index = 0
        spine_mltmtx = func.createUtil('multMatrix')
        hip_mltmtx = func.createUtil('multMatrix')
        func.connectMultAttr(
            [
                '%s.matrix' % x['Proxy'] for x in [
                    spine_ik_ctrl, spine_ik_ctrlspace
                ]
            ], '%s.matrixIn' % spine_mltmtx
        )
        func.connectMultAttr(
            [
                '%s.matrix' % x['Proxy'] for x in [
                    hip_ik_ctrl, hip_ik_ctrlspace
                ]
            ], '%s.matrixIn' % hip_mltmtx
        )

        for top_mod, btm_mod, ratio in zip(
                cv_top_modifier_proxies, cv_btm_modifier_proxies, ratio_list
            ):
            pb = func.createUtil('pairBlend')
            ik_ratio_attr = param.addFloatAttr('ikRatio%s' % index)
            ik_ratio_attr >>  pb/'w'
            ik_ratio_attr.set(ratio)
            attr_index = 1
            for mod_node, ctrl_mtx in zip(
                    [btm_mod, top_mod], [hip_mltmtx, spine_mltmtx]
                ):
                pmm = func.createUtil('pointMatrixMult')
                ctrl_mtx/'matrixSum' >> pmm.attr('inMatrix')
                value = mod_node('t')[0]
                pmm('ip', value)
                
                ~pmm.attr('o') >> ~pb.attr('it%s' % attr_index)
                attr_index += 1
            func.connect3ChannelAttr(
                '%s.ot' % pb, '%s.cp[%s].%%sValue' % (ik_curve, index)
            )
            index += 1
        cmds.delete(cv_top_modifier_proxies, cv_btm_modifier_proxies)
        # ---------------------------------------------------------------------
        # =====================================================================

        # Create stretch system.===============================================
        result_node = func.createTranslationStretchSystem(
            spines_rigJnt['ikJnt'][0], spines_rigJnt['ikJnt'][-1],
            distanceCurve=ik_curve
        )
        unitname.setNodeType('loc')
        unitname.setName(basename + 'Start')
        start_loc = unitname()
        
        unitname.setName(basename + 'End')
        end_loc = unitname()
        
        unitname.setName(basename + 'Distance')
        unitname.setNodeType('grp')
        dist_node = unitname()

        start_loc = cmds.parent(
            cmds.rename(result_node['start'], start_loc),
            hip_ik_ctrl['Proxy']
        )[0]
        end_loc = cmds.parent(
            cmds.rename(result_node['end'], end_loc),
            spine_ik_ctrl['Proxy']
        )[0]
        dist_node = func.asObject(
            cmds.parent(
                cmds.rename(result_node['result'], dist_node), ik_setup_grp
            )[0]
        )
        stretch_attr >> dist_node/'stretch'
        shrink_attr >> dist_node/'shrink'
        keep_attr >> dist_node/'volumeScale'
        # =====================================================================

        # Adds twist attribute.================================================
        hip_twist_attr >> ik/'roll'

        mdl = func.createUtil('multDoubleLinear')
        hip_twist_attr >> mdl/'input1'
        mdl('input2', -1, l=True)

        adl = func.createUtil('addDoubleLinear')
        spine_twist_attr >> adl/'input1'
        mdl.attr('output') >> adl/'input2'
        adl.attr('output') >> ik/'twist'
        # =====================================================================
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////

        
        # /////////////////////////////////////////////////////////////////////
        # Create a fk system on the ik system.                               //
        # /////////////////////////////////////////////////////////////////////
        # Connect ik joints to fk joints.
        num = len(spines_rigJnt['ikJnt'])
        for i in range(num):
            ikj = spines_rigJnt['ikJnt'][i]
            fkj = spines_rigJnt['fkJnt'][i]
            
            ~ikj.attr('t') >> ~fkj.attr('t')
            if i == num - 1:
                continue
            ~ikj.attr('r') >> ~fkj.attr('r')

        # Create controllers and it's proxies.=================================
        # Create a root node for the all of fk controllers.--------------------
        unitname.setName(basename + 'FkCtrl')
        unitname.setNodeType('grp')
        fkctrl_parent = node.createNode(
            'transform', p=hip_ctrl[''], n=unitname()
        )
        fkctrl_parent.fitTo(rig_parent_proxy)
        fkctrl_parent.lockTransform()
        # ---------------------------------------------------------------------

        # Create a hip position proxy for fk controllers.----------------------
        fkhip_posproxy = func.copyNode(
            spines_rigJnt['fkJnt'][0], 'fkCtrlSpace', fkctrl_parent
        )
        cmds.setAttr('%s.drawStyle' % fkhip_posproxy, 2)
        func.connect3ChannelAttr(
            '%s.t' % spines_rigJnt['fkJnt'][0], '%s.t' % fkhip_posproxy
        )
        func.connect3ChannelAttr(
            '%s.r' % spines_rigJnt['fkJnt'][0], '%s.r' % fkhip_posproxy
        )
        # ---------------------------------------------------------------------

        # Create controller for an all of spines.------------------------------
        unitname.setName(basename + 'SpineAll')
        unitname.setNodeType('ctrlSpace')
        spine_all_space = func.copyNode(
            spines_rigJnt['fkJnt'][1], 'allCtrlSpace', fkhip_posproxy
        )
        spine_all_space('drawStyle', 2)
        func.connectKeyableAttr(spines_rigJnt['fkJnt'][1], spine_all_space)

        unitname.setNodeType('ctrl')
        spine_all_ctrl = node.createNode(
            'transform', n=unitname(), p=spine_all_space
        )
        func.lockTransform([spine_all_ctrl, spine_all_space])
        spine_all_ctrl.editAttr(['r:a'], k=True, l=False)
        # ---------------------------------------------------------------------

        fk_ctrls = []
        fk_ctrl_proxies = []
        ctrl_parent = spine_all_space
        for i in range(1, num-1):
            # Create fk controller proxy.--------------------------------------
            jnt = spines_rigJnt['fkJnt'][i]
            name = func.Name(jnt)
            name.setNodeType('ctrlProxy')
            ctrl_proxy = node.createNode('transform', p=jnt, n=name())

            spines_rigJnt['fkJnt'][i+1] = cmds.parent(
                spines_rigJnt['fkJnt'][i+1](), ctrl_proxy
            )[0]
            fk_ctrl_proxies.append(ctrl_proxy)
            self.addLockedList(ctrl_proxy)
            # -----------------------------------------------------------------

            # Create fk controller.--------------------------------------------
            name.setNodeType('ctrlSpace')
            space = func.createSpaceNode(n=name(), p=ctrl_parent)
            if i != 1:
                func.copyJointState(jnt, space)
                func.connectKeyableAttr(jnt, space)
            self.addLockedList(space)

            name.setNodeType('autoTrs')
            auto_trs = node.createNode('transform', n=name(), p=space)
            ~spine_all_ctrl.attr('r') >> ~auto_trs.attr('r')
            dist_node+'.volumeScaleRatio' >> auto_trs.attr('sy')
            dist_node+'.volumeScaleRatio' >> auto_trs.attr('sz')
            
            name.setNodeType('ctrl')
            ctrl = node.createNode('transform', n=name(), p=auto_trs)
            ctrl.editAttr(['v'], k=False, l=False)

            func.createDecomposeMatrix(
                ctrl_proxy, [x/'matrix' for x in (ctrl, auto_trs)]
            )
            self.addLockedList([auto_trs, space])
            fk_ctrls.append(ctrl)
            ctrl_parent = ctrl
            # -----------------------------------------------------------------
        # =====================================================================
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////

        # /////////////////////////////////////////////////////////////////////
        # ヒップシェイク用コントローラを作成。                               //
        # /////////////////////////////////////////////////////////////////////
        unitname.setName(basename + 'HipShake')
        unitname.setNodeType('ctrlPos')
        ctrl_pos = func.asObject(
            cmds.rename(
                cmds.duplicate(fkhip_posproxy, po=True)[0], unitname()
            )
        )
        for attr in 'tr':
            ~spines_rigJnt['fkJnt'][0].attr(attr) >> ~ctrl_pos.attr(attr)

        unitname.setNodeType('ctrlSpace')
        space = node.createNode('transform', n=unitname(), p=ctrl_pos)
        func.createDecomposeMatrix(
            space, [spines_rigJnt['fkJnt'][1] + '.matrix'],
            withMultMatrix=False
        )
        unitname.setNodeType('ctrl')
        hip_shake_ctrl = node.createNode('transform', n=unitname(), p=space)

        temp_hip_shake_proxy = node.createNode('transform', p=hip_shake_ctrl)
        temp_hip_shake_proxy.fitTo(ctrl_pos)
        # Connects scale attribute to fk hip joint and fk hip proxy.
        # for target in [fkhip_posproxy, spines_chain[0]]:
        for target in [fkhip_posproxy]:
            ~hip_shake_ctrl.attr('s') >> ~target.attr('s')
        md = func.createUtil('multiplyDivide')
        for axis in func.Axis:
            src_attr = hip_shake_ctrl.attr('s'+axis)
            dst_attr = spines_chain[0].attr('s'+axis)
            if axis == 'x':
                src_attr >> dst_attr
                continue
            src_attr >> md.attr('i1'+axis)
            dist_node+'.volumeScaleRatio' >> md.attr('i2'+axis)
            md.attr('o'+axis) >> dst_attr
        func.lockTransform([hip_shake_ctrl, ctrl_pos, space, fkhip_posproxy])
        hip_shake_ctrl.editAttr(['t:a', 'r:a', 's:a'], k=True, l=False)
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////

        # /////////////////////////////////////////////////////////////////////
        # Connects from rigged joints to final joints.                       //
        # /////////////////////////////////////////////////////////////////////
        # For the hip joint.---------------------------------------------------
        cst = func.asObject(
            cmds.parentConstraint(
                temp_hip_shake_proxy, spines_rigJnt['combJnt'][0]
            )[0]
        )

        mltmtx = func.createUtil('multMatrix')
        hip_shake_ctrl.attr('matrix') >> mltmtx/'matrixIn[0]'
        mltmtx('matrixIn[1]', space('matrix'), type='matrix')
        spines_rigJnt['fkJnt'][0].attr('matrix') >> mltmtx/'matrixIn[2]'
        mltmtx(
            'matrixIn[3]', hip_ctrl['Proxy']('inverseMatrix'), type='matrix'
        )
        hip_ctrl['Proxy'].attr('matrix') >> mltmtx.attr('matrixIn[4]')

        mltmtx.attr('matrixSum') >> cst/'target[0].targetParentMatrix'

        attr = cst.attr('constraintParentInverseMatrix')
        attr.disconnect()
        attr.set(
            [1, 0, 0 ,0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1], type='matrix'
        )
        # ---------------------------------------------------------------------

        # Blend results from hip fk joint and hip shake controller.------------
        # Creates input matrix(1) from the hip shake controller.
        mltmtx = func.createUtil('multMatrix')
        decmtx_a = func.createUtil('decomposeMatrix')
        mltmtx.attr('matrixSum') >> decmtx_a/'inputMatrix'
        nodelist = [
            (temp_hip_shake_proxy, False), (hip_shake_ctrl, True),
            (space, False), (ctrl_pos, True)
        ]
        index = 0
        for n, connecting in nodelist:
            out_plug = n.attr('matrix')
            in_plug = mltmtx.attr('matrixIn[%s]' % (index))
            if connecting:
                out_plug >> in_plug
            else:
                in_plug.set(out_plug.get(), type='matrix')
            index += 1

        hip_ikrig_jntproxy = func.Name(spine_start_jnt)
        hip_ikrig_jntproxy.setNodeType('ikFkJntProxy')
        hip_ikrig_jntproxy = node.createNode(
            'transform', n=hip_ikrig_jntproxy(), p=rig_parent_proxy
        )
        for attr in 'tr':
            ~decmtx_a.attr('o'+attr) >> ~hip_ikrig_jntproxy.attr(attr)
        hip_ikrig_jntproxy.lockTransform()
        # ---------------------------------------------------------------------

        # Post process for the temporary node.---------------------------------
        connections = cmds.listConnections(
            temp_hip_shake_proxy, s=False, d=True, c=True, p=True
        )
        for i in range(0, len(connections), 2):
            cmds.disconnectAttr(connections[i], connections[i+1])
            value = cmds.getAttr(connections[i])
            if isinstance(value, (list, tuple)):
                cmds.setAttr(connections[i+1], *value[0])
            else:
                cmds.setAttr(connections[i+1], value)
        cmds.delete(temp_hip_shake_proxy)
        # ---------------------------------------------------------------------

        # For the other spine joints without end joint.------------------------
        inverse_matrices = ['%s.inverseMatrix' % hip_ikrig_jntproxy]
        fk_start_jnt = spines_rigJnt['fkJnt'][0]
        for proxy, joint, in zip(
                fk_ctrl_proxies, spines_rigJnt['combJnt'][1:-1], 
            ):
            ~proxy.attr('s') >> ~joint.attr('s')

            cst = cmds.parentConstraint(proxy, joint)[0]
            parent_nodes = func.listNodeChain(fk_start_jnt, proxy)[:-1]
            parent_nodes.reverse()
            mltmtx = func.createUtil('multMatrix')
            func.connectMultAttr(
                [x + '.matrix' for x in parent_nodes], mltmtx + '.matrixIn', 0
            )
            cmds.connectAttr(
                mltmtx + '.matrixSum', cst + '.target[0].targetParentMatrix',
                f=True
            )

            if len(inverse_matrices) == 1:
                mtxattr = inverse_matrices[0]
            else:
                mltmtx = func.createUtil('multMatrix')
                func.connectMultAttr(inverse_matrices, '%s.matrixIn' % mltmtx)
                mtxattr = '%s.matrixSum' % mltmtx
            cmds.connectAttr(
                mtxattr, '%s.constraintParentInverseMatrix' % cst, f=True
            )
            inverse_matrices.append('%s.inverseMatrix' % joint)
        # ---------------------------------------------------------------------
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////
        # ---------------------------------------------------------------------


        # /////////////////////////////////////////////////////////////////////
        # Connect proxy joints to original joints.                           //
        # /////////////////////////////////////////////////////////////////////
        for proxy, orig in zip(
                spines_rigJnt['combJnt'][:-1], spines_chain[:-1]
            ):
            func.connectKeyableAttr(proxy, orig)

        mdl = func.createUtil('multDoubleLinear')
        spines_rigJnt['combJnt'][-2].attr('sx') >> mdl.attr('input1')
        dist_node+'.stretchRatio' >> mdl.attr('input2')
        mdl.attr('o') >> spines_chain[-2].attr('sx')
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////

        # /////////////////////////////////////////////////////////////////////
        # Setup parent proxy.
        # /////////////////////////////////////////////////////////////////////
        parent_matrix = self.createParentMatrixNode(
            cmds.listRelatives(spine_start_jnt, p=True, pa=True)[0]
        )
        if parent_matrix:
            decmtx = func.createDecomposeMatrix(
                ctrl_parent_proxy, ['%s.matrixSum' % parent_matrix],
                withMultMatrix=False
            )[0]
        func.lockTransform([ctrl_parent_proxy])
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////

        
        # /////////////////////////////////////////////////////////////////////
        # Add shapes to the all controllers.                                 //
        # /////////////////////////////////////////////////////////////////////
        # Adds shape to the hip controller.------------------------------------
        creator = func.PrimitiveCreator()
        size = start_to_end.length() * 0.75
        creator.setSizes([size, size, size])
        creator.setColorIndex(22)
        creator.setCurveType('plane')
        creator.create(parentNode=hip_ctrl[''])
        # ---------------------------------------------------------------------

        # Adds shape to the parameter controller of the spine ik.--------------
        creator.setSize(size * 0.25)
        creator.setColorIndex(26)
        creator.setCurveType('cross')
        creator.setRotation([90, 0, 0])
        creator.create(parentNode=param)
        # ---------------------------------------------------------------------
        
        # Adds shape to the fk controllers.------------------------------------
        size *= 0.6
        creator.setSizes([size, size, size])
        creator.setColorIndex(self.colorIndex('sub'))
        creator.setRotation([0, 0, 90])
        creator.setCurveType('circle')
        creator.create(parentNode=spine_all_ctrl)
        
        size *= 0.8
        creator.setColorIndex(self.colorIndex('extra'))
        for ctrl in fk_ctrls:
            creator.setSizes([size, size, size])
            creator.create(parentNode=ctrl)
        creator.setRotation()
        # ---------------------------------------------------------------------
        
        # Adds shape to the hip shake controller.------------------------------
        size = start_to_end.length() * 0.5
        creator.setSizes([size*0.1, size*0.1, -size*0.5])
        creator.setTranslation([0, 0, -size])
        creator.setRotation([0, 0, 90])
        creator.setCurveType('pyramid')
        creator.setColorIndex(self.colorIndex('key'))
        creator.create(parentNode=hip_shake_ctrl)
        creator.setTranslation()
        # ---------------------------------------------------------------------

        # Adds shape to the spine ik controllers.------------------------------
        size *= 0.6
        creator.setSizes([size, size*0.2, size])
        creator.setCurveType('box')
        creator.setColorIndex(self.colorIndex('sub'))
        for ctrl in [hip_ik_ctrl, spine_ik_ctrl]:
            shape = creator.create(parentNode=ctrl[''])
        # ---------------------------------------------------------------------
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////

        # /////////////////////////////////////////////////////////////////////
        # Post processes.                                                    //
        # /////////////////////////////////////////////////////////////////////
        # Set up advanced ik twist controls.===================================
        ik('dTwistControlEnable', 1)
        ik('dWorldUpType', 4)
        ik('dWorldUpAxis', 0)
        ik('dWorldUpVector', (1, 0, 0))
        ik('dWorldUpVectorEnd', (1, 0, 0))
        spine_ik_ctrl['Proxy']/'worldMatrix[0]' >> ik.attr('dWorldUpMatrixEnd')
        hip_ik_ctrl['Proxy']/'worldMatrix[0]' >> ik.attr('dWorldUpMatrix')
        # =====================================================================
        
        
        # Add controller to the anim set.======================================
        anim_set.addChild(
            *(hip_ctrl[''], spine_all_ctrl, hip_shake_ctrl, param)
        )
        anim_set.addChild(fk_ctrls)
        anim_set.addChild(*[x[''] for x in (hip_ik_ctrl, spine_ik_ctrl)])
        # =====================================================================
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////