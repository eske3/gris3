#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    便利関数色々
    
    Dates:
        date:2017/01/22 0:00[Eske](eske3g@gmail.com)
        update:2025/05/29 11:59 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from maya.api import OpenMaya
from gris3 import node, mathlib
cmds = node.cmds

ComponentMask = [28, 30, 31, 32, 34]
class ClosestVertexFinder(object):
    def __init__(self, *polygons):
        r"""
            引数polygonsには操作対象となるポリゴンの名前を2つ以上渡す。
            最後に指定したポリゴンの各頂点から最も近い頂点を、それ以外の
            ポリゴンから探してくる。

            Args:
                *polygons (str): 操作対象となるポリゴン名のリスト
        """
        if len(polygons) < 2:
            raise ValueError(
                'The argument "polygons" needs to be specified '
                'more than 2 polygonal objects.'
            )
        self.__sourcelist = list(polygons[:-1])
        self.__target = polygons[-1]
        self.__points_list = {}
        self.__cell_count = 10

    def setup(self):
        self.__points_list = {}
        self.__bb = []
        sel = OpenMaya.MSelectionList()
        for i, p in enumerate(self.__sourcelist + [self.__target]):
            sel.add(p)
            dagpath = sel.getDagPath(i)
            mesh = OpenMaya.MFnMesh(dagpath)
            self.__points_list[p] = mesh.getPoints(OpenMaya.MSpace.kWorld)
    
    def getPoints(self, name):
        self.__points_list.get(name, [])

    def setCellCount(self, count):
        self.__cell_count = count

    def cellCount(self):
        return self.__cell_count

    def buildSpatialGrid(self, name):
        from collections import defaultdict
        grid = defaultdict(list)
        points = self.getPoints(name)
        
        # バウンディングボックスを取得。
        xlist, ylist, zlist = set(), set(), set()
        for pt in points:
            xlist.add(pt.x)
            ylist.add(pt.y)
            zlist.add(pt.z)
        bb = [f(x) for x in [xlist, ylist, zlist] for f in [min, max]]
        cell_size = (
            max([bb[1] - bb[0], bb[3] - bb[2], bb[5] - bb[4]])
            / self.cellCount()
        )

        for idx, pt in enumerate(points):
            cell = (
                int(pt.x // cell_size),
                int(pt.y // cell_size),
                int(pt.z // cell_size)
            )
            grid[cell].append((idx, pt))
        return grid, cell_size

    @staticmethod
    def getNeighboringCells(cell):
        x, y, z = cell
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                for dz in [-1, 0, 1]:
                    yield (x + dx, y + dy, z + dz)

    def findClosestPoint(self, pt, grid, cellSize):
        def sq_dist(a, b):
            delta = a - b
            return delta.x**2 + delta.y**2 + delta.z**2

        min_dist_sq = float('inf')
        closest_idx = None
        cell = (
            int(pt.x // cell_size),
            int(pt.y // cell_size),
            int(pt.z // cell_size)
        )
        for neighbor_cell in self.getNeighboringCells(cell):
            for idx, pt_b in grid.get(neighbor_cell, []):
                dist_sq = sq_dist(pt, pt_b)
                if dist_sq < min_dist_sq:
                    min_dist_sq = dist_sq
                    closest_idx = idx
        return closest_idx, min_dist_sq

    def listClosestVertexPairs(self):
        self.setup()
        pairs = []
        grid_data = {x: self.buildSpatialGrid(x) for x in self.__sourcelist}
        for i, pt_a in enumerate(self.getPoints(self.__target)):
            closest_data_list =  []
            for src, g_c in grid_data:
                c_id_dist = self.findClosestPoint(pt_a, g_c[0], g_c[1])
                closest_id_list.append(c_id_dist)
            pairs.append(closest_data_list)

        results = []
        for a_id, c_data in enumerate(pairs):
            print(a_id)
            print(c_data)
            print()
        
            
def positionCenter(positions):
    r"""
        与えられた座標リストの中心点を求める
        
        Args:
            positions (list):x,y,zの座標をtupleで持つリスト
            
        Returns:
            list, float:中心座標と座標リストの最大サイズ
    """
    xlist, ylist, zlist = [], [], []
    for pos in positions:
        xlist.append(pos[0])
        ylist.append(pos[1])
        zlist.append(pos[2])
    center = [(min(x)+max(x))*0.5 for x in (xlist, ylist, zlist)]
    size = [max(x)-min(x) for x in (xlist, ylist, zlist)]
    return center, size


def getComponentCenter(components=None):
    r"""
        複数コンポーネントの中心座標を返す。
        引き数componentsの指定がない場合、選択されたコンポーネントから
        座標を取得する。
        
        Args:
            components (list):コンポネントのリスト。
            
        Returns:
            list:
    """
    if not components:
        components = cmds.filterExpand(sm=ComponentMask)
    points = cmds.filterExpand(components, sm=[28, 30, 31]) or []

    converted_points = cmds.ls(
        cmds.polyListComponentConversion(
            cmds.filterExpand(components, sm=[32, 34]) or [], tv=True
        ),
        fl=True
    )
    points.extend(converted_points)
    positions = [cmds.pointPosition(x, w=True) for x in points]
    return positionCenter(positions)

    
def getFaceNormal(faceId):
    r"""
        任意のフェースの法線を返す。
        
        Args:
            faceId (str):
            
        Returns:
            any:(OpenMaya.MVector):
    """
    normal_data = cmds.polyInfo(faceId, fn=True)[0]
    n = [float(x) for x in normal_data .rsplit(':', 1)[-1].split()]
    shape = cmds.listRelatives(faceId, p=True, pa=True)
    matrix = node.MMatrix(cmds.getAttr(shape[0]+'.wm'))
    normal_mtx = node.MMatrix(
        [
            n[0], n[1], n[2], 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1
        ]
    )
    normal = node.MVector(
        list(normal_mtx * matrix)[:3]
    ).normalize()
    return normal


def mirror(sel=None, axis='X'):
    r"""
        任意のオブジェクトをミラーリング（Behavior）する。
        
        Args:
            sel (list):対象ノードのリスト
            axis (str):X、YまたはZ
    """
    sel = node.selected(sel)
    num = len(sel)
    if num % 2 == 1:
        raise TypeError('Select src object, and then dst object.')

    axis = getattr(mathlib.mirrorMatrix, axis)
    for i in range(0, num, 2):
        src = sel[i]
        dst = sel[i+1]
        if not dst:
            print('[Warning]Mirrored objects was not detected : {}'.format(src))
            continue
        dst.setMatrix(mathlib.mirrorMatrix(src.matrix(), axis))


class Transform(object):
    r"""
        Transformの位置情報を保持、復元するための機能を提供する
    """
    def __new__(cls):
        r"""
            シングルトン化処理
            
            Returns:
                Transform:
        """
        if hasattr(cls, '__singletoninstance__'):
            return cls.__singletoninstance__
        obj = super(Transform, cls).__new__(cls)
        obj.__data = []
        cls.__singletoninstance__ = obj
        return obj

    def savePositions(self, nodelist=None):
        r"""
            nodelistのノードの位置情報を保持する。
            
            Args:
                nodelist (list):
                
            Returns:
                any:
        """
        nodelist = node.selected(nodelist)
        self.__data = [
            (x.matrix(), x.rotatePivot(), x.scalePivot()) for x in nodelist
            if hasattr(x, 'matrix')
        ]

    def restorePositions(self, nodelist=None, flags=0b111111):
        r"""
            保持している位置情報をnodelistに対して復元する。
            引数flagsは2進数で、左から順に
            translate,rotate,scale,shear,rotatePivot,scalePivot
            を復元するかどうかを指定する。
            
            Args:
                nodelist (list):復元対象となるノードのリスト
                flags (bin):
                
            Returns:
                any:None
        """
        if not self.__data:
            return
        nodelist = node.selected(nodelist)

        numdata = len(self.__data)
        if numdata== 1:
            indexlist = [0 for x in nodelist]
        else:
            indexlist = range(numdata)

        rs_flag = flags >> 2 & 0b0111
        for n, i in zip(nodelist, indexlist):
            if not hasattr(n, 'setMatrix'):
                continue
            # Translate, rotate, scale, shearの適応を行う。
            if flags & 0b100000:
                cmds.move(*self.__data[i][1], rpr=True)
            if rs_flag:
                n.setMatrix(self.__data[i][0], flags=rs_flag)

            # rotateピボットポイントの反映
            if flags & 0b000010:
                n.setRotatePivot(self.__data[i][1])
            # scaleピボットポイントの反映
            if flags & 0b000001:
                n.setScalePivot(self.__data[i][2])


def listSingleChain(topNode):
    r"""
        任意のノード下にある、最初の子の階層チェーンを返すメソッド。
        
        Args:
            topNode (str):トップノード名。
            
        Returns:
            list:
    """
    parent = node.asObject(topNode)
    result = [parent]
    while(True):
        children = parent.children()
        if not children:
            return result
        result.append(children[0])
        parent = children[0]


def detectAimAxis(mainNode, comparedNode):
    r"""
        mainNodeのX,Y,Zのうち、どの軸がcomparedNodeの方向を向いているかを
        判定し返す。
        戻り値はリストで、中身は
            向いている軸(X=0, Y=1, Z=2)
            軸がプラス方向かどうかの補正値(1 or -1)
            サブの軸(X=0, Y=1, Z=2)
        が格納されている。
        
        Args:
            mainNode (node.Transform):
            comparedNode (node.Transform):
            
        Returns:
            list:向いている軸、軸がプラス方向かどうか、サブの軸
    """
    mtx = mainNode.matrix()
    vec = (
        node.MVector(comparedNode.position()) - node.MVector(mtx[12:15])
    ).normal()
    biggest = 0.0
    calclist = []
    for axis in (mtx[0:3], mtx[4:7], mtx[8:11]):
        axis = node.MVector(axis).normal()
        value = axis * vec
        if abs(biggest) <= abs(value):
            biggest = value
        calclist.append(value)
    index = calclist.index(biggest)
    sub = list(range(3))
    sub.remove(index)
    return (index, (1 if biggest>=0 else -1), sub[0])


class CameraInfo(object):
    r"""
        カメラの情報を保持、提供するクラス。
        インスタンス時にMaya上でアクティブになっているカメラとビュー情報を
        保持し、任意のタイミングで取得する事ができる。
    """
    def __init__(self):
        from gris3.uilib import mayaUIlib
        self.__camera, self.__view = mayaUIlib.getActiveCamera(True)

    def isValid(self):
        r"""
            インスタンス化した際に、アクティブなカメラを取得できたか
            どうかを返す。
            
            Returns:
                bool:
        """        
        return self.__camera is not None

    def cameraView(self):
        return (self.__camera, self.__view)

    def getDrawnVector(self, start, end, world=True, isNormalize=True):
        r"""
            与えられた開始座標と終了座標のベクトルを、シーン中のベクトルに
            変換して返す。
            
            Args:
                start (QtCore.QPoint):開始座標
                end (QtCore.QPoint):終了座標
                world (bool):ワールド空間でのベクトルに変換するかどうか
                isNormalize (bool):結果を正規化するかどうか
                
            Returns:
                list:3Dベクトルを表すリスト
        """
        from maya.api.OpenMaya import MMatrix, MVector
        camera, view = self.cameraView()
        
        world_matrix = cmds.getAttr(camera+'.worldMatrix')
        world_matrix[12:15] = [0, 0, 0]
        cam_invmtx = MMatrix(cmds.getAttr(camera+'.worldInverseMatrix'))

        v = end - start
        v = MVector((v.x(), -v.y(), 0))
        if isNormalize:
            v = v.normalize()
        v = list(v)
        if not world:
            return v
    
        pt_matrix = MMatrix(
            (1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, v[0], v[1], v[2], 1)
        )
        pt_local =list(pt_matrix * MMatrix(world_matrix))[12:15]
        if isNormalize:
            pt_local = list(MVector(pt_local).normalize())
        return pt_local


def listNamespaces():
    r"""
        シーン中のリファレンスファイルとネームスペースのリストを返す。
        戻り値はOrderedDictのため、読み込み順序も保証されたものを返す。
        
        Returns:
            OrderedDict:ネームスペースをキーとし対応したファイルパス
    """
    from collections import OrderedDict
    results = OrderedDict()
    for file in cmds.file(q=True, r=True):
        results[cmds.referenceQuery(file, ns=True)] = file
    return results


def analyzeHierarchy(nodelist=None):
    r"""
        任意のノードの階層構造を解析し、枝分かれしている箇所ごとに分解した
        シングルチェーンのリストを返す。
        
        Args:
            nodelist (list):
            
        Returns:
            list:
    """
    global_list = {}
    def add_newlist():
        newlist = []
        global_list[len(global_list)] = newlist
        return newlist

    def get_hierarchy(trs, hirlist):
        r"""
            Args:
                trs (node.Transform):
                hirlist (list):
        """
        hirlist.append(trs)
        for i, children in enumerate(trs.children()):
            if i == 0:
                get_hierarchy(children, hirlist)
            else:
                get_hierarchy(children, add_newlist())

    nodelist = node.selected(nodelist)
    for n in nodelist:
        get_hierarchy(n, add_newlist())
    return [global_list[x] for x in sorted(global_list.keys())]


