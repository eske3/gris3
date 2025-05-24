#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    IKスプラインとFK調整コントローラを付加するリグを提供するモジュール
    
    Dates:
        date:2017/09/17 19:56[Eske](eske3g@gmail.com)
        update:2024/05/17 10:25 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import rigScripts, node
cmds = node.cmds
func = rigScripts.func

Category = 'Utilties'
BaseName = 'ikFkChain'
Version = 2.0


class Option(rigScripts.Option):
    r"""
        IKコントローラの数を決めるオプションを定義するクラス。
    """
    def define(self):
        r"""
            オプション項目を設定する。
        """
        self.addIntOption('numberOfIkControls', default=5, min=3, max=100)
        self.addBoolOption('oldSpecification', default=False)


class JointCreator(rigScripts.JointCreator):
    r"""
        ジョイント作成用のクラス。
        始点と終点のみが作成される。
    """
    def process(self):
        r"""
            ジョイント作成を行う。始点と終点のジョイントのみ作成する。
        """
        from gris3.tools import jointEditor
        basename = self.baseName()
        name = self.basenameObject()
        parent = self.parent()
        options = self.options()

        offset = 15
        joints = []
        for i, suffix in enumerate(('Start', 'End')):
            name.setName(basename + suffix)
            joints.append(node.createNode('joint', n=name(), p=parent))
            joints[-1].setPosition((0.0, offset * i + 100.0, 0.0))
            joints[-1].setRadius(2)
            parent = joints[-1]

        # ジョイントの軸の設定を行う。
        om = jointEditor.OrientationModifier()
        om.setSecondaryMode('vector')
        om.setApplyToChildren(False)
        om.setTargetUpAxis('-Z')
        om.execute(joints)

        # ユニットの設定を行う。===============================================
        unit = self.unit()
        unit.addMember('startJoint', joints[0])
        unit.addMember('endJoint', joints[1])
        unit.addIntAttr(
            'numberOfIkControls', min=2, max=100,
            default=options.get('numberOfIkControls')
        )
        unit.addBoolAttr(
            'oldSpecification', default=options.get('oldSpecification')
        )
        # =====================================================================


class RigCreator(rigScripts.RigCreator):
    r"""
        IKスプラインとFK調整コントローラ機能を作成する。
    """
    def process(self):
        r"""
            リグを作成する。
        """
        def blendScaleAttr(srcAttrA, srcAttrB, dstAttr):
            r"""
                ２つのスケールアトリビュートをブレンドする。
                
                Args:
                    srcAttrA (str):入力スケールアトリビュートA
                    srcAttrB (str):入力スケールアトリビュートB
                    dstAttr (str):ブレンドされる対象スケールアトリビュート
            """
            md = func.createUtil('multiplyDivide')
            srcAttrA.children() >> md.attr('input1').children()
            srcAttrB.children() >> md.attr('input2').children()
            md.attr('output').children() >> dstAttr.children()

        unit = self.unit()
        unitname = func.Name(self.unitName())
        basename = unitname.name()
        anim_set = self.animSet()

        number_of_ctrl = unit('numberOfIkControls')
        use_old_style = True
        if unit.hasAttr('oldSpecification'):
            use_old_style = unit('oldSpecification')

        spline_start_jnt = unit.getMember('startJoint')
        spine_end_jnt = unit.getMember('endJoint')

        spline_chain = func.listNodeChain(spline_start_jnt, spine_end_jnt)
        spline_jnt = spline_chain[1:-1]

        # 各種ベクトルの取得。==================================================
        start_vector = func.Vector(
            cmds.xform(spline_start_jnt, q=True, ws=True, rp=True)
        )
        end_vector = func.Vector(
            cmds.xform(spine_end_jnt, q=True, ws=True, rp=True)
        )
        start_to_end = end_vector - start_vector
        # =====================================================================

        # ルートノードを作成する。=============================================
        # リグ用の代理親ノードを作成する。
        parent_proxy = self.createRigParentProxy(spline_start_jnt, basename)

        # コントローラ用代理親ノードを作成する。
        ctrl_parent_proxy = self.createCtrlParentProxy(
            spline_start_jnt, basename
        )

        # IKセットアップ用グループを作成する。
        unitname.setNodeType('parentProxy')
        unitname.setName(basename + 'IkSetup')
        ik_setup_grp = node.createNode(
            'transform', n=unitname(), p=parent_proxy
        )
        # =====================================================================

        # リグ用のジョイントチェーンをコピーする。=============================
        spline_rigJnt = {}

        for key in ('ikJnt', 'fkJnt', 'combJnt'):
            parent = parent_proxy
            chains_list = []
            for joint in spline_chain:
                chains_list.append(func.copyNode(joint, key, parent)
                )
                parent = chains_list[-1]
            spline_rigJnt[key] = chains_list
        # =====================================================================
        
        # IKコントローラとそのシステムを作成する。=============================
        # スプラインカーブとそのカーブによって動作するIK作成する。-------------
        ik, eff, curve = node.ikHandle(
            sj=spline_rigJnt['ikJnt'][0], ee=spline_rigJnt['ikJnt'][-1],
            sol='ikSplineSolver', scv=False, ns=4,pcv=False
        )
        unitname.setName(basename)
        unitname.setNodeType('ik')
        ik.rename(unitname())

        unitname.setName(basename + 'Ik')
        unitname.setNodeType('ikCrv')
        curve.rename(unitname())
        # カーブのリビルド。
        if use_old_style:
            if number_of_ctrl == 3:
                curve.shapes()[0].simpleRebuild(3, 2)
            else:
                cmds.rebuildCurve(
                    curve(), ch=False, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=0,
                    kt=0, s=number_of_ctrl-4, d=3, tol=0.01
                )
        else:
            if number_of_ctrl <= 3:
                curve.shapes()[0].simpleRebuild(1, number_of_ctrl-1)
            else:
                cmds.rebuildCurve(
                    curve(), ch=False, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=0,
                    kt=0, s=number_of_ctrl-3, d=3, tol=0.01
                )

        ik_setup_grp.addChild(ik, curve)
        cmds.makeIdentity(curve(), a=True, t=True, r=True, s=True)
        cmds.xform(curve(), os=True, piv=[0, 0, 0])
        # ---------------------------------------------------------------------

        # カーブシェイプを変形させるためのIKコントローラを作成する。-----------
        index_char = func.Alphabet('A')
        pad = len(str(number_of_ctrl))
        ik_ctrls = []
        ik_ctrl_spaces = []
        cv_pointers = []
        parent_matrix = ctrl_parent_proxy.matrix(False)

        for cv in cmds.ls(curve+'.cv[*]', fl=True):
            unitname.setName(basename+'Ik'+index_char.zfill(pad))
            index_char += 1
            unitname.setNodeType('ctrlSpace')
            space = node.createNode(
                'transform', p=ctrl_parent_proxy, n=unitname()
            )
            space.setPosition(cmds.pointPosition(cv))
            self.addLockedList(space)
            unitname.setNodeType('ctrl')
            ctrl = node.createNode('transform', p=space, n=unitname())
            ctrl.editAttr(['r:a', 's:a'], k=False, l=True)
            ctrl.editAttr(['v'], k=False)
            parent = ctrl
            ik_ctrls.append(ctrl)
            ik_ctrl_spaces.append(space)

            pmm = node.createUtil('pointMatrixMult')
            space.attr('matrix') >> pmm.attr('inMatrix')
            ~ctrl.attr('translate') >> ~pmm.attr('inPoint')
            pmm.attr('output') >> cv
            cv_pointers.append(pmm)

            # ワールド空間へのスイッチ機構の追加。-----------------------------
            world_plug = ctrl.addFloatAttr('world', 0)
            mltmtx = node.createNode('multMatrix')
            mltmtx('matrixIn[0]', space.matrix(False), type='matrix')
            mltmtx('matrixIn[1]', parent_matrix, type='matrix')
            ctrl_parent_proxy.attr('im') >> mltmtx/'matrixIn[2]'
            func.createDecomposeMatrix(space, [mltmtx/'matrixSum'], False)
            func.blendSelfConnection(space, world_plug, blendMode=1)
            # -----------------------------------------------------------------
        # ---------------------------------------------------------------------

        # パラメータを持つコントローラを作成する。-----------------------------
        unitname.setName(basename + 'Param')
        unitname.setNodeType('ctrl')
        param = node.createNode(
            'transform', n=unitname(), p=ctrl_parent_proxy
        )
        param_stretch = param.addFloatAttr('stretch', default=0)
        param_shrink = param.addFloatAttr('shrink', default=0)
        param_keepvol = param.addFloatAttr('keepVolume', default=0)
        rootik_twist = param.addFloatAttr(
            'rootTwist', min=None, max=None, default=0
        )
        end_twist = param.addFloatAttr(
            'endTwist', min=None, max=None, default=0
        )
        param.lockTransform()
        # ---------------------------------------------------------------------
        # =====================================================================

        # ストレッチシステムの構築。=============================================
        result_node = func.createTranslationStretchSystem(
            spline_rigJnt['ikJnt'][0], spline_rigJnt['ikJnt'][-1],
            distanceCurve=curve()
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
                ik_setup_grp
            )[0]
        )
        end_loc = func.asObject(
            cmds.parent(
                cmds.rename(result_node['end'], end_loc),
                ik_setup_grp
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

        # ツイストアトリビュートの追加。=======================================
        rootik_twist >> ik.attr('roll')

        mdl = func.createUtil('multDoubleLinear')
        rootik_twist >> mdl.attr('input1')
        mdl('input2', -1, l=True)

        adl = func.createUtil('addDoubleLinear')
        end_twist >> adl.attr('input1')
        mdl.attr('output') >> adl.attr('input2')
        adl.attr('output') >> ik.attr('twist')
        # =====================================================================
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////

        # /////////////////////////////////////////////////////////////////////
        # FKシステムをIKシステムの上階層として作成する。
        # /////////////////////////////////////////////////////////////////////
        # IK骨をFk骨へ接続する。
        num = len(spline_rigJnt['ikJnt'])
        for i in range(num):
            ikj = spline_rigJnt['ikJnt'][i]
            fkj = spline_rigJnt['fkJnt'][i]
            
            ikj.attr('t').children() >> fkj.attr('t').children()
            if i == num - 1:
                continue
            ikj.attr('r').children() >> fkj.attr('r').children()

        # コントローラとその代理ノードを作成する。===============================
        # すべてのFKのコントローラのルートを作成する。---------------------------
        unitname.setName(basename + 'FkCtrl')
        unitname.setNodeType('grp')
        fkctrl_parent = node.createNode(
            'transform', p=ctrl_parent_proxy, n=unitname()
        )
        fkctrl_parent.setMatrix(parent_proxy.matrix())
        fkctrl_parent.lockTransform()
        # ---------------------------------------------------------------------

        # FKコントローラをすべて同時に動かすオールコントローラを作成する。 ----
        unitname.setName(basename + 'FkAll')
        unitname.setNodeType('ctrlSpace')
        spline_all_space = func.copyNode(
            spline_rigJnt['fkJnt'][0], 'allCtrlSpace', fkctrl_parent
        )
        spline_all_space('drawStyle', 2)

        unitname.setNodeType('ctrl')
        spline_all_ctrl = node.createNode(
            'transform', n=unitname(), p=spline_all_space
        )
        func.lockTransform([spline_all_ctrl, spline_all_space])
        spline_all_ctrl.editAttr('r:a', k=True, l=False)
        # ---------------------------------------------------------------------

        locked_nodes = []
        fkjnt_parent = None
        fk_ctrls = []
        fk_auto_trs = []
        fk_ctrl_proxies = []
        ctrl_parent = spline_all_space
        vol_scale_ratio = dist_node.attr('volumeScaleRatio')
        for i in range(num-1):
            jnt = spline_rigJnt['fkJnt'][i]
            if fkjnt_parent:
                fkjnt_parent.addChild(jnt)
                jnt.setInverseScale()

            # FKコントローラの代理を作成する。---------------------------------
            name = func.Name(jnt())
            name.setNodeType('ctrlProxy')
            ctrl_proxy = node.createNode('transform', p=jnt, n=name())

            fk_ctrl_proxies.append(ctrl_proxy)
            locked_nodes.append(ctrl_proxy)
            fkjnt_parent = ctrl_proxy
            # -----------------------------------------------------------------

            # FKコントローラを作成する。 --------------------------------------
            name.setNodeType('ctrlSpace')
            space = func.createSpaceNode(n=name(), p=ctrl_parent)
            if i != 0:
                func.copyJointState(jnt, space)
                func.connectKeyableAttr(jnt, space)
            else:
                pmm = func.createUtil('pointMatrixMult')
                jnt.attr('t').children() >> pmm.attr('ip').children()
                pmm(
                    'inMatrix', spline_all_space('inverseMatrix'),
                    type='matrix'
                )
                pmm.attr('o').children() >> space.attr('t').children()
                jnt.attr('r').children() >> space.attr('r').children()
                jnt.attr('s').children() >> space.attr('s').children()
            # -----------------------------------------------------------------
            locked_nodes.append(space)

            name.setNodeType('autoTrs')
            auto_trs = node.createNode('joint', n=name(), p=space)
            auto_trs.hideDisplay()
            auto_trs.setInverseScale()
            (
                spline_all_ctrl.attr('r').children()
                >> auto_trs.attr('r').children()
            )

            vol_scale_ratio >> auto_trs.attr('sy')
            vol_scale_ratio >> auto_trs.attr('sz')
            
            name.setNodeType('ctrl')
            ctrl = node.createNode('joint', n=name(), p=auto_trs)
            ctrl.hideDisplay()
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
        # リグが入ったジョイントから最終ジョイントへ接続する。
        # /////////////////////////////////////////////////////////////////////
        # 開始ジョイント以外のジョイントの接続。===============================
        fk_start_jnt = spline_rigJnt['fkJnt'][0]
        parent = parent_proxy
        for proxy, joint, fk_joint, ctrl, auto_trs in zip(
                fk_ctrl_proxies,
                spline_rigJnt['combJnt'], spline_rigJnt['fkJnt'],
                fk_ctrls, fk_auto_trs
            ):
            blendScaleAttr(
                ctrl.attr('s'), auto_trs.attr('s'), joint.attr('s')
            )
            cst = node.asObject(cmds.parentConstraint(proxy, joint)[0])

            # ParentMatrix側の処理。
            proxy_space = proxy.parent()
            (
                proxy_space+'.matrix'
                >> cst.attr('target[0].targetParentMatrix')
            )
            cst.attr('cpim').disconnect()
            cst('cpim', node.identityMatrix(), type='matrix')
        # =====================================================================
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////

        # /////////////////////////////////////////////////////////////////////
        # 代理ジョイントからオリジナルのジョイントへの接続。                 //
        # /////////////////////////////////////////////////////////////////////
        for proxy, orig in zip(
                spline_rigJnt['combJnt'], spline_chain
            ):
            func.connectKeyableAttr(proxy, orig)

        mdl = func.createUtil('multDoubleLinear')
        spline_rigJnt['combJnt'][-2].attr('sx') >> mdl.attr('input1')
        dist_node.attr('stretchRatio') >> mdl.attr('input2')
        mdl.attr('o') >> spline_chain[-2].attr('sx')
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////

        # /////////////////////////////////////////////////////////////////////
        # 代理親のセットアップ。
        # /////////////////////////////////////////////////////////////////////
        parent_matrix = self.createParentMatrixNode(
            cmds.listRelatives(spline_start_jnt, p=True, pa=True)[0]
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
        # すべてのコントローラにシェイプを追加する。   
        # /////////////////////////////////////////////////////////////////////
        # Adds shape to the hip controller.------------------------------------
        creator = func.PrimitiveCreator()
        size = start_to_end.length() * 0.75

        # パラメータコントローラにシェイプを追加。 
        creator.setColorIndex((0.028, 0.148, 0.07))
        creator.setCurveType('line')
        crv = creator.create(parentNode=param)
        shape = crv.shapes()[0]
        cmds.curve(
            shape, replace=True, p=[x('output')[0] for x in cv_pointers]
        )
        for i, pmm in enumerate(cv_pointers):
            pmm.attr('o') >> '{}.cv[{}]'.format(shape, i)
        # ---------------------------------------------------------------------

        # FKコントローラにシェイプを追加。-------------------------------------
        size *= 0.4
        creator.setSize(size)
        creator.setColorIndex(self.colorIndex('sub'))
        creator.setRotation([0, 0, 90])
        creator.setCurveType('circleArrow')
        creator.create(parentNode=spline_all_ctrl)
        
        size *= 0.8
        creator.setColorIndex(self.colorIndex('extra'))
        pre_vec = func.Vector(spline_rigJnt['fkJnt'][1].position())
        for i in range(len(fk_ctrls)-1):
            vec = func.Vector(fk_ctrls[i].position())
            length = (pre_vec - vec).length()
            pre_vec = vec
            creator.setSize(length)
            creator.create(parentNode=fk_ctrls[i])
        creator.create(parentNode=fk_ctrls[-1])
        # ---------------------------------------------------------------------

        # Adds shape to the spine ik controllers.------------------------------
        # IKコントローラ用のシェイプを追加。  
        creator.setRotation()
        creator.setSize(start_to_end.length()/number_of_ctrl*0.5)
        creator.setCurveType('box')
        creator.setColorIndex(self.colorIndex('sub'))
        for ctrl in ik_ctrls:
            shape = creator.create(parentNode=ctrl)
        # ---------------------------------------------------------------------
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////        
        
        # Add controller to the anim set.======================================
        anim_set.addChild(param)
        fk_set = anim_set.addSet(
            basename+'Fk'+unitname.suffix(), unitname.position()
        )
        fk_set.addChild(spline_all_ctrl)
        fk_set.addChild(*fk_ctrls)
        ik_set = anim_set.addSet(
            basename+'Ik'+unitname.suffix(), unitname.position()
        )
        ik_set.addChild(*ik_ctrls)
        # =====================================================================
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////


def updateNewStyle1(targetUnits=None):
    r"""
        既存のユニットを最新版にアップデートするパッチ関数。

        Args:
            targetUnits (list):操作対象ユニット名
    """
    from .. import grisNode, core
    if not targetUnits:
        root = grisNode.getGrisRoot()
        unit_grp = root.unitGroup()
        targetUnits = unit_grp.listUnits()
    else:
        targetUnits = grisNode.listNodes(grisNode.Unit, targetUnits)
    for unit in targetUnits:
        if unit('unitName') != BaseName:
            continue
        if unit.hasAttr('oldSpecification'):
            continue
        unit.addBoolAttr('oldSpecification', default=False)
