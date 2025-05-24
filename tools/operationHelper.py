#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    操作の手助けとなる機能を集めたモジュール。
    表示制御系など、実際にオブジェクトに影響しないものを集めたもの。
    
    Dates:
        date:2018/03/14 4:23[Eske](eske3g@gmail.com)
        update:2023/04/27 14:46 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2018 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from maya import mel
from gris3 import node
from gris3.tools import util
cmds = node.cmds


def setManipAxisToSelected():
    r"""
        選択エッジ（またはフェース）の軸にMoveツールの軸をあわせる。
        同時にScaleツールの軸もセットする。
    """
    selected = cmds.filterExpand(sm=32)
    vector = None
    if selected:
        vtx = cmds.ls(
            cmds.polyListComponentConversion(selected[0], fe=True, tv=True),
            fl=True
       )
        # エッジのベクトルを取得
        pos_a = cmds.pointPosition(vtx[0], w=True)
        pos_b = cmds.pointPosition(vtx[1], w=True)
        vector = [
            x-y for x, y in zip(
                *[cmds.pointPosition(vtx[i], w=True) for i in range(2)]
           )
        ]
    else:
        selected = cmds.filterExpand(sm=34)
        if selected:
            vector = util.getFaceNormal(selected[0])
    if vector:
        cmds.manipMoveContext('Move', e=True, m=6, aa=vector)
        cmds.manipScaleContext('Scale', e=True, m=6, aa=vector)
    else:
        selected = cmds.ls(sl=True, tr=True)
        if not selected:
            from ..uilib import mayaUIlib
            selected = node.asObject(mayaUIlib.getActiveCamera())
            if not selected:
                return
            selected = [selected]
        try:
            cmds.manipMoveContext('Move', e=True, m=6, oo=selected[0])
            cmds.manipScaleContext('Scale', e=True, m=6, oo=selected[0])
        except:
            return
    cmds.refresh(f=True)


def toggleTransformChannel(transforms=None):
    r"""
        Transformアトリビュートのロック/アンロックをトグルする。
        
        Args:
            transforms (list):
    """
    transforms = node.selected(type='transform')
    if not transforms:
        return
    attr = 'unlockTransform'
    for at in [x+y for x in 'trs' for y in 'xyz']:
        if not transforms[-1](at, k=True):
            break
    else:
        attr = 'lockTransform'
    for trs in transforms:
        getattr(trs, attr)()


def toggleWireOnShaded():
    r"""
        モデルパネルのワイヤーフレームシェード状態をトグル切り替えする
        
        Returns:
            bool:
    """
    currentPanel = cmds.getPanel(wf=True)
    state = cmds.modelEditor(currentPanel, q=True, wos=True) == False
    cmds.modelEditor(currentPanel, e=True, wos=state)
    return state


class SelectionMemory(object):
    r"""
        選択オブジェクトのリストを保持する機能を提供するクラス
    """
    def __new__(cls, createNew=False):
        r"""
            シングルトン化を行う。
            
            Args:
                createNew (bool):シングルトンではなく新規で作成する
                
            Returns:
                SelectionMemory:
        """
        if hasattr(cls, '__singletonInstance__') and not createNew:
            return cls.__singletonInstance__
        obj = super(SelectionMemory, cls).__new__(cls)
        obj.__selectionlist = []
        obj.__limit = 10
        cls.__singletonInstance__ = obj
        return obj

    def __add__(self, other):
        r"""
            +演算のオーバーライド。addを実行する
            
            Args:
                other (list):追加するノードのリスト
        """
        self.add(other)

    def __len__(self):
        r"""
            このクラスが保持するリストの数を返す
            
            Returns:
                int:
        """
        return len(self.__selectionlist)

    def __iter__(self):
        r"""
            forループで呼ばれるオーバーライド。
            
            Returns:
                iterator:
        """
        return self.__selectionlist.__iter__()

    def setLimit(self, limit):
        r"""
            保持するリストの数の上限を設定する。
            
            Args:
                limit (int):
        """
        self.__limit = limit

    def limit(self):
        r"""
            保持するリストの数の上限を返す。
            
            Returns:
                int:
        """
        return self.__limit

    def add(self, nodelist=None):
        r"""
            選択ノードのリストを追加する。limitを超えると古いものは破棄
            
            Args:
                nodelist (list):Noneの場合選択ノードのリストを追加
        """
        if not nodelist:
            nodelist = cmds.ls(sl=True)
            if not nodelist:
                return
        self.__selectionlist.append(nodelist)
        limit = self.limit()
        if len(self.__selectionlist) > limit:
            self.__selectionlist = self.__selectionlist[-limit:]

    def clear(self):
        r"""
            リストをクリアする
        """
        self.__selectionlist = []

    def listSelection(self):
        r"""
            保持している選択リストを返す
            
            Returns:
                list:
        """
        return self.__selectionlist[:]

    def __getitem__(self, key):
        r"""
            選択リストの任意の番号のリストを返す。
            
            Args:
                key (int):
                
            Returns:
                list:
        """
        return self.__selectionlist[key]

    def select(self, index=-1, **keywords):
        r"""
            indexで指定した選択リストの内容のオブジェクトを選択する。
            
            Args:
                index (int or tuple):() : 番号または番号のリスト
                **keywords (str):
        """
        if not self.__selectionlist:
            return
        if isinstance(index, int):
            cmds.select(self.__selectionlist[index], **keywords)
            return
        if isinstance(index, (list, tuple)):
            nodelist = []
            for i in index:
                nodelist.extend(self.__selectionlist[i])
            cmds.select(nodelist, **keywords)

# =============================================================================
# 選択状況に応じてツールを自動選択して実行する機能郡                         ==
# =============================================================================
def getSelectedComponentType():
    r"""
        選択コンポーネントの種類を返す。
        
        Returns:
            str:
    """
    for index, key in [
        (34, 'face'), (32, 'edge'), (31, 'vtx'),
        (9, 'curve'), (10, 'surface'), (39, 'param'), (45, 'isoparan'),
    ]:
        if cmds.filterExpand(sm=index):
            return key
 
def switchExtrude(option=False):
    r"""
        コンポーネントに合ったExtrudeを行う。
        
        Args:
            option (bool):オプションを表示するかどうか
    """
    command = {
        'face':'ExtrudeFace', 'edge':'ExtrudeEdge', 'vtx':'ExtrudeVertex',
        'curve':'Extrude',
    }.get(getSelectedComponentType(), 'ExtrudeFace')
    mel.eval(command + ('Options' if option else ''))


def switchSplitObject(option=False):
    r"""
        コンポーネントに合ったExtrudeを行う。
        
        Args:
            option (bool):オプションを表示するかどうか
    """
    command, opt = {
        'param':('InsertKnot', 'Options'),
        'isoparan':('InsertIsoparms', 'Options'),
    }.get(
        getSelectedComponentType(),
        ('setToolTo polySplitContext;', 'toolPropertyWindow')
    )
    
    mel.eval(command + (opt if option else ''))


def switchBevel(option=False):
    r"""
        コンポーネントに合ったBevelを行う。
        
        Args:
            option (bool):オプションを表示するかどうか
    """
    if option:
        command = {'curve':'BevelOptions'}.get(
            getSelectedComponentType(), 'performPolyBevel 1'
        )
    else:
        command = {'curve':'Bevel'}.get(
            getSelectedComponentType(), 'performPolyBevel 0'
        )
    mel.eval(command)


def switchReverse(option=False):
    r"""
        コンポーネントに合った法線反転を行う。
        
        Args:
            option (bool):オプションを表示するかどうか
    """
    command = {
        'curve':'ReverseCurve', 'surface':'ReverseSurfaceDirection',
    }.get(getSelectedComponentType(), 'ReversePolygonNormals')
    mel.eval(command + ('Options' if option else ''))


def switchAttachNURBS(option=False):
    r"""
        コンポーネントに合ったNURBSをアタッチする。
        
        Args:
            option (bool):オプションを表示するかどうか
    """
    command = {
        'curve':'AttachCurve', 'param':'AttachCurve',
    }.get(getSelectedComponentType(), 'AttachSurfaces')
    mel.eval(command + ('Options' if option else ''))


def switchDettachNURBS(option=False):
    r"""
        コンポーネントに合ったNURBSのデタッチする。
        
        Args:
            option (bool):オプションを表示するかどうか
    """
    command = {
        'curve':'DetachCurve', 'param':'DetachCurve',
    }.get(getSelectedComponentType(), 'DetachSurfaces')
    mel.eval(command + ('Options' if option else ''))


def switchRebuildNURBS(option=False):
    r"""
        コンポーネントに合ったリビルドNURBSを行う。
        
        Args:
            option (bool):オプションを表示するかどうか
    """
    command = {'curve':'RebuildCurve'}.get(
        getSelectedComponentType(), 'RebuildSurfaces'
    )
    mel.eval(command + ('Options' if option else ''))


def switchOpenCloseNURBS(option=False):
    r"""
        コンポーネントに合ったNURBS開く/閉じるを行う。
        
        Args:
            option (bool):オプションを表示するかどうか
    """
    command = {'curve':'OpenCloseCurve'}.get(
        getSelectedComponentType(), 'OpenCloseSurfaces'
    )
    mel.eval(command + ('Options' if option else ''))
# =============================================================================
#                                                                            ==
# =============================================================================



