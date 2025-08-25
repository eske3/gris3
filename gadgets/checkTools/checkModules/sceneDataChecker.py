#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    unknownプラグインの検知と、任意のプラグインが読み込まれているかどうかを
    チェックする。
    任意のプラグインの読み込みチェックについては、主に読み込む必要がない
    プラグインをリストアップする目的で使用する。

    checkToolの設定jsonファイルで使用できるオプションは以下の通り。
    {
        "moduleName": "sceneDataChecker",
        "modulePrefix": "-default",
        "options": {
            "invalidPlugins": ["プラグイン名"...]]
        }
    }
    
    invalidPluginsで不要なプラグインをリストアップしておく。
    デフォルトは空（指定無し))。


    Dates:
        date:2024/06/03 17:48 Eske Yoshinob[eske3g@gmail.com]
        update:2024/06/03 17:48 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import core, ui
from ....tools.sceneChecker import sceneDataChecker
from .... import uilib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class CategoryOption(core.AbstractCategoryOption):
    def  __init__(self):
        super(CategoryOption, self).__init__()
        self.invalid_plugins = []

    def category(self):
        return 'Scene Data Checker'

    def buildUI(self, parent):
        self.result_view = ui.NodeResultViewer()
        layout = QtWidgets.QVBoxLayout(parent)
        layout.addWidget(self.result_view)
    
    def setOptions(self, **optionData):
        self.invalid_plugins = optionData.get('invalidPlugins', [])

    def execCheck(self):
        checker = sceneDataChecker.SceneDataChecker()
        checker.setInvalidPlugins(*self.invalid_plugins)
        checked = checker.check()
        self.result_view.setResults(checked)
        return self.getResultFromData(checked)