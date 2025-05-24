#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ホットキーを作成するモジュール。
    
    Dates:
        date:2017/05/30 5:12[Eske](eske3g@gmail.com)
        update:2020/10/13 14:43 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from maya import cmds

class Hotkey(object):
    r"""
        ホットキーを定義するクラス。
    """
    def __init__(self, name, command, ann='', category='GrisGadgets'):
        r"""
            ランタイムコマンド名、実行コマンド(python)、注釈を渡す。
            
            Args:
                name (str):コマンド名
                command (str):python実行コマンド
                ann (str):注釈
                category (str):カテゴリ
        """
        self.name = name
        self.command = command
        self.ann = ann
        self.cat = category

    def create(self):
        r"""
            ランタイムコマンドを生成する。
            
            Returns:
                bool:
        """
        if cmds.runTimeCommand(self.name, ex=True):
            return False
        try:
            cmds.runTimeCommand(
                self.name, cat=self.cat, c=self.command,
                ann=self.ann, cl='python'
            )
        except:
            return
        print('Generate hotkey command : %s' % self.name)

    def delete(self):
        r"""
            ランタイムコマンドを削除する。
        """
        if not cmds.runTimeCommand(self.name, ex=True):
            return
        cmds.runTimeCommand(self.name, e=True, delete=True)

class FunctionHotkey(Hotkey):
    r"""
        カテゴリがGrisCommandとして登録されるホットキークラス
    """
    def __init__(self, name, command, ann=''):
        r"""
            Args:
                name (str):コマンド名
                command (str):python実行コマンド
                ann (str):注釈
        """
        super(FunctionHotkey, self).__init__(name, command, ann, 'GrisCommand')

# /////////////////////////////////////////////////////////////////////////////
# ホットキーの定義。                                                         //
# /////////////////////////////////////////////////////////////////////////////
HOTKEY_TABLE = [
    # ウィジェット。===========================================================
    Hotkey(
        'OpenGrisAnimLibrary',
        'from gris3 import gadgets;gadgets.openAnimLibrary();',
        'Open Gris Anim Library'
    ),
    Hotkey(
        'OpenGrisSimUtility',
        'from gris3 import gadgets;gadgets.openSimUtility();',
        'Open Simulation Utility'
    ),
    Hotkey(
        'OpenGrisJointEditor',
        'from gris3 import gadgets;gadgets.openJointEditor();',
        'Open Joint Editor'
    ),
    Hotkey(
        'OpenGrisModelSetupWidget',
        'from gris3 import gadgets;gadgets.openModelSetup();',
        'Open Model Setup'
    ),
    Hotkey(
        'OpenGrisPolyHalfRemoverWidget',
        'from gris3 import gadgets;gadgets.openPolyHalfRemover();',
        'Open Poly Half Remover'
    ),
    Hotkey(
        'OpenGrisPolyMirrorWidget',
        'from gris3 import gadgets;gadgets.openPolyMirror();',
        'Open Poly Mirror'
    ),
    Hotkey(
        'OpenGrisPolyCutWidget',
        'from gris3 import gadgets;gadgets.openPolyCutter();',
        'Open Poly Cutter'
    ),
    Hotkey(
        'OpenNodeRenamer',
        'from gris3 import gadgets;gadgets.showRenamer();',
        'Open Renamer'
    ),
    Hotkey(
        'OpenNodeRenamerForProject',
        'from gris3 import gadgets;gadgets.showNodeRenamer();',
        'Open Node Renamer'
    ),
    Hotkey(
        'OpenSurfaceMaterialTools',
        'from gris3 import gadgets;gadgets.showSurfaceMaterialTools()',
        'Open Surface Material Tools'
    ),
    Hotkey(
        'OpenGrisFactory',
        'from gris3.ui import factory;factory.showWindow();',
        'Open GRIS Facotry'
    ),
    Hotkey(
        'OpenDockableGrisFactory',
        'from gris3.ui import factory;factory.showWindow(isDockable=True);',
        'Open Dockable GRIS Facotry'
    ),
    Hotkey(
        'OpenGrisToolbar',
        'from gris3 import gadgets;gadgets.openToolbar();',
        'Open GRIS Toolbar'
    ),
    # =========================================================================
    
    # 実行機能系。=============================================================
    FunctionHotkey(
        'grsExtractPolyFace',
        (
            'from gris3.tools import modelingSupporter;'
            'modelingSupporter.extractPolyFace();'
        ),
        'Extract selected poly faces.'
    ),
    FunctionHotkey(
        'grsDuplicatePolyFace',
        (
            'from gris3.tools import modelingSupporter;'
            'modelingSupporter.extractPolyFace(True);'
        ),
        'Duplicate selected poly faces.'
    ),
    FunctionHotkey(
        'grsCombinePolygons',
        (
            'from gris3.tools import modelingSupporter;'
            'modelingSupporter.Combine().operate();'
        ),
        'Duplicate selected poly faces.'
    ),
    FunctionHotkey(
        'grsBooleanUnion',
        (
            'from gris3.tools import modelingSupporter;'
            "modelingSupporter.Boolean('union').operate();"
        ),
        'Do boolean - union.'
    ),
    FunctionHotkey(
        'grsBooleanDifference',
        (
            'from gris3.tools import modelingSupporter;'
            "modelingSupporter.Boolean('difference').operate();"
        ),
        'Do boolean - difference.'
    ),
    FunctionHotkey(
        'grsBooleanIntersection',
        (
            'from gris3.tools import modelingSupporter;'
            "modelingSupporter.Boolean('intersection').operate();"
        ),
        'Do boolean - intersection.'
    ),
    FunctionHotkey(
        'grsRenameOppositeSide',
        (
            'from gris3.tools import nameUtility;'
            'nameUtility.renameOppositeSide();'
        ),
        'Rename selected to opposite side names.'
    ),
    FunctionHotkey(
        'grsSetManipAxisToSelected',
        (
            'from gris3.tools import operationHelper;'
            'operationHelper.setManipAxisToSelected()'
        ),
        (
            'Set axis of the move and scale manipulators'
            'to selected edge or Face.'
        )
    ),
    FunctionHotkey(
        'grsToggleWireframeOnShaded',
        (
            'from gris3.tools import operationHelper;'
            'operationHelper.toggleWireOnShaded()'
        ),
        'Toggle wireframe on shaded to the active panel.'
    ),
    FunctionHotkey(
        'grsToggleMakeLive',
        (
            'from gris3.tools import makelive;'
            'makelive.makeLive()'
        ),
        'Toggle make live.'
    ),
    FunctionHotkey(
        'grsClearMakeLivedObject',
        (
            'from gris3.tools import makelive;'
            'makelive.clearCache()'
        ),
        'Clear a chace of a make live object.'
    ),
    # =========================================================================
]

# Utility.=====================================================================
for cmd, ann in (
    (
        'switchSplitObject', 'Switch spliting by selected component type.'
    ),
    (
        'switchExtrude', 'Switch extruding by selected component type.'
    ),
    (
        'switchBevel', 'Switch beveling by selected component type.'
    ),
    (
        'switchReverse', 'Switch reversing by selected component type.'
    ),
    (
        'switchAttachNURBS',
        'Switch attaching NURBS by selected component type.'
    ),
    (
        'switchDettachNURBS',
        'Switch dettaching NURBS by selected component type.'
    ),
    (
        'switchRebuildNURBS',
        'Switch rebuilding NURBS by selected component type.'
    ),
    (
        'switchOpenCloseNURBS',
        'Switch to open / close NURBS by selected component type.'
    ),
):
    template = (
        'from gris3.tools import operationHelper;'
        'operationHelper.%s(%%s);' % cmd
    )
    for opt, label in zip(('False', 'True'), ('', 'Option')):
        hot_key = Hotkey(
            'grs%s%s%s' % (cmd[0].upper(), cmd[1:], label),
            template % opt,
            ann,
            'GrisOperationHelper'
        )
        HOTKEY_TABLE.append(hot_key)
# =============================================================================
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////

def createHotkey(table=HOTKEY_TABLE):
    r"""
        tableに渡されたHotkeyオブジェクトのリストに従ってホットキーを作成する。
        
        Args:
            table (list):
    """
    for hotkey in table:
        hotkey.create()

def refreshHotkey(table=HOTKEY_TABLE):
    r"""
        tableに渡されたHotkeyオブジェクトのリストに従ってホットキーを再生成する。
        
        Args:
            table (list):
    """
    for hotkey in table:
        hotkey.delete()
    createHotkey(table)