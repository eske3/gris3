#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    hand_jnt_L(R)以下で、handモジュールに属するジョイントのインバーススケールの
    効果をOFFにする機能を提供する。
    
    Dates:
        date:2017/02/25 13:10[Eske](eske3g@gmail.com)
        update:2021/08/18 06:19 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import extraConstructor, func

class ExtraConstructor(extraConstructor.ExtraConstructor):
    def _setupSystem(self):
        self.hands = []
        for s in func.SuffixIter():
            hand = func.asObject('hand_jnt'*s)
            self.hands.append(hand)
            # 指のスケール設定。
            fingers = hand.children(type='joint')
            for joint in fingers:
                joint('ssc', 0)

    def setupSystem(self):
        for hand in self.hands:
            attr = hand.attr('message')
            attrs = attr.destinations(p=True, type='joint')
            tgt_joint = None
            for attr in attrs:
                if attr.attrName() == 'baseSkeleton':
                    tgt_joint = func.asObject(attr.nodeName())
                    break
            else:
                continue
            ~hand.attr('s') >> ~tgt_joint.attr('s')
