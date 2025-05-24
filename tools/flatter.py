#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    任意の面ベクトルにオブジェクトや頂点を貼り付けるための機能を提供する。
    
    Dates:
        date:2017/08/17 22:43[Eske](eske3g@gmail.com)
        update:2020/10/02 12:17 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import node
from gris3.tools import util
cmds = node.cmds

def fitNodeToPlane(point, normal, nodeList=None):
    r"""
        Args:
            point (list):貼り付ける面を定義するXYZ座標。
            normal (list):貼り付ける面を定義する法線ベクトル。
            nodeList (list):面に貼り付けるオブジェクト。
    """
    if not nodeList:
        nodeList = cmds.ls(sl=True)
    if not nodeList:
        raise AttributeError('No nodes or components were specified.')
    vertexlist = cmds.filterExpand(nodeList, sm=31) or []
    nodeList = cmds.ls(nodeList, transforms=True)

    n = node.MVector(normal)
    nn = n.normalize()
    c = node.MVector(point)

    for objlist, getter in (
        (vertexlist, cmds.pointPosition),
        (nodeList, lambda x:cmds.xform(x, q=True, ws=True, t=True)),
    ):
        for obj in objlist:
            p = node.MVector(getter(obj))
            pa = p - c
            dist = pa * n
            pos = p - (nn * dist)
            cmds.xform(obj, ws=True, t=list(pos))

def fitVertsToFace(vertices=None, face=None):
    r"""
        任意のオブジェクトや頂点を、任意の面にフィットさせる。
        
        Args:
            vertices (list):貼り付けるオブジェクトのリスト
            face (str):貼り付け対象となるフェースの名前。
    """
    if not face:
        face = cmds.filterExpand(sm=34)
        if face:
            face = face[0]
    if not face:
        raise AttributeError('No face was specified.')
    n = util.getFaceNormal(face)
    c = util.getComponentCenter(face)[0]
    fitNodeToPlane(c, n, vertices)


class CameraInfo(util.CameraInfo):
    def flat(self, newVector, start, end):
        r"""
            Args:
                newVector (list):入力ベクトル
                start (QtCore.QPoint):ドラッグ開始座標
                end (QtCore.QPoint):ドラッグ終了座標
        """
        from maya.api.OpenMaya import MMatrix, MVector, MPoint, MQuaternion
        camera, view = self.cameraView()
        
        cam_matrix = MMatrix(cmds.getAttr(camera+'.worldMatrix'))
        cam_invmtx = MMatrix(cmds.getAttr(camera+'.worldInverseMatrix'))

        # マウスのポジションからアクティブなビューのクリック位置を求める。=====
        screen_pos = view.getScreenPosition()
        screen_rect = view.viewport()
        pt, vec = MPoint(), MVector()
        center = ((start.x()+end.x())/2, (start.y()+end.y())/2)
        view.viewToWorld(
            center[0]-screen_pos[0], screen_pos[1]+screen_rect[3]-center[1],
            pt, vec
        )

        # 上記ポイントをカメラ空間でローカル化。
        pt_matrix = MMatrix(
            (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, pt[0], pt[1], pt[2], 1)
        )
        pt_local = pt_matrix * cam_invmtx
        pt_local = list(pt_local)[12:15]
        # =====================================================================

        # UIからの軸をベースにカメラ空間での行列に変換。=======================
        newVector = MVector(newVector)
        z_vector = MVector(0, 0, 1)
        y_vector = z_vector ^ newVector
        local_matrix = MMatrix(
            [
                newVector[0], newVector[1], newVector[2], 0,
                y_vector[0], y_vector[1], y_vector[2],  0,
                z_vector[0], z_vector[1], z_vector[2], 0,
                0, 0, 0, 1
            ]
        )
        # =====================================================================

        # UIからの行列をクリック位置の行列に向けてクォータニオンで回転。=======
        # 回転角度を求める。
        vec_b = MVector(*pt_local)
        angle = vec_b.angle(-z_vector)

        vec_b[2] = 0
        n = vec_b.normalize() ^ newVector.normalize()
        test = n.normalize() * -z_vector
        angle = angle if test > 0 else -angle
        q = MQuaternion(angle, newVector)
        # =====================================================================

        world_matrix = local_matrix * q.asMatrix() * cam_matrix
        normal = list(world_matrix)[4:7]

        fitNodeToPlane((pt.x, pt.y, pt.z), normal)
