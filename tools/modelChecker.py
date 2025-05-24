#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    モデルデータに対するチェッカー機能を提供するモジュール。
    
    Dates:
        date:2017/02/18 7:04[Eske](eske3g@gmail.com)
        update:2024/08/21 10:49 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import node
cmds = node.cmds

DefaultIgnoredTypes = ['skinCluster', 'tweak', 'blendShape']

def selectNodeByName(nodelist, **keywords):
    r"""
        任意の名前のリストに該当するオブジェクトを選択する。
        
        Args:
            nodelist (list):
            **keywords (str):cmds.selectコマンドに渡すフラグ
    """
    nodelist = node.cmds.ls(nodelist)
    if nodelist:
        node.cmds.select(nodelist, **keywords)


class PolyCvValueChecker(object):
    r"""
        ポリゴンの頂点に数値が入っていないかをチェック、修正する機能を提供する。
    """
    def __init__(self, nodelist=None):
        r"""
            Args:
                nodelist (list):
        """
        self.__checked = []
        self.check(nodelist)

    def check(self, nodelist=None):
        r"""
            チェックを行い、不正なメッシュをリストにキャッシュする。
            引数nodelistがNoneの場合は、シーン中すべてのメッシュに対して
            チェックを行う。
            
            Args:
                nodelist (list):
        """
        checked = []
        if not nodelist:
            nodelist = node.ls(type='mesh')
        for mesh in nodelist:
            vts = cmds.ls(mesh/'vtx[*]', fl=True)
            for vtx in vts:
                if [x for x in cmds.getAttr(vtx)[0] if x]:
                    checked.append(mesh)
                    break
        self.__checked = checked

    def listInvalidMeshes(self):
        r"""
            チェックの結果判明した、不正なメッシュのリストを返す。
            
            Returns:
                list:
        """
        return self.__checked[:]

    def isInvalid(self):
        r"""
            チェックの結果、不正なデータがあるかどうかを返す。
            
            Returns:
                bool:
        """
        return True if self.__checked else False

    def cleanup(self):
        r"""
            キャッシュ済みの不正なメッシュをクリーンナップする。
        """
        cached_selection = cmds.ls(sl=True)
        for mesh in self.__checked:
            print('Clean up vertex value : {}'.format(mesh))
            cmds.polyMoveVertex(mesh)
        cmds.delete(self.__checked, ch=True)
        if cached_selection:
            cmds.select(cached_selection, r=True, ne=True)
        else:
            cmds.select(cl=True)


def listUnfreezedNodes(targets=None):
    r"""
        フリーズ、リセットを行っていないノードを検出する。
        戻り値ではフリーズがかかっていないノードのリストと、リセットの
        かかっていないリストを持つtupleを返す。
        
        Args:
            targets (list):操作対象ノードのリスト。指定がない場合はシーン全体が対象
            
        Returns:
            tuple:フリーズされていないノード、リセットされていないノード
    """
    id_mtx = node.identityMatrix()
    pivot_attrs = ('rp', 'sp', 'rpt', 'spt')
    piv = (0, 0, 0)

    unfreezed_nodes = []
    unreset_nodes = []
    if targets is None:
        targets = node.ls(et='transform')
    else:
        targets = node.ls(targets, et=['transform'])
    for trs in targets:
        if trs.isShared():
            continue
        if trs.matrix(False) != id_mtx:
            unfreezed_nodes.append(trs)
            continue
        if [x for x in pivot_attrs if trs(x)[0] != piv]:
            unreset_nodes.append(trs)
    return (unfreezed_nodes, unreset_nodes)


def listPolySmoothness(targets=None):
    r"""
        1番表示になっていないメッシュをリストする。
        
        Args:
            targets (list):操作対象Meshのリスト。指定がない場合はシーン全体が対象
            
        Returns:
            list:
    """
    if targets is None:
        targets = node.ls(type=['mesh', 'transform'])
    else:
        targets = node.ls(targets, type=['mesh', 'transform'])
    results = []
    for tgt in targets:
        try:
            if tgt('dsm'):
                results.append(tgt)
        except:
            pass
    return results


def listIntermediates(targets=None):
    r"""
        intermediateObjectの一覧を返す。
        戻り値は４つのlistを持ち、それぞれコネクションの無いIO、srcからの接続
        のみのIO、dstへの接続のみのIO、そしてsrc、dstともに接続されている
        IOを持つ。
        
        Args:
            targets (any):
            
        Returns:
            tuple(list, list, list, list):
    """
    if targets is None:
        targets = node.ls(type=['transform'])
    else:
        targets = node.ls(targets, type=['transform'])
    no_con, from_src, to_dst, both = [], [], [], []
    for trs in targets:
        if not hasattr(trs, 'children'):
                continue
        for io in [x() for x in trs.children() if x('io')]:
            has_src = bool(cmds.listConnections(io, d=False, s=True))
            has_dst = bool(cmds.listConnections(io, d=True, s=False))
            if has_src and has_dst:
                both.append(io)
            elif has_src:
                from_src.append(io)
            elif has_dst:
                to_dst.append(io)
            else:
                no_con.append(io)
    return no_con, from_src, to_dst, both


def listDuplicateName():
    r"""
        重複した名前を持つノードをリストする。
        
        Returns:
            list:
    """
    return [x for x in node.ls(dag=True) if '|' in x]


def listInstances():
    r"""
        インスタンスをリストする。
        
        Returns:
            list:
    """
    results = []
    for n in node.ls(shapes=True, transforms=True):
        if not hasattr(n, 'isInstance') or not n.isInstance():
            continue
        results.append((n.shortName(), n.parents()))
    return results


def checkHistory(nodelist=None, ignoredTypes=None):
    r"""
        任意のノードのヒストリをチェックし、任意のノードタイプ以外が接続
        されているノードを検出する。
        戻り値は
            キー：操作対象ノード名
            値：辞書{
                'checked'：チェック済みのノードのリスト
                'ignored': ignoredTypesに該当する、スルーされたノードのリスト
            }
        を持つOrderedDict。
        値の'checked'、'ignored'内のリストには
            ('ノード名', 'ノードタイプ')
        を持つtupleが要素として格納されている。
        
        Args:
            nodelist (list):操作対象となるノードのリスト
            ignoredTypes (list):チェック対象外にするノードタイプのリスト

        Returns:
            OrderedDict:
    """
    from collections import OrderedDict
    if not nodelist:
        nodelist = cmds.ls(sl=True)
    if not ignoredTypes:
        ignoredTypes = DefaultIgnoredTypes
    results = OrderedDict()
    for n in nodelist:
        checked, ignored = [], []
        for h in cmds.listHistory(n, pdo=True, il=1) or []:
            n_type = cmds.nodeType(h)
            datalist = ignored if n_type in ignoredTypes else checked
            datalist.append((h, n_type))
        results[n] = {'checked':checked, 'ignored':ignored}
    return results

