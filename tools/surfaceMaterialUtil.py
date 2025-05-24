#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    マテリアルに関するアクセス等を行うための機能を提供するモジュール。
    
    Dates:
        date:2018/03/29 10:12[Eske](eske3g@gmail.com)
        update:2021/03/28 19:06 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2018 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import node
cmds = node.cmds

def listMaterials(nodelist=None):
    r"""
        選択オブジェクトがアサインされているマテリアルを返す。
        戻り値はマテリアルのリストとマテリアルがアサインされているノード
        のリストを持つタプル。
        
        Args:
            nodelist (list):
            
        Returns:
            tuple:
    """
    nodelist = node.selected(nodelist)
    if not nodelist:
        return []
    materials = []
    for n in nodelist:
        setlist = cmds.listSets(ets=True, type=1, object=n)
        if not setlist:
            continue
        sgs = node.ls(setlist, type='shadingEngine')
        for sg in sgs:
            matlist = node.ls(sg.sources(), mat=True)
            for mat in matlist:
                if mat in materials:
                    continue
                materials.append(mat)
    return materials, nodelist


def assignMaterialToSelected(material, assignTo=None):
    r"""
        materialをassignToへアサインする関数。
        
        Args:
            material (str):アサインするマテリアル
            assignTo (list):アサインされるノードのリスト
    """
    assignTo = assignTo or cmds.ls(sl=True)
    if not assignTo:
        return
    sgs = cmds.listConnections(material, s=False, d=True, type='shadingEngine')
    if not sgs:
        return
    cmds.sets(assignTo, e=True, forceElement=sgs[0])


def listMaterialMembers(materials, nodelist):
    r"""
        materialsのメンバーかつnodelistに属するオブジェクトを返す。
        
        Args:
            materials (list):マテリアルのリスト
            nodelist (list):操作対象ノードのリスト(Transformノードのみ）
            
        Returns:
            list:
    """
    shapelist = []
    for trs in node.toObjects(nodelist):
        if '.f[' in trs:
            shapelist.extend(cmds.listRelatives(trs, p=True) or [])
            continue
        if not trs or not trs.hasChild():
            continue
        meshes = trs.shapes(typ='mesh')
        if meshes:
            shapelist.extend(meshes)
    nodelist = list(set(nodelist + shapelist))
    if not shapelist:
        return []

    materials = node.toObjects(materials)
    members = []
    for mat in materials:
        sglist = mat.attr('outColor').destinations(type='shadingEngine')
        for sg in sglist:
            shapes = sg.children()
            members.extend(shapes)
    members = list(set(members))

    selections = []
    for m in members:
        elements = m.split('.')
        if elements[0] in nodelist:
            selections.append(m)
    return selections

