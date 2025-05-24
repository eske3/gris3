# -*- coding: utf-8 -*-
r'''
    @file     subdivSmoothSetting.py
    @brief    モデルのsubudiv_setに対してsmoothMeshPreviewの処理を追加する
    @class    ExtraConstructor : smoothMeshPreview処理を追加する
    @date        2017/02/25 13:10[Eske](eske3g@gmail.com)
    @update      2019/02/06 16:42[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
from gris3 import extraConstructor, node
cmds = node.cmds

class ExtraConstructor(extraConstructor.ExtraConstructor):
    r'''
        @brief       smoothMeshPreview処理を追加する
        @inheritance extraConstructor.ExtraConstructor
        @date        2017/02/25 13:10[Eske](eske3g@gmail.com)
        @update      2019/02/06 16:42[Eske](eske3g@gmail.com)
    '''
    SetName = 'subdiv_set'
    PreviewLevel = 0
    RenderSmoothLevel = 2
    def postProcess(self):
        r'''
            @brief  後処理時に実行。
            @return None
        '''
        def setSubdivSetting(mesh):
            print('Set subdivision setting : %s' % mesh)
            mesh('dsm', 2)
            mesh('lev', self.PreviewLevel)
            mesh('uspr', False)
            mesh('rsl', self.RenderSmoothLevel)

        cst = self.constructor()

        model_grp = cst.modelGroup()
        extra_grp = [
            getattr(model_grp, x)() for x in ('rigDataGroup', 'renderDataGroup')
        ]
        children = [
            x for x in model_grp.children(type='transform') if not x in extra_grp
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
        for mesh in subdiv_nodes:
            setSubdivSetting(mesh)
        subdiv_set.delete()