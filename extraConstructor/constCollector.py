#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ctrl_grp内に存在するコントローラーグループ内にあるコンストレインをすべて
    rig_grp内に収集する。
    
    installExtraConstructorで返ってくるインスタンスでは以下の設定が可能。
    ConstGroupName : コンストレインを格納するグループ名
    addNodeFilter(*function):判別用フィルタ関数を追加する。
    removeNodeFilter(*function):判別用フィルタ関すを削除する。
    useDefault(bool) : デフォルトのフィルタ（コンストレインだけを取得）を使用するかどうか
    
    Dates:
        date:2017/02/25 13:10[Eske](eske3g@gmail.com)
        update:2021/08/03 10:07 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import extraConstructor, node, func
cmds = node.cmds


class ExtraConstructor(extraConstructor.ExtraConstructor):
    ConstGroupName = 'ctrlCst_grp'
    def __init__(self, const):
        r"""
            Args:
                const (constructors.Constructor):
        """
        super(ExtraConstructor, self).__init__(const)
        self.__node_filters = []
        self.__use_default = True

    def defaultFilter(self, target):
        r"""
            対象ノードがコンストレインかどうかを返す。
            デフォルトのフィルタ関数。
            
            Args:
                target (node.Transform):
                
            Returns:
                bool :対象ノードがコンストレインかどうか
        """
        return bool(cmds.ls(target, type='constraint'))

    def useDefault(self, state):
        r"""
            デフォルトのフィルタ関数を使用するかどうかを設定する。

            Args:
                state (bool):
        """
        self.__use_default = bool(state)

    def addNodeFilter(self, *func):
        r"""
            任意のフィルタ関数を追加する。
            追加する関数の第一引数にノード名を受け取る必要がある。
            また、戻り値として第一引数に渡されたノードの可否をBoolで返す。
            
            Args:
                *func (function):
        """
        self.__node_filters.expand(func)

    def removeNodeFilter(self, *func):
        r"""
            任意のフィルタ関数を削除する
            
            Args:
                *func (function):削除したい関数オブジェクト
                
            Returns:
                int :削除した関数の数
        """
        cnt = 0
        for f in func:
            if f not in self.__node_filters:
                continue
            idx = self.__node_filters.index(f)
            del self.__node_filters[idx]
            cnt += 1
        return cnt

    def nodeFilters(self):
        r"""
            セットされているフィルタ関数のリストを返す。
            useDefaultをFalseに設定した場合、defaultFilterを含まないリストを
            返す。

            Returns:
                list : 関数のリスト
        """
        if self.__use_default:
            return self.__node_filters + [self.defaultFilter]
        else:
            return self.__node_filters[:]
            

    def doit(self, targetNodes):
        r"""
            Args:
                targetNodes (any):
        """
        cst = self.constructor()
        rig_group = cst.rigGroup()
        cst_grp = [
            x for x in rig_group.children()
            if x.shortName()==self.ConstGroupName
        ]
        if cst_grp:
            cst_grp = cst_grp[0]
        else:
            cst_grp = node.createNode(
                'transform', n=self.ConstGroupName, p=rig_group
            )
            cst_grp.lockTransform()
        if targetNodes:
            cmds.parent(targetNodes, cst_grp)

    def postProcess(self):
        r"""
            セットアップ後、ポスト処理後に実行されるメソッド
        """
        filters = self.nodeFilters()
        cst = self.constructor()
        ctrl_top = cst.ctrlTop()
        targets = []
        for ctrl in ctrl_top.allChildren():
            for f in filters:
                if f(ctrl):
                    targets.append(ctrl)
                    break
        self.doit(targets)
