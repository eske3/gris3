#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    任意ノードのアトリビュートに設定されている外部参照ファイルが存在するか
    どうかをチェックする。
    
    Dates:
        date:2024/06/24 13:04 Eske Yoshinob[eske3g@gmail.com]
        update:2024/06/24 17:30 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
from .. import checkUtil
from ... import node, verutil
cmds = node.cmds


class FilePathChecker(checkUtil.AbstractAssetChecker):
    r"""
        任意ノードのアトリビュートに設定されている外部参照ファイルが存在するか
        どうかをチェックする機能を提供するクラス。
    """
    def setTargets(self, targetlist):
        r"""
            チェック対象となるノードのタイプと、参照するアトリビュートを設定する。
            引数targetlistには
            (nodeType : str, attribute : str)
            の形式のtupleを格納したリストを渡す。
            
            Args:
                targetlist (tuple or list):
        """
        for target in targetlist:
            if not isinstance(target, (tuple, list)) and len(target) != 2:
                raise AttributeError(
                    (
                        'The target elements must be type "list" that '
                        'has node type and attribute name.'
                    )
                )
        super(FilePathChecker, self).setTargets(targetlist)


    def targets(self, convertObject=False):
        r"""
            targetsのオーバーライド。covnertObjectフラグを強制的にOFFにして
            返す。
            
            Args:
                convertObject (bool):
        """
        return super(FilePathChecker, self).targets(False)
        

    def checkObject(self, target, attr):
        r"""
            任意のノードのチェックを行う。
            引数attrのアトリビュートの値を取得し、その値がファイルパスとして
            存在しているかを確認する。
            attrの値がstr以外であれば無条件にスルーする。
            
            Args:
                target (node.AbstractNode):
                attr (str):
                
            Returns:
                checkUtil.CheckedResult:
        """
        filepath = target(attr)
        if not isinstance(filepath, verutil.BaseString):
            return
        if os.path.exists(filepath):
            return
        return [
            checkUtil.CheckedResult(
                'The file "{}" does not exist.'.format(filepath)
            )
        ]

    def search(self, target):
        r"""
            シーン中に存在する任意のノードタイプをすべて調査する。
            
            Args:
                target (tuple or list):
                
            Returns:
                list:
        """
        result = []
        n_type, attr = target
        for n in node.ls(type=n_type):
            checked = self.checkObject(n, attr)
            if checked:
                result.append((n(), checked))
        return result