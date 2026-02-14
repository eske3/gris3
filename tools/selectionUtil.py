#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    選択に関する便利関数を収録するモジュール。
    
    Dates:
        date:2018/03/06 8:53[Eske](eske3g@gmail.com)
        update:2023/08/01 04:42 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2018 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import re
from maya.api import OpenMaya
from gris3 import node
from gris3.tools import nameUtility
SIDE_TABLE = nameUtility.SIDE_TABLE
cmds = node.cmds

def selected(*args, **keywords):
    r"""
        cmds.lsの互換コマンド。選択オブジェクトのリストを返す。
        使用できる引数もcmds.lsと同じ。
        
        Args:
            *args (any):
            **keywords (any):
            
        Returns:
            list:
    """
    keywords['sl'] = True
    return cmds.ls(*args, **keywords)


def selectNodes(nodelist, **keywds):
    r"""
        引数nodelistで指定された名前ノードを選択する。
        対象ノードが存在しない場合はそのノードはスキップする。
        戻り値として、実際に選択したノードのリストを返す。
        
        Args:
            nodelist (list):選択対象のノードリスト
            **keywds (any):
            
        Returns:
            list :実際に選択されたノードのリスト。
    """
    nodes = [x for x in nodelist if cmds.objExists(x)]
    if not nodes:
        cmds.select(cl=True)
        return []
    if not keywds:
        keywds = {'ne':True, 'r':True}
    cmds.select(nodes, **keywds)
    return nodes


def listNamespaces(nodelist=None):
    r"""
        Args:
            nodelist (list):検索対象のノードリスト
            
        Returns:
            list :ネームスペースのリスト
    """
    selected = node.selected(nodelist)
    if not selected:
        return []
    namespaces = [
        x.rsplit(':', 1)[0]+':' if ':' in x else '' for x in selected
    ]
    nslist = []
    for ns in namespaces:
        if ns in nslist:
            continue
        nslist.append(ns)
    return nslist


def listEndNodes(nodelist=None):
    r"""
        Args:
            nodelist (list):検索対象のノードリスト
            
        Returns:
            list : エンドノードをリストする
    """
    endnodes = []
    for trs in node.selected(nodelist, type='transform'):
        if trs.hasChild():
            if trs.children(type='transform'):
                continue
        endnodes.append(trs)
    return endnodes


def reverseSelectionOrder():
    r"""
        選択順序を反転する
    """
    selected = cmds.ls(sl=True)
    if not selected:
        return
    selected.reverse()
    cmds.select(selected, ne=True)


def selectOppositeSide(mode='select'):
    r"""
        特定の名前法則に従って反対側のノードを選択する
        
        Args:
            mode (str):selectかadd
    """
    selected = cmds.ls(sl=True)
    new_selections = []
    for s in selected:
        for ptn, key in SIDE_TABLE:
            if not ptn.search(s):
                continue
            name = ptn.sub(key, s)
            if not cmds.objExists(name):
                continue
            new_selections.append(name)

    if mode == 'add':
        selected.extend(new_selections)
        new_selections = selected
    cmds.select(new_selections, ne=True)


def selectEdgeLoopRing(mode='lpt'):
    r"""
        特定パターンのエッジループ（リング）選択を行う。
        
        Args:
            mode (str):リングの場合はrpt、ループの場合はlpt
            
        Returns:
            list:
    """
    index_ptn = re.compile('.e\[(\d+)\]')
    indexes = [
        int(index_ptn.search(x).group(1))
        for x in cmds.filterExpand(sm=32 or [])
    ]
    if not indexes:
        return []
    flags = {mode:[indexes[0], indexes[1]]}
    if len(indexes) > 1:
        return cmds.polySelect(**flags)
    return []


def listShapes(types, nodelist=None):
    r"""
        Args:
            types (list or str):リスト対象となるノードの種類
            nodelist (list):
    """
    if not isinstance(types, (list, tuple)):
        types = [types]
    nodelist = node.selected(nodelist, type=(['transform']+types))
    shapelist = []
    for n in nodelist:
        for typ in types:
            if n.isType(typ):
                shapelist.append(n())
                break
        else:
            if not hasattr(n, 'shapes'):
                continue
            shapes = n.shapes(ni=True, typ=types)
            for shape in shapes:
                shapelist.append(shape())
    return shapelist


ptn = re.compile('(.*\[)(\d+)\:(\d+)\]')
def expandCompList(idlist):
    r"""
        まとめられたコンポーネント表記をバラす
        
        Args:
            idlist (list):コンポーネントのリスト
            
        Returns:
            list:
    """
    r = []
    for id in idlist:
        mobj = ptn.search(id)
        if not mobj:
            r.append(id)
            continue
        nameformat = mobj.group(1)+'%s]'
        for i in range(int(mobj.group(2)), int(mobj.group(3))+1):
            r.append(nameformat % i)
    return r


def listFaceBorders(faces=None, select=True):
    r"""
        選択フェースのボーダーとなるエッジを選択する
        
        Args:
            faces (list):対象となるフェースのリスト
            select (bool):選択するかどうか
            
        Returns:
            list:ボーダーエッジのリスト
    """
    faces = faces or cmds.filterExpand(sm=34)
    if not faces:
        return
    result = cmds.polyListComponentConversion(faces, te=True, bo=True)
    if select:
        cmds.select(result, r=True)
    return result


def convertFaceInsideHardedges(facelist=None, select=True):
    r"""
        ハードエッジの境界線内のフェースを全て返す。
        
        Args:
            facelist (list):精査するフェースのリスト
            select (bool):取得結果を選択するかどうか
            
        Returns:
            list:
    """
    if facelist:
        facelist = cmds.filterExpand(facelist, sm=34, fp=True)
    else:
        facelist = cmds.filterExpand(sm=34, fp=True)
    if not facelist:
        return
    
    def search(face_idx, mfn_poly, mfn_edge, converted_faces, finished_edges):
        r"""
            与えられたフェース番号に隣接するエッジを調べ、ハードエッジでは
            なかった場合、さらに隣接するフェースまで探査を行う。
            結果、ハードエッジ内に収まるフェース番号のリストを
            引数converted_facesに格納する再帰関数。

            Args:
                face_idx (int):探索フェース番号
                mfn_poly (OpenMaya.MFnMeshPolygon):操作対象ポリゴン
                mfn_edge (OpenMaya.MFnMeshEdge):操作対象エッジ
                converted_faces (set):変換済みフェース番号のセット
                finished_edges (set):処理済みエッジ番号のセット
        """
        mfn_poly.setIndex(face_idx)
        edges = mfn_poly.getEdges()
        for e_index in edges:
            if e_index in finished_edges:
                continue
            finished_edges.add(e_index)
            mfn_edge.setIndex(e_index)
            if not mfn_edge.isSmooth:
                continue
            c_faces = mfn_edge.getConnectedFaces()
            for f_index in c_faces:
                if f_index in converted_faces:
                    continue
                converted_faces.add(f_index)
                search(
                    f_index, mfn_poly, mfn_edge, converted_faces, finished_edges
                )
    
    def search_inside_faces(face_data, edge_data):
        r"""
            シェイプ名をキー、フェース番号のセットを値として持つ辞書を受け取り、
            フェースがハードエッジに到達するまで選択拡張を続け、その結果の
            フェース名を返す。
            edge_dataは処理済みエッジ番号を保持するためのバッファ変数で、
            face_dataと同じシェイプ名のキーを持つ辞書。

            Args:
                face_data (dict):
                edge_data (dict):

            Returns:
                list(str):結果のフェースリスト
        """
        faces = []
        for mesh in face_data:
            finished_edges = edge_data[mesh]
            converted_faces = face_data[mesh]
            sel = OpenMaya.MSelectionList()
            sel.add(mesh)
            dpend = sel.getDependNode(0)
            # fmesh = OpenMaya.MFnMesh(dpend)
            mipoly = OpenMaya.MItMeshPolygon(dpend)
            miedge = OpenMaya.MItMeshEdge(dpend)
            for index in [x for x in face_data[mesh]]:
                search(index, mipoly, miedge, converted_faces, finished_edges)
            
            best_name = cmds.ls(mesh)[0]
            for f_index in converted_faces:
                faces.append('{}.f[{}]'.format(best_name, f_index))
        return faces

    converted_faces = {}
    face_ptn = re.compile('(^[a-zA-Z\d_|]+)\.f\[(\d+)\]$')
    for face in facelist:
        r = face_ptn.search(face)
        converted_faces.setdefault(r.group(1), set()).add(int(r.group(2)))
    finished_edges = {x: set() for x in converted_faces}
    import sys
    limit = sys.getrecursionlimit()
    sys.setrecursionlimit(10000000)
    try:
        faces = search_inside_faces(converted_faces, finished_edges)
    except Exception as e:
        raise e
    finally:
        sys.setrecursionlimit(limit)
    if select and faces:
        cmds.select(faces, r=True, ne=True)
    return faces


def selectCreasedEdges(edges=None, isSelecting=True):
    r"""
        Args:
            edges (list):検索対象のエッジのリスト
            isSelecting (bool):結果のリストを選択するかどうか
            
        Returns:
            list:検索したクリースエッジのリスト
    """
    if not edges:
        edges = cmds.filterExpand(sm=32)
        if not edges:
            edges = []
            selected = node.selected(type=['transform', 'mesh'])
            for sel in selected:
                if sel.isType('transform'):
                    sel = sel.shapes(typ='mesh')
                else:
                    sel = [sel]
                edges.extend(
                    cmds.ls([x+'.e[*]' for x in sel if not x('io')], fl=True)
                )
    else:
        edges = cmds.filterExpand(edges, sm=32)
    if not edges:
        return []
    edges = list(set(edges))
    creased = [x for x in edges if cmds.polyCrease(x, q=True, v=True)[0] > 0.0]
    if creased and isSelecting:
        cmds.select(creased, r=True)
    return creased


def selectHardEdges(mesh, isSelecting=True, threshold=0.995):
    r"""
        引数meshのエッジのウチ法線的にハードエッジ扱いのものを選択する。
        
        Args:
            mesh (str):操作対象となるメッシュノード
            isSelecting (bool):選択するかどうか
            threshold (float):選択判定のしきい値(内積)
            
        Returns:
            list:検索したハードエッジのリスト
    """
    def listVectorDots(normalList):
        r"""
            与えられた法線のリストに対し、n番目とn+1番目の法線の内積結果を
            格納したリストを返す。
            
            Args:
                normalList (list):
                
            Returns:
                list:
        """
        dotlist = []
        nl = len(normalList)
        for i in range(nl):
            for j in range(i+1, nl):
                dotlist.append(normalList[i]*normalList[j])
        return dotlist

    sel = OpenMaya.MSelectionList()
    sel.add(mesh)
    depend = sel.getDependNode(0)
    mfnm = OpenMaya.MFnMesh(depend)
    miedge = OpenMaya.MItMeshEdge(depend)
    hardedges = []
    while(not miedge.isDone()):
        index = miedge.index()
        vts_idx = mfnm.getEdgeVertices(index)
        face_idx = list(miedge.getConnectedFaces())
        if len(face_idx) < 2:
            miedge.next()
            continue
        count = 0
        for vid in vts_idx:
            normals = []
            for fid in face_idx:
                normals.append(mfnm.getFaceVertexNormal(fid, vid).normal())
            dotlist = listVectorDots(normals)
            try:
                min_dot = min(dotlist)
            except Exception as e:
                print('Invalid edge : %s' % ('%s.e[%s]'%(mesh, index)))
                raise e
            if min(dotlist) < threshold:
                count += 1
        miedge.next()
        
        if count == len(vts_idx):
            hardedges.append('%s.e[%s]'%(mesh, index))
    if isSelecting and hardedges:
        cmds.select(hardedges, r=True, ne=True)
    return hardedges


def selectKeyableHir(nodelist=None, isSelecting=True):
    r"""
        任意ノードの子改装を調べ、TRSがいずれかKeyableになっているノードを
        リストし、選択する。
        
        Args:
            nodelist (list):
            isSelecting (bool):選択するかどうか
            
        Returns:
            list:結果のノードのリスト
    """
    def is_unlocked_trs(obj):
        r"""
            TRSがいずれかKeyableになっているかどうかを調べる
            
            Args:
                obj (node.Transform):
                
            Returns:
                bool:
        """
        for at in 'trs':
            for ax in 'xyz':
                try:
                    if obj.attr(at+ax).isKeyable():
                        return True
                except:
                    return False
        return False

    new_selection = []
    last_selection = []
    for n in node.selected(nodelist, type='transform'):
        children = n.allChildren()
        children.append(n)
        children = [x for x in children if is_unlocked_trs(x)]
        if not children:
            continue
        new_selection.extend(children)
        if is_unlocked_trs(n):
            last_selection.append(n)
    if isSelecting and new_selection:
        cmds.select(new_selection, r=True)
        cmds.select(last_selection, add=True)
    return new_selection


def selectEndNodes(nodelist=None, **args):
    endnodes = listEndNodes(nodelist)
    if not endnodes:
        return
    cmds.select(endnodes, **args)


def selectHierarchyWithEndNodes(withoutEndNode, nodelist=None):
    cmds.select(node.selected(nodelist), hierarchy=True)
    endnodes = listEndNodes()
    if not endnodes:
        return
    if withoutEndNode:
        cmds.select(endnodes, d=True)
    else:
        cmds.select(endnodes, r=True, ne=True)


class ConditionalSelection(object):
    ShapeKey = '(Transform)'

    def __init__(self):
        self.__node_types = []

    def setNodeTypes(self, nodetypes):
        self.__node_types = list(nodetypes)

    def nodeTypes(self):
        return self.__node_types

    def listFilteredByNodeType(
        self, nodelist, includeShapes=False, includeTransform=False
    ):
        node_types = []
        shape_types = []
        for nt in self.nodeTypes():
            if nt.endswith(self.ShapeKey):
                key = nt.replace(self.ShapeKey, '')
                shape_types.append(key)
                if includeTransform:
                    node_types.append(key)
            else:
                node_types.append(nt)

        targets = []
        for n in nodelist:
            nt = n.type()
            added = False
            if nt in shape_types:
                targets.append(n.parent())
                added = True
            if nt in node_types:
                targets.append(n)
                added = True
            if added or not includeShapes or not n.isSubType('transform'):
                continue
            for shape in n.shapes(ni=True):
                if shape.type() in shape_types:
                    targets.append(n)
                    break
        return targets

    def select(self, nodelist=None, **args):
        targets = self.listFilteredByNodeType(node.selected(nodelist), True)
        cmds.select(targets, **args)
    
    def selectHierarchy(self, nodelist=None, **args):
        cmds.select(node.selected(nodelist), hierarchy=True)
        targets = self.listFilteredByNodeType(
            node.selected(), includeTransform='d' in args
        )
        if not targets:
            return
        cmds.select(targets, **args)

        
        

    
