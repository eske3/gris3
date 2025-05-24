# -*- coding:utf-8 -*-
import string

from gris3 import rigScripts, node
func = rigScripts.func
cmds = func.cmds

Sides = ['L', 'R']

class JointCreator(rigScripts.JointCreator):
    def process(self):
        from gris3.tools import jointEditor
        name = self.basenameObject()
        parent = self.parent()

        # ルートの作成。
        name.setName('eyeBallRoot')
        name.setNodeType('trs')
        root = node.createNode('transform', n=name(), p=parent)
        root.setPosition((0.0, 168.8, -0.2))
        root('rotate', (180, 0, 90))

        # ジョイント軸補正機能を呼び出す。
        name.setNodeType('jnt')
        om = jointEditor.OrientationModifier()
        om.setSecondaryMode('vector')
        om.setApplyToChildren(True)

        root_eyss = {}
        target_eyes = {}
        for side in func.SuffixIter():
            if side == 'R':
                x_factor = -1
                om.setPrimaryAxis('-X')
                om.setTargetUpAxis('+Y')
            else:
                x_factor = 1
                om.setPrimaryAxis('+X')
                om.setTargetUpAxis('-Y')

            # 目のジョイントを作成する。
            name.setPosition(side)
            name.setName('eye')
            eye_base = node.createNode('joint', n=name(), p=root)
            eye_base.setPosition((x_factor*2.5, 176, 4))

            name.setName('eyeEnd')
            eye_end = node.createNode('joint', n=name(), p=eye_base)
            eye_end.setPosition((x_factor*2.5, 176, 40))

            # ジョイントの軸を修正する。
            om.execute([eye_base])
            root_eyss[side] = eye_base
            target_eyes[side] = eye_end

        # Unit setting.--------------------------------------------------------
        unit = self.unit()
        unit.addMember('root', root)
        unit.addMember('eyeL', root_eyss['L'])
        unit.addMember('targetL', target_eyes['L'])
        unit.addMember('eyeR', root_eyss['R'])
        unit.addMember('targetR', target_eyes['R'])
        # ---------------------------------------------------------------------


class RigCreator(rigScripts.RigCreator):
    def process(self):
        unit = self.unit()
        unitname = self.unitName()
        basename = unitname.name()
        anim_set = self.animSet()

        # ルートノードを取得する。
        root_node = unit.getMember('root')

        # ルートの作成。=======================================================
        # リグ用の代理親を作成する。
        parent_proxy = self.createRigParentProxy(root_node, basename)

        # コントローラ用の代理親を作成する。
        ctrl_parent_proxy = self.createCtrlParentProxy(root_node, basename)
        # =====================================================================

        # ルートノードにまつわるセットアップ。=================================
        root_trs = {}
        for key, parent in zip(
                ['', 'Proxy'], [ctrl_parent_proxy, parent_proxy]
            ):
            unitname.setName(basename + 'Root')
            unitname.setNodeType('trsSpace' + key)
            root_trs[key] = node.createNode(
                'transform', n=unitname(), p=parent
            )
            root_trs[key].fitTo(root_node)
            root_trs[key].lockTransform()
        # =====================================================================

        # 目と視線の先となるジョイントをリグ用としてコピーする。===============
        base_joint = {}
        end_joint = {}
        base_proxy = {}
        for side in ['L', 'R']:
            base_joint[side] = unit.getMember('eye%s' % side)
            end_joint[side] = unit.getMember('target%s' % side)
            base_proxy[side] = func.copyNode(
                base_joint[side], 'jntProxy', root_trs['Proxy']
            )
        # =====================================================================

        # コントローラとその代理ノードを作成する。=============================
        target_pos_l = end_joint['L'].position()
        target_pos_r = end_joint['R'].position()
        target_pos = [(x+y)*0.5 for x, y in zip(target_pos_l, target_pos_r)]

        aim_ctrlspace = {}
        aim_ctrl = {}
        aim_ctrl_s = {'L':{}, 'R':{}}
        for key in ['', 'Proxy']:
            # Create aim controller for the both eyes.-------------------------
            unitname.setPosition('None')
            unitname.setName(basename + 'EyeAim')
            unitname.setNodeType('ctrlSpace' + key)
            aim_ctrlspace[key] = node.createNode(
                'transform', n=unitname(), p=root_trs[key]
            )
            aim_ctrlspace[key].setPosition(target_pos)

            unitname.setNodeType('ctrl' + key)
            aim_ctrl[key] = node.createNode(
                'transform', n=unitname(), p=aim_ctrlspace[key]
            )
            aim_ctrl[key].lockTransform()
            aim_ctrl[key].editAttr(['t:a'], k=True, l=False)
            #------------------------------------------------------------------

            for side, pos in zip(Sides, [target_pos_l, target_pos_r]):
                unitname.setPosition(side)
                unitname.setName(basename + 'EyeAim')
                unitname.setNodeType('ctrlSpace' + key)

                # 片面の目のエイムコントローラを作成する。
                space = node.createNode(
                    'transform', n=unitname(), p=aim_ctrl[key]
                )
                space.setPosition(pos)

                unitname.setNodeType('ctrl' + key)
                aim_ctrl_s[side][key] = node.createNode(
                    'transform', n=unitname(), p=space
                )
                space, aim_ctrl_s[side][key].lockTransform()
                aim_ctrl_s[side][key].editAttr(['t:a'], k=True, l=False)
        world_plug = aim_ctrl[''].addFloatAttr(
            'world', min=0, max=1, default=0
        )

        # コントローラから代理ノードへ接続する。
        for couple in [aim_ctrl, aim_ctrl_s['L'], aim_ctrl_s['R']]:
            func.connectKeyableAttr(couple[''], couple['Proxy'])

        for couple in [aim_ctrlspace]:
            func.connectKeyableAttr(couple['Proxy'], couple[''])
            couple['Proxy'].lockTransform()
            couple[''].lockTransform()
        # =====================================================================


        # /////////////////////////////////////////////////////////////////////
        # Creates aim constraint to base joint.                              //
        # /////////////////////////////////////////////////////////////////////
        for side in Sides:
            x_factor = -1 if side == 'R' else 1
            world_matrix = base_proxy[side].matrix()
            up_vector = world_matrix[8:11]
            dot = sum([x * y for x, y in zip(up_vector, [0, 1, 0])])
            up_vector_factor = 1 if dot > 0 else -1

            c = cmds.aimConstraint(
                aim_ctrl_s[side]['Proxy'], base_proxy[side],
                aimVector=[x_factor * 1, 0, 0], upVector=[0, 0, 1],
                worldUpType='vector',
                worldUpVector=up_vector
            )
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////

        # 代理ジョイントから元骨へ接続する。
        for side in Sides:
            func.connectKeyableAttr(base_proxy[side], base_joint[side])

        # /////////////////////////////////////////////////////////////////////
        # 全てのコントローラにシェイプを追加する。                           //
        # /////////////////////////////////////////////////////////////////////
        size = (target_pos_l[0] - target_pos_r[0]) * 1.2
        creator = func.PrimitiveCreator()
        creator.setSizes([size, size* 0.6, size])
        creator.setColorIndex(23)
        creator.setCurveType('circle')
        creator.setRotation([90, 0, 0])
        creator.create(parentNode=aim_ctrl[''])

        size *= 0.3
        creator.setSizes([size, size, size])
        creator.setColorIndex(6)
        creator.create(parentNode=aim_ctrl_s['L'][''])
        creator.setColorIndex(4)
        creator.create(parentNode=aim_ctrl_s['R'][''])
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////



        # /////////////////////////////////////////////////////////////////////
        # 後処理。                                                           //
        # /////////////////////////////////////////////////////////////////////
        # コントローたの親を、親の代理ノードへ接続する。
        parent_matrix = self.createParentMatrixNode(root_node.parent())
        parent_decmtx = func.createDecomposeMatrix(
            ctrl_parent_proxy, ['%s.matrixSum' % parent_matrix],
            withMultMatrix=False
        )[0]

        # ---------------------------------------------------------------------
        # 親の逆の動きをする代理親へ逆行列を接続する。
        aim_ctrlspace['Proxy'].unlockTransform()
        dmy = node.duplicate(aim_ctrlspace['Proxy'], po=True)[0]

        inv_matrix_nodes = parent_matrix.attr('matrixIn').sources()
        inv_matrix_nodes.reverse()
        inv_matrix_nodes = [x/'inverseMatrix' for x in inv_matrix_nodes]
        inv_matrix_nodes.append(root_trs['Proxy']/'inverseMatrix')
        inv_matrix_nodes.insert(0, dmy/'worldMatrix[0]')

        inv_decmtx, mltmtx = func.createDecomposeMatrix(
            aim_ctrlspace['Proxy'], inv_matrix_nodes
        )

        f = lambda a: (a[0], a[-1]) if a else []
        for plug in f(mltmtx.attr('matrixIn').listArray()):
            plug.disconnect(True)
        # ---------------------------------------------------------------------

        # エイムコントローラのセットアップ。-----------------------------------
        pb_tr, pb_s = func.blendTransform(
                dmy, dmy, aim_ctrlspace['Proxy'], '%s.world' % aim_ctrl['']
        )
        for attr, pb in zip('trs', [pb_tr, pb_tr, pb_s]):
            pb_attr = 't' if attr == 's' else attr
            for ax in func.Axis:
                cmds.disconnectAttr(
                    '%s.%s%s' % (dmy, attr, ax),
                    '%s.i%s%s2' % (pb, pb_attr, ax)
                )
                cmds.connectAttr(
                    '%s.o%s%s' % (inv_decmtx, attr, ax),
                    '%s.i%s%s2' % (pb, pb_attr, ax),
                    f=True
                )
                cmds.disconnectAttr(
                    '%s.%s%s' % (dmy, attr, ax),
                    '%s.i%s%s1' % (pb, pb_attr, ax)
                )
        # ---------------------------------------------------------------------

        for n in (
            root_node, parent_proxy, ctrl_parent_proxy, aim_ctrlspace['Proxy']
        ):
            n.lockTransform()
        
        # Add controller to the anim set.======================================
        # コントローラをanimSetへ登録する。
        anim_set.addChild(
            *[x[''] for x in [aim_ctrl, aim_ctrl_s['L'], aim_ctrl_s['R']]]
        )
        # =====================================================================
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////
