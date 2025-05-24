# -*- coding: utf-8 -*-
#, *- coding: utf-8, *-
r'''
    @file     copyAndPasteMM.py
    @brief    ここに説明文を記入
    @class    CopyMarkingMenu : 様々な要素をコピーするためのマーキングメニュー
    @class    PasteMarkingMenu : 様々な要素をペーストするためのマーキングメニュー
    @date        2018/03/05 23:38[Eske](eske3g@gmail.com)
    @update      2018/04/14 3:35[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
from maya import cmds, mel
from gris3 import node
from gris3.tools import util, nameUtility
from gris3.uilib import mayaUIlib
QtWidgets, QtGui, QtCore = (
    mayaUIlib.QtWidgets, mayaUIlib.QtGui, mayaUIlib.QtCore
)

class CopyMarkingMenu(mayaUIlib.MarkingMenuWithTool):
    r'''
        @brief       様々な要素をコピーするためのマーキングメニュー
        @inheritance mayaUIlib.MarkingMenuWithTool
        @date        2018/04/14 3:20[Eske](eske3g@gmail.com)
        @update      2018/04/14 3:35[Eske](eske3g@gmail.com)
    '''
    def createMenu(self, parent):
        r'''
            @brief  メニューを作成する。
            @param  parent : [str]
            @return None
        '''
        cmds.menuItem(
            l='Cut', rp='N', p=parent, c=self.mel('CutSelected')
        )
        cmds.menuItem(
            l='Copy', rp='S', p=parent, c=self.mel('CopySelected')
        )
        
        cmds.menuItem(
            l='Copy names of selected', rp='W', p=parent,
            c=self.copySelectedNames
        )

    def copySelectedNames(self, *args):
        r'''
            @brief  選択ノードの名前をクリップボードに保存する
            @param  *args : [tuple]
            @return None
        '''
        nameUtility.copyNames()

    def command(self):
        r'''
            @brief  選択ノードの位置情報を一時的にメモリに保存する。
            @return None
        '''
        trs = util.Transform()
        trs.savePositions()

class PasteMarkingMenu(mayaUIlib.MarkingMenuWithTool):
    r'''
        @brief       様々な要素をペーストするためのマーキングメニュー
        @inheritance mayaUIlib.MarkingMenuWithTool
        @date        2018/04/14 3:20[Eske](eske3g@gmail.com)
        @update      2018/04/14 3:35[Eske](eske3g@gmail.com)
    '''
    def createMenu(self, parent):
        r'''
            @brief  メニューを作成する。
            @param  parent : [str]
            @return None
        '''
        cmds.menuItem(
            l='Paste', rp='S', p=parent, c=self.mel('PasteSelected')
        )
        
        cmds.menuItem(
            l='Paste names to selected', rp='W', p=parent,
            c=self.pasteNamesToSelected
        )
        cmds.menuItem(optionBox=True, c=self.openPasteOption)

    def pasteNamesToSelected(self, *args):
        r'''
            @brief  クリップボードに保存された名前を選択オブジェクトに適応する
            @param  *args : [tuple]
            @return None
        '''
        with node.DoCommand():
            nameUtility.pasteName()

    def openPasteOption(self, *args):
        from ..gadgets import renamer
        renamer.showPasteNameOption()

    def command(self):
        r'''
            @brief  メモリにホジした位置情報を選択ノードに適応する。
            @return None
        '''
        with node.DoCommand():
            trs = util.Transform()
            trs.restorePositions()