# -*- coding:utf-8 -*-
from .. import rigScripts, node
cmds = node.cmds
func = rigScripts.func

Category = 'Utilties'
BaseName = 'simpleSpine'


class JointCreator(rigScripts.JointCreator):
    def process(self):
        from gris3.tools import jointEditor
        name = self.basenameObject()
        parent = self.parent()
        options = self.options()

        offset = 15
        startchar = func.Alphabet('A')
        spines = []
        for i in range(4):
            name.setName('spine' + startchar)
            spines.append(node.createNode('joint', n=name(), p=parent))
            spines[-1].setPosition((0.0, offset * i + 100.0, 0.0))
            spines[-1].setRadius(2)
            parent = spines[-1]
            startchar += 1

        # Fix joint orient.
        om = jointEditor.OrientationModifier()
        om.setSecondaryMode('vector')
        om.setApplyToChildren(False)
        om.setTargetUpAxis('-Z')
        om.execute(spines)

        # Unit setting.--------------------------------------------------------
        unit = self.unit()
        unit.addMember('startJoint', spines[0])
        unit.addMember('endJoint', spines[1])
        # ---------------------------------------------------------------------


class RigCreator(rigScripts.RigCreator):
    def process(self):
        def blendScaleAttr(srcAttrA, srcAttrB, dstAttr):

            # srcAttr.children() >> dstAttr.children()
            # return
            md = func.createUtil('multiplyDivide')
            srcAttrA.children() >> md.attr('input1').children()
            srcAttrB.children() >> md.attr('input2').children()
            md.attr('output').children() >> dstAttr.children()

        unit = self.unit()
        unitname = func.Name(self.unitName())
        basename = unitname.name()
        anim_set = self.animSet()

        spine_start_jnt = unit.getMember('startJoint')
        spine_end_jnt = unit.getMember('endJoint')

        if spine_end_jnt.hasChild():
            spine_end_jnt = spine_end_jnt.children()[0]

        spines_chain = func.listNodeChain(spine_start_jnt, spine_end_jnt)
        spines_jnt = spines_chain[1:-1]

        # ---------------------------------------------------------------------
        start_vector = func.Vector(
            cmds.xform(spine_start_jnt, q=True, ws=True, rp=True)
        )
        end_vector = func.Vector(
            cmds.xform(spine_end_jnt, q=True, ws=True, rp=True)
        )
        start_to_end = end_vector - start_vector


        # ルートノードを作成する。=============================================
        # リグ用の代理親ノードを作成する。
        parent_proxy = self.createRigParentProxy(spine_start_jnt, basename)

        # コントローラ用代理親ノードを作成する。
        ctrl_parent_proxy = self.createCtrlParentProxy(spine_start_jnt, basename)

        # IKセットアップ用グループを作成する。
        unitname.setName(basename + 'IkSetup')
        unitname.setNodeType('parentProxy')
        ik_setup_grp = node.createNode(
            'transform', n=unitname(), p=parent_proxy
        )
        # =====================================================================

        # リグ用のジョイントチェーンをコピーする。=============================
        spines_rigJnt = {}

        for key in ('ikJnt', 'fkJnt', 'combJnt'):
            parent = parent_proxy
            chains_list = []
            for joint in spines_chain:
                chains_list.append(func.copyNode(joint, key, parent)
                )
                parent = chains_list[-1]
            spines_rigJnt[key] = chains_list
        # =====================================================================

        # コントローラとその代理ノードを作成する。=============================
        root_ik_ctrlspace = {}
        root_ik_ctrl = {}
        spine_ik_ctrlspace = {}
        spine_ik_ctrl = {}

        # Create hip controller.-----------------------------------------------
        unitname.setName(basename+'Root')
        unitname.setNodeType('ctrlSpace')
        root_ctrl_space = node.createNode(
            'transform', n=unitname(), p=ctrl_parent_proxy
        )
        root_ctrl_space.setMatrix(spine_start_jnt.matrix())
        root_ctrl_space.lockTransform()

        unitname.setNodeType('ctrl')
        root_ctrl = node.createNode(
            'transform', n=unitname(), p=root_ctrl_space
        )
        root_ctrl.editAttr('s:a', k=False, l=True)
        root_ctrl.editAttr('v', k=False)
        # ---------------------------------------------------------------------

        for key, root_parent in zip(
                ['', 'Proxy'], [root_ctrl, ik_setup_grp]
            ):
            # Create root ik controller.
            unitname.setName(basename+'RootIk')
            unitname.setNodeType('ctrlSpace' + key)
            root_ik_ctrlspace[key] = node.createNode(
                'transform', n=unitname(), p=root_parent
            )
            root_ik_ctrlspace[key].setMatrix(spine_start_jnt.matrix())

            unitname.setNodeType('ctrl' + key)
            root_ik_ctrl[key] = node.createNode(
                'transform', n=unitname(), p=root_ik_ctrlspace[key]
            )
            func.lockTransform(
                [root_ik_ctrlspace[key], root_ik_ctrl[key]]
            )
            root_ik_ctrl[key].editAttr(('t:a', 'r:a'), k=True, l=False)

            # Create end ik controller.
            unitname.setName(basename+'Ik')
            unitname.setNodeType('ctrlSpace' + key)
            spine_ik_ctrlspace[key] = node.createNode(
                'transform', n=unitname(), p=root_parent
            )
            spine_ik_ctrlspace[key].setMatrix(spine_end_jnt.matrix())

            unitname.setNodeType('ctrl' + key)
            spine_ik_ctrl[key] = node.createNode(
                'transform', n=unitname(), p=spine_ik_ctrlspace[key]
            )
            func.lockTransform(
                [spine_ik_ctrlspace[key], spine_ik_ctrl[key]]
            )
            spine_ik_ctrl[key].editAttr(('t:a', 'r:a'), k=True, l=False)
            # -----------------------------------------------------------------

        rootik_twist = root_ik_ctrl[''].addFloatAttr(
            'twist', min=None, max=None, default=0
        )
        spineik_twist = spine_ik_ctrl[''].addFloatAttr(
            'twist', min=None, max=None, default=0
        )
        
        # Connect controller to proxy.
        for couple in [root_ik_ctrl, spine_ik_ctrl]:
            func.connectKeyableAttr(couple[''], couple['Proxy'])

        # Adds parameter controller for this spine.----------------------------
        unitname.setName(basename + 'Param')
        unitname.setNodeType('ctrl')
        param = node.createNode('transform', n=unitname(), p=root_ctrl)
        param_stretch = param.addFloatAttr('stretch', default=0)
        param_shrink = param.addFloatAttr('shrink', default=0)
        param_keepvol = param.addFloatAttr('keepVolume', default=0)
        param_slide = param.addFloatAttr('slide', default=1, min=0.001, max=10)

        pma = func.createUtil('plusMinusAverage')
        pma_input_attr = pma.attr('input3D')
        mdl = func.createUtil('multiplyDivide')
        mdl('input2', (0.5, 0.5, 0.5))
        for n in [
            root_ik_ctrlspace, root_ik_ctrl, spine_ik_ctrlspace, spine_ik_ctrl
        ]:
            n[''].attr('t') >> pma_input_attr.nextElement()

        pma.attr('output3D') >> mdl.attr('input1')
        mdl.attr('output') >> param.attr('t')
        param.lockTransform()
        # ---------------------------------------------------------------------
        # =====================================================================

        # /////////////////////////////////////////////////////////////////////
        # Create an ik controllers and the it's system.                      //
        # /////////////////////////////////////////////////////////////////////
        # Create ik system.====================================================
        # Create ik spline curve and ik that is driven by the curve.-----------

        unitname.setName(basename + 'Ik')
        unitname.setNodeType('crv')
        chain_positions = [x.rotatePivot() for x in spines_chain]
        ik_curve = func.asObject(
            cmds.rename(
                cmds.curve(d=1, p=chain_positions), unitname()
            )
        )
        ik_setup_grp.addChild(ik_curve)
        cmds.makeIdentity(ik_curve(), a=True, t=True, r=True, s=True)
        cmds.xform(ik_curve(), os=True, piv=[0, 0, 0])

        # Create ik spine.
        ik = cmds.ikHandle(
            sj=spines_rigJnt['ikJnt'][0], ee=spines_rigJnt['ikJnt'][-1],
            c=ik_curve, sol='ikSplineSolver', ccv=False, pcv=False
        )[0]
        unitname.setName(basename)
        unitname.setNodeType('ik')
        ik = func.asObject(cmds.rename(ik, unitname()))

        ik_setup_grp.addChild(ik)
        # ---------------------------------------------------------------------

        # Create transform to modify the curve shape.--------------------------
        index = 0
        cv_top_modifier_proxies = []
        cv_btm_modifier_proxies = []
        for joint in spines_rigJnt['ikJnt']:
            top_space = node.createNode('transform', p=spine_ik_ctrl['Proxy'])
            func.fitTransform(
                joint, top_space, rotate=False, scale=False
            )
            func.fitTransform(
                parent_proxy, top_space, translate=False, scale=False
            )

            btm_space = cmds.parent(
                cmds.duplicate(top_space)[0], root_ik_ctrl['Proxy']
            )[0]

            cv_top_modifier_proxies.append(top_space)
            cv_btm_modifier_proxies.append(func.asObject(btm_space))
        ratio_list = func.createMovementWeightList(cv_top_modifier_proxies)

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
                    root_ik_ctrl, root_ik_ctrlspace
                ]
            ], '%s.matrixIn' % hip_mltmtx
        )

        index = 0
        for top_mod, btm_mod, ratio in zip(
                cv_top_modifier_proxies, cv_btm_modifier_proxies, ratio_list
            ):
            pb = func.createUtil('pairBlend')
            ratio_attr = param.addFloatAttr('ikRatio%s' % index)
            ratio_attr >> pb.attr('w')
            ratio_attr.set(ratio)
            attr_index = 1
            for mod_node, ctrl_mtx in zip(
                    [btm_mod, top_mod], [hip_mltmtx, spine_mltmtx]
                ):
                pmm = func.createUtil('pointMatrixMult')
                ctrl_mtx.attr('matrixSum') >> pmm.attr('inMatrix')

                value = mod_node('t')[0]
                pmm('ip', value)
                
                func.connect3ChannelAttr(
                    '%s.o' % pmm, '%s.it%%s%s' % (pb, attr_index),
                    ignoreKeyable=True
                )
                attr_index += 1

            func.connect3ChannelAttr(
                '%s.ot' % pb, '%s.cp[%s].%%sValue' % (ik_curve, index)
            )
            index += 1
        cmds.delete(cv_top_modifier_proxies, cv_btm_modifier_proxies)
        # ---------------------------------------------------------------------
        # =====================================================================

        # ストレッチシステムの構築。===========================================
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

        start_loc = func.asObject(
            cmds.parent(
                cmds.rename(result_node['start'], start_loc),
                root_ik_ctrl['Proxy']
            )[0]
        )
        end_loc = func.asObject(
            cmds.parent(
                cmds.rename(result_node['end'], end_loc),
                spine_ik_ctrl['Proxy']
            )[0]
        )
        dist_node = func.asObject(
            cmds.parent(
                cmds.rename(result_node['result'], dist_node), ik_setup_grp
            )[0]
        )

        param.attr('stretch') >> dist_node.attr('stretch')
        param.attr('shrink') >> dist_node.attr('shrink')
        param.attr('keepVolume') >> dist_node.attr('volumeScale')
        # =====================================================================
        
        # スライド機能を差し込む。=============================================
        for j in spines_rigJnt['ikJnt'][1:]:
            tx = j.attr('tx')
            s_plug = tx.source(p=True)
            mdl = func.createUtil('multDoubleLinear')
            s_plug >> mdl.attr('i1')
            param_slide >> mdl.attr('i2')
            mdl.attr('o') >> tx
        # =====================================================================

        # ツイストアトリビュートの追加。=======================================
        rootik_twist >> ik.attr('roll')

        mdl = func.createUtil('multDoubleLinear')
        rootik_twist >> mdl.attr('input1')
        mdl('input2', -1, l=True)

        adl = func.createUtil('addDoubleLinear')
        spineik_twist >> adl.attr('input1')
        mdl.attr('output') >> adl.attr('input2')
        adl.attr('output') >> ik.attr('twist')
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
            
            ikj.attr('t').children() >> fkj.attr('t').children()
            if i == num - 1:
                continue
            ikj.attr('r').children() >> fkj.attr('r').children()

        # Create controllers and it's proxies.=================================
        # Create a root node for the all of fk controllers.--------------------
        unitname.setName(basename + 'FkCtrl')
        unitname.setNodeType('grp')
        fkctrl_parent = node.createNode(
            'transform', p=root_ctrl, n=unitname()
        )
        fkctrl_parent.setMatrix(parent_proxy.matrix())
        fkctrl_parent.lockTransform()
        # ---------------------------------------------------------------------

        # Create controller for an all of spines.------------------------------
        unitname.setName(basename + 'SpineAll')
        unitname.setNodeType('ctrlSpace')
        spine_all_space = func.copyNode(
            spines_rigJnt['fkJnt'][0], 'allCtrlSpace', fkctrl_parent
        )
        spine_all_space('drawStyle', 2)

        unitname.setNodeType('ctrl')
        spine_all_ctrl = node.createNode(
            'transform', n=unitname(), p=spine_all_space
        )
        func.lockTransform([spine_all_ctrl, spine_all_space])
        spine_all_ctrl.editAttr('r:a', k=True, l=False)
        # ---------------------------------------------------------------------

        locked_nodes = []
        fkjnt_parent = None
        fk_ctrls = []
        fk_auto_trs = []
        fk_ctrl_proxies = []
        ctrl_parent = spine_all_space
        vol_scale_ratio = dist_node.attr('volumeScaleRatio')
        for i in range(num-1):
            jnt = spines_rigJnt['fkJnt'][i]
            if fkjnt_parent:
                fkjnt_parent.addChild(jnt)
                jnt.setInverseScale()

            # Create fk controller proxy.--------------------------------------
            name = func.Name(jnt())
            name.setNodeType('ctrlProxy')
            ctrl_proxy = node.createNode('transform', p=jnt, n=name())

            fk_ctrl_proxies.append(ctrl_proxy)
            locked_nodes.append(ctrl_proxy)
            fkjnt_parent = ctrl_proxy
            # -----------------------------------------------------------------

            # Create fk controller.--------------------------------------------
            name.setNodeType('ctrlSpace')
            space = func.createSpaceNode(n=name(), p=ctrl_parent)
            if i != 0:
                func.copyJointState(jnt, space)
                func.connectKeyableAttr(jnt, space)
            else:
                pmm = func.createUtil('pointMatrixMult')
                jnt.attr('t').children() >> pmm.attr('ip').children()
                pmm('inMatrix', spine_all_space('inverseMatrix'), type='matrix')
                pmm.attr('o').children() >> space.attr('t').children()
                jnt.attr('r').children() >> space.attr('r').children()
                jnt.attr('s').children() >> space.attr('s').children()
            locked_nodes.append(space)

            name.setNodeType('autoTrs')
            auto_trs = node.createNode('joint', n=name(), p=space)
            auto_trs.hideDisplay()
            auto_trs.setInverseScale()
            spine_all_ctrl.attr('r').children() >> auto_trs.attr('r').children()

            vol_scale_ratio >> auto_trs.attr('sy')
            vol_scale_ratio >> auto_trs.attr('sz')
            
            name.setNodeType('ctrl')
            ctrl = node.createNode('joint', n=name(), p=auto_trs)
            ctrl.hide()
            ctrl.setInverseScale()
            ctrl.editAttr(['v'], k=False, l=False)

            func.createDecomposeMatrix(
                ctrl_proxy, ['%s.matrix' % x for x in [ctrl, auto_trs]]
            )
            locked_nodes.extend([auto_trs, space])
            fk_auto_trs.append(auto_trs)
            fk_ctrls.append(ctrl)
            ctrl_parent = ctrl
            # -----------------------------------------------------------------

        func.lockTransform(locked_nodes)
        # =====================================================================
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////

        # /////////////////////////////////////////////////////////////////////
        # Connects from rigged joints to final joints.                       //
        # /////////////////////////////////////////////////////////////////////
        # 開始ジョイントの接続。===============================================
        cst = func.localConstraint(
            cmds.parentConstraint,
            fk_ctrl_proxies[0], spines_rigJnt['combJnt'][0]
        )
        mltmtx = func.createUtil('multMatrix')
        plug = mltmtx.attr('matrixIn')
        i = (x for x in range(10))
        inv_mtx = node.MMatrixToFloat(
            root_ctrl_space._node().transformationMatrix().inverse() *
            root_ctrl._node().transformationMatrix().inverse()
        )

        spines_rigJnt['fkJnt'][0].attr('matrix') >> plug.elementAt(next(i))
        plug.elementAt(next(i)).set(inv_mtx, type='matrix')
        root_ctrl.attr('matrix') >> plug.elementAt(next(i))
        plug.elementAt(next(i)).set(
            root_ctrl_space('worldMatrix'), type='matrix'
        )
        mltmtx.attr('matrixSum') >> cst.attr('target[0].targetParentMatrix')

        (
            fk_ctrl_proxies[0].attr('s').children()
             >> spines_rigJnt['combJnt'][0].attr('s').children()
         )
        # blendScaleAttr(
            # fk_ctrl_proxies[0].attr('s'), spines_rigJnt['combJnt'][0].attr('s'),
            # param_keepvol
        # )
        # =====================================================================

        # 開始ジョイント以外のジョイントの接続。===============================
        # コントロールスペースの逆行列
        space_inv_mtx = root_ctrl_space._node().transformationMatrix().inverse()
        ctrl_inv_mtx = root_ctrl._node().transformationMatrix().inverse()
        inv_mtx = node.MMatrixToFloat(space_inv_mtx * ctrl_inv_mtx)

        inverse_matrices = [
            root_ctrl.attr('matrix'),
            root_ctrl_space.attr('matrix'),
            spines_rigJnt['combJnt'][0].attr('inverseMatrix')
        ]
        fk_start_jnt = spines_rigJnt['fkJnt'][0]
        for proxy, joint, ctrl, auto_trs in zip(
                fk_ctrl_proxies[1:], spines_rigJnt['combJnt'][1:-1], 
                fk_ctrls[1:], fk_auto_trs[1:]
            ):
            blendScaleAttr(
                ctrl.attr('s'), auto_trs.attr('s'), joint.attr('s')
            )

            cst = func.asObject(cmds.parentConstraint(proxy, joint)[0])
            # ParentMatrix側の処理。
            parent_nodes = func.listNodeChain(fk_start_jnt, proxy)[:-1]
            parent_nodes.reverse()
            mltmtx = func.createUtil('multMatrix')
            func.connectMultAttr(
                [x + '.matrix' for x in parent_nodes], mltmtx + '.matrixIn', 0
            )
            mltmtx.attr('matrixSum') >> cst.attr('target[0].targetParentMatrix')

            # ConstraintInverseMatrix側の処理。
            cst_inv_plug = cst.attr('constraintParentInverseMatrix')
            mltmtx = func.createUtil('multMatrix')
            mltmtx.attr('matrixIn').elementAt(0).set(inv_mtx, type='matrix')
            func.connectMultAttr(inverse_matrices, '%s.matrixIn' % mltmtx, 1)
            mltmtx.attr('matrixIn').elementAt(2).disconnect(True)
            mltmtx.attr('matrixSum') >> cst_inv_plug
            inverse_matrices.append('%s.inverseMatrix' % joint)
        # =====================================================================
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////

        # /////////////////////////////////////////////////////////////////////
        # 代理ジョイントからオリジナルのジョイントへの接続。                 //
        # /////////////////////////////////////////////////////////////////////
        for proxy, orig in zip(
                spines_rigJnt['combJnt'][:-1], spines_chain[:-1]
            ):
            func.connectKeyableAttr(proxy, orig)

        mdl = func.createUtil('multDoubleLinear')
        spines_rigJnt['combJnt'][-2].attr('sx') >> mdl.attr('input1')
        dist_node.attr('stretchRatio') >> mdl.attr('input2')
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
        creator.setRotation([0, 0, 90])
        creator.setColorIndex(22)
        creator.setCurveType('plane')
        creator.create(parentNode=root_ctrl)
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
        creator.setCurveType('circleArrow')
        creator.create(parentNode=spine_all_ctrl)
        
        size *= 0.8
        creator.setColorIndex(self.colorIndex('extra'))
        for ctrl in fk_ctrls:
            creator.setSizes([size, size, size])
            creator.create(parentNode=ctrl)
        # ---------------------------------------------------------------------

        # Adds shape to the spine ik controllers.------------------------------
        size *= 0.6
        creator.setRotation()
        creator.setSizes([size*0.2, size, size])
        creator.setCurveType('box')
        creator.setColorIndex(self.colorIndex('sub'))
        for ctrl in [root_ik_ctrl, spine_ik_ctrl]:
            shape = creator.create(parentNode=ctrl[''])
        # ---------------------------------------------------------------------
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////

        # /////////////////////////////////////////////////////////////////////
        # Post processes.                                                    //
        # /////////////////////////////////////////////////////////////////////
        # Set up advanced ik twist controls.===================================
        cmds.setAttr(ik + '.dTwistControlEnable', 1)
        cmds.setAttr(ik + '.dWorldUpType', 4)
        cmds.setAttr(ik + '.dWorldUpAxis', 0)
        cmds.setAttr(ik + '.dWorldUpVector', 0, 1, 0)
        cmds.setAttr(ik + '.dWorldUpVectorEnd', 0, 1, 0)
        cmds.connectAttr(
            spine_ik_ctrl['Proxy'] + '.worldMatrix[0]',
            ik + '.dWorldUpMatrixEnd'
        )
        cmds.connectAttr(
            root_ik_ctrl['Proxy'] + '.worldMatrix[0]',
            ik + '.dWorldUpMatrix'
        )
        # =====================================================================
        
        
        # Add controller to the anim set.======================================
        anim_set.addChild(root_ctrl, spine_all_ctrl, param)
        anim_set.addChild(*fk_ctrls)
        anim_set.addChild(*[x[''] for x in (root_ik_ctrl, spine_ik_ctrl)])
        # =====================================================================
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////