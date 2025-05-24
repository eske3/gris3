#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    任意の階層内のメッシュのポリゴン数に関する情報をチェックする。
    
    Dates:
        date:2024/06/07 13:46 Eske Yoshinob[eske3g@gmail.com]
        update:2024/06/07 21:25 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import checkUtil, cleanup
from ... import node
cmds = node.cmds


def errorLevel(count, goalCount, limitCount):
    r"""
        引数countのポリゴン数が、goalCountとlimitCount内のなかでどれくらいの
        エラー度化を浮動少数型の数値で返す。
        限界値であるlimitCountに近づくほど１に近い数値になり、超えるポリゴン数の
        場合は戻り値は１を超える。
        goalCount以下の場合は0を返す。

        Args:
            count (int): エラーレベルを図るポリゴン数
            goalCount (int): 設定されたポリゴン数の上限
            limitCount (int): 設定されたポリゴン数の限界値

        Returns:
            float:
    """
    if not count or not goalCount or not limitCount:
        return 0.0
    if count <= goalCount:
        return 0.0
    return (count - goalCount) / (limitCount - goalCount)


class PolyCountChecker(checkUtil.REBasedDagNameChecker):
    def __init__(self):
        super(PolyCountChecker, self).__init__()
        self.setCategory('Poly count checker')
        self.__error_level = 0
        self.__total_count = 0
        self.__goal_count = None
        self.__limit_count = None

    def setGoalCount(self, size=None):
        r"""
            目標ポリゴン数を設定する。

            Args:
                size (int):
        """
        self.__goal_count = size

    def goalCount(self):
        r"""
            設定された目標ポリゴン数を返す。

            Return:
                int:
        """
        return self.__goal_count

    def setLimitCount(self, size=None):
        r"""
            限界ポリゴン数を設定する。

            Args:
                size (int):
        """
        self.__limit_count = size

    def limitCount(self):
        r"""
            設定された限界ポリゴン数を返す。

            Return:
                int:
        """
        return self.__limit_count

    def setTotalCount(self, count):
        r"""
            checkを行った結果のトータルポリゴン数を設定する。（内部使用専用）

            Args:
                count (int):
        """
        self.__total_count = count

    def totalCount(self):
        r"""
            checkを行った結果のトータルポリゴン数を返す。

            Returns:
                int:
        """
        return self.__total_count

    def setErrorLevel(self, level=0):
        r"""
            checkを行った結果のトータルポリゴン数のエラーレベルを設定する
            （内部使用専用）

            Args:
                level (float):
        """
        self.__error_level = level

    def errorLevel(self):
        r"""
            checkを行った結果のトータルポリゴン数のエラーレベルを返す。

            Returns:
                float:
        """
        return self.__error_level

    def checkObject(self, target):
        r"""
            Args:
                target (node.Transform):
        """
        checked = []
        target = node.asObject(target)
        if not hasattr(target, 'children'):
            return []
        num_tri = -1
        for mesh in target.children(type='mesh'):
            if mesh('io'):
                continue
            num_tri = cmds.polyEvaluate(mesh, t=True)
            continue
        if num_tri < 1:
            return []
        checked.append(
            checkUtil.CheckedResult(numFaces=num_tri)
        )
        return checked
    
    def check(self):
        result = super(PolyCountChecker, self).check()
        poly_counts = []
        for r in result:
            poly_counts.append(r[1][0].numFaces)
        total_counts = sum(poly_counts)
        self.setTotalCount(total_counts)
        self.setErrorLevel(
            errorLevel(total_counts, self.goalCount(), self.limitCount())
        )
        
        return result

