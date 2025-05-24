#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    UV編集を行うためのサポート機能を提供する。
    
    Dates:
        date:2017/08/17 22:43[Eske](eske3g@gmail.com)
        update:2024/08/21 19:45 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import re, time
from maya import mel
from maya.api import OpenMaya
from gris3 import node
from gris3.tools import util, selectionUtil
cmds = node.cmds


# DEBUG.***************************************************************
def updateView(t=0.5):
    r"""
        Args:
            t (any):
    """
    cmds.textureWindow(
        cmds.getPanel(sty='polyTexturePlacementPanel'), e=True, ref=True
    )
    time.sleep(t)
# *********************************************************************

def alignGridUV(faces=None):
    r"""
        ポリゴンフェースのUVをグリッド状に配置する。
        選択フェースは必ずすべて４角ポリゴンである必要がある。
        
        Args:
            faces (list):操作対象となるフェースのリスト。
    """
    class Uv(int):
        r"""
            UV名とそれに付随する情報を持つクラス。
        """
        def __new__(cls, uvid, shape, edgelist, face_ids, position):
            r"""
                Args:
                    uvid (any):
                    shape (any):
                    edgelist (any):
                    face_ids (any):
                    position (any):
            """
            obj = super(Uv, cls).__new__(cls, uvid)
            obj.shape = shape
            obj.edges = edgelist
            obj.face_ids = set(face_ids)
            obj.is_done = False
            obj.p = position
            obj.init_p = position[:]
            obj.numEdges = len(edgelist)
            return obj

        def __call__(self):
            return '%s.map[%s]' % (self.shape, self)

        def update(self, edgelist, applyIndex=False):
            r"""
                Args:
                    edgelist (list):
                    applyIndex (any):
            """
            self.edges = list(
                {
                    edgelist[edgelist.index(x)]
                    for x in self.edges if x in edgelist
                }
            )
            for edge in self.edges:
                edge.uvs.add(self)
            self.numEdges = len(self.edges)

        def position(self, initPosition=False):
            r"""
                UVの位置を返す。
                
                Args:
                    initPosition (any):
                    
                Returns:
                    list:
            """
            return self.init_p if initPosition else self.p

        def move(self, u, v):
            r"""
                UVを任意の座標に移動する。
                移動後、positionで返す内容は更新される。
                
                Args:
                    u (float):
                    v (float):
            """
            cmds.polyEditUV(self(), r=False, u=u, v=v)
            self.p = [u, v]

    class Edge(int):
        r"""
            エッジ名とそれに付随する情報を持つクラス。
            メンバー変数facesにはこのエッジに接するフェース名がset形式で格納
            されている。
        """
        def __new__(cls, edge):
            r"""
                Args:
                    edge (int):エッジ番号
            """
            obj = super(Edge, cls).__new__(cls, edge)
            obj.faces = set()
            obj.uvs = set()
            obj.counts = 0
            return obj

        def toUvs(self):
            return list(self.uvs)


    # DEBUG.***************************************************************
    def updateView(t=0.5):
        r"""
            Args:
                t (any):
        """
        cmds.textureWindow(
            cmds.getPanel(sty='polyTexturePlacementPanel'), e=True, ref=True
        )
        time.sleep(t)
    # *********************************************************************

    def align(uv, xEdgeData, yEdgeData, allUvs):
        r"""
            uvに接続される隣接UVの位置をグリッド状に位置合わせする。
            
            Args:
                uv (Uv):操作対象元のUVコンポーネント名。
                xEdgeData (list):X軸相当のエッジ名と向き
                yEdgeData (list):Y軸相当のエッジ名と向き
                allUvs (list):操作対象となる全UVコンポーネントのリスト
        """
        pos = uv.position()
        next_uvs = []
        # cmds.select(uv(), ['%s.e[%s]'%(uv.shape, x) for x in uv.edges])
        # updateView(1)
        for edge in uv.edges:
            uvids = edge.toUvs()
            target = None
            # 操作対象UVをエッジから検出する。=================================
            for uvid in uvids:
                if uvid == uv:
                    continue
                tgt = allUvs.get(uvid)
                if tgt is None:
                    continue
                if uv.face_ids & tgt.face_ids:
                    target = tgt
                    break
            if target is None or target.is_done:
                continue
            # =================================================================
            
            # エッジ情報から移動方向を決定する。===============================
            offset = None
            data = [target, None, None]
            if edge == yEdgeData[0]:
                offset = [0, yEdgeData[1]]
                data[2] = [yEdgeData[0], -yEdgeData[1]]
            elif edge == xEdgeData[0]:
                offset = [xEdgeData[1], 0]
                data[1] = [xEdgeData[0], -xEdgeData[1]]
            else:
                if edge.faces & xEdgeData[0].faces:
                    offset = [0, -yEdgeData[1]]
                    data[2] = [edge, yEdgeData[1]]
                elif edge.faces & yEdgeData[0].faces:
                    offset = [-xEdgeData[1], 0]
                    data[1] = [edge, xEdgeData[1]]
            if not offset:
                continue
            # =================================================================
            newpos = [x+y*0.01 for x, y in zip(pos, offset)]
            target.move(newpos[0], newpos[1])
            target.is_done = True
            next_uvs.append(data)

        for nuv in next_uvs:
            for i in range(1, 3):
                if nuv[i]:
                    continue
                src = nuv[3-i][0]
                edgedata = [xEdgeData, yEdgeData][i-1]
                for edge in nuv[0].edges:
                    if edge == src:
                        continue
                    if edge.faces & src.faces:
                        f = 1 if edge.faces & edgedata[0].faces else -1
                        nuv[i] = (edge, edgedata[1]*f)
            align(nuv[0], nuv[1], nuv[2], allUvs)

    def search_and_align(allUvs):
        r"""
            Args:
                allUvs (any):
        """
        corner = None
        for uv in allUvs:
            if not corner and uv.numEdges <= 2:
                corner = uv
        if not corner:
            return

        # コーナーの縦エッジを特定する。=======================================
        vx = OpenMaya.MVector((1, 0, 0))
        vy = OpenMaya.MVector((0, 1, 0))
        edgelist = {}
        for edge in corner.edges:
            comp = [x for x in edge.toUvs() if x.face_ids & corner.face_ids]
            vectors = [OpenMaya.MVector(allUvs[x].position()+[0]) for x in comp]
            s_vector = vectors.pop(comp.index(corner))
            v = (vectors[0]-s_vector).normal()
            xdot = v * vx
            ydot = v * vy
            edgelist.setdefault(abs(ydot), []).append(
                (edge, -1 if xdot < 0 else 1, -1 if ydot < 0 else 1)
            )
        # =====================================================================

        # UVシェルの最大値の大きさを求め、移動量の目安にする。=================
        poslist = [
            [uv.position()[x] for uv in allUvs] for x in range(2)
        ]
        pivot = corner.position()
        # =====================================================================

        y_edge = edgelist[max(edgelist.keys())][0]
        x_edge = edgelist[min(edgelist.keys())][0]
        del allUvs[corner]
        align(corner, x_edge[:2], (y_edge[0], y_edge[2]), allUvs)
        corner.is_done = True

        # 大きさを合わせる。===================================================
        moved_uvs = {x:y for x, y in allUvs.items() if x.is_done}
        moved_uvs[corner] = corner
        init_poslist = [
            [uv.position(True)[x] for uv in moved_uvs] for x in range(2)
        ]
        pos = [min(init_poslist[0]), min(init_poslist[1])]
        wh = [max(x)-min(x) for x in init_poslist]
        poslist = [
            [uv.position()[x] for uv in moved_uvs] for x in range(2)
        ]
        new_wh = [max(x)-min(x) for x in poslist]
        new_pos = [min(poslist[0]), min(poslist[1])]
        uv_targets = [x() for x in moved_uvs]
        cmds.polyEditUV(
            uv_targets, pu=new_pos[0], pv=new_pos[1],
            su=(wh[0]/new_wh[0]), sv=(wh[1]/new_wh[1])
        )
        cmds.polyEditUV(
            uv_targets, u=pos[0]-new_pos[0], v=pos[1]-new_pos[1]
        )
        # =====================================================================
        
        allUvs = {x:y for x, y in allUvs.items() if not x.is_done}
        search_and_align(allUvs)
        # cmds.select([x() for x in allUvs])

            
    if not faces:
        faces = cmds.filterExpand(sm=34)
    else:
        faces = cmds.filterExpand(faces, sm=35)
    if not faces:
        return

    bb = cmds.polyEvaluate(bc2=True)
    shortest = min([bb[x][1]-bb[x][0] for x in range(2)])

    # シェイプごとに切り分ける。
    shapes = {}
    idx_ptn = re.compile('\[(\d+)\]')
    for face in faces:
        shapes.setdefault(face.split('.')[0], []).append(face)
    for shape, faces in shapes.items():
        edgecounts = {}
        uvdata = []
        face_ids = [int(idx_ptn.search(x).group(1)) for x in faces]
        sel = OpenMaya.MSelectionList().add(shape)
        dagpath = sel.getDagPath(0)
        mfnm = OpenMaya.MFnMesh(dagpath)
        poly_iter = OpenMaya.MItMeshPolygon(dagpath)
        vtx_iter = OpenMaya.MItMeshVertex(dagpath)

        edgecounts = {}
        # UVとフェース、エッジの関係性を探索し保持する。=======================
        for face_id in face_ids:
            poly_iter.setIndex(face_id)
            edge_indexes = set(poly_iter.getEdges())
            # 四角ポリゴンではない場合は無視する。
            if len(edge_indexes) != 4:
                continue
            for i, vid in enumerate(poly_iter.getVertices()):
                vtx_iter.setIndex(vid)
                v_edges = set(vtx_iter.getConnectedEdges())
                uvid = poly_iter.getUVIndex(i)
                edges = list(v_edges & edge_indexes)
                # エッジの数をカウント。
                for edge in edges:
                    if not edge in edgecounts:
                        e_data = Edge(edge)
                        edgecounts[edge] = e_data
                    else:
                        e_data = edgecounts[edge]
                    e_data.counts += 1
                    e_data.faces.add(face_id)
                if not uvid in uvdata:
                    uvdata.append(
                        Uv(uvid, shape, edges, [face_id], poly_iter.getUV(i))
                    )
                else:
                    uv_obj = uvdata[uvdata.index(uvid)]
                    uv_obj.edges.extend(edges)
                    uv_obj.face_ids.add(face_id)
        # 選択面を形成するエッジオブジェクトのリスト。
        edges = [x for x in edgecounts.values() if x.counts>1]
        # =====================================================================

        # 端となるUVをどれか一点取得する。=====================================
        uvs = {}
        for uv in uvdata:
            uv.update(edges)
            # 四角ポリゴン以外を除外。
            if uv.numEdges > 4:
                continue
            uvs[uv] = uv

        search_and_align(uvs)


def switchUvForFlipbook(index, numU, numV, moveUvs=None):
    r"""
        polyMoveUVを、仮想タイルの任意のインデックスへと移動・スケールする。
        （フリップブック的な動作）

        Args:
            index (int):
            numU (int):
            numV (int):
            moveUvs (list):
    """
    if not moveUvs:
        moveUvs = node.selected(type='polyMoveUV')
    scale_uv = [1.0 / numU, 1.0 / numV]
    tu = index % numU + 1
    tv = index // numU + 1
    for uv in node.toObjects(moveUvs):
        uv('scaleU', -scale_uv[0])
        uv('scaleV', -scale_uv[1])
        uv('tu', scale_uv[0] * tu)
        uv('tv', scale_uv[1] * tv)
