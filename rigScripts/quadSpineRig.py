#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    四足歩行動物用の背骨リグ機能を提供するモジュール。

    Dates:
        date:2020/11/16 00:48 eske yoshinob[eske3g@gmail.com]
        update:2020/11/16 00:48 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2020 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from ..tools import jointEditor
from .. import rigScripts, func, node
cmds = func.cmds
math = func.math

Category = 'Quads'

'''
class Option(rigScripts.Option):
    def define(self):
        self.addFloatOption('spineBias', default=1.0, min=0.0, max=1.0)
        self.addIntOption('numberOfSpines', default=4, min=1, max=20)
        self.addBoolOption('newMode', default=1)
        self.addEnumOption(
            'defaultOrientation', default=0, enumerations=['x', 'y', 'z']
        )
        self.addStringOption('ID', default='0x02121')
'''


class JointCreator(rigScripts.JointCreator):
    def process(self):
        name = self.basenameObject()
        parent = self.parent()
        options = self.options()

        # Hip.
        name.setName('hip')
        hip = node.createNode('joint', n=name(), p=parent)
        hip.setPosition((0.0, 90.0, -43))
        hip.setRadius(2)

        # SpineA.
        name.setName('spineA')
        spineA = node.createNode('joint', n=name(), p=hip)
        spineA.setPosition((0.0, 93, -24))

        # SpineB
        name.setName('spineB')
        spineB = node.createNode('joint', n=name(), p=spineA)
        spineB.setPosition((0.0, 89, -6.6))

        # SpineC.
        name.setName('spineC')
        spineC = node.createNode('joint', n=name(), p=spineB)
        spineC.setPosition((-0.0, 87, 10))

        # SpineD.
        name.setName('spineD')
        spineD = node.createNode('joint', n=name(), p=spineC)
        spineD.setPosition((-0.0, 89, 29))

        # Fix joint orient.
        om = jointEditor.OrientationModifier()
        om.setSecondaryMode('vector')
        om.setApplyToChildren(False)
        om.setTargetUpAxis('+Y')
        om.execute([hip, spineA, spineB, spineC, spineD])

        # Unit setting.--------------------------------------------------------
        unit = self.unit()
        unit.addMember('hip', hip)
        unit.addMember('spineEnd', spineD)
        # ---------------------------------------------------------------------



class RigCreator(rigScripts.RigCreator):
    def listSpineWeights(self, surf, ctrllist):
        r"""
            背骨のウェイトを計算して返す。

            Args:
                surf (str):NURBSサーフェース名
                ctrllist (list):コントローラ名のリスト

            Returns:
                list:(node.Transform, float)を持つリスト
        """
        span_u = cmds.getAttr(surf + '.spansU')
        cvfmt = '%s.cv[%s][%s]'
        ctrlposlist = {
            x : func.Vector(cmds.xform(x, q=True, ws=True, rp=True))
            for x in ctrllist
        }

        poslist = []
        for u in range(span_u + 1):
            p0 = cmds.pointPosition(cvfmt % (surf, u, 0))
            p1 = cmds.pointPosition(cvfmt % (surf, u, 1))
            poslist.append(
                func.Vector([(x + y) * 0.5 for x, y in zip(p0, p1)])
            )

        result = []
        for p in poslist:
            lengthlist = {}
            templ, tempc = [], []
            for ctrl, ctrlpos in ctrlposlist.items():
                l = (p - ctrlpos).length()
                if l in lengthlist:
                    lengthlist[l].append(ctrl)
                else:
                    lengthlist[l] = [ctrl]
            ll = list(lengthlist.keys())
            ll.sort()
            for l in ll:
                for c in lengthlist[l]:
                    tempc.append(c)
                    templ.append(l)
                if len(tempc) > 2:
                    break
            
            tl = float(sum(templ[:2]))
            result.append(
                [(c, l / tl) for c, l in zip(tempc[:2], templ[:2])]
            )
        return result
        
    def process(self):
        unit = self.unit()
        unitname = func.Name(self.unitName())
        basename = unitname.name()
        anim_set = self.animSet()

        spine_start_jnt = unit.getMember('hip')
        spine_end_jnt = unit.getMember('spineEnd')

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
        # ---------------------------------------------------------------------

        # ルートノードの作成。=================================================
        # リグ用の代理親ノードを作成。
        parent_proxy = self.createRigParentProxy(spine_start_jnt, name=basename)

        # ikコントローラ用の代理親ノードの作成。
        ctrl_parent_proxy = self.createCtrlParentProxy(
            spine_start_jnt, basename
        )

        # IKセットアップグループを作成。
        unitname.setName(basename + 'IkSetup')
        unitname.setNodeType('parentProxy')
        ik_setup_grp = node.createNode(
            'transform', n=unitname(), p=parent_proxy
        )
        # =====================================================================

        # 元の背骨ジョイントからリグ用のジョイントチェーンを複製する。=========
        unitname.setName(basename+'IkJnt')
        unitname.setNodeType('grp')
        ik_joint_grp = node.createNode(
            'transform', n=unitname(), p=parent_proxy
        )
        spines_rigJnt = {}
        for key, isparent in zip(
            ('ikJnt', 'fkJnt', 'combJnt'), (False, True, True)
        ):
            parent = parent_proxy
            chains_list = []
            for joint in spines_chain:
                chains_list.append(func.copyNode(joint, key, parent))
                if isparent:
                    parent = chains_list[-1]
            spines_rigJnt[key] = chains_list
        spines_rigJnt['combJnt'][0].editAttr(['s:a'], k=False, l=True)
        # ---------------------------------------------------------------------
        # =====================================================================

        # コントローラとその代理ノードを作成する。=============================
        hip_ctrl = {}
        hip_ik_ctrlspace = {}
        hip_ik_ctrl = {}
        stomach_ik_ctrlspace = {}
        stomach_ik_ctrl = {}
        spine_ik_ctrlspace = {}
        spine_ik_ctrl = {}

        # 腰のコントローラを作成する。-----------------------------------------
        unitname.setName(basename+'Hip')
        unitname.setNodeType('ctrlSpace')
        hip_ctrl_space = node.createNode(
            'transform', n=unitname(), p=ctrl_parent_proxy
        )
        hip_ctrl_space.fitTo(spine_start_jnt, 0b1011)
        hip_ctrl_space.fitTo(parent_proxy, 0b0100)
        self.addLockedList(hip_ctrl_space)

        unitname.setNodeType('ctrl')
        hip_ctrl[''] = node.createNode(
            'transform', n=unitname(), p=hip_ctrl_space
        )
        hip_ctrl['Proxy'] = func.copyNode(
            spine_start_jnt, 'ctrlProxy', parent_proxy
        )
        func.localConstraint(
            cmds.parentConstraint, hip_ctrl[''], hip_ctrl['Proxy'],
            mo=True
        )
        self.addLockedList(hip_ctrl['Proxy'])
        hip_ctrl[''].lockTransform()
        hip_ctrl[''].editAttr(['t:a', 'r:a'], k=True, l=False)
        # ---------------------------------------------------------------------

        for key, root_parent, ctrltype in zip(
                ('', 'Proxy'),
                (hip_ctrl[''], ik_setup_grp),
                ('transform', 'joint')
            ):
            # 腰のIKコントローラを作成。
            unitname.setName(basename+'HipIk')
            unitname.setNodeType('ctrlSpace' + key)
            hip_ik_ctrlspace[key] = node.createNode(
                'transform', n=unitname(), p=root_parent
            )
            hip_ik_ctrlspace[key].fitTo(spine_start_jnt, 0b1000)
            hip_ik_ctrlspace[key].fitTo(parent_proxy, 0b0100)

            unitname.setNodeType('ctrl' + key)
            hip_ik_ctrl[key] = node.createNode(
                ctrltype, n=unitname(), p=hip_ik_ctrlspace[key]
            )

            # 腹のIKコントローラを作成。
            unitname.setName(basename+'StomachIk')
            unitname.setNodeType('ctrlSpace' + key)
            stomach_ik_ctrlspace[key] = node.createNode(
                'transform', n=unitname(), p=root_parent
            )

            unitname.setNodeType('ctrl' + key)
            stomach_ik_ctrl[key] = node.createNode(
                ctrltype, n=unitname(), p=stomach_ik_ctrlspace[key]
            )
            
            # 背骨のIKコントローラを作成。
            unitname.setName(basename+'Ik')
            unitname.setNodeType('ctrlSpace' + key)
            spine_ik_ctrlspace[key] = node.createNode(
                'transform', n=unitname(), p=root_parent
            )
            spine_ik_ctrlspace[key].fitTo(spine_end_jnt, 0b1000)
            spine_ik_ctrlspace[key].fitTo(parent_proxy, 0b0100)

            unitname.setNodeType('ctrl' + key)
            spine_ik_ctrl[key] = node.createNode(
                ctrltype, n=unitname(), p=spine_ik_ctrlspace[key]
            )

            cmds.delete(
                cmds.parentConstraint(
                    hip_ik_ctrl[key], spine_ik_ctrl[key],
                    stomach_ik_ctrlspace[key]
                )
            )
            self.addLockedList(
                [
                    hip_ik_ctrlspace[key], stomach_ik_ctrlspace[key], 
                    spine_ik_ctrlspace[key], 
                ]
            )
            func.lockTransform(
                [hip_ik_ctrl[key], stomach_ik_ctrl[key], spine_ik_ctrl[key]]
            )
            func.controlChannels(
                [hip_ik_ctrl[key], stomach_ik_ctrl[key], spine_ik_ctrl[key]],
                ['t:a', 'r:a'],
                isKeyable=True, isLocked=False
            )
            # -----------------------------------------------------------------

        twist_plugs = []
        for ctrl in (hip_ik_ctrl[''], spine_ik_ctrl['']):
            plug = ctrl.addFloatAttr(
                'twist', min=None, max=None, default=0
            )
            twist_plugs.append(plug)

        # コントローラから代理ノードへ接続する。
        for couple in [hip_ik_ctrl, stomach_ik_ctrl, spine_ik_ctrl]:
            func.connectKeyableAttr(couple[''], couple['Proxy'])

        # 背骨のパラメータ制御用コントローラを追加する。-----------------------
        unitname.setName(basename + 'Param')
        unitname.setNodeType('ctrl')
        param = node.createNode('transform', n=unitname(), p=hip_ctrl[''])
        keepvol_plug = param.addFloatAttr('keepVolume', default=0.5)
        
        pma = node.createUtil('plusMinusAverage')
        mdl = node.createUtil('multiplyDivide')
        mdl('input2', (0.5, 0.5, 0.5))
        index = 0
        for n in [
            hip_ik_ctrlspace, hip_ik_ctrl, spine_ik_ctrlspace, spine_ik_ctrl
        ]:
            n[''].attr('t') >> '%s.input3D[%s]'%(pma, index)
            index += 1
        pma.attr('output3D') >> mdl/'input1'
        mdl.attr('output') >> param/'t'
        self.addLockedList(param)
        # ---------------------------------------------------------------------
        # =====================================================================

        # /////////////////////////////////////////////////////////////////////
        # IKコントローラとそれを動かすシステムを作成。                       //
        # /////////////////////////////////////////////////////////////////////
        # IKシステムの構築。===================================================
        # 背骨ジョイントを動かすサーフェイスを作成する。-----------------------
        unitname.setName(basename + 'IkA')
        unitname.setNodeType('crv')
        chain_positions = [x.rotatePivot() for x in spines_chain]
        ik_curveA = cmds.rename(
            cmds.curve(d=1, p=chain_positions), unitname()
        )
        ik_curveA = node.parent(ik_curveA, ik_setup_grp)[0]
        cmds.makeIdentity(ik_curveA, a=True, t=True, r=True, s=True)
        cmds.xform(ik_curveA, os=True, piv=[0, 0, 0])

        unitname.setName(basename + 'IkB')
        ik_curveB = node.rename(cmds.duplicate(ik_curveA)[0], unitname())
        
        total_length = sum(func.listLength(spines_chain)) * 0.1

        posmtx = func.FMatrix(spines_chain[0].matrix())
        y_vector = func.Vector(posmtx.columns()[1][:3])
        y_vector = y_vector.norm() * total_length
        cmds.move(y_vector.x, y_vector.y, y_vector.z, ik_curveA)
        cmds.move(-y_vector.x, -y_vector.y, -y_vector.z, ik_curveB)

        unitname.setName(basename + 'IK')
        unitname.setNodeType('surf')
        ik_surf = node.parent(
            cmds.rename(
                cmds.loft(
                    ik_curveA, ik_curveB,
                    ch=0, u=1, c=0, ar=1, d=1, ss=1, rn=0, po=0, rsn=True
                )[0], unitname()
            ), ik_setup_grp
        )[0]
        cmds.makeIdentity(ik_surf, a=True, t=True, r=True, s=True)
        cmds.rebuildSurface(
            ik_surf, ch=0, rpo=1, rt=1, end=1, kr=0, kcp=0, kc=0, su=7, du=1,
            sv=1, dv=1, tol=0.01, fr=0,  dir=2
        )
        cmds.delete(ik_curveA, ik_curveB)

        arclen = node.createUtil('arcLengthDimension', p=ik_setup_grp)
        ik_surf.attr('local') >> arclen/'nurbsGeometry'
        arclen('uParamValue', 1.0)
        arclen('vParamValue', 0.5)

        # 背骨IKを作成。-------------------------------------------------------
        fitter = func.SurfaceFitter(ik_surf)
        ik_fitted_space = node.createNode(
            'transform', n='offset_' + spines_rigJnt['ikJnt'][0], p=ik_joint_grp
        )
        func.localConstraint(
            cmds.parentConstraint, hip_ik_ctrl['Proxy'], ik_fitted_space
        )
        spines_rigJnt['ikJnt'][0] = node.parent(
            spines_rigJnt['ikJnt'][0], ik_fitted_space
        )[0]
        spines_rigJnt['ikFittedJnt'] = [
            {'space':ik_fitted_space, 'joint':spines_rigJnt['ikJnt'][0]}
        ]

        parent = spines_rigJnt['ikJnt'][0]
        for joint in spines_rigJnt['ikJnt'][1:-1]:
            fitted = fitter.fit([joint])
            space = node.parent(fitted[0][-1], parent)[0]
            spines_rigJnt['ikFittedJnt'].append(
                {
                    'space':space,
                    'joint':fitted[0][-1].children(type='joint')[0]
                }
            )
            parent = spines_rigJnt['ikFittedJnt'][-1]['joint']
        
        ik_fitted_space = node.createNode(
            'transform', n='offset_' + spines_rigJnt['ikJnt'][-1], p=parent
        )
        cmds.parentConstraint(spine_ik_ctrl['Proxy'], ik_fitted_space)
        spines_rigJnt['ikJnt'][-1] = cmds.parent(
            spines_rigJnt['ikJnt'][-1], ik_fitted_space
        )[0]
        spines_rigJnt['ikFittedJnt'].append(
            {'space':ik_fitted_space, 'joint':spines_rigJnt['ikJnt'][-1]}
        )
        # ---------------------------------------------------------------------

        # IKコントローラー内のジョイントでカーブをバインドする。---------------
        ctrl_weights = self.listSpineWeights(
            ik_surf,
            [x['Proxy'] for x in (hip_ik_ctrl, stomach_ik_ctrl, spine_ik_ctrl)]
        )
        for i, point_weights in enumerate(ctrl_weights):
            pb_weight = (
                (math.cos(point_weights[0][1] * math.pi + math.pi) + 1) * 0.5
            )
            for v in range(2):
                cv_name = '%s.cv[%s][%s]' % (ik_surf, i, v)
                pb = node.createUtil('pairBlend')
                for j, c in enumerate(point_weights, 1):
                    parent = c[0].parent()
                    mltmtx = node.createUtil('multMatrix')
                    c[0].attr('matrix') >> mltmtx/'matrixIn[0]'
                    parent.attr('matrix') >> mltmtx/'matrixIn[1]'

                    dmy = node.createNode('transform', p=c[0])
                    wpos = cmds.pointPosition(cv_name, w=True)
                    cmds.xform(dmy, ws=True, t=wpos)
                    pmm = node.createUtil('pointMatrixMult')
                    pmm('ip', dmy('t')[0])
                    mltmtx.attr('matrixSum') >> pmm/'inMatrix'
                    
                    cmds.delete(dmy)
                    pmm.attr('o') >> '%s.it%s'%(pb, j)
                pb.attr('ot') >> cv_name
                pb('w', pb_weight)
        # ---------------------------------------------------------------------
        # =====================================================================

        # ストレッチシステムの作成。===========================================
        cndt_list = func.createStretchCalculator(
            ik_surf, arclen + '.al', arclen('al')
        )
        # 後でスケールコントローラが変わった場合の保険として、
        # 一度変数に入れておく。
        scale_ctrlproxy = ik_surf

        scale_ctrlproxy('stretch', 1)
        scale_ctrlproxy('shrink', 1)
        keepvol_plug >> scale_ctrlproxy+'.volumeScale'
        # =====================================================================
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////


        # /////////////////////////////////////////////////////////////////////
        # IKシステムの上にFKを追加作成する。                                 //
        # /////////////////////////////////////////////////////////////////////
        # IK骨からFK骨へ接続する。
        num = len(spines_rigJnt['ikJnt'])
        for i in range(num):
            ikj = spines_rigJnt['ikFittedJnt'][i]['joint']
            ikj_space = spines_rigJnt['ikFittedJnt'][i]['space']
            fkj = spines_rigJnt['fkJnt'][i]

            cst = func.localConstraint(
                cmds.parentConstraint,
                ikj, fkj, parents=[[ikj_space + '.matrix']]
            )

        # コントローラとその代理ノードを作成する。=============================
        # 全てのFKコントローラの親ノードを作成する。---------------------------
        unitname.setName(basename + 'FkCtrl')
        unitname.setNodeType('grp')
        fkctrl_parent = node.createNode(
            'transform', p=hip_ctrl[''], n=unitname()
        )
        fkctrl_parent.fitTo(parent_proxy)
        self.addLockedList(fkctrl_parent)
        # ---------------------------------------------------------------------

        # FKコントローラ用の腰位置の代理ノードを作成する。---------------------
        fkhip_posproxy = func.copyNode(
            spines_rigJnt['fkJnt'][0], 'fkCtrlSpace', fkctrl_parent
        )
        fkhip_posproxy('drawStyle', 2)
        ~spines_rigJnt['fkJnt'][0].attr('t') >> ~fkhip_posproxy.attr('t')
        ~spines_rigJnt['fkJnt'][0].attr('r') >> ~fkhip_posproxy.attr('r')
        # ---------------------------------------------------------------------

        # すべての背骨のコントローラを作成する。-------------------------------
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
        self.addLockedList(spine_all_space)
        spine_all_ctrl.lockTransform()
        spine_all_ctrl.editAttr(['r:a'], k=True, l=False)
        # ---------------------------------------------------------------------

        locked_nodes = []
        fk_ctrls = []
        fk_sub_ctrls = []
        fk_ctrl_proxies = []
        ctrl_parent = spine_all_space
        for i in range(1, num):
            # FKコントローラの代理ノードを作成する。---------------------------
            jnt = spines_rigJnt['fkJnt'][i]
            name = func.Name(jnt)
            name.setNodeType('ctrlProxy')
            ctrl_proxy = node.createNode('transform', p=jnt, n=name())
            
            fk_ctrl_proxies.append(ctrl_proxy)
            locked_nodes.append(ctrl_proxy)
            
            name.setNodeType('ctrlRev')
            ctrl_rev = node.createNode('transform', p=ctrl_proxy, n=name())
            
            if i < num - 1:
                spines_rigJnt['fkJnt'][i+1] = node.parent(
                    spines_rigJnt['fkJnt'][i+1], ctrl_rev
                )[0]
                cmds.connectAttr(
                    ctrl_proxy + '.s', spines_rigJnt['fkJnt'][i+1] + '.is',
                    f=True
                )
            # -----------------------------------------------------------------

            # FKコントローラを作成する。---------------------------------------
            name.setNodeType('ctrlSpace')
            space = func.createSpaceNode(n=name(), p=ctrl_parent)
            if i != 1:
                func.copyJointState(jnt, space)
                func.connectKeyableAttr(jnt, space)
            if len(fk_ctrls):
                md = node.createUtil('multiplyDivide')
                auto_trs = fk_ctrls[-1].parent()
                fk_ctrls[-1].attr('s') >> md/'i1'
                auto_trs.attr('s') >> md/'i2'
                md.attr('o') >> space/'inverseScale'

            locked_nodes.append(space)

            name.setNodeType('autoTrs')
            auto_trs = node.createNode('transform', n=name(), p=space)
            ~spine_all_ctrl.attr('r') >> ~auto_trs.attr('r')
            vol_ratio_plug = scale_ctrlproxy.attr('volumeScaleRatio')
            vol_ratio_plug >> (auto_trs/'sy', auto_trs/'sz')
            name.setNodeType('ctrl')
            ctrl = node.createNode('transform', n=name(), p=auto_trs)
            
            name.setName(name.name() + 'Sub')
            name.setNodeType('ctrl')
            sub_ctrl = node.createNode('transform', n=name(), p=ctrl)
            func.lockTransform([ctrl, sub_ctrl])
            func.controlChannels(
                [ctrl, sub_ctrl],
                ['t:a', 'r:a', 's:a'], isKeyable=True, isLocked=False
            )
            func.createDecomposeMatrix(ctrl_rev, [sub_ctrl + '.inverseMatrix'])
            decmtx, mltmtx = func.createDecomposeMatrix(
                ctrl_proxy, [
                    '%s.matrix' % x for x in [sub_ctrl, ctrl, auto_trs]
                ]
            )
            for ax in func.Axis[1:]:
                cmds.disconnectAttr(
                    '%s.os%s' % (decmtx, ax), '%s.s%s' % (ctrl_proxy, ax)
                )

            locked_nodes.extend([auto_trs, space])
            fk_ctrls.append(ctrl)
            fk_sub_ctrls.append(sub_ctrl)
            ctrl_parent = ctrl
            # -----------------------------------------------------------------
        self.addLockedList(locked_nodes)
        # =====================================================================
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////

        # /////////////////////////////////////////////////////////////////////
        # ヒップシェイクコントローラを作成。                                 //
        # /////////////////////////////////////////////////////////////////////
        unitname.setName(basename + 'HipShake')
        unitname.setNodeType('ctrlPos')
        ctrl_pos = node.rename(
            cmds.duplicate(fkhip_posproxy, po=True)[0], unitname()
        )
        ~spines_rigJnt['fkJnt'][0].attr('t') >> ~ctrl_pos.attr('t')
        ~spines_rigJnt['fkJnt'][0].attr('r') >> ~ctrl_pos.attr('r')
        
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

        # FKの腰骨と代理ノードにスケールアトリビュートを接続する。
        for target in [fkhip_posproxy]:
            ~hip_shake_ctrl.attr('s') >> ~target.attr('s')
        md = node.createUtil('multiplyDivide')
        for axis in func.Axis:
            src_attr = hip_shake_ctrl.attr('s%s'%axis)
            dst_attr = spines_chain[0].attr('s%s'%axis)
            if axis == 'x':
                src_attr >> dst_attr
                continue

            src_attr >> '%s.i1%s'%(md, axis)
            vol_ratio_plug >> '%s.i2%s'%(md, axis)
            '%s.o%s'%(md, axis) >> dst_attr


        self.addLockedList([hip_shake_ctrl, ctrl_pos, space, fkhip_posproxy])
        hip_shake_ctrl.editAttr(['t:a', 'r:a', 's:a'], k=True, l=False)
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////

        # /////////////////////////////////////////////////////////////////////
        # リグジョイントから最終ジョイントへ接続。                           //
        # /////////////////////////////////////////////////////////////////////
        # 腰骨-----------------------------------------------------------------
        cst = cmds.parentConstraint(
            temp_hip_shake_proxy, spines_rigJnt['combJnt'][0]
        )[0]

        mltmtx = node.createUtil('multMatrix')
        hip_shake_ctrl.attr('matrix') >> mltmtx/'matrixIn[0]'
        mltmtx('matrixIn[1]', space('matrix'), type='matrix')
        spines_rigJnt['fkJnt'][0].attr('matrix') >> mltmtx/'matrixIn[2]'
        mltmtx('matrixIn[3]', hip_ctrl['Proxy']('im'), type='matrix')
        hip_ctrl['Proxy'].attr('matrix')  >> mltmtx/'matrixIn[4]'

        mltmtx.attr('matrixSum') >> cst+'.target[0].targetParentMatrix'
        plugs = cmds.listConnections(
            cst + '.constraintParentInverseMatrix',
            s=True, d=False, p=True, c=True
        )
        cmds.disconnectAttr(plugs[1], plugs[0])
        cmds.setAttr(
            plugs[0], func.FMatrix().asList(),
            type='matrix'
        )
        # ---------------------------------------------------------------------

        # 腰FKとヒップシェイプを最終骨にブレンドする。-------------------------
        mltmtx = node.createUtil('multMatrix')
        decmtx_a = node.createUtil('decomposeMatrix')
        mltmtx.attr('matrixSum') >> decmtx_a/'inputMatrix'
        nodelist = [
            (temp_hip_shake_proxy, False), (hip_shake_ctrl, True),
            (space, False), (ctrl_pos, True)
        ]
        index = 0
        for n, connecting in nodelist:
            out_plug = n.attr('matrix')
            in_plug = '%s.matrixIn[%s]' % (mltmtx, index)
            if connecting:
                out_plug >>in_plug
            else:
                cmds.setAttr(in_plug, out_plug.get(), type='matrix')
            index += 1

        hip_ikrig_jntproxy = func.Name(spine_start_jnt)
        hip_ikrig_jntproxy.setNodeType('ikFkJntProxy')
        hip_ikrig_jntproxy = node.createNode(
            'transform', n=hip_ikrig_jntproxy(), p=parent_proxy
        )
        for attr in ['t', 'r']:
            ~decmtx_a.attr('o'+attr) >> ~hip_ikrig_jntproxy.attr(attr)
        self.addLockedList(hip_ikrig_jntproxy)
        # ---------------------------------------------------------------------

        # テンポラリノードへの後処理。-----------------------------------------
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
                fk_ctrl_proxies, spines_rigJnt['combJnt'][1:], 
            ):
            cst = cmds.parentConstraint(proxy, joint)[0]
            parent_nodes = func.listNodeChain(fk_start_jnt, proxy)[:-1]
            parent_nodes.reverse()
            mltmtx = node.createUtil('multMatrix')
            func.connectMultAttr(
                [x + '.matrix' for x in parent_nodes], mltmtx + '.matrixIn', 0
            )
            mltmtx.attr('matrixSum') >> cst+'.target[0].targetParentMatrix'

            if len(inverse_matrices) == 1:
                mtxattr = inverse_matrices[0]
            else:
                mltmtx = node.createUtil('multMatrix')
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
        unused_md = cmds.listConnections(
            spines_chain[0] + '.sy', s=True, d=False, type='multiplyDivide'
        )
        
        fk_ctrl_B = [''] + fk_ctrls
        num = len(spines_chain)
        i = 0
        for proxy, orig, ctrl, sub_ctrl in zip(
            spines_rigJnt['combJnt'], spines_chain,
            [''] + fk_ctrls, [''] + fk_sub_ctrls
        ):
            i += 1
            ~proxy.attr('t') >> ~orig.attr('t')
            ~proxy.attr('r') >> ~orig.attr('r')
            if not cmds.listConnections(orig + '.sx', s=True, d=False):
                proxy.attr('sx') >> orig.attr('sx')

            if not ctrl:
                proxy.attr('sy') >> orig.attr('sy')
                proxy.attr('sz') >> orig.attr('sz')
                continue

            ctrl_md = node.createUtil('multiplyDivide')
            ctrl.attr('s') >> ctrl_md/'input1'
            sub_ctrl.attr('s') >> ctrl_md/'input2'
            
            if i == num:
                ctrl_md.attr('o') >> orig/'s'
                continue
            ctrl_md.attr('ox') >> proxy/'sx'

            mdA = node.createUtil('multiplyDivide')
            for ax in ('y', 'z'):
                vol_ratio_plug >> '%s.i1%s'%(mdA, ax)
                ctrl_md.attr('o'+ax) >> '%s.i2%s'%(mdA, ax)
                mdA.attr('o'+ax) >> '%s.s%s'%(orig, ax)

        # 不要なmultiplyDivideを削除する。
        if unused_md:
            for md in unused_md:
                if not cmds.listConnections(md, d=True, s=False):
                    cmds.delete(md)
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////

        # /////////////////////////////////////////////////////////////////////
        # 親の代理ノードをセットアップする。                                 //
        # /////////////////////////////////////////////////////////////////////
        parent_matrix = self.createParentMatrixNode(spine_start_jnt.parent())
        if parent_matrix:
            decmtx = func.createDecomposeMatrix(
                ctrl_parent_proxy, ['%s.matrixSum' % parent_matrix],
                withMultMatrix=False
            )[0]
        self.addLockedList(ctrl_parent_proxy)
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////

        
        # /////////////////////////////////////////////////////////////////////
        # シェイプをコントローラに追加する。                                 //
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
            creator.setSize(size)
            creator.create(parentNode=ctrl)
        creator.setCurveType('circleArrow')
        size *= 0.9
        for ctrl in fk_sub_ctrls:
            creator.setSize(size)
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
        creator.setSizes([size, size, size*0.2])
        creator.setCurveType('box')
        creator.setColorIndex(self.colorIndex('sub'))
        for ctrl in [hip_ik_ctrl, stomach_ik_ctrl, spine_ik_ctrl]:
            shape = creator.create(parentNode=ctrl[''])
        # ---------------------------------------------------------------------
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////


        # /////////////////////////////////////////////////////////////////////
        # 後処理。                                                           //
        # /////////////////////////////////////////////////////////////////////
        # 伸縮率のインジケータを追加する。=====================================
        unitname.setName(basename + 'Indctr')
        unitname.setNodeType('trsSpace')
        indicator_space = node.createNode(
            'transform', n=unitname(), p=ctrl_parent_proxy
        )
        indicator_space('inheritsTransform', 0)
        self.addLockedList(indicator_space)

        unitname.setNodeType('trs')
        indicator = cmds.curve(d=1, p=((0, 0, 1), (0, 0, 0)), n=unitname())
        indicator = node.parent(indicator, indicator_space)[0]
        indicator.lockTransform(k=False, l=False)
        curve_shape = indicator.shapes(typ='nurbsCurve')[0]
        curve_shape('ihi', 0)
        curve_shape('v', 0, l=True)

        arclen = node.createUtil('arcLengthDimension', p=indicator)
        curve_shape.attr('worldSpace') >> arclen/'nurbsGeometry'
        arclen('uParamValue', 1)
        arclen('overrideEnabled', 1)
        arclen('overrideColor', 14)

        ik_surf.attr('stretchRatio') >> curve_shape/'cv[0].zValue'

        cst = cmds.parentConstraint(
            hip_ik_ctrl[''], spine_ik_ctrl[''], indicator_space
        )[0]
        func.controlChannels([cst], cmds.listAttr(cst, k=True), k=False)
        # =====================================================================


        # Add controller to the anim set.======================================
        anim_set.addChild(
            [hip_ctrl[''], spine_all_ctrl, hip_shake_ctrl, param]
        )
        anim_set.addChild(fk_ctrls)
        anim_set.addChild(fk_sub_ctrls)
        anim_set.addChild(
            [x[''] for x in (hip_ik_ctrl, stomach_ik_ctrl, spine_ik_ctrl)]
        )
        # =====================================================================
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////