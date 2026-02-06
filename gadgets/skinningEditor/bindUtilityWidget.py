#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    バインド操作を助ける機能郡を提供するGUI。
    
    Dates:
        date:2017/06/15 16:35[Eske](eske3g@gmail.com)
        update:2020/07/29 13:04 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from ...tools import skinUtility
from ... import uilib, node
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class BindUtility(uilib.ClosableGroup):
    r"""
        バインドに関する機能を提供するGUI。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):
        """
        super(BindUtility, self).__init__('Bind Utility', parent)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(2)
        from ...exporter import skinWeightExporter
        from ...tools.controllerUtil import restoreToDefault
        self.__temp_wgt = skinWeightExporter.TemporaryWeight()

        for data in (
            (
                skinUtility.showBindSkinOption,
                'Open bind skin option',
                (96, 128, 20), 'uiBtn_bindSkinOption'
            ),
            (
                self.bindFromBinded,
                'Bind skin to selected from last selection that was binded.',
                (38, 128, 148), 'uiBtn_bindSkin'
            ),
            (
                self.bindToTube,
                'Set weight from joint chain to selected faces.',
                (38, 128, 148), 'uiBtn_bindToTube'
            ),
            (
                self.transferObjectsWeights,
                'Transfer selected weights to last selected object.',
                (38, 128, 148), 'uiBtn_extractFace'
            ),
            10,
            (
                self.tempExportWeight,
                'Export weight of selected node temporarily.',
                (11, 68, 128), 'uiBtn_export'
            ),
            (
                self.tempImportWeight,
                'Import weight of selected node temporarily.',
                (11, 68, 128), 'uiBtn_import'
            ),
            10,
            (
                restoreToDefault,
                'Reset selected controllers.',
                (91, 82, 182), 'uiBtn_reset'
            ),
        ):
            if isinstance(data, int):
                layout.addSpacing(data)
                continue
            cmd, tooltip, color, icon = data
            btn = uilib.OButton()
            btn.setToolTip(tooltip)
            btn.setBgColor(*color)
            btn.setIcon(uilib.IconPath(icon))
            btn.setSize(38)
            btn.clicked.connect(cmd)
            layout.addWidget(btn)
        layout.addStretch()

    def bindFromBinded(self):
        r"""
            バインド済みオブジェクトのバインド情報を他のオブジェクトに移す。
        """
        with node.DoCommand():
            selected = node.selected()
            skinUtility.bindFromBinded(selected[:-1], selected[-1])

    def bindToTube(self):
        r"""
            ジョイントチェーン用いてをチューブ上の形状に柔らかくウェイトを
            セットする。
        """
        with node.DoCommand():
            selected = node.selected()
            skinUtility.bindToFace()

    def transferObjectsWeights(self):
        r"""
            任意の複数オブジェクトのウェイトをターゲットに写す
        """
        with node.DoCommand():
            skinUtility.transferObjectsWeights()

    def tempExportWeight(self):
        r"""
            テンポラリに現在選択しているオブジェクトのウェイトを書き出す
        """
        self.__temp_wgt.save()

    def tempImportWeight(self):
        r"""
            テンポラリのウェイトを読み込む
        """
        self.__temp_wgt.restore()

