#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ファイル制御に関する便利UIのライブラリ。
    
    Dates:
        date:2017/01/21 23:58[Eske](eske3g@gmail.com)
        update:2021/04/23 10:01 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import re

from gris3 import uilib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class FileNameLineEdit(uilib.FilteredLineEdit):
    r"""
        Windows準拠でパスとして入力不能な文字列をフィルタする機能が
        入ったQlineEdit
    """
    RegularExpression ='[/\\\*\<\>\:\?\|\^\"]'
    def __init__(self, *args, **keywords):
        r"""
            Args:
                *args (tuple):
                **keywords (dict):
        """
        super(FileNameLineEdit, self).__init__(*args, **keywords)
        self.setFilter(self.RegularExpression)

    def filtering(self, text, result):
        r"""
            Args:
                text (str):
                result (str):
                
            Returns:
                str:
        """
        return self.filterObject().sub('', text)

