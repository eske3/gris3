#, *- coding: utf-8, *-
r'''
    @file     selectToolMM.py
    @brief    ここに説明文を記入
    @date        2018/03/05 23:38[Eske](eske3g@gmail.com)
    @update      2018/03/05 23:38[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
from maya import cmds, mel
from gris3.tools import selectionUtil
from gris3.uilib import mayaUIlib
QtWidgets, QtGui, QtCore = (
    mayaUIlib.QtWidgets, mayaUIlib.QtGui, mayaUIlib.QtCore
)

class MarkingMenu(mayaUIlib.MarkingMenuWithTool):
    def createMenu(self, parent):
        # ポップアップセレクションの切り替え
        cmds.menuItem(
            parent=parent, l='Pick Chooser', c=self.pickChooer,
            cb=cmds.selectPref(q=True, pms=True), rp='E'
        )

        # Reposition Using MMB の使用の切り替え(Maya7以降のみで機能)
        cmds.menuItem(
            parent=parent, l='Reposition Using Middle Mouse Button',
            c=self.repositionMudButton,
            cb=int(cmds.manipOptions(q=True, mm=True)[0]),
            rp='SE'
        )

        # カメラのクリッププレーンを変更するウィンドウを表示する
        cmds.menuItem(
            parent=parent,
            l='Edit Camera Clip Plane', c=self.showCameraSettings,
            rp='S'
        )

        # クリックドラッグセレクトの切り替え
        cmds.menuItem(
            parent=parent, l='Click Drag Select', c=self.clickDragSelection,
            cb=cmds.selectPref(q=True, cld=True),
            rp='W'
        )

        # ポリゴンフェイスの選択タイプ(ポイントタイプ：フェイス全体タイプの切り替え)
        cmds.menuItem(
            parent=parent, l='Select Face with Whole Face',
            c=self.selectWholeFace,
            cb=cmds.polySelectConstraint(q=True, ws=True),
            rp='NW'
        )

        # カスタムParentツールウィンドウの表示
        cmds.menuItem(
            parent=parent,
            l='Parent Tool...',
            c=self.showParentTool,
            rp='SW'
        )

        # プリファレンスの表示
        cmds.menuItem(
            parent=parent,
            l='Preferences...',
            c=self.showPreference,
            rp='NE'
        )
    def command(self):
        mel.eval('Parent')

    def showPreference(self, *args):
        self.mel('preferencesWnd "timeslider";')

    def repositionMudButton(self, *args):
        cmds.manipOptions(mm=(cmds.manipOptions(q=True, mm=True)==0))

    def pickChooer(self, *args):
        cmds.selectPref(pms=(cmds.selectPref(q=True, pms=True) == 0))

    def clickDragSelection(self, *args):
        cmds.selectPref(cld=(cmds.selectPref(q=True, cld=True) == 0))

    def showCameraSettings(self, *args):
        import cameraSettings
        cameraSettings.showWindow()

    def selectWholeFace(self, *args):
        cmds.polySelectConstraint(
            ws=(cmds.polySelectConstraint(q=True, ws=True) == 0)
        )
        cmds.refresh()

    def showParentTool(self, *args):
        import parent
        parent.ParentTool().show()