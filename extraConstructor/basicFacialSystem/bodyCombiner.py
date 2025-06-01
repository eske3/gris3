#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    aiToolsのマスターモデルと連動したフェイシャルセットアップを行うための
    ExtraConstructor。
    
    Dates:
        date:2017/02/25 13:10[Eske](eske3g@gmail.com)
        update:2021/08/18 05:49 noriyoshi tsujimoto[tensoftware@hotmail.co.jp]
        
    License:
        Copyright 2017 noriyoshi tsujimoto[tensoftware@hotmail.co.jp] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import re
from gris3 import node
from gris3.tools import modelingSupporter
cmds = node.cmds

def combineFace(face, sub_objects, parent):
    ptn = re.compile('\[(\d+)\]')
    def list_pfxtoons(*objectlist):
        result = {}
        for obj in objectlist:
            pfx_toon_plugs = obj.attr('outMesh').destinations(
                type='pfxToon', p=True
            )
            for p in pfx_toon_plugs:
                if 'inputSurface' not in p:
                    continue
                index = ptn.search(p()).group(1)
                pfx_toon = p.nodeName()
                pfx_toon_obj = node.asObject(pfx_toon)
                out_p = pfx_toon_obj.attr('outProfileMesh[{}]'.format(index))
                in_mtx_p = pfx_toon_obj.attr(
                    'inputSurface[{}].inputWorldMatrix'.format(index)
                )
                meshs = out_p.destinations(type='mesh')
                if not  meshs:
                    continue
                cmds.delete(meshs, ch=True)
                result.setdefault(obj, []).append((p, in_mtx_p, out_p, meshs))
                
        return result

    face = node.asObject(face)
    if not face:
        raise RuntimeError(
            '[aiToolsFacialSetup] This scene does not contain a "face_geo".'
        )
    sub_objects = node.toObjects(sub_objects)
    pfx_toons = list_pfxtoons(face, *sub_objects)

    c = modelingSupporter.Combine([face] + sub_objects)
    c.setParent(parent)
    c.setName('bodyAll_geo')
    c.operate()
    tgt_obj = c.object()()

    # 境界エッジを選択し、頂点をマージする。
    cmds.select(tgt_obj+'.e[*]')
    cmds.polySelectConstraint(pp=3)
    borders = cmds.ls(sl=True)
    cmds.polyMergeVertex(borders, d=0.1, am=1, ch=1)
    cmds.polySoftEdge(tgt_obj, a=180, ws=1, ch=0)
    cmds.delete(tgt_obj, ch=True)

    for obj, pfx_toon_plugs in pfx_toons.items():
        attr = tgt_obj+'.outMesh'
        mtx_attr = tgt_obj+'.worldMatrix'
        for in_p, in_mtx_p, out_p, meshs in pfx_toon_plugs:
            if obj != face:
                cmds.delete(meshs)
                continue
            attr >> in_p
            mtx_attr >> in_mtx_p
            for mesh in meshs:
                out_p >> mesh+'.inMesh'
    return tgt_obj

def combineFaceCage(face_cage, sub_objects, parent):
    face_cage = node.asObject(face_cage)
    combined =  modelingSupporter.unitePolygons(
        [face_cage]+sub_objects, 'bodyAll_cage'
    )
    return node.parent(combined, parent)[0]