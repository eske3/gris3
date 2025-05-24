#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2024/05/09 18:02 Eske Yoshinob[eske3g@gmail.com]
        update:2024/05/09 18:06 Eske Yoshinob[eske3g@gmail.com]
        
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


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。

        Returns:
            MainGUI:
    """
    from gris3.uilib import mayaUIlib
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(680, 520)
    widget.show()
    return widget

