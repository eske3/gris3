#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2024/08/26 11:39 Eske Yoshinob[eske3g@gmail.com]
        update:2024/09/02 14:13 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import node, grisNode
cmds = node.cmds
Version = '1.0.0'
GroupPrefix = '__grsObjStatGrp__'
TagAttr = '__grsObjStatTag__'


class ObjStatsRoot(grisNode.AbstractTopGroup):
    r"""
        セットアップデータを格納するgroupに関するクラス
    """
    BasicName = 'grsObjStatsData'
    NodeType = 'geometryVarGroup'
    BasicAttrs = [
        (
            {'ln':'grsObjStatsDataVersion', 'dt':'string'}, {},
            [Version, {'type':'string'}]
        )
    ]


class DataTransform(node.Transform, grisNode.AbstractGrisNode):
    r"""
        グループトップとなるTransformノード用クラス。
        _createメソッドが呼ばれると、translate・rotate・scaleに
        ロックをかけてからノードオブジェクトを返す。
    """
    NodeType = 'transform'
    BasicAttrs = [
        ({'ln':TagAttr, 'dt':'string'}, {'l':True}, None),
        ({'ln':'parent', 'dt':'string'}, {'l':True}, None),
    ]
    SupportedAttr = ('t', 'r', 's', 'sh', 'v')

    def _set_str_attr(self, attr, value):
        r"""
            string系アトリビュートに値valueを設定する。
            
            Args:
                attr (str):
                value (str):
        """
        self(attr, l=False)
        self(attr, value, l=True, type='string')

    def _copyAttrStats(self, src, dst):
        r"""
            Args:
                src (node.Transform):
                dst (node.Transform):
        """
        for at in self.SupportedAttr:
            attr_names = [x.attrName() for x in ~src.attr(at) or []]
            attr_names.append(at)
            for attr in attr_names:
                dst.editAttr([attr],
                    l=src.attr(attr).isLocked(),
                    k=src.attr(attr).isKeyable()
                )
    
    def _unlockAttrs(self, target):
        r"""
            Args:
                target (node.Transform):
        """
        for at in self.SupportedAttr:
            attr_names = [x.attrName() for x in ~target.attr(at) or []]
            attr_names.append(at)
            target.editAttr(attr_names, l=False)

    def setTag(self, tag):
        r"""
            タグを設定する。
            実行するとこのクラスが扱うオブジェクトのカスタムアトリビュートに
            設定される。

            Args:
                tag (str):
        """
        self._set_str_attr(TagAttr, tag)

    def tag(self):
        r"""
            このクラスが取り扱うオブジェクトに設定されたカスタムアトリビュートに
            登録されたタグを返す。

            Returns:
                parentName (str):
        """
        return self(TagAttr)

    def setParentName(self, parentName):
        r"""
            親の名前を設定する。
            実行するとこのクラスが扱うオブジェクトのカスタムアトリビュートに
            設定される。

            Args:
                parentName (str):
        """
        if parentName is None:
            parentName = ''
        self._set_str_attr('parent', parentName)

    def parent(self):
        r"""
            このクラスが取り扱うオブジェクトに設定されたカスタムアトリビュートに
            登録された親オブジェクトの名前を返す。

            Returns:
                parentName (str):
        """
        return self('parent')

    def storeStats(self, target=None):
        r"""
            引数ターゲットで指定したTransformの状態を自身に移す。

            Args:
                target (node.Transform):
        """
        target = (
            target if target else self.target()
        )
        self._unlockAttrs(self)
        self.fitTo(target)
        self.setParentName(target.parent())
        self._copyAttrStats(target, self)

    def restoreStats(self, dataGroup):
        r"""
            dataGroupが対応するターゲットに対し、自身の状態を移す。

            Args:
                dataGroup (DataGroup): ターゲット情報を持つDataGroup
        """
        target = dataGroup.target()
        self._unlockAttrs(target)
        parent = node.asObject(self.parent())
        if parent:
            if parent != target.parent():
                cmds.parent(target, parent)
        else:
            if target.parent():
                cmds.parent(target, w=True)
        target.fitTo(self)
        self._copyAttrStats(self, target)


class DataGroup(node.Transform, grisNode.AbstractGrisNode):
    NodeType = 'transform'
    BasicAttrs = [
        (
            {'ln':'grsObjStatsGroupVersion', 'dt':'string'}, {},
            [Version, {'type':'string'}]
        )
    ]
    def targetName(self):
        return self.replace(GroupPrefix, '')

    def target(self, withName=False):
        r"""
            Args:
                withName (bool):
        """
        name = self.targetName()
        obj = node.asObject(name)
        return (obj, name) if withName else obj

    def dataTransforms(self):
        return grisNode.listNodes(DataTransform, self.children())

    def listTags(self):
        return [
            x.tag() for x in self.dataTransforms()
        ]

    def removeTags(self, taglist):
        removed = [x for x in self.dataTransforms() if x.tag() in taglist]
        if removed:
            cmds.delete(removed)


def getDataTransform(targetGroup, tag):
    r"""
        Args:
            targetGroup (node.Transform):
            tag (str):
    """
    for trs in targetGroup.dataTransforms():
        if trs.tag() == tag:
            return trs


def listStoredGroup():
    root = grisNode.listNodes(ObjStatsRoot)
    results = []
    if not root:
        return results
    return [DataGroup(x()) for x in root[0].children()]


def listStoredTargets():
    from collections import OrderedDict
    result = OrderedDict()
    for str_grp in listStoredGroup():
        target = str_grp.target()
        if not target:
            continue
        result[str_grp] = target
    return result


def listTags():
    taglist = []
    for grp in listStoredGroup():
        taglist.extend(grp.listTags())
    taglist = list(set(taglist))
    taglist.sort()
    return taglist


def store(tag='default', targets=None):
    r"""
        位置情報や状態をノードに保存する。
        保存対象はTransformノードで、アトリビュートは
            matrix
            t/r/s/sh/vのロック・キーアブル情報
            visibilityの状態
            親オブジェクト
        
        Args:
            tag (str):保存時の状態を表す識別タグ
            targets (list):操作対象ノード
        
        Returns:
            ObjStatsRoot: データを格納するルートノード
    """
    targets = node.selected(targets, type='transform')
    if not targets:
        return []
    pre_selection = cmds.ls(sl=True)
    root = grisNode.listNodes(ObjStatsRoot)
    if not root:
        root = grisNode.createNode(ObjStatsRoot)
    else:
        root = root[0]
    children = root.children()
    for target in targets:
        # オブジェクトごとの管理グループを作成する。
        grp = GroupPrefix + target
        if not grp in children:
            grp = grisNode.createNode(DataGroup, n=grp, p=root)
        else:
            grp = DataGroup(grp)
        grp.lockTransform()

        data_trs = getDataTransform(grp, tag)
        if not data_trs:
            data_trs = grisNode.createNode(DataTransform, p=grp)
            data_trs.setTag(tag)
        data_trs.storeStats(target)

    if pre_selection:
        cmds.select(pre_selection, r=True, ne=True)

    return root


def storeToRegistered(tag='default'):
    r"""
        Args:
            tag (str):
        
        Returns:
            list: 
    """
    targets = listStoredTargets()
    if not targets:
        return []
    return store(tag, list(targets.values()))


def restore(tag='default'):
    r"""
        Args:
            tag (str):
    """
    for grp in listStoredGroup():
        data_trs = getDataTransform(grp, tag)
        if not data_trs:
            continue
        data_trs.restoreStats(grp)


def selectTargetByStoredGroup(storedGroups):
    r"""
        与えられたDataGroupのリストのターゲットとなるオブジェクトを選択する。

        Args:
            storedGroups (list):選択したいDataGroupの名前のリスト
    """
    targets = []
    for str_grp in storedGroups:
        data_grp = DataGroup(str_grp)
        target = data_grp.target()
        if target:
            targets.append(target)
    if targets:
        cmds.select(targets, r=True, ne=True)


def removeStored(taglist=None, storedGroupList=None):
    r"""
        任意のターゲットのタグと、任意のDataGroupを削除する。
        引数taglistには以下の書式の文字列のリストを渡す。
            DataGroup名 + "->" + tag名
            例） __grsObjStatGrp__face_geo->default

        Args:
            taglist (list):削除するタグの一覧（文字列のリスト）
            storedGroupList (list):削除するDataGroupの一覧（文字列のリスト）
    """
    for tag in taglist or []:
        grp, tag = tag.split('->', 1)
        str_grp = DataGroup(grp)
        if not str_grp:
            continue
        str_grp.removeTags([tag])

    deleting_grps = []
    for grp in storedGroupList or []:
        str_grp = DataGroup(grp)
        if not str_grp:
            continue
        deleting_grps.append(str_grp)
    if deleting_grps:
        cmds.delete(deleting_grps)


def removeTagAll(tag):
    r"""
        tagで指定されたタグに該当するデータを全て削除する。

        Args:
            tag (str):
    """
    for data_grp in listStoredGroup():
        data_grp.removeTags([tag])