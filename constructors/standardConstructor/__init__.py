# -*- coding: utf-8 -*-
r'''
    @file     __init__.py
    @brief    ここに説明文を記入
    @class    Constructor : ここに説明文を記入
    @function relayoutForLow : joint_grp下にあるベースジョイントに親子付されたメッシュを
    @date        2017/01/22 0:11[Eske](eske3g@gmail.com)
    @update      2017/06/30 7:15[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
import re
from gris3 import constructors, node

def relayoutForLow():
    r'''
        @brief  joint_grp下にあるベースジョイントに親子付されたメッシュを
        @brief  セットアップ用にリネームしてall_grp下に再配置する。
        @return None
    '''
    from gris3 import grisNode, core
    root = grisNode.getGrisRoot()
    if not root:
        raise RuntimeError('No gris root node was not in the current scene.')

    try:
        all_grp = grisNode.ModelAllGroup(grisNode.ModelAllGroup.BasicName)
    except:
        all_grp = core.createModelRoot()

    geometries = []
    for jnt in root.baseJointGroup().allChildren():
        if not jnt.hasChild():
            continue
        for geo in jnt.children():
            shapes = geo.children(type=('mesh', 'nurbsSurface'))
            if not shapes:
                continue
            geo.rename(jnt+'_geo#')
            geometries.append(geo)
    all_grp.addChild(*geometries)

class Constructor(constructors.BasicConstructor):
    r'''
        @brief       一般用途のスタンダードなコンストラクタ。
        @inheritance constructors.BasicConstructor
        @date        2017/06/23 21:46[Eske](eske3g@gmail.com)
        @update      2017/06/30 7:15[Eske](eske3g@gmail.com)
    '''
    LowLodName = 'low'
    def parentLowModelToJoint(self):
        r'''
            @brief  ローモデルをベースジョイントへペアレントする
            @return None
        '''
        # ロー用のDisplayセットを作成し登録する。==============================
        lod_dsp_set = self.lodDisplaySet(self.LowLodName)
        self.connectDisplayCtrlToSet(self.LowLodName, True)
        # lod_dsp_set.addChild(all_grp)
        # =====================================================================

        model_grp = node.asObject(self.ModelGroupName)
        if not model_grp:
            self.importModels(lod=self.LowLodName)
            model_grp = node.asObject(self.ModelGroupName)
        if not model_grp:
            return

        joint_name_ptn = re.compile('(.+)_geo\d*$')
        for mesh in model_grp.allChildren(type='transform'):
            r = joint_name_ptn.match(mesh)
            if not r:
                continue
            joint = node.asObject(r.group(1))
            if not joint:
                continue
            joint.addChild(mesh)
            lod_dsp_set.addChild(mesh)

    def setupModelGroup(self):
        r'''
            @brief  モデルの読み込み処理のオーバーライド。
            @return None
        '''
        if self.lod() == self.LowLodName:
            from gris3 import grisNode
            from gris3.tools import cleanup
            try:
                all_grp = grisNode.ModelAllGroup(self.ModelGroupName)
            except Exception as e:
                raise e
            cleanup.deleteAllDisplayLayers()
            mdlset = all_grp.modelAllSet()
            if mdlset:
                mdlset.delete()
            return
        super(Constructor, self).setupModelGroup()

    def postProcess(self):
        self.parentLowModelToJoint()
        super(Constructor, self).postProcess()
        