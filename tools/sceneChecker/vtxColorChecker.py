#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    任意のメッシュの頂点カラーの有無をチェックする。
    
    Dates:
        date:2024/06/07 13:46 Eske Yoshinob[eske3g@gmail.com]
        update:2024/06/07 15:21 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import checkUtil, cleanup
from ... import node
cmds = node.cmds


def listColorSets(targetTransform):
    r"""
        Args:
            targetTransform (str):
        
        Returns:
            dict: シェイプ名をキー、カラーセットのリストを値とした辞書
    """
    target = node.asObject(targetTransform)
    if not hasattr(target, 'children'):
        return []
    result = {}
    for mesh in target.children(type='mesh'):
        if mesh('io'):
            continue
        acs = cmds.polyColorSet(mesh, q=True, acs=True)
        if not acs:
            continue
        result[mesh] = acs
    return result


class VtxColorChecker(checkUtil.REBasedDagNameChecker):
    def __init__(self):
        super(VtxColorChecker, self).__init__()
        self.setCategory('Vertex Color Checker')
        self.__level = checkUtil.CheckedResult.Warning

    def setErrorLevel(self, level):
        r"""
            Args:
                level (int):
        """
        self.__level = level

    def errorLevel(self):
        return self.__level

    def checkObject(self, target):
        r"""
            Args:
                target (node.Transform):
        """
        checked = []
        color_sets = listColorSets(target)
        if not color_sets:
            return checked
        for mesh, acs in color_sets.items():
            num = len(acs)
            if num < 2:
                text = ' was'
            else:
                text = 's were'
            checked.append(
                checkUtil.CheckedResult(
                    '[{}] {} color set{} detected.'.format(mesh, num, text),
                    self.errorLevel(), 2
                )
            )
        return checked

