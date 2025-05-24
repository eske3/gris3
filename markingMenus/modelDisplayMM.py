#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    モデル表示に関する表示制御用マーキングメニューを生成するモジュール。
    
    Dates:
        date:2018/03/05 23:38[Eske](eske3g@gmail.com)
        update:2023/08/14 09:12 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2018 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from maya import cmds
from gris3 import node
from gris3.tools import displayUtil
from gris3.uilib import mayaUIlib
QtWidgets, QtGui, QtCore = (
    mayaUIlib.QtWidgets, mayaUIlib.QtGui, mayaUIlib.QtCore
)

class MarkingMenu(mayaUIlib.MarkingMenuWithTool):
    r"""
        モデル表示制御用マーキングメニュー生成クラス。
    """
    def createMenu(self, parent):
        r"""
            メニューを作成するオーバーライドメソッド。
            
            Args:
                parent (str):親メニュー
        """
        from functools import partial
        panel = cmds.getPanel(wf=True)
        self.focused_panel = panel

        cmds.menuItem(l='Isolate select option', sm=1, p=parent, rp='N')
        cmds.menuItem(
            l='Add Selected Objects', rp='N',
            c=self.mel('addSelectedToEditor ' + panel)
        )
        cmds.menuItem(
            l='Remove Selected Objects', rp='S',
            c=self.mel('removeSelectedFromEditor ' + panel)
        )
        
        cmds.menuItem(
            l='Disable Isolate Selecte', rp='S', p=parent,
            c=self.mel('enableIsolateSelect %s false;' % panel)
        )

        cmds.menuItem(
            l='Use Default Material', rp='W', p=parent,
            cb=displayUtil.getModelPanelStatus('udm'),
            c=partial(self.toggleDisplay, 'udm', panel)
        )
        cmds.menuItem(
            l='X-Ray Joint', rp='E', p=parent,
            cb=displayUtil.getModelPanelStatus('jointXray'),
            c=partial(self.toggleDisplay, 'jointXray', panel)
        )
        cmds.menuItem(
            l='Display joint', rp='SE', p=parent,
            cb=displayUtil.getModelPanelStatus('joints'),
            c=partial(self.toggleDisplay, 'joints', panel)
        )

        cmds.menuItem(l='X-ray Display', sm=1, p=parent, rp='NW')
        cmds.menuItem(
            l='Turn X-ray on', rp='NW', c=partial(self.setDisplaySurface, True)
        )
        cmds.menuItem(
            l='Turn X-ray off', rp='SE',
            c=partial(self.setDisplaySurface, False)
        )
        
        cmds.menuItem(
            l='Display Settings', p=parent, rp='NE',
            c=self.showDisplaySettings
        )

        cmds.menuItem(
            l='Print current panel name', p=parent,
            c=partial(self.printCurrentPanelName, panel)
        )

    def toggleDisplay(self, key, panel, *args):
        r"""
            panelの表示状態をトグル変更する
            
            Args:
                key (str):
                panel (str):モデルパネル名
                *args (any):
        """
        with node.DoCommand():
            displayUtil.toggleModelPanelDisplay(key, panel)

    def setDisplaySurface(self, state, *args):
        r"""
            デフォルトマテリアル表示のトグル設定を行う。
            
            Args:
                state (bool):
                *args (any):
        """
        displayUtil.setDisplaySurface(state)

    def showDisplaySettings(self, *args):
        r"""
            表示設定を表示する。
            
            Args:
                *args (any):
        """
        from gris3 import gadgets
        gadgets.showDisplaySettings()

    def printCurrentPanelName(self, panelName, *args):
        r"""
            現在のパネル名を表示する。

            Args:
                panelName (str):
                *args (any):
        """
        print('Current panel name : {}'.format(panelName))

    def command(self):
        r"""
            IsolateSelection設定をトグルで行う。
        """
        if not hasattr(self, 'focused_panel'):
            return
        displayUtil.enableIsolateSelect(self.focused_panel)
