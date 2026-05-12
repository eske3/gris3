#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    便利ツールを提供するモジュール。
    
    Dates:
        date:2017/05/30 4:38[Eske](eske3g@gmail.com)
        update:2025/08/17 12:12 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
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


def openSkinningEditor():
    r"""
        スキニング用の補助ツールを開く。
        
        Returns:
            gadgets.skinningEditor.MainGUI:
    """
    from . import skinningEditor
    w = skinningEditor.showWindow()
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


def openDisplayLayerViewer():
    r"""
        ディスプレイレイヤを一括表示制御するビューワを開く。
        
        Returns:
            displayLayerViewer.MainGUI:
    """
    from . import displayLayerViewer
    w = displayLayerViewer.showWindow()
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


def openBlendShapeOperator(
    blendShapeName='', targetGeometry='', targetShapeContainer=''
):
    r"""
        ブレンドシェイプの管理・編集機能を提供するツールを開く。
        
        Args:
            blendShapeName (str):ブレンドシェイプ名
            targetGeometry (str):ブレンドシェイプを適用されるノード名
            targetShapeContainer (str):シェイプターゲットを格納するグループ名
   
        Returns:
            blendShapeOperator.MainGUI:
    """
    from . import blendShapeOperator
    return blendShapeOperator.showWindow(
        blendShapeName, targetGeometry, targetShapeContainer
    )


def showRenamer():
    r"""
        リネーマーを表示する。
    """
    from . import renamer
    renamer.showWindow()


def showAutoRenamer():
    r"""
        自動リネームツールを起動する。
    """
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
        アクティブなパネルのカメラディスプレイ設定を開く。
        
        Returns:
            QWidget:
    """
    from . import displaySettings
    return displaySettings.showWindow()


def openMaterialManager():
    r"""
        シーン中のマテリアルのアサイン状況と名前を管理するマネージャーを開く。
        
        Returns:
            materialManager.MainGUI:
    """
    from . import materialManager
    return materialManager.showWindow()


def showSurfaceMaterialTools():
    r"""
        マテリアル一覧を表示するウィンドウを開く。
    """
    from . import surfaceMaterialTools
    surfaceMaterialTools.showWindow()


def openCheckTools(categoryFile=''):
    r"""
        チェックツールを開く。
        
        Args:
            categoryFile (any):
            
        Returns:
            checkTools.MainGUI:
    """
    from . import checkTools
    w = checkTools.showWindow(categoryFile)
    return w


def openGagetsLauncher():
    r"""
        ガジェットランチャーを開く。
        
        Returns:
            gadgetsLauncher.MainGUI:
    """
    from . import gadgetsLauncher
    gadgetsLauncher.showWindow()


def openScriptExecutor():
    r"""
        スクリプト登録・実行ツールを開く。
        
        Returns:
            scriptExecUtility.MainGUI:
    """
    from . import scriptExecUtility
    scriptExecUtility.showWindow()

