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
from ... import node, mathlib
cmds = node.cmds


class SkinWeightDecimalChecker(checkUtil.AbstractDagChecker):
    def __init__(self):
        super(SkinWeightDecimalChecker, self).__init__()
        self.setCategory('Skin Weight Decimal Checker')
        self.__decimal = 2
    
    def setNumberOfDecimal(self, limit):
        self.__decimal = int(limit)

    def numberOfDecimal(self):
        return self.__decimal

    def checkObject(self, target):
        r"""
            Args:
                target (node.Transform):
        """
        checked = []
        if target is None:
            return checked

        if not target.isType('transform'):
            return checked
        meshs = [x for x in target.children(type='mesh') if not x('io')]
        if not meshs:
            return checked

        weightlist = skinUtility.listWeightValues(target)
        if not weightlist:
            return checked

        decimal = self.numberOfDecimal()
        limit_error, zero_error = False, False
        for idx, wlist in enumerate(weightlist):
            for w in wlist:
                if mathlib.getNumberOfDecimals(w) > decimal:
                    checked.append(
                        checkUtil.CheckedResult(
                            (
                                'This mesh contains skinning weights '
                                'with more than {} decimal places.'
                            ).format(decimal),
                            processId=1
                        )
                    )
                    return checked
        return checked

