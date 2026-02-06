#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2026/02/06 12:20 Eske Yoshinob[eske3g@gmail.com]
        update:2026/02/06 12:20 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2026 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from . import main


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。
        
        Returns:
            QtWidgets.QWidget:
    """
    from ...uilib import mayaUIlib
    widget = main.MainGUI(mayaUIlib.MainWindow)
    widget.resize(350, 600)
    widget.show()
    return widget
