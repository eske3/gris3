#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    任意のノードが参照しているファイルが存在するかどうかのチェックを行う。
    現状のバージョンではfileノードのUDIM設定などは対応していない。
    （要望があればいつか・・・）

    checkToolの設定jsonファイルで使用できるオプションは以下の通り。
    {
        "moduleName": "filePathChecker",
        "modulePrefix": "-default",
        "options": {
            "types": [["ノードの種類", "アトリビュート"]...]
        }
    }
    typesには
    操作対象ノードのタイプ（文字列）、取得するアトリビュート名（文字列）
    の2つの情報を持つリストをリスト化したものを渡す。

    Dates:
        date:2024/06/24 17:09 Eske Yoshinob[eske3g@gmail.com]
        update:2024/06/24 17:09 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import core, ui
from ....tools.sceneChecker import filePathChecker
from .... import uilib, node
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class CategoryOption(core.AbstractCategoryOption):
    def  __init__(self):
        super(CategoryOption, self).__init__()
        self.target_types = []

    def category(self):
        return 'File path Checker'

    def buildUI(self, parent):
        r"""
            Args:
                parent (QtWidgets.QWidget): 親ウィジェット
        """
        self.result_view = ui.NodeResultViewer()
        # self.result_view.addOperatorPage(VtxColorPatch(), 2)
        layout = QtWidgets.QVBoxLayout(parent)
        layout.addWidget(self.result_view)

    def setOptions(self, **optionData):
        r"""
            Args:
                **optionData (any):
        """
        self.target_types = optionData.get('types', [('file', 'ftn')])

    def execCheck(self):
        checker = filePathChecker.FilePathChecker()
        checker.setTargets(self.target_types)
        checked = checker.check()
        self.result_view.setResults(checked)
        return self.getResultFromData(checked)

