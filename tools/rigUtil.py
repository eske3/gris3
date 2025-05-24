#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2022/06/08 14:22 Eske Yoshinob[eske3g@gmail.com]
        update:2024/02/16 13:47 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2022 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from . import selectionUtil
from .. import node
cmds = node.cmds


class PolyUvPinner(object):
    MessageAttr = 'grsPinTarget'
    def __init__(self, name=None):
        r"""
            Args:
                name (str):
        """
        super(PolyUvPinner, self).__init__()
        self.__target_poly = None
        self.__pin_node = None
        self.__exist_pin = False
        self.__outmesh_plug = 'outMesh'
        self.__post_callback = self.defaultCallback
        self.setTargetPolygon(name)

    def setTargetPolygon(self, polyName=None):
        r"""
            ピンどめ先のメッシュを指定する。
            指定先の名前がメッシュではない場合、Noneを返す。
            
            Args:
                polyName (str):
                
            Returns:
                str:セットされたメッシュシェイプ
        """
        if not polyName:
            self.__target_poly = None
            return
        mesh = selectionUtil.listShapes('mesh', polyName)
        if not mesh:
            return
        self.__target_poly = mesh[0]
        return self.__target_poly

    def targetPolygon(self):
        r"""
            Returns:
                str:セットされているメッシュシェイプ名
        """
        return self.__target_poly

    def setOutmeshPlug(self, attrName):
        r"""
            メッシュから繋ぐアトリビュート名を指定する。
            
            Args:
                attrName (str):
        """
        self.__outmesh_plug = attrName

    def outmeshPlug(self):
        r"""
            uvPinノードにつなぐメッシュの出力アトリビュート名を返す。
            デフォルトではoutMeshを返す。
            
            Returns:
                str:アトリビュート名
        """
        return self.__outmesh_plug

    def setPinNode(self, pinName):
        r"""
            Args:
                pinName (str):
        """
        self.__pin_node = pinName

    def pinNode(self):
        return self.__pin_node

    def isUsingExistingPin(self):
        return self.__exist_pin

    def setIsUsingExistingPin(self, state):
        r"""
            対象となるメッシュに既にuvPinが刺さっている場合、それを使用するか
            どうかを指定する。
            
            Args:
                state (bool):
        """
        self.__exist_pin = bool(state)

    def getPinNode(self):
        r"""
            設定に応じて新規か既存のuvPinを返す。
            戻り値のuvPinは必ずシーンに存在しているノートであり、設定によって
            存在したものを取得できない場合はエラーを返す。
            
            Returns:
                str:
        """
        mesh = node.asObject(self.targetPolygon())
        if not mesh:
            raise RuntimeError('A polygon mesh is not specified.')
        if self.isUsingExistingPin():
            pin_node = self.pinNode()
            if pin_node:
                pin_node = node.selected(pin_node, type='uvPin')
                if not pin_node:
                    raise RuntimeError('The specified uvPin does not exist.')
                return pin_node[0]
            pin_nodes = []
            for attr in ('outMesh', 'worldMesh', 'outSmoothMesh'):
                pin_nodes.extend(
                    [
                        x.nodeName() for x in
                        mesh.attr(attr).destinations(type='uvPin', p=True)
                        if x.endswith('deformedGeometry')
                    ]
                )
                if pin_nodes:
                    break
            if pin_nodes:
                return pin_nodes[0]
        pin_node = node.createUtil('uvPin')
        mesh.attr(self.outmeshPlug()) >> pin_node/'deformedGeometry'
        return pin_node

    def getPinAndLatestIndex(self):
        pin_node = node.asObject(self.getPinNode())
        attrs = cmds.listAttr(pin_node/'outputMatrix', m=True)
        if attrs:
            r = node.index_reobj.search(attrs[-1])
            if r:
                return pin_node, int(r.group(2)) + 1
        return pin_node, 0

    def defaultCallback(self, pinNode, target, mesh, index):
        r"""
            Args:
                pinNode (any):
                target (any):
                mesh (any):
                index (any):
        """
        m_plug = target.attr('message')
        if pinNode.hasAttr(self.MessageAttr):
            con = m_plug.destinations(type='uvPin', p=True)
            if con:
                for c in con:
                    r = node.index_reobj.search(c.attrName())
                    if not r:
                        continue
                    i = int(r.group(2))
                    if self.MessageAttr != r.group(1):
                        continue
                    if i == index:
                        return
                    c.disconnect()
        else:
            cmds.addAttr(pinNode, ln=self.MessageAttr, at='message', m=True)
        m_plug >> '{}.{}[{}]'.format(pinNode, self.MessageAttr, index)

    def addPostCallback(self, func):
        r"""
            UVピンを作成したあとのカスタム処理を追加する。
            引数は関数であり、以下のフォーマットに従う必要がある。
            callback(pinNode, target, mesh, index)
            pinNode : ピン付に仕様されたピンノード
            target : ピン付けされたtransformノード
            mesh : ピン付け先のメッシュ
            index : ピンとの接続に使用されているインデックス
            
            Args:
                func (function):関数
        """
        self.__post_callback = func

    def postCallback(self):
        r"""
            UVピンを作成したあとのカスタム処理の関数を返す。
            addPostCallbackで関数を設定できる。
            デフォルトではPolyUvPinner.defaultCallbackが設定されている。
            
            Returns:
                func:関数
        """
        return self.__post_callback

    def execute(self, targets=None):
        r"""
            Args:
                targets (list):ピン止めするTransform名のリスト
        """
        mesh = node.asObject(self.targetPolygon())
        transforms = node.selected(targets, type='transform')

        pin_node, i = self.getPinAndLatestIndex()
        for trs in transforms:
            rp = trs.rotatePivot()
            uv = mesh.closestUV(rp)
            pin_node('coordinate[{}].coordinateU'.format(i), uv[0])
            pin_node('coordinate[{}].coordinateV'.format(i), uv[1])
            pin_mtx = node.MMatrix(pin_node('outputMatrix[{}]'.format(i)))
            offset_mtx = node.MMatrix(trs.matrix()) * pin_mtx.inverse()
            
            mltmtx = node.createUtil('multMatrix')
            mltmtx('matrixIn[0]', list(offset_mtx), type='matrix')
            (
                pin_node.attr('outputMatrix[{}]'.format(i))
                >> '{}.matrixIn[1]'.format(mltmtx)
            )
            trs.attr('pim') >> '{}.matrixIn[2]'.format(mltmtx)

            decmtx = node.createUtil('decomposeMatrix')
            mltmtx.attr('matrixSum') >> decmtx/'inputMatrix'
            for attr in 'tr':
                ~decmtx.attr('o'+attr) >> ~trs.attr(attr)
            if self.__post_callback:
                self.__post_callback(pin_node, trs, mesh, i)
            i += 1


def connectMeshKeepingShape(input, target):
    r"""
        ポリゴンoutMeshのoutMeshをポリゴンtargetのinMeshに接続する。
        inputとtargetは同トポロジのポリゴンである必要がある。

        Args:
            input (str):接続元のメッシュ
            target (str):接続先のメッシュ
    """
    from maya.api import OpenMaya
    orig_list = [input, target]
    input, target = node.toObjects(
        selectionUtil.listShapes(['mesh'], orig_list)
    )
    for o, n in zip(orig_list, [input, target]):
        if not n:
            raise RuntimeError(
                'The node "{}" was not found in the current scene.'.format(o)
            )
    sel = OpenMaya.MSelectionList()
    sel.add(target)
    dag_path = sel.getDagPath(0)
    mit_vtx = OpenMaya.MItMeshVertex(dag_path)

    vertex_pos = [
        x.position(OpenMaya.MSpace.kTransform) for x in mit_vtx
    ]
    mit_vtx.reset()
    input.attr('outMesh') >> target.attr('inMesh')
    for pos, vtx in zip(vertex_pos, mit_vtx):
        vtx.setPosition(pos, OpenMaya.MSpace.kTransform)
