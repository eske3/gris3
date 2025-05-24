#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    パスに関する設定を行うモジュール。
    
    Dates:
        date:2017/01/22 0:04[Eske](eske3g@gmail.com)
        update:2025/05/24 10:22 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
RootPath = os.path.dirname(__file__)
PrefPath = []
IconPath = os.path.join(RootPath, 'icons')

def getIconPath(iconName):
    r"""
        アイコンのパスを取得する関数。
        
        Args:
            iconName (str):
            
        Returns:
            str: アイコンの絶対パス
    """
    iconName = (
        iconName if iconName.endswith('.png') else iconName + '.png'
    )
    return os.path.join(IconPath, iconName)