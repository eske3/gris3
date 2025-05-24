# -*- coding:utf-8 -*-
r'''
    @file     humanBaseLimbsRig.py
    @brief    UNITY用の腕を作成するための機能を提供するモジュール。
    @class    BlockNameRule : ベースとなる名前のルールを定義するクラス。
    @class    Option : 作成時に表示するUI用のクラス。
    @class    JointCreator : 腕のジョイント作成機能を提供するクラス。
    @class    RigCreator : 四肢の共通部分を作成する機能を提供するクラス。
    @date        2017/02/01 1:01[Eske](eske3g@gmail.com)
    @update      2017/07/01 1:26[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
from .. import rigScripts, func, node, verutil
from gris3.tools import jointEditor
cmds = func.cmds

IgnoreLoad = False
Category = 'Basic Human'
BaseName = 'arm'

class BlockNameRule(object):
    r'''
        @brief       ベースとなる名前のルールを定義するクラス。
        @inheritance object
        @date        2017/02/07 20:30[Eske](eske3g@gmail.com)
        @update      2017/07/01 1:26[Eske](eske3g@gmail.com)
    '''
    def __init__(self, partName, endPartName, upblock, lowblock, endblock):
        r'''
            @brief  初期化を行う。
            @param  partName : [str]パーツ名
            @param  endPartName : [str]末端のパーツ名
            @param  upblock : [str]上部の名前
            @param  lowblock : [str]下部の名前
            @param  endblock : [str]末端の名前
            @return None
        '''
        self.partname = partName
        self.endpartname = endPartName
        self.upblock = upblock
        self.lowblock = lowblock
        self.endblock = endblock
        self.upblockTitle = upblock[0].upper() + upblock[1:]
        self.lowblockTitle = lowblock[0].upper() + lowblock[1:]
        self.endblockTitle = endblock[0].upper() + endblock[1:]
        self.bend = 'bendCtrl'
        self.numup = 'numberOf' + self.upblockTitle
        self.numlow = 'numberOf' + self.lowblockTitle
        self.attrlist = [self.bend, self.numup, self.numlow]

Default_Block_Name_Rule = BlockNameRule(
    'Arm', 'Hand', 'uparm', 'lowarm', 'hand'
)

class Option(rigScripts.Option):
    r'''
        @brief       作成時に表示するUI用のクラス。
        @inheritance rigScripts.Option
        @date        2017/02/04 18:52[Eske](eske3g@gmail.com)
        @update      2017/07/01 1:26[Eske](eske3g@gmail.com)
    '''
    BlockNameRule = Default_Block_Name_Rule
    def define(self):
        r'''
            @brief  オプション内容を定義する
            @return None
        '''
        self.addBoolOption(self.BlockNameRule.attrlist[0], True)
        for attr in self.BlockNameRule.attrlist[1:]:
            self.addIntOption(attr, default=3, min=1, max=26)

class JointCreator(rigScripts.JointCreator):
    r'''
        @brief       腕のジョイント作成機能を提供するクラス。
        @inheritance rigScripts.JointCreator
        @date        2017/02/01 1:01[Eske](eske3g@gmail.com)
        @update      2017/07/01 1:26[Eske](eske3g@gmail.com)
    '''
    BlockNameRule = Default_Block_Name_Rule
    def createUnit(self):
        r'''
            @brief  ユニット作成のオーバーライド。
            @return None
        '''
        super(JointCreator, self).createUnit()
        unit = self.unit()
        options = self.options()
        attr = self.BlockNameRule.attrlist[0]
        unit.addBoolAttr(attr, options.get(attr, True))
        for attr in self.BlockNameRule.attrlist[1:]:
            value = options.get(attr, 3)
            attr = unit.addIntAttr(attr, default=1, min=1, max=26)
            attr.set(value)

    def finalize(self):
        r'''
            @brief  ジョイントのファイナライズ時にコールされる。
            @return None
        '''
        namerule = self.BlockNameRule
        unit = self.unit()
        name = func.Name(unit())
        name.setSuffix(self.suffix())
        name.setNodeType('jnt')

        bend = unit(namerule.bend)
        if not bend:
            return
        num_up = unit(namerule.numup)
        num_low = unit(namerule.numlow)

        lowblock = unit.getMember(namerule.lowblock)
        endblock = unit.getMember(namerule.endblock)

        upjoints = jointEditor.splitJoint(num_up, lowblock)[0]
        lowjoints = jointEditor.splitJoint(num_low, endblock)[0]
        for joints, key in zip(
                [upjoints, lowjoints],
                [namerule.upblock, namerule.lowblock]
            ):
            for joint, char in zip(joints, verutil.LOWERCASE):
                name.setName('%sTwist%s' % (key, char))
                joint.rename(name())


class RigCreator(rigScripts.RigCreator):
    r'''
        @brief       四肢の共通部分を作成する機能を提供するクラス。
        @inheritance rigScripts.RigCreator
        @date        2017/02/01 1:01[Eske](eske3g@gmail.com)
        @update      2017/07/01 1:26[Eske](eske3g@gmail.com)
    '''
    BlockNameRule = Default_Block_Name_Rule
    AimZFactor = 1
    def __init__(self, unit):
        r'''
            @brief  初期化を行う。
            @param  unit : [grisNode.Unit]
            @return None
        '''
        super(RigCreator, self).__init__(unit)
        self.extrajoints = []
        self.extrajoint_proxies = []
        self.extra_rigJnts = []
        self.isConstrainingDmyIk = True
        self.isBending = True

    def getXFactor(self, positonIndex):
        r'''
            @brief  左右で変化するX軸の値の係数を返す。
            @param  positonIndex : [int]位置を表す数字
            @return int
        '''
        return 1 if positonIndex != 3 else -1

    def createBendSystem(self,
        unitname, basename,
        limbs_ikdmy, up_keep_attr, low_keep_attr, bend_vis_attr
    ):
        r'''
            @brief  ベンドコントローラを上部と下部のジョイントチェーンへ追加
            @brief  する。
            @brief  この処理後、結合ジョイントから代理ジョイントへ接続されている。
            @return None
        '''
        namerule = self.BlockNameRule
        # 元のジョイントから代理ジョイントを作成する。=========================
        upblock_twists = func.listNodeChain(
            self.upblock_jnt, self.lowblock_jnt
        )[1:-1]
        lowblock_twists = func.listNodeChain(
            self.lowblock_jnt, self.endblock_jnt
        )[1:-1]

        upblock_proxy = func.copyNode(
            self.upblock_jnt, None, self.parent_proxy, 'Proxy'
        )
        parent = upblock_proxy
        for twist_joint in upblock_twists:
            self.upblock_twist_proxies.append(
                func.copyNode(twist_joint, None, parent, 'Proxy')
            )
            parent = self.upblock_twist_proxies[-1]

        lowblock_proxy = func.copyNode(
            self.lowblock_jnt, None, parent, 'Proxy'
        )
        parent = lowblock_proxy
        for twist_joint in lowblock_twists:
            self.lowblock_twist_proxies.append(
                func.copyNode(twist_joint, None, parent, 'Proxy')
            )
            parent = self.lowblock_twist_proxies[-1]

        self.endblock_proxy = func.copyNode(
            self.endblock_jnt, None, parent, 'Proxy'
        )

        parent = self.endblock_proxy
        for jnt in self.extrajoints:
            parent = func.copyNode(jnt, None, parent, 'Proxy')
            self.extrajoint_proxies.append(parent)
        # =====================================================================
 
        # ツイストの角度を取るためのangleDriverノードを作成。==================
        unitname.setName(basename + 'upblockAglDrv')
        unitname.setNodeType('trs')
        upblock_agl_drv = func.createAngleDriverNode(
            self.upblock_rigJnt['combJnt'], name=unitname(),
            parent=self.parent_proxy,
        )

        unitname.setName(basename + 'endblockAglDrv')
        endblock_agl_drv = func.createAngleDriverNode(
            self.endblock_rigJnt['combJnt'], name=unitname(),
            parent=self.parent_proxy,
        )
        # =====================================================================

        # ベンドシステムの作成。===============================================
        upblock_bend_ctrls = func.createBendTwistControl(
            self.upblock_rigJnt['combJnt'], self.lowblock_rigJnt['combJnt'],
            upblock_proxy, lowblock_proxy, limbs_ikdmy,
            aimVector=self.vectorX()
        )
        up_keep_attr >> upblock_bend_ctrls['scaleInfo']/'volumeScale'
        # サーフェース方向制御用のaimコンストレイン作成。----------------------
        factor = -1 if self.upblock_rigJnt['combJnt'].isOpposite() else 1
        cmp_mtx = node.createUtil('composeMatrix')
        sr = node.createUtil('setRange')
        for attr, val in zip(
            ('minX', 'maxX', 'oldMinX', 'oldMaxX'),
            (-180, 180, -1, 1)
        ):
            sr(attr, val)
        sr.attr('outValueX') >> cmp_mtx/'inputRotateY'
        upblock_agl_drv.attr('angle2XZ') >> sr/'valueX'

        mltmtx = node.createUtil('multMatrix')
        mltmtx(
            'matrixIn[0]',
            [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1], type='matrix'
        )
        cmp_mtx.attr('outputMatrix') >> mltmtx/'matrixIn[1]'
        mltmtx(
            'matrixIn[2]',
            self.upblock_rigJnt['combJnt']('matrix'), type='matrix'
        )
        self.upblock_rigJnt['combJnt'].attr('im') >> mltmtx/'matrixIn[3]'

        aim = node.createNode('aimConstraint', p=upblock_bend_ctrls['topCtrl'])
        aim('aimVector', (1, 0, 0))
        aim('upVector', (0, 0, 1))
        aim('worldUpType', 1)
        aim('target[0].targetTranslate', (1, 0, 0))
        mltmtx.attr('matrixSum') >> aim/'worldUpMatrix'
        upblock_bend_ctrls['topCtrl'].attr('t') >> aim/'ct'
        ~aim.attr('cr') >> ~upblock_bend_ctrls['topCtrl'].attr('r')
        # ---------------------------------------------------------------------

        lowblock_bend_ctrls = func.createBendTwistControl(
            self.lowblock_rigJnt['combJnt'], self.endblock_rigJnt['combJnt'],
            lowblock_proxy, self.endblock_proxy,
            self.lowblock_rigJnt['combJnt'],
            False, self.vectorX()
        )
        low_keep_attr >> lowblock_bend_ctrls['scaleInfo']/'volumeScale'
        # =====================================================================

        # ベンドシステムを制御するためのコントローラを作成する。===============
        # ベンドコントローラ用の代理親ノードを作成する。
        unitname.setName(basename + namerule.upblockTitle + 'BendCtrl')
        unitname.setNodeType('parentProxy')
        upblock_bend_parentproxy = func.createSpaceNode(
            n=unitname(), p=self.ctrl_parent_proxy
        )
        func.connectKeyableAttr(
            self.upblock_rigJnt['combJnt'], upblock_bend_parentproxy
        )
        (
            ~self.upblock_rigJnt['combJnt'].attr('jo')
            >> ~upblock_bend_parentproxy.attr('jo')
        )

        unitname.setName(basename + namerule.lowblockTitle + 'BendCtrl')
        lowblock_bend_parentproxy = func.createSpaceNode(
            n=unitname(), p=upblock_bend_parentproxy
        )
        func.connectKeyableAttr(
            self.lowblock_rigJnt['combJnt'], lowblock_bend_parentproxy
        )
        (
            self.lowblock_rigJnt['combJnt'].attr('jo')
            >> lowblock_bend_parentproxy.attr('jo')
        )
        func.lockTransform(
            [upblock_bend_parentproxy, lowblock_bend_parentproxy]
        )
        # =====================================================================

        # ベンド用コントローラを作成する。=====================================
        bend_ctrls = []
        bend_ctrlspace = []

        # 上部ベンドコントローラの作成。---------------------------------------
        unitname.setName(basename + 'UplimbsBendCtrl')
        unitname.setNodeType('ctrl')
        ctrl = unitname()

        unitname.setNodeType('ctrlSpace')
        space = unitname()
    
        ctrl, space = func.createFkController(
            upblock_bend_ctrls['midCtrl'], upblock_bend_parentproxy,
            ctrl, space,
            skipTranslate=True, skipRotate=True, skipScale=True,
        )
        bend_ctrls.append(ctrl)
        bend_ctrlspace.append(space)

        mltmtx = node.createUtil('multMatrix')
        ctrl.attr('matrix') >> mltmtx/'matrixIn[0]'
        space.attr('matrix') >> mltmtx/'matrixIn[1]'
        mltmtx('matrixIn[2]', space('inverseMatrix'), type='matrix')
        for plug in (
            upblock_bend_ctrls['midCtrl'].attr('matrix').destinations(p=True)
        ):
            mltmtx/'matrixSum' >> plug
        upblock_bend_ctrls['midCtrl'].delete()
        # ---------------------------------------------------------------------

        # 肘（膝）と下部のベンドコントローラの作成。
        for block_name, targets in zip(
                ['Midlimbs', 'Lowlimbs'],
                [
                    [
                        upblock_bend_ctrls['btmCtrl'],
                        lowblock_bend_ctrls['topCtrl']
                    ],
                    [
                        lowblock_bend_ctrls['midCtrl']
                    ]
                ]
            ):
            unitname.setName(basename + '%sBendCtrl' % block_name)
            unitname.setNodeType('ctrl')
            ctrl = unitname()

            unitname.setNodeType('ctrlSpace')
            space = unitname()
            
            ctrl, space = func.createFkController(
                targets[0], lowblock_bend_parentproxy,
                ctrl, space,
                skipTranslate=True, skipRotate=True, skipScale=True,
            )
            bend_ctrls.append(ctrl)
            bend_ctrlspace.append(space)

            mltmtx = node.createUtil('multMatrix')
            ctrl.attr('matrix') >> mltmtx/'matrixIn[0]'
            space.attr('matrix') >> mltmtx/'matrixIn[1]'
            mltmtx('matrixIn[2]', space('inverseMatrix'), type='matrix')
            for target in targets:
                for plug in target.attr('matrix').destinations(p=True):
                    mltmtx/'matrixSum' >> plug
                target.delete()
                # decmtx, mltmtx = func.createDecomposeMatrix(
                    # target, [x + '.matrix' for x in (ctrl, space)]
                # )
                # mltmtx('matrixIn[2]', space('inverseMatrix'), type='matrix')
        # =====================================================================

        # ベンドコントローラのツイスト用の接続を行う。=========================
        for val, driver, ctrl in zip(
            (-0.5, 0.5),
            (upblock_agl_drv, endblock_agl_drv),
            (bend_ctrlspace[0], bend_ctrlspace[-1])
        ):
            mdl = node.createUtil('multDoubleLinear')
            mdl('input2', val)
            driver.attr('twistX') >> mdl.attr('input1')

            func.fConnectAttr(mdl + '.output', ctrl + '.rx')
            func.lockTransform(bend_ctrls)
            func.controlChannels(
                bend_ctrls, ['t:a', 'r:a'], isKeyable=True, isLocked=False
            )
        # =====================================================================
        
        bend_vis_attr >> upblock_bend_parentproxy/'v'

        # 代理ジョイントから元ジョイントへの接続を行う。=======================
        proxy_joints  = [
            upblock_proxy, lowblock_proxy, self.endblock_proxy
        ] + self.extrajoint_proxies
        origin_joints = [
            self.upblock_jnt, self.lowblock_jnt, self.endblock_jnt
        ] + self.extrajoints
        for proxy, orig in zip(proxy_joints, origin_joints):
            func.connectKeyableAttr(proxy, orig)

        for proxy_list, orig_list in zip(
            (self.upblock_twist_proxies, self.lowblock_twist_proxies),
            (upblock_twists, lowblock_twists)
        ):
            for proxy, orig in zip(
                proxy_list, orig_list, 
            ):
                func.connect3ChannelAttr(proxy + '.t', orig + '.t')
                func.connect3ChannelAttr(proxy + '.r', orig + '.r')
                func.fConnectAttr(proxy + '.sx', orig + '.sx')
                func.transferConnection(proxy + '.sy', orig + '.sy')
                func.transferConnection(proxy + '.sz', orig + '.sz')

        all_joints = [upblock_proxy]
        all_joints.extend(upblock_twists)
        all_joints.append(lowblock_proxy)
        all_joints.extend(lowblock_twists)
        all_joints.append(self.endblock_proxy)
        length_ratios = func.listLengthRatio(all_joints)
        for j, r in zip(all_joints[:-1], length_ratios):
            r = func.math.sin(func.math.pi * r)
            md = cmds.listConnections(
                j + '.sy', s=True, d=False, type='multiplyDivide'
            )[0]
            src_plug = cmds.listConnections(
                md + '.input2Y', s=True, d=False, p=True
            )[0]
            blender = node.createUtil('blendTwoAttr')
            blender('input[0]', 1)
            src_plug >> blender.attr('input[1]')
            blender('attributesBlender', r)
            blender.attr('output') >> (md+'.i2y', md+'.i2z')
        # =====================================================================

        self.isBending = True
        return (
            bend_ctrls, bend_ctrlspace, upblock_bend_ctrls, lowblock_bend_ctrls
        )

    def connectCombToOrig(self):
        for attr in ('upblock', 'lowblock', 'endblock'):
            func.connectKeyableAttr(
                getattr(self, attr+'_rigJnt')['combJnt'],
                getattr(self, attr+'_jnt')
            )
        self.isBending = False
        return [], []

    def createBasicRig(self):
        r'''
            @brief  共有部分のリグ作成メソッド。
            @return None
        '''
        unit = self.unit()
        unitname = self.unitName()
        basename = unitname.name()
        side = unit.positionIndex()
        anim_set = self.animSet()
        namerule = self.BlockNameRule

        x_factor = self.getXFactor(side)
        is_bending = unit(namerule.bend)

        self.upblock_jnt = unit.getMember(namerule.upblock)
        self.lowblock_jnt = unit.getMember(namerule.lowblock)
        self.endblock_jnt = unit.getMember(namerule.endblock)

        # 四肢のパーツのベクトルを取得。=======================================
        upblock_vector = func.Vector(self.upblock_jnt.position())
        lowblock_vector = func.Vector(self.lowblock_jnt.position())
        self.endblock_vector = func.Vector(self.endblock_jnt.position())
        self.limbs_vector = self.endblock_vector - upblock_vector
        upblock_to_lowblock = lowblock_vector - upblock_vector
        lowblock_to_endblock = self.endblock_vector - lowblock_vector

        h = (
            upblock_to_lowblock * self.limbs_vector
            / self.limbs_vector.length()
        )

        pv_dir_vector = (
            upblock_to_lowblock - (self.limbs_vector.norm() * h)
        ).norm()
        if (
            (upblock_to_lowblock.norm() * lowblock_to_endblock.norm()) - 1.0
            < 0.00000001
        ):
            orig_angle = self.lowblock_jnt('r')[0]
            pref_angle = self.lowblock_jnt('pa')[0]
            self.lowblock_jnt('r', pref_angle)

            t_endblock_vector = func.Vector(self.endblock_jnt.position())
            self.limbs_vector = t_endblock_vector - upblock_vector

            t_h = (
                upblock_to_lowblock * self.limbs_vector
                / self.limbs_vector.length()
            )
            pv_dir_vector = (
                upblock_to_lowblock - (self.limbs_vector.norm() * t_h)
            ).norm()

            limbs_v_vector = (
                (t_endblock_vector - lowblock_vector) ** upblock_to_lowblock
            ).norm()

            self.lowblock_jnt('r', orig_angle)
        else:
            limbs_v_vector = (
                lowblock_to_endblock ** upblock_to_lowblock
            ).norm()
        # =====================================================================

        # ルートノードの作成。=================================================
        # リグ用の代理親ノードの作成。
        self.parent_proxy = self.createRigParentProxy(
            self.upblock_jnt, name=basename
        )

        # ikコントローラ用の代理親ノードの作成。
        self.ikctrl_parent_proxy = self.createCtrlParentProxy(
            self.upblock_jnt, basename+'Ik'
        )
        self.ctrl_parent_proxy = self.createCtrlParentProxy(
            self.upblock_jnt, basename
        )

        # ブレンドを行うための親ノードを作成。
        unitname.setName(basename + 'Ik')
        unitname.setNodeType('parentBlender')
        parent_blender = self.createParentProxy(
            self.upblock_jnt, name=unitname()
        )
        # =====================================================================

        # リグ用のジョイントをオリジナルからコピーする。=======================
        # IK用、FK用、そして合成用のジョイントをオリジナルからコピー。---------
        self.upblock_rigJnt, self.lowblock_rigJnt, self.endblock_rigJnt = (
            {}, {}, {}
        )
        self.extra_rigJnts = [{} for x in range(len(self.extrajoints))]
        for key in ('ikJnt', 'fkJnt', 'combJnt'):
            self.upblock_rigJnt[key] = func.copyNode(
                self.upblock_jnt, key, self.parent_proxy
            )
            self.lowblock_rigJnt[key] = func.copyNode(
                self.lowblock_jnt, key, self.upblock_rigJnt[key]
            )
            self.endblock_rigJnt[key] = func.copyNode(
                self.endblock_jnt, key, self.lowblock_rigJnt[key]
            )
            parent = self.endblock_rigJnt[key]
            for i, extra in enumerate(self.extrajoints):
                parent = func.copyNode(extra, key, parent)
                self.extra_rigJnts[i][key] = parent
        # ---------------------------------------------------------------------
        # =====================================================================

        # IKロール用のダミージョイントを作成する。=============================
        limbs_ikdmy = func.copyNode(
            self.upblock_jnt, 'ikDmy', self.parent_proxy
        )
        limbsend_ikdmy = func.copyNode(self.endblock_jnt, 'ikDmy', limbs_ikdmy)

        orientation_mod = jointEditor.OrientationModifier()
        orientation_mod.setPrimaryAxis(self.axisX())
        orientation_mod.execute([limbs_ikdmy, limbsend_ikdmy])
        # =====================================================================
        
        self.upblock_twist_proxies = []
        self.lowblock_twist_proxies = []

        # コントローラとその代理ノードを作成する。=============================
        self.limbs_ik_ctrlspace = {}
        self.limbs_ik_ctrl = {}

        for key, root_parent in zip(
                ['', 'Proxy'], [self.ikctrl_parent_proxy, parent_blender]
            ):
            # 四肢のIKのスペーサーとコントローラ。-----------------------------
            unitname.setName(basename+'Ik')
            unitname.setNodeType('ctrlSpace' + key)
            self.limbs_ik_ctrlspace[key] = node.createNode(
                'transform', n=unitname(), p=root_parent
            )
            f = 1 if side != 3 else -1
            self.limbs_ik_ctrlspace[key].fitTo(self.endblock_jnt, 8)
            aim = node.createNode('aimConstraint')
            aim('aimVector', (0, -f, 0))
            aim('upVector', (0, 0, f * self.AimZFactor))
            aim('worldUpType', 3)
            aim('worldUpVector', self.endblock_jnt.matrix()[8:11])
            aim(
                'target[0].targetParentMatrix',
                self.endblock_jnt('worldMatrix'), type='matrix'
            )
            aim('target[0].targetTranslate', (1, 0, 0))
            aim('cpim', self.limbs_ik_ctrlspace[key]('pim'), type='matrix')
            aim('constraintTranslate', self.limbs_ik_ctrlspace[key]('t')[0])
            self.limbs_ik_ctrlspace[key]('rotate', aim('constraintRotate')[0])
            aim.delete()
            unitname.setNodeType('ctrl' + key)
            self.limbs_ik_ctrl[key] = node.createNode(
                'transform', n=unitname(), p=self.limbs_ik_ctrlspace[key]
            )
            func.lockTransform(
                (self.limbs_ik_ctrlspace[key], self.limbs_ik_ctrl[key])
            )
            self.limbs_ik_ctrl[key].editAttr(('t:a', 'r:a'), k=True, l=False)
            # -----------------------------------------------------------------
        stretch_attr = self.limbs_ik_ctrl[''].addFloatAttr(
            'stretch', default=0
        )
        softik_attr = self.limbs_ik_ctrl[''].addFloatAttr(
            'softIk', min=0, max=100, default=0, smx=1
        )
        self.limbs_ik_ctrl[''].addFloatAttr('world')
        self.limbs_ik_ctrl[''].editAttr('ro', k=True)
        # =====================================================================
        
        # 四肢のIKシステムのセットアップ。=====================================
        # コントローラから代理ノードへの接続を行う。---------------------------
        (
            ~self.limbs_ik_ctrl[''].attr('t')
            >> ~self.limbs_ik_ctrl['Proxy'].attr('t')
        )
        # =====================================================================

        # IKコントローラとそのシステムの作成。=================================
        # IKの仕組みの作成。---------------------------------------------------
        # 四肢のIKの作成。
        unitname.setNodeType('ik')
        unitname.setName(basename + namerule.partname)
        limbs_ik = cmds.ikHandle(n=unitname(),
            sj=self.upblock_rigJnt['ikJnt'], ee=self.endblock_rigJnt['ikJnt'],
            sol='ikRPsolver'
        )[0]

        unitname.setName(basename + namerule.partname + 'Dmy')
        self.limbs_dmyik = cmds.ikHandle(n=unitname(),
            sj=limbs_ikdmy, ee=limbsend_ikdmy, sol='ikSCsolver'
        )[0]

        self.limbs_dmyik = node.asObject(
            cmds.parent(self.limbs_dmyik, self.parent_proxy
        )[0])

        unitname.setName(basename+'IkPos')
        unitname.setNodeType('pos')
        self.limbs_ik_pos = node.createNode(
            'transform', n=unitname(), p=self.limbs_ik_ctrl['Proxy']
        )
        limbs_ik = node.asObject(cmds.parent(limbs_ik, self.limbs_ik_pos)[0])

        # 四肢のIKをダミーIKへコンストレインする。
        if self.isConstrainingDmyIk:
            matrixlist = [self.limbs_ik_ctrlspace['Proxy'], parent_blender]
            matrixlist = ['%s.matrix' % x for x in matrixlist]
            matrixlist.append('%s.inverseMatrix' % self.parent_proxy)
            func.createTranslateConnection(
                '%s.t' % self.limbs_ik_ctrl['Proxy'], matrixlist,
                '%s.t' % self.limbs_dmyik
            )
        # ---------------------------------------------------------------------

        # ストレッチシステムの作成。-------------------------------------------
        result_node = func.createScaleStretchSystem(
            self.upblock_rigJnt['ikJnt'], self.endblock_rigJnt['ikJnt']
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
                cmds.rename(result_node['start'], start_loc), self.parent_proxy
            )[0]
        )
        end_loc = node.asObject(
            cmds.parent(
                cmds.rename(result_node['end'], end_loc),
                self.limbs_ik_ctrl['Proxy']
            )[0]
        )
        dist_node = node.asObject(
            cmds.parent(
                cmds.rename(result_node['result'], dist_node), limbs_ikdmy
            )[0]
        )
        stretch_attr >> dist_node.attr('stretch')
        # ---------------------------------------------------------------------
        
        # ソフトIKの作成。-----------------------------------------------------
        cmds.aimConstraint(
            start_loc, self.limbs_ik_pos,
            aimVector=[1, 0, 0], upVector=[0, 1, 0], worldUpType='none'
        )
        self.addLockedList(self.limbs_ik_pos)
        func.createSoftIkFromStretchNode(
            softik_attr.name(), dist_node, limbs_ik
        )
        # ---------------------------------------------------------------------

        # IKの自動ポールベクターシステムの作成。===============================
        # システムの作成。
        unitname.setName(basename + 'IkPv')
        unitname.setNodeType('trs')
        ik_roll_ctrlproxy = node.asObject(
            cmds.pointConstraint(start_loc, end_loc, dist_node)[0]
        )
        dist_node('r', (0, 0, 0))

        # 膝(肘)の位置からポールベクターのとロール用コントローラの位置を決定。-
        cst_vector = func.Vector(ik_roll_ctrlproxy.position())
        pv_pos = cst_vector + (
            pv_dir_vector * (self.limbs_vector.length() * 0.5)
        )
        pv_locator = node.createNode(
            'transform', n=unitname(), p=ik_roll_ctrlproxy
        )
        pv_locator.setPosition(pv_pos)
        pv_locator.lockTransform()
        cmds.poleVectorConstraint(pv_locator, limbs_ik)
        # ---------------------------------------------------------------------

        # ロール用コントローラを作成する。-------------------------------------
        unitname.setName(basename + 'IkRole')
        unitname.setNodeType('ctrlSpace')
        ikrole_ctrlspace = node.createNode(
            'transform', n=unitname(), p=self.ikctrl_parent_proxy
        )
        ikrole_ctrlspace.editAttr(('s:a', 'sh:a'), k=False, l=True)

        unitname.setNodeType('ctrl')
        ikrole_ctrl = node.createNode(
            'transform', n=unitname(), p=ikrole_ctrlspace
        )
        ikrole_ctrl.lockTransform()
        ikrole_ctrl.editAttr(['rx'], k=True, l=False)
        # ---------------------------------------------------------------------

        # システムとコントローラ間の接続を行う。-------------------------------
        inputMatrices = [
            x + '.matrix' for x in [dist_node, limbs_ikdmy, self.parent_proxy]
        ]
        inputMatrices.append(self.ikctrl_parent_proxy + '.inverseMatrix')
        decmtx, mltmtx = func.createDecomposeMatrix(
            ikrole_ctrlspace, inputMatrices
        )
        ikrole_ctrlspace.lockTransform()

        func.connectKeyableAttr(ikrole_ctrl, ik_roll_ctrlproxy)
        # ---------------------------------------------------------------------
        # =====================================================================

        # IKのスケール用コントローラを作成する。===============================
        parent = self.ctrl_parent_proxy
        ik_scale_spaces = []
        self.ik_scale_ctrls = []
        jointlist = [
            self.upblock_rigJnt, self.lowblock_rigJnt, self.endblock_rigJnt
        ] + self.extra_rigJnts[:-1]

        scale_ctrls = []
        for part in jointlist:
            name = func.Name(part['ikJnt'])
            name.setName(name.name() + 'Scale')
            name.setNodeType('ctrlSpace')
            space = func.createSpaceNode(p=parent, n=name())
            if self.ik_scale_ctrls and ik_scale_spaces:
                md = node.createUtil('multiplyDivide')
                ik_scale_spaces[-1].attr('s') >> md.attr('i1')
                self.ik_scale_ctrls[-1].attr('s') >> md.attr('i2')
                md.attr('o') >> space.attr('inverseScale')

            for attr in 'tr':
                ~part['ikJnt'].attr(attr) >> ~space.attr(attr)
            for ax in func.Axis:
                jo = part['ikJnt']('jo'+ax)
                space('jo'+ax, jo)

            name.setNodeType('ctrl')
            ctrl = node.createNode('transform', n=name(), p=space)
            ik_scale_spaces.append(space)
            self.ik_scale_ctrls.append(ctrl)
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

        sum_node = node.createUtil('plusMinusAverage')
        sum_plug = sum_node.attr('input1D').elementAt
        i = 0
        for ctrl, vec in zip(
            scale_ctrls, (upblock_to_lowblock, lowblock_to_endblock)
        ):
            adl = node.createUtil('multDoubleLinear')
            ctrl.attr('sx') >> adl.attr('i1')
            adl('i2', vec.length())
            adl.attr('output') >> sum_plug(i)
            i += 1
        sum_node.attr('output1D') >> result_node['dist'].attr('defaultLength')
        # =====================================================================
        
        # IKのルートコントローラを作成する。===================================
        unitname.setName(basename + 'IkRoot')
        unitname.setNodeType('ctrl')
        limbsIkRoot_ctrl = unitname()
        
        unitname.setNodeType('ctrlSpace')
        limbsIkRoot_space = unitname()
        limbsIkRoot_ctrl, limbsIkRoot_space = func.createFkController(
            target=self.upblock_rigJnt['ikJnt'], parent=self.ctrl_parent_proxy,
            name=limbsIkRoot_ctrl, spaceName=limbsIkRoot_space,
            skipTranslate=False, skipRotate=True, skipScale=True,
            isLockTransform=True
        )
        limbsIkRoot_ctrl.lockTransform()
        limbsIkRoot_ctrl.editAttr(['t:a'], k=True, l=False)
        pmm = limbsIkRoot_ctrl.attr('tx').destinations()[0]
        for n in [limbs_ikdmy, start_loc]:
            ~pmm.attr('o') >> ~n.attr('t')
        # =====================================================================

        # FKコントローラを作成する。===========================================
        fk_ctrls = []
        unitname.setName(basename + namerule.upblockTitle + 'FK')
        unitname.setNodeType('ctrl')
        upblock_fkCtrl = unitname()

        # 上部のFKコントローラの作成。-----------------------------------------
        unitname.setNodeType('ctrlSpace')
        upblock_fkroot = unitname()
        upblock_fkCtrl, upblock_fkroot = func.createFkController(
            self.upblock_rigJnt['fkJnt'], self.ctrl_parent_proxy,
            upblock_fkCtrl, upblock_fkroot, skipTranslate=False,
            isLockTransform=False, calculateWithSpace=True
        )
        world_attr = upblock_fkCtrl.addFloatAttr('world', default=0)

        ctrl_space = upblock_fkCtrl.parent()
        mltmtx = node.createUtil('multMatrix')
        mltmtx('matrixIn[0]', ctrl_space('worldMatrix'), type='matrix')
        self.ctrl_parent_proxy.attr('inverseMatrix') >> mltmtx/'matrixIn[1]'

        decmtx = node.createUtil('decomposeMatrix')
        mltmtx.attr('matrixSum') >> decmtx/'inputMatrix'

        ~decmtx.attr('or') >> ~ctrl_space.attr('r')
        func.blendSelfConnection(
            ctrl_space, blendControlAttr=upblock_fkCtrl + '.world',
            skipTranslate=True, skipScale=True, blendMode=1
        )
        ctrl_space.lockTransform()
        fk_ctrls.append(upblock_fkCtrl)
        # ---------------------------------------------------------------------

        # 下部のFKコントローラの作成。-----------------------------------------
        unitname.setName(basename + namerule.lowblockTitle + 'Fk')
        unitname.setNodeType('ctrlSpace')
        fk_ctrlspace = unitname()
        
        unitname.setNodeType('ctrl')
        lowblock_fkCtrl = func.createFkController(
            self.lowblock_rigJnt['fkJnt'], upblock_fkCtrl, unitname(),
            fk_ctrlspace, skipTranslate=False
        )[0]
        fk_ctrls.append(lowblock_fkCtrl)
        # ---------------------------------------------------------------------

        # 末端部のFKコントローラの作成。---------------------------------------
        unitname.setName(basename + namerule.endblock.title() + 'Fk')
        unitname.setNodeType('ctrlSpace')
        fk_ctrlspace = unitname()
        
        unitname.setNodeType('ctrl')
        endblock_fkCtrl = func.createFkController(
            self.endblock_rigJnt['fkJnt'], lowblock_fkCtrl, unitname(),
            fk_ctrlspace, skipTranslate=False
        )[0]
        fk_ctrls.append(endblock_fkCtrl)
        # ---------------------------------------------------------------------
        
        # IK/FKスイッチのターゲットを追加する。--------------------------------
        unitname.setName(basename + 'IkFkSwitchTgt')
        target = node.createNode(
            'transform', n=unitname(), p=self.endblock_rigJnt['fkJnt']
        )
        target.setMatrix(self.limbs_ik_ctrl[''].matrix())
        target.lockTransform()
        switch_tgt_attr = self.limbs_ik_ctrl[''].addMessageAttr(
            'ikFkSwitchTarget'
        )
        target/'message' >> switch_tgt_attr
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        parent = endblock_fkCtrl
        for jnt in self.extra_rigJnts[:-1]:
            name = func.Name(jnt['fkJnt'])
            unitname.setName(basename + name.name().title() + 'Fk')
            unitname.setNodeType('ctrlSpace')
            fk_ctrlspace = unitname()

            unitname.setNodeType('ctrl')
            fkctrl = func.createFkController(
                jnt['fkJnt'], parent, unitname(), fk_ctrlspace,
                skipTranslate=False
            )[0]
            parent = fkctrl
            fk_ctrls.append(fkctrl)
        # ---------------------------------------------------------------------
        # =====================================================================

        # ikジョイントとfkジョイントの結合を行う。=============================
        # パラメータ制御用コントローラの作成。
        unitname.setName(basename + 'Param')
        unitname.setNodeType('ctrl')
        param_ctrl = node.createNode(
            'transform', n=unitname(), p=ikrole_ctrlspace
        )
        param_ctrl.editAttr(('t:a', 'r:a', 's:a', 'v'), k=False, l=False)
        ikblend_attr = param_ctrl.addFloatAttr('ikBlend', default=1)
        ikscl_vis_attr = param_ctrl.addDisplayAttr(
            'ikScalingController', default=0, cb=True
        )
        if is_bending:
            bend_vis_attr = param_ctrl.addDisplayAttr(
                'bendCtrlVisibility', default=0, cb=True
            )
        up_keep_attr = param_ctrl.addFloatAttr(
            'upKeepVolume', default=0, min=-2, max=2, smn=-1, smx=1
        )
        low_keep_attr = param_ctrl.addFloatAttr(
            'lowKeepVolume', default=0, min=-2, max=2, smn=-1, smx=1
        )

        param_ctrl_vector = (
            limbs_v_vector * (self.limbs_vector.length() * 0.35 * x_factor)
            + cst_vector
        )
        param_ctrl.setPosition(param_ctrl_vector)
        # IKブレンド用のアトリビュートをik/fkコントローラの表示アトリビュートへ
        # 接続する。
        ikblend_attr >>  [
            x/'v' for x in (
                self.limbs_ik_ctrlspace[''], ikrole_ctrl, limbsIkRoot_space
            )
        ]
        # =====================================================================

        # 結合ジョイントを代理ジョイントへ接続する。===========================
        if is_bending:
            bend_ctrls, bend_ctrlspace, up_bendsys, low_bendsys = (
                self.createBendSystem(
                    unitname, basename,
                    limbs_ikdmy, up_keep_attr, low_keep_attr, bend_vis_attr
                )
            )
        else:
            bend_ctrls, bend_ctrlspace = self.connectCombToOrig()

        # 代理親ノードとブレンド用ノードのセットアップ。=======================
        parent_matrix = self.createParentMatrixNode(
            cmds.listRelatives(self.upblock_jnt, p=True, pa=True)[0]
        )
        decmtx = func.createDecomposeMatrix(
            self.parent_proxy, ['%s.matrixSum' % parent_matrix],
            withMultMatrix=False
        )[0]
        func.makeDecomposeMatrixConnection(
            decmtx, [self.ctrl_parent_proxy]
        )

        func.blendTransform(
            self.parent_proxy, None, [parent_blender, self.ikctrl_parent_proxy],
            '%s.world' % self.limbs_ik_ctrl[''],
            skipScale=True, blendMode=1
        )

        func.lockTransform(
            [
                self.parent_proxy, parent_blender,
                self.ctrl_parent_proxy, self.ikctrl_parent_proxy
            ]
        )
        # =====================================================================

        # 全てのコントローラにシェイプを追加する。=============================
        # ベンドコントローラへのシェイプ追加。---------------------------------
        size = self.limbs_vector.length() * 0.5
        self.creator = func.PrimitiveCreator()
        self.creator.setSize(size)
        self.creator.setColorIndex(self.colorIndex('special'))
        self.creator.setCurveType('crossArrow')
        self.creator.setRotation([0, 0, 90])
        for ctrl in bend_ctrls:
            self.creator.create(parentNode=ctrl)
        # ---------------------------------------------------------------------

        # IK用コントローラへのシェイプ追加。-----------------------------------
        # IK回転コントローラへのシェイプ追加。
        size *= 0.6
        self.creator.setSize(size)
        self.creator.setRotation([0, 0, -90])
        self.creator.setCurveType('circleArrow')
        self.creator.setColorIndex(self.colorIndex('extra'))
        shape = self.creator.create(parentNode=ikrole_ctrl)
        if side == 3:
            shape.setRotate(180, 0, 0)
        self.creator.setRotation()
        
        # IKのルート移動用コントローラへのシェイプ追加。
        size = self.limbs_vector.length() * 0.1
        self.creator.setSize(size)
        self.creator.create('box', limbsIkRoot_ctrl)

        # 四肢のIKコントローラへのシェイプ追加。
        size = self.limbs_vector.length() * 0.3
        self.creator.setSizes([size, size* 0.4, size])
        self.creator.setColorIndex(self.colorIndex('main'))
        shape = self.creator.create('box', self.limbs_ik_ctrl[''])

        # パラメータ制御用コントローラへのシェイプ追加。
        size = self.limbs_vector.length() * 0.1
        self.creator.setSize(size)
        self.creator.setRotation([90, 0, 0])
        shape = self.creator.create('cross', param_ctrl)
        self.creator.setRotation()

        # IKスケール用のコントローラへのシェイプ追加。
        size = self.limbs_vector.length() * 0.25
        self.creator.setSize(size)
        self.creator.setColorIndex(16)
        self.creator.setRotation([0, 0, 90])
        for ctrl in self.ik_scale_ctrls:
            self.creator.create('scalePlane', ctrl)
        # ---------------------------------------------------------------------
        
        # FK用コントローラへのシェイプ追加。-----------------------------------
        self.creator.setCurveType('sphere')
        self.creator.setColorIndex(self.colorIndex('key'))

        for fk_ctrl in fk_ctrls:
            shape = self.creator.create(parentNode=fk_ctrl)
        # ---------------------------------------------------------------------
        # =====================================================================

        # 後処理。=============================================================
        # ikジョイントとfkjointを結合jointへのブレンド処理を行う。-------------
        for joint in jointlist:
            func.blendTransform(
                joint['fkJnt'], joint['ikJnt'], joint['combJnt'],
                ikblend_attr, blendMode=1
            )
        ikscl_vis_attr >> ik_scale_spaces[0]+'.v' 

        self.vis_rev_node = node.createUtil('reverse')
        ikblend_attr >> self.vis_rev_node/'inputX'
        self.vis_rev_node.attr('outputX') >> upblock_fkroot/'v'
        # ---------------------------------------------------------------------

        # コントローラをanimセットへ追加する。---------------------------------
        anim_set.addChild(
            *[
                limbsIkRoot_ctrl, self.limbs_ik_ctrl[''], ikrole_ctrl,
                param_ctrl
            ]
        )
        anim_set.addChild(*bend_ctrls)
        anim_set.addChild(*self.ik_scale_ctrls)
        
        anim_set.addChild(*fk_ctrls)
        # ---------------------------------------------------------------------
        # =====================================================================

    def customPreRigging(self):
        r'''
            @brief  ベーシックリグ作成前に呼ばれる上書き用メソッド。
            @return None
        '''
        pass

    def customRigging(self):
        r'''
            @brief  カスタムのリグを作成するための上書き用。
            @brief  このクラスのサブクラスは基本的にこのメソッドを上書きする。
            @return None
        '''
        pass

    def process(self):
        r'''
            @brief  実処理部分。基本的にこの部分はサブクラスでは上書きしない。
            @return None
        '''
        self.customPreRigging()
        self.createBasicRig()
        self.customRigging()
