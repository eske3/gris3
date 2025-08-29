#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    任意の階層内のTransformノードがフリーズされているかどうかをチェックする
    
    Dates:
        date:2024/06/07 13:46 Eske Yoshinob[eske3g@gmail.com]
        update:2025/08/29 12:26 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import checkUtil
from ... import node


class TransformChecker(checkUtil.GroupMemberChecker):
    DefaultTargets = ['all_grp']

    def __init__(self):
        super(TransformChecker, self).__init__()
        self.setCategory('Transform checker')
        self.setTargets(self.DefaultTargets)
        self.__matrix_error_level = checkUtil.CheckedResult.Error
        self.__pivot_error_level = checkUtil.CheckedResult.Error

    def setMatrixErrorLevel(self, level):
        r"""
            行列チェックの結果のエラーレベルを設定する。

            Args:
                level (int):
        """
        self.__matrix_error_level = level

    def matrixErrorLevel(self):
        r"""
            設定された行列チェックの結果のエラーレベルを返す。

            Returns:
                int:
        """
        return self.__matrix_error_level

    def setPivotErrorLevel(self, level):
        r"""
            ピボットチェックの結果のエラーレベルを設定する。

            Args:
                level (int):
        """
        self.__pivot_error_level = level

    def pivotErrorLevel(self):
        r"""
            設定されたピボットチェックの結果のエラーレベルを返す。

            Returns:
                int:
        """
        return self.__pivot_error_level

    def checkObject(self, target):
        r"""
            Args:
                target (node.AbstractNode):
        """
        checked = []
        target = node.asObject(target)
        if not target.isType('transform'):
            return []

        # フリーズしているかどうかのチェック。
        for s_elm, d_elm in zip(target.matrix(False), node.identityMatrix()):
            if s_elm == d_elm:
                continue
            checked.append(
                checkUtil.CheckedResult(
                    'Unfreezed transformation node.',
                    self.matrixErrorLevel()
                )
            )
            break
        for attr in (
            'rotatePivot', 'scalePivot',
            'rotatePivotTranslate', 'scalePivotTranslate'
        ):
            for val in target(attr)[0]:
                if val != 0:
                    break
            else:
                continue
            checked.append(
                checkUtil.CheckedResult(
                    '{} is not reset.'.format(attr),
                    self.pivotErrorLevel()
                )
            )
            break
        return checked

