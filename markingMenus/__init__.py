# -*- coding: utf-8 -*-
r'''
    @file     __init__.py
    @brief    ここに説明文を記入
    @function execCommand : 与えられたモジュールのMarkingMenuクラスを呼び出し実行する
    @function selectToolCommand : ここに説明文を記入
    @function showAttributeEditor : AttributeEditorの表示ならびにサブメニューの表示
    @function parentAndPreference : parentの実行、もしくはプレファレンスにまつわるメニューの表示
    @function showDisplayMenu : parentの実行、もしくはプレファレンスにまつわるメニューの表示
    @function showModelDisplayMenu : ここに説明文を記入
    @date        2018/03/08 1:14[Eske](eske3g@gmail.com)
    @update      2018/04/07 3:58[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
def execCommand(mode, module, cls='MarkingMenu'):
    r'''
        @brief  与えられたモジュールのMarkingMenuクラスを呼び出し実行する
        @brief  modeは０でメニューの表示、１でコマンドの実行
        @param  mode : [int]
        @param  module : [str]モジュール名
        @return None
    '''
    mm = getattr(module, cls)()
    if mode == 0:
        mm.showMenu()
    else:
        mm.execute()

def selectToolCommand(mode):
    r'''
        @brief  ここに説明文を記入
        @param  mode : [int]
        @return None
    '''
    from . import selectToolMM
    execCommand(mode, selectToolMM)

def showAttributeEditor(mode):
    r'''
        @brief  AttributeEditorの表示ならびにサブメニューの表示
        @param  mode : [int]
        @return None
    '''
    from . import attributeEditorMM
    execCommand(mode, attributeEditorMM)

def parentAndPreference(mode):
    r'''
        @brief  parentの実行、もしくはプレファレンスにまつわるメニューの表示
        @param  mode : [int]
        @return None
    '''
    from . import parentAndPreferenceMM
    execCommand(mode, parentAndPreferenceMM)

def showDisplayMenu(mode):
    r'''
        @brief  表示のリセット、もしくは表示にまつわるメニューの表示
        @param  mode : [int]
        @return None
    '''
    from . import displayMM
    execCommand(mode, displayMM)

def showModelDisplayMenu(mode):
    r'''
        @brief  isolateの実行、もしくはモデル表示にまつわるメニューの表示
        @param  mode : [int]
        @return None
    '''
    from . import modelDisplayMM
    execCommand(mode, modelDisplayMM)

def showCopyMenu(mode):
    from . import copyAndPasteMM
    execCommand(mode, copyAndPasteMM, 'CopyMarkingMenu')

def showPasteMenu(mode):
    from . import copyAndPasteMM
    execCommand(mode, copyAndPasteMM, 'PasteMarkingMenu')