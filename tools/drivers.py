#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    角度や長さを図るドライバーを作成するモジュール
    
    Dates:
        date:2017/02/25 18:51[Eske](eske3g@gmail.com)
        update:2024/10/07 15:36 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import node
cmds = node.cmds

GRIS_DISTANCE_DRIVER = ('grisDistanceDriverVersion', 1.0)

def createAngleDriver(targetNode, name='angleDriver#', parent=None):
    r"""
        angleDriverノードを作成する。
        
        Args:
            targetNode (str):参照元のオブジェクト名
            name (str):angleDriverノードの名前(デフォルトはangleDriver#)
            parent (str):angleDriverを作る親ノード
            
        Returns:
            node.Transform:作成されたドライバー機能コンテナ
    """
    targetNode = node.asObject(targetNode)

    cpsmtx = node.createNode('composeMatrix')
    invmtx = node.createNode('inverseMatrix')
    cpsmtx.attr('outputMatrix') >> invmtx.attr('inputMatrix')

    mltmtx = node.createNode('multMatrix')
    cpsmtx.attr('outputMatrix') >> mltmtx.attr('matrixIn[0]')
    mltmtx('matrixIn[1]', invmtx('outputMatrix'), type='matrix')
    invmtx.delete()

    md = [node.createNode('multiplyDivide') for x in range(2)]
    contained_nodes = [cpsmtx, mltmtx, md[0], md[1]]
    vectorlist = (
        ((0, 0, -1), (0, -1, 0)),
        ((-1, 0, 0), (0, 0, -1)),
        ((0, -1, 0), (-1, 0, 0)),
    )
    for i, axs in enumerate(vectorlist):
        vector = [0, 0, 0]
        vector[i] = 1

        pmm = node.createNode('pointMatrixMult')
        pmm('inPoint', vector)
        mltmtx.attr('matrixSum') >> pmm.attr('inMatrix')
        contained_nodes.append(pmm)

        agl = node.createNode('angleBetween')
        pmm.attr('o') >> agl.attr('vector1')
        agl('vector2', vector)
        contained_nodes.append(agl)

        for j, ax in enumerate(axs):
            dp = node.createNode('vectorProduct')
            contained_nodes.append(dp)
            agl.attr('axis') >> dp.attr('input1')
            dp('input2', ax)

            agl.attr('angle') >> md[j].attr('i1').children()[i]
            dp.attr('ox') >> md[j].attr('i2').children()[i]

    contained_nodes.extend(
        [
            node.asObject(cmds.listConnections(md[0]/'input1'+x, scn=False)[0])
            for x in 'XYZ'
        ]
    )
    sr = []
    for i in range(2):
        setrange = node.createNode('setRange')
        contained_nodes.append(setrange)
        setrange('oldMin', (-180, -180, -180))
        setrange('oldMax', (180, 180, 180))
        setrange('min', (-1, -1, -1))
        setrange('max', (1, 1, 1))
        ~md[i].attr('o') >> ~setrange.attr('v')
        sr.append(setrange)

    for n in contained_nodes:
        n('ihi', 0)

    # angleDriverノードとなる、containerノードの作成及び編集。=================
    drv = cmds.container(
            name=name, type='dagContainer', addNode=contained_nodes
    )
    if parent:
        drv = cmds.parent(drv, parent)[0]
    drv = node.Transform(drv)
    drv.lockTransform(k=False, l=False)
    drv('blackBox', 1, l=True)

    # 出力用アトリビュートの作成。---------------------------------------------
    cmds.addAttr(drv(), ln='angle', at='double3')
    for ax in ('XY', 'YZ', 'ZX'):
        cmds.addAttr(drv(), ln='angle' + ax, at='double', p='angle')

    cmds.addAttr(drv(), ln='angle2', at='double3')
    for ax in ('XZ', 'YX', 'ZY'):
        cmds.addAttr(drv(), ln='angle2' + ax, at='double', p='angle2')

    cmds.addAttr(drv(), ln='twist', at='double3')
    for ax in 'XYZ':
        cmds.addAttr(drv(), ln='twist' + ax, at='double', p='twist')
    # -------------------------------------------------------------------------

    for ax, attr in zip('yzx', drv.attr('twist').children()):
        md[0].attr('o'+ax) >> attr
        attr.setChannelBox(True)

    for ax, attr in zip('XYZ', drv.attr('angle').children()):
        sr[0].attr('outValue'+ax) >> attr
        attr.setKeyable(True)

    for ax, attr in zip('XYZ', drv.attr('angle2').children()):
        sr[1].attr('outValue'+ax) >> attr
        attr.setKeyable(True)

        attr = cmds.container(drv, e=True, publishName='inRotate'+ax)
        cmds.container(drv, e=True, bindAttr=(cpsmtx/'inputRotate'+ax, attr))
    attr = cmds.container(drv, e=True, publishName='inRotateOrder')
    cmds.container(drv, e=True, bindAttr=(cpsmtx/'inputRotateOrder', attr))
    
    for ax in 'XYZ':
        cmds.connectAttr(targetNode/'rotate'+ax, drv/'inRotate'+ax)
    cmds.connectAttr(targetNode/'rotateOrder', drv/'inRotateOrder')
    # =========================================================================

    return drv


def createEyeDriver(name, target, aimVector=[1, 0, 0]):
    r"""
        視線移動量をドライバー用値を返す機能を提供するノードを作成する。
        視線移動量は任意のジョイントの現在位置を基準地点として、垂直方向を
        verticalStrength+-1.0、水平方向をhorizontalStrength+-1.0として
        出力するアトリビュートを持つノードを作成する。
        
        Args:
            name (str):作成されるノードの名前
            target (str):ドライバとなるジョイント名
            aimVector (list):ドライバの視線方向となる軸
            
        Returns:
            node.Transform:作成されたドライバー機能コンテナ
    """
    contained_nodes = []
    tgt = node.asObject(target)
    dec = node.createUtil('decomposeMatrix')
    contained_nodes.append(dec)
    cmp = node.createUtil('composeMatrix')
    contained_nodes.append(cmp)
    tgt.attr('m') >> dec.attr('imat')
    ~dec.attr('or') >> ~cmp.attr('ir')
    pmm = node.createUtil('pointMatrixMult')
    contained_nodes.append(pmm)
    pmm('ip', aimVector)
    cmp.attr('omat') >> pmm.attr('im')
    basic_vec = node.MVector(pmm('o')[0])
    x_mtx = node.identityMatrix()
    l_x_mtx = node.multiplyMatrix([tgt.parent().inverseMatrix(), x_mtx])
    l_x_vec = node.MVector(l_x_mtx[0:3])

    # 垂直方向のローカル基準軸を決定。
    v_vec = basic_vec ^ l_x_vec
    # 水平方向のローカル基準軸を決定。
    h_vec = v_vec ^ basic_vec

    vps = []
    for v in (v_vec, h_vec):
        vp = node.createUtil('vectorProduct')
        vp('normalizeOutput', True)
        vp('i2', list(v))
        pmm.attr('o') >> vp.attr('i1')
        vps.append(vp)
        contained_nodes.append(vp)
    
    drv = node.asObject(
        cmds.container(
            name=name, type='dagContainer', addNode=contained_nodes
        )
    )
    drv.lockTransform(k=False, l=False)
    drv('blackBox', 1, l=True)
    for l, vp in zip(('vertical', 'horizontal'), vps):
        plug = drv.addFloatAttr(l + 'Strength', min=None, max=None)
        vp.attr('outputX') >> plug
        plug.setLock(True)
    return drv


def createDistanceDriver(
    startMatrixAttr, endMatrixAttr, name='', parent=None
):
    r"""
        2点の距離に応じて伸縮率を返すdistanceDriverを作成する。
        
        Args:
            startMatrixAttr (str):開始位置となるMatrixアトリビュート
            endMatrixAttr (str):終端位置となるMatrixアトリビュート
            name (str):ルートノードにつける名前
            parent (str):ルートノードを格納する親ノード名
            
        Returns:
            node.Transform:
    """
    start_matrix = node.asAttr(startMatrixAttr)
    if not start_matrix:
        raise AttributeError('Invalid attribute name : %s' % startMatrixAttr)
    end_matrix = node.asAttr(endMatrixAttr)
    if not end_matrix:
        raise AttributeError('Invalid attribute name : %s' % endMatrixAttr)

    # dagContainerに含むノードを先に作成する。=================================
    md = node.createUtil('multiplyDivide')
    md('operation', 2)
    contained_nodes = [md]

    bind_list = []
    for attr in ('startMatrix', 'endMatrix'):
        pmm = node.createUtil('pointMatrixMult')
        bind_list.append((pmm, attr))
        contained_nodes.append(pmm)
    # =========================================================================

    # ルートノードを作成する。
    flags = {'type':'dagContainer', 'addNode':contained_nodes}
    if name:
        flags['name'] = name
    root_node = cmds.container(**flags)
    root_node = (
        node.parent(root_node, parent)[0] if parent
        else node.asObject(root_node)
    )
    for attrs, src_attr in zip(bind_list, (start_matrix, end_matrix)):
        attr = cmds.container(root_node(), e=True, publishName=attrs[1])
        attr = cmds.container(
            root_node(), e=True, bindAttr=(attrs[0]/'inMatrix', attr)
        )
        src_attr >> root_node/attr[0]

        name = attrs[1].replace('Matrix', 'Offset')
        cmds.addAttr(root_node(), ln=name, at='double3')
        for ax in 'XYZ':
            cmds.addAttr(root_node(), ln=name+ax, p=name)
        attr = root_node.attr(name)
        for at in attr.children():
            at.setKeyable(True)
        attr >> attrs[0]+'.inPoint'

    root_node('blackBox', 1, l=True)
    ver_plug = root_node.addStringAttr(
        GRIS_DISTANCE_DRIVER[0], default=GRIS_DISTANCE_DRIVER[1]
    )
    ver_plug.setLock(True)

    distance = node.createNode('distanceDimShape', p=root_node)
    bind_list[0][0].attr('o') >> distance/'startPoint'
    bind_list[1][0].attr('o') >> distance/'endPoint'

    # ルートノードの初設定。===================================================
    root_node.editAttr(['t:a', 'r:a', 's:a', 'v'], k=False)

    dd_plug = root_node.addFloatAttr(
        'defaultDistance', sn='dd', min=None, max=None
    )
    dd_plug.set(distance('distance'))
    dd_plug.setLock(True)
    dd_plug.setKeyable(False)

    result_plug = root_node.addFloatAttr(
        'stretchFactor', sn='sf', min=None, max=None
    )
    # =========================================================================

    # 各種コネクションの作成。=================================================
    dd_plug >> md/'input2X'
    distance.attr('distance') >> md/'input1X'
    md/'outputX' >> result_plug
    # =========================================================================

    return root_node


def resetDistanceDriver(driverNodes=None):
    r"""
        任意のdistanceDriverノードを現在の状態をデフォルト値としてリセットする。
        
        Args:
            driverNodes (list):
    """
    driverNodes = node.selected(driverNodes)
    for driver in driverNodes:
        if (
            not driver.hasAttr(GRIS_DISTANCE_DRIVER[0]) or 
            not driver.hasAttr('defaultDistance')
        ):
            continue
        md = driver.attr('stretchFactor').source()
        plug = driver.attr('defaultDistance')
        with plug:
            plug.set(md('input1X'))
