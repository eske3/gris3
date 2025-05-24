#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    メインとなる機能群を持つモジュール。
    
    Dates:
        date:2017/01/23 0:49[Eske](eske3g@gmail.com)
        update:2021/04/21 16:04 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import grisNode, func, lib, rigScripts
cmds = func.cmds
Do = func.Do
# /////////////////////////////////////////////////////////////////////////////
# パラメーター。                                                             //
# /////////////////////////////////////////////////////////////////////////////
AssetTypes = ['CH', 'BG', 'PR', 'CR', 'VE', 'FX', 'CP', 'SI']
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////


def selected(*args, **keywords):
    r"""
        選択ノードを返す。
        
        Args:
            *args (tuple):cmds.lsコマンドにわたす引き数と同じ
            **keywords (dict):cmds.lsコマンドにわたす引き数と同じ
            
        Returns:
            list:
    """
    keywords['sl'] = True
    return cmds.ls(*args, **keywords)


# /////////////////////////////////////////////////////////////////////////////
# ルートなどを作成する関数セット。                                           //
# /////////////////////////////////////////////////////////////////////////////
def getConstructorSystems(rootPath=''):
    r"""
        各種ルート作成用コマンドを取得するためのオブジェクト。
        ConstructorManager, FactorySettings, strをtupleで返す。

        Args:
            rootPath (str):Factory用のルートディレクトリパス
            
        Returns:
            tuple:(ConstructorManager, FactorySettings, str)
    """
    from gris3 import factoryModules, constructors
    cm = constructors.ConstructorManager()
    fs = factoryModules.FactorySettings()
    if rootPath:
        fs.setRootPath(rootPath)
    constructor_name = fs.constructorName()
    return cm, constructor_name, fs


def createRoot(rootPath=''):
    r"""
        基礎となるルートノード(grisNode.GrisRoot)を作成する。
        引数rootPathが指定されている場合は、そのディレクトリをFactory用の
        設定として使用する。
        
        Args:
            rootPath (str):factoryが定義されているディレクトリパス。
            
        Returns:
            grisNode.GrisRoot:
    """
    cm, constructor_name, fs = getConstructorSystems(rootPath)
    cmd = cm.getRootCreatorCmd(constructor_name)
    root = cmd()
    root.setAssetName(fs.assetName())
    root.setAssetType(fs.assetType())
    root.setProject(fs.project())
    cmds.select(root, r=True)
    return root

def createRootCtrl(rootPath='', size=100):
    r"""
        コントローラのルートを作成する。
        引数rootPathが指定されている場合は、そのディレクトリをFactory用の
        設定として使用する。
        
        Args:
            rootPath (str):Factory用のルートディレクトリパス。
            size (int):

        Returns:
            any:
    """
    root = grisNode.getGrisRoot()
    cm, constructor_name, fs = getConstructorSystems(rootPath)
    cmd = cm.getRootCtrlCreatorCmd(constructor_name)
    ctrl_root = cmd(root, size)
    return ctrl_root

def createModelRoot():
    r"""
        モデルを格納するルートを作成する。

        Returns:
            grisNode.AbstractTopGroup:
    """
    root = grisNode.createNode(grisNode.ModelAllGroup)
    for obj in root.setup():
        obj.setup()
    cmds.select(root, r=True)
    return root

def createConstructionScript(rootPath=''):
    r"""
        Constructorで使用するスクリプトを生成する。
        
        Args:
            rootPath (str):Factory用のルートディレクトリパス。
            
        Returns:
            any:
    """
    cm, constructor_name, fs = getConstructorSystems(rootPath)
    cmd, module = cm.getConstructionScriptCmd(constructor_name)
    result = cmd(fs, module)
    return result
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////


# /////////////////////////////////////////////////////////////////////////////
# リグ用モジュールに関する関数セット。                                       //
# /////////////////////////////////////////////////////////////////////////////
def execPreset(moduleName):
    r"""
        リグユニットのプリセットを実行する

        Args:
            moduleName (str):プリセット名
    """
    mod = rigScripts.getRigModule(moduleName, True)
    p = mod.Preset()
    p.execute()

def createJoint(
    unitType, baseName, position=1, suffix='', parent=None, options={}
):
    r"""
        引数unitTypeのユニットモジュールのJointCreatorから、
        ジョイントとユニットを作成する。
        
        Args:
            unitType (str):ユニット名
            baseName (str):作成されるジョイントのベースとなる名前
            position (int):位置を表す文字列
            suffix (str):サフィックス
            parent (grisNode.AbstractNode):親オブジェクト
            options (dict):オプションを表す辞書
            
        Returns:
            rigScripts.JointCreator:
    """
    module = rigScripts.getRigModule(unitType, True)

    # =========================================================================
    creator = module.JointCreator()

    if not parent:
        selection = cmds.ls(sl=True)
        # if not selection:
        #    raise RuntimeError('No parent was specified or selected.')
        # parent = selection[0]
        parent = selection[0] if selection else creator.jointRoot()
    else:
        parent = func.asObject(parent)
    
    creator.setParent(parent)
    creator.setName(baseName)
    creator.setSuffix(suffix)
    creator.setPosition(position)
    creator.setBasenameObject()
    creator.setOptions(options)
    creator.createBaseJoint(parent)
    # =========================================================================
    
    return creator

def createRig(unit):
    r"""
        指定したユニットのリグ作成メソッドを呼び出す関数。
        
        Args:
            unit (any):[str]grisNode.Unit
            
        Returns:
            any:
    """
    unitType = unit('unitName')
    side = unit('position')
    module = rigScripts.getRigModule(unitType, True)
    creator = module.RigCreator(unit)
    creator.createRig()

def createRigForAllUnit(withAllCtrl=True, rootPath=''):
    r"""
        ルート内にある全てのユニットのリグ作成メソッドを呼び出す。
        
        Args:
            withAllCtrl (True):[bool]
            
        Returns:
            any:
            
        Brief:
            引数withAllCtrlがTrueの場合、allのコントローラも作成する。
    """
    if withAllCtrl:
        createRootCtrl(rootPath)
    root = grisNode.getGrisRoot()
    unit_grp = root.unitGroup()
    for unit in unit_grp.listUnits():
        createRig(unit)
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////


# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////
def finalizeBaseSkeleton(
    withFixOrientation=False, withSetupInverseScale=False
):
    r"""
        ベースジョイントのファイナライズ処理を行う。
        withFixOrientation:がTrueの場合、ファイナライズ処理前にジョイント軸の
        補正を行う。
        
        Args:
            withFixOrientation (bool):
            withSetupInverseScale (bool):
    """
    # GrisRootノードを見つける。
    gris_root = grisNode.getGrisRoot()

    all_joints = []
    all_joints.extend(gris_root.baseJointGroup().allChildren(type='joint'))
    all_joints.reverse()

    # 全てのユニットのfinalize処理を行う。=====================================
    unit_grp = gris_root.unitGroup()
    for unit in unit_grp.listUnits():
        unitType = unit('unitName')
        module = rigScripts.getRigModule(unitType, True)
        creator = module.JointCreator(unit)
        creator.execFinalize()
    # =========================================================================

    # 全てのジョイントの軸調整を行う。=========================================
    if withFixOrientation:
        from gris3.tools import jointEditor
        jointEditor.fixOrientation(all_joints)
    # =========================================================================

    # 全てのジョイントのinvserseScale設定を行う。==============================
    if withSetupInverseScale:
        for joint in all_joints:
            joint.setInverseScale()
    # =========================================================================
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////