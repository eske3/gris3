#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ポリゴンの頂点カラーセットの検出を行う。
    checkToolの設定jsonファイルで使用できるオプションは以下の通り。
    {
        "moduleName": "vtxColorChecker",
        "modulePrefix": "-default",
        "options": {
            "target": ["操作対象グループ名"],
            "errorLevel": 1 # 警告止まりの場合１，エラーとして認識する場合は０
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
from ....tools.sceneChecker import vtxColorChecker
from .... import uilib, node
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class VtxColorPatch(ui.OperatorPage):
    def buildUI(self, parent):
        r"""
            Args:
                parent (QtWidgets.QWidget): 親ウィジェット
        """
        self.target_label = QtWidgets.QLabel('')
        self.target_label.setStyleSheet(
            'font-size: 12pt;'
        )

        vtx_list_grp = QtWidgets.QGroupBox('Vertex color sets.')
        self.vtx_color_list = QtWidgets.QLabel('')
        layout = QtWidgets.QVBoxLayout(vtx_list_grp)
        layout.addWidget(self.vtx_color_list)

        operator = QtWidgets.QGroupBox('Operation')
        btn = QtWidgets.QPushButton('Remove all color sets.')
        btn.clicked.connect(self.removeAllColorSets)
        layout = QtWidgets.QVBoxLayout(operator)
        layout.addWidget(btn)
        
        layout = QtWidgets.QVBoxLayout(parent)
        layout.addWidget(self.target_label)
        layout.addWidget(operator)
        layout.addWidget(vtx_list_grp)
        layout.addStretch()

    def updateUI(self, info):
        r"""
            Args:
                info (list):
        """
        self.target_label.setText(info[0])
        color_sets = vtxColorChecker.listColorSets(info[0])
        texts = []
        for mesh, acs in color_sets.items():
            texts.append(mesh())
            texts.extend(['    + {}'.format(x) for x in acs])
        self.vtx_color_list.setText('\n'.join(texts))

    def removeAllColorSets(self):
        target = node.asObject(self.target_label.text())
        if not target:
            return
        from ....tools import cleanup
        with node.DoCommand():
            cleanup.removeAllVertexColorSets([target])
        self.updateUI([target()])


class CategoryOption(core.AbstractCategoryOption):
    def  __init__(self):
        super(CategoryOption, self).__init__()
        self.invalid_plugins = []

    def category(self):
        return 'Poly Vertex Color Checker'

    def buildUI(self, parent):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        self.result_view = ui.NodeResultViewer()
        self.result_view.addOperatorPage(VtxColorPatch(), 2)
        
        layout = QtWidgets.QVBoxLayout(parent)
        layout.addWidget(self.result_view)

    def setOptions(self, **optionData):
        r"""
            Args:
                **optionData (any):
        """
        self.targets = optionData.get('target', ['all_grp'])
        self.error_level = optionData.get('errorLevel', 0)

    def execCheck(self):
        checker = vtxColorChecker.VtxColorChecker()
        checker.setTargets(self.targets)
        checker.setErrorLevel(self.error_level)
        checked = checker.check()
        self.result_view.setResults(checked)
        return self.getResultFromData(checked)

