#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    GRIS用ノードを定義するクラスを提供するモジュール。
    
    Dates:
        date:2017/01/22 0:05[Eske](eske3g@gmail.com)
        update:2021/04/23 13:46 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from . import node, info, system

class AbstractGrisNode(object):
    r"""
        GrisNodeの基底クラス。必ずnode.AbstractNodeと合わせて
        多重継承させる必要がある。
    """
    BasicName = ''
    NodeType = ''
    BasicAttrs = []
    ExtraAttrs = []
    def _test(self):
        r"""
            設定されたノードが、このクラスを構成するに足るかどうを判定する。
            
            Returns:
                bool:
        """
        if not self.isType(self.NodeType):
            return False
        for attr in [
            x[0].get('ln', x[0].get('longName')) for x in self.BasicAttrs
        ]:
            if not self.hasAttr(attr):
                return False
        return True

    @classmethod
    def _create(cls, **keywords):
        r"""
            ノードを作成するためのクリエーターメソッド。
            
            Args:
                **keywords (dict):
                
            Returns:
                any:
        """
        if cls.BasicName:
            if 'name' in keywords:
                del keywords['name']
            keywords['n'] = cls.BasicName
        n = node.createNode(cls.NodeType, **keywords)

        for flags, state, value in cls.BasicAttrs + cls.ExtraAttrs:
            attrname = flags.get('ln', flags.get('longName'))
            node.cmds.addAttr(n, **flags)
            if value is not None:
                n(attrname, value[0], **value[1])
            node.cmds.setAttr(n + '.' + attrname, **state)
        return cls(n())

    def setup(self):
        r"""
            関連ノードの作成を行う上書き専用メソッド。
            特に関連ノードがなければ記述する必要はない。
        """
        pass


class AbstractRootNode(AbstractGrisNode):
    r"""
        アセットのルートとなるノードを定義する基底クラス。
    """
    def _setupRelatedNode(self, groupType, grisNodeClass, **keywords):
        r"""
            groupTypeに接続されているノードを返すメソッド。
            コネクションにノードが存在していない場合は、grisNodeClassで
            指定したノードを作成し、groupTypeアトリビュートととの
            コネクションを作成する。
            
            Args:
                groupType (str):
                grisNodeClass (AbstractGrisNode):
                **keywords (dict):
                
            Returns:
                any:
        """
        t_attr = self.attr(groupType)
        n = t_attr.source()
        if n:
            return grisNodeClass(n())

        n = grisNodeClass._create(**keywords)
        n.attr('message') >> t_attr
        return n


class AbstractRootSet(AbstractRootNode):
    r"""
        ルートとなるセットを定義するための基底クラス。
        AbstractRootNode:のセット版。
    """
    def _setupRelatedNode(self, groupType, grisNodeClass, **keywords):
        r"""
            groupTypeに接続されているノードを返すメソッド。
            コネクションにノードが存在していない場合は、grisNodeClassで
            指定したノードを作成し、groupTypeアトリビュートととのコネクションを
            作成する。
            AbstractRootNode:と違い、keywordsにpフラグを指定すると、
            そのセットの子セットになる。
            
            Args:
                groupType (str):
                grisNodeClass (AbstractGrisNode):
                **keywords (dict):
                
            Returns:
                any:
        """
        parent_set = ''
        for key in ('p', 'parent'):
            if key in keywords:
                parent_set =  keywords.pop(key)
        node = super(AbstractRootSet, self)._setupRelatedNode(
            groupType, grisNodeClass, **keywords
        )
        if parent_set:
            parent_set.addChild(node)
        return node


class AbstractTopGroup(node.Transform, AbstractGrisNode):
    r"""
        グループトップとなるTransformノード用クラス。
        _createメソッドが呼ばれると、translate・rotate・scaleに
        ロックをかけてからノードオブジェクトを返す。
    """
    NodeType = 'transform'
    @classmethod
    def _create(cls, **keywords):
        r"""
            Args:
                **keywords (dict):
                
            Returns:
                AbstractTopGroup:
        """
        n = super(AbstractTopGroup, cls)._create(**keywords)
        n.lockTransform()
        return n


class AbstractDataSet(node.ObjectSet, AbstractGrisNode):
    r"""
        クラスメンバ変数IDの文字列をsetのテキストに入れた状態でobjectSetを
        作成するクラス。
    """
    NodeType = 'objectSet'
    ID = ''
    @classmethod
    def _create(cls, **keywords):
        r"""
            Args:
                **keywords (dict):
                
            Returns:
                AbstractDataSet:
        """
        n = super(AbstractDataSet, cls)._create(**keywords)
        if cls.ID:
            n('an', cls.ID, type='string')
        return n

class ManagerSet(AbstractDataSet):
    r"""
        特定の命名規則にそってセットを生成する機能を提供するクラス
        サブクラスは必ず定数NodeIDを作成し、BasicAttrsには
        enum:型のpositionを表すアトリビュートを含む必要がある。
    """
    BasicAttrs = [
        (
            {
                'ln':'position', 'at':'enum',
                'en':':'.join(
                    system.GlobalSys().defaultPositionList()
                )
            }, {'k':False, 'cb':True}, None
        ),
    ]
    NodeID = 'mngSet'
    def listPositions(self):
        r"""
            このノードが持つpositionのenum文字列のリストを返す
            
            Returns:
                str:
        """
        return node.cmds.attributeQuery(
            'position', le=True, n=self()
        )[0].split(':')

    def setPosition(self, position):
        r"""
            位置を表すインデックスをセットする。
            
            Args:
                position (str):
        """
        self('position', system.GlobalSys().toPositionIndex(position))

    def position(self):
        r"""
            位置を表す文字列を返す。
            
            Returns:
                str:
        """
        return system.GlobalSys().positionFromIndex(self('position'))

    def positionIndex(self):
        r"""
            位置を表すインデックスを返す。
            
            Returns:
                int:
        """
        return self('position')

    def addSet(self, baseName, position=0):
        r"""
            新しいAnimSetをこのセットの子として追加する。
                すでに存在する場合は、存在しているそのノードを返す。
            
            Args:
                baseName (str):
                position (str): 位置を表すインデックスまたは文字

            Returns:
                any:
        """
        name = system.GlobalSys().nameRule()()
        name.setName(baseName)
        name.setNodeType(self.NodeID)
        name.setPosition(position)
        if node.cmds.objExists(name()):
            return self.__class__(name())

        subset = createNode(self.__class__, n=name())
        subset.setPosition(position)
        super(ManagerSet, self).addChild(subset)
        return subset

class AnimSet(ManagerSet):
    r"""
        コントローラ登録用animSetの機能を提供するクラス。
    """
    BasicAttrs = [
        ({'ln':'order', 'at':'long', 'dv':0}, {'k':False, 'cb':True}, None),
        (
            {
                'ln':'position', 'at':'enum',
                'en':':'.join(
                    system.GlobalSys().defaultPositionList()
                )
            }, {'k':False, 'cb':True}, None
        ),
        ({'ln':'category', 'dt':'string'}, {'l':True}, None),
        ({'ln':'extra', 'dt':'string'}, {'l':True}, None),
        ({'ln':'ignore', 'at':'bool', 'dv':0}, {'k':False, 'cb':True}, None),
    ]
    ID = 'grisAnimSet'
    NodeID = 'anmSet'


class DisplaySet(ManagerSet):
    r"""
        表示・非表示を制御するセット機能を提供するクラス。
    """
    BasicAttrs = [
        ({'ln':'display', 'at':'bool', 'dv':1}, {'k':True}, None),
        (
            {
                'ln':'displayType', 'at':'enum',
                'en':':Normal:Template:Reference', 'dv':0
            },
            {'k':True, 'l':False}, None
        ),
        (
            {'ln':'overrideEnabled', 'at':'bool', 'h':True, 'dv':1},
            {}, None
        ),
        (
            {'ln':'displaySet', 'at':'message', 'm':True, 'im':False}, {}, None
        ),
        (
            {
                'ln':'position', 'at':'enum',
                'en':':'.join(
                    system.GlobalSys().defaultPositionList()
                )
            }, {'k':False, 'cb':True}, None
        ),
    ]
    ID = 'grisDisplaySet'
    ConnectedAttrs = [
        ('overrideEnabled', 'overrideEnabled'),
        ('display', 'overrideVisibility'),
        ('displayType', 'overrideDisplayType'),
    ]
    NodeID = 'dpsSet'
    def addChild(self, *child):
        r"""
            ディスプレイセットにオブジェクトを追加する。
            
            Args:
                *child (tuple):
        """
        super(DisplaySet, self).addChild(*child)
        connections = [
            (self.attr(x), y) for x, y in self.ConnectedAttrs
        ]
        for c in child:
            for srcattr, dstattr in connections:
                d_attr = c+'.'+dstattr
                if srcattr.isConnecting(d_attr):
                    continue
                srcattr >> d_attr

    def addSet(self, baseName, position=0):
        r"""
            新しいDisplaySetをこのセットの子として追加する。
            
            Args:
                baseName (str):
                position (str):位置を表すインデックスまたは文字
                
            Returns:
                DisplaySet:
        """
        dsp = super(DisplaySet, self).addSet(baseName, position)
        node.cmds.connectAttr(dsp+'.message', self+'.displaySet', na=True)
        return dsp

class AllSet(AbstractDataSet, AbstractRootSet):
    r"""
        allSet用クラス。
    """
    BasicName = 'allSet'
    BasicAttrs = [
        ({'ln':'animSet', 'at':'message'}, {}, None),
        ({'ln':'displaySet', 'at':'message'}, {}, None),
    ]
    ID = 'grisAllSet'
    def animSet(self):
        r"""
            animSetのルートを返す。
            
            Returns:
                AnimSet:
        """
        return self._setupRelatedNode(
            'animSet', AnimSet, p=self, n='all_anmSet'
        )

    def displaySet(self):
        r"""
            displaySetのルートを返す。
            
            Returns:
                DisplaySet:
        """
        return self._setupRelatedNode(
            'displaySet', DisplaySet, p=self, n='all_dspSet'
        )

    def setup(self):
        r"""
            関連ノードの作成を行う。
            
            Returns:
                list:
        """
        nodes = [x() for x in (self.animSet, self.displaySet)]
        return nodes


# /////////////////////////////////////////////////////////////////////////////
# モデルにまつわるクラス。                                                   //
# /////////////////////////////////////////////////////////////////////////////
class SubdivSet(AbstractDataSet):
    r"""
        サブディビジョンをかけるノードを格納するセット用クラス。
    """
    BasicName = 'subdiv_set'
    ID = 'modelSubdiv_set'


class ModelAllSet(AbstractDataSet, AbstractRootSet):
    r"""
        モデル版allSet用クラス。
    """
    BasicName = 'modelAllSet'
    BasicAttrs = [
        ({'ln':'subdivSet', 'at':'message'}, {}, None),
    ]
    ID = 'grisModelAllSet'
    def subdivSet(self):
        r"""
            サブディビジョンをかけるノードを格納するセットを返す。
            
            Returns:
                SubdivSet:
        """
        return self._setupRelatedNode('subdivSet', SubdivSet, p=self)

    def setup(self):
        r"""
            関連ノードの作成を行う。
            
            Returns:
                list:
        """
        nodes = [x() for x in (self.subdivSet,)]
        return nodes

class RigDataGroup(AbstractTopGroup):
    r"""
        リグに必要な情報として示すノードを格納するグループ用クラス。
    """
    BasicName = 'rigData_grp'

class RenderDataGroup(AbstractTopGroup):
    r"""
        レンダリングに必要な情報として示すノードを格納するグループ
    """
    BasicName = 'renderData_grp'

class ModelAllGroup(AbstractTopGroup, AbstractRootNode):
    r"""
        モデル用のルートグループクラス。
    """
    BasicName = 'all_grp'
    BasicAttrs = [
        ({'ln':'rigDataGroup', 'at':'message'}, {}, None),
        ({'ln':'renderDataGroup', 'at':'message'}, {}, None),
        ({'ln':'modelAllSet', 'at':'message'}, {}, None),
    ]
    def rigDataGroup(self):
        r"""
            rigData_grpを参照する。存在しない場合は作成される。
            
            Returns:
                RigDataGroup:
        """
        return self._setupRelatedNode('rigDataGroup', RigDataGroup, p=self)

    def renderDataGroup(self):
        r"""
            renderDataGroupを参照する。存在しない場合は作成される。
            
            Returns:
                RenderDataGroup:
        """
        return self._setupRelatedNode(
            'renderDataGroup', RenderDataGroup, p=self
        )

    def modelAllSet(self):
        r"""
            modelAllSetを参照する。存在しない場合は作成される。
            
            Returns:
                ModelAllSet:
        """
        return self._setupRelatedNode('modelAllSet', ModelAllSet)

    def setup(self):
        r"""
            関連ノードの作成を行う。
            
            Returns:
                list:
        """
        nodes = [
            x() for x in (
                self.rigDataGroup, self.renderDataGroup, self.modelAllSet,
            )
        ]
        for node in nodes:
            node.setup()
        return nodes
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////

# /////////////////////////////////////////////////////////////////////////////
# rootノードにまつわるクラス。                                               //
# /////////////////////////////////////////////////////////////////////////////
class UnitGroup(AbstractTopGroup):
    r"""
        unitを格納するgroupに関するクラス
    """
    BasicName = 'unit_grp'
    def listUnits(self):
        r"""
            このグループが持つユニットをリストで返す。
            
            Returns:
                list:Unitのリスト
        """
        return listNodes(Unit, self.children())

class Unit(AbstractTopGroup):
    r"""
        ユニットを定義するメタノードを取扱うクラス。
    """
    BasicAttrs = [
        ({'ln':'unitName', 'dt':'string'}, {'l':True}, None),
        (
            {
                'ln':'position', 'at':'enum',
                'en':':'.join(
                    system.GlobalSys().defaultPositionList()
                )
            }, {}, None
        ),
        ({'ln':'suffix', 'dt':'string'}, {'l':True}, None),
    ]
    def setUnitName(self, name):
        r"""
            ユニット名をセットする。
            
            Args:
                name (str):
        """
        self('unitName', name, type='string')

    def unitName(self):
        r"""
            ユニット名を返す。
            
            Returns:
                str:
        """
        return self('unitName')

    def setPosition(self, position):
        r"""
            位置を表す文字列をセットする。
            
            Args:
                position (str):
                
        """
        self('position', system.GlobalSys().toPositionIndex(position))

    def position(self):
        r"""
            位置を表す文字列を返す。
            
            Returns:
                str:
        """
        return system.GlobalSys().positionFromIndex(self('position'))

    def positionIndex(self):
        r"""
            位置を表すインデックスを返す。
            
            Returns:
                int:
        """
        return self('position')

    def setSuffix(self, suffix):
        r"""
            サフィックスをセットする。
            
            Args:
                suffix (str):
        """
        self('suffix', suffix, type='string')

    def suffix(self):
        r"""
            サフィックスを返す。
            
            Returns:
                str:
        """
        return self('suffix')

    def addMember(self, label, nodes):
        r"""
            unitにノードを紐付けるためのメソッド。
            引数nodesは引数labelによって定義されるメッセージ
            アトリビュートに接続され、後のリグ作成時などに活用される。
            尚引数nodesがリストの場合はマルチアトリビュートとして
            アトリビュートが作成される。
            
            Args:
                label (str):[]作成されるアトリビュート名
                nodes (str or list):メンバーとなるノードの名前のリスト
        """
        is_list = isinstance(nodes, (list, tuple))
        if not self.hasAttr(label):
            keywords = {'m':True, 'im':False} if is_list else {}
            attr = self.addMessageAttr(label, **keywords)
        else:
            attr = self.attr(label)
        if is_list:
            for n in nodes:
                node.cmds.connectAttr(n+'.message', self/label, na=True)
        else:
            nodes+'.message' >> attr

    def getMember(self, keyword):
        r"""
            引数keywordで指定されたアトリビュートに紐付けされているノードを返す。
            
            Args:
                keyword (str):
        """
        if not self.hasAttr(keyword):
            return
        attr = self.attr(keyword)
        connections = node.cmds.listConnections(self/keyword, s=True, d=False)
        if not connections:
            return []

        if attr.isArray():
            return node.toObjects(connections)
        else:
            return node.asObject(connections[0])

class BaseJointGroup(AbstractTopGroup):
    r"""
        ベースジョイントを格納するgroupに関するクラス
    """
    BasicName = 'joint_grp'
    BasicAttrs = [
        ({'ln':'topNode', 'at':'message'}, {}, None),
    ]
    def worldTransform(self):
        r"""
            ジョイント階層のトップとなるノードを返す。
            
            Returns:
                node.Transform:
        """
        return self.attr('topNode').source()

    def setup(self):
        r"""
            ジョイント階層のトップとなるworld_trsを作成する。
        """
        trs = node.createNode('transform', n='world_trs', p=self())
        trs.attr('message') >> self.attr('topNode')

class CtrlGroup(AbstractTopGroup):
    r"""
        コントローラを格納するgroupに関するクラス
    """
    BasicName = 'ctrl_grp'
    BasicAttrs = [
        ({'ln':'rigGroup', 'at':'message'}, {}, None),
        ({'ln':'ctrlRoot', 'at':'message'}, {}, None),
        ({'ln':'ctrlTop', 'at':'message'}, {}, None),
        ({'ln':'displayCtrl', 'at':'message'}, {}, None),
    ]
    def rigGroup(self):
        r"""
            リグ用のデータを格納するグループを返す。
            
            Returns:
                node.Transform:
        """
        return self.attr('rigGroup').source()

    def ctrlRoot(self):
        r"""
            コントローラの最上位ルート階層を返す。
            デフォルトでは何も接続されていないので、Constructorの
            createRoot:関数内で、それぞれが任意にコントローラを接続
            する必要がある。
            
            Returns:
                node.Transform:
        """
        return self.attr('ctrlRoot').source()

    def ctrlTop(self):
        r"""
            コントローラの最下層ノードを返す。
            このノードが、その他全てのコントローラの親となる。
            
            Returns:
                node.Transform:
        """
        return self.attr('ctrlTop').source()

    def displayCtrl(self):
        r"""
            表示制御用コントローラを返す。
            このノードはDisplayCtrlクラスの仕様に合わせる必要がある。
            
            Returns:
                DisplayCtrl:
        """
        return DisplayCtrl(self.attr('displayCtrl').source())

    def _setCtrls(self, rootCtrl, topCtrl, displayCtrl):
        r"""
            任意のノードを、コントローラのルート、トップおよび表示用
            コントローラとしてこのノードにセットする。
            displayCtrlはDisplayCtrlクラスの仕様に合わせる必要がある。
            
            Args:
                rootCtrl (str):ルートコントローラの名前
                topCtrl (str):サブコントローラのトップの名前
                displayCtrl (str):表示コントローラの名前
        """
        disp_ctrl = DisplayCtrl(displayCtrl)
        if not disp_ctrl._test():
            raise ValueError(
                'The given node as displayCtrl "%s" is invalid.' % displayCtrl
            )
        rootCtrl + '.message' >> self.attr('ctrlRoot')
        topCtrl + '.message' >> self.attr('ctrlTop')
        displayCtrl + '.message' >> self.attr('displayCtrl')

    def setup(self):
        r"""
            リグ用のデータを格納するグループを作成する。
        """
        rig_grp = node.createNode('transform', n='rig_grp', p=self())
        disp_attr = rig_grp.addDisplayAttr(default=False, cb=True)
        disp_attr >> rig_grp/'v'
        rig_grp.lockTransform()
        rig_grp.attr('message') >> self.attr('rigGroup')
    

class SetupGroup(AbstractTopGroup):
    r"""
        セットアップデータを格納するgroupに関するクラス
    """
    BasicName = 'setup_grp'
    BasicAttrs = [
        ({'ln':'bindJointGroup', 'at':'message'}, {}, None),
        ({'ln':'cageGroup', 'at':'message'}, {}, None),
    ]
    def bindJointGroup(self):
        r"""
            バインドジョイントを格納するグループを返す。
            
            Returns:
                node.Transform:
        """
        return self.attr('bindJointGroup').source()

    def cageGroup(self):
        r"""
            ケージを格納するグループを返す。
            
            Returns:
                node.Transform:
        """
        return self.attr('cageGroup').source()

    def setup(self):
        r"""
            バインドジョイントとケージを格納するグループを作製する。
            
            Returns:
                any:
        """
        for name, attr in (
            ('bindJoint_grp', 'bindJointGroup'),
            ('cage_grp', 'cageGroup')
        ):
            grp = node.createNode('transform', n=name, p=self())
            grp.lockTransform()
            grp.attr('message') >> self.attr(attr)

    @classmethod
    def _create(cls, **keywords):
        r"""
            Args:
                **keywords (dict):
                
            Returns:
                SetupGroup:
        """
        n = super(SetupGroup, cls)._create(**keywords)
        attr = n.addDisplayAttr(default=False)
        attr >> n.attr('v')
        return n

class GrisRoot(AbstractTopGroup, AbstractRootNode):
    r"""
        アセットのルートとなるノードを定義するクラス。
    """
    BasicName = 'root'
    NodeType = 'geometryVarGroup'
    BasicAttrs = (
        ({'ln':'assetName', 'dt':'string'}, {'l':True}, None),
        ({'ln':'project', 'dt':'string'}, {'l':True}, None),
        ({'ln':'assetType', 'dt':'string'}, {'l':True}, None),
        ({'ln':'allSet', 'at':'message'}, {}, None),
    )
    ExtraAttrs = (
        ({'ln':'grisVersion', 'dt':'string'}, {'l':True}, None),
        ({'ln':'unitGroup', 'at':'message'}, {}, None),
        ({'ln':'baseJointGroup', 'at':'message'}, {}, None),
        ({'ln':'controllerGroup', 'at':'message'}, {}, None),
        ({'ln':'setupGroup', 'at':'message'}, {}, None),
    )
    def setAssetName(self, assetName):
        r"""
            アセット名をセットする
            
            Args:
                assetName (str):
        """
        self('assetName', assetName, type='string')

    def assetName(self):
        r"""
            セットされているアセット名を返す。
            
            Returns:
                str:
        """
        return self('assetName')

    def setAssetType(self, assetType):
        r"""
            アセットタイプをセットする
            
            Args:
                assetType (str):
        """
        self('assetType', assetType, type='string')

    def assetType(self):
        r"""
            セットされているアセットタイプを返す。
            
            Returns:
                str:
        """
        return self('assetType')

    def setProject(self, project):
        r"""
            プロジェクト名をセットする
            
            Args:
                project (str):
        """
        self('project', project, type='string')

    def project(self):
        r"""
            セットされているプロジェクト名を返す。
            
            Returns:
                str:
        """
        return self('project')

    def unitGroup(self):
        r"""
            unit_grpを参照する。存在しない場合は作成される。
            
            Returns:
                UnitGroup:
        """
        return self._setupRelatedNode('unitGroup', UnitGroup, p=self)

    def baseJointGroup(self):
        r"""
            joint_grpを参照する。存在しない場合は作成される。
            
            Returns:
                BaseJointGroup:
        """
        return self._setupRelatedNode(
            'baseJointGroup', BaseJointGroup, p=self
        )

    def ctrlGroup(self):
        r"""
            ctrl_grpを参照する。存在しない場合は作成される。
            
            Returns:
                CtrlGroup:
        """
        return self._setupRelatedNode('controllerGroup', CtrlGroup, p=self)

    def setupGroup(self):
        r"""
            ctrl_grpを参照する。存在しない場合は作成される。
            
            Returns:
                SetupGroup:
        """
        return self._setupRelatedNode('setupGroup', SetupGroup, p=self)

    def allSet(self):
        r"""
            allSetを参照する。存在しない場合は作成される。
            
            Returns:
                AllSet:
        """
        return self._setupRelatedNode('allSet', AllSet)

    def setup(self):
        r"""
            関連ノードの作成を行う。
        """
        return [
            x() for x in (
                self.unitGroup, self.baseJointGroup, self.ctrlGroup,
                self.setupGroup, self.allSet
            )
        ]

    def setCreationData(self):
        r"""
            ルートに製作者名と制作日時を記述する。
        """
        import getpass
        attrs = []
        for at in ('author', 'creationDate'):
            if not self.hasAttr(at):
                attrs.append(self.addStringAttr(at))
            else:
                attrs.append(self.attr(at))
            attrs[-1].setLock(False)

        import os, datetime
        attrs[0].set(getpass.getuser(), type='string')
        attrs[1].set(
            datetime.datetime.now().strftime('%Y/%m/%d - %H:%M:%S'),
            type='string'
        )
        for at in attrs:
            at.setLock(True)

    @classmethod
    def _create(cls, **keywords):
        r"""
            createNode関数で呼ばれるクラスメソッド。
            
            Args:
                **keywords (dict):
                
            Returns:
                GrisRoot:
        """
        n = super(GrisRoot, cls)._create(**keywords)
        n('grisVersion', info.Version, type='string')
        return n

class DisplayCtrl(node.Transform, AbstractGrisNode):
    NodeType = 'transform'
    BasicAttrs = [
        (
            {'at':'enum', 'ln':'lod', 'en':'Low:High'},
            {'k':False, 'cb':True}, None
        ),
        (
            {
                'at':'enum', 'ln':'displayType',
                'en':'Normal:Template:Reference'
            },
            {'k':False, 'cb':True}, None,
        ),
        (
            {
                'at':'enum', 'ln':'jointDisplay',
                'en':'Normal:Template:Reference'
            },
            {'k':False, 'cb':True}, None,
        )
    ]
    @classmethod
    def _create(cls, **keywords):
        r"""
            Args:
                **keywords (dict):
                
            Returns:
                DisplayCtrl:
        """
        n = super(DisplayCtrl, cls)._create(**keywords)
        n.lockTransform(k=False, l=False)
        return n

# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////


# /////////////////////////////////////////////////////////////////////////////
# 関数。                                                                     //
# /////////////////////////////////////////////////////////////////////////////
def createNode(nodeClass, **keywords):
    r"""
        GrisNodeに関するノードを作成する
        
        Args:
            nodeClass (AbstractGrisNode):
            **keywords (dict):
            
        Returns:
            any:
    """
    return nodeClass._create(**keywords)

def nodeSetup(node):
    r"""
        GrisNodeに対し、再帰的にセットアップを行う。
        
        Args:
            node (AbstractGrisNode):
    """
    objects = node.setup()
    if not objects:
        return
    for obj in objects:
        nodeSetup(obj)

def listNodes(grisNode, *nodelist, **keywords):
    r"""
        このモジュールで定義されたAbstractGrisNodeの派生クラスに該当する
        ノードをリストで返す。
        引き数nodelistとkeywordsはcmds.lsにわたす引き数となる。
        
        Args:
            grisNode (AbstractGrisNode):
            *nodelist (tuple):
            **keywords (dict):
            
        Returns:
            list:
    """
    result = []
    for n in node.ls(*nodelist, type=grisNode.NodeType, **keywords):
        gn = grisNode(n.name())
        if gn._test():
            result.append(gn)
    return result

def listGrisRoots(*nodelist, **keywords):
    r"""
        アセットのルートノードをリストで返す。
        
        Args:
            *nodelist (tuple):
            **keywords (dict):
            
        Returns:
            list:
    """
    return listNodes(GrisRoot, *nodelist, **keywords)

def getGrisRoot():
    r"""
        アセットのルートノード"GrisRoot"を返す。
        listGrisRoots:と違い、シーン中に唯一でない場合はエラーを返す。
        
        Returns:
            GrisNode:
    """
    roots = listGrisRoots()
    if not roots:
        raise RuntimeError('No gris root is not in the current scene.')
    if len(roots) > 1:
        raise RuntimeError('More than one gris root are in the scene.')
    return roots[0]
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////
