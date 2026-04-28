#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    標準的な人型のリグを作成するプリセット。

    Dates:
        date:2017/02/01 1:01[Eske](eske3g@gmail.com)
        update:2023/01/24 11:12 Eske Yoshinob[eske3g@gmail.com]

    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import rigScripts, node


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