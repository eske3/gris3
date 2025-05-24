#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    便利ツールを提供するモジュール。
    
    Dates:
        date:2017/05/30 4:38[Eske](eske3g@gmail.com)
        update:2020/10/20 06:06 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
def showWindow(uiClass, execute=False):
    r"""
        渡されたuiClassを使用してウィンドウを表示する。
        
        Args:
            uiClass (type):
            execute (bool):
            
        Returns:
            QtWidgets.QWidget:
    """
    from gris3.uilib import mayaUIlib
    ui = uiClass(mayaUIlib.MainWindow)
    ui.show()
    return ui


def openToolbar():
    r"""
        ツールバーを表示する
        
        Returns:
            gadgets.toolbar.MainGUI:
    """
    from . import toolbar
    w = toolbar.showWindow()
    return w


def openJointEditor():
    r"""
        ジョイント編集ウィンドウを開く。
        
        Returns:
            gadgets.jointEditorWidget.MainGUI:
    """
    from . import jointEditorWidget
    w = jointEditorWidget.showWindow()
    return w


def openModelSetup():
    r"""
        モデルを整理するウィンドウを開く。
        
        Returns:
            gadgets.modelSetupWidget.MainGUI:
    """
    from . import modelSetupWidget
    w = modelSetupWidget.showWindow()
    return w


def openPolyHalfRemover():
    r"""
        ポリゴンの半分を消去するためのウィンドウを開く。
        
        Returns:
            gadgets.modelSetupWidget.PolyHalfRemoverWidget:
    """
    from . import modelSetupWidget
    w = modelSetupWidget.showPolyHalfRemover()
    return w


def openPolyMirror():
    r"""
        ポリゴンをミラーするためのウィンドウを開く。
        
        Returns:
            gadgets.modelSetupWidget.PolyMirrorWidget:
    """
    from . import modelSetupWidget
    w = modelSetupWidget.showPolyMirror()
    return w


def openPolyCutter():
    r"""
        ポリゴンを任意の軸でカットするためのウィンドウを開く。
        
        Returns:
            gadgets.modelSetupWidget.PolyCutWidget:
    """
    from . import modelSetupWidget
    w = modelSetupWidget.showPolyCutter()
    return w


def openHardsurfacer():
    r"""
        モデルを整理するウィンドウを開く。
        
        Returns:
            gadgets.hardsurfacer.MainGUI:
    """
    from . import hardsurfacer
    w = hardsurfacer.showWindow()
    return w


def openAnimLibrary():
    r"""
        ポーズ・アニメーションのライブラリを開く。
        
        Returns:
            any:.QWidget
    """
    from .animLibrary import ui
    ui.showWindow()
    return ui


def openSimUtility():
    r"""
        シミュレーションの補助ツールを開く。
        
        Returns:
            any:.QWidget
    """
    from .simUtility import ui
    ui.showWindow()
    return ui


def showRenamer():
    r"""
        リネーマーを表示する。
    """
    from . import renamer
    renamer.showWindow()


def showAutoRenamer():
    from . import renamer
    renamer.showAutoRenameWindow()

def showNodeRenamer():
    r"""
        ノード名の個別要素編集機能のあるリネーマーを起動する。
    """
    from . import nodeRenamer
    nodeRenamer.showWindow()


def showDisplaySettings():
    r"""
        ディスプレイ設定を開く。
        
        Returns:
            QWidget:
    """
    from . import displaySettings
    return displaySettings.showWindow()


def showSurfaceMaterialTools():
    r"""
        マテリアル一覧を表示するウィンドウを開く。
    """
    from . import surfaceMaterialTools
    surfaceMaterialTools.showWindow()


def showCheckTools(categoryFile=''):
    r"""
        チェックツールを開く。

        Returns:
            checkTools.MainGUI:
    """
    from . import checkTools
    w = checkTools.showWindow()
    w.main().setCategoryFromFile(categoryFile)
    return w


