#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2021/04/15 09:26 eske yoshinob[eske3g@gmail.com]
        update:2022/01/29 18:13 noriyoshi tsujimoto[tensoftware@hotmail.co.jp]
        
    License:
        Copyright 2021 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import node
cmds = node.cmds

def bridgePipe(srcFace=None, dstFace=None, divisions=3):
    r"""
        2つのポリゴンフェースをブリッジする。
        ブリッジする際、2つのフェースにpolyMoveComponentを追加し、距離の調整を
        行えるようにするアトリビュートを追加する。
        
        Args:
            srcFace (str):
            dstFace (str):
            divisions (any):
    """
    # フェースが２つ指定されているかどうかのチェック。=========================
    if not srcFace or not dstFace:
        faces = cmds.filterExpand(sm=34) or []
        if not srcFace and not dstFace:
            if len(faces) < 2:
                raise RuntimeError('Specify 2 faces.')
            srcFace, dstFace = faces[:2]
        else:
            is_valid = len(faces) > 1
            if not srcFace:
                if is_valid:
                    raise RuntimeError('Specify source face.')
                srcFace = faces[0]
            elif not dstFace:
                if is_valid:
                    raise RuntimeError('Specify destination face.')
                srcFace = faces[1]
    # =========================================================================

    for face in faces:
        cmds.polyMoveFacet(face, ch=1, random=0)

    movers = [
        node.asObject(cmds.polyMoveFacet(x, ch=True, random=0)[0])
        for x in (srcFace, dstFace)
    ]
    edges = cmds.polyListComponentConversion(srcFace, dstFace, ff=True, te=True)
    tmpset = cmds.sets(edges, n='tempEdgeSet')
    cmds.delete(srcFace, dstFace)
    
    bridge = node.asObject(
        cmds.polyBridgeEdge(
            cmds.sets(tmpset, q=True),
            ch=True, divisions=divisions,
            twist=0, taper=1, curveType=1, smoothingAngle=30, direction=0,
            sourceDirection=0, targetDirection=0
        )[0]
    )
    cmds.delete(tmpset)
    del_cmp = bridge.attr('inputPolymesh').source(type='deleteComponent')
    if del_cmp:
        del_cmp('ihi', 0)

    for pfx, mover in zip(('src', 'dst'), movers):
        plug = bridge.addFloatAttr(
            '%sPosition'%pfx, min=None, max=None, default=0
        )
        mover('ihi', 0)
        plug >> mover/'localTranslateZ'
    cmds.select(bridge, addFirst=True)
    


def duplicateOnCurve(
    target, distance, curves=None,
    aimVector=[1, 0, 0], upVector=[1, 0, 0],
    targetUpVector=[0, 1, 0],
    startOffset=0
):
    r"""
        ベータ版。

        Args:
            target (str):
            distance (float):
            curves (list):
            aimVector (list):
            upVector (list):
            targetUpVector (list):
            startOffset (float):
    """
    curves = node.selected(curves, type=['nurbsCurve', 'transform'])
    results = []
    cst = node.createNode('orientConstraint')
    for crv in node.selected():
        if crv.isType('transform'):
            shapes = crv.shapes(typ='nurbsCurve')
            if not shapes:
                continue
            crv = shapes[0]
        l = crv.length() - startOffset
        num = int(float(l) / distance) + 1
        for i in range(num):
            p = startOffset + distance * i
            param = crv.findParam(p)
            pos = crv.point(param)
            t = crv.tangent(param)

            mtx = node.identityMatrix()
            mtx[0:3] = t
            t = node.MVector(*t).normal()
            z_vec = (t ^ node.MVector(targetUpVector)).normal()
            mtx[8:11] = list(z_vec)
            mtx[4:7] = list((z_vec ^ t).normal())
            mtx[12:15] = pos
            
            geo = node.duplicate(target)[0]
            geo.setPosition(pos)
            cst('tg[0].tpm', mtx, type='matrix')
            cst('cro', geo('ro'))
            cst('cpim', geo('pim'), type='matrix')
            if geo.isType('joint'):
                cst('cjo', geo('jo'))
            geo('r', cst('cr')[0])
            results.append(geo)
    cmds.delete(cst)
    if results:
        cmds.select(results)
    return results
