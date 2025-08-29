#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Transformノードがフリーズされているかどうかをチェックする。
    checkToolの設定jsonファイルで使用できるオプションは以下の通り。
    {
        "moduleName": "vtxColorChecker",
        "modulePrefix": "-default",
        "options": {
            "target": ["操作対象グループ名"],
            "matrixErrorLevel": 0 # 警告止まりの場合１，エラーとして認識する場合は０
            "pivotErrorLevel": 0 # 警告止まりの場合１，エラーとして認識する場合は０
        }
    }
    
    Dates:
        date:2024/06/03 17:48 Eske Yoshinob[eske3g@gmail.com]
        update:2024/06/07 15:10 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import core, ui
from ....tools.sceneChecker import transformChecker
from ....tools import checkUtil
from .... import uilib, node
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class CategoryOption(core.AbstractCategoryOption):
    def  __init__(self):
        super(CategoryOption, self).__init__()
        self.targets = []
        self.matrixErrorLevel = checkUtil.CheckedResult.Error
        self.pivotErrorLevel = checkUtil.CheckedResult.Error

    def category(self):
        return 'Transform Checker'

    def buildUI(self, parent):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        self.result_view = ui.NodeResultViewer()
        layout = QtWidgets.QVBoxLayout(parent)
        layout.addWidget(self.result_view)

    def setOptions(self, **optionData):
        r"""
            Args:
                **optionData (any):
        """
        self.targets = optionData.get(
            'target', transformChecker.TransformChecker.DefaultTargets
        )
        self.matrixErrorLevel = optionData.get(
            'matrixErrorLevel', checkUtil.CheckedResult.Error
        )
        self.pivotErrorLevel = optionData.get(
            'pivotErrorLevel', checkUtil.CheckedResult.Error,
        )

    def execCheck(self):
        checker = transformChecker.TransformChecker()
        checker.setTargets(self.targets)
        checker.setMatrixErrorLevel(self.matrixErrorLevel)
        checker.setPivotErrorLevel(self.pivotErrorLevel)
        checked = checker.check()
        self.result_view.setResults(checked)
        return self.getResultFromData(checked)

