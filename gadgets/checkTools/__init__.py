#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2024/05/09 18:02 Eske Yoshinob[eske3g@gmail.com]
        update:2025/08/25 16:53 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from ... import lib, uilib
from . import ui

class MainGUI(uilib.AbstractSeparatedWindow):
    def centralWidget(self):
        r"""
            メインとなるウィジェットを作成して返す。
            
            Returns:
                ui.Framework:
        """
        return ui.Framework()


def showWindow(categoryData=''):
    r"""
        ウィンドウを作成するためのエントリ関数。
        引数categoryDataはカテゴリを定義するファイルパスか、その中身を展開した
        辞書データを渡す。
        
        Args:
            categoryData (str/dict):
            
        Returns:
            MainGUI:
    """
    from gris3.uilib import mayaUIlib
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(680, 520)
    if isinstance(categoryData, dict):
        widget.main().setCategoryFromData(categoryData)
    else:
        widget.main().setCategoryFromFile(categoryData)
    widget.show()
    return widget

