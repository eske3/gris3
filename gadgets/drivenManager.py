# -*- coding: utf-8 -*-
r'''
    @file     drivenManager.py
    @brief    ジョイントの編集機能を提供するGUI。
    @class    DrivenUtility : ドリブンキーにまつわる便利ツールGUIを提供するクラス。
    @class    MainGUI : 単独ウィンドウとして表示されるウィンドウ。
    @function showWindow : ウィンドウを作成するためのエントリ関数。
    @date        2017/06/15 16:35[Eske](eske3g@gmail.com)
    @update      2017/09/03 23:27[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
from gris3.tools import drivenUtilities
from gris3 import uilib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore
Exec_Color = (64, 72, 150)

class DrivenUtility(uilib.ClosableGroup):
    r'''
        @brief       ドリブンキーにまつわる便利ツールGUIを提供するクラス。
        @inheritance uilib.ClosableGroup
        @date        2017/09/03 23:26[Eske](eske3g@gmail.com)
        @update      2017/09/03 23:27[Eske](eske3g@gmail.com)
    '''
    def __init__(self, parent=None):
        r'''
            @brief  初期化を行う。
            @param  parent(None) : [QtWidgets.QWidget]
            @return None
        '''
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
        r'''
            @brief  選択されているノード下のドリブンノードを選択する。
            @return None
        '''
        drivenUtilities.selectDrivenNode(isSelecting=True)

class MainGUI(uilib.AbstractSeparatedWindow):
    r'''
        @brief       単独ウィンドウとして表示されるウィンドウ。
        @inheritance uilib.AbstractSeparatedWindow
        @date        2017/06/27 18:31[s_eske](eske3g@gmail.com)
        @update      2017/09/03 23:27[Eske](eske3g@gmail.com)
    '''
    def centralWidget(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return DrivenUtility()


def showWindow():
    r'''
        @brief  ウィンドウを作成するためのエントリ関数。
        @return QtWidgets.QWidget
    '''
    from gris3.uilib import mayaUIlib
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(300, 100)
    widget.show()
    return widget