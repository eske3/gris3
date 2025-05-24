# -*- coding: utf-8 -*-
r'''
    @file     setup.py
    @brief    GRISの初期設定を行う。userSetup.pyなどで呼び出す。
    @date        2017/05/30 5:26[Eske](eske3g@gmail.com)
    @update      2017/05/30 5:26[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''

# ホットキーの設定。
from . import hotkeyManager
hotkeyManager.createHotkey()

# Maya用のマーキングメニューの設定。
from .markingMenus import hotkeyData
hotkeyManager.createHotkey(hotkeyData.HOTKEY_TABLE)