#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2021/05/04 03:44 eske yoshinob[eske3g@gmail.com]
        update:2021/05/04 06:18 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2021 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import math
from .. import node
from ..tools import util
from ..uilib import mayaUIlib


def searchChain(trs, nodeType='transform'):
    r"""
        Args:
            trs (any):
            nodeType (any):
    """
    result = []
    for attr in ('rx', 'ry', 'rz'):
        if not trs(attr, k=True) or trs(attr, l=True):
            break
    else:
        result.append(trs)
    for c in trs.children(type=nodeType):
        result.extend(searchChain(c, nodeType))
        break
    return result


def setPositionFromData(
    trsChain, data, aimAxis=None, upAxis=None, worldUpAxis=None
):
    r"""
        Args:
            trsChain (list):
            data (list):DrawerOnCamera.drawVectorDataによって生成されたデータ
            aimAxis (list):操作対象ノードが向けるベクトル
            upAxis (any):
            worldUpAxis (list):アップ軸を向ける方向を示すベクトル
    """
    total_len = 0
    last_index = 0
    num = len(data)
    j_num = len(trsChain)
    c_p = node.MVector(trsChain[0].position())
    pre_v = node.MVector()
    poslist = []
    for i in range(j_num):
        if i < j_num-1:
            # 事前情報の取得
            n_p = node.MVector(trsChain[i+1].position())
            v = c_p - n_p
            pre_v = v
            c_p = n_p
        else:
            v = pre_v
        for j in range(last_index, num):
            if total_len < data[j][-1]:
                last_index = j-1
                break
        start, vector, l = data[last_index]
        move_vec = vector * (total_len-l)
        goal = start + move_vec
        poslist.append(goal)
        total_len += v.length()

    for i in range(j_num-1):
        trs = trsChain[i]
        # ワールド空間上で向かせるベクトル
        aim_vec = (poslist[i+1] - poslist[i]).normal()
        
        if not aimAxis:
            # 自動設定が有効の場合、全ての軸を自動的に決定する。
            main, opposite, sub = util.detectAimAxis(trs, trsChain[i+1])
            l = [0, 0, 0]
            l[main] = 1 * opposite
            basic_aim_vec = node.MVector(l)
            l = [0, 0, 0]
            l[sub] = 1
            basic_up_axis = node.MVector(l)
            mtx = trs.matrix()
            world_up_vec = node.MVector((mtx[0:3], mtx[4:7], mtx[8:11])[sub])
        else:
            basic_aim_vec = node.MVector(aimAxis)
            world_up_vec = worldUpAxis
        if upAxis:
            basic_up_axis = upAxis

        # アップベクトルの定義
        up_vec = node.MVector(world_up_vec)
        w_vec = (aim_vec ^ up_vec).normal()
        up_vec = w_vec ^ aim_vec

        # 主軸のクォータニオン回転を作成。
        quaternion = node.MQuaternion(basic_aim_vec, aim_vec)

        upRotated = basic_up_axis.rotateBy(quaternion)
        angle = math.acos(upRotated * up_vec)
        quaternionV = node.MQuaternion(angle, aim_vec)
        if not up_vec.isEquivalent(upRotated.rotateBy(quaternionV), 1.0e-5):
            angle = (2*math.pi) - angle
            quaternionV = node.MQuaternion(angle, aim_vec)
        quaternion *= quaternionV

        trs_mtx = node.MTransformationMatrix(node.MMatrix(trs.matrix()))
        trs_mtx.reorderRotation(trs._node().rotationOrder())
        trs_mtx.setRotation(quaternion)
        trs_mtx.setTranslation(poslist[i], node.MSpace.kWorld)
        trs.setMatrix(list(trs_mtx.asMatrix()))
        # trs.setPosition(pos)


def moveChainByDrawn(aimAxis=None, upAxis=None, worldUpAxis=None):
    r"""
        Args:
            aimAxis (list):操作対象ノードが向けるベクトル
            upAxis (list):操作対象ノードが向けるアップベクトル
            worldUpAxis (list):アップ軸を向ける方向を示すベクトル
    """
    transforms = node.selected(type='transform')
    if not transforms:
        raise RuntimeError('No transform objects was selected.')
    dc = mayaUIlib.DrawerOnCamera(mayaUIlib.MainWindow)
    if not dc.isValid():
        dc.deleteLater()
        del dc
        return

    if not dc.exec_():
        return

    if not worldUpAxis:
        # worldUpAxisの指定がない場合はカメラの視線ベクトルを使用する。
        worldUpAxis = dc.cameraAimVector()

    for trs in transforms:
        trschain = searchChain(trs)
        data = dc.drawVectorData(trs.position())
        setPositionFromData(trschain, data, aimAxis, upAxis, worldUpAxis)
