#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2021/08/16 21:46 eske yoshinob[eske3g@gmail.com]
        update:2021/08/16 21:50 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2021 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import node
cmds = node.cmds

def keyAllBlendShapeTargets(blendShapeName, startFrame=0, step=20):
    r"""
        任意のブレンドシェイプのターゲットを一つずつ０～１～０のアニメーションを
        つける関数。
        ブレンドシェイプのチェック用などに便利。
        
        Args:
            blendShapeName (str):対象となるブレンドシェイプ名
            startFrame (float):アニメーション開始フレーム
            step (float):各ターゲット間のアニメーションフレーム数
    """
    bs = node.BlendShape(blendShapeName)
    attrs = bs.listWeightAttr()
    num = len(attrs)
    cmds.playbackOptions(min=startFrame, max=startFrame+num*step)
    for i in range(num):
        cur = startFrame+i*step
        cmds.cutKey(attrs[i], cl=True)
        cmds.setKeyframe(attrs[i], v=0, t=cur)
        cmds.setKeyframe(attrs[i], v=1, t=cur+step)
        cmds.setKeyframe(attrs[i], v=0, t=cur+step*2)

def deleteAllBlendShapeTargetAnims(blendShapeName):
    r"""
        ブレンドシェイプのアニメーションをすべて削除する。

        Args:
            blendShapeName (str):対象となるブレンドシェイプ名
    """
    bs = node.BlendShape(blendShapeName)
    attrs = bs.listWeightAttr()
    for attr in attrs:
        cmds.cutKey(attr, cl=True)
        attr.set(0)
# keyAllBlendShapeTargets('facial_bs')