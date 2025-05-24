#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ノードの表示色に関する機能を提供するモジュール。
    
    Dates:
        date:2017/01/21 12:05[Eske](eske3g@gmail.com)
        update:2025/05/24 10:18 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import mayaCmds as cmds

NewColorIndex = (
    (0.184474080801, 0.184474080801, 0.184474080801),       # 0
    (0.0, 0.0, 0.0),                                        # 1
    (0.0481716692448, 0.0481716692448, 0.0481716692448),    # 2
    (0.21222653985, 0.21222653985, 0.21222653985),          # 3
    (0.327785313129, 0.0, 0.0212190486491),                 # 4
    (0.0, 0.0012138064485, 0.116971932352),                 # 5
    (0.0, 0.0, 1.00002408028),                              # 6
    (0.0, 0.0612473413348, 0.00856800563633),               # 7
    (0.0176415853202, 0.0, 0.0561296865344),                # 8
    (0.57112210989, 0.0, 0.57112210989),                    # 9
    (0.250157862902, 0.0612473413348, 0.0331039950252),     # 10
    (0.0481716692448, 0.015996010974, 0.0137021318078),     # 11
    (0.318554520607, 0.0176415853202, 0.0),                 # 12
    (1.0, 0.0, 0.0),                                        # 13
    (0.0, 1.0, 0.0),                                        # 14
    (0.0, 0.0528613589704, 0.318554520607),                 # 15
    (1.0, 1.0, 1.0),                                        # 16    
    (1.00002408028, 1.00002408028, 0.0),                    # 17
    (0.124773681164, 0.715708136559, 1.00002408028),        # 18
    (0.0561296865344, 1.00002408028, 0.361310094595),       # 19
    (1.00002408028, 0.428684949875, 0.428684949875),        # 20
    (0.768161118031, 0.412538588047, 0.19120413065),        # 21
    (1.00002408028, 1.00002408028, 0.122140586376),         # 22
    (0.0, 0.318554520607, 0.0843748599291),                 # 23
    (0.351537019014, 0.141265928745, 0.0284263640642),      # 24
    (0.341920375824, 0.351537019014, 0.0284263640642),      # 25
    (0.138434261084, 0.351537019014, 0.0284263640642),      # 26
    (0.0284263640642, 0.351537019014, 0.10946149379),       # 27
    (0.0284263640642, 0.351537019014, 0.351537019014),      # 28
    (0.0284263640642, 0.135635942221, 0.351537019014),      # 29
    (0.158960610628, 0.0284263640642, 0.351537019014),      # 30
    (0.351537019014, 0.0284263640642, 0.141265928745),      # 31
)

if cmds.MAYA_VERSION >= 2016:
    #Maya2016以降ではこちらの関数が呼ばれる。
    def applyColor(node, color=None):
        r"""
            ノードのワイヤーフレームカラーを設定するメソッド。
            引数colorにはrgb値を持つlistか、NewColorIndexで定義される
            0～31の整数を渡す。
            Maya2016以降専用のコマンド。
            
            Args:
                node (str):操作対象ノード名
                color (list or tuple or int):
        """
        children = cmds.listRelatives(node, shapes=True, ni=True, pa=True)
        if children:
            children.append(node)
            node = children
        else:
            node = [node]

        if color is None:
            use = 0
            color = (0, 0, 0)
        else:
            use = 2
            color = NewColorIndex[color] if isinstance(color, int) else color
        for n in node:
            cmds.setAttr(n + '.useObjectColor', use)
            cmds.setAttr(n + '.wireColorRGB', *color)
else:
    # Maya2015以前ではこちらの関数が呼ばれる。
    def applyColor(node, color=None):
        r"""
            ノードのワイヤーフレームカラーを設定するメソッド。
            Maya2015:以前のバージョンではこちらの関数が使用される。
            
            Args:
                node (str):操作対象ノード名。
                color (int):カラーインデックス。
        """
        enable = not color is None
        cmds.setAttr(node + '.overrideEnabled', enable)
        cmds.setAttr(node + '.overrideColor', color if enable else 0)

