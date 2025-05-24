# -*- coding:utf-8 -*-
r'''
    @file     unityHeadRig.py
    @brief    UNITY用の頭部を作成するための機能を提供するモジュール。
    @class    JointCreator : ここに説明文を記入
    @class    RigCreator : ここに説明文を記入
    @date        2017/02/01 1:04[Eske](eske3g@gmail.com)
    @update      2017/02/01 1:04[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
from gris3 import rigScripts, node

class Preset(rigScripts.Preset):
    def name(self):
        return 'Basic Human'

    def description(self):
        return u'ベーシックな人型のリグプリセット。'

    def includes(self):
        return [
            rigScripts.PresetElement('humanSpineRig', 1),
            rigScripts.PresetElement('humanHeadRig', 1),
            rigScripts.PresetElement('humanClavicleRig', 2),
            rigScripts.PresetElement('humanArmRig', 2),
            rigScripts.PresetElement('humanHandRig', 2),
            rigScripts.PresetElement('humanLegRig', 2),
            rigScripts.PresetElement('humanClavicleRig', 3),
            rigScripts.PresetElement('humanArmRig', 3),
            rigScripts.PresetElement('humanHandRig', 3),
            rigScripts.PresetElement('humanLegRig', 3),
        ]
    def create(self, creators):
        parent = node.selected()
        if not parent:
            parent = self.jointRoot()
        else:
            parent = parent[0]

        # 背骨の作成。
        spine = creators['humanSpineRig-C']
        spine.createBaseJoint(parent)

        # 頭部の作成。
        head = creators['humanHeadRig-C']
        head.createBaseJoint(spine.unit().getMember('spineEnd'))

        for side in ('LR'):
            clv = creators['humanClavicleRig-'+side]
            clv.createBaseJoint(spine.unit().getMember('spineEnd'))
            
            arm = creators['humanArmRig-'+side]
            arm.createBaseJoint(clv.unit().getMember('clavicle'))

            hand = creators['humanHandRig-'+side]
            hand.createBaseJoint(arm.unit().getMember('hand'))

            leg = creators['humanLegRig-'+side]
            leg.createBaseJoint(spine.unit().getMember('hip'))