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
from . import bindingObjectList
from ... import uilib, node
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class InfluenceUtility(uilib.ClosableGroup):
    r"""
        バインドに関する機能を提供するGUI。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):
        """
        super(InfluenceUtility, self).__init__('Influence Utility', parent)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(2)

        for data in (
            (
                bindingObjectList.showWindow,
                'Show skinned objects are binded from selected influences.',
                (150, 38, 45), 'uiBtn_skeleton'
            ),
            10,
            (
                self.refsetInfluence,
                (
                    'Reset influence to a binded objects '
                    'that is binded from the selected influences.'
                ),
                (96, 38, 160), 'uiBtn_reset'
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

    def refsetInfluence(self):
        with node.DoCommand():
            skinUtility.resetInfluence()
