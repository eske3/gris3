#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ポリゴン編集を行うためのサポート機能を提供する。
    
    Dates:
        date:2017/08/17 22:43[Eske](eske3g@gmail.com)
        update:2025/05/27 16:59 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from abc import ABCMeta, abstractmethod
import re

from maya import mel

from .. import node, mathlib
from . import util, selectionUtil, cleanup
cmds = node.cmds

RENDER_STATS = {
    'castsShadows'          : 1,
    'receiveShadows'        : 1,
    'motionBlur'            : 1,
    'primaryVisibility'     : 1,
    'smoothShading'         : 1,
    'visibleInReflections'  : 1,
    'visibleInRefractions'  : 1,
    'doubleSided'           : 1,
    'opposite'              : 1,
}

def getSekectedComponents(maskNumbers=[31]):
    r"""
        選択中のコンポーネントのリストを返す。
        maskNumbersはcmds.filterExpandのsmに渡すものに準拠する。
        
        Args:
            maskNumbers (list):マスク番号のリスト(デフォルトは31)
            
        Returns:
            list:
    """
    return cmds.filterExpand(sm=maskNumbers) or []

# /////////////////////////////////////////////////////////////////////////////
# ポリゴン編集機能。                                                         //
# /////////////////////////////////////////////////////////////////////////////
class PolyOperation(object):
    r"""
        ポリゴンオブジェクトが新規で作成された際の挙動を制御する
    """
    def __init__(self, objectList=None):
        r"""
            Args:
                objectList (list):編集対象オブジェクトのリスト。
        """
        self.__object = None
        self.__restore_trs = True

        objectList = node.selected(objectList, type=['transform', 'mesh'])
        if not objectList:
            raise ValueError('No polygonal objects selected.')

        # アトリビュート取得のためのポリゴンメッシュを検出する。===============
        for i in range(len(objectList)-1, -1, -1):
            if objectList[i].isType('mesh'):
                self.__object = objectList[i]
                break
            shapes = objectList[i].shapes()
            if not shapes:
                meshlist = objectList[i].allChildren(type='mesh')
                if not meshlist:
                    continue
                self.__object = meshlist[-1]
                break
            self.__object = shapes[0]
            break

        if not self.__object:
            raise ValueError('No polygonal objects selected.')
        # =====================================================================

        # アトリビュートの状態を記憶する。=====================================
        self.__targets = objectList
        transform = self.__object.parent()
        self.setName(transform.shortName())
        self.setParent(self.__targets[-1].parent())
        self.__members = []
        self.__dumy = None

        self.__stats = {x : y for x, y in RENDER_STATS.items()}
        
        self.setTransform(transform.matrix(False))
        self.setPivots(*transform.pivot())
        # =====================================================================

    def setObject(self, object):
        r"""
            操作対象オブジェクトをセットする。
            
            Args:
                object (str):操作対象となるオブジェクト名
        """
        self.__object = node.asObject(object)

    def object(self):
        r"""
            セットされている操作対象オブジェクトを返す。
            
            Returns:
                node.AbstractNode:
        """
        return self.__object

    def setName(self, name):
        r"""
            ターゲットとなるオブジェクトの名前を設定する
            
            Args:
                name (str):
        """
        self.__name = name

    def name(self):
        r"""
            ターゲットとなるオブジェクトの名前を返す。
            
            Returns:
                str:
        """
        return self.__name

    def setTransform(self, transform):
        r"""
            Args:
                transform (any):
        """
        self.__transform = transform

    def transform(self, asMatrixType=True):
        r"""
            設定されている行列値を返す。
            
            Args:
                asMatrixType (bool):
                
            Returns:
                list:asMatrixTypeがTrueの場合MMatrixで返す。
        """
        return (
            node.MMatrix(self.__transform)if asMatrixType
            else self.__transform
        )

    def setPivots(self, rotatePivot, scalePivot):
        r"""
            Args:
                rotatePivot (list):rotateピボットの座標
                scalePivot (list):scaleピボットの座標
        """
        self.__rotate_pivot = rotatePivot
        self.__scale_pivot = scalePivot

    def pivots(self):
        return (self.__rotate_pivot, self.__scale_pivot)

    def targets(self):
        r"""
            操作対象のオブジェクトのリストを返す。
            
            Returns:
                list:
        """
        return self.__targets[:]

    def setParent(self, parent):
        r"""
            操作対象となるオブジェクトの親を設定する。
            
            Args:
                parent (str):
        """
        self.__parent = node.asObject(parent)

    def parent(self):
        r"""
            操作対象となるオブジェクトのうち、最初のオブジェクトの親を返す。
            
            Returns:
                str:
        """
        return self.__parent

    def members(self):
        r"""
            メンバーを返す。
            
            Returns:
                list:
        """
        return self.__members

    def popAttr(self):
        r"""
            処理後のノードに適応するアトリビュートを保持する
        """
        name = self.object().parent()()

        if self.parent():
            self.__members = self.parent().children()
        else:
            self.__members = node.ls(assemblies=True)
        for i in range(len(self.__members)):
            if not name == self.__members[i]:
                continue
            self.__members = self.__members[:i]
            break
        for stat in RENDER_STATS:
            self.__stats[stat] = self.__object(stat)
    
    def setRestoringTransform(self, isRetoring):
        r"""
            Args:
                isRetoring (any):
        """
        self.__restore_trs = bool(isRetoring)
    
    def isRestoringTransform(self):
        return self.__restore_trs

    def pushAttr(self):
        r"""
            保持されたアトリビュートを処理後のノードに適応する
        """
        obj = self.object()
        if self.parent():
            self.parent().addChild(obj)
        cmds.select(obj)
        cmds.reorder(f=True)

        # アウトライナーの順番調整。===========================================
        num = len(self.__members)
        if num > 0:
            for i in range(num-1, -1, -1):
                if not self.__members[i].exists():
                    continue
                break
            num = 0
            for i in range(i+1):
                if self.__members[i].exists():
                    num += 1
            cmds.reorder(r=num)
        # =====================================================================

        # RenderStatsの復元。
        for stat in RENDER_STATS:
            obj(stat, self.__stats[stat])

        # transform情報の復元。================================================
        if self.isRestoringTransform():
            matrix = self.transform()
            cur_matrix = node.MMatrix(obj.matrix(False))
            pivots = self.pivots()
            obj.setMatrix((cur_matrix*matrix.inverse()), False)
            obj.freeze()
            obj.setMatrix(matrix, False)
            obj.setRotatePivot(pivots[0])
            obj.setScalePivot(pivots[1])
        # =====================================================================

        self.setObject(node.asObject(obj.rename(self.name())))
    # =========================================================================

    def preMethod(self):
        r"""
            操作実行前に呼ばれるメソッド。
        """
        if not self.parent():
            return

        self.__dumy = node.createNode('transform', p=self.parent())
        node.createNode('mesh', p=self.__dumy)

    def method(self):
        r"""
            再実装用の操作内容を記述するメソッド。
        """
        pass
    
    def postMethod(self):
        r"""
            操作実行後に呼ばれるメソッド。
        """
        if self.__dumy:
            self.__dumy.delete()

        if cmds.objExists(self.__object):
            return
        setlist = node.toObjects(
            cmds.listSets(ets=True, type=1, object=self.__object())
       )
        sgs = [x for x in setlist if x.isType('shadingEngine')]
        if len(sgs) != 1:
            return
        cmds.sets(
            self.__object(), e=True, forceElement=sgs[0]
       )

    def operate(self, popAttr=True, pushAttr=True):
        r"""
            操作を実行する。
            
            Args:
                popAttr (bool):編集前のアトリビュートを保持するかどうか
                pushAttr (bool):保持したアトリビュートを復元するかどうか
        """
        self.preMethod()

        if popAttr:
            self.popAttr()

        self.method()

        if pushAttr:
            self.pushAttr()

        self.postMethod()
        mel.eval('setSelectMode("objects", "Objects");')


class Combine(PolyOperation):
    r"""
        ポリゴンオブジェクトをコンバインする。
    """
    def method(self):
        r"""
            内部で実行されるメソッド。
        """
        unite = cmds.polyUnite(self.targets(), ch=False, mergeUVSets=True)
        for tgt in self.targets():
            if not cmds.objExists(tgt):
                continue
            tgt.delete()
        self.setObject(unite[0])


class Boolean(PolyOperation):
    r"""
        ポリゴンオブジェクトをブーリアンする。
    """
    operationlist = { 'union':1, 'difference':2, 'intersection':3 }
    def __init__(self, operation='union'):
        r"""
            初期化を行う。引数operationには下記のいずれかを渡す。
            union, difference, intersection
            
            Args:
                operation (str):union, difference, intersectionのいずれか
        """
        super(Boolean, self).__init__()
        if not operation in self.operationlist:
            raise TypeError(
                'The argument "operation" is only "union", "difference" or '
                '"intersection".'
           )
        first_obj = self.targets()[0]
        self.setParent(first_obj.parent())
        self.setName(first_obj())
        self.setTransform(first_obj.matrix(False))
        self.setPivots(*first_obj.pivot())
        self.__operation = operation

    def operation(self):
        return self.__operation

    def method(self):
        r"""
            内部で実行されるメソッド。
        """
        boolOp = cmds.polyCBoolOp(
            self.targets(),
            op=self.operationlist[self.operation()],
            ch=True,
            useThresholds=1, preserveColor=0,
            classification=1
        )
        self.setObject(boolOp[0])
        for target in self.targets():
            target.rename(target+'_bl')


class PBoolean(Boolean):
    r"""
        新しい機構のブーリアン機能を提供するクラス。
    """

    operationlist = {
        'union':1, 'difference':2, 'intersection':3, 'differenceBA':4,
        'slice':5, 'holePunch':6, 'cutOut':7, 'splitEdges':8
    }
    def method(self):
        from maya.plugin.polyBoolean import booltoolUtils
        cmds.select(self.targets())
        for mesh in selectionUtil.listShapes('mesh', self.targets()):
            mesh = node.asObject(mesh)
            for at in cmds.listAttr(mesh/'drawOverride'):
                attr = mesh.attr(at)
                if not attr.isConnected():
                    continue
                attr.disconnect()
        bool_op = booltoolUtils.createBoolTool(
            self.operationlist[self.operation()]
        )
            
        self.setObject(bool_op[0])
        for target in self.targets():
            target.rename(target+'_bl')


def polyBoolean(operation):
    r"""
        Args:
            operation (any):
    """
    plugin_name = 'polyBoolean'
    cls = None
    try:
        if not cmds.pluginInfo(plugin_name, q=True, l=True):
            cmds.loadPlugin(plugin_name)
        cls = PBoolean
    except Exception as e:
        pass
    cls = cls if cls else Boolean
    cls(operation).operate()

# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////

def reassignMaterial(nodelist):
    r"""
        オブジェクトにアサインされているマテリアルが一つの場合
        そのマテリアルを再アサインしてファセットアサイン状態を解消する。
        
        Args:
            nodelist (list):
    """
    nodelist = node.selected(nodelist)
    for n in nodelist:
        sgs = cmds.listSets(o=n, ets=True, type=1)
        if len(sgs) != 1:
            continue
        cmds.sets(n, e=True, forceElement=sgs[0])


def extractPolyFace(isDuplicated=False, faces=None):
    r"""
        現在請託されている面を剥離またはコピーする。
        
        Args:
            isDuplicated (bool):面をコピーするかどうか。
            faces (list):対象フェースのリスト。
    """
    if faces is None:
        faces = cmds.filterExpand(sm=34)
    else:
        faces = cmds.filterExpand(faces, sm=34)
    if not faces:
        return

    result = []
    # 現在選択されているシェイプのフェース番号を収集する。=====================
    shapelist = {}
    name_index_ptn = re.compile('(.*)\.f\[(\d+)\]$')
    for face in faces:
        r = name_index_ptn.match(face)
        if not r:
            continue
        index = int(r.group(2))
        shapename = r.group(1)
        if not shapename in shapelist:
            shapelist[shapename] = [index]
        else:
            shapelist[shapename].append(index)
    # =========================================================================

    # フェースの編集。=========================================================
    for mesh, indexes in shapelist.items():
        if cmds.nodeType(mesh) == 'mesh':
            mesh = cmds.listRelatives(mesh, p=True, pa=True)[0]
        new_mesh = cmds.duplicate(mesh, rr=True)[0]

        # クリーンナップ。
        deleted = []
        for shape in cmds.listRelatives(new_mesh, pa=True, shapes=True):
            if cmds.nodeType(shape) != 'mesh':
                deleted.append(shape)
            if cmds.getAttr(shape+'.io'):
                deleted.append(shape)
        if deleted:
            cmds.delete(deleted)

        # 削除するフェース番号を収集し、そのフェースを削除する。
        all_indexes = set(range(cmds.polyEvaluate(mesh, f=True)))
        all_indexes -= set(indexes)
        cmds.delete(['{}.f[{}]'.format(new_mesh, x) for x in all_indexes])
        result.append(new_mesh)
        
        # isDuplicatedがFalseの場合、元メッシュの選択フェースを削除する。
        if isDuplicated:
            continue
        cmds.delete(['{}.f[{}]'.format(mesh, x) for x in indexes])
    # =========================================================================

    if result:
        reassignMaterial(result)
        cmds.select(result, r=True, ne=True)
    return result


# /////////////////////////////////////////////////////////////////////////////
# ミラーリングツール。                                                       //
# /////////////////////////////////////////////////////////////////////////////
def mirrorObject(
    targetNodes=None, axis='x', mirrorPivotMatrix=None
):
    r"""
        targetNodesをミラーリングする。
        
        Args:
            targetNodes (list):操作対象ノードのリスト
            axis (str):ミラー軸。x,yまたはz
            mirrorPivotMatrix (list):ミラー軸を変更する行列。
    """
    targetNodes = node.selected(targetNodes, type='transform')
    if not targetNodes:
        return
    # ミラー軸を定義する行列をMMatrixにキャストする。==========================
    if not mirrorPivotMatrix:
        mirrorPivotMatrix = node.identityMatrix()
    mirrorPivotMatrix = node.MMatrix(mirrorPivotMatrix)
    mirror_inv_mtx = mirrorPivotMatrix.inverse()
    # =========================================================================

    # ミラーリング用行列を作成する。===========================================
    axis_table = {'y':5, 'z':10}
    neg_index = axis_table.get(axis.lower(), 0)
    revmtx = node.MMatrix(node.identityMatrix())
    revmtx[neg_index] = -1
    # =========================================================================

    for target in targetNodes:
        mtx = node.MMatrix(target.matrix())
        rp = target.rotatePivot()
        sp = target.scalePivot()
        r = mtx * mirror_inv_mtx * revmtx * mirrorPivotMatrix
        target.setMatrix(r)

        # ピボットをミラーリング位置へ移動。-----------------------------------
        for piv, method in (
            (rp, target.setRotatePivot), (sp, target.setScalePivot)
        ):
            p_mtx = node.MMatrix(
                [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, piv[0], piv[1], piv[2], 1]
            )
            r = p_mtx * mirror_inv_mtx * revmtx * mirrorPivotMatrix
            method((r[12], r[13], r[14]))
        # ---------------------------------------------------------------------


class AbstractPostAction(object):
    r"""
        ミラー後のポストアクションを定義する抽象クラス。
    """
    __metaclass__ = ABCMeta
    def __init__(self):
        self.init()

    def init(self):
        r"""
            再実装用の初期化メソッド。
        """
        pass


    def targetTypes(self):
        r"""
            対象ターゲットのノードタイプを返す。
            
            Returns:
                str or list:
        """
        return ''

    def checkTargetType(self, obj):
        r"""
            ターゲットが指定のタイプかどうかを判定する。
            
            Args:
                obj (node.AbstractNode):
                
            Returns:
                list:
        """
        types = self.targetTypes()
        if types is None:
            return [obj]
        return [obj] if obj.isType(types) else None

    @abstractmethod
    def action(self, source, object):
        r"""
            ターゲットに対して行う処理を記述する再実装専用メソッド。
            
            Args:
                source (node.AbstractNode):
                object (node.AbstractNode):
        """
        pass

    def doAction(self, source, object):
        r"""
            アクションを呼び出す。呼び出し後、一度ノードタイプの
            チェックを行い、適合しない場合は無視する。
            
            Args:
                source (node.AbstractNode):
                object (node.AbstractNode):
        """
        targets = self.checkTargetType(object)
        if not targets:
            return
        for target in targets:
            self.action(source, target)


class AbstractShapePostAction(AbstractPostAction):
    r"""
        shapeに対するポストアクションを定義するクラス。
    """
    def checkTargetType(self, obj):
        r"""
            ターゲットのシェイプが指定のタイプかどうかを判定する。
            
            Args:
                obj (node.AbstractNode):
                
            Returns:
                list:
        """
        shapes = obj.shapes()
        if not shapes:
            return False
        t_type = self.targetTypes()
        result = []
        return [x for x in shapes if x.isType(t_type)]


class TransformPostAction(AbstractPostAction):
    r"""
        transformノードに対するポストアクションを定義するクラス。
    """
    def init(self):
        self.__flags = {
            't':True, 'r':True, 's':True, 'pn':True
        }

    def setFlags(self, option=0b1111):
        r"""
            t,r,s,preserveNormalのフラグを2進数4bitで指定する。
            
            Args:
                option (bin):
        """
        flags = [bool(int(x)) for x in bin(option)[2:]]
        for at, flag in zip(('t', 'r', 's', 'pn'), flags):
            self.__flags[at] = flag

    def targetTypes(self):
        r"""
            transformを返す。
            
            Returns:
                str:
        """
        return 'transform'

    def action(self, source, object):
        r"""
            transformノードをフリーズする。
            
            Args:
                source (node.AbstractNode):
                object (node.AbstractNode):
        """
        cmds.makeIdentity(object(), a=True, **self.__flags)


class RenamePostAction(AbstractPostAction):
    r"""
        ノードをリネームするポストアクションを定義するクラス。
    """
    def init(self):
        from gris3.tools import nameUtility
        self.__manager = nameUtility.MultNameManager()

    def setSearchingText(self, text):
        r"""
            置換される文字列を設定する。
            
            Args:
                text (str):
        """
        self.__manager.setSearchingText(text)

    def setReplacingText(self, text):
        r"""
            置換する文字列を設定する。
            
            Args:
                text (str):
        """
        self.__manager.setReplacingText(text)

    def targetTypes(self):
        r"""
            対象ターゲットのタイプを返すが、対象は無いのでNoneを返す。
            
            Returns:
                None:
        """
        return None

    def action(self, source, object):
        r"""
            リネーム処理を行う。
            
            Args:
                source (node.AbstractNode):
                object (node.AbstractNode):
        """
        if not self.__manager.searchingText():
            return
        from gris3.tools import nameUtility
        targets = object.allChildren()
        targets.append(object)
        self.__manager.setNameList([x.shortName() for x in targets])
        nameUtility.multRename(
            [x() for x in targets], self.__manager.result()
        )


class ParentPostAction(AbstractPostAction):
    r"""
        ここに説明文を記入
    """
    def init(self):
        self.setSearchingText('')
        self.setReplacingText('')

    def setSearchingText(self, text):
        r"""
            置換される文字列を設定する。
            
            Args:
                text (str):
        """
        self.__searching_text = text

    def setReplacingText(self, text):
        r"""
            置換する文字列を設定する。
            
            Args:
                text (str):
        """
        self.__replacing_text = text

    def targetTypes(self):
        r"""
            対象ターゲットのノードタイプを返す。
            
            Returns:
                str:
        """
        return 'transform'

    def action(self, source, object):
        r"""
            親子付けを行う。
            
            Args:
                source (node.AbstractNode):
                object (node.AbstractNode):
        """
        if not self.__searching_text:
            return
        parent = source.parent()
        if not parent:
            return
        opp_parent = node.asObject(
            parent.replace(self.__searching_text, self.__replacing_text, 1)
        )
        if not opp_parent or opp_parent == parent:
            return
        try:
            opp_parent.addChild(object())
        except:
            pass


class NurbsPostAction(AbstractShapePostAction):
    r"""
        NURBS用のポストアクションを定義するクラス。
    """
    def init(self):
        self.__direction = 0

    def setDirection(self, direction):
        r"""
            NURBSの方向を反転させるオプション。
            0 : U方向の反転
            1 : V方向の反転
            3 : UVの入れ替え
            
            Args:
                direction (list):
        """
        if not direction in (0, 1, 3):
            raise ValueError('The given value must be a 0, 1 and 3.')
        self.__direction = direction

    def targetTypes(self):
        r"""
            nurbsSurfaceを返す。
            
            Returns:
                str:
        """
        return 'nurbsSurface'

    def action(self, shape):
        r"""
            NURBSのdirectionを変更し、OppositeをOffにする。。
            
            Args:
                shape (any):(node.AbstractNode) : []
        """
        cmds.reverseSurface(
            shape(), d=self.__direction, ch=False, rpo=1
      )
        shape('opposite', 0)


class MirrorObjectUtil(object):
    r"""
        オブジェクトをミラーリングする機能を提供するクラス。
    """
    Duplicated, Instanced, Self = range(3)
    NoBoundingBox, Minimum, Maximum, MinimumForAll, MaximumForAll = range(5)
    def __init__(self):
        r"""
            初期化を行う。
        """
        self.__axis = 'x'
        self.__mirror_pivot_mtx = None
        self.__mirror_with = 0
        self.__postactions = []
        self.__bb = None

    @staticmethod
    def createMirrorPlane(name='mirror_plane'):
        r"""
            ミラー軸を定義するプレビュー用プレーンを作成する。
            
            Args:
                name (str):
        """
        trs = node.createNode('transform', n=name)
        trs.editAttr(['s', 'v'], k=False)
        shape = node.createNode('sketchPlane', n=trs+'Shape', p=trs)
        return trs

    @staticmethod
    def setPlaneDirection(plane, axis):
        r"""
            プレーンの向きを変更する。
            
            Args:
                plane (str):プレーンの名前
                axis (str):向ける向きを表す文字列。(x, y, z)
        """
        matrix_axis = {
            'x':[0, 0 , -1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1],
            'y':[1, 0 , 0, 0, 0, 0, -1, 0, 0, 1, 0, 0, 0, 0, 0, 1],
            'z':[1, 0 , 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
        }
        matrix = matrix_axis.get(axis.lower())
        if not matrix:
            raise ValueError(
                'The axis flag requires one of theese strings. x, y and z.'
            )
        plane = node.asObject(plane)
        plane.setMatrix(matrix, flags=0b0100)

    def setMirrorAxis(self, axis):
        r"""
            ミラーリングの軸を設定する。対応する値はx、y、ｚのいずれか
            
            Args:
                axis (str):x or y or z
        """
        if not axis.lower() in 'xyz':
            raise ValueError('The mirror axis must be "x", "y" ans "z".')
        self.__axis = axis.lower()

    def mirrorAxis(self):
        r"""
            ミラーリングの軸を返す。
            
            Returns:
                str:
        """
        return self.__axis

    def setMirrorPivotMatrix(self, matrix=None):
        r"""
            ミラーリング軸を補正する行列を設定する。
            
            Args:
                matrix (list):16個のfloatを持つリスト
        """
        self.__mirror_pivot_mtx = matrix

    def setMirrorPivotByNode(self, nodeName):
        r"""
            ミラーリング軸となるオブジェクトをセットする
            
            Args:
                nodeName (str):対象オブジェクト名
                
            Returns:
                node.AbstractNode:
        """
        obj = node.asObject(nodeName)
        if not obj:
            raise RuntimeError('"{} does not exist.'.format(nodeName))
        self.setMirrorPivotMatrix(obj.matrix())
        return obj

    def mirrorPivotMatrix(self):
        r"""
            ミラーリング軸を補正する行列を返す。
            
            Returns:
                list:float x 16のリスト
        """
        return self.__mirror_pivot_mtx

    def setMirrorWith(self, mode):
        r"""
            ミラーする対象をどうするかを設定する。
            Duplicated : ターゲットのコピー
            Instanced : ターゲットのインスタンス
            Self : ターゲットの自身
            
            Args:
                mode (int):0~2
        """
        if not mode in (self.Duplicated, self.Instanced, self.Self):
            raise ValueError(
                'setMirrorWith method requests one '
                'from these value : {}'.format(
                    ', '.join(
                        [
                            self.__class__.__name__ + '.' + x
                            for x in ('Duplicated', 'Instanced', 'Self')
                        ]
                  )
              )
          )
        self.__mirror_with = mode

    def mirrorWith(self):
        r"""
            ミラーする対象をどうするかを返す。
            
            Returns:
                int:
        """
        return self.__mirror_with

    def setPostActions(self, *actions):
        r"""
            ミラー後に実行するポストアクションをセットする。
            
            Args:
                *actions (any):
        """
        self.__postactions = actions[:]

    def postActions(self):
        r"""
            ミラー後に実行するポストアクションのリストを返す。
            
            Returns:
                list:
        """
        return self.__postactions

    def useBoundingBox(self, minMax=0):
        r"""
            バウンディングボックスを基準にミラーを行う。
            NoBoundingBox : バウンディングボックスを使用しない。
            Minimum : バウンディングボックスの最小値を使用。
            Maximum : バウンディングボックスの最大値を使用。
            MinimumForAll : 全てのバウンディングボックスの最小値を使用。
            MaximumForAll : 全てのバウンディングボックスの最大値を使用。
            
            Args:
                minMax (int):
        """
        if not minMax in range(5):
            raise ValueError(
                'The given value must be one of theese : {}'.format(
                    ', '.join(
                        [
                            self.__class__.__name__ + '.' + x
                            for x in (
                                'NoBoundingBox', 'Minimum', 'Maximum',
                                'MinimumForAll', 'MaximumForAll'
                          )
                        ]
                  )
              )
          )
        self.__bb = minMax

    def mirror(self, targetNodes=None):
        r"""
            ミラーリングを実行する。
            
            Args:
                targetNodes (list):
        """
        # ローカル関数。+++++++++++++++++++++++++++++++++++++++++++++++++++++++
        def duplicate(obj):
            r"""
                objのコピーを返す。
                
                Args:
                    obj (node.AbstractNode):
                    
                Returns:
                    node.AbstractNode:
            """
            return node.duplicate(obj)[0]
    
        def instance(obj):
            r"""
                objのインスタンスを返す。
                
                Args:
                    obj (node.AbstractNode):
                    
                Returns:
                    node.AbstractNode:
            """
            return node.asObject(cmds.instance(obj())[0])

        def returnSelf(obj):
            r"""
                引き数自身を無加工で返す。
                
                Args:
                    obj (node.AbstractNode):
                    
                Returns:
                    node.AbstractNode:
            """
            return obj
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        targetNodes = node.selected(targetNodes, type='transform')
        if not targetNodes:
            raise ValueError('No transform nodes selected.')

        result = []
        axis = self.mirrorAxis()
        axis_index = 'xyz'.index(axis)
        bb_offset = axis_index + (
            [0, 0, 3, 0, 3][self.__bb] if self.__bb else 0
      )
        axis_index = 12 + axis_index

        if self.__bb > 2:
            pivots = [
                cmds.exactWorldBoundingBox(x)[bb_offset] for x in targetNodes
            ]
            mirror_piv_mtx = node.identityMatrix()
            pivot = max(pivots) if self.__bb > 3 else min(pivots)
            mirror_piv_mtx[axis_index] = pivot
        else:
            mirror_piv_mtx = self.mirrorPivotMatrix()

        
        mirror_with = self.mirrorWith()
        method = [duplicate, instance, returnSelf][mirror_with]

        for target in targetNodes:
            mirrored = method(target)
            if 0 < self.__bb < 3:
                value = cmds.exactWorldBoundingBox(mirrored)[bb_offset]
                mirror_piv_mtx = node.identityMatrix()
                mirror_piv_mtx[axis_index] = value

            mirrorObject(mirrored, axis, mirror_piv_mtx)
            result.append(mirrored)

            if mirror_with == 1:
                # インスタンスの場合は何も処理を行わない。
                continue
            for action in self.__postactions:
                action.doAction(target, mirrored)

        if result:
            cmds.select([x() for x in result], r=True, ne=True)
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////


def removePolyFaceOnHalf(axis=None, baseAxis='world'):
    r"""
        指定した軸の半分のポリゴンを削除する。
        
        Args:
            axis (mathlib.Axis):削除基準となる軸
            baseAxis (str):ワールドかローカルか
            
        Returns:
            bool:
    """
    from maya.api import OpenMaya
    class Position(object):
        r"""
            位置情報xyzアトリビュートで参照するための内部クラス
        """
        def __init__(self, x=0, y=0, z=0):
            r"""
                Args:
                    x (float):
                    y (float):
                    z (float):
            """
            self.x = x
            self.y = y
            self.z = z
    
    def get_localize_matrix(dag_path, fn_trs):
        r"""
            Args:
                dag_path (any):
                fn_trs (any):
        """
        w_mtx = list(
            fn_trs.transformation().asMatrix() * dag_path.exclusiveMatrix()
        )
        w_mtx[12:15] = list(fn_trs.rotatePivot(OpenMaya.MSpace.kWorld))[:3]
        w_mtx = OpenMaya.MMatrix(w_mtx)
        return w_mtx

    def localized_point(pos, inverse_mtx):
        r"""
            Args:
                pos (OpenMaya.MPoint):
                inverse_mtx (list):
        """
        if not inverse_mtx:
            return pos
        mtx = node.identityMatrix()
        mtx[12:15] = list(pos)[:3]
        new_pos = node.multiplyMatrix([mtx, inverse_mtx])
        return OpenMaya.MPoint(new_pos[12:15])
            
    selection = OpenMaya.MGlobal.getActiveSelectionList()
    if selection.isEmpty():
        return
    pre_selected = cmds.ls(sl=True)

    if axis is None:
        _mtx = node.identityMatrix()
        _mtx[12] = 1
        axis = mathlib.Axis(mathlib.FMatrix(_mtx))

    iter = OpenMaya.MItSelectionList(selection)
    deleted_list = []
    while not iter.isDone():
        _axis = axis.lower()
        inv_mtx = None
        dagpath = iter.getDagPath()
        trans_fn = OpenMaya.MFnTransform(dagpath)
        poly_iter = OpenMaya.MItMeshPolygon(dagpath)
        if baseAxis == 'world':
            center = Position()
        elif baseAxis == 'pivot':
            center = trans_fn.rotatePivot(OpenMaya.MSpace.kWorld)
        elif baseAxis == 'center':
            center = trans_fn.boundingBox.center
        else:
            mtx = get_localize_matrix(dagpath, trans_fn)
            vec = OpenMaya.MMatrix(axis.asMatrix().asList())
            inv_mtx = mtx.inverse()
            _axis = mathlib.Axis(mathlib.FMatrix(list(vec * inv_mtx)))
            center = OpenMaya.MPoint(0, 0, 0)
            inv_mtx = list(inv_mtx)
        if _axis == '+x':
            fn = lambda x, y : x.x > y.x
        elif _axis == '-x':
            fn = lambda x, y : x.x < y.x
        elif _axis == '+y':
            fn = lambda x, y : x.y > y.y
        elif _axis == '-y':
            fn = lambda x, y : x.y < y.y
        elif _axis == '+z':
            fn = lambda x, y : x.z > y.z
        elif _axis == '-z':
            fn = lambda x, y : x.z < y.z
        else:
            raise ValueError('axis must be a type : {}'.format(mathlib.Axis))

        while not poly_iter.isDone():
            face_pos = poly_iter.center(OpenMaya.MSpace.kWorld)
            if fn(localized_point(face_pos, inv_mtx), center):
                face_name = '{}.f[{}]'.format(
                    dagpath.partialPathName(), poly_iter.index()
                )
                deleted_list.append(face_name)
            poly_iter.next()
        iter.next()
    if not deleted_list:
        return False
    cmds.delete(deleted_list)
    cmds.select(pre_selected, r=True, ne=True)
    return True


def mirrorGeometry(nodelist=None, axis=0, baseAxis='world'):
    r"""
        mirrorGeometryを行う
        
        Args:
            nodelist (list):対象ノードのリスト
            axis (int):ミラー軸を表す整数
            baseAxis (str): world, local, pivotまたはboundingBox
        
        Returns:
            list: 生成されたpolyMirrorノードのリスト
    """
    nodelist = node.selected(nodelist)
    results = []
    for n in nodelist:
        args = {
            'ws':1, 'direction':axis, 'mergeMode':1,
            'mergeThresholdType':1, 'mergeThreshold':0.0001,
            'ch':True
        }
        if baseAxis == 'world':
            args['pivot'] = [0, 0, 0]
        elif baseAxis in ('pivot', 'local'):
            if n.isType('mesh'):
                piv = n.parent().rotatePivot()
            else:
                piv = n.rotatePivot()
            args['pivot'] = piv
        pm = cmds.polyMirrorFace(n, **args)
        results.extend(pm)
        if baseAxis == 'local':
            cmds.setAttr(pm[0]+'.mirrorAxis', 1)
    return results


def mirrorGeometryByAxis(nodelist=None, axis=None, baseAxis='world'):
    r"""
        任意の軸でmirrorGeometryを行うラッパー関数。
        baseAxisがlocalの場合は、引数axisはmathlib.Axisによる行列データが格納
        された軸情報である必要がある。
        軸情報の行列は、オフセット値をベクトルとして扱い、ミラーしたい軸を定義
        する。
        ミラー時に軸情報はローカル化され、polyMirrorのミラー軸に使用される。

        Args:
            nodelist (any):
            axis (mathlib.Axis):
            baseAxis (str): ミラーの基準空間

        Returns:
            list: 生成されたpolyMirrorノードのリスト
    """
    if axis is None:
        _mtx = node.identityMatrix()
        _mtx[12] = 1
        axis = mathlib.Axis(mathlib.FMatrix(_mtx))
    direction = {
        '+x' : 0, '-x' : 1, '+y' : 2, '-y' : 3, '+z' : 4, '-z' : 5
    }
    nodelist = node.selected(nodelist)
    if baseAxis != 'local':
        return mirrorGeometry(nodelist, direction[axis], baseAxis)
    results = []
    for n in nodelist:
        inv_mtx = node.MMatrix(n.inverseMatrix())
        vec = node.MMatrix(axis.asMatrix().asList())
        _axis = mathlib.Axis(mathlib.FMatrix(list(vec * inv_mtx)))
        results.extend(mirrorGeometry([n], direction[_axis], baseAxis))
    return results


def cutGeometry(operation='x'):
    r"""
        選択ポリゴンを任意の軸でカットする。
        
        Args:
            operation (str):カットする軸
    """
    cutnodes = cmds.polyCut(cd=operation)
    cmds.select(cutnodes, add=True)
    cmds.setToolTo('ShowManips')


def cutToolManipulator(facelist=None, name='cutToolManip#', isRandomColor=True):
    r"""
        polyCutを3点で制御するコントローラを追加したものを作成する。
        戻り値には作成されたノードの辞書を返す。辞書にキーは
        ・parent : トップノード
        ・root   : 全体を制御するgroup
        ・base   : cutプレーンの起点を制御するコントローラ
        ・aim    : cutプレーンの方向を制御するコントローラ
        ・up     : cutプレーンの法線方向を成魚するコントローラ
        ・cut    : cutプレーンノード
        
        Args:
            facelist (list):cutを適応するフェースのリスト
            name (str):作成されるコントローラのベース名
            isRandomColor (bool):
            
        Returns:
            dict:
    """
    if facelist is None:
        facelist = cmds.filterExpand(sm=[12, 34])
    else:
        facelist = cmds.filterExpand(facelist, sm=[12, 34])
    if not facelist:
        raise RuntimeError('No faces or polygonal object was selected.')

    transform = cmds.listRelatives(
        cmds.listRelatives(facelist[0], p=True, pa=True)[0], p=True, pa=True
    )[0]
    # transformノードの作成。==================================================
    trs = {}
    trs['parent'] = node.createNode('transform', n=name)
    cmds.parentConstraint(transform, trs['parent'])

    trs['root'] = node.createNode('transform', n=name)
    loc_tags = ('base', 'aim', 'up')
    for tag in loc_tags:
        trs[tag] = node.createNode(
            'transform',
            n=('%s%sLocator' % (trs['root'], (tag[0].upper()+tag[1:]))),
            p=trs['root']
        )
    cut = node.asObject(cmds.polyCut(facelist, ws=True, cd='Y', ch=True)[0])
    # =========================================================================

    # LocatorとAnnotationを追加する。==========================================
    shapes = {}
    for tag, typ in zip(loc_tags, ('annotationShape', 'locator', 'locator')):
        shapes[tag] = node.createNode(typ, n=(trs[tag]+'Shape'), p=trs[tag])
    shapes['base']('text', trs['root'](), type='string')
    # =========================================================================

    # rootグループの位置と回転をpolyCutに合わせる。============================
    w = cut('cutPlaneWidth')
    h = cut('cutPlaneHeight')
    trs['root']('translate', cut('cutPlaneCenter')[0])
    trs['root']('rotate', cut('cutPlaneRotate')[0])
    # =========================================================================

    # ロケーターを移動する。===================================================
    trs['aim']('translateY', h*0.5)
    trs['up']('translateZ', h*0.5)
    heightlist = [h*0.2 for x in range(3)]
    shapes['aim']('localScale', heightlist)
    shapes['up']('localScale', heightlist)
    # =========================================================================

    trs['root'].editAttr(['v'], k=False, l=False)
    for tag in loc_tags:
        trs[tag].editAttr(['r:a', 's:a', 'v'], k=False, l=False)

    # コネクションを形成する。=================================================
    shapes['aim'].attr('worldMatrix[0]') >> shapes['base']/'dagObjectMatrix[0]'
    decmtx = node.createUtil('decomposeMatrix')
    trs['base'].attr('worldMatrix') >> decmtx/'inputMatrix'
    decmtx.attr('outputTranslate') >> cut/'cutPlaneCenter'
    decmtx.attr('outputRotate') >> cut/'cutPlaneRotate'
    try:
        aim = node.asObject(
            cmds.aimConstraint(
                trs['aim'](), trs['base'](),
                w=1, aimVector=(0, 1, 0), upVector=(1, 0, 0),
                worldUpType='object', worldUpObject=trs['up']()
            )[0]
        )
    except Exception as e:
        cmds.select(trs['aim'], trs['base'], trs['up'])
        raise e

    orient = node.asObject(
        cmds.orientConstraint(trs['root'], trs['aim'])[0]
    )
    aim('io', 1)
    orient('io', 1)

    if isRandomColor:
        import random
        color_id = int(random.uniform(0, 80))
        color_id = color_id*0.1 + 1
        cmds.color(trs['root'], ud=color_id)
    # =========================================================================

    trs['parent'].addChild(trs['root'])
    trs['cut'] = cut
    cmds.select(trs['base'])
    return trs


def moveToClosestVtx(targetVts, destinationVts):
    r"""
        頂点targetVtsをdestinationVtsの中から最も近い頂点に移動する。
        
        Args:
            targetVts (list):
            destinationVts (list):
    """
    dst_pos = {
        x:node.MVector(cmds.pointPosition(x)) for x in destinationVts
    }
    for vtx in targetVts:
        pos = node.MVector(cmds.pointPosition(vtx))
        dstlist = {}
        for v, p in dst_pos.items():
            dstlist[(p-pos).length()] = p
        p = dstlist[min(dstlist)]
        cmds.xform(vtx, ws=True, t=p)


def getPointFromVectorToPlane(linePoint, lineVector, facePoint, faceNormal):
    r"""
        Args:
            linePoint (list):
            lineVector (list):
            facePoint (list):
            faceNormal (list):
    """
    m = -sum(
        [n*(x2-x1) for n, x1, x2 in zip(faceNormal, facePoint, linePoint)]
    )
    d = sum([x*y for x, y in zip(faceNormal, lineVector)])
    t = m / float(d)
    return([x+t*y for x, y in zip(linePoint, lineVector)])


def fitVertsToPlaneAlongEdge(point, normal, vertices=None):
    r"""
        任意のベクトル平面に沿って任意の頂点をフィットさせる。
        
        Args:
            point (list):位置を表す3つのfloat
            normal (list):面の方向ベクトルを表す３つのfloat
            vertices (list):フィットさせる頂点
    """
    # バーテックスの取得。
    if not vertices:
        vertices = cmds.filterExpand(sm=31)
    if not vertices:
        raise AttributeError('No vertices were specified.')

    n = node.MVector(normal)
    nn = n.normalize()
    c = node.MVector(point)

    datalist = []
    for vertex in vertices:
        v_pos = cmds.pointPosition(vertex, w=True)
        # 頂点を構成するエッジのうち、対象面と最も向きが近いベクトル上の点に
        # 頂点を移動する。
        edges = cmds.ls(
            cmds.polyListComponentConversion(vertex, fv=True, te=True), fl=True
        )
        edge_vectors = {}
        for edge in edges:
            vts = cmds.ls(
                cmds.polyListComponentConversion(edge, fe=True, tv=True),
                fl=True
            )
            a = node.MVector(cmds.pointPosition(vts[0]))
            b = node.MVector(cmds.pointPosition(vts[1]))
            v = b - a
            d = abs(nn * v.normalize())
            edge_vectors[d] = v
        line_vector = edge_vectors[max(edge_vectors.keys())]
        pos = getPointFromVectorToPlane(
            v_pos, list(line_vector), point, normal
        )
        datalist.append((vertex, pos))
    for vertex, pos in datalist:
        cmds.xform(vertex, ws=True, t=pos)


def fitVertsToFace(vertices=None, face=None):
    r"""
        頂点を、頂点を構成するエッジ上の線とフェースの交点にフィットさせる。
        
        Args:
            vertices (list):捜査対象頂点のリスト
            face (str):フィットさせるフェース
    """
    # ポリゴンフェースの取得。
    if not face:
        face = cmds.filterExpand(sm=34)
        if face:
            face = face[0]
    if not face:
        raise AttributeError('No face was specified.')
    n = util.getFaceNormal(face)
    c = util.getComponentCenter(face)[0]
    fitVertsToPlaneAlongEdge(c, n, vertices)


def createGeoGroup(targetNodes=None, nodeType='meshVarGroup'):
    r"""
        任意のオブジェクトを特定ルールに従ったグループ化する。
        グループ化の際には任意のオブジェクトの親ごとにまとめられる。
        
        Args:
            targetNodes (list):グループ化されるオブジェクトのリスト
            nodeType (str):グループ化するノードの種類
            
        Returns:
            list:
    """
    from gris3 import system
    nr = system.GlobalSys().nameRule()

    targetNodes = node.selected(targetNodes)
    parentlist = {}
    for target in targetNodes:
        parent = target.parent()
        if parent in parentlist:
            parentlist[parent].append(target)
        else:
            parentlist[parent] = [target]

    result = []
    for parent, targets in parentlist.items():
        try:
            nameobj = nr(parent())
            nameobj.setNodeType('geoGrp')
            name = nameobj()
        except Exception as e:
            name = parent+'_geoGrp'
        grp = node.createNode(nodeType, p=parent, n=name)
        attr = grp.addStringAttr('grisNodeType', default='geometryGroup')
        attr.setLock(True)
        grp.setMatrix()
        cmds.parent(targets, grp)
        result.append(grp)
    return grp


def unitePolygons(meshes=None, name='polyUnited#'):
    r"""
        複数のポリゴンをひとつにまとめる。
        この時元のポリゴンは消えずにそのまま残る
        
        Args:
            meshes (list):操作対象ポリゴンのリスト
            name (str):作成されるポリゴンの名前
            
        Returns:
            node.Transform:作成されたポリゴンオブジェクト
    """
    meshes = node.selected(meshes)
    if not meshes:
        return
    trs   = node.createNode('transform', n=name)
    shape = node.createNode('mesh', n='%sShape' % trs, p=trs)
    unt   = node.createNode('polyUnite', n='%s_pUnt' % trs)
    for i, mesh in enumerate(meshes):
        mesh.attr('outMesh') >> '%s.inputPoly[%s]' % (unt, i)
        mesh.attr('matrix') >> '%s.inputMat[%s]' % (unt, i)
    unt.attr('output') >> shape.attr('inMesh')
    cmds.sets(shape, e=True, forceElement='initialShadingGroup')
    cmds.select(trs)
    return trs


def copyAllBlendshapeTargets(mesh, blendShape):
    r"""
        blendShapeのターゲット数分meshを複製する
        
        Args:
            mesh (str):複製するメッシュ名
            blendShape (str):ブレンドシェイプの名前
            
        Returns:
            node.Transform:複製されたメッシュを格納するトップグループ名
    """
    bs = node.asObject(blendShape)
    attrnames = bs.listAttrNames()
    plugs = []
    grp = node.createNode('transform', n='%sFacialTgt_grp' % mesh)
    for attr in attrnames:
        p = bs.attr(attr)
        plugs.append((p, attr))
        p.set(0)

    for p, name in plugs:
        p.set(1)
        n = node.duplicate(mesh, rr=True)[0]
        p.set(0)
        cleanup.deleteUnusedIO([n])
        grp.addChild(n)
        n.rename(name)
    return grp


def creaseToHardEdges(meshlist=None):
    r"""
        ハードエッジに対してCreaseを適応する
        
        Args:
            meshlist (list):操作対象オブジェクト名のリスト
    """
    meshlist = node.selected(meshlist, et=['transform', 'mesh'])
    for mesh in meshlist:
        if mesh.isType('transform'):
            mesh = mesh.shapes(typ='mesh', ni=True)
            if not mesh:
                continue
            meshes = mesh
        else:
            meshes = [mesh]
        for mesh in meshes:
            cmds.displaySmoothness(
                divisionsU=3, divisionsV=3,
                pointsWire=16, pointsShaded=4, polygonObject=3
            )
            edges = []
            for edge in cmds.ls(mesh+'.e[*]', fl=True):
                if cmds.polyInfo(edge, ev=True)[0].split()[-1] != 'Hard':
                    continue
                edges.append(edge)
            if not edges:
                continue
            cmds.polyCrease(edges, op=0, v=10, ch=False)


def clearCreaseEdges(meshlist=None):
    r"""
        任意のメッシュのすべてのエッジのクリース情報を削除する
        
        Args:
            meshlist (list):対象メッシュのリスト
    """
    meshlist = node.selected(meshlist)
    for mesh in meshlist:
        cmds.polyCrease(mesh, op=2, ch=False)

        
def mergeSubdivCorner(vertices=None):
    r"""
        サブディビ用のコーナー処理を行うための便利関数。（ベータ版）
        
        Args:
            vertices (list or None):
    """
    def listComp(*nodes, **args):
        r"""
            polyListComponentConversion+lsの組み合わせを行うwrappper関数
            
            Args:
                *nodes (tuple):
                **args (dict):
                
            Returns:
                list:フラット化されたコンポーネントのリスト
        """
        return cmds.ls(
            cmds.polyListComponentConversion(*nodes, **args), fl=True
        )

    def edgeLengthList(edgelist):
        r"""
            Args:
                edgelist (list):
        """
        result = {}
        for edge in edgelist:
            vert = listComp(edge, fe=True, tv=True)
            veclist = [node.MVector(cmds.pointPosition(x)) for x in vert]
            l = (veclist[1] - veclist[0]).length()
            result.setdefault(l, []).append(edge)
        return result

    if not vertices:
        target_verts = cmds.filterExpand(sm=31)
    else:
        target_verts = cmds.filterExpand(vertices, sm=31)

    processing_vts = []
    processing_edges = []
    for tgt_vtx in target_verts:
        edges = listComp(tgt_vtx, te=True)
        if len(edges) < 3:
            continue
        collapsed_vts = []
        deleted_edge = []
        for edge in edges:
            vts = listComp(edge, fe=True, tv=True)
            index = vts.index(tgt_vtx)
            del vts[index]
            if len(vts) != 1:
                break
            sec_edges = listComp(vts, fv=True, te=True)
            if len(sec_edges) == 3:
                collapsed_vts.extend(vts)
            else:
                deleted_edge.append(edge)
        if len(collapsed_vts)!=2 or not deleted_edge:
            break
        pos = cmds.pointPosition(tgt_vtx)
        for v in collapsed_vts:
            cmds.move(pos[0], pos[1], pos[2], v)

        processing_vts.append(tgt_vtx)
        processing_vts.extend(collapsed_vts)
        
        # 複数あるエッジから最も短いエッジを抽出する。-------------------------
        lenlist = edgeLengthList(deleted_edge)
        processing_edges.append(lenlist[min(lenlist.keys())][0])
        # ---------------------------------------------------------------------

    if not processing_vts or not processing_edges:
        return
    cmds.delete(processing_edges)
    cmds.polyMergeVertex(processing_vts, d=0.001, am=1, ch=False)


def polyResetVertPosition(targets=None):
    # 後ほどMayaAPIで高速化した方が良いかも？
    r"""
        Args:
            targets (any):
    """
    targets = node.selected(targets)
    for tgt in targets:
        for vtx in cmds.ls(tgt+'.vtx[*]', fl=True):
            cmds.setAttr(vtx, 0, 0, 0)


def unlockAndSetNormal(nodelist=None, threshold=0.995):
    r"""
        メッシュのエッジが法線的にハードエッジになっているものを、Maya的な
        ハードエッジに変換する。
        主にFBX等で読み込んだハードエッジ情報がないオブジェクトに有効。
        
        Args:
            nodelist (list):操作対象メッシュのリスト
            threshold (float):判定のしきい値
    """
    pre_selection = cmds.ls(sl=True)
    meshlist = selectionUtil.listShapes('mesh', nodelist)
    for mesh in meshlist:
        hardedges = selectionUtil.selectHardEdges(mesh, False, threshold)
        cmds.polyNormalPerVertex(mesh, ufn=True)
        cmds.polySoftEdge(mesh, a=180, ws=1, ch=False)
        if hardedges:
            cmds.polySoftEdge(hardedges, a=0, ws=1, ch=False)
    if pre_selection:
        cmds.select(pre_selection, ne=True)

        
def duplicateConnectedClone(targets=None):
    r"""
        Args:
            targets (list):
    """
    targets = node.selected(targets, type=['transform', 'mesh'])
    created = []
    for tgt in targets:
        if tgt.isType('mesh'):
            tgt = tgt.parent()
        elif tgt.isType('transform'):
            if not tgt.shapes(typ='mesh'):
                continue
        else:
            continue
        new = node.duplicate(tgt)[0]
        trs_children = new.children(type='transform')
        if trs_children:
            cmds.delete(trs_children)
        cleanup.deleteUnusedIO(new, False)
        cmds.lattice(new)
        cmds.delete(new, ch=True)
        cmds.polyMoveFacet(new, ch=1)
        if new.parent():
            new = node.parent(new, w=True)[0]
        io = [x for x in new.children() if x('io') and x.isType('mesh')]
        tgt.attr('outMesh') >> io[0].attr('inMesh')
        created.append(node.rename(new, 'cloned_' + tgt))
    if created:
        cmds.select(created)
    return created
    

def idMtxGroup(targets=None):
    r"""
        Args:
            targets (list):
    """
    targets = node.selected(targets, type='transform')
    new_grp = node.asObject(cmds.group(em=True, n='group#'))
    if targets:
        cmds.parent(new_grp, targets[0].parent())
    new_grp.addChild(*targets)
    cmds.select([x() for x in targets], r=True)
    return new_grp

