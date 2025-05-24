#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ペイントウェイトに関する便利関数集。
    
    Dates:
        date:2017/09/14 4:53[Eske](eske3g@gmail.com)
        update:2022/12/22 13:57 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import node
from maya import mel
cmds = node.cmds
ART_CTX = 'artAttrSkinContext'      # ペイントツールのコンテキスト名
OPERATIONS = {
    'replace':'absolute',
    'add':'additive',
    'remove':'remove',
    'scale':'scale',
    'smooth':'smooth'
}

def listSkinnedNode(skinCluster):
    r"""
        Args:
            skinCluster (node.SkinCluster):
        
        Returns:
            node.DagNode: 
    """
    TargetType = ['mesh', 'nurbsSurface', 'nurbsCurve']
    targets = skinCluster.attr('outputGeometry[0]').destinations(sh=True)
    if not targets:
        return
    searched = set()
    while True:
        new_targets = []
        if not targets:
            return
        for target in targets:
            if target.type() in TargetType:
                return target
            searched.add(target)
            new_targets.extend(target.destinations(sh=True))
        targets = set(new_targets) - searched


def selectBindedSkin(skinCluster):
    r"""
        現在選択されているノードが、skinClusterのインフルエンスの場合
        skinClusterによってバインドされているノードを選択する。
        
        Args:
            skinCluster (str):スキンクラスタ名
            
        Returns:
            node.AbstractNode:選択されていたインフルエンス名
    """
    selected = node.selected(type='transform')
    if not selected:
        return
    inf = selected[0]
    if not inf.hasAttr('worldMatrix'):
        return
    sclist = inf.attr('worldMatrix[0]').destinations()
    if not sclist:
        return
    if skinCluster not in sclist:
        return
    skinned = listSkinnedNode(skinCluster)
    if not skinned:
        return

    cmds.select(skinned, r=True, ne=True)
    return inf


def runPaintSkinTool(skinCluster=None):
    r"""
        PaintSkinWeightToolを起動するラッパー関数。
        引き数skinClusterにskinCluster名が指定されている状態でツール起動時に
        インフルエンスが選択されていると、skinClusterが影響を与えている
        シェイプを選択する。
        
        Args:
            skinCluster (str):
    """
    if cmds.currentCtx(q=True) != ART_CTX:
        mel.eval('ArtPaintSkinWeightsTool;')
    if not skinCluster:
        return
    inf = selectBindedSkin(skinCluster)
    if inf:
        mel.eval('setSmoothSkinInfluence {}'.format(inf))


def changeOperationOpacity(operation, value, skinCluster=None):
    r"""
        paintSkinを起動し、その後引数operationに切り替えてopacityの値を
        引数valueへ変更する。
        
        Args:
            operation (str):オペレーション
            value (gloat):opacityの値
            skinCluster (str):スキンクラスタ名
    """
    if not operation in OPERATIONS:
        return
    runPaintSkinTool(skinCluster)
    cmds.artAttrSkinPaintCtx(ART_CTX, e=True, opacity=value)
    cmds.artAttrSkinPaintCtx(
        ART_CTX, e=True, selectedattroper=OPERATIONS[operation]
    )


def getOperationOpacity(operation, skinCluster=None):
    r"""
        paintSkinを起動し、operationに切り替えてから現在のopacityを返す
        
        Args:
            operation (str):オペレーション
            skinCluster (str):スキンクラスタ名
            
        Returns:
            str:
    """
    if not operation in OPERATIONS:
        return
    runPaintSkinTool(skinCluster)
    cmds.artAttrSkinPaintCtx(
        ART_CTX, e=True, selectedattroper=OPERATIONS[operation]
    )
    return cmds.artAttrSkinPaintCtx(ART_CTX, q=True, opacity=True)


def changeValue(value, skinCluster=None):
    r"""
        paintSkinを起動し、その後valueを引数valueへ変更する。
        
        Args:
            value (float):valueの値
            skinCluster (str):スキンクラスター名
    """
    runPaintSkinTool(skinCluster)
    cmds.artAttrSkinPaintCtx(ART_CTX, e=True, minvalue=-1)
    cmds.artAttrSkinPaintCtx(ART_CTX, e=True, value=value)
    

def hummberWeigt():
    r"""
        HummerToolを実行するラッパー関数。
    """
    mel.eval('weightHammerVerts;')