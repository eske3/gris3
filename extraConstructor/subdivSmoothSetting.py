#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    モデルのsubudiv_setに対してsmoothMeshPreviewの処理を追加する
    
    Dates:
        date:2017/02/25 13:10[Eske](eske3g@gmail.com)
        update:2025/06/01 23:21 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import extraConstructor, node
cmds = node.cmds

class ExtraConstructor(extraConstructor.ExtraConstructor):
    r"""
        smoothMeshPreview処理を追加する
    """
    SetName = 'subdiv_set'
    PreviewLevel = 0
    RenderSmoothLevel = 2
    def postProcess(self):
        r"""
            後処理時に実行。
        """
        def setSubdivSetting(mesh):
            r"""
                Args:
                    mesh (node.Mesh):
            """
            print('Set subdivision setting : %s' % mesh)
            mesh('dsm', 2)
            mesh('lev', self.PreviewLevel)
            mesh('uspr', False)
            mesh('rsl', self.RenderSmoothLevel)

        cst = self.constructor()

        model_grp = cst.modelGroup()
        extra_grp = [
            getattr(model_grp, x)()
            for x in ('rigDataGroup', 'renderDataGroup')
        ]
        children = [
            x for x in model_grp.children(type='transform')
            if not x in extra_grp
        ]
        all_meshes = [
            x for x in
            node.toObjects(cmds.listRelatives(children,ad=True, type='mesh'))
            if x and not x('io')
        ]
        subdiv_set = node.asObject(self.SetName)
        if not subdiv_set:
            for mesh in all_meshes:
                setSubdivSetting(mesh)
            return

        subdiv_nodes = node.toObjects(cmds.sets(subdiv_set, q=True))
        for mesh in all_meshes:
            mesh('dsm', 0)
            mesh('lev', 0)
            mesh('uspr', True)
            mesh('rsl', self.RenderSmoothLevel)
        for sbdv_node in subdiv_nodes:
            if sbdv_node.isType('mesh'):
                meshs = [sbdv_node]
            elif sbdv_node.isSubType('transform'):
                meshs = sbdv_node.allChildren(type='mesh', ni=True)
            else:
                continue
            for mesh in meshs:
                setSubdivSetting(mesh)
        subdiv_set.delete()