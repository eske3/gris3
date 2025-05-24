#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    表示に関する便利関数を提供するモジュール
    
    Dates:
        date:2018/04/07 4:21[Eske](eske3g@gmail.com)
        update:2023/08/14 09:06 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2018 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import node
cmds = node.cmds

def getModelPanelStatus(key, panel=None):
    r"""
        モデルパネルの任意のオプションの状態を返す。
        
        Args:
            key (str):調べるオプション文字列
            panel (str):モデルパネル名
            
        Returns:
            bool:
    """
    panel = panel or cmds.getPanel(wf=True)
    return cmds.modelEditor(panel, **{'q':True, key:True})


def toggleModelPanelDisplay(key, panel=None):
    r"""
        モデルパネルの任意のオプションをトグル変更する。
        戻り値として変更後の値(bool)を返す。
        
        Args:
            key (str):変更するオプション文字列
            panel (str):モデルパネル名
            
        Returns:
            bool:
    """
    panel = panel or cmds.getPanel(wf=True)
    value = getModelPanelStatus(key, panel) == False
    cmds.modelEditor(panel, **{'e':True, key:value})
    return value


def enableIsolateSelect(panel=None):
    r"""
        panelのisolateSelectを有効にする。
        
        Args:
            panel (str):モデルパネル名
    """
    from maya import mel
    panel = panel or cmds.getPanel(wf=True)
    mel.eval('enableIsolateSelect %s true' % panel)
    # mel.eval('isoSelectAutoAddNewObjs %s 1' % panel)


def setDisplaySurface(state):
    r"""
        オブジェクトのX-Ray表示を設定する。
        
        Args:
            state (bool):
    """
    cmds.displaySurface(x=state)
