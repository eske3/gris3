#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    リグ用スクリプトを管理するモジュール。
    
    Dates:
        date:2017/01/22 0:01[Eske](eske3g@gmail.com)
        update:2020/10/20 14:18 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import re
from abc import ABCMeta, abstractmethod
from .. import grisNode, func, node, lib, system, verutil
cmds = func.cmds

RigNamePattern = re.compile('Rig[A-Z]*$')

class BaseCreator(object):
    r"""
        ユニットデータ作成クラスの基底クラス。
    """
    Axises = ['X', 'Y', 'Z']
    LockControllerColor = True

    def __init__(self):
        self.__grisroot = None
        self.__lockedlist = []

    def root(self):
        r"""
            grisNode.GrisRootを返す。ない場合はNoneを返す。
            grisNode:.GrisRootはシーン中に１つである必要がある。
            
            Returns:
                grisNode.GrisRoot:
        """
        if not self.__grisroot:
            try:
                self.__grisroot = grisNode.getGrisRoot()
            except:
                self.__grisroot = None
        return self.__grisroot

    def jointRoot(self):
        r"""
            ジョイントのトップノード(全てのジョイントのトップ)を返す。
            
            Returns:
                node.Transform:
        """
        return self.root().baseJointGroup().worldTransform()

    def ctrlGroup(self):
        r"""
            コントローラを保持するトップノードを返す。
            
            Returns:
                node.CtrlGroup:
        """
        return self.root().ctrlGroup()

    def ctrlTop(self):
        r"""
            コントローラのトップ(全てのコントローラのトップ)を返す。
            
            Returns:
                node.Transform:
        """
        return self.root().ctrlGroup().ctrlTop()

    def rigGroup(self):
        r"""
            リグのグループトップを返す。
            
            Returns:
                node.Transform:
        """
        return self.root().ctrlGroup().rigGroup()

    def setupGroup(self):
        r"""
            セットアップ用のデータを格納するルートを返す。
            
            Returns:
                grisNode.SetupGroup:
        """
        return self.root().setupGroup()

    def allSet(self):
        r"""
            allSetを返す。
            
            Returns:
                grisNode.AllSet:
        """
        return self.root().allSet()

    def allAnimSet(self):
        r"""
            animセットのトップを返す。
            
            Returns:
                grisNode.AnimSet:
        """
        return self.root().allSet().animSet()

    def allDisplaySet(self):
        r"""
            displaySetのトップを返す。
            
            Returns:
                grisNode.DisplaySet:
        """
        return self.root().allSet().displaySet()

    def addLockedList(self, nodelist):
        r"""
            postProcess内でTransformのロックをかけるノードを追加する。
            
            Args:
                nodelist (str):listでも可
        """
        if isinstance(nodelist, (list, tuple)):
            self.__lockedlist.extend(nodelist)
        else:
            self.__lockedlist.append(nodelist)

    def removeLockedList(self, nodelist):
        r"""
            任意のノードをロックリストから解除する。
            
            Args:
                nodelist (str):listでも可
        """
        nodelist = (nodelist
            if isinstance(nodelist, (list, tuple)) else [nodelist]
        )
        for n in nodelist:
            if not n in self.__lockedlist:
                continue
            index = self.__lockedlist.index(n)
            del self.__lockedlist[index]

    def lockLockedListNodes(self):
        r"""
            addLockedListによって登録されたノードのtransformをロック
        """
        if not self.__lockedlist:
            return
        func.lockTransform([x for x in self.__lockedlist if x])

    def createParentMatrixNode(self, baseJoint):
        r"""
            jointのトップから指定ノードまでのmatrixを表すmultMatrixを返す。
            引数baseJointはジョイント階層のトップであるworldTransform内に
            いる事が前提となる。
            
            Args:
                baseJoint (str):
                
            Returns:
                AbstractNode:multMatrix
        """
        node_chain = func.listNodeChain(self.jointRoot(), baseJoint)
        if len(node_chain) < 2:
            return

        node_chain.reverse()
        mltmtx = func.createUtil('multMatrix')
        matrix_list = [x/'matrix' for x in node_chain[:-1]]
        func.connectMultAttr(matrix_list, '%s.matrixIn' % mltmtx)
        return mltmtx

    def constraintFromBaseJoint(self, nodes, parentBaseJoint):
        r"""
            parentBaseJointからnodesで指定されたノードのリストへコンストレイン
            を行う。
            コンストレインはdecomposeMatrixによって行うため、nodeはtransform
            ノードが望ましい。(jointOrientが0の場合、jointでも可）
            
            Args:
                nodes (list):[node.Transform, ...]
                parentBaseJoint (str):
                
            Returns:
                list:作成されたdecomposeMatrix、multMatrix
        """
        nodes = nodes if isinstance(nodes, (list, tuple)) else [nodes]
        mltmtx = self.createParentMatrixNode(parentBaseJoint)
        if not mltmtx:
            # １階層しかない場合は、直接コネクトする。
            func.connectKeyableAttr(parentBaseJoint, node)
            return
        decmtx = func.createDecomposeMatrix(
            nodes[0], [mltmtx/'matrixSum'], False
        )[0]
        if len(nodes) > 1:
            func.makeDecomposeMatrixConnection(dexmtx, nodes[1:])
        return [decmtx, mltmtx]

    def createBaseJointProxy(self, srcNode, name='transform', parent=None):
        r"""
            引数srcNodeと同じ位置のTransformを引数parent内に作成する。
            
            Args:
                srcNode (str):
                name (str):作成されるノードの名前
                parent (node.AbstractNode):親ノード
                
            Returns:
                node.Transform:
        """
        srcNode = node.asObject(srcNode)
        parent = node.asObject(parent) if parent else self.unitRigGroup()

        proxy = node.createNode(srcNode.type(), n=name, p=parent)
        if hasattr(proxy, 'hideDisplay'):
            proxy.hideDisplay()
        proxy.setMatrix(srcNode.matrix())
        return proxy

    def createParentProxy(self, srcNode, name='transform', parent=None):
        r"""
            引数srcNodeの親と同じ位置のTransformを引数parent内に作成する。
            
            Args:
                srcNode (str):
                name (str):作成されるノードの名前
                parent (node.AbstractNode):親ノード
                
            Returns:
                node.Transform:
        """
        srcNode = node.asObject(srcNode)
        if not srcNode.hasParent():
            return
        return self.createBaseJointProxy(srcNode.parent(), name, parent)

    def createRigParentProxy(self, srcNode, name, position=None):
        r"""
            rigGroup内にsrcNodeの親と同じ位置のTransformを作成する。
            srcNodeはjoint_grpのworldTransform下にある必要がある。
            
            Args:
                srcNode (str):
                name (str):ノードのベース名
                position (str/int):位置を表す文字または数字
                
            Returns:
                node.Transform:
        """
        n = func.Name()
        n.setName(name+'Rig')
        n.setNodeType('parentProxy')
        n.setPosition(
            self.unit().position() if position is None else position
        )
        return self.createParentProxy(srcNode, n())

    def createCtrlParentProxy(self, srcNode, name, position=None):
        r"""
            コントローラのトップ階層下に、srcNodeの親と同じ位置のTransformを
            作成する。
            srcNodeはjoint_grpのworldTransform下にある必要がある。
            
            Args:
                srcNode (str):
                name (str):ノードのベース名。
                position (int/str):位置を表す文字または数字
                
            Returns:
                noide.Transform:
        """
        n = func.Name()
        n.setName(name+'Ctrl')
        n.setNodeType('parentProxy')
        n.setPosition(
            self.unit().position() if position is None else position
        )
        return self.createParentProxy(srcNode, n(), self.ctrlTop())

    def shapeCreator(self):
        r"""
            新規のPrimitiveCreatorを返す。
            
            Returns:
                func.PrimitiveCreator:
        """
        return func.PrimitiveCreator()

    def storeDefaultToAllControllers(self):
        r"""
            animSetに登録されている全てのコントローラの現在の状態をデフォルト
            として登録する。
        """
        from ..tools import controllerUtil
        for ctrl in self.allAnimSet().allChildren():
            m = controllerUtil.DefaultAttrManager(ctrl)
            m.setDefault()
    
    def lockControllersColor(self):
        if not self.LockControllerColor:
            return
        from ..tools import curvePrimitives
        curvePrimitives.addWireColorCtrlAttr(*self.allAnimSet().allChildren())



class StandardCreator(BaseCreator):
    r"""
        標準的な作成用クラス
    """
    def __init__(self, unit=None):
        r"""
            初期化を行う。引数unitにはgrisNodeのUnitオブジェクトを渡すが、
            なくても機能はする。
            
            Args:
                unit (grisNode.Unit):
        """
        super(StandardCreator, self).__init__()
        if unit is not None:
            self.setUnit(unit)
        else:
            self.__unit = None

    def setUnit(self, unit):
        r"""
            ユニットノードをセットする。
            
            Args:
                unit (grisNode.Unit):
        """
        if not isinstance(unit, grisNode.Unit):
            raise TypeError(
                'The given argument must be instance of gris3.grisNode.Unit'
            )
        self.__unit = unit

    def unit(self):
        r"""
            このクラスが管理するユニットを返す。
            
            Returns:
                grisNode.Unit:
        """
        return self.__unit

    def unitName(self):
        r"""
            ユニットの名前をNameRuleオブジェクトにして返す。
            
            Returns:
                system.BasicNameRule:
        """
        return system.GlobalSys().defaultNameRule()(self.unit())

    def baseName(self):
        r"""
            ユニット用のノードのベースとなる名前を返す。
            
            Returns:
                str:
        """
        return self.unitName().name()

    def process(self):
        r"""
            実行時に呼ばれるオーバーライド要メソッド。
        """
        pass

    def postProcess(self):
        r"""
            作成後の後処理メソッド。
        """
        self.lockLockedListNodes()


class JointCreator(StandardCreator):
    r"""
        ユニットのジョイントを作成する機能を提供する基底クラス。
    """
    def __init__(self, unit=None):
        r"""
            Args:
                unit (grisNode.Unit):
        """
        super(JointCreator, self).__init__(unit)
        self.__unit_type = str(self.__class__).split('.')[-2]
        self.__name = ''
        self.__position = 1
        self.__parent = None
        self.__unit = None
        self.__options = {}
        self.__basename = None

    def setName(self, name):
        r"""
            ベースとなる名前をセットする。
            
            Args:
                name (str):
        """
        self.__name = name
    
    def name(self):
        r"""
            ベースとなる名前を返す。
            
            Returns:
                str:
        """
        return self.__name

    def setSuffix(self, suffix):
        r"""
            名前につけるサフィックスをセットする。
            
            Args:
                suffix (str):
        """
        self.__suffix = suffix

    def suffix(self):
        r"""
            名前につけるサフィックスを返す。
            
            Returns:
                str:
        """
        if self.unit():
            return self.unit().suffix()
        else:
            return self.__suffix

    def setBasenameObject(self, nameObject=None):
        r"""
            ベースネームを定義するNameRuleオブジェクトをセットする。
            
            Args:
                nameObject (system.AbstractNameRule):
        """
        if not nameObject:
            name = system.GlobalSys().nameRule()()
            name.setSuffix(self.suffix())
            name.setPosition(self.position())
            name.setNodeType('jnt')
            self.__basename = name
        else:
            self.__basename = nameObject

    def basenameObject(self):
        r"""
            ベースネームを定義するNameRuleオブジェクトを返す。
            
            Returns:
                system.AbstractNameRule:
        """
        return self.__basename

    def setParent(self, parent):
        r"""
            親を指定する。
            指定された親がジョイントのルート下にいないいない場合はjointRootを
            親として指定する。
            
            Args:
                parent (grisNode.AbstractNode):
        """
        root_joint = self.jointRoot()
        try:
            func.listNodeChain(root_joint, parent)
        except ValueError:
            self.__parent = root_joint
            return
        self.__parent = parent

    def parent(self):
        r"""
            設定されている親を返す。
            
            Returns:
                node.AbstractNode:
        """
        return self.__parent

    def asRoot(self, *joints):
        r"""
            引数で指定したノードをユニットのルートとして登録する。
            
            Args:
                *joints (tuple):ジョイント名のリスト
        """
        unit = self.unit()
        shapes = []
        namerule = system.GlobalSys().nameRule()
        for joint in node.toObjects(joints):
            name = namerule(joint.shortName())
            name.setNodeType('unitRoot')
            loc = node.createNode('locator', n=name(), p=joint)
            if joint.isType('joint'):
                joint.attr('radius') >> ~loc.attr('localScale')
            ~joint.attr('rotatePivot') >> ~loc.attr('localPosition')
                
            loc.applyColor((1, 0.62, 0.02))
            for attr in ('localScale', 'localPosition'):
                for axis in 'XYZ':
                    plug = loc.attr(attr+axis)
                    plug.setChannelBox(False)
                    plug.setKeyable(False)
            msg_plug = loc.addMessageAttr('unitRoot')
            unit/'message' >> msg_plug

            shapes.append(loc)

    def unitType(self):
        r"""
            ユニットタイプを表す文字列を返す。
            
            Returns:
                str:
        """
        return self.__unit_type

    def setPosition(self, position):
        r"""
            このユニットの場所を表す文字列をセットする。
            
            Args:
                position (int/str):
        """
        self.__position = system.GlobalSys().toPositionIndex(position)

    def position(self):
        r"""
            このユニットの場所を表す文字列を返す。
            
            Returns:
                int/str:
        """
        return system.GlobalSys().positionFromIndex(self.__position)

    def positionIndex(self):
        r"""
            このユニットの場所を表すインデックスを返す。
            
            Returns:
                int:
        """
        return self.__position

    def createUnit(self):
        r"""
            ユニットノードを作成する。
        """
        basename = self.name()
        if not basename:
            raise RuntimeError('The basename was not defined.')

        # ルートを探し、そのルートからunitをまとめるグループを探す。===========
        gris_root = grisNode.getGrisRoot()
        unit_grp = gris_root.unitGroup()
        # =====================================================================

        name = system.GlobalSys().defaultNameRule()()
        name.setSuffix(self.suffix())
        name.setName(self.name())
        name.setNodeType('unit')
        name.setPosition(self.position())
        position_list = name.positionList()

        # unit = node.createNode('transform', n=name(), p=unit_grp())
        unit = grisNode.createNode(grisNode.Unit, n=name(), p=unit_grp())
        unit.lockTransform()

        # ユニット名を保持するアトリビュートを追加し、セットする。
        unit.setUnitName(self.unitType())
        # 位置を表すアトリビュートを追加し、セットする。
        unit.setPosition(self.position())

        # サフィックスを保持するアトリビュートを追加し、セットする。
        unit.setSuffix(self.suffix())

        self.setUnit(unit)

    def setOptions(self, options):
        r"""
            オプションの値を保持したオブジェクトをセットする。
            
            Args:
                options (Option):
        """
        self.__options = options
    
    def options(self):
        r"""
            オプションの値を保持したオブジェクトを返す。
            
            Returns:
                Option:
        """
        return self.__options

    def createBaseJoint(self, parent):
        r"""
            ジョイントを作成する際に呼ばれるエントリメソッド。
            
            Args:
                parent (str):作成する際のターゲットとなる親の名前
        """
        unit = self.createUnit()
        self.setParent(parent)
        self.process()
        self.postProcess()

    def finalize(self):
        r"""
            ファイナライズ時にコールされる、オーバーライド用メソッド。
        """
        pass

    def execFinalize(self):
        r"""
            ファイナライズ時にコールされる。
            内部ではrootマーカーを消してfinalizeをコールする。
        """
        connected = self.unit().attr('message').destinations(p=True)
        deleted = [
            x.nodeName() for x in connected if x.attrName() == 'unitRoot'
        ]
        if deleted:
            cmds.delete(deleted)
        self.finalize()


class RigCreator(StandardCreator):
    r"""
        リグを作成するための機能を提供する基底クラス。
    """
    LeftSideColorTable = {
        'main':15, 'sub':29, 'extra':28, 'special':18, 'key':6,
    }
    RightSideColorTable = {
        'main':31, 'sub':30, 'extra':9, 'special':20, 'key':4,
    }
    CenterColorTable = {
        'main':23, 'sub':26, 'extra':25, 'special':27, 'key':14,
    }
    def __init__(self, unit):
        r"""
            Args:
                unit (grisNode.Unit):
        """
        super(RigCreator, self).__init__(unit)
        self.__animset = None
        self.__rig_group = None

    def axisX(self):
        r"""
            ユニットのposition設定にもとづいて、X軸が正方向か負方向かを返す。
            
            Returns:
                str:'-X'か'+X'
        """
        return '-X' if self.unit().positionIndex() == 3 else '+X'

    def vectorX(self):
        r"""
            ユニットのposition設定に基づいて、正方向か負方向のX軸ベクトルを返す。
            
            Returns:
                list:[-1, 0, 0]または[1, 0, 0]
        """
        return [-1, 0, 0] if self.unit().positionIndex() == 3 else [1, 0, 0]

    def colorIndex(self, keyword):
        r"""
            キーワードに従って色の値を返す。
            キーワードはLeftSideColorTable、RightSideColorTableまたは
            CenterColorTableの辞書オブジェクトのキーのいずれか
            
            Args:
                keyword (str):
                
            Returns:
                int:
        """
        position = self.unit().positionIndex()
        if position == 2:
            return self.LeftSideColorTable.get(keyword, 15)
        elif position == 3:
            return self.RightSideColorTable.get(keyword, 31)
        else:
            return self.CenterColorTable.get(keyword, 23)

    def createRigGroup(self):
        r"""
            このユニットのリグを格納するグループを作成する。
        """
        unitname = self.unitName()
        unitname.setName(unitname.name()+'Rig')
        unitname.setNodeType('grp')
        root = node.createNode('transform', n=unitname(), p=self.rigGroup())
        root.lockTransform()
        self.__rig_group = root

    def unitRigGroup(self):
        r"""
            このユニットのリグを格納するためのグループを返す。
            
            Returns:
                node.Transform:
        """
        return self.__rig_group

    def createUnitAnimSet(self):
        r"""
            このユニット用のanimセットを作成する。
        """
        unit = self.unit()
        all_animset = self.allAnimSet()
        self.__animset = all_animset.addSet(self.baseName(), unit.position())

    def animSet(self):
        r"""
            このユニット用のanimセットを返す。
            
            Returns:
                grisNode.AnimSet:
        """
        return self.__animset

    def createBaseJoint(self):
        r"""
            ベーススケルトンを作成するためのオーバーライド専用メソッド。
        """
        pass

    def preProcess(self):
        r"""
            createRig内でリグ作成前に呼ばれるオーバーライド用メソッド。
        """
        pass

    def createRig(self):
        r"""
            リグ作成時に呼ばれるエントリメソッド。
        """
        self.createUnitAnimSet()
        self.preProcess()
        self.createRigGroup()
        self.process()
        self.postProcess()

class Option(object):
    r"""
        ユニット作成時のオプションを定義するクラス。
    """
    def __init__(self):
        self.__attributelist = []
        self.define()

    def define(self):
        r"""
            初期化時に呼ばれるオーバーライド用メソッド。
            オプションの定義などはこの中で行う。
        """
        pass

    def addFloatOption(self, attributeName, default=1.0, min=0.0, max=1.0):
        r"""
            float型のオプションを作成する。
            
            Args:
                attributeName (str):
                default (float):
                min (float):
                max (float):
        """
        self.__attributelist.append(
            ['float', attributeName, default, min, max]
        )

    def addIntOption(self, attributeName, default=1, min=0, max=1):
        r"""
            int型のオプションを作成する。
            
            Args:
                attributeName (str):
                default (int):
                min (int):
                max (int):
        """
        self.__attributelist.append(
            ['int', attributeName, default, min, max]
        )

    def addBoolOption(self, attributeName, default=1):
        r"""
            bool型のオプションを作成する。
            
            Args:
                attributeName (str):
                default (bool):
        """
        self.__attributelist.append(['bool', attributeName, default])

    def addEnumOption(self, attributeName, default=0, enumerations=[]):
        r"""
            列挙型のオプションを作成する。
            
            Args:
                attributeName (str):
                default (int):
                enumerations (list):列挙する文字列のリスト。
        """
        self.__attributelist.append(
            ['enum', attributeName, default, enumerations]
        )

    def addStringOption(self, attributeName, default=''):
        r"""
            str型のオプションを作成する。
            
            Args:
                attributeName (str):[]
                default (str):
        """
        self.__attributelist.append(
            ['string', attributeName, default]
        )

    def optionlist(self):
        r"""
            作成されたオプションのリストをリストで返す。
            
            Returns:
                list:
        """
        return self.__attributelist

def rigModuleList(loadMode=0):
    r"""
        grisのリグ用モジュールの一覧を返す。
        モジュールにIgnoreLoadアトリビュートがあり、その値がFalseの場合
        はリストの対象からはずれる。
        
        Args:
            loadMode (int):読み込みモード
            
        Returns:
            list:
    """
    import os
    rootpath = os.path.join(os.path.dirname(__file__))
    prefix = __name__
    return [
        x for x in lib.loadPythonModules(rootpath, prefix, loadMode)
        if not hasattr(x, 'IgnoreLoad') or x.IgnoreLoad
    ]

def getRigModule(unitType, isReload=False):
    r"""
        引数unitTypeのモジュールを返す
        
        Args:
            unitType (str):ユニット名
            isReload (bool):モジュールをリロードするかどうか
            
        Returns:
            module:
    """
    modulelist = rigModuleList()
    modulelist = [
        x for x in modulelist if x.endswith('.%s' % unitType)
    ]
    if not modulelist:
        raise RuntimeError(
            'No rig set was not found : %s' % unitType
        )
    module = lib.importModule(modulelist[0])
    if isReload:
        verutil.reload_module(module)
    return module

class PresetElement(object):
    r"""
        プリセットの要素を定義するクラス。
        Presetクラスのincludesメソッドで返されるリストの中にこのクラスの
        インスタンスを列挙する。
    """
    def __init__(self, unitName, position=0, suffix=''):
        r"""
            Args:
                unitName (str):ユニット名
                position (int):位置を表す0~8の番号
                suffix (str):同名ユニットの場合に識別するためのサフィックス
        """
        self.__unitname = unitName
        self.__suffix = suffix
        self.__position = position

    def __call__(self):
        r"""
            関数として呼び出し時に実行される
            
            Returns:
                str:
        """
        return '{}{}-{}'.format(
            self.unitName(), self.suffix(), self.positionString()
        )

    def __repr__(self):
        r"""
            正式名称を返す
            
            Returns:
                str:
        """
        return '{}{} : {}'.format(
            self.unitName(), self.suffix(), self.positionString()
        )

    def unitName(self):
        r"""
            ユニットの名前を返す。
            
            Returns:
                str:
        """
        return self.__unitname

    def positionString(self):
        r"""
            位置を表す文字列を返す。
            これは現在のsystem.GlobalPrefによって変化する。
            
            Returns:
                str:
        """
        return system.GlobalSys().positionFromIndex(self.position())

    def position(self):
        r"""
            位置を表す番号を返す。
            
            Returns:
                int:
        """
        return self.__position

    def suffix(self):
        r"""
            ユニット識別のためのsuffix
            
            Returns:
                str:
        """
        return self.__suffix


class Preset(BaseCreator):
    r"""
        プリセットを定義するメソッド。
    """
    __metaclass__ = ABCMeta
    @abstractmethod
    def name(self):
        r"""
            プリセット名を返す。
            
            Returns:
                str:
        """
        return ''

    @abstractmethod
    def includes(self):
        r"""
            プリセットに何を含んでいるかをリストで返す。
            
            Returns:
                list:
        """
        return []

    def moduleList(self):
        r"""
            モジュールのリストを返す。
            
            Returns:
                OrderedDict:
        """
        from collections import OrderedDict
        modules = OrderedDict()
        for preset in self.includes():
            mod = getRigModule(preset.unitName(), True)
            name = (
                mod.BaseName if hasattr(mod, 'BaseName') else preset.unitName()
            )
            creator = mod.JointCreator()
            creator.setName(mod.BaseName)
            creator.setPosition(preset.position())
            creator.setSuffix('')
            creator.setBasenameObject()
            modules[preset()] = creator
        return modules

    def description(self):
        r"""
            プリセットの概要を説明する文を返す。
            
            Returns:
                str:
        """
        return ''

    def create(self, creators):
        r"""
            ベースジョイントを作成する。
            
            Args:
                creators (list):
        """
        for creator in creators:
            creator.createBaseJoint(None)

    def execute(self):
        r"""
            登録されているモジュール全てのベースジョイントを作成する。
        """
        creators = self.moduleList()
        self.create(creators)

