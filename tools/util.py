#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    便利関数色々
    
    Dates:
        date:2017/01/22 0:00[Eske](eske3g@gmail.com)
        update:2020/12/22 19:41 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import node, mathlib
cmds = node.cmds

ComponentMask = [28, 30, 31, 32, 34]

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

    '''
    # 法線の平均値をとり、向きを求める。
    # 不確定のため現在はロック中。
    vector = None
    xlist, ylist, zlist = [], [], []
    if withDirection and len(pos) > 2:
        vec_a = mathlib.Vector(poslist[0])
        vec_b = mathlib.Vector(poslist[1])
        a = vec_a - vec_b
        for pos in poslist[2:]:
            vec_a = vec_b
            vec_b = mathlib.Vector(pos)
            b = vec_a - vec_b

            vec_c = a ** b
            vec_c.normalize()
            xlist.append(vec_c.x)
            ylist.append(vec_c.y)
            zlist.append(vec_c.z)

            a = b

        x_ = sum(xlist)
        y_ = sum(ylist)
        z_ = sum(zlist)
        d = mathlib.math.sqrt(sum([x*x for x in (x_, y_, z_)]))
        vector = mathlib.Vector(
            [x/d for x in (x_, y_, z_)]
        )
        vector.normalize()
    return center, vector
    '''
    
def getFaceNormal(faceId):
    r"""
        任意のフェースの法線を返す。
        
        Args:
            faceId (str):
            
        Returns:
            any:(OpenMaya.MVector):
    """
    print(faceId)
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
            
        Returns:
            any:None
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
            list: 向いている軸、軸がプラス方向かどうか、サブの軸
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