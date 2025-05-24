#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    クリーンナップ用の機能を提供するモジュール。
    
    Dates:
        date:2017/02/13 23:59[Eske](eske3g@gmail.com)
        update:2024/06/07 16:04 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import node
cmds = node.cmds


DefaultShadingEngines = ['initialParticleSE', 'initialShadingGroup', 'defaultTextureList1']


def deleteAllDisplayLayers():
    r"""
        シーン中の全てのdisplayLayerを削除する。
    """
    print('# Delete all display layers.'.ljust(80, '='))
    for layer in cmds.ls(type='displayLayer'):
        if layer == 'defaultLayer':
            continue
        try:
            cmds.delete(layer)
        except:
            pass
        else:
            print('    Delete "%s".' % layer)
    print('=' * 80)


def disableOverrideEnables(nodeName, affectToChildren=True):
    r"""
        指定したノード（とその子）のoverrideEnablesをオフにする。
        
        Args:
            nodeName (str):
            affectToChildren (bool):子にも適用するかどうか
    """
    nodeName = node.asObject(nodeName)
    if not nodeName:
        return

    if affectToChildren:
        nodes = nodeName.allChildren()
        nodes.append(nodeName)
    else:
        nodes = [nodeName]

    print('# Delete all display layers.'.ljust(80, '='))
    locked_attrs = []
    for n in nodes:
        attr = n.attr('overrideEnabled')
        if not attr:
            continue
        if attr.get() == 0:
            continue

        if attr.isLocked():
            locked_attrs.append(attr)
            attr.setLock(False)
        try:
            attr.set(0)
        except:
            pass
        else:
            print('    Disable override enables : %s' % n)
    for attr in locked_attrs:
        attr.setLock(True)
    print('=' * 80)


def resetTransformDisplay(nodelist=None, affectToChildren=False):
    r"""
        Args:
            nodelist (list):
            affectToChildren (bool):子にも適用するかどうか
    """
    nodelist = node.selected(nodelist, type='transform')
    if affectToChildren:
        nodelist.extend(
            node.listRelatives(*nodelist, type='transform', ad=True)
        )
    attrlist = (
        'displayHandle', 'displayLocalAxis',
        'displayRotatePivot', 'displayScalePivot'
    )
    for n in nodelist:
        for attr in attrlist:
            n(attr, 0)


def deleteUnusedIO(nodelist=None, showResults=True):
    r"""
        指定したノード下にある不要なintermediateObjectsを削除する
        
        Args:
            nodelist (list):[]削除対象ノードのリスト
            showResults (bool):結果を表示するかどうか
    """
    nodelist = node.selected(nodelist, type='transform')
    intermediates = []
    deleted = []
    for trs in nodelist:
        io = [
            x for x in trs.children()
            if x('io') and not cmds.listConnections(x())
        ]
        if io:
            intermediates.extend(io)
            deleted.append((trs(), len(io)))

    if not intermediates:
        return
    cmds.delete(intermediates)
    if not showResults:
        return
    print('# Delete unused intermediate objects.'.ljust(80, '='))
    for d, num in deleted:
        key = 'object' if num == 1 else 'objects'
        print('    - %s (%s %s deleted.)' % (d, num, key))
    print('=' * 80)


def deleteUnusedUserDefinedAttr(nodelist=None, showResults=True):
    r"""
        Args:
            nodelist (list):
            showResults (bool):結果を表示するかどうか
    """
    nodelist = node.selected(nodelist)
    if showResults:
        print('# Delete unused user defined attrs.'.ljust(80, '='))
    for n in nodelist:
        dynamic_attrs = n.listAttr(ud=True)
        if not dynamic_attrs:
            continue
        if showResults:
            print('    %s' % n)
        for attr in dynamic_attrs:
            if cmds.listConnections(attr()):
                continue
            if showResults:
                print('    - %s' % attr)
            cmds.deleteAttr(attr)
    if showResults:
        print('=' * 80)


def removeAllVertexColorSets(nodelist=None, showResults=True):
    r"""
        任意のメッシュの頂点カラーセットをすべて削除する。

        Args:
            nodelist (list):
            showResults (bool):
    """
    nodelist = node.selected(nodelist)
    if showResults:
        print('# Remove all vertex color sets.'.ljust(80, '='))
    for n in nodelist:
        if not n.isType('mesh'):
            if not hasattr(n, 'children'):
                continue
            meshs = n.children(type='mesh')
            if not meshs:
                continue
        else:
            meshs = [n]
        for mesh in meshs:
            colorsets = cmds.polyColorSet(mesh, q=True, acs=True)
            if not colorsets:
                continue
            if showResults:
                print('  Remove color sets : {}'.format(mesh))
            for s in colorsets:
                if showResults:
                    print('    - {}'.format(s))
                cmds.polyColorSet(mesh, delete=True, colorSet=s)
    if showResults:
        print('=' * 80)


def deleteDagPoses():
    r"""
        シーン中のdagPoseノードをすべて削除する。
    """
    dag_poses = cmds.ls(type='dagPose')
    if dag_poses:
        cmds.delete(dag_poses)


def unloadPlugins(plugins):
    r"""
        任意のプラグインのロードを強制的にアンロードする。

        Args:
            plugins (list): プラグイン名のリスト。
    """
    from maya import cmds
    print('Unload plugins'.ljust(80, '='))
    for plugin in plugins:
        try:
            if cmds.pluginInfo(plugin, q=True, l=True):
                cmds.unloadPlugin(plugin, f=True)
                print('  - Unload plugin "{}"'.format(plugin))
        except Exception as e:
            print('  ! {}'.format(e.args[0]))
    print('=' * 80)


def removeUnknownPlugins():
    r"""
        不要なプラグイン情報を削除する。
    """
    cmds = node.cmds
    unknown_plugins = cmds.unknownPlugin(q=True, l=True) or []
    for p in unknown_plugins:
        try:
            cmds.unknownPlugin(p, r=True)
            print('Removed unknown plugin : {}'.format(p))
        except Exception as e:
            print('[Warning] Failed to remove : %s' % p)
            print('    %s' % e.args[0])


def unlockInitialShadings():
    r"""
        シェーディングのロックを解除する。
    """
    targets = cmds.ls(DefaultShadingEngines)
    if targets:
        cmds.lockNode(targets, l=0, lu=0)


def deleteAllUnknownNodes():
    r"""
        unknownNodesをすべて削除する。
        ロックがかかっていてもロックを解除してから削除を実行する。
    """
    cmds = node.cmds
    unknown_nodes = cmds.ls(type=('unknown', 'unknownDag'))
    if not unknown_nodes:
        return
    for unknown in unknown_nodes:
        cmds.lockNode(unknown, l=False)
    cmds.delete(unknown_nodes)
    print('Removed below unknown nodes.'.ljust(80, '='))
    for unknown in unknown_nodes:
        print('    %s' % unknown)
    print('=' * 80)

