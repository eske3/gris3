#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    プリセットに登録されているカーブ形状を作成するための機能を提供する
    
    Dates:
        date:2017/02/19 9:25[Eske](eske3g@gmail.com)
        update:2024/11/12 12:31 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os

from maya import OpenMaya, mel
from ... import node, colorUtil
cmds = node.cmds

# パラメータ。=================================================================
Maya_Version = float(cmds.about(v=True).split()[0])
DefaultLineWidth = 3.0
CurveWidthAttr = 'grsCurveWidth'
CurveColorAttr = 'grsCurveWireColor'
CurveTypeList = None
def updateCurveTypeList():
    r"""
        melsディレクトリに保存されているファイルの一覧をCurveTypeListに
        反映させる
    """
    global CurveTypeList
    rootdir = os.path.join(os.path.dirname(__file__), 'mels')
    CurveTypeList = {
        x[:-4] : os.path.join(rootdir, x)
        for x in os.listdir(rootdir) if x.endswith('.mel')
    }
updateCurveTypeList()

__CURVE_SHAPE_BUFFER__ = {}
# =============================================================================

if Maya_Version < 2016:
    def setColorIndex(shape, colorIndex):
        r"""
            Maya2016未満でのカラー設定用関数。
            
            Args:
                shape (str):カーブのシェイプ名
                colorIndex (int):インデックスカラーの番号
        """
        cmds.setAttr('%s.overrideEnabled' % shape, 1)
        cmds.setAttr('%s.overrideColor' % shape, colorIndex)
else:
    def setColorIndex(shape, colorIndex):
        r"""
            Maya2016以降でのカラー設定用関数。
            
            Args:
                shape (str):カーブのシェイプ名
                colorIndex (list):r,g,bのリスト
        """
        cmds.setAttr('%s.useObjectColor' % shape, 2)
        if isinstance(colorIndex, (list, tuple)):
            cmds.setAttr('%s.wireColorRGB' % shape, *colorIndex)
        else:
            cmds.setAttr(
                '%s.wireColorRGB' % shape, *colorUtil.NewColorIndex[colorIndex]
            )


def addCurveWidthCtrlAttr(*curves):
    r"""
        任意のnurbsCurveにラインの太さを制御するカスタムアトリビュートを追加し、
        lineWidthにコネクトする。
        （カーブの太さを設定したファイルをリファレンスすると、カーブの太さが
        -1に設定されてしまうバグを防ぐためのもの）
        すでにlineWidthに何かが接続されている場合は無視する。
        
        戻り値はカスタムアトリービュートの接続処理を行わなかったnurbsCurveの
        リスト。

        Args:
            *curves (str):操作対象カーブのリスト
        
        Returns:
            list:
    """
    not_processed = []
    for curve in curves:
        for crv in node.getShapes(curve, 'nurbsCurve'):
            if crv.attr('lineWidth').source():
                not_processed.append(crv)
                continue
            if not crv.hasAttr(CurveWidthAttr):
                crv.addFloatAttr(
                    CurveWidthAttr, min=None, max=None, default=-1, k=False
                )
            crv(CurveWidthAttr, crv('lineWidth'))
            crv.attr(CurveWidthAttr) >> crv/'lineWidth'
    return not_processed


def addWireColorCtrlAttr(*curves):
    not_processed = []
    for curve in curves:
        for crv in node.getShapes(curve, 'nurbsCurve'):
            if not crv.hasAttr(CurveColorAttr):
                cmds.addAttr(
                    crv, ln=CurveColorAttr, at='float3', usedAsColor=True
                )
                for c in 'RGB':
                    cmds.addAttr(
                        crv, ln=CurveColorAttr+c, at='float',
                        parent=CurveColorAttr
                    )
            else:
                attr = crv.attr('wireColorRGB')
                for at in list(~attr) + [attr]:
                    if at.source():
                        attr = None
                        break
                if not attr:
                    continue
            crv(CurveColorAttr, crv('wireColorRGB')[0])
            crv('useObjectColor', 2)
            ~crv.attr(CurveColorAttr) >> ~crv.attr('wireColorRGB')


def createCurvePrimitive(curveType, parentNode=None, **keywords):
    r"""
        引き数parentNodeの下に任意の形状のカーブを作成する。
        **keywordsはparentNodeがNoneの場合に渡す、createNode用の引き数。
        
        Args:
            curveType (str):作成するカーブのタイプ
            parentNode (str):カーブを作成する親ノードの名前
            **keywords (any):
            
        Returns:
            Primitive:
    """
    if not curveType in CurveTypeList:
        raise ValueError(
            'The sepcified type is invalid : {}'.format(curveType)
        )
    script_path = CurveTypeList[curveType]
    if not parentNode:
        flag = ''
        for key in keywords:
            flag += ' -%s "%s"' % (key, keywords[key])
        script_lines = [
            '{\nstring $trs = `createNode "transform" %s`;\n' % flag
        ]
    else:
        script_lines = ['{\nstring $trs = "%s";\n' % parentNode]
    creation_cmds = __CURVE_SHAPE_BUFFER__.get(curveType)
    if not creation_cmds:
        with open(script_path, 'r') as f:
            creation_cmds = f.readlines()
        __CURVE_SHAPE_BUFFER__[curveType] = creation_cmds
    script_lines.extend(creation_cmds)
    script_lines.append('select -r $trs;\n}')
    result = mel.eval(''.join(script_lines))
    node = cmds.ls(sl=True)[0]
    return Primitive(node)


def mirrorCurve(curveList=None, axis='x', world=True):
    r"""
        curveListのカーブをミラーリングする。
        
        Args:
            curveList (list):
            axis (str):ミラーリングする軸
            world (bool):ワールド空間でのミラーかどうか
    """
    axislist = {'x':0, 'y':5, 'z':10}
    def getCurveShape(node):
        r"""
            与えられたノードのカーブシェイプを返す。
            
            Args:
                node (node.Transform):
                
            Returns:
                node.NurbsCurve:
        """
        if node.isType('nurbsCurve'):
            return [node]
        elif cmds.ls(node(), type='transform'):
            curves = node.shapes(typ='nurbsCurve')
            if curves:
                return curves

        raise RuntimeError(
            'The node "%s" must be a "nurbsCurve".' % node
        )

    def appplyMirrorCurve(src_curve, dst_curve, axis, world):
        r"""
            ミラーリングを実行する。
            
            Args:
                src_curve (node.Shape):
                dst_curve (node.Shape):
                axis (str):ミラーリング軸
                world (bool):ワールド空間でのミラーかどうか
        """
        temp_trsgeo = node.createNode('transformGeometry')

        src_curve.attr('local')  >> temp_trsgeo/'inputGeometry'

        # 空間をミラーリングしたものに修正。===================================
        matrix = node.identityMatrix()
        matrix[axislist[axis]] = -1

        mltmtx = node.createUtil('multMatrix')
        i = 0
        if world:
            src_curve.attr('worldMatrix') >> mltmtx/'matrixIn[{}]'.format(i)
            (
                dst_curve.attr('worldInverseMatrix')
                >> mltmtx/'matrixIn[{}]'.format(i+2)
            )
            i += 1
        mltmtx('matrixIn[{}]'.format(i), matrix, type='matrix')
        mltmtx.attr('matrixSum') >> temp_trsgeo/'transform'
        # =====================================================================

        temp_trsgeo.attr('outputGeometry') >> dst_curve/'create'
        cmds.delete(dst_curve, ch=True)

    pre_selection = cmds.ls(sl=True)

    curveList = node.selected(curveList)
    if len(curveList) % 2 == 1:
        raise ValueError(
            'A curves you want to mirror must be a list that incluses'
            'a couple of curves.'
        )
    for i in range(0, len(curveList), 2):
        src_curves = getCurveShape(curveList[i])
        dst_curves = getCurveShape(curveList[i+1])
        if len(src_curves) != len(dst_curves):
            raise RuntimeError(
                'A number of the source curves is not match as the '
                "destination's curves."
            )
        for src, dst in zip(src_curves, dst_curves):
            appplyMirrorCurve(src, dst, axis, world)

    if pre_selection:
        cmds.select(pre_selection, ne=True, r=True)


def mirrorCurveByName(curveList=None):
    r"""
        名前から判断してミラーリングを行う。
        
        Args:
            curveList (list):
    """
    curveList = node.selected(curveList)
    if not curveList:
        return
    from gris3 import system
    name_rule = system.GlobalSys().nameRule()
    pl = name_rule.positionList()
    coupled = {pl[2]:[], pl[4]:[], pl[6]:[]}
    for curve in curveList:
        n = name_rule(curve)
        m = n.mirroredName(withPosition=True)
        if not m or not cmds.objExists(m[0]):
            continue
        coupled[m[1]].extend((curve, m[0]))
    for p, a in zip((pl[2], pl[4], pl[6]), ('x', 'y', 'z')):
        if not coupled[p]:
            continue
        mirrorCurve(coupled[p], axis=a)


class PrimitiveCreator(object):
    r"""
        任意の形状、色、サイズのカーブを生成するための機能を提供するクラス。
    """
    def __init__(self):
        self.__curveType = 'box'
        self.__translation = None
        self.__rotation = None
        self.__sizes = None
        self.__colorIndex = None
        self.__affect_from_nodesize = False
        self.__size_ratio = 1.0
        self.__line_width = DefaultLineWidth

    def setCurveType(self, curveType='box'):
        r"""
            カーブのタイプを指定する。
            
            Args:
                curveType (str):
        """
        self.__curveType = curveType
    
    def curveType(self):
        r"""
            セットされているカーブのタイプを返す。
            
            Returns:
                str:
        """
        return self.__curveType

    def setTranslation(self, values=None):
        r"""
            カーブシェイプの移動量を指定する。
            
            Args:
                values (list):
        """
        self.__translation = values

    def translation(self):
        r"""
            指定されているカーブの移動量を返す。
            
            Returns:
                list:
        """
        return self.__translation

    def setRotation(self, values=None):
        r"""
            カーブシェイプの回転量を指定する。
            
            Args:
                values (list):
        """
        self.__rotation = values

    def rotation(self):
        r"""
            指定されているカーブシェイプの回転量を返す。
            
            Returns:
                list:
        """
        return self.__rotation

    def setAffectFromNodeSize(self, state):
        r"""
            ノードのradius値がカーブの大きさに影響を与えるかどうかを設定する。
            
            Args:
                state (bool):
        """
        self.__affect_from_nodesize = bool(state)

    def affectFromNodeSize(self):
        r"""
            ノードのradius値がカーブの大きさに影響を与えるかどうか
            
            Returns:
                bool:
        """
        return self.__affect_from_nodesize

    def __setSizeRatio(self, ratio=1.0):
        r"""
            作成されるカーブの大きさにバイアスをかける。
            内部使用専用。
            
            Args:
                ratio (float):
        """
        self.__size_ratio = ratio

    def setSizes(self, values=None):
        r"""
            作成されるカーブの大きさをX,Y,Zで指定する。
            
            Args:
                values (list):
        """
        self.__sizes = values

    def setSize(self, value):
        r"""
            作成されるカーブの大きさを指定する。
            
            Args:
                value (float):
        """
        self.setSizes([value, value, value])

    def sizes(self):
        r"""
            作成されるカーブの大きさをX,Y,Zで返す。
            
            Returns:
                list:
        """
        return (
            [x*self.__size_ratio for x in self.__sizes]
            if self.__sizes else None
        )

    def resetTransform(self):
        r"""
            移動・回転・スケールをリセットする。
        """
        self.setTranslation()
        self.setRotation()
        self.setSizes()

    def setColorIndex(self, index=None):
        r"""
            カーブの色を指定する。
            
            Args:
                index (list):r, g, bでの色指定
        """
        self.__colorIndex = index

    def colorIndex(self):
        r"""
            指定されているカーブの色を返す。
            
            Returns:
                list:
        """
        return self.__colorIndex
    
    def setLineWidth(self, width):
        r"""
            ラインの幅を設定する。
            
            Args:
                width (float):
        """
        self.__line_width = width
    
    def lineWidth(self):
        r"""
            設定されたラインの幅を返す。
            
            Returns:
                float:
        """
        return self.__line_width

    def create(self, curveType=None, parentNode=None, **keywords):
        r"""
            設定されている条件に従ってカーブを作成する。
            各種引き数を指定すると、指定されている条件を上書きして作成する。
            また引き数keywordsはparentNodeがNoneの場合に渡す、
            createNodeへの引き数。
            
            Args:
                curveType (str):
                parentNode (str):親ノード
                **keywords (any):
                
            Returns:
                Primitive:
        """
        if (
            self.affectFromNodeSize() and
            cmds.attributeQuery('radius', ex=True, n=parentNode)
        ):
            self.__setSizeRatio(cmds.getAttr(parentNode+'.radius'))
        else:
            self.__setSizeRatio()
            
        if not curveType:
            curveType = self.curveType()

        shape = createCurvePrimitive(curveType, parentNode, **keywords)
        for s in shape.shapes():
            cmds.setAttr('%s.ihi' % s, 0)

        for attr, function in zip(
                [shape.setRotate, shape.setScale, shape.setTranslate],
                [self.rotation, self.sizes, self.translation]
            ):
            values = function()
            if not values:
                continue
            attr(values[0], values[1], values[2])

        if self.colorIndex():
            shape.setColorIndex(self.colorIndex())
        addCurveWidthCtrlAttr(*shape.shapes())
        shape.setLineWidth(self.lineWidth())

        self.__setSizeRatio()
        return shape

    def replace(self, targets=None, curveType=None):
        r"""
            targetsのカーブの形状をcurveTypeに置き換える
            
            Args:
                targets (list):置き換えられるカーブノードのリスト
                curveType (str):置き換えるカーブのタイプ
        """
        pre_selection = cmds.ls(sl=True)
        targets = node.selected(targets)
        temp_curve = self.create(curveType)
        out_plug = temp_curve.name() + '.local'
        done = []
        for target in targets:
            if not target.isType('nurbsCurve'):
                if not node.ls(target, type='transform'):
                    continue
                curves = target.children(type='nurbsCurve')
            else:
                curves = [target]
            for curve in curves:
                cmds.connectAttr(out_plug, curve+'.create')
            done.extend(curves)
        cmds.delete(done, ch=True)
        cmds.delete(temp_curve.name())
        if pre_selection:
            cmds.select(pre_selection, ne=True, r=True)

    def copyParam(self, target):
        r"""
            PrimitiveCreatorオブジェクトにこのオブジェクトのパラメータを
            コピーする。
            
            Args:
                target (PrimitiveCreator):
        """
        for attr in (
            'curveType', 'translation', 'rotation', 'sizes',
            'affectFromNodeSize', 'colorIndex'
        ):
            setter = 'set{}{}'.format(attr[0].upper(), attr[1:])
            setter = getattr(target, setter)
            setter(getattr(self, attr)())


class Primitive(object):
    r"""
        カーブシェイプを修正するための機能を持つクラス。
    """
    def __init__(self, transform):
        r"""
            Args:
                transform (str):カーブシェイプを持つtransformノード名
        """
        self.__transform = transform

    def name(self):
        r"""
            初期化時に登録されたtransformノード名を返す。
            
            Returns:
                str:
        """
        return self.__transform

    def shapes(self):
        r"""
            カーブシェイプを返す。
            
            Returns:
                str:
        """
        return cmds.listRelatives(self.name(), shapes=True, type='nurbsCurve')

    def shapeCVs(self):
        r"""
            カーブシェイプのcvのリストを返す。
            登録されたtransformが複数カーブを持つ場合もあるので
            戻り値にはリストの中にcvのリストが入っている。
            
            Returns:
                list:
        """
        return [cmds.ls('%s.cv[*]' % x)[0] for x in self.shapes()]

    def setTranslate(self, positionX, positionY, positionZ):
        r"""
            cvをローカルで移動する。
            
            Args:
                positionX (float):x座標
                positionY (float):y座標
                positionZ (float):z座標
        """
        cmds.move(
            positionX, positionY, positionZ, self.shapeCVs(), r=True, os=True
        )

    def setRotate(self, angleX, angleY, angleZ):
        r"""
            cvをローカルで回転させる。
            
            Args:
                angleX (float):x軸
                angleY (float):y軸
                angleZ (float):z軸
        """
        cmds.rotate(angleX, angleY, angleZ, self.shapeCVs(), os=True)

    def setScale(self, sizeX, sizeY, sizeZ):
        r"""
            cvをローカルでスケールする。
            
            Args:
                sizeX (float):x軸
                sizeY (float):y軸
                sizeZ (float):z軸
        """
        cmds.scale(sizeX, sizeY, sizeZ, self.shapeCVs(), os=True)

    def setColorIndex(self, colorIndex=0):
        r"""
            シェイプの色を変更する。
            
            Args:
                colorIndex (tuple):intまたはfloatを３つ持つtuple
        """
        if isinstance(colorIndex, int) and not 0 <= colorIndex <= 32:
            raise ValueError('The color index is out of range')
        for shape in self.shapes():
            setColorIndex(shape, colorIndex)

    def setLineWidth(self, lineWidth):
        r"""
            カーブのラインの太さを設定する。
            addCurveWidthCtrlAttrによりカスタムアトリビュートが設定されて
            いる場合はカスタムアトリビュートを、設定されていない場合はlineWidth
            アトリビュートに値を設定する。

            Args:
                lineWidth (float):
        """
        shapes = self.shapes()
        if not shapes:
            return
        for shape in shapes:
            for at in (CurveWidthAttr, 'lineWidth'):
                attr = at
                if cmds.attributeQuery(attr, ex=True, n=shape):
                    break
            else:
                continue
            cmds.setAttr(shape + '.' + attr, lineWidth)


def transferCurveShape(srcCrv=None, dstCrv=None):
    r"""
        srcCrvの形状をdstCrvへ転送する
        
        Args:
            srcCrv (str):転送元のカーブの名前
            dstCrv (str):転送先のカーブの名前
    """
    # エラーチェック。=========================================================
    if not srcCrv or not dstCrv:
        selected = node.selected()
        if not srcCrv:
            srcCrv = selected.pop(0)
        if not dstCrv:
            dstCrv = selected.pop(0)
    curves = []
    for crv, label in zip(
        node.toObjects([srcCrv, dstCrv]),
        ('source curve', 'destination curve')
    ):
        if not crv:
            raise ValueError('The %s "%s" does not exist.' % (label, crv))
        if crv.isType('nurbsCurve'):
            curves.append(crv)
            continue
        if crv.isType('transform'):
            children = crv.children(type='nurbsCurve')
            if not children:
                raise ValueError(
                    'The %s "%s" is not curve.' % (label, crv)
                )
            curves.append(children[0])
            continue
        raise ValueError('The %s "%s" is not curve.' % (label, crv))
    # =========================================================================

    tmp_trsgeo = node.createNode('transformGeometry')
    tmp_mltmtx = node.createNode('multMatrix')
    curves[0].attr('local') >> tmp_trsgeo.attr('inputGeometry')
    curves[0].attr('parentMatrix') >> tmp_mltmtx/'matrixIn[0]'
    curves[1].attr('parentInverseMatrix') >> tmp_mltmtx/'matrixIn[1]'
    tmp_mltmtx.attr('matrixSum') >> tmp_trsgeo.attr('transform')
    tmp_trsgeo.attr('outputGeometry') >> curves[1].attr('create')
    cmds.delete(curves[1], ch=True)
    
    cmds.select(srcCrv)

