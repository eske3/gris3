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
import string

from .. import rigScripts, func, node, verutil
from ..tools import jointEditor
cmds = func.cmds

Category = 'Utilties'
BaseName = 'bentChain'

class Option(rigScripts.Option):
    r'''
        @brief       作成時に表示するUI用のクラス。
        @inheritance rigScripts.Option
        @date        2017/02/04 18:52[Eske](eske3g@gmail.com)
        @update      2017/07/01 1:26[Eske](eske3g@gmail.com)
    '''
    def define(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        self.addStringOption('name', default='bentBase')
        self.addIntOption('division', default=3, min=1, max=26)

class JointCreator(rigScripts.JointCreator):
    r'''
        @brief       腕のジョイント作成機能を提供するクラス。
        @inheritance rigScripts.JointCreator
        @date        2017/02/01 1:01[Eske](eske3g@gmail.com)
        @update      2017/07/01 1:26[Eske](eske3g@gmail.com)
    '''
    def createUnit(self):
        r'''
            @brief  ユニット作成のオーバーライド。
            @return None
        '''
        super(JointCreator, self).createUnit()
        unit = self.unit()
        options = self.options()
        
        value = options.get('name', 'bentBase')
        attr = unit.addStringAttr('name')
        attr.set(value)

        value = options.get('division', 3)
        attr = unit.addIntAttr('division', default=3, min=1, max=26)
        attr.set(value)

    def process(self):
        r'''
            @brief  ジョイント作成プロセスとしてコールされる。
            @return None
        '''
        unit = self.unit()
        name = self.basenameObject()
        parent = self.parent()

        x_factor = -1 if self.position() == 'R' else 1

        # ルートを作成.
        name.setName(unit('name'))
        base = node.createNode('joint', n=name(), p=parent)
        base.setRadius(1.4)
        base('ssc', 0)

        # Lowarm.
        name.setName(unit('name')+'End')
        end = node.createNode('joint', n=name(), p=base)
        end('t', (x_factor * 10, 0, 0))

        # Unit setting.--------------------------------------------------------
        unit = self.unit()
        unit.addMember('base', base)
        unit.addMember('end', end)
        # ---------------------------------------------------------------------

        self.asRoot(base)
        end.select()

    def finalize(self):
        r'''
            @brief  ジョイントのファイナライズ時にコールされる。
            @return None
        '''
        unit = self.unit()
        name = func.Name(unit())
        name.setSuffix(self.suffix())
        name.setNodeType('jnt')
        
        base_name = unit('name')

        div = unit('division')
        baseblock = unit.getMember('base')
        endblock = unit.getMember('end')

        twisted = jointEditor.splitJoint(div, endblock)[0]
        for joint, char in zip(twisted, verutil.LOWERCASE):
            name.setName('%sTwist%s' % (base_name, char))
            joint.rename(name())


class RigCreator(rigScripts.RigCreator):
    r'''
        @brief       四肢の共通部分を作成する機能を提供するクラス。
        @inheritance rigScripts.RigCreator
        @date        2017/02/01 1:01[Eske](eske3g@gmail.com)
        @update      2017/07/01 1:26[Eske](eske3g@gmail.com)
    '''
    def process(self):
        r'''
            @brief  実処理部分。基本的にこの部分はサブクラスでは上書きしない。
            @return None
        '''
        unit = self.unit()
        unitname = self.unitName()
        basename = unitname.name()
        side = unit.positionIndex()
        anim_set = self.animSet()

        base = unit.getMember('base')
        end = unit.getMember('end')
        
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