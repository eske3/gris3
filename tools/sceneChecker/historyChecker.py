#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    スキニングされたポリゴンの各頂点のインフルエンス数が既定値を超えて
    いないかをチェックする。
    
    Dates:
        date:2024/06/27 17:37 Eske Yoshinob[eske3g@gmail.com]
        update:2024/09/25 11:32 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import checkUtil, modelChecker
from ... import node
cmds = node.cmds


class HistoryChecker(checkUtil.GroupMemberChecker):
    def __init__(self):
        super(HistoryChecker, self).__init__()
        self.setCategory('History Checker')

    def checkIgnoredHistoryNode(self, target, checkedResults):
        r"""
            ヒストリをチェックした結果、無効リストに該当したノードを再度
            検査するためのオーバーライド専用メソッド。

            Args:
                target (node.Transform):
                checkedResults (list):
            
            Returns:
                list: CheckedResultのリスト
        """
        return []
    
    def checkObject(self, target):
        r"""
            Args:
                target (node.Transform):

            Returns:
                list: CheckedResultのリスト
        """
        checked = []
        results = modelChecker.checkHistory([target])
        checked.extend(
            self.checkIgnoredHistoryNode(target, results[target]['ignored'])
        )
        if not results[target]['checked']:
            return checked
        checked.append(
            checkUtil.CheckedResult('Found unsupported history.')
        )
        return checked
