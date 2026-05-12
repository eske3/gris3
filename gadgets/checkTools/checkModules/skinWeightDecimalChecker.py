#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    スキニングされたポリゴンの各頂点のインフルエンス数が既定値を超えて
    いないかをチェックする。

    checkToolの設定jsonファイルで使用できるオプションは以下の通り。
    {
        "moduleName": "skinWeightDecimalChecker",
        "modulePrefix": "-default",
        "options": {
            "target": ["チェック対象グループ名"...],
            "numberOfDecimal": 2
        }
    }

    Dates:
        date:2024/06/27 17:33 Eske Yoshinob[eske3g@gmail.com]
        update:2024/06/27 17:33 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from ....tools import skinUtility
from ....tools.sceneChecker import skinWeightDecimalChecker
from . import genericCheckerBase, skinInfluenceChecker


class ErrorVertexSelector(skinInfluenceChecker.AbstractVertexSelector):
    def __init__(self, parent=None):
        super(ErrorVertexSelector, self).__init__(parent)
        self.__number_of_decimal = 2

    def setNumberOfDecimal(self, decimal):
        self.__number_of_decimal = decimal

    def numberOfDecimal(self):
        return self.__number_of_decimal

    def label(self):
        return 'The vertex that contains many decimal selector'

    def getErroredVertices(self):
        geo = self.target()
        decimal = self.numberOfDecimal()
        return skinUtility.listOverDecimalWeightVertices(geo, decimal, False)


class CategoryOption(genericCheckerBase.GenericCategoryOption):
    Checker = skinWeightDecimalChecker.SkinWeightDecimalChecker

    def  __init__(self):
        super(CategoryOption, self).__init__()
        self.targets = []
        self.number_of_decimal = 2

    def category(self):
        return 'Skin Weight Decimal Checker'

    def buildUI(self, parent):
        super(CategoryOption, self).buildUI(parent)
        self.result_view.addOperatorPage(ErrorVertexSelector(), 1)

    def setOptions(self, **optionData):
        self.targets = optionData.get('target', ['geo_grp'])
        self.number_of_decimal = optionData.get('numberOfDecimal', 2)

    def initChecker(self, checkerTypeObj):
        r"""
            Args:
                checkerTypeObj (type):checkUtil.DataBasedHierarchyChecker
            
            Returns:
                checkUtil.DataBasedHierarchyChecker: 
        """
        obj = checkerTypeObj()
        obj.setTargets(self.targets)
        obj.setNumberOfDecimal(self.number_of_decimal)
        op = self.result_view.operatorPage(1)
        op.setNumberOfDecimal(self.number_of_decimal)
        return obj
