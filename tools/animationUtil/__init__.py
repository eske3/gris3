#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2022/10/28 07:01 Eske Yoshinob[eske3g@gmail.com]
        update:2023/07/26 11:13 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2022 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import re
from gris3 import node
cmds = node.cmds

def listAnimPlugs(srcNode):
    r"""
        引数srcNodeに接続されているアニメーションノードと、そのアトリビュートを
        リストにして返す。
        戻り値は
            アニメーションカーブの出力アトリビュート
            srcNodeのアニメーションアトリビュート
            srcNodeのアニメーションアトリビュート名
        のtupleを持つリスト。
        
        Args:
            srcNode (node.AbstractNode):操作対象ノード
            
        Returns:
            list:(animCrvAttr, connectedNodeAttr, connectedAttrName)
    """
    crv_ptn = re.compile('T[ALTU]$')
    buffer = srcNode.sources(type='animCurve', p=True, c=True)
    anim_plugs = []
    for i in range(0, len(buffer), 2):
        crv = buffer[i+1]
        if not crv_ptn.search(crv.node().type()):
            continue
        anim_plugs.append((buffer[i+1], buffer[i], buffer[i].attrName()))
    return anim_plugs


def listFlatAnimCurves(srcNode):
    r"""
        引数srcNodeに接続されたアニメーションカーブのうち、キーフレームが
        変動していないアニメーションカーブのリストを返す。
        戻り値は
            アニメーションカーブノード名
            アニメーションカーブの出力アトリビュート
            srcNodeのアニメーションアトリビュート
            srcNodeのアニメーションアトリビュート名
        のtupleを持つリスト。
        
        Args:
            srcNode (node.AbstractNode):操作対象ノード
            
        Returns:
            list:
    """
    results = []
    for crv_attr, attr, attrName in listAnimPlugs(srcNode):
        crv = crv_attr.nodeName()
        values = list(set(cmds.keyframe(crv, q=True, vc=True) or []))
        if len(values) == 1:
            results.append((crv, crv_attr, attr, attrName))
    return results


def deleteFlatAnimCurves(nodelist=None):
    r"""
        引数nodelistで指定したノードのうち、アニメーションが変動していない
        アトリビュートのアニメーションを削除する。

        Args:
            nodelist (list):
    """
    nodelist = node.selected(nodelist)
    deleting_curves = []
    for n in nodelist:
        deleting_curves.extend([x[0] for x in listFlatAnimCurves(n)])
    if not deleting_curves:
        return
    cmds.delete(deleting_curves)


def transferAnimation(nodelist=None, move=True, checkAllAttr=True):
    r"""
        引数nodelistの最後のノードのアニメーションをそれ以外のノードに移植する。
        引数checkAllAttrがTrueの場合、移植元のアトリビュートと同じ
        アトリビュートが存在しない場合は移植をスキップする。
        引数moveがTrueの場合、引数nodelistは移植先と移植元の２つだけを指定する。
        
        Args:
            nodelist (list):操作対象となるノード名のリスト（２つ以上）
            move (bool):アニメーションを移動する場合するかどうか
            checkAllAttr (bool):
            
        Returns:
            list:移植されたノードの一覧
    """
    nodelist = node.selected(nodelist)
    if (move and len(nodelist) != 2) or (not move and len(nodelist) < 2):
        raise ValueError('Must select at least more than 2 nodes.')
    src = nodelist[-1]
    anim_plugs = listAnimPlugs(src)
    transfered = []
    for dst in nodelist[:-1]:
        if checkAllAttr:
            invalid_attrs = []
            for a in anim_plugs:
                if not dst.hasAttr(a[-1]):
                    invalid_attrs.append(a[-1])
            if invalid_attrs:
                print(
                    (
                        '[WARNING] target node "{}" does not match a '
                        'following attrs.'
                    ).format(dst)
                )
                for attr in invalid_attrs:
                    print('  -> {}'.format(attr))
                break
        for anim_plug, target_attr, attr in anim_plugs:
            if not checkAllAttr and not dst.hasAttr(attr):
                continue
            anim_plug >> dst.attr(attr)
        transfered.append(dst)
        if move:
            for attr in anim_plugs:
                attr[1].disconnect(True)
            return transfered
    return transfered


