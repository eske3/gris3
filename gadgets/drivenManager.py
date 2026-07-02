#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    選択に関する便利関数を収録するモジュール。

    Dates:
        date:2018/03/06 8:53[Eske](eske3g@gmail.com)
        update:2026/06/04 22:17 Eske Yoshinob[eske3g@gmail.com]

    License:
        Copyright 2018 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from ..tools import drivenUtilities
from .. import uilib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class DrivenUtility(uilib.ClosableGroup):
    r"""
    ドリブンキーにまつわる便利ツールGUIを提供するクラス。
    """
    def __init__(self, parent=None):
        r"""
        Args:
            parent(QtWidgets.QWidget):親ウィジェット
        """
        super(DrivenUtility, self).__init__('Driven Utilities', parent)
        self.setWindowTitle('+Driven Manager')
        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(2)

        for data in (
            (
                self.selectDriven,
                'Select driven nodes under selected nodes.',
                (12, 65, 160), 'uiBtn_select'
            ),
            (
                drivenUtilities.mirrorDriven,
                'Mirror driven keys from selected nodes.',
                (49, 115, 154), 'uiBtn_mirror'
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

    def selectDriven(self):
        r"""
        選択されているノード下のドリブンノードを選択する。
        """
        drivenUtilities.selectDrivenNode(isSelecting=True)


class MainGUI(uilib.AbstractSeparatedWindow):
    r"""
    単独ウィンドウとして表示されるウィンドウ。
    """
    def centralWidget(self):
        r"""
        Returns:
            DrivenUtility:
        """
        return DrivenUtility()


def showWindow():
    r"""
    ウィンドウを作成するためのエントリ関数。

    Returns:
        MainGUI:
    """
    from ..uilib import mayaUIlib
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(300, 100)
    widget.show()
    return widget