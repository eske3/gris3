#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2024/09/25 14:32 Eske Yoshinob[eske3g@gmail.com]
        update:2025/09/02 11:50 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import node
from . import cleanup
cmds = node.cmds


DefaultBlendShapeName = 'facial_bs'
DefaultTargetContainer = 'facialMorph_grp'
DefaultTargetGeometory = 'face_geo'


def getTargetContainerGroup(targetGroup):
    r"""
        targetGroupという名のブレンドシェイプターゲットを格納する
        グループノードをnode.Transform形式で返す。
        targetGroupがシーン中に存在しないか、childrenアトリビュートを持たない
        場合はValueErrorを返す。

        Args:
            targetGroup (str): ターゲット格納グループ名

        Returns:
            node.Transform:
    """
    t_grp = node.asObject(targetGroup)
    if not t_grp or not hasattr(t_grp, 'children'):
        raise ValueError(
            'The target shape container group is invalid : {}'.format(
                targetGroup
            )
        )
    return t_grp


def convTargetContainerGroupToList(targetGroup):
    r"""
        ターゲットを格納するグループtargetGroupが格納している
        子グループの名前の一覧を返す。

        Args:
            targetGroup (str):ターゲット格納グループ名
    """
    t_grp = getTargetContainerGroup(targetGroup)
    return [x() for x in t_grp.children()]


def makeShapeTargetGroup(targetGroup, targetList, deleteUnknownTarget=True):
    r"""
        ブレンドシェイプターゲットの各要素を格納するグループを、
        引数targetListの分だけ作成する。

        Args:
            targetGroup (str):
            targetList (list):
        
        Returns:
            list:
    """
    t_grp = getTargetContainerGroup(targetGroup)
    old_children = convTargetContainerGroupToList(t_grp)
    results = []
    for tgt in reversed(targetList):
        if tgt in old_children:
            cmds.reorder(tgt, f=True)
            results.append(node.asObject(tgt))
            old_children.remove(tgt)
            continue
        trs = node.createNode('transform', name=tgt, p=t_grp)
        cmds.reorder(trs, f=True)
        results.append(trs)

    return results


class BasicFacialBSNameEngine(object):
    def __init__(self, targetGroupName):
        self.__obj = node.asObject(targetGroupName)
        self.analyzeName()

    def node(self):
        return self.__obj

    def typeName(self):
        return 'facialGrp'

    def setData(category, baseName, position):
        self.__category = category
        self.__basename = baseName
        self.__position = position

    def analyzeName(self):
        name = self.node()()
        elms = name.split('_')
        typename = self.typeName()
        type_name = '_{}'.format()
        if not typename in elms:
            raise NameError('Invalid target name : {}'.format(name))
        category = elms.pop(0)
        position = elms.pop(-1)
        elms.remove(typename)
        basename = '_'.join(elms)
        self.setData(category, basename, position)

    def category(self):
        return self.__category

    def basename(self):
        return self.__basename
        
    def position(self):
        return self.__position


class BasicFacialBSManager(object):
    def __init__(
        self,
        geometry=DefaultTargetGeometory,
        blendShape=DefaultBlendShapeName,
        container=DefaultTargetContainer,
        # nameEngine=BasicFacialBSNameEngine
    ):
        self.setGeometory(geometry)
        self.setBlendShape(blendShape)
        self.setContainer(container)
        # self.setNameEngine(BasicFacialBSNameEngine)

    def setGeometory(self, geometry):
        self.__geometory = geometry

    def geometry(self):
        return node.asObject(self.__geometory)

    def setBlendShape(self, blendShapeName):
        self.__blendshape = blendShapeName

    def blendShape(self):
        return node.asObject(self.__blendshape)

    def setContainer(self, container):
        self.__container = container

    def container(self):
        return getTargetContainerGroup(self.__container)

    def setNameEngine(self, nameEngine):
        self.__name_engine = nameEngine

    def nameEngine(self):
        return self.__name_engine

    def duplicateGeo(self, geometry, container):
        if container.children():
            return
        duplicated = cmds.duplicate(geometry, rr=True)
        all_duplicated = cmds.listRelatives(
            duplicated, ad=True, pa=True, type='transform'
        ) or []
        all_duplicated = duplicated + all_duplicated
        # IntermediateObjectの削除。
        cleanup.deleteUnusedIO(all_duplicated, False)
        # Transformノードのロック解除
        for geo in node.toObjects(all_duplicated):
            if not geo.isSubType('transform'):
                continue
            geo.unlockTransform()
        cmds.parent(duplicated, container)

    def makeTargets(self):
        geo = self.geometry()
        shapes = [geo]
        if geo.isSubType('transform'):
            if not geo.shapes(ni=True):
                shapes = [
                    x for x in geo.allChildren(type='mesh') if not x('io')
                ]
        container = self.container()
        bbmins, bbmaxs = [], []
        for s in shapes:
            with node.editFreezedShape(s) as shape:
                bb = cmds.polyEvaluate(shape, b=True)
                bbmins.append(bb[0][0])
                bbmaxs.append(bb[0][1])
        max_pos = max(bbmaxs)
        width = max_pos - min(bbmins)

        pre_category = None
        name_engine = self.nameEngine()
        containers = [
            name_engine(x) for x in convTargetContainerGroupToList(container)
        ]
        for i, con_data in enumerate(containers):
            self.duplicateGeo(geo, tgt_grp)


def createBlendShapeForFacial(geometry, blendShape, targetGroup):
    r"""
        Args:
            geometry (str):
            blendShape (str):
            targetGroup (str):
    """
    t_grp = getTargetContainerGroup(targetGroup)
    facial_targets = t_grp.children()
    if not facial_targets:
        return
    facial_targets.append(geometry)
    bs = cmds.blendShape(facial_targets, frontOfChain=True, n=blendShape)[0]


def duplicateTargets(geometry, blendShape, parent=None):
    r"""
        Args:
            geometry (str):ブレンドシェイプを適用されるノード名
            blendShape (str):ブレンドシェイプ名
            parent (str):シェイプターゲットを格納するグループ名
    """
    bs = node.asObject(blendShape)
    if not bs.isType('blendShape'):
        raise AttributeError(
            'The specified node "{}" is not blendShape.'.format(blendShape)
        )
    duplicated = bs.duplicateTargets(geometry)
    all_duplicated = cmds.listRelatives(
        duplicated, ad=True, pa=True, type='transform'
    ) or []
    all_duplicated = duplicated + all_duplicated
    cleanup.deleteUnusedIO(all_duplicated, False)
    for geo in all_duplicated:
        if not geo.isSubType('transform'):
            continue
        geo.unlockTransform()
    
    parent = getTargetContainerGroup(parent)
    children = {x.shortName(): x for x in parent.children()}
    for geo in duplicated:
        name = geo.shortName()
        if name in children:
            geo.fitTo(children[name])
            cmds.delete(children[name])
        cmds.parent(geo, parent)

