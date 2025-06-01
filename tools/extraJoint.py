#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    extraJointを取扱うモジュール。
    
    Dates:
        date:2017/02/22 6:36[Eske](eske3g@gmail.com)
        update:2021/09/13 15:30 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import node, system, mathlib, verutil

class ExtraJoint(node.Transform):
    r"""
        ExtraJointを取扱う機能を提供するクラス。
    """
    NodeType = 'implicitSphere'

    def __init__(self, nodeName):
        r"""
            初期化を行う。
            
            Args:
                nodeName (str):ExtraJoint名
        """
        if verutil.PyVer < 3:
            super(ExtraJoint, self).__init__(nodeName)
        else:
            super(ExtraJoint, self).__init__()
        self.__shape = None
        typ = self.type()
        if typ == 'transform':
            spheres = self.children(type=self.NodeType)
        elif typ == self.NodeType:
            spheres = [self]
        else:
            return
        if not spheres:
            return
        for sphere in spheres:
            if sphere.hasAttr('extraJoint'):
                self.__shape = sphere
                break

    def shape(self):
        return self.__shape

    def isValid(self):
        r"""
            初期化を行ったオブジェクト名がExtraJointかどうかを返す。
            
            Returns:
                bool:
        """
        return True if self.shape() else False

    def joint(self):
        r"""
            ジョイントを返す。
            ジョイントとは、ExtraJointのSpace階層直下のジョイントを指す
            
            Returns:
                node.Joint:
        """
        joint = self.shape().attr('extraJoint').source()
        return joint if joint else None

    def radius(self):
        r"""
            implicitSphereの半径を返す。
            
            Returns:
                float:
        """
        return self.__shape('radius')

    def jointRadius(self):
        r"""
            このExtraJointが持つジョイントの大きさを返す。
            
            Returns:
                float:
        """
        j = self.joint()
        if not j:
            return 1.0
        return j('radius')

    def __getTagPlug(self):
        shape = self.shape()
        if not shape:
            return
        if not shape.hasAttr('extraJointTag'):
            plug = shape.addStringAttr('extraJointTag')
        else:
            plug = shape.attr('extraJointTag')
        return plug

    def tag(self):
        r"""
            設定されているタグを返す。
            
            Returns:
                str:
        """
        plug = self.__getTagPlug()
        tag = plug.get()
        plug.setLock(True)
        return tag or ''

    def setTag(self, tag=''):
        r"""
            任意のタグを設定する。
            
            Args:
                tag (str):
        """
        plug = self.__getTagPlug()
        plug.setLock(False)
        plug.set(tag)
        plug.setLock(True)


def create(
        basename, nodeType='joint', nodeTypeLabel='bndJnt', side=0,
        parent=None, offset=0, matrix=None, worldSpace=False,
        radius=None, jointSize=None, parentLength=-1,
        tag=''
    ):
    r"""
        extraJointを作成する。
        引数parentLengthは親の長さを入力する。親の長さとは親ノードから親ノードの
        最初の子ノードまでの長さで、引数parentに指定したノードの同様の長さとの
        比率で、matrixで指定した位置に補正をかける。
        
        Args:
            basename (str):ベースとなる名前
            nodeType (str):ノードの種類
            nodeTypeLabel (str):ノードの種類を表す文字列
            side (str):ノードの位置を表す値。
            parent (str):作成する親ノード。
            offset (int):オフセットの数
            matrix (list):作成位置を表す行列
            worldSpace (bool):
            radius (float):implicitSphereの大きさ
            jointSize (float):jointの大きさ
            parentLength (float):
            tag (str):任意のタグ
            
        Returns:
            dict:
    """
    def correctMatrix(matrix, parentLength, parent):
        r"""
            与えられた行列に対し、長さの比率分の移動値の補正を行う。
            
            Args:
                matrix (list):位置行列
                parentLength (float):親までの長さ
                parent (str):親ノード
                
            Returns:
                list:修正された位置情報を表す行列
        """
        if parentLength <= 0 or not parent:
            return matrix
        children = parent.children()
        if len(children) < 2:
            return matrix
        length = (
            mathlib.Vector(children[0].position())
            -mathlib.Vector(children[0].position())
        ).length()
        ratio = parentLength / length
        for i in (12, 13, 14):
            matrix[i] *= ratio
        return matrix

    parent = node.selected(parent, type='transform')[0]
    name = system.GlobalSys().nameRule()()
    name.setName(basename)
    name.setNodeType(nodeTypeLabel + 'Space')
    name.setPosition(side)

    # スペーサーの作成。=======================================================
    if None in (radius, jointSize):
        if parent.isType('joint'):
            size = parent('radius')
        elif parent.hasParent():
            size = parent.distance(parent.parent()) * 0.2
        else:
            size = 2.0
        if radius is None:
            radius = size * 0.75
        if jointSize is None:
            jointSize = size * 0.5

    space = node.createNode('transform', n=name(), p=parent())
    space_shape = node.createNode(
        ExtraJoint.NodeType, n=space+'Shape', p=space
    )
    space_shape('radius', radius)
    space_shape.addMessageAttr('extraJointOffsets', m=True, im=False)
    space_shape.addMessageAttr('extraJoint')
    # =========================================================================

    # オフセットノードを作成する。=============================================
    if offset > 26:
        offset = 26
    offset_nodes = []
    p = space
    for i in range(offset):
        index = i + 1
        name.setNodeType(nodeTypeLabel+'Offset'+verutil.UPPERCASE[i])
        offset_nodes.append(node.createNode('transform', n=name(), p=p))
        p=offset_nodes[-1]
        p.editAttr(['v'], k=False)

        cmds.connectAttr(
            p/'message', space_shape/'extraJointOffsets', na=True
        )
    # =========================================================================

    # コントローラを作成。=====================================================
    name.setNodeType(nodeTypeLabel)
    ctrl = node.createNode(nodeType, n=name(), p=p)
    if nodeType == 'joint':
        ctrl('radius', jointSize)
    ctrl.attr('message') >>  space_shape.attr('extraJoint')
    # =========================================================================

    # 行列の指定がある場合は、行列をセットする。===============================
    if matrix:
        matrix = correctMatrix(matrix, parentLength, parent)
        space.setMatrix(matrix, worldSpace)
    # =========================================================================

    space.select()
    print(space)
    print('-' * 80)
    space = ExtraJoint(space())
    space.setTag(tag)
    return {
        'space':space, 'offsets':offset_nodes, 'ctrl':ctrl
    }

    
def listExtraJoints(nodelist=None, tag=''):
    r"""
        任意のノードのリストの中からExtraJointをリストする。
        
        Args:
            nodelist (list):
            tag (str):
            
        Returns:
            list:
    """
    nodelist = [
        ExtraJoint(x())
        for x in node.selected(
            nodelist, type=['transform', ExtraJoint.NodeType]
        )
    ]
    extra_joints = [x for x in nodelist if x.isValid()]
    if tag:
        extra_joints = [x for x in extra_joints if x.tag() == tag]
    return extra_joints


def listExtraJointsInScene(tag=''):
    r"""
        シーン中にあるすべてのExtraJointをリストする。
        
        Args:
            tag (str):
            
        Returns:
            list:
    """
    all_targets = node.cmds.ls(type=ExtraJoint.NodeType)
    return listExtraJoints(all_targets, tag=tag)


def selectExtraJoint(topNodes=None, tag=''):
    r"""
        任意のノード下にあるエクストラジョイントを選択する。
        
        Args:
            topNodes (list):捜査対象ノード
            tag (str):フィルタリング用のタグ
            
        Returns:
            list:
    """
    cmds = node.cmds
    if not topNodes:
        topNodes = node.cmds.ls(sl=True, type='transform')

    all_nodes = cmds.listRelatives(topNodes, ad=True, type=ExtraJoint.NodeType)
    if not all_nodes:
        return
    ej = []
    for n in all_nodes:
        if not cmds.attributeQuery('extraJoint', ex=True, n=n):
            continue
        extra_joint = ExtraJoint(cmds.listRelatives(n, p=True, pa=True)[0])
        if tag and extra_joint.tag() != tag:
            continue
        ej.append(extra_joint)
    if not ej:
        return
    cmds.select(ej, r=True)
    return ej


def createMirroredJoint(targetJoints=None):
    r"""
        選択されたExtraJointをミラーリングする。
        
        Args:
            targetJoints (list):
            
        Returns:
            list:作成されたExtraJoint情報のリスト
    """
    from gris3 import mathlib
    name_rule = system.GlobalSys().nameRule()
    result = []
    for n in [ExtraJoint(x()) for x in node.selected(targetJoints)]:
        if not n.isValid():
            continue
        name = name_rule(n())
        name = name.mirroredName()
        if not name:
            continue

        j = n.joint()
        if not j:
            continue
        j_name = name_rule(j)

        parent = n.parent()
        p_name = name_rule(parent)
        p_name = p_name.mirroredName()
        if not p_name:
            p_name = parent
        parent = node.asObject(p_name())

        matrix = n.matrix()
        matrix = mathlib.mirrorMatrix(matrix, mathlib.mirrorMatrix.X)

        exj = create(
            name.name(), nodeTypeLabel=j_name.nodeType(),
            side=name.positionIndex(), parent=parent,
            radius=n.radius(), jointSize=n.jointRadius(), tag=n.tag()
        )
        exj['space'].setMatrix(matrix)
        result.append(exj)
    return result

