#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Mayaを操作する便利関数・クラスを提供するモジュール。
    
    Dates:
        date:2017/01/21 23:02[Eske](eske3g@gmail.com)
        update:2025/05/27 17:57 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import re
import math

from . import mayaCmds as cmds
from . import node
from maya import mel

from . import lib, mathlib, verutil
from .numericalChar import Alphabet
from .tools.curvePrimitives import PrimitiveCreator

# nodeモジュールの関数セットを取り込む。=======================================
asObject = node.asObject
toObjects = node.toObjects
createUtil = node.createUtil
# =============================================================================

# 必要プラグインのロード。=====================================================
for plugin in ('matrixNodes', 'nearestPointOnMesh'):
    if not cmds.pluginInfo(plugin, q=True, l=True):
        cmds.loadPlugin(plugin)
# =============================================================================

# 正規表現オブジェクトのタイプを調べるためのオブジェクト。=====================
RETYPE = type(re.compile(''))

Positions = [
    'L', 'R', 'F', 'B', 'U', 'D', 'C', 'None'
]
# =============================================================================


# The lists of transformation attributes.======================================
## The list of axis.
Axis = ['x', 'y', 'z']

## The list of translate attributes.
TranslateAttr = ['tx', 'ty', 'tz']
TranslateAttrShortName = {
    'translateX' : 'tx', 'translateY' : 'ty', 'translateZ' : 'tz'
}

## The list of rotate attributes.
RotateAttr    = ['rx', 'ry', 'rz']

## The list of scale attributes.
ScaleAttr     = ['sx', 'sy', 'sz']
ScaleAttrShortName = {'scaleX' : 'sx', 'scaleY' : 'sy', 'scaleZ' : 'sz'}
# =============================================================================

Do = node.DoCommand()

def createLocator(**keywords):
    r"""
        ロケータを作成する。
        
        Args:
            **keywords (dict):cmds.createNodeに渡す引数と同じ。
            
        Returns:
            node.Transform:
    """
    trs = node.createNode('transform', **keywords)
    loc = node.createNode('locator', n=trs+'Shape', p=trs)
    return trs

def createSpaceNode(**keywords):
    r"""
        スペーサーとしてのノードを作成する。
        
        Args:
            **keywords (dict):cmds.createNodeに渡す引数と同じ。
            
        Returns:
            node.Joint:
    """
    spacenode = node.createNode('joint', **keywords)
    spacenode.hideDisplay()
    spacenode.setInverseScale()
    return spacenode

SoftIkExpTemplate = '''float $stretch = %(stretchValue)s;
float $softness = %(softIkAttr)s * 0.01;
float $defaultLength = %(defaultLengthAttr)s;
float $ctrlLength = %(ctrlLengthAttr)s;

float $softLength = $defaultLength * $softness;
float $delta = $defaultLength - $softLength;

float $ikX = 0;
if($softness != 0 && $ctrlLength > $delta){
    float $scaleRatio = %(scaleRatioAttr)s;
    float $invScaleRatio = 1 - $scaleRatio;

    float $e = exp(($delta - $ctrlLength) / $softLength);
    float $softIkLength = (1 - $e) * $softLength + $delta;
    float $softRatio = $softIkLength / $defaultLength;

    $stretch = (1 / $softRatio * %(lengthRatio)s) * $scaleRatio + $invScaleRatio;
    $ikX = ($ctrlLength - $softIkLength) * $invScaleRatio;
}

%(targetAttrs)s
%(ikCounterAttr)s = $ikX;
'''

def createSoftIk(
        softIkAttr, stretchValueAttr, defaultLengthAttr, ctrlLengthAttr,
        scaleRatioAttr, lengthRatioAttr,
        targetAttrs, ikCounterAttr
    ):
    r"""
        ソフトikを作成する関数。
        
        Args:
            softIkAttr (str):ソフトIKの適用強度を操作するアトリビュート名
            stretchValueAttr (str):
            defaultLengthAttr (str):基準値となる長さを定義するアトリビュート名
            ctrlLengthAttr (str):
            scaleRatioAttr (str):
            lengthRatioAttr (str):
            targetAttrs (list):ストレッチの結果を受け取るアトリビュートのリスト
            ikCounterAttr (str):ソフトIKの結果を受け取るアトリビュート
            
        Returns:
            str:
    """
    target_attr_connections = ''
    for target_attr in targetAttrs:
        target_attr_connections += '%s = $stretch;\n' % target_attr

    expression = SoftIkExpTemplate % {
        'softIkAttr':softIkAttr,
        'stretchValue':stretchValueAttr,
        'defaultLengthAttr':defaultLengthAttr,
        'ctrlLengthAttr':ctrlLengthAttr,
        'scaleRatioAttr':scaleRatioAttr,
        'lengthRatio':lengthRatioAttr,
        'targetAttrs':target_attr_connections,
        'ikCounterAttr':ikCounterAttr
    }
    expr = cmds.expression(s=expression, o='', ae=1, uc='all')
    cmds.setAttr('%s.ihi' % expr, 0)
    return expr


def createSoftIkFromStretchNode(
        softIkAttr, stretchNode, ik
    ):
    r"""
        ストレッチノードを元にソフトIKを作成する関数。
        
        Args:
            softIkAttr (str):ソフトIKの適用強度を操作するアトリビュート名
            stretchNode (str):ソフトIKの結果のストレッチ値を受け取るアトリビュート
            ik (str):ソフトIKの結果を受け取るIKノード名
    """
    stretch_proxy = cmds.createNode(
        'transform', p=stretchNode, n='softIkScaleOutput_proxy#'
    )

    blender = cmds.listConnections(
        '%s.stretch' % stretchNode, d=True, type='blendTwoAttr'
    )[0]
    conditionNode = cmds.listConnections(
        '%s.input[0]' % blender, s=True, type='condition'
    )[0]
    lengthRatioNode = cmds.listConnections(
        '%s.input[1]' % blender, s=True, type='multiplyDivide'
    )[0]

    stretchAttr = '%s.stretchRatio' % stretchNode
    stretchConnection = cmds.listConnections(
        stretchAttr, s=True, d=False, p=True
    )
    if stretchConnection:
        cmds.disconnectAttr(stretchConnection[0], stretchAttr)
    stretchConnection = []

    stretchConnection = cmds.listConnections(
        stretchAttr, s=False, d=True, p=True
    )
    targetAttrs = ['%s.sx' % stretch_proxy]
    if stretchConnection:
        for con in stretchConnection:
            cmds.connectAttr('%s.sx' % stretch_proxy, con, f=True)
            #cmds.disconnectAttr(stretchAttr, con)
    #else:
    #   targetAttrs = [stretchAttr]

    createSoftIk(
        softIkAttr,
        '%s.outColorR' % conditionNode,
        '%s.firstTerm' % conditionNode,
        '%s.secondTerm' % conditionNode,
        '%s.attributesBlender' % blender,
        '%s.outputX' % lengthRatioNode,
        targetAttrs, '%s.tx' % ik
    )

def isnum(n):
    r"""
        引数が数値型かどうかを調べる関数。
        
        Args:
            n (any):
            
        Returns:
            bool:
    """
    return isinstance(n, (int, float, verutil.Long, complex))

# /////////////////////////////////////////////////////////////////////////////
# Math libs                                                                  //
# /////////////////////////////////////////////////////////////////////////////
Vector = mathlib.Vector
FMatrix = mathlib.FMatrix
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////

def Name(name=''):
    r"""
        グローバルな設定からNameオブジェクトを返す。
        
        Args:
            name (str):名前を表す文字列
            
        Returns:
            system.BasicNameRule:
    """
    from .system import GlobalSys
    return GlobalSys().nameRule()(name)


class SuffixModifier(str):
    r"""
        このクラスのインスタンスをコールする際に渡した文字列引数に任意の
        サフィックスを付加して返す機能を提供するクラス。
    """
    def __new__(cls, suffix, separator=''):
        r"""
            Args:
                suffix (str):サフィックス
                separator (str):サフィックス前に付けるセパレータ文字
                
            Returns:
                SuffixModifier:
        """
        obj = super(SuffixModifier, cls).__new__(cls, suffix)
        obj.__suffix = suffix
        obj.__separator = separator
        return obj

    def __repr__(self):
        r"""
            設定されたsuffixを返す。
            
            Returns:
                str:
        """
        return self.__suffix

    def __str__(self):
        r"""
            Returns:
                str:
        """
        return self.__suffix

    def __eq__(self, other):
        r"""
            Args:
                other (any):
                
            Returns:
                bool:
        """
        return self.__suffix == other

    def __hash__(self):
        r"""
            任意のサフィックスをハッシュキーとして返す。
            
            Returns:
                any:
        """
        return self.__suffix.__hash__()

    def __add__(self, other):
        r"""
            Args:
                other (str):
                
            Returns:
                str:
        """
        return self.__suffix + other

    def __radd__(self, other):
        r"""
            Args:
                other (str):
                
            Returns:
                str:
        """
        return other + self.__suffix

    def __mul__(self, other):
        r"""
            Args:
                other (str):
                
            Returns:
                str:
        """
        return self.__suffix + self.__separator + other

    def __rmul__(self, other):
        r"""
            Args:
                other (str):
                
            Returns:
                str:
        """
        return other + self.__separator + self.__suffix

    def setSuffix(self, suffix):
        r"""
            サフィックスを設定するメソッド。
            
            Args:
                suffix (str):サフィックス
        """
        self.__suffix = suffix

    def setSeparator(self, separator):
        r"""
            区切り文字を設定するメソッド。
            
            Args:
                separator (str):
        """
        self.__separator = separator

    def __call__(self, baseName):
        r"""
            与えられた文字＋区切り文字＋Suffixを返すコール関数のオーバーライド。
            
            Args:
                baseName (str):
                
            Returns:
                str:
        """
        return self.__separator.join((baseName, self.__suffix))

class SuffixIter(object):
    r"""
        与えられた文字をサフィックスとして持つSuffixModifierを返す
        イテレータ機能を持つクラス。
    """
    def __init__(self, *suffixes):
        r"""
            初期化関数。引数が空の場合は('L', 'R')を使用する。
            
            Args:
                *suffixes (tuple):原則一文字づつのリスト
        """
        self.__suffixes = suffixes if suffixes else ('L', 'R')
        self.__separator = '_'
        self.__i = 0

    def setSeparator(self, separator):
        r"""
            セパレータを設定するメソッド。デフォルトは"_"。
            
            Args:
                separator (str):
        """
        self.__separator = separator

    def next(self):
        r"""
            nextメソッドのオーバーライド。
            
            Returns:
                SuffixModifier:
        """
        if self.__i == len(self.__suffixes):
            self.__i = 0
            raise StopIteration()
        obj = SuffixModifier(
            self.__suffixes[self.__i], self.__separator
        )
        self.__i += 1
        return obj

    def __getitem__(self, slice):
        r"""
            Args:
                slice (any):
        """
        return SuffixModifier(self.__suffixes[slice], self.__separator)

    def __len__(self):
        return len(self.__suffixes)


def copyJointState(srcJoint, tgtJoint):
    r"""
        srcJointのt,r,s,joの状態をtgtJointへ移植する。
        
        Args:
            srcJoint (str):元ジョイント名
            tgtJoint (str):移植先のジョイント名
    """
    for attr in ['t', 'r', 's', 'jo']:
        for axis in Axis:
            value = cmds.getAttr('%s.%s%s' % (srcJoint, attr, axis))
            cmds.setAttr('%s.%s%s' % (tgtJoint, attr, axis), value)


def makeDecomposeMatrixConnection(
    decomposeMatrix, targets, makeShearConnection=True
):
    r"""
        decomposeMatrixノードをtargetsに接続する。
        
        Args:
            decomposeMatrix (str):ソースとなるdecomposeMatrix
            targets (list):接続されるノードのリスト
            makeShearConnection (bool):shearへの接続を行うかどうか
    """
    decmtx = asObject(decomposeMatrix)
    attrs = ('t', 'r', 's', 'sh') if makeShearConnection else 'trs'
    for target in targets:
        target = asObject(target)
        for attr in attrs:
            for src, dst in zip(
                ~decmtx.attr('o'+attr), ~target.attr(attr)
            ):
                if dst.isLocked():
                    continue
                src >> dst


def createDecomposeMatrix(
        target=None, matrices=[], withMultMatrix=True, startNumber=0,
        makeShearConnection=True
    ):
    r"""
        ターゲットTransformノードに任意のマトリックスリストの乗算値を
        decomposeMatrixを経由して接続する関数。
        引数withMultMatrixがFalseでかつmatricesの数が１の場合はmultMatrixを
        作成せず、戻り値はdecomposeMatrixを１つだけ含むリストになる。
        
        Args:
            target (node.Transform):Transformノード名
            matrices (list):合成するマトリクスのリスト
            withMultMatrix (bool):multMatrixを作成するかどうか
            startNumber (int):multMatrixのmatrixSnumに接続する最初の番号
            makeShearConnection (bool):shearへの接続を行うかどうか
            
        Returns:
            list:作成された[decomposeMatrix, multMatirx]のリスト
    """
    decmtx = createUtil('decomposeMatrix')
    if target:
        makeDecomposeMatrixConnection(decmtx, [target], makeShearConnection)

    # withMultMatrixがFalseかつmatricesが１つの場合のみ。======================
    # 戻り値がdecomposeMatrixのみになる。
    if not withMultMatrix:
        if len(matrices) == 1:
            matrices[0] >> decmtx.attr('inputMatrix')
        return [decmtx]
    # =========================================================================

    mltmtx = createUtil('multMatrix')
    mltmtx/'matrixSum' >> decmtx.attr('inputMatrix')
    if matrices:
        connectMultAttr(matrices, mltmtx/'matrixIn', startNumber)
    return [decmtx, mltmtx]


def connectMatrix(target, matrices=[], withMultMatrix=True, startNumber=0):
    r"""
        任意の行列リストをtargetへ接続する。
        maya2020前後で挙動が変わり、2019以前は内部ではcreateDecomposeMatrixを
        呼び出すが、2020以降はparentOffsetMatrixへ接続する。
        
        将来的に実装予定だが、現在2020以降への対応していない。
        
        Args:
            target (node.Transform):Transformノード名
            matrices (list):合成するマトリクスのリスト
            withMultMatrix (bool):multMatrixを作成するかどうか
            startNumber (int):
            
        Returns:
            list:作成された[decomposeMatrix, multMatirx]のリスト
    """
    return createDecomposeMatrix(
        target, matrices, withMultMatrix, startNumber
    )


def copyNode(nodename, nodeType=None, parent=None, suffix=''):
    r"""
        ノードをコピーする関数。子供がいる場合、子は無視される。
        与えられるノード名はこのツールの命名規則に従っている必要がある。
        
        Args:
            nodename (str):ノード名
            nodeType (str):ノードの種類を表す文字列
            parent (str):コピー後に配置される親ノード
            suffix (str):('') : サフィックス
            
        Returns:
            node.AbstractNode:
    """
    nodename = verutil.String(nodename)
    parent = verutil.String(parent) if parent else parent
    newnode = cmds.duplicate(nodename, po=True)[0]
    if parent:
        cur_parent = cmds.listRelatives(newnode, p=True, pa=True)
        if not cur_parent or cur_parent[0] != parent:
            try:
                newnode = cmds.parent(newnode, parent)[0]
            except:
                print('Children : {}'.format(newnode))
                print('Parent   : {}'.format(parent))
                raise ValueError('Failed to parent.')
    if nodeType or suffix:
        newnodeName = Name(nodename)
        nodetype = (nodeType if nodeType else newnodeName.nodeType()) + suffix
        newnodeName.setNodeType(nodetype)
        newnode = cmds.rename(newnode, newnodeName())

    # 上流との接続を切る。=====================================================
    con = cmds.listConnections(newnode, p=True, s=False, d=True, c=True)
    if con:
        for i in range(0, len(con), 2):
            dst_node = con[i+1].split('.', 1)[0]
            if cmds.nodeType(dst_node) == 'shadingEngine':
                continue
            cmds.disconnectAttr(con[i], con[i+1])
    # =========================================================================

    newnode = asObject(newnode)
    if newnode.isType('joint'):
        newnode.setInverseScale()
    return newnode


def copyNodeTree(rootNode, nodeType=None, parent=None, endJoint=None):
    r"""
        選択ノードの子供も調べて、その子も含めてコピーする。
        引数endJointは正規表現パターンを表し、このパターンに該当する
        オブジェクトが出現した時点でそのオブジェクトより下はコピーしない
        
        Args:
            rootNode (str):コピー元のルートノード。
            nodeType (str):コピー後のノード名につける種類を表す文字
            parent (str):コピー後のノードの親ノード。
            endJoint (_sre.SRE_Pattern):
            
        Returns:
            list:作成されたノードのリスト
    """
    rootNode = asObject(rootNode)
    newnode = copyNode(rootNode, nodeType, parent)

    result = [newnode]
    children = rootNode.children()
    if not children:
        return result

    for child in children:
        if endJoint and endJoint.search(child):
            continue
        result.extend(copyNodeTree(child, nodeType, newnode, endJoint))
    return result


def copyMesh(mesh, typeSuffix, nodeType='', parent=None):
    r"""
        meshシェイプをコピーする関数。コピーされるmeshはシェーディングがない。
        
        Args:
            mesh (str):コピー元のメッシュ名
            typeSuffix (str):ノードタイプのサフィックス
            nodeType (str):変更後のノードタイプを表す文字列
            parent (str):親ノード
            
        Returns:
            node.Mesh:
    """
    supported_types = {
        'mesh' : ('outMesh', 'inMesh'),
        'nurbsSurface' : ('local', 'create'),
        'nurbsCurve' : ('local', 'create'),
    }
    mesh = node.asObject(mesh)
    if mesh.isType('transform'):
        shape = mesh.shapes()
        if not shape:
            raise RuntimeError('%s is not supported type for copyMesh' % mesh)
        shape = shape[0]
    else:
        shape = mesh
    creation_type = shape.type()
    if not creation_type in supported_types:
        raise RuntimeError('%s is not supported type for copyMesh' % shape)
    if not parent:
        parent = cmds.listRelatives(mesh, p=True, pa=True)
        if parent:
            parent = parent[0]

    if nodeType:
        name = Name(mesh)
        name.setNodeType(nodeType + typeSuffix)
        new_name = name()
    else:
        new_name = mesh + '_' + typeSuffix

    new_mesh = node.createNode(creation_type, p=parent, n=new_name)
    out_plug, in_plug = supported_types[creation_type]
    cmds.connectAttr(mesh+'.'+out_plug, new_mesh+'.'+in_plug)
    cmds.delete(new_mesh, ch=True)

    return new_mesh


def copyMeshNode(mesh, nodeType, parent=None):
    r"""
        入力メッシュをコピーする。
        copyMeshと違い、こちらはTransformを新規で作成し、その下にコピーされた
        メッシュを格納する。
        戻り値としてコピーされたメッシュ名(transformノード)を返す。
        
        Args:
            mesh (str):コピー対象のメッシュ名
            nodeType (str):ノードの種類を表す文字列
            parent (str):コピー後の親ノード名。
            
        Returns:
            node.Transform:
    """
    mesh = asObject(mesh)
    if not parent:
        parent = mesh.parent()

    name = Name(mesh)
    name.setNodeType(nodeType)
    new_name = name()

    trs = node.createNode('transform', p=parent, n=new_name)
    new_mesh = copyMesh(mesh, 'CPDTEMP', 'TEMPTYPE', trs)
    new_mesh.rename(trs + 'Shape')
    return trs


def listCommonParentPathList(targetA, targetB):
    r"""
        targetAとtargetBの共通の親までのリストを２つ返す。
        
        Args:
            targetA (str):
            targetB (str):
            
        Returns:
            list:[targetAの親のリスト,targetBの親のリスト]
    """
    parent_lists = []
    for target in (targetA, targetB):
        parent = cmds.listRelatives(target, p=True, f=True)
        if parent:
            parent = parent[0].split('|')
            parent.reverse()
            parent_lists.append(parent)
        else:
            parent_lists.append([])
    parentsA = parent_lists[0]
    parentsB = parent_lists[1]

    if not parentsA or not parentsB:
        return [parentsA, parentsB]

    for i in range(len(parentsA)):
        if not parentsA[i] in parentsB:
            continue

        index = parentsB.index(parentsA[i])
        return [parentsA[:i+1], parentsB[:index+1]]


def listNodeChain(startNode, endNode):
    r"""
        始点と終端ノードを指定すると、その間の階層ノードをリストで返す。
        終端のノードは始点のノード下にある事が前提。
        
        Args:
            startNode (node.AbstractNode):始点となるノード。
            endNode (node.AbstractNode):終端となるノード。
            
        Returns:
            list:
    """
    startNode, endNode = node.toObjects((startNode, endNode))
    if startNode == endNode:
        return [startNode]
    if not endNode.hasParent():
        raise ValueError('"%s" is not under "%s".' % (endNode, startNode))
    fullname = endNode.fullName()
    startname = startNode.fullName()
    joint_chain = [endNode]
    while(True):
        fullname = fullname.rsplit('|', 1)[0]
        if not fullname:
            raise ValueError(
                (
                    'The specified end joint "%s" '
                    'is not child of %s' % (endNode, startNode)
                )
            )
        if startname == fullname:
            joint_chain.append(startNode)
            break
        joint_chain.append(asObject(fullname))
    joint_chain.reverse()
    return joint_chain


def listSingleChain(topNode):
    r"""
        任意のノード下にある、最初の子の階層チェーンを返すメソッド。
        
        Args:
            topNode (str):トップノード名。
            
        Returns:
            list:
    """
    from gris3.tools import util
    return util.listSingleChain(topNode)


def listLength(nodelist):
    r"""
        与えられたノードチェーンの、各ブロック間の長さをリストで返す。
        引数で渡すノードのリストはチェーン状に親子構造になっている必要がある。
        
        Args:
            nodelist (list):ノードのリスト
            
        Returns:
            float:
    """
    pre_position = Vector(cmds.xform(nodelist[0], q=True, ws=True, rp=True))
    node_length_list = []
    for i in range(len(nodelist) - 1):
        pos = Vector(cmds.xform(nodelist[i+1], q=True, ws=True, rp=True))
        bvector = pos - pre_position
        node_length_list.append(bvector.length())
        pre_position = pos

    return node_length_list


def listLengthRatio(nodelist):
    r"""
        与えられたノードチェーンの各ブロックの長さの、全長における割合を返す。
        引数で渡すノードのリストはチェーン状に親子構造になっている必要がある。
        
        Args:
            nodelist (list):
            
        Returns:
            float:
    """
    lengths = listLength(nodelist)
    total_length = sum(lengths)
    result = [0.0]
    current_length = 0
    
    for l in lengths:
        current_length += l
        result.append(current_length / total_length)
    return result


def listMatrixPath(targetA, targetB):
    r"""
        targetAからtargetBまでの共通の親を検索し、共通親を経由したローカル行列
        を返す。
        戻り値はリスト２つを持つtupleで1つ目は
            targetAから共通親までのmatrixで階層をつくるノードのリスト
        2つ目は
        　　共通親からtargetBまでのinverseMatrixで階層をつくるノードのリスト
        となる。

        共通の親が見つからない場合はNoneを返す。

        Args:
            targetA (str): トランスフォームノード（開始地点）
            targetB (str):トランスフォームノード（終了地点）
        
        Returns:
            tuple: 
    """
    target_a = node.asObject(targetA)
    target_b = node.asObject(targetB)
    st_p_list = target_a.fullName()
    ed_p_list = target_b.fullName()
    parent = st_p_list
    mtxlist = []
    while(True):
        parent, child = parent.rsplit('|', 1)
        mtxlist.append(parent)
        if not parent:
            break
        if ed_p_list.startswith(parent):
            break
    if not parent:
        return
    mtxlist = node.toObjects(mtxlist)
    invlist = func.listNodeChain(parent, target_b)
    return mtxlist, invlist[:-1]


def expandAttr(attributes):
    r"""
        t、r、s、アトリビュートをt:aの書式で渡した場合、[tx, ty, tz]のように
        各軸で分解した名前で返す。
        
        Args:
            attributes (list):アトリビュート名のリスト
            
        Returns:
            list:
    """
    result = []
    for attr in attributes:
        if attr.startswith(':'):
            if len(attr) == 1:
                attrStr = 'trs'
            else:
                attrStr = attr[1:]

            for a in attrStr:
                if a == 't':
                    result.extend(TranslateAttr)
                elif a == 'r':
                    result.extend(RotateAttr)
                elif a == 's':
                    result.extend(ScaleAttr)
            continue

        if attr.find(':') < 1:
            result.append(attr)
            continue

        data = attr.split(':')
        if data[-1] == 'a' or len(data) == 1:
            result.append('%sx' % data[0])
            result.append('%sy' % data[0])
            result.append('%sz' % data[0])
        elif data[-1] == 'A':
            result.append('%sX' % data[0])
            result.append('%sY' % data[0])
            result.append('%sZ' % data[0])
    return result


def controlChannels(nodes, attributes,
    isKeyable=None, isLocked=None, isChannelBox=None, **keywords
    ):
    r"""
        アトリビュートのチャンネルボックスでの挙動を制御するメソッド。
        
        Args:
            nodes (list):操作対象となるノード
            attributes (list):捜査対象となるアトリビュートのリスト
            isKeyable (bool):キーアブルかどうかのフラグ
            isLocked (bool):ロックをかけるかどうかのフラグ
            isChannelBox (bool):チャンネルボックスに表示するかどうかのフラグ
            **keywords (dict):
    """
    pa = lib.ParseArgs(keywords)
    if isKeyable == None:
        isKeyable = pa.value(('isKeyable', 'k'), True)
    if isLocked == None:
        isLocked = pa.value(('isLocked', 'l'), False)
    if isChannelBox == None:
        isChannelBox = pa.value(('isChannelBox', 'cb'), False)

    attributeList = expandAttr(attributes)
    for node in nodes:
        for attr in attributeList:
            if not cmds.attributeQuery(attr, ex=True, n=str(node)):
                continue

            cmds.setAttr(
                '%s.%s' % (node, attr),
                k=isKeyable, l=isLocked, cb=isChannelBox
            )


def lockTransform(nodes, hideVisibility=True):
    r"""
        ノードのリストのtrsアトリビュートをロック＆非表示する。
        
        Args:
            nodes (list):transformノードのリスト
            hideVisibility (bool):visibilityを非表示にするかどうか
    """
    for n in nodes:
        node.Transform(n).lockTransform()


def unlockTransform(nodes, showVisibility=True):
    r"""
        ノードのリストのtrsアトリビュートをアンロック＆表示する。
        
        Args:
            nodes (list):transformノードのリスト
            showVisibility (bool):visibilityを表示するかどうか
    """
    for n in nodes:
        node.Transform(n).unlockTransform()


def setRenderStats(nodes, **keywords):
    r"""
        Args:
            nodes (any):
            **keywords (any):
    """
    default_settings = {
        'castsShadows': 1,
        'receiveShadows': 1,
        'holdOut': 0,
        'motionBlur': 1,
        'primaryVisibility': 1,
        'smoothShading': 1,
        'visibleInReflections': 1,
        'visibleInRefractions': 1,
        'doubleSided': 1,
    }
    default_settings.update(keywords)
    print('# Set render stats.'.ljust(80, '='))
    for n in nodes:
        results = []
        for attr, val in default_settings.items():
            try:
                cmds.setAttr(n + '.' + attr, val)
            except:
                pass
            else:
                results.append('    - set {} : {}'.format(attr, val))
        if not results:
            continue
        print('  Set render stats to "{}"'.format(n))
        for r in results:
            print(r)
        print('-' * 80)
    print('=' * 80)


def fitTransform(
            srcNode, dstNode,
            translate=True, rotate=True, scale=True, shear=True
    ):
    r"""
        dstNodeの位置をsrcNodeの位置へ合わせる。
        
        Args:
            srcNode (str):位置合わせを行うためのソースとなるtransformノード
            dstNode (str):位置を合わせる対象となるtransformノード
            translate (bool):translateを合わせるかどうか
            rotate (bool):rotateを合わせるかどうか
            scale (bool):scaleを合わせるかどうか
            shear (bool):shearを合わせるかどうか
    """
    src = node.asObject(srcNode)
    dst = node.asObject(dstNode)
    flags = int(
        ''.join(
            ['1' if x else '0' for x in (translate, rotate, scale, shear)]
        ),
        2
    )
    dst.fitTo(src, flags)


def fConnectAttr(srcNodeAttr, dstNodeAttr):
    r"""
        srcNodeAttrをdstNodeAttrへ接続する。
        dstNodeAttrがロックされていてもロックを解除してから接続する。
        
        Args:
            srcNodeAttr (str):
            dstNodeAttr (str):
    """
    lockState = cmds.getAttr(dstNodeAttr, l=True)
    if lockState :
        cmds.setAttr(dstNodeAttr, l=False)
    cmds.connectAttr(srcNodeAttr, dstNodeAttr, f=True)
    if lockState:
        cmds.setAttr(dstNodeAttr, l=True)


def kConnectAttr(srcNodeAttr, dstNodeAttr, ignoreKeyable=False):
    r"""
        dstNodeAttrがロックされていない場合だけsrcNodeAttrを接続する。
        またignoreKeyableがTrueの場合、dstNodeAttrがkeyableの場合のみ接続する
        
        Args:
            srcNodeAttr (str):
            dstNodeAttr (str):
            ignoreKeyable (bool):
            
        Returns:
            bool:接続したかどうか
    """
    if cmds.getAttr(dstNodeAttr, l=True):
        return False

    if not ignoreKeyable and not cmds.getAttr(dstNodeAttr, k=True):
        return False

    cmds.connectAttr(srcNodeAttr, dstNodeAttr, f=True)
    return True


def transferConnection(srcNodeAttr, dstNodeAttr, keepConnection=False):
    r"""
        srcNodeAttrに接続しているアトリビュートをdstNodeAttrへ接続しなおす。
        keepConnectionがFalseの場合、srcNodeAttrへの接続は解除する。
        
        Args:
            srcNodeAttr (str):
            dstNodeAttr (str):
            keepConnection (bool):
            
        Returns:
            str:接続しなおしたアトリビュート名
    """
    src = cmds.listConnections(srcNodeAttr, s=True, scn=False, p=True)
    if not src:
        return
    fConnectAttr(src[0], dstNodeAttr)
    if not keepConnection:
        value = cmds.getAttr(srcNodeAttr)
        cmds.disconnectAttr(src[0], srcNodeAttr)
        cmds.setAttr(srcNodeAttr, value)
    return src[0]


def connectKeyableAttr(srcNode, dstNode):
    r"""
        keyableアトリビュート同士を接続する。
        
        Args:
            srcNode (str):
            dstNode (str):
    """
    attr = cmds.listAttr(srcNode, k=True)
    if not attr:
        return
    srcNode = asObject(srcNode)
    dstNode = asObject(dstNode)
    for at in attr:
        if not dstNode.hasAttr(at):
            continue
        fConnectAttr('%s.%s' % (srcNode, at), '%s.%s' % (dstNode, at))


def connectMultAttr(srcAttrs, dstAttr, startNumber=0):
    r"""
        マルチアトリビュートdstAttrに、srcAttrsを順に接続する。
        
        Args:
            srcAttrs (list):入力アトリビュートのリスト
            dstAttr (str):接続されるマルチアトリビュート名。
            startNumber (int):接続されるマルチアトリビュートの開始番号
    """
    for src_attr in srcAttrs:
        cmds.connectAttr(src_attr, '%s[%s]' % (dstAttr, startNumber))
        startNumber += 1


def connect3ChannelAttr(
        srcAttr, dstAttr, srcAxises='xyz', dstAxises='xyz',
        ignoreKeyable=False
    ):
    r"""
        複数の子アトリビュート同士を接続する。
        
        Args:
            srcAttr (str):[]ソースアトリビュート
            dstAttr (str):[]相手のアトリビュート
            srcAxises ([str or list):ソースの子アトリビュートのリスト
            dstAxises (str or list):相手の子アトリビュートのリスト
            ignoreKeyable (bool):keyableではなくても接続するかどうか
    """
    if isinstance(srcAttr, node.Attribute):
        srcAttr = srcAttr.split('.')[0] + '.' + srcAttr.attrName(False)
    if isinstance(dstAttr, node.Attribute):
        dstAttr = dstAttr.split('.')[0] + '.' + dstAttr.attrName(False)

    if '%s' in srcAttr:
        src_attr_format = srcAttr
    else:
        src_attr_format = srcAttr + '%s'

    if '%s' in dstAttr:
        dst_attr_format = dstAttr
    else:
        dst_attr_format = dstAttr + '%s'

    for src_axis, dst_axis in zip(srcAxises, dstAxises):
        kConnectAttr(
            src_attr_format % src_axis, dst_attr_format % dst_axis,
            ignoreKeyable
        )


def replaceConnections(srcNode, dstNode, source=True, destination=True):
    r"""
        srcNodeのコネクションをdstNodeにつなぎ直し、srcNodeのコネクションは開放する。
        srcNodeとdstNodeは互換性のあるノードが望ましい。
        
        Args:
            srcNode (str):元ノード
            dstNode (str):つなぎ直しの対象ノード
            source (bool):入力コネクションのつなぎ直しを行うかどうか
            destination (bool):出力コネクションのつなぎ直しを行うかどうか
    """
    def reconnect(srcNode, dstNode, srcFlag):
        r"""
            再接続を行うローカル関数
            
            Args:
                srcNode (str):元ノード
                dstNode (str):対象ノード
                srcFlag (bool):入力コネクションを対象とするかどうか
        """
        con = cmds.listConnections(
            srcNode, s=srcFlag, d=srcFlag==False, p=True, c=True
        )
        if not con:
            return
        for i in range(0, len(con), 2):
            new_plug = con[i].split('.')
            new_plug[0] = dstNode
            new_plug = '.'.join(new_plug)

            if srcFlag:
                cmds.disconnectAttr(con[i+1], con[i])
                fConnectAttr(con[i+1], new_plug)
            else:
                cmds.disconnectAttr(con[i], con[i+1])
                fConnectAttr(new_plug, con[i+1])
    if source:
        reconnect(srcNode, dstNode, True)
    if destination:
        reconnect(srcNode, dstNode, False)


def blendAttr(srcNodeAttr, targetAttr):
    r"""
        ソースとターゲットのアトリビュートをブレンドする仕組みを作る
        
        Args:
            srcNodeAttr (str):ソースノードのアトリビュート
            targetAttr (str):ターゲットノードのアトリビュート
            
        Returns:
            node.AbstractNode:blendWeightedノード
    """
    blender = createUtil('blendWeighted')
    index = 0
    for src_attr in srcNodeAttr:
        cmds.connectAttr(src_attr, '%s.input[%s]' % (blender, index))
        index += 1
    cmds.connectAttr('%s.output' % blender, targetAttr, f=True)
    return blender


def copyKeyableAttr(srcNode, dstNode):
    r"""
        srcNodeのkeyableアトリビュートの値をdstNodeへ適用する
        
        Args:
            srcNode (str):
            dstNode (str):
    """
    kattrs = cmds.listAttr(srcNode, k=True)
    if not kattrs:
        return

    for attr in kattrs:
        if not cmds.attributeQuery(attr, ex=True, n=dstNode):
            continue
        value = cmds.getAttr('%s.%s' % (srcNode, attr))
        cmds.setAttr('%s.%s' % (dstNode, attr), value)


def setAttrFromConnected(nodeAttr, **keywords):
    r"""
        引数で指定されたアトリビュートに接続されているコネクションを外し
        接続されていた時の値をセットする関数。
        
        Args:
            nodeAttr (str):値をセットするノード・アトリビュート名。
            **keywords (dict):cmds.setAttrコマンドに渡す引数と同じ
    """
    src = cmds.listConnections(nodeAttr, s=True, d=False, p=True)
    if not src:
        return
    srcAttr = src[0]
    value = cmds.getAttr(srcAttr)
    attrType = cmds.getAttr(srcAttr, type=True)
    cmds.disconnectAttr(srcAttr, nodeAttr)
    try:
        cmds.setAttr(nodeAttr, value, **keywords)
    except:
        cmds.setAttr(nodeAttr, value, type=attrType)
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////


        
# /////////////////////////////////////////////////////////////////////////////
# There are functions to create a rig system.                                //
# /////////////////////////////////////////////////////////////////////////////
def createMovementWeightList(transforms, ratioPower=2):
    r"""
        与えられたTransformのリストの位置関係から、ウェイト値を生成する
        
        Args:
            transforms (list):ノードのリスト
            ratioPower (int):
            
        Returns:
            list:
    """
    start_position = Vector(
        cmds.xform(transforms[0], q=True, ws=True, rp=True)
    )
    end_position = Vector(
        cmds.xform(transforms[-1], q=True, ws=True, rp=True)
    )
    trs_length_list = listLength(transforms)
    total_length = sum(trs_length_list)
    tmp_length = 0
    trs_length_list.insert(0, 0)

    result = []
    for i in range(len(transforms)):
        tmp_length += trs_length_list[i]
        result.append((tmp_length / total_length) ** ratioPower)
    return result


def blendTransform(
        srcNodeA, srcNodeB, dstNodes, blendControlAttr=None,
        skipTranslate=False, skipRotate=False, skipScale=False,
        blendMode=0,
    ):
    r"""
        srcNodeAとsrcNodeBの位置をpairBlendでブレンドしてdstNodesに適用する。
        適用割合はblendControlAttrで指定したアトリビュートで変更可能。
        blendControlAttrがNoneの場合、作成されたpairBlendには何も行わない
        
        Args:
            srcNodeA (str):ソースとなるtransformノードA
            srcNodeB (str):ソースとなるtransformノードB
            dstNodes (list):操作対象transformノードのリスト
            blendControlAttr (str):ブレンドを操作するアトリビュート名
            skipTranslate (bool):translateのブレンドをスキップするかどうか
            skipRotate (bool):rotateのブレンドをスキップするかどうか
            skipScale (bool):scaleのブレンドをスキップするかどうか
            blendMode (bool):rotateの制御方法。１の場合Quantumを使用。
            
        Returns:
            list:作成されたpairBlendノードのリスト
    """
    result = []
    pairBlend_tr = None
    pairBlend_s = None
    srcNodePair = ([srcNodeA, srcNodeB], [srcNodeB, srcNodeA])
    
    if not isinstance(dstNodes, (list, tuple)):
        dstNodes = [dstNodes]

    for attr, skip_mode in zip(['t', 'r'], [skipTranslate, skipRotate]):
        if skip_mode:
            continue

        if not pairBlend_tr:
            pairBlend_tr = createUtil('pairBlend')
            cmds.setAttr('%s.rotInterpolation' % pairBlend_tr, blendMode)
            result.append(pairBlend_tr)

        for index, nodeset in zip(range(2), srcNodePair):
            index += 1
            if nodeset[0]:
                connect3ChannelAttr(
                    '%s.%s' % (nodeset[0], attr),
                    pairBlend_tr + '.i' + attr + '%s' + str(index),
                    ignoreKeyable=True
                )
            elif not nodeset[0] and nodeset[1]:
                for axis in Axis:
                    value = cmds.getAttr('%s.%s%s' % (nodeset[1], attr, axis))
                    cmds.setAttr(
                        '%s.i%s%s%s' % (pairBlend_tr, attr, axis, index), value
                    )

        for dstNode in dstNodes:
            connect3ChannelAttr(
                '%s.o%s' % (pairBlend_tr, attr), '%s.%s' % (dstNode, attr)
            )

    if not skipScale:
        pairBlend_s = createUtil('pairBlend')
        result.append(pairBlend_s)
        for index, nodeset in zip(range(2), srcNodePair):
            index += 1
            if nodeset[0]:
                connect3ChannelAttr(
                    '%s.s' % nodeset[0], pairBlend_s + '.it%s' + str(index),
                    ignoreKeyable=True
                )
            elif not nodeset[0] and nodeset[1]:
                for axis in Axis:
                    value = cmds.getAttr('%s.s%s' % (nodeset[1], axis))
                    cmds.setAttr('%s.it%s%s' % (pairBlend_s, axis, index))

        for dstNode in dstNodes:
            connect3ChannelAttr(
                '%s.ot' % pairBlend_s, '%s.s' % dstNode, ignoreKeyable=True
            )

    if not blendControlAttr:
        return result

    if pairBlend_tr:
        cmds.connectAttr(blendControlAttr, '%s.weight' % pairBlend_tr)
    if pairBlend_s:
        cmds.connectAttr(blendControlAttr, '%s.weight' % pairBlend_s)

    return result


def blendSelfConnection(node, blendControlAttr=None,
        skipTranslate=False, skipRotate=False,  skipScale=False,
        blendMode=0, origToBlended=True
    ):
    r"""
        Transformノードについているコネクションをブレンド出来るようにする。
        blendControlAttr:にアトリビュート名を入れると、そのアトリビュートを
        使用してWeightをコントロール出来るようになる。
        
        origToBlendedがTrueの場合、weightが１の時に元のコネクションの位置になる。
        
        Args:
            node (str):対象ノード
            blendControlAttr (str):
            skipTranslate (bool):Translateへの処理をスキップする
            skipRotate (bool):Rotateへの処理をスキップする
            skipScale (bool):Scaleへの処理をスキップする
            blendMode (int):rotateの制御方法。１の場合Quantumを使用。
            origToBlended (bool):
            
        Returns:
            list:作成されたpairBlendノードのリスト
    """
    index_table = (1, 2) if origToBlended else (2, 1)
    def connectOrSetAttr(node, outattr, pair_blend, pbattr):
        r"""
            Args:
                node (str):
                outattr (str):
                pair_blend (str):
                pbattr (str):
        """
        for ax in Axis:
            attr = node + '.' + outattr + ax
            value = cmds.getAttr(attr)

            con = cmds.listConnections(attr, s=True, d=False, p=True)
            if con:
                cmds.disconnectAttr(con[0], attr)
                cmds.connectAttr(
                    con[0],
                    pair_blend + '.i%s%s%s' % (pbattr, ax, index_table[1])
                )
            else:
                cmds.setAttr(
                    '%s.i%s%s%s' % (pair_blend, pbattr, ax, index_table[1]),
                    value
                )

            cmds.setAttr(
                '%s.i%s%s%s' % (pair_blend, pbattr, ax, index_table[0]), value
            )
            cmds.connectAttr(
                '%s.o%s%s' % (pair_blend, pbattr, ax), attr
            )

    tr_pb, s_pb = '', ''
    result = []
    if not skipTranslate:
        tr_pb = createUtil('pairBlend')
        connectOrSetAttr(node, 't', tr_pb, 't')
        result.append(tr_pb)
    if not skipRotate:
        if not tr_pb:
            tr_pb = createUtil('pairBlend')
            result.append(tr_pb)
        connectOrSetAttr(node, 'r', tr_pb, 'r')
        cmds.setAttr('%s.rotInterpolation' % tr_pb, blendMode)
    if not skipScale:
        s_pb = createUtil('pairBlend')
        result.append(s_pb)
        connectOrSetAttr(node, 's', s_pb, 't')

    if blendControlAttr:
        for r in result:
            cmds.connectAttr(blendControlAttr, r + '.weight')

    return result


def fixConstraint(constraintCommand, *node, **keywords):
    r"""
        コンストレイン実行後、ワールド空間との接続を切る。
        
        Args:
            constraintCommand (function):cmds.parentConstraintなど
            *node (tuple):
            **keywords (dict):
            
        Returns:
            node.Constraint:
    """
    cnst = asObject(constraintCommand(*node, **keywords)[0])
    target_attr = cmds.listAttr(
        '%s.target[*].targetParentMatrix' % cnst,  m=True
    )
    target_attr.append('constraintParentInverseMatrix')
    for attr in target_attr:
        matrix = cnst(attr)
        cnst.attr(attr).disconnect(True)
        cnst(attr, matrix, type='matrix')
    return cnst


def localConstraint(constraintCommand, *node, **keywords):
    r"""
        ローカル空間でのコンストレインを行うためのメソッド。
        特殊引数としてparentsとtargetParentsがある。
        parentsはコンストレインする側の親ノードの行列を定義するリストを渡し、
        targetParentsはコンストレインされる側の親ノードの逆行列を定義する
        リストを渡す。
        
        Args:
            constraintCommand (function):cmds.parentConstraintなど
            *node (tuple):
            **keywords (dict):
            
        Returns:
            node.Transform:
    """
    # Analyzes a keywords.-----------------------------------------------------
    parents = []
    targetParents = []
    if 'parents' in keywords:
        parents = keywords.pop('parents')
    if 'targetParents' in keywords:
        targetParents = keywords.pop('targetParents')
    # -------------------------------------------------------------------------

    cnst = fixConstraint(constraintCommand, *node, **keywords)

    if parents:
        tpm = cmds.listAttr(
            cnst + '.target[*].targetParentMatrix', m=True
        )
        if len(parents) != len(tpm):
            print('Specified parents : {}'.format(parents))
            print('Constraint target attributes : {}'.format(tpm))
            raise KeyError(
                'Wrong The number of element for the "parents" argument.'
            )
        for parentlist, p_matrix_attr, n in zip(parents, tpm, node[:-1]):
            if not parentlist:
                continue

            num_parents = len(parentlist)
            mltmtx = createUtil('multMatrix')
            for i in range(num_parents):
                cmds.connectAttr(
                    parentlist[i], '%s.matrixIn[%s]' % (mltmtx, i)
                )

            if not parentlist:
                matrix = cmds.getAttr(n + '.parentMatrix')
            else:
                p = parentlist[-1].split('.')[0]
                matrix = cmds.getAttr(p + '.parentMatrix')

            cmds.setAttr(
                '%s.matrixIn[%s]' % (mltmtx, i + 1), matrix, type='matrix'
            )

            cmds.connectAttr(
                mltmtx + '.matrixSum', cnst + '.' + p_matrix_attr, f=True
            )

    if targetParents:
        num_parents = len(targetParents)
        mltmtx = createUtil('multMatrix')
        for i in range(num_parents):
            cmds.connectAttr(
                targetParents[i], '%s.matrixIn[%s]' % (mltmtx, i + 1)
            )
        matrix = cmds.getAttr(
            targetParents[0].split('.')[0] + '.parentInverseMatrix'
        )
        cmds.setAttr(mltmtx + '.matrixIn[0]', matrix, type='matrix')

        cmds.connectAttr(
            mltmtx + '.matrixSum',
            cnst + '.constraintParentInverseMatrix', f=True
        )

    return asObject(cnst)

# =============================================================================
# Stretch system.                                                            ==
# =============================================================================
def createDistanceSystem(
        startName='startPoint', endName='endPoint',
        distanceNodeName='distanceNode',
        startParent=None, endParent=None, distanceNodeParent=None
    ):
    r"""
        長さを図るための仕組みを作成する
        
        Args:
            startName (str):
            endName (str):
            distanceNodeName (str):
            startParent (str):開始ノードの親を指定する
            endParent (str):終了ノードの親を指定する
            distanceNodeParent (str):distantノードの親を指定する
            
        Returns:
            tuple:(開始ノード、終了ノード、distantノード)
    """
    start_node = createNode('transform', n=startName, p=startParent)
    start_loc = createNode('locator', n='%sShape' % start_node, p=start_node)

    end_node = createNode('transform', n=endName, p=endParent)
    end_loc = createNode('locator', n='%sShape' % end_node, p=end_node)

    dist_node = node.createNode(
        'transform', n=distanceNodeName, p=distanceNodeParent
    )
    dist_shape = createUtil('distanceDimShape',
        p=dist_node, n='%sShape' % dist_node
    )

    cmds.connectAttr(
        '%s.worldPosition[0]' % start_loc, '%s.startPoint' % dist_shape
    )
    cmds.connectAttr(
        '%s.worldPosition[0]' % end_loc, '%s.endPoint' % dist_shape
    )

    return (start_node, end_node, dist_node)


def createStretchCalculator(resultNode, distanceAttr, defaultLength):
    r"""
        伸縮率を計算するノードを作成する。
        
        Args:
            resultNode (dict):
            distanceAttr (str):計算基準となる長さを返すアトリビュート
            defaultLength (float):デフォルトの長さ
            
        Returns:
            list:
    """
    cndt_list = []
    for operation in [2, 4, 2]:
        cndt = createUtil('condition')
        cmds.setAttr('%s.operation' % cndt, operation, l=True)
        cmds.setAttr('%s.firstTerm' % cndt, defaultLength)
        cmds.connectAttr(distanceAttr, '%s.secondTerm' % cndt)
        cndt_list.append(cndt)

    cmds.connectAttr(
        cndt_list[0] + '.outColorR', cndt_list[2] + '.colorIfTrueR'
    )
    cmds.connectAttr(
        cndt_list[1] + '.outColorR', cndt_list[2] + '.colorIfFalseR'
    )
    # -------------------------------------------------------------------------

    blend2attrs = []
    mdlist = []
    for cndt in cndt_list[:2]:
        # Create multiplyDivide node to get a stretch ratio.
        md = createUtil('multiplyDivide')
        cmds.setAttr('%s.operation' % md, 2)
        cmds.connectAttr('%s.secondTerm' % cndt, '%s.input1X' % md)
        cmds.connectAttr('%s.firstTerm' % cndt, '%s.input2X' % md)
        mdlist.append(md)

        # Create blendTwoAttr to switch stretch state.
        blend2attr = createUtil('blendTwoAttr')
        cmds.connectAttr('%s.colorIfFalseR' % cndt, '%s.input[0]' % blend2attr)
        cmds.connectAttr('%s.outputX' % md, '%s.input[1]' % blend2attr)
        cmds.connectAttr('%s.output' % blend2attr, '%s.colorIfTrueR' % cndt)
        blend2attrs.append(blend2attr)

    for attr in cmds.listAttr(resultNode, k=True):
        cmds.setAttr('%s.%s' % (resultNode, attr), k=False)

    for attr, keywords, cbKeywords in zip(
        ['stretch', 'shrink', 'volumeScale', 'stretchRatio', 'volumeScaleRatio'],
        [{'min':0, 'max':1}, {'min':0, 'max':1}, {'min':0, 'max':1}, {}, {}],
        [{'k':True}, {'k':True}, {'k':True}, {'cb':True}, {'cb':True}]
    ):
        keywords['ln'] = attr
        keywords['at'] = 'float'
        cmds.addAttr(resultNode, **keywords)
        cmds.setAttr('%s.%s' % (resultNode, attr), **cbKeywords)
    
    for attr, blend2attr in zip(['shrink', 'stretch'], blend2attrs):
        cmds.connectAttr(
            '%s.%s' % (resultNode, attr),
            '%s.attributesBlender' % blend2attr
        )
    cmds.connectAttr(
        '%s.outColorR' % cndt_list[2], '%s.stretchRatio' % resultNode
    )
    
    # Create connections to output inverse scale from the stretch.-------------
    md = createUtil('multiplyDivide')
    cmds.setAttr(md + '.operation', 2)
    cmds.setAttr(md + '.input1X', 1, l=True)
    cmds.connectAttr(
        '%s.outColorR' % cndt_list[2], '%s.input2X' % md
    )
    
    blend2attr = createUtil('blendTwoAttr')
    cmds.setAttr('%s.input[0]' % blend2attr, 1)
    cmds.connectAttr('%s.outputX' % md, '%s.input[1]' % blend2attr)
    cmds.connectAttr(
        '%s.volumeScale' % resultNode, '%s.attributesBlender' % blend2attr
    )
    
    cmds.connectAttr(blend2attr + '.output', resultNode + '.volumeScaleRatio')
    # -------------------------------------------------------------------------
    
    return cndt_list


def createStretchSystem(jointChain, distanceCurve=None):
    r"""
            与えれたジョイントのリストに対してストレッチの仕組みを作成する。
            戻り値には作成されたノードが辞書形式で格納される。
            各ノードには以下のキーでアクセスできる。
                start : 伸縮開始位置を表すノード
                end : 伸縮終了位置を表すノード
                result : ストレッチの結果を返すノード
                dist : 伸縮具合を計測するためのノード
                arcLength : さを計測するためのノード(カーブの場合のみ）
        }
        
        Args:
            jointChain (list):シングルジョイントチェーンのリスト
            distanceCurve (str):伸張の基準となる長さを提供するカーブ
            
        Returns:
            dict:
    """
    jointChain = [verutil.String(x) for x in jointChain]
    start_joint, end_joint = jointChain[0], jointChain[-1]
    joint_length_list = listLength(jointChain)
    default_length = sum(joint_length_list)

    # Create locator and distanceDimShape.-------------------------------------
    start_pos = node.createNode('transform')
    start_loc = node.createNode('locator', p=start_pos)

    end_pos = node.createNode('transform')
    end_loc = node.createNode('locator', p=end_pos)

    result_node = node.createNode('transform')
    dist_node = createUtil('distanceDimShape', p=result_node)
    d_plug = dist_node.addFloatAttr(
        'defaultLength', max=None, default=default_length
    )
    cmds.connectAttr(
        '%s.worldPosition[0]' % start_loc, '%s.startPoint' % dist_node
    )
    cmds.connectAttr(
        '%s.worldPosition[0]' % end_loc, '%s.endPoint' % dist_node
    )
    # Match positon to locators from specified joint by arguments.
    for loc, joint in zip([start_pos, end_pos], [start_joint, end_joint]):
        pos = cmds.xform(joint, q=True, ws=True, rp=True)
        pos.append(loc)
        cmds.move(*pos, rpr=True)
    # -------------------------------------------------------------------------

    cndt_list = createStretchCalculator(
        result_node, dist_node + '.distance', default_length
    )
    d_plug >> cndt_list[1]/'firstTerm'
    result = {
        'start':start_pos, 'end':end_pos, 'result':result_node,
        'dist' : dist_node, 'arcLength' : None
    }

    if distanceCurve:
        arc = cmds.arcLengthDimension(
            '%s.u[%s]' % (
                distanceCurve, cmds.getAttr(distanceCurve + '.spans')
            )
        )
        for plug in cmds.listConnections(
            dist_node + '.distance', d=True, s=False, p=True
        ):
            cmds.connectAttr(arc + '.arcLength', plug, f=True)
        result['arcLength'] = arc

    return result


def createTranslationStretchSystem(
        startJoint, endJoint, scaleAttr='translateX', distanceCurve=None,
        makeScaleConnection=True
    ):
    r"""
        Translateによってストレッチするシステムを作成する関数。
        
        Args:
            startJoint (str):開始ジョイント
            endJoint (str):末端ジョイント
            scaleAttr (str):スケール対象アトリビュート
            distanceCurve (str):距離を図る基準となるカーブ名。
            makeScaleConnection (bool):
            
        Returns:
            str:伸縮結果を返すノード
    """
    s_a = 's' + scaleAttr[-1].lower()
    scale_attr_sn = TranslateAttrShortName.get(s_a, s_a)
    other_scale_attrs = []
    for sa in ScaleAttr:
        if sa == scale_attr_sn:
            continue
        other_scale_attrs.append(sa)
    if len(other_scale_attrs) != 2:
        raise RunTimeError(
            'Scale Attr is invalid. Must be a following attribute : '
            'sx, sy and sz.'
        )

    joint_chain = listNodeChain(startJoint, endJoint)
    result = createStretchSystem(joint_chain, distanceCurve)
    result_node = result['result']

    for joint in joint_chain[1:]:
        mdl = createUtil('multDoubleLinear')
        mdl('input1', joint(scaleAttr))
        result_node/'stretchRatio' >> mdl.attr('input2')
        mdl.attr('output') >> joint/scaleAttr
        
        if makeScaleConnection:
            result_node.attr('volumeScaleRatio') >> [
                joint/x for x in other_scale_attrs
            ]

    return result


def createScaleStretchSystem(
        startJoint, endJoint, scaleAttr='scaleX', distanceCurve=None
    ):
    r"""
        Scaleによってストレッチするシステムを作成する関数。
        
        Args:
            startJoint (str):開始ジョイント
            endJoint (str):末端ジョイント
            scaleAttr (str):スケール対象となるアトリビュート
            distanceCurve (str):距離を図る基準となるカーブ名。
            
        Returns:
            str:伸縮結果を返すノード
    """
    scale_attr_sn = ScaleAttrShortName.get(scaleAttr, scaleAttr)
    other_scale_attrs = []
    for sa in ScaleAttr:
        if sa == scale_attr_sn:
            continue
        other_scale_attrs.append(sa)
    if len(other_scale_attrs) != 2:
        raise RunTimeError(
            'Scale Attr is invalid. Must be a following attribute : '
            'sx, sy and sz.'
        )

    joint_chain = listNodeChain(startJoint, endJoint)
    result = createStretchSystem(joint_chain, distanceCurve)
    result_node = result['result']

    for joint in joint_chain[:-1]:
        cmds.connectAttr(
            '%s.stretchRatio' % result_node,
            '%s.%s' % (joint, scale_attr_sn)
        )
        for sa in other_scale_attrs:
            cmds.connectAttr(
                '%s.volumeScaleRatio' % result_node, '%s.%s' % (joint, sa)
            )
    return result
# =============================================================================
#                                                                            ==
# =============================================================================


def createTranslateConnection(srcNodeAttr, matrixAttrList, dstNodeAttr=None):
    r"""
        任意のノードの3チャンネルアトリビュートを、pointMatrixMultを経由して
        ターゲットの任意のアトリビュートへ接続する関数。
        
        Args:
            srcNodeAttr (str):ソースとなる3チャンネルアトリビュート
            matrixAttrList (list):座標変換するための行列リスト
            dstNodeAttr (str):
            
        Returns:
            list:[pointMatrixMult, multMatrix]または None
    """
    num_matrix = len(matrixAttrList)
    if num_matrix == 0:
        if dstNodeAttr:
            connect3ChannelAttr(srcNodeAttr, dstNodeAttr, ignoreKeyable=True)
        return

    pmm = createUtil('pointMatrixMult')
    if srcNodeAttr:
        connect3ChannelAttr(srcNodeAttr, (pmm + '.ip'), ignoreKeyable=True)
    result = []
    if num_matrix > 1:
        mltmtx = createUtil('multMatrix')
        index = 0
        for attr in matrixAttrList:
            cmds.connectAttr(attr, '%s.matrixIn[%s]' % (mltmtx, index))
            index += 1
        cmds.connectAttr('%s.matrixSum' % mltmtx, '%s.inMatrix' % pmm)
        result = [pmm, mltmtx]
    else:
        cmds.connectAttr(matrixAttrList[0], '%s.inMatrix' % pmm)
        result = [pmm]

    if dstNodeAttr:
        connect3ChannelAttr('%s.o' % pmm, dstNodeAttr, ignoreKeyable=True)
    return result



def createBendTwistControl(
        startProxy, endProxy, startJoint, endJoint,
        baseAxisNode, fromStartToEnd=True, aimVector=[1, 0, 0]
    ):
    r"""
        startProxy～endProxy間のジョイントでベンドとツイストのシステムを作成する
        戻り値には作成されたノードが辞書形式で格納される。
        各ノードには以下のキーでアクセスできる。
            root : 捻りや曲げの制御を行うサーフェース名
            topCtrlSpace : 根本の位置制御を行うコントローラースペース名
            midCtrlSpace : 中間の位置制御を行うコントローラースペース名
            btmCtrlSpace : 末端の位置制御を行うコントローラースペース名
            topCtrl : 根本の位置制御を行うコントローラー名
            midCtrl : 中間の位置制御を行うコントローラー名
            btmCtrl : 末端の位置制御を行うコントローラー名
            scaleInfo : スケール情報を返すノード。rootと同じ
        
        Args:
            startProxy (str):開始位置となる代理ジョイント
            endProxy (str):末端となる代理ジョイント
            startJoint (str):開始ジョイント
            endJoint (str):末端ジョイント
            baseAxisNode (str):
            fromStartToEnd (bool):開始から末端へと作成するかどうか
            aimVector (list):子の方向をむくベクトル
            
        Returns:
            dict:作成されたノードを格納する辞書オブジェクト
    """
    result = {}
    startProxy, endProxy = node.toObjects((startProxy, endProxy))
    if fromStartToEnd:
        rotationBaseNode = startProxy
    else:
        rotationBaseNode = endProxy
    
    joint_chains = listNodeChain(startJoint, endJoint)

    start_position = joint_chains[0].position()
    end_position = joint_chains[-1].position()
    mid_position = [
        (x + y)  * 0.5 for x, y in zip(start_position, end_position)
    ]

    # 開始ジョイントのX軸が子を向いているかどうかによってfactorの値を決定する。
    factor = -1 if joint_chains[0].isOpposite() else 1
    start_vector = mathlib.Vector(start_position)

    # カーブの位置情報を作成する。=============================================
    crv_length = (
        mathlib.Vector(end_position) - start_vector
    ).length()
    y_vector = mathlib.Vector(
        cmds.xform(joint_chains[0], q=True, ws=True, m=True)[4:7]
    )
    y_vector.normalize()
    y_length = crv_length * (1.0 / len(joint_chains))
    move_yA = y_vector * y_length
    move_yB = y_vector * -y_length
    # =========================================================================
    
    # スパン２の制御用コントロールカーブを作成する。===========================
    rootA = cmds.curve(d=2, p=[start_position, mid_position, end_position])
    rootA = cmds.parent(rootA, startProxy)[0]
    rootB = cmds.duplicate(rootA)[0]
    
    cmds.move(move_yA.x, move_yA.y, move_yA.z, rootA, ws=True, r=True)
    cmds.move(move_yB.x, move_yB.y, move_yB.z, rootB, ws=True, r=True)

    base_surf = asObject(
        cmds.parent(
            cmds.loft(
                rootA, rootB,
                ch=0, u=1, c=0, ar=1, d=1, ss=0, rn=0, po=0, rsn=True
            ),
            startProxy
        )[0]
    )
    base_surf.freeze().reset()
    cmds.delete(rootA, rootB)

    cmds.rebuildSurface(
        base_surf,
        ch=0, rpo=1, rt=1, end=1, kr=0, kcp=0, kc=0, su=4,
        du=3, sv=4, dv=3, tol=0.01, fr=0, dir=2
    )
    
    arc_len = node.createNode('arcLengthDimension', p=base_surf)
    base_surf/'worldSpace' >> arc_len.attr('nurbsGeometry')
    arc_len('uParamValue', 1)
    arc_len('vParamValue', 0.5)

    createStretchCalculator(
        base_surf, arc_len + '.arcLength',
        cmds.getAttr(arc_len + '.arcLength')
    )
    # =========================================================================

    # 代理コントローラを作成し、カーブポイントに接続する。=====================
    control_proxies = []
    space_proxies = []
    for suffix, position, parent in zip(
            ['Start', 'Middle', 'End'],
            [start_position, mid_position, end_position],
            [base_surf, base_surf, endProxy]
        ):
        space = createSpaceNode(p=parent)
        startProxy.attr('scale') >> space/'inverseScale'
        ctrl = node.createNode('transform', p=space)

        space.setPosition(position)
        control_proxies.append(ctrl)
        space_proxies.append(space)

    for i in range(3):
        for j in range(2):
            matrix_list = [
                x + '.matrix' for x in
                (control_proxies[i], space_proxies[i])
            ]
            cv = '%s.cv[%s][%s]' % (base_surf, i, j)
            pos = cmds.pointPosition(cv, w=True)
            tmp_null = node.createNode('transform', p=control_proxies[i])
            tmp_null.setPosition(pos)
            pos = tmp_null('t')[0]
            tmp_null.delete()

            if i == 2:
                matrix_list.extend(
                    ['%s.matrix' % endProxy, '%s.inverseMatrix' % base_surf]
                )

            tcn = createTranslateConnection(
                None, matrix_list, cv + '.%sValue'
            )
            cmds.setAttr(tcn[0] + '.ip', *pos)

    # 中間のベンドコントローラの配置。-----------------------------------------
    cst = node.asObject(
        cmds.pointConstraint(
            space_proxies[0], space_proxies[2], space_proxies[1],
        )[0]
    )
    for attr in (
        'target[0].targetParentMatrix', 'constraintParentInverseMatrix'
    ):
        cst.attr(attr).disconnect(False)
        cst(attr, node.identityMatrix(), type='matrix')
    mltmtx = createUtil('multMatrix')
    space_proxies[2].parent().attr('matrix') >> mltmtx/'matrixIn[0]'
    base_surf.attr('inverseMatrix') >> mltmtx/'matrixIn[1]'
    mltmtx.attr('matrixSum') >> cst/'target[1].targetParentMatrix'
    # -------------------------------------------------------------------------

    lockTransform(space_proxies)
    # =========================================================================

    # =========================================================================
    cps = node.createNode('closestPointOnSurface')
    base_surf/'worldSpace' >> cps.attr('inputSurface')

    completed_joint_chains = []
    root_matrix = joint_chains[0]('matrix')
    
    proxy_parents, joint_parents = listCommonParentPathList(
        startProxy, startJoint
    )
    parent_matrix_node = None
    if len(proxy_parents) != 1 or len(joint_parents) != 1:
        joint_parents.reverse()
        index = 0
        parent_matrix_node = createUtil('multMatrix')
        for parent in proxy_parents[:-1]:
            cmds.connectAttr(
                '%s.matrix' % parent,
                '%s.matrixIn[%s]' % (parent_matrix_node, index)
            )
            index += 1

        for parent in joint_parents[1:]:
            cmds.connectAttr(
                '%s.inverseMatrix' % parent,
                '%s.matrixIn[%s]' % (parent_matrix_node, index)
            )
            index +=1

    for joint in joint_chains:
        world_position = cmds.xform(joint, q=True, ws=True, rp=True)
        cmds.setAttr('%s.inPosition' % cps, *world_position)
        parameter_u = cmds.getAttr('%s.parameterU' % cps)
        parameter_v = cmds.getAttr('%s.parameterV' % cps)

        psi = createUtil('pointOnSurfaceInfo')
        cmds.connectAttr('%s.local' % base_surf, '%s.inputSurface' % psi)
        cmds.setAttr('%s.parameterU' % psi, parameter_u)
        cmds.setAttr('%s.parameterV' % psi, parameter_v)

        # カーブ上のpositionアトリビュートをジョイントチェインへ繋ぐ。
        matrix_list = ['%s.matrix' % startProxy]
        if parent_matrix_node:
            matrix_list.append('%s.matrixSum' % parent_matrix_node)
        matrix_list.extend(
            ['%s.inverseMatrix' % x[0] for x in completed_joint_chains]
        )
        matrix_nodes = createTranslateConnection(
            '%s.p' % psi, matrix_list, '%s.t' % joint
        )

        completed_joint_chains.append(
            (
                joint, psi,
                (
                    startProxy + '.matrix' if len(matrix_nodes) == 1
                    else matrix_nodes[-1] + '.matrixSum'
                )
            )
        )
    # =========================================================================

    # 回転制御の作成、およびスケールアトリビュートの接続を行う。===============
    base_surf('stretch', 1)
    base_surf('shrink', 1)
    base_surf_volume_attr = base_surf.attr('volumeScaleRatio')
    y_moved_matrix = node.MMatrix(
        [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, y_length, 0, 1]
    )
    for i in range(len(completed_joint_chains)-1):
        joint = completed_joint_chains[i][0]
        psi = completed_joint_chains[i][1]
        child_joint = completed_joint_chains[i+1][0]
        child_psi = completed_joint_chains[i+1][1]
        invmtx_plug = completed_joint_chains[i][2]

        fbfmtx = createUtil('fourByFourMatrix')
        rot_mtx = [0] * 16
        for i, attr in enumerate(('tu', 'tv', 'n', 'p')):
            for j, axis in enumerate(('x', 'y', 'z')):
                psi.attr(attr+axis) >> fbfmtx/('in%s%s' % (i, j))
                if i < 3:
                    rot_mtx[j+i*4] = psi(attr+axis)
        rot_mtx = node.MMatrix(rot_mtx)
        inv_rot_mtx = rot_mtx.inverse()
        y_matrix = y_moved_matrix * inv_rot_mtx

        mltmtx = createUtil('multMatrix')
        mltmtx('matrixIn[0]', y_matrix, type='matrix')
        fbfmtx.attr('output') >> mltmtx/'matrixIn[1]'
        base_surf.attr('worldMatrix') >> mltmtx/'matrixIn[2]'

        # コンストレイン設定。-------------------------------------------------
        aim_cst = node.createNode('aimConstraint', p=base_surf)
        aim_cst('aimVector', (factor, 0, 0))
        aim_cst('upVector', (0, 1, 0))
        base_surf.attr('worldMatrix') >> aim_cst/'target[0].targetParentMatrix'
        child_psi.attr('p') >> aim_cst/'target[0].targetTranslate'

        aim_cst('worldUpType', 1)
        mltmtx.attr('matrixSum') >> aim_cst/'worldUpMatrix'

        ~aim_cst.attr('constraintRotate') >> ~joint.attr('r')
        joint.attr('pim') >> aim_cst/'constraintParentInverseMatrix'
        joint.attr('inverseScale') >> aim_cst/'inverseScale'
        joint.attr('jo') >> aim_cst/'constraintJointOrient'
        joint.attr('t') >> aim_cst/'constraintTranslate'
        joint.attr('rotateOrder') >> aim_cst/'constraintRotateOrder'
        # ---------------------------------------------------------------------

        # スケールの接続。
        md = createUtil('multiplyDivide')
        for axis in Axis:
            start_attr = startProxy.attr('s'+axis)
            joint_attr = joint.attr('s'+axis)
            if axis != 'x':
                start_attr >> md.attr('i1'+axis)
                base_surf_volume_attr >> md.attr('i2'+axis)
                md.attr('o'+axis) >> joint_attr
            else:
                start_attr >> joint_attr
    # =========================================================================
    cmds.delete(cps)

    result['root'] = base_surf
    result['topCtrlSpace'] = space_proxies[0]
    result['midCtrlSpace'] = space_proxies[1]
    result['btmCtrlSpace'] = space_proxies[2]
    result['topCtrl'] = control_proxies[0]
    result['midCtrl'] = control_proxies[1]
    result['btmCtrl'] = control_proxies[2]
    result['scaleInfo'] = base_surf
    return result
    

def createBendControl(
        startProxy, endProxy, startJoint, endJoint,
        baseAxisNode, fromStartToEnd=True, aimVector=[1, 0, 0]
    ):
    r"""
        startJointとendJoint間をベンドするコントローラを作成する。
        endJointはstartJointの子である必要がある。
        戻り値には作成されたノードが辞書形式で格納される。
        各ノードには以下のキーでアクセスできる。
            root : 捻りや曲げの制御を行うサーフェース名
            topCtrlSpace : 根本の位置制御を行うコントローラースペース名
            midCtrlSpace : 中間の位置制御を行うコントローラースペース名
            btmCtrlSpace : 末端の位置制御を行うコントローラースペース名
            topCtrl : 根本の位置制御を行うコントローラー名
            midCtrl : 中間の位置制御を行うコントローラー名
            btmCtrl : 末端の位置制御を行うコントローラー名
        
        Args:
            startProxy (any):[edit]
            endProxy (any):[edit]
            startJoint (str):開始ジョイント
            endJoint (str):終了ジョイント
            baseAxisNode (str):
            fromStartToEnd (bool):
            aimVector (list):ジョイントを向ける向き
            
        Returns:
            dict:作成されたノードを格納する辞書オブジェクト
    """
    result = {}
    if fromStartToEnd:
        rotationBaseNode = startProxy
    else:
        rotationBaseNode = endProxy
    
    joint_chains = listNodeChain(startJoint, endJoint)
    start_position = cmds.xform(joint_chains[0], q=True, ws=True, rp=True)
    end_position = cmds.xform(joint_chains[-1], q=True, ws=True, rp=True)
    mid_position = [
        (x + y)  * 0.5 for x, y in zip(start_position, end_position)
    ]
    
    # Create control curve that a span of is 2.
    root = cmds.curve(d=2, p=[start_position, mid_position, end_position])
    root = cmds.parent(root, startProxy)[0]
    cmds.makeIdentity(root, a=True, t=True, r=True, s=True)
    cmds.xform(root, os=True, piv=[0,0,0])

    # Create controller proxies and connects to curve points.------------------
    control_proxies = []
    space_proxies = []
    for suffix, position, parent in zip(
            ['Start', 'Middle', 'End'],
            [start_position, mid_position, end_position],
            [root, root, endProxy]
        ):
        space = node.createNode('transform', p=parent)
        ctrl = node.createNode('transform', p=space)
        
        cmds.move(position[0], position[1], position[2], space, rpr=True)
        control_proxies.append(ctrl)
        space_proxies.append(space)

    for i in range(3):
        matrix_list = [space_proxies[i]+'.matrix']
        if i == 2:
            matrix_list.extend(
                ['%s.matrix' % endProxy, '%s.inverseMatrix' % root]
            )

        createTranslateConnection(
            '%s.t' % control_proxies[i], matrix_list,
            ('%s.cp[%s].%%sValue' % (root, i))
        )

    cmds.pointConstraint(space_proxies[0], space_proxies[2], space_proxies[1])
    lockTransform(space_proxies)
    # -------------------------------------------------------------------------


    # -------------------------------------------------------------------------
    npc = node.createNode('nearestPointOnCurve')
    cmds.connectAttr('%s.worldSpace' % root, '%s.inputCurve' % npc)

    completed_joint_chains = []
    root_matrix = cmds.getAttr('%s.matrix' % joint_chains[0])
    
    proxy_parents, joint_parents = listCommonParentPathList(
        startProxy, startJoint
    )
    parent_matrix_node = None
    if len(proxy_parents) != 1 or len(joint_parents) != 1:
        joint_parents.reverse()
        index = 0
        parent_matrix_node = createUtil('multMatrix')
        for parent in proxy_parents[:-1]:
            cmds.connectAttr(
                '%s.matrix' % parent,
                '%s.matrixIn[%s]' % (parent_matrix_node, index)
            )
            index += 1

        for parent in joint_parents[1:]:
            cmds.connectAttr(
                '%s.inverseMatrix' % parent,
                '%s.matrixIn[%s]' % (parent_matrix_node, index)
            )
            index +=1

    for joint in joint_chains:
        world_position = cmds.xform(joint, q=True, ws=True, rp=True)
        cmds.setAttr('%s.inPosition' % npc, *world_position)
        parameter = cmds.getAttr('%s.parameter' % npc)

        ppi = createUtil('pointOnCurveInfo')
        cmds.connectAttr('%s.local' % root, '%s.inputCurve' % ppi)
        cmds.setAttr('%s.parameter' % ppi, parameter)

        # Connect position attribute on the curve to the joint chain.
        matrix_list = ['%s.matrix' % startProxy]
        if parent_matrix_node:
            matrix_list.append('%s.matrixSum' % parent_matrix_node)
        matrix_list.extend(
            ['%s.inverseMatrix' % x for x in completed_joint_chains]
        )
        matrix_nodes = createTranslateConnection(
            '%s.p' % ppi, matrix_list, '%s.t' % joint
        )
        # --
        completed_joint_chains.append(joint)
    # -------------------------------------------------------------------------


    # Make a rotation system and scale attribute connections.------------------
    factor = 1.0 / (len(joint_chains))
    base_factor = factor
    parent = root
    for joint in joint_chains[:-1]:
        orientation_base = node.createNode('transform', p=parent)
        cnst = cmds.orientConstraint(
            rotationBaseNode, baseAxisNode, orientation_base,
            skip=['y', 'z']
        )[0]
        cmds.setAttr('%s.interpType' % cnst, 2)
        attrs = cmds.orientConstraint(cnst, q=True, wal=True)
        cmds.setAttr('%s.%s' % (cnst, attrs[0]), factor)
        cmds.setAttr('%s.%s' % (cnst, attrs[1]), 1 - factor)
        lockTransform([orientation_base])

        cmds.tangentConstraint(
            root, joint,
            w=1, aimVector=aimVector, upVector=[0, 1, 0],
            worldUpType='objectrotation', wuo=orientation_base
        )[0]
        
        # Make scale connection.
        connect3ChannelAttr('%s.s' % startProxy, '%s.s' % joint)
        
        factor += base_factor
    # -------------------------------------------------------------------------

    cmds.delete(npc)

    result['root'] = root
    result['topCtrlSpace'] = space_proxies[0]
    result['midCtrlSpace'] = space_proxies[1]
    result['btmCtrlSpace'] = space_proxies[2]
    result['topCtrl'] = control_proxies[0]
    result['midCtrl'] = control_proxies[1]
    result['btmCtrl'] = control_proxies[2]

    return result
    
    
def createNonTwistedBender(startJoint, endJoint):
    r"""
        createBendControlで作成されたベンド機構からツイスト動作を抜いた状態の
        ジョイントを作成する。
        
        Args:
            startJoint (str):開始ジョイント
            endJoint (str):終端ジョイント
            
        Returns:
            list:作成されたノードのリスト
    """
    chains = listNodeChain(startJoint, endJoint)
    parent = chains[0].parent()
    results = []
    num = len(chains)
    idt_mtx = node.identityMatrix()
    rot_matrix = chains[0].matrix(world=False)
    for i in range(num):
        name = Name(chains[i])
        
        name.setSuffix('NnTwst')
        copied = node.rename(copyNode(chains[i], parent=parent), name())
        if copied.isType('joint'):
            copied('radius', copied('radius')*1.25)
        results.append(copied)
        parent = copied

        ~chains[i].attr('t') >> ~copied.attr('t')
        ~chains[i].attr('s') >> ~copied.attr('s')
        if i == num-1:
            if chains[i].hasChild():
                target = chains[i].children()[0]
            else:
                continue
        else:
            target = chains[i+1]
        cst = localConstraint(
            cmds.aimConstraint, target, copied,
            aimVector=(-1 if chains[i].isOpposite() else 1, 0, 0),
            upVector=(0, 0, 1)
        )
        cst('worldUpType', 2)
        cst('worldUpVector', (0, 0, 1))
        cst('target[0].targetParentMatrix', idt_mtx, type='matrix')
        cst('constraintParentInverseMatrix', idt_mtx, type='matrix')
        chains[0].attr('matrix') >> cst/'worldUpMatrix'
        # matrixの設定。=======================================================
        # parentMatrixの設定。
        if i > 0:
            parent_mtx = node.createUtil('multMatrix')
            for j, n in enumerate(reversed(chains[:i+1])):
                n.attr('matrix') >> parent_mtx.attr('matrixIn[%s]' % j)
            parent_plug = parent_mtx.attr('matrixSum')
        else:
            parent_plug = chains[0].attr('matrix')
        parent_plug >> cst/'target[0].targetParentMatrix'

        # inverseMatrixの設定
        if i == 0:
            continue
        elif i == 1:
            parent_plug = results[0].attr('inverseMatrix')
        else:
            parent_mtx = node.createUtil('multMatrix')
            for j, n in enumerate(results[:-1]):
                n.attr('inverseMatrix') >> parent_mtx.attr('matrixIn[%s]' % j)
            parent_plug = parent_mtx.attr('matrixSum')
        parent_plug >> cst/'constraintParentInverseMatrix'
        # =====================================================================
    return results


def createFkController(
        target, parent=None, name='fk_ctrl#', spaceName='fk_ctrlSpace#',
        spaceType='joint',
        skipTranslate=True, skipRotate=False, skipScale=False,
        isLockTransform=True, calculateWithSpace=False
    ):
    r"""
        targetを制御するFKコントローラを作成する。
        
        Args:
            target (str):
            parent (str):コントローラを作成する親ノード
            name (str):コントローラの名前
            spaceName (str):スペーサーの名前
            spaceType (str):jointの場合inverseScaleの接続も行う
            skipTranslate (bool):translateの接続をスキップする
            skipRotate (bool):rotateの接続をスキップする
            skipScale (bool):scaleの接続をスキップする
            isLockTransform (bool):スペーサーをロックするかどうか
            calculateWithSpace (bool):
            
        Returns:
            list:[コントローラー,スペーサーノード]
    """
    target = asObject(target)
    space = createSpaceNode(n=spaceName, p=parent)
    ctrl = node.createNode('transform', n=name, p=space)
    cmds.setAttr('%s.v' % ctrl, k=False)
    space.fitTo(target)
    if target.type() == spaceType == 'joint':
        space.setInverseScale(False)
        space('ssc', target('ssc'))

    if not skipTranslate:
        pmm = createUtil('pointMatrixMult')
        cmds.connectAttr('%s.matrix' % space, '%s.inMatrix' % pmm)
        connect3ChannelAttr('%s.t' % ctrl, '%s.ip' % pmm, ignoreKeyable=True)
        connect3ChannelAttr('%s.o' % pmm, '%s.t' % target)

    if not skipRotate:
        if calculateWithSpace:
            localConstraint(
                cmds.orientConstraint, ctrl, target,
                parents=[[space + '.matrix']]
            )
        else:
            connect3ChannelAttr('%s.r' % ctrl, '%s.r' % target)

    if not skipScale:
        connect3ChannelAttr('%s.s' % ctrl, '%s.s' % target)

    if isLockTransform:
        space.lockTransform()
    return [ctrl, space]


def connectMcpBakeToCtrl(srcNode, dstNode):
    r"""
        srcNodeからdstNodeへmcpBake用の関係を表すmessageコネクションを作成する。
        
        Args:
            srcNode (str):
            dstNode (str):
    """
    cmds.addAttr(dstNode, ln='mcpBakeSourceNode', at='message')
    cmds.connectAttr('%s.message' % srcNode, '%s.mcpBakeSourceNode' % dstNode)


def createSculptDeformer(
        targetShapes, name='sculpt', position=None, parent=None
    ):
    r"""
        スカルプトでフォーマーを追加する。
        
        Args:
            targetShapes (str):
            name (str):
            position (str):
            parent (str):
            
        Returns:
            list:作成されたノードのリスト
    """
    basename = Name()
    basename.setName(name)
    basename.setPosition(position)
    basename.setNodeType('trs')

    # Create sculpt deformer and rename it.------------------------------------
    sculpts = cmds.sculpt(
        targetShapes,
        mode='flip', insideMode='even', maxDisplacement=0.1,
        dropoffType='linear', dropoffDistance=0.1, groupWithLocator=0,
        objectCentered=0
    )
    sculpts[1] = cmds.rename(sculpts[1], basename())

    basename.setNodeType('sclpt')
    sculpts[0] = node.rename(sculpts[0], basename())

    basename.setNodeType('sctPos')
    sculpts[2] = cmds.rename(sculpts[2], basename())
    # -------------------------------------------------------------------------

    # Creates group for it.----------------------------------------------------
    basename.setNodeType('grp')
    group = node.createNode('transform', n=basename(), p=parent)
    sculpts[1], sculpts[2] = node.parent(sculpts[1], sculpts[2], group)
    cmds.makeIdentity(sculpts[1], sculpts[2], t=True, r=True, s=True)
    # -------------------------------------------------------------------------

    return [group, sculpts[0], sculpts[1], sculpts[2]]


def createAngleDriverNode(targetNode, name='angleDriver#', parent=None):
    r"""
        ベクトルベースの角度を返すangleDriverノードを作成する
        
        Args:
            targetNode (str):角度参照ノード
            name (str):作成されるノードの名前
            parent (str):ノードを配置する親ノード
            
        Returns:
            node.Transform:
    """
    from gris3.tools import drivers
    return drivers.createAngleDriver(targetNode, name, parent)


def createDistanceDriverNode(
    startNode, endNode, name='distanceDriver#', parent=None
):
    r"""
        ２つのマトリクス間の距離ベースの伸縮率を返すdistanceDriverノードを
        作成する。
        
        Args:
            startNode (str):
            endNode (str):
            name (str):
            parent (str):
            
        Returns:
            node.Transform:
    """
    from gris3.tools import drivers
    inputs = [
        x if '.' in x else x+'.worldMatrix' for x in (startNode, endNode)
    ]
    return drivers.createDistanceDriver(inputs[0], inputs[1], name, parent)


class SurfaceFitter(object):
    r"""
        登録サーフェイスまたはメッシュにオブジェクトを貼り付ける機能を
        提供するクラス。
        meshとnurbsSurfaceのみサポート。
    """
    SupportedTypes = ('mesh', 'nurbsSurface')
    def __init__(self, surface=None, createOffset=True):
        r"""
            Args:
                surface (str):
                createOffset (bool):Fit時にオフセットを作るかどうか
        """
        self.setSurface(surface)
        self.setCreatingOffset(createOffset)

    def setSurface(self, surface):
        r"""
            メッシュまたはサーフェースをセットする。
            
            Args:
                surface (str):
        """
        self.__surface = ''
        if surface is None:
            return
        surface = asObject(surface)
        if surface.isType(('transform', 'joint')):
            shapes = surface.shapes(typ=self.SupportedTypes)
            if shapes:
                surface = shapes[0]
        if not surface.isType(('mesh', 'nurbsSurface')):
            raise ValueError(
                (
                    'The specified node "%s" is not supoorted.'
                    'Set only a following types : %s'
                ) % (surface, self.SupportedTypes)
            )
        self.__surface = surface

    def surface(self):
        r"""
            セットされているメッシュまたはサーフェースを返す。
            
            Returns:
                (node.Mesh or gris3.node.NurbsSurface):
        """
        return self.__surface

    def setCreatingOffset(self, state):
        r"""
            オフセットを作成するかどうかを指定する。
            
            Args:
                state (bool):
        """
        self.__creating_offset = bool(state)

    def isCreatingOffset(self):
        r"""
            オフセットを作成するかどうかを返す。
            
            Returns:
                bool:
        """
        return self.__creating_offset

    def fit(self, nodes, flags=0b11):
        r"""
            与えらたノードをセットされているサーフェイスに固定する。
            flags:はtranslate、rotateを接続するかどうかのビットフラグで
            左からtranslate、rotateのフラグになっている。
            
            戻り値にはフィットしたノードのリストを返す。
            リストの中には[操作対象ノード、オフセットノード]が引数nodesの数だけ
            入る。
            
            Args:
                nodes (list):固定されるノードのリスト
                flags (bin):ビットフラグ（translate, rotate)
                
            Returns:
                list:
        """
        result = []
        surface = self.surface()
        if not surface:
            raise RuntimeError('No surface was not specified to fit.')

        if surface.isType('mesh'):
            outplug = surface.attr('outMesh')
            inplug = 'inputMesh'
        else:
            outplug = surface.attr('local')
            inplug = 'inputSurface'

        creating_offset = self.isCreatingOffset()
        connect_t, connect_r = flags & 0b10, flags & 0b01
        for n in toObjects(nodes):
            u, v = surface.closestUV(n.position())
            
            # オフセットノードの作成。=========================================
            if creating_offset:
                target = node.createNode(
                    'transform', n='offset_%s' % n,
                    p=n.parent() if n.hasParent() else None
                )
            else:
                target = n
            # =================================================================

            # サーフェイスに固定するためのfollicleを作成する。=================
            follicle = createUtil('follicle', p=target, n='%sShape' % target)
            follicle('v', 0)
            target.attr('parentInverseMatrix') >> follicle/'inputWorldMatrix'
            outplug >> follicle/inplug
            follicle('parameterU', u)
            follicle('parameterV', v)
            # =================================================================

            # follicleをターゲットに接続。=====================================
            if connect_t:
                ~follicle.attr('ot') >> ~target.attr('t')
            if connect_r:
                ~follicle.attr('or') >> ~target.attr('r')
            # =================================================================

            if creating_offset:
                n = asObject(cmds.parent(n, target)[0])
                result.append((n, target))
            else:
                result.append((n,))
        return result


def wrap(targets, cage):
    r"""
        exclusiveBindがOnなWrapを実行する。
        戻り値として、wrapノードのリストを返す。
        
        Args:
            targets (list):ラップされるノードのリスト
            cage (str):ラップするケージ
            
        Returns:
            list:
    """
    cmds.select(targets, cage)
    wrap_nodes = mel.eval(
        'doWrapArgList "7" { "1","0","1", "2", "1", "1", "0", "1" };'
    )
    return wrap_nodes


def localWrap(targets, cage):
    r"""
        ローカライズされたラップを行う。
        wrapノードとベースノードのリストを持つ辞書を返す。
        アクセスするためのキーは以下ｎ通り。
            wrapNode : ラップノードのリスト
            baseNode : ベースノードのリスト
        
        Args:
            targets (list):ラップされるノードのリスト
            cage (str):ラップするケージ
            
        Returns:
            dict:
    """
    supported_nodelist = [
        'mesh', 'nurbsSurface', 'nurbsCurve', 'lattice'
    ]
    local_out_plug = {
        'mesh':'outMesh',
        'nurbsSurface':'local', 'nurbsCurve':'local',
        'lattice': 'latticeOutput'
    }
    world_out_plug = {
        'mesh':'worldMesh',
        'nurbsSurface':'worldSpace', 'nurbsCurve':'worldSpace',
        'lattice': 'worldLattice'
    }
    def findImShape(n):
        r"""
            入力コネクションを辿ってIMノードを探す。
            
            Args:
                n (str):操作対象ノード
                
            Returns:
                tuple:
        """
        node_type = cmds.nodeType(n)
        if node_type in supported_nodelist:
            if cmds.getAttr('%s.io' % n):
                return (
                    n, local_out_plug[node_type], world_out_plug[node_type]
                )
        con = cmds.listConnections(n, s=True, d=False, p=True)
        if not con:
            if node_type in supported_nodelist:
                return (
                    n, local_out_plug[node_type], world_out_plug[node_type]
                )
            return
        con = [
            x for x in con if cmds.getAttr(x, type=True) in supported_nodelist
        ]
        if not con:
            return
        for c in con:
            node_name = c.split('.')[0]
            result = findImShape(node_name)
            if result:
                return result

    wrap_nodes = wrap(targets, cage)
    base_nodes = []
    for wrap_node, node in zip(wrap_nodes, targets):
        # Reconnect outMesh instead of worldMesh.
        for plug in ['basePoints', 'driverPoints']:
            wrap_plug = '{}.{}[0]'.format(wrap_node, plug)
            input = cmds.listConnections(
                wrap_plug, s=True, d=False, sh=True
            )[0]
            cmds.connectAttr(
                '{}.{}'.format(input, local_out_plug[cmds.nodeType(input)]),
                wrap_plug,
                f=True
            )
            if plug == 'basePoints':
                base_nodes.append(input)
        wrap_plug = '{}.geomMatrix'.format(wrap_node)
        shape_plug = cmds.listConnections(
            wrap_plug, s=True, d=False, p=True
        )[0]
        cmds.disconnectAttr(shape_plug, wrap_plug)
        cmds.setAttr(wrap_plug, cmds.getAttr(shape_plug), type='matrix')

        im_start = cmds.listConnections(
            '{}.input[0].inputGeometry'.format(wrap_node),
            s=True, d=False, sh=True
        )
        d = findImShape(im_start[0])
        im, local_plug, world_plug = findImShape(im_start[0])

        out_con = cmds.listConnections(
            '%s.%s' % (im, world_plug), s=False, d=True, p=True
        )
        if not out_con:
            continue
        out_con = out_con[0]
        cmds.disconnectAttr('%s.%s' % (im, world_plug), out_con)
        cmds.connectAttr('%s.%s' % (im, local_plug), out_con)

    return {'wrapNode':wrap_nodes, 'baseNode':base_nodes}


def localizeDeformer(inputPlug, inverseMatrices, withOffset=True):
    r"""
        inputPlugに刺さっているコネクションの間にtransformGeometryを挟み
        inverseMatricesのコネクションによって動きを相殺する。
        
        Args:
            inputPlug (str):
            inverseMatrices (list):
            withOffset (bool):
            
        Returns:
            node.AbstractNode:transformGeometry
    """
    old_input = cmds.listConnections(inputPlug, s=True, d=False, p=True)
    if not old_input:
        return

    mltmtx = createUtil('multMatrix')
    connectMultAttr(inverseMatrices, '%s.matrixIn' % mltmtx)
    mtx_plug = '%s.matrixSum' % mltmtx

    if withOffset:
        input = inputPlug.split('.')[0]
        parent = inverseMatrices[-1].split('.')[0]
        if node.ls(input, shapes=True):
            input = cmds.listRelatives(input, p=True, type='transform')
            if not input:
                return
        dmy = cmds.duplicate(input, po=True)
        unlockTransform(dmy)
        dmy = cmds.parent(dmy, parent)[0]

        inv_mtx = cmds.getAttr('%s.inverseMatrix' % dmy)
        cmds.delete(dmy)
        cmds.setAttr(
            '%s.matrixIn[%s]' % (mltmtx, len(inverseMatrices)), inv_mtx,
            type='matrix'
        )


    trsgeo = createUtil('transformGeometry')
    cmds.connectAttr(mtx_plug, '%s.transform' % trsgeo)
    cmds.connectAttr(old_input[0], '%s.inputGeometry' % trsgeo)
    cmds.connectAttr('%s.outputGeometry' % trsgeo, inputPlug, f=True)

    return trsgeo

    
def createPoleVector(ikHandles=None):
    r"""
        与えられたikHandleに対し、ポールベクターコンストレインを行う。
        この時のコンストレインターゲットは自動で生成され、元のIKの回転方向を
        変更しない位置に作成される。
        
        Args:
            ikHandles (list):IKのリスト
            
        Returns:
            list:(作成されたコンストレインターゲットのノードのリスト）
    """
    result = []
    if not ikHandles:
        ikHandles = node.ls(sl=True, type=['ikHandle'])
    else:
        ikHandles = toObjects(ikHandles)

    for ik_handle in ikHandles:
        parent_mtx = (
            ik_handle.parent().matrix() if ik_handle.hasParent()
            else node.identityMatrix()
        )

        start_joint = ik_handle.attr('startJoint').source()
        if not start_joint:
            continue
        vector = ik_handle('poleVector')[0]
        p_pos = start_joint.position()
        mtx_a = node.identityMatrix()
        for i, j in enumerate((12, 13, 14)):
            mtx_a[j] = vector[i]
            parent_mtx[j] = p_pos[i]
        matrix = node.MMatrix(mtx_a) * node.MMatrix(parent_mtx)
        trs = node.createNode('transform')
        trs.setMatrix(matrix)

        cmds.poleVectorConstraint(trs, ik_handle)
        result.append(trs)

    return result


class SoftModification(object):
    r"""
        softModによるデフォーマーと、それを制御するコントローラを作成する機能を
        提供するクラス。
    """
    VolumeMode, SurfaceMode = range(2)
    Nothing, Linear, Smooth, Sprine = range(4)
    def __init__(self):
        self.__radios = 20
        self.__falloff_mode = 0
        self.__folloff_center = [0, 0, 0]
        self.__falloff_arround_selection = False
        self.__falloff_masking = False
        self.__curve_list = []
        self.__name = Name('softMod_ctrl')
        self.__radius_scale = 1.0

    def addFalloffCurveValue(
            self, position, value, interporation=3
        ):
        r"""
            フォールオフの影響度合いを定義するカーブの座標を追加する
            
            Args:
                position (float):影響距離を表す横軸座標(0～1)
                value (float):影響度合いを表す縦軸座標(0～1)
                interporation (3):カーブの補完モード
        """
        self.__curve_list.append((position, value, interporation))

    def clearFalloffCurveValues(self):
        r"""
            フォールオフの影響度合いを定義するカーブの座標リストをクリアする
        """
        self.__curve_list = []

    def falloffCurveValues(self):
        r"""
            フォールオフの影響度合いを定義するカーブの座標リストを返す
            
            Returns:
                list:(位置座標、強度、補完モード)のtupleを持つリスト
        """
        return self.__curve_list[:]
        
    def setFalloffCurveValues(self, curveValueList):
        r"""
            フォールオフの影響度合いを定義するカーブの座標のリストを設定する。
            引数curveValueListは
                (位置座標(float)、強度(float)、補完モード(int))
            のtupleを持つリストである必要がある。
            
            Args:
                curveValueList (list):
        """
        self.__curve_lsit = curveValueList

    def removeFalloffCurveValue(self, index):
        r"""
            フォールオフの影響度合いを定義するカーブ座標リストから、
            任意の番号の座標情報を消去する
            
            Args:
                index (int):
        """
        del(self.__curve_list[index])

    def setFalloffRadius(self, radius):
        r"""
            フォールオフのデフォルトとなる半径を設定する
            
            Args:
                radius (float):
        """
        self.__radius = float(radius)

    def setFalloffMode(self, mode):
        r"""
            フォールオフのモードを設定する。
            SoftModification.VolumeModeかSoftModification.SurfaceModeを設定する
            
            Args:
                mode (int):
        """
        if not mode in (self.VolumeMode, self.SurfaceMode):
            raise ValueError(
                'The mode argument must be SoftModification.VolumeMode or '
                'SoftModification.SurfaceMode.'
            )
        self.__falloff_mode = mode

    def setFalloffCenter(self, x, y, z):
        r"""
            フォールオフの起点となる中心座標を設定する
            
            Args:
                x (float):X座標
                y (float):Y座標
                z (float):Z座標
        """
        self.__falloff_center = [x, y, z]
    
    def setFalloffArroundSelection(self, state):
        r"""
            選択した頂点の周囲にも減衰計算を行うかどうか
            
            Args:
                state (bool):
        """
        self.__falloff_arround_selection = bool(state)

    def setFalloffMasking(self, state):
        r"""
            変形効果を選択頂点に限定するかどうかを設定する
            
            Args:
                state (bool):
        """
        self.__falloff_masking = bool(state)

    def create(self, *nodes):
        r"""
            SoftModificationを作成する。
            
            Args:
                *nodes (tuple):操作対象となるノードのリスト
                
            Returns:
                list:作成されたsoftModならびにハンドルノード
        """
        if not nodes:
            nodes = node.ls(sl=True)
        curvelist = (
            self.__curve_list[:]
            if self.__curve_list else [(0, 1, 3), (0.5, 0.3, 3), (1, 0, 3)]
        )
        pos = [x[0] for x in curvelist]
        val = [x[1] for x in curvelist]
        ip = [x[2] for x in curvelist]

        args = {
            "falloffRadius" : self.__radios,
            'falloffMode' : self.__falloff_mode,
            'falloffCenter' : self.__folloff_center,
            'falloffBasedOnX' : 1,
            'falloffBasedOnY' : 1,
            'falloffBasedOnZ' : 1,
            'falloffAroundSelection' : self.__falloff_arround_selection,
            'falloffMasking' : self.__falloff_masking,
            'curveValue' : val, 'curvePoint' : pos, 'curveInterpolation' : ip,
        }

        softmod, handle = cmds.softMod(nodes, **args)
        return softmod, handle

    # These functions are for creating controller./////////////////////////////
    def setRadiusScale(self, scale):
        r"""
            フォールオフのデフォルト半径を変更する。
            このメソッドでフォールオフ値を変更しても、作成される
            radiusコントローラのデフォルト値は１のままになる。
            
            Args:
                scale (float):
        """
        self.__radius_scale = scale

    def setBaseName(self, name):
        r"""
            デフォーマーのノード名を設定する
            
            Args:
                name (str):
        """
        self.__name.setName(name)

    def setPosition(self, position):
        r"""
            デフォーマーの位置を表す文字列を設定する
            
            Args:
                position (str):
        """
        self.__name.setPosition(position)

    def createWithControllerSystem(self, *nodes):
        r"""
            コントローラ付きでsoftModを作成する。
            戻り値は作成されたノードを格納した辞書。
            各内容には以下のキーでアクセスする。
                controllers : [ctrl, r_ctrl, ctrl_space]
                proxies : [handle, r_ctrl_proxy, ctrl_space_proxy]
            
            Args:
                *nodes (tuple):操作対象となるノードのリスト
                
            Returns:
                dict:
        """
        if not nodes:
            nodes = node.ls(sl=True)

        basename = self.__name.name()

        # Creates a soft mod system with renaming it.--------------------------
        softmod, handle = self.create(*nodes)
        self.__name.setNodeType('sftMod')
        softmod = cmds.rename(softmod, self.__name())
        self.__name.setNodeType('ctrlProxy')
        handle = cmds.rename(handle, self.__name())
        # ---------------------------------------------------------------------

        # Creates a local rigging system.--------------------------------------
        self.__name.setNodeType('ctrlSpaceProxy')
        ctrl_space_proxy = node.createNode('transform', n=self.__name())

        self.__name.setNodeType('ctrlProxy')
        self.__name.setName(basename + 'Radius')
        r_ctrl_proxy = node.createNode(
            'transform', n=self.__name(), p=ctrl_space_proxy
        )
        handle = cmds.parent(handle, r_ctrl_proxy)[0]
        cmds.connectAttr(
            r_ctrl_proxy + '.worldInverseMatrix',
            softmod + '.bindPreMatrix'
        )
        radius_attr = r_ctrl_proxy + '.sx'
        for axis in ('y', 'z'):
            cmds.connectAttr(
                radius_attr, '%s.s%s' % (r_ctrl_proxy, axis)
            )
        # Creates a radius connection.
        self.__name.setNodeType('mdl')
        mdl = createUtil('multDoubleLinear', n=self.__name())
        cmds.setAttr(mdl + '.input1', self.__radius_scale)
        cmds.connectAttr(radius_attr, mdl + '.input2')
        cmds.connectAttr(mdl + '.output' , softmod + '.fr')

        # Creates a falloff center connetion.
        self.__name.setNodeType('pmm')
        pmm = createUtil('pointMatrixMult', n=self.__name())
        cmds.connectAttr(r_ctrl_proxy + '.parentMatrix', pmm + '.inMatrix')
        connect3ChannelAttr(
            r_ctrl_proxy + '.t', pmm + '.ip', ignoreKeyable=True
        )
        connect3ChannelAttr(pmm + '.o', softmod + '.fc')
        # ---------------------------------------------------------------------

        # Creates a controllers.-----------------------------------------------
        self.__name.setName(basename)
        self.__name.setNodeType('ctrlSpace')
        ctrl_space = node.createNode('transform', n=self.__name())

        self.__name.setName(basename + 'Radius')
        self.__name.setNodeType('ctrl')
        r_ctrl = node.createNode('transform', n=self.__name(), p=ctrl_space)
        for axis in ('y', 'z'):
            cmds.connectAttr(
                r_ctrl + '.sx', '%s.s%s' % (r_ctrl, axis)
            )
        r_ctrl.lockTransform()
        controlChannels(
            [r_ctrl], ['t:a', 'r:a', 'sx'], isKeyable=True, isLocked=False
        )

        self.__name.setName(basename)
        ctrl = node.createNode('transform', n=self.__name(), p=r_ctrl)
        cmds.setAttr(ctrl + '.v', k=False)

        connectKeyableAttr(r_ctrl, r_ctrl_proxy)
        connectKeyableAttr(ctrl, handle)

        # Adds shapes.
        shapeCreator = PrimitiveCreator()
        shapeCreator.setSize(self.__radius_scale)
        shapeCreator.setColorIndex(12)
        shapeCreator.create('sphere', r_ctrl)

        shapeCreator.setColorIndex(9)
        shapeCreator.create('box', ctrl)
        # ---------------------------------------------------------------------

        self.__name.setName(basename)
        cmds.aliasAttr('radius', r_ctrl/'sx')
        
        return {
            'controllers' : [ctrl, r_ctrl, ctrl_space],
            'proxies' : [handle, r_ctrl_proxy, ctrl_space_proxy],
        }
    # /////////////////////////////////////////////////////////////////////////
        
    def controllerFromNode(
        self, originalNode, removeOriginal=True, *nodes
    ):
        r"""
            選択ノードに対してsoftModデフォーマーとそれを制御するコントローラを
            追加する。
            
            戻り値は作成されたコントローラとその代理ノードのリストを格納した
            辞書で、アクセスするには以下のキーを使用する。
            controllers : 作成されたコントローラとそのスペーサーのリスト
            proxies : 作成された代理コントローラとその代理スペーサーのリスト
            コントローラはメインコントローラ、影響範囲制御コントローラ、スペーサー
            が作成され、この順番にリストに格納されている。
            
            Args:
                originalNode (str):
                removeOriginal (bool):
                *nodes (tuple):
                
            Returns:
                dict:
        """
        if cmds.nodeType(originalNode) != 'transform':
            raise RuntimeError('The original node must be transform node.')

        name = Name(originalNode)
        self.setBaseName(name.name())
        self.setPosition(name.position())
        radius = cmds.getAttr(originalNode + '.sx')

        self.setRadiusScale(radius)
        result = self.createWithControllerSystem(*nodes)
        for key in ('controllers', 'proxies'):
            cmds.delete(
                cmds.parentConstraint(originalNode, result[key][-1])
            )
        if removeOriginal:
            cmds.delete(originalNode)
        return result

# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////


# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////
def createBindJoint(
    startJoint, endJoint=None, parent=None, jointGrp=None, namespace=''
    ):
    r"""
        bindJointを作成する関数。
        引数endJointはstartJointよりも下の階層のジョイントである必要が ある。
        また-1を入れた場合はstartJointのbindJointのみを作成する。
        
        Noneの場合は末端まですべて作成する。
        endJointに正規表現オブジェクト、もしくは正規表現オブジェクトを
        内包するリストを渡すと、その正規表現にひっかかったノードで作成を止める。
        
        Args:
            startJoint (str or list or tuple):開始ジョイント
            endJoint (str or int or None):終了ジョイント
            parent (str):作成する親ノード
            jointGrp (str):parentがNoneの場合に格納される親グループ
            namespace (str):ノードタイプに負荷するネームスペース
            
        Returns:
            node.Transform:作成されたバインドジョイントを格納するグループ
    """
    def isInvalidType(obj):
        r"""
            objがtransformかjoint以外の場合はTrueを返す
            
            Args:
                obj (node.AbstractNode):
                
            Returns:
                bool:
        """
        return not obj.isType(('transform', 'joint'))

    def convNodeType(nodename):
        r"""
            ノードの名前をバインドジョイントの形式に変換する
            
            Args:
                nodename (str):
                
            Returns:
                str:
        """
        name = Name(nodename)
        nodetype = name.nodeType()
        nodetype = 'bnd' + nodetype[0].upper() + nodetype[1:]
        return nodetype

    def copyToBindJoint(joint, nodetype, parent):
        r"""
            バインドジョイントとしてjointをコピーする。
            
            Args:
                joint (node.Transform):
                nodetype (str):
                parent (node.Transform):
                
            Returns:
                node.Joint:作成されたジョイント
        """
        nodetype += namespace
        bind_joint = copyNode(joint, nodetype, parent)
        bind_joint.addBoolAttr('isConnected', default=False, k=False)
        bnd_jnt_attr = bind_joint.addMessageAttr('bindJoint')
        joint/'message' >> bnd_jnt_attr
        return bind_joint

    def create(joint, parent, pattern_objects):
        r"""
            jointとその下階層のノードについて、pattern_objectsの名前に該当する
            ところまで再帰的にバインドジョイントを作成する。
            
            Args:
                joint (node.Transform):
                parent (node.Transform):
                pattern_objects (_sre.SRE_Pattern):
        """
        if isInvalidType(joint):
            return
        nodetype = convNodeType(joint())
        parent = copyToBindJoint(joint, nodetype, parent)
        if not joint.hasChild():
            return
        for child in joint.children(type='transform'):
            for pattern in pattern_objects:
                if pattern.search(child()):
                    break
            else:
                create(child, parent, pattern_objects)
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    top_joint = None
    pattern_objects = []
    if isinstance(startJoint, (list, tuple)):
        joint_chains = node.toObjects(startJoint)
        startJoint = joint_chains[0]
    else:
        startJoint = node.asObject(startJoint)
        if endJoint:
            if endJoint == -1:
                # -1の場合はstartJointのみが作成される。
                joint_chains = [startJoint]
            elif isinstance(endJoint, RETYPE):
                pattern_objects = [endJoint]
                top_joint = startJoint
            elif isinstance(endJoint, (list, tuple)):
                pattern_objects = [
                    x for x in endJoint if isinstance(x, RETYPE)
                ]
                top_joint = startJoint
            else:
                # 文字の場合は、startJointとendJoint間のbindJointが作成される。
                joint_chains = listNodeChain(startJoint, endJoint)
        else:
            joint_chains = None
            top_joint = startJoint

    if not parent:
        parent_node = startJoint.parent()
        if not parent_node:
            parent = node.asObject(jointGrp)
        else:
            name = Name(startJoint)
            name.setName(name.name() + 'Parent')
            name.setNodeType('parentProxy')
            parent = node.createNode('transform', n=name(), p=jointGrp)
            parent.fitTo(parent_node)
            parent.lockTransform()
    else:
        parent = node.asObject(parent)

    if not top_joint:
        first_parent = parent
        for joint in joint_chains:
            if isInvalidType(joint):
                continue
            nodetype = convNodeType(joint)
            parent = copyToBindJoint(joint, nodetype, parent)
        return first_parent
    create(top_joint, parent, pattern_objects)
    return parent


def findBindJoint(baseJoint):
    r"""
        与えれたジョイントのバインドジョイントを見つけ、返す。
        戻り値は複数場合があるのでlistとなっている。
        
        Args:
            baseJoint (str):
            
        Returns:
            list:
    """
    targets = cmds.listConnections(
        baseJoint+'.message', d=True, s=False, p=True, type='transform'
    )
    if not targets:
        return []
    result = [
        node.asObject(x.split('.')[0])
        for x in targets if x.endswith('.bindJoint')
    ]
    return result


def connectToBindJoint(topJoint):
    r"""
        与えれたトップ階層下のジョイントをバインドジョイントへ接続する。
        
        Args:
            topJoint (str):
    """
    topJoint = node.asObject(topJoint)
    if not topJoint or not topJoint.exists():
        return

    if topJoint.hasChild():
        joints = topJoint.allChildren(type='transform')
        joints.append(topJoint)
    else:
        joints = [topJoint]
    for joint in joints:
        for target in findBindJoint(joint):
            if target('isConnected'):
                continue
            connectKeyableAttr(joint, target)
            target('isConnected', True)


def createSurfaceOnTrs(transform, name=None, axis='x', size=1):
    r"""
        任意のトランスフォームノードに合わせて四角いNURBSサーフェースを作成する
        
        Args:
            transform (str):任意のトランスフォームノード名
            name (str):作成されたサーフェースの名前
            axis (str):どの軸を上として作成するか
            size (float):サーフェースのサイズ
            
        Returns:
            node.NurbsSurface:
    """
    size *= 0.5
    indextable = {
        'x':(0, 1, 2), 'y':(1, 0, 2), 'z':(2, 0, 1), 
    }
    indexes = indextable.get(axis.lower())
    if not indexes:
        raise ValueError(
            'Invalid axis was given : "%s". Use only "x", "y" and "z".' % (
                axis
            )
        )

    trs = node.Transform(transform)
    if not trs:
        raise ValueError(
            (
                'The given node "%s" is invalid type.'
                ' Specify only a transform node'
            ) % transform
        )
    trs_matrix = FMatrix(trs.matrix())

    base_matrix = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0]
    couple_points = []
    for i in (-1, 1):
        points = []
        for j in (1, -1):
            plist = range(4)
            plist[indexes[0]] = 0
            plist[indexes[1]] = i*size
            plist[indexes[2]] = j*size
            plist[3] = 1
            p_matrix = FMatrix(base_matrix + plist) * trs_matrix
            points.append(p_matrix.translate())
        couple_points.append(points)

    curves = []
    for points in couple_points:
        curves.append(cmds.curve(d=1, p=points))
    lofted = cmds.loft(
        curves, ch=False, u=1, c=0, ar=1, d=1, ss=1, rn=0, po=0, rsn=True
    )
    cmds.delete(curves)
    cmds.rebuildSurface(
        lofted[0], ch=0, rpo=1, rt=1, end=1, kr=0, kcp=0, kc=0, su=4, du=3,
        sv=4, dv=3, tol=0.01, fr=0, dir=2
    )
    if not name:
        return asObject(lofted[0])
    return asObject(cmds.rename(lofted, name))

# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////
