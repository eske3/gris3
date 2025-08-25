#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    スキニングされたポリゴンの各頂点のインフルエンス数が既定値を超えて
    いないかをチェックする。

    checkToolの設定jsonファイルで使用できるオプションは以下の通り。
    {
        "moduleName": "skinInfluenceChecker",
        "modulePrefix": "-default",
        "options": {
            "target": ["チェック対象グループ名"...],
            "numberOfLimit": 4
        }
    }

    Dates:
        date:2024/06/27 17:33 Eske Yoshinob[eske3g@gmail.com]
        update:2024/06/27 17:33 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from maya import cmds
from .. import core, ui
from ....tools import skinUtility
from ....tools.sceneChecker import skinInfluenceChecker
from .... import uilib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class AbstractVertexSelector(ui.OperatorPage):
    def label(self):
        return ''

    def buildUI(self, parent=None):
        self.__target = None
        label = QtWidgets.QLabel(self.label())
        btn = QtWidgets.QPushButton('Select error vertex')
        btn.clicked.connect(self.selectVertex)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(btn)
        layout.addStretch()

    def setTarget(self, target):
        self.__target = target

    def target(self):
        return self.__target
    
    def check(self, weightlist):
        return False

    def updateUI(self,  info):
        self.setTarget(info[0])

    def getErroredVertices(self):
        target = self.target()
        weightlist = skinUtility.listWeights(target)
        vertices = []
        fmt = '{}.vtx[{{}}]'.format(target)
        for idx, wlist in weightlist.items():
            if not self.check(wlist):
                continue
            vertices.append(fmt.format(idx))
        return vertices

    def selectVertex(self):
        vertices = self.getErroredVertices()
        if not vertices:
            return
        cmds.hilite(self.target(), r=True)
        cmds.select(vertices, r=True)


class ZeroInfluenceSelector(AbstractVertexSelector):
    def label(self):
        return 'Non weighted vertices selector'

    def check(self, weightlist):
        return not weightlist

class LimitationBreakSelector(AbstractVertexSelector):
    def __init__(self, parent=None):
        super(LimitationBreakSelector, self).__init__(parent)
        self.__limit = 4

    def label(self):
        return 'limitation broken vertices selector'

    def setLimit(self, limit):
        self.__limit = int(limit)

    def limit(self):
        return self.__limit

    def check(self, weightlist):
        return len(weightlist) > self.limit()


class CategoryOption(core.AbstractCategoryOption):
    def  __init__(self):
        super(CategoryOption, self).__init__()
        self.invalid_plugins = []

    def category(self):
        return 'Poly Influence Checker'

    def buildUI(self, parent):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        self.result_view = ui.NodeResultViewer()
        self.result_view.addOperatorPage(ZeroInfluenceSelector(), 1)
        self.result_view.addOperatorPage(LimitationBreakSelector(), 2)
        
        layout = QtWidgets.QVBoxLayout(parent)
        layout.addWidget(self.result_view)

    def setOptions(self, **optionData):
        r"""
            Args:
                **optionData (any):
        """
        self.targets = optionData.get('target', ['geo_grp'])
        self.number_of_limit = optionData.get('numberOfLimit', 4)

    def execCheck(self):
        checker = skinInfluenceChecker.PolySkinInfluenceChecker()
        checker.setTargets(self.targets)
        checker.setNumberOfLimit(self.number_of_limit)
        checked = checker.check()
        self.result_view.setResults(checked)
        return self.getResultFromData(checked)
