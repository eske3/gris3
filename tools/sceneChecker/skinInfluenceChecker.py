#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    スキニングされたポリゴンの各頂点のインフルエンス数が既定値を超えて
    いないかをチェックする。

    Dates:
        date:2024/06/27 17:37 Eske Yoshinob[eske3g@gmail.com]
        update:2024/06/27 17:37 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import checkUtil, skinUtility
from ... import node
cmds = node.cmds


class PolySkinInfluenceChecker(checkUtil.AbstractDagChecker):
    def __init__(self):
        super(PolySkinInfluenceChecker, self).__init__()
        self.setCategory('Poly skin influence Checker')
        self.__limit = 4
    
    def setNumberOfLimit(self, limit):
        self.__limit = int(limit)

    def numberOfLimit(self):
        return self.__limit

    def checkObject(self, target):
        r"""
            Args:
                target (node.Transform):
        """
        checked = []
        if not target.isType('transform'):
            return checked
        meshs = [x for x in target.children(type='mesh') if not x('io')]
        if not meshs:
            return checked
        
        weightlist = skinUtility.listWeights(target)
        if not weightlist:
            return checked
        limit = self.numberOfLimit()
        limit_error, zero_error = False, False
        for idx, wlist in weightlist.items():
            if not wlist:
                zero_error = True
            elif len(wlist) > limit:
                limit_error = True
            if zero_error and limit_error:
                break
        if zero_error:
            checked.append(
                checkUtil.CheckedResult(
                    'No weighted vertex was found.', processId=1
                )
            )
        if limit_error:
            checked.append(
                checkUtil.CheckedResult(
                    'Some vertices break a limit about number of influences.',
                    processId=2
                )
            )
        return checked

