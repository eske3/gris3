#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ルートモジュール
    
    Dates:
        date:2018/12/26 19:51[Eske](eske3g@gmail.com)
        update:2021/04/24 05:15 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2018 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""


def showFactory(
    directoryPath='', assetName='', assetType='', project='', isDockable=False,
    forceUpdate=False
):
    r"""
        Factoryを表示するエントリ関数。
        ProjectSelectorを経由せず直接任意のプロジェクトを開くには引数
        directoryPathにプロジェクトディレクトリを指定する。
        また、アセット名を強制的に指定する場合はassetName、タイプを指定する
        場合はassetType、プロジェクト名を指定する場合はprojectをそれぞれ
        設定する。
        これら３つの要素がない場合はプロジェクトディレクトリにある設定ファイル
        から自動設定される。
        
        Args:
            directoryPath (str):プロジェクトディレクトリ
            assetName (str):アセット名
            assetType (str):アセットタイプ
            project (str):プロジェクト名
            isDockable (bool):ドッキング可能かどうか
            forceUpdate (bool):強制的に更新をかけるかどうか
            
        Returns:
            factory.MainWindow:
    """
    from .ui import factory
    return factory.showWindow(
        directoryPath, assetName, assetType, project, isDockable, forceUpdate
    )


def showToolbar():
    r"""
        ツールバーを表示するエントリ関数
        
        Returns:
            gadgets.toolbar.MainGUI:
    """
    from . import gadgets
    return gadgets.openToolbar()
