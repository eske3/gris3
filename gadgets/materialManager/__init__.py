#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2025/09/17 13:02 Eske Yoshinob[eske3g@gmail.com]
        update:2025/09/17 13:02 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2025 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from ... import uilib
from . import ui


class MainGUI(uilib.AbstractSeparatedWindow):
    def centralWidget(self):
        r"""
            メインとなるウィジェットを作成して返す。
            
            Returns:
                ui.Framework:
        """
        return ui.MainGUI()


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。

        Returns:
            MainGUI:
    """
    from ...uilib import mayaUIlib
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(900, 900)
    widget.main().refresh()
    widget.show()
    return widget

