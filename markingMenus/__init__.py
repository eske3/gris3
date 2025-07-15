#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Mayaのマーキングメニューに関するモジュール。
    主にホットキー押しによる機能＋独自のマーキングメニューを構成する特殊
    GUIを提供する。
    
    Dates:
        date:2018/03/08 1:14[Eske](eske3g@gmail.com)
        update:2025/06/27 12:50 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2018 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""


def execCommand(mode, module, cls='MarkingMenu'):
    r"""
        与えられたモジュールのMarkingMenuクラスを呼び出し実行する。
        mode０でメニューの表示、１でコマンドの実行
        
        Args:
            mode (int):
            module (str):モジュール名
    """
    mm = getattr(module, cls)()
    if mode == 0:
        mm.showMenu()
    else:
        mm.execute()


def selectToolCommand(mode):
    r"""
        選択ツールならびに選択にまつわるマーキングメニューの表示を行う。
        
        Args:
            mode (int):
    """
    from . import selectToolMM
    execCommand(mode, selectToolMM)


def showAttributeEditor(mode):
    r"""
        AttributeEditorの表示ならびにサブメニューの表示を行う。
        
        Args:
            mode (int):
    """
    from . import attributeEditorMM
    execCommand(mode, attributeEditorMM)


def parentAndPreference(mode):
    r"""
        parentの実行、もしくはプレファレンスにまつわるメニューの表示
        
        Args:
            mode (int):
    """
    from . import parentAndPreferenceMM
    execCommand(mode, parentAndPreferenceMM)


def showDisplayMenu(mode):
    r"""
        表示のリセット、もしくは表示にまつわるメニューの表示
        
        Args:
            mode (int):
    """
    from . import displayMM
    execCommand(mode, displayMM)


def showModelDisplayMenu(mode):
    r"""
        isolateの実行、もしくはモデル表示にまつわるメニューの表示
        
        Args:
            mode (int):
    """
    from . import modelDisplayMM
    execCommand(mode, modelDisplayMM)


def showCopyMenu(mode):
    r"""
        Transform情報のコピー、ならびにその他雑多なコピー機能にまつわる
        マーキングメニューの表示。

        Args:
            mode (int):
    """
    from . import copyAndPasteMM
    execCommand(mode, copyAndPasteMM, 'CopyMarkingMenu')


def showPasteMenu(mode):
    r"""
        Transform情報のペースト、ならびにその他雑多なペースト機能にまつわる
        マーキングメニューの表示。

        Args:
            mode (int):
    """
    from . import copyAndPasteMM
    execCommand(mode, copyAndPasteMM, 'PasteMarkingMenu')

