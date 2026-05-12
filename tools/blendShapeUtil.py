#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2024/09/25 14:32 Eske Yoshinob[eske3g@gmail.com]
        update:2025/10/22 05:07 Eske Yoshinob[eske3g@gmail.com]
        
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
            targetGroup (str):ターゲット格納グループ名
            
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
            deleteUnknownTarget (any):
            
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
    if old_children and deleteUnknownTarget:
        cmds.delete(old_children)
    return results


class BasicFacialBSNameEngine(object):
    r"""
        ブレンドシェイプターゲットの名前ルールを管理する機能を提供するクラス。
    """
    TypeName = 'facialGrp'
    BasePattern = '([a-zA-Z\d]+?)_([a-zA-Z\d]+?){}(_[A-Z]$|$)'

    def __init__(self, targetGroupName, baseGeometry=None):
        r"""
            Args:
                targetGroupName (str):
                baseGeometry (node.Transform):ブレンドシェイプ適用先ジオメトリ
        """
        self.__obj = node.asObject(targetGroupName)
        self.__base_geo = baseGeometry
        self.analyzeName()

    def node(self):
        return self.__obj

    def setBaseGeometry(self, geometry):
        self.__base_geo = geometry

    def baseGeometry(self):
        return self.__base_geo

    def setData(self, category, baseName, position):
        r"""
            Args:
                category (str):
                baseName (str):
                position (str):
        """
        self.__category = category
        self.__basename = baseName
        self.__position = position

    def analyzeName(self):
        import re
        ptn = re.compile(self.BasePattern.format('_' + self.TypeName))
        name = self.node().shortName()
        r = ptn.match(name)
        if not r:
            raise NameError('Invalid target name : {}'.format(name))
        self.setData(r.group(1), r.group(2), r.group(3).rsplit('_')[-1])

    def category(self):
        return self.__category

    def basename(self):
        return self.__basename
        
    def position(self):
        return self.__position

    def bsTargetName(self):
        return '_'.join([self.category(), self.basename(), self.position()])

    def topTargetName(self):
        base_geo = self.baseGeometry()
        if not base_geo:
            raise RuntimeError(
                (
                    'Makeing top target name requires '
                    'the base geometry name. : {}'
                ).format(self.bsTargetName())
            )
        return '{}_{}'.format(self.bsTargetName(), base_geo)


class BasicFacialBSManager(object):
    r"""
        フェイシャル用ブレンドシェイプの管理・作成を行う機能を提供するクラス。
    """
    def __init__(
        self,
        geometry=DefaultTargetGeometory,
        blendShape=DefaultBlendShapeName,
        container=DefaultTargetContainer,
        nameEngine=BasicFacialBSNameEngine
    ):
        r"""
            Args:
                geometry (str):
                blendShape (str):
                container (str):
                nameEngine (BasicFacialBSNameEngine):
        """
        self.setGeometory(geometry)
        self.setBlendShape(blendShape)
        self.setContainer(container)
        self.setNameEngine(nameEngine)

    def setGeometory(self, geometry):
        r"""
            Args:
                geometry (str):
        """
        self.__geometory = geometry

    def geometry(self):
        return node.asObject(self.__geometory)

    def setBlendShape(self, blendShapeName):
        r"""
            Args:
                blendShapeName (str):
        """
        self.__blendshape = blendShapeName

    def blendShape(self):
        r"""
            設定されているブレンドシェイプ名を返す。
            
            Returns:
                str:
        """
        return self.__blendshape

    def setContainer(self, container):
        r"""
            Args:
                container (str):
        """
        self.__container = container

    def container(self):
        return getTargetContainerGroup(self.__container)

    def setNameEngine(self, nameEngine):
        r"""
            ターゲットグループの命名規則を定義するエンジンを設定する。
            
            Args:
                nameEngine (BasicFacialBSNameEngine):
        """
        self.__name_engine = nameEngine

    def nameEngine(self):
        r"""
            設定されている命名規則エンジンを返す。
            
            Returns:
                BasicFacialBSNameEngine:
        """
        return self.__name_engine

    def cleanupTarget(self, target, targetGroup):
        r"""
            ターゲットをクリーンナップし、与えられたtargetGroupに応じた名前に
            変更する。

            Args:
                targets (str):
                targetGroup (BasicFacialBSNameEngine):
        """
        all_targets = cmds.listRelatives(
            target, ad=True, pa=True, type='transform'
        ) or []
        all_targets = all_targets + [target]
        # IntermediateObjectの削除。
        cleanup.deleteUnusedIO(all_targets, False)
        # Transformノードのロック解除
        transforms = []
        for geo in node.toObjects(all_targets):
            if not geo.isSubType('transform'):
                continue
            geo.unlockTransform()
            transforms.append(geo)
        prefix = (targetGroup.bsTargetName() + '_{}').format
        for geo in transforms[:-1]:
            cmds.rename(geo, prefix(geo.shortName()))
        return node.rename(target, targetGroup.topTargetName())

    def duplicateGeo(self, targetGroup):
        r"""
            Args:
                targetGroup (BasicFacialBSNameEngine):

            Returns:
                node.Transform:
        """
        obj = targetGroup.node()
        obj.setMatrix(node.identityMatrix())
        if obj.children():
            return []
        duplicated = cmds.duplicate(targetGroup.baseGeometry(), rr=True)[0]
        duplicated = self.cleanupTarget(duplicated, targetGroup)
        return node.parent(duplicated, obj)[0]

    def makeTargets(self):
        geo = self.geometry()
        shapes = [x for x in geo.allChildren(type='mesh') if not x('io')]
        container = self.container()
        bbs = [[], [], [], []] # xMin, xMax, yMin, yMax
        for s in shapes:
            with node.editFreezedShape(s) as shape:
                bb = cmds.polyEvaluate(shape, b=True)
                bbs[0].append(bb[0][0])
                bbs[1].append(bb[0][1])
                bbs[2].append(bb[1][0])
                bbs[3].append(bb[1][1])
        width = max(bbs[1]) - min(bbs[0])
        height = max(bbs[3]) - min(bbs[2])
        offset_x = width * 0.2
        offset_y = height * 0.2
        x_corner = width + offset_x + offset_x
        
        name_engine = self.nameEngine()
        tgt_groups = [
            name_engine(x, geo)
            for x in convTargetContainerGroupToList(container)
        ]
        categories = {}
        row = 0
        for tgt_grp in tgt_groups:
            duplicated = self.duplicateGeo(tgt_grp)
            cat = tgt_grp.category()
            if cat not in categories:
                categories[cat] = [row, 0]
                row += 1
            else:
                categories[cat][1] += 1
            x = x_corner + categories[cat][1] * (width + offset_x)
            y = categories[cat][0] * (height + offset_y)
            tgt_grp.node().setPosition([x, y, 0])

    def createBlendShape(self):
        r"""
            フェイシャル用のブレンドシェイプを作成する。
        """
        geo = self.geometry()
        container = self.container()
        name_engine = self.nameEngine()
        tgt_groups = [
            name_engine(x, geo)
            for x in convTargetContainerGroupToList(container)
        ]
        bs = cmds.blendShape(geo, frontOfChain=True, n=self.blendShape())[0]
        for idx, con in enumerate(tgt_groups):
            con_name = con.node()()
            cmds.blendShape(bs, e=True, t=(geo, idx, con_name, 1.0))
            cmds.aliasAttr(con.bsTargetName(), '{}.weight[{}]'.format(bs, idx))

    def duplicateTargets(self):
        print('# Duplicate targets '.ljust(80, '='))
        bs = node.asObject(self.blendShape())
        if not bs or not bs.isType('blendShape'):
            raise AttributeError(
                'The specified node "{}" is not blendShape.'.format(blendShape)
            )
        geo = self.geometry()
        container = self.container()
        name_engine = self.nameEngine()
        print('  * Geometry : {}'.format(geo))
        print('  * Target group container : {}'.format(container))
        print('  * Name Engine : {}'.format(name_engine))

        tgt_groups = [
            name_engine(x, geo)
            for x in convTargetContainerGroupToList(container)
        ]
        tgt_grpname_keys = {x.bsTargetName() : x for x in tgt_groups}

        print('  + Start duplicating targets from {}.'.format(geo))
        ak_prestate = cmds.autoKeyframe(q=True, state=True)
        cmds.autoKeyframe(state=False)
        duplicated = bs.duplicateTargets(geo)
        cmds.autoKeyframe(state=ak_prestate)

        for target in duplicated:
            tgt_group = tgt_grpname_keys.get(target.shortName())
            if not tgt_group:
                print(
                    '  ! Warning : Target group does not detected of {}'.format(
                        target
                    )
                )
                continue
            parent = tgt_group.node()
            children = parent.children()
            if children:
                pos = children[0].matrix(False)
                cmds.delete(children)
            else:
                pos = target.matrix()
            target = node.parent(target, tgt_group.node())[0]
            target.setMatrix(pos, False)
            self.cleanupTarget(target, tgt_group)
        print('# Done. '.ljust(80, '='))

    def renameBsAttrs(self):
        bs = node.asObject(self.blendShape())
        container = self.container()
        name_engine = self.nameEngine()
        tgt_groups = [
            name_engine(x) for x in convTargetContainerGroupToList(container)
        ]
        tgt_grpname_keys = {
            x.node().shortName() : x.bsTargetName() for x in tgt_groups
        }
        
        for attr in bs.listAttrNames():
            new_name = tgt_grpname_keys.get(attr)
            if not new_name:
                continue
            cmds.aliasAttr(new_name, bs/attr)


def createBlendShapeForFacial(geometry, blendShape, targetGroup):
    r"""
        フェイシャル用のブレンドシェイプを作成する。
        ターゲットがグループに入っていない構造を前提とした機能となっている。
        ターゲットをグループに入れて管理する機構についてはBasicFacialBSManager
        を使用する。
        この機能は廃止予定。
        
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
        過去バージョン版。
        ターゲットがグループに入っていない構造を前提とした機能となっている。
        ターゲットをグループに入れて管理する機構についてはBasicFacialBSManager
        を使用する。
        この機能は廃止予定。
        
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

