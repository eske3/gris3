#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    選択にまつわるMMを定義する
    
    Dates:
        date:2019/11/09 17:42[eske3g@gmail.com]
        update:2023/11/26 08:56 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2019 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from maya import cmds, mel
from gris3.tools import selectionUtil
from gris3.uilib import mayaUIlib
QtWidgets, QtGui, QtCore = (
    mayaUIlib.QtWidgets, mayaUIlib.QtGui, mayaUIlib.QtCore
)

class MarkingMenu(mayaUIlib.MarkingMenuWithTool):
    r"""
        選択にまつわるMMを提供するクラス
    """
    def createMenu(self, parent):
        r"""
            MMをを作成する。
            
            Args:
                parent (str):親のUI名
        """
        # リング選択に関するメニュー。=========================================
        cmds.menuItem(l='Select Edge Ring', rp='SW', sm=True, p=parent)
        cmds.menuItem(
            l='Select Edge Ring', rp='SW', c=self.mel('SelectEdgeRing')
        )
        cmds.menuItem(
            l='Select Edge Ring Pattern', rp='NW', c=self.selectEdgeRingPattern
        )
        cmds.menuItem(
            l='Select Edge Ring Tool', rp='SE',
            c=self.mel('SelectEdgeRingTool')
        )
        # =====================================================================

        # ループ選択に関するメニュー。=========================================
        cmds.menuItem(l='Select Edge Loop', rp='SE', sm=True, p=parent)
        cmds.menuItem(
            l='Select Edge Loop', rp='SE', c=self.mel('SelectEdgeLoop')
        )
        cmds.menuItem(
            l='Select Edge Loop', rp='NE', c=self.selectEdgeLoopPattern
        )
        cmds.menuItem(
            l='Select Edge Loop Tool', rp='SW',
            c=self.mel('SelectEdgeLoopTool')
        )
        # =====================================================================

        # ポリゴンに関する拡張選択メニュー。===================================
        cmds.menuItem(l='Advanced Poly Selection', rp='NW', sm=True, p=parent)
        cmds.menuItem(
            l='Glow face selections inside hardedges', rp='NW',
            c=self.convertFaceInsideHardedges
        )
        cmds.menuItem(
            l='Convert faces to border edges.', rp='NE',
            c=self.selectFaceBorder
        )
        cmds.menuItem(
            l='Select creased poly edges.', rp='SE',
            c=self.selectCreasedEdge
        )
        # =====================================================================

        cmds.menuItem(
            l='Poly Loop Edge', rp='NE', aob=True, p=parent,
            c=self.mel('SelectContiguousEdges')
        )
        cmds.menuItem(
            l='Poly Loop Edge Options', ob=True, p=parent,
            c=self.mel('SelectContiguousEdgesOptions')
        )
        cmds.menuItem(
            l='Polygon Selection Constraints...', rp='S', p=parent,
            c=self.mel('PolygonSelectionConstraints')
        )

        # =====================================================================
        cmds.menuItem(
            l='Reverse order to Selected', rp='N', p=parent,
            c=self.reverseSelectionOrder
        )

        cmds.menuItem(
            l='Reverse Side Select', rp='W', p=parent,
            c=self.selectOppositeSide
        )
        cmds.menuItem(
            l='Reverse Side Add', rp='E', p=parent, c=self.addOppositeSide
        )
        # =====================================================================

    def command(self):
        r"""
            選択ツールに変更する
        """
        selections = cmds.ls(sl=True)
        cmds.setToolTo(mel.eval('global string $gSelect; $gSelect=$gSelect;'))
        cmds.selectPref(paintSelect=0)

    def convertFaceInsideHardedges(self, *args):
        r"""
            選択フェースをハードエッジ境界線内まで拡大する
            
            Args:
                *args (any):
        """
        selectionUtil.convertFaceInsideHardedges()

    def selectFaceBorder(self, *args):
        r"""
            選択フェースのボーダーエッジを選択する
            
            Args:
                *args (any):
        """
        selectionUtil.listFaceBorders()

    def selectCreasedEdge(self, *args):
        r"""
            選択オブジェクトのクリースされたエッジを選択する。
            
            Args:
                *args (any):
        """
        selectionUtil.selectCreasedEdges()
        

    def selectEdgeRingPattern(self, *args):
        r"""
            任意のエッジリングパターンの選択を拡張する
            
            Args:
                *args (any):
        """
        selectionUtil.selectEdgeLoopRing('rpt')

    def selectEdgeLoopPattern(self, *args):
        r"""
            任意のエッジループパターンの選択を拡張する
            
            Args:
                *args (any):
        """
        selectionUtil.selectEdgeLoopRing('lpt')

    def reverseSelectionOrder(self, *args):
        r"""
            選択順序を逆順にする
            
            Args:
                *args (any):
        """
        selectionUtil.reverseSelectionOrder()

    def selectOppositeSide(self, *args):
        r"""
            任意の命名規則に従って反対側のオブジェクトを選択する
            
            Args:
                *args (any):
        """
        selectionUtil.selectOppositeSide()

    def addOppositeSide(self, *args):
        r"""
            任意の命名規則に従って反対側のオブジェクトを追加選択する
            
            Args:
                *args (any):
        """
        selectionUtil.selectOppositeSide('add')
