#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Mayaのノードをクラス化してOOPで記述出来るようにするための機能を
    提供するモジュール。
    PyMel:のような動きをするが、PyMelよりも機能を制限し、代わりに
    初期化の速度を向上させたバージョン。
    
    Dates:
        date:2017/01/22 0:02[Eske](eske3g@gmail.com)
        update:2024/11/12 13:23 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import re

from maya import cmds
from maya import OpenMaya, OpenMayaAnim
from maya.api import OpenMaya as OpenMaya2
sutil = OpenMaya.MScriptUtil()
#from gris3.mayaCmds import parent as c_parent
from . import mayaCmds, colorUtil, mathlib, verutil
index_reobj = re.compile('(^.*[^\]])\[(\d+)\]$')

# /////////////////////////////////////////////////////////////////////////////
# ポインタ用クラス及び関数。                                                 //
# /////////////////////////////////////////////////////////////////////////////
class MPointor(object):
    r"""
        OpenMayaのポインタを扱うためのラッパークラス。
    """
    def __init__(self, pointer, restoreFunc):
        r"""
            Args:
                pointer (ptr):
                restoreFunc (function):ポインタを値に復元する関数
        """
        self.__pointer = pointer
        self.__restore_func = restoreFunc

    def __call__(self):
        r"""
            ポインタの値を返す。value()と同義。
            
            Returns:
                float:
        """
        return self.value()

    def pointer(self):
        r"""
            登録されているポインタオブジェクトを返す。
            
            Returns:
                ptr:
        """
        return self.__pointer

    def value(self):
        r"""
            ポインタの値を返す。
            
            Returns:
                float:
        """
        return self.__restore_func(self.__pointer)

def getMDouble():
    r"""
        ダブル型のポインタを返す。
        
        Returns:
            MPointor:
    """
    scriptutil = OpenMaya.MScriptUtil()
    scriptutil.createFromDouble(0)
    ptr = scriptutil.asDoublePtr()
    return MPointor(ptr, scriptutil.getDouble)
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////

# /////////////////////////////////////////////////////////////////////////////
# 行列に関する関数等。                                                       //
# /////////////////////////////////////////////////////////////////////////////
def toDegree(eular):
    r"""
        オイラーをディグリー角に変換する。
        
        Args:
            eular (float):
            
        Returns:
            float:
    """
    return mathlib.math.degrees(eular)
        
def identityMatrix():
    r"""
        単位行列のリストを返す。
        
        Returns:
            list:
    """
    return [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]

MMatrix = OpenMaya2.MMatrix
MTransformationMatrix = OpenMaya2.MTransformationMatrix
MVector = OpenMaya2.MVector
MSpace = OpenMaya2.MSpace
MQuaternion = OpenMaya2.MQuaternion

def multiplyMatrix(matrixList, asList=True):
    r"""
        行列の掛け算を行う。
        引数matrixListには乗算対象となる行列を表すリストのリストを渡す。
        与えられた行列は頭から順に乗算されていく。
        asListがFalseの場合は乗算結果をMMatrixとして返す。
        
        Args:
            matrixList (list):行列を表すリストを持つlist
            asList (bool):戻り値をリストとして返すかどうか。
    """
    matrices = [MMatrix(x) for x in matrixList]
    r = matrices[0]
    for i in range(1, len(matrices)):
        r *= matrices[i]
    if asList:
        r = [x for x in r]
    return r

def pointMatrixMult(position, matrixList):
    r"""
        引数position(3つのfloatを持つリスト)とmatrixListの乗算した結果を返す。
        戻り値は3つのfloatを持つlist
        
        Args:
            position (list):[float, float, float]
            matrixList (list):行列を持つlist
            
        Returns:
            list:[float, float, float]
    """
    mtx = identityMatrix()
    mtx[12:15] = position
    new_mtx = multiplyMatrix([mtx]+matrixList)
    return new_mtx[12:15]
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////


class DoCommand(object):
    r"""
        コンテキスト制御型のundo制御クラス。
    """
    def __init__(self, waitCursor=False):
        r"""
            Args:
                waitCursor (any):
        """
        self.__q_app = None
        if waitCursor:
            from . import uilib
            self.__q_app = [
                uilib.QtWidgets.QApplication,
                uilib.QtGui.QCursor(uilib.QtCore.Qt.WaitCursor)
            ]

    def __enter__(self):
        cmds.undoInfo(openChunk=True)
        if not self.__q_app:
            return
        self.__q_app[0].setOverrideCursor(self.__q_app[1])

    def __exit__(self, exc_type, exc_value, traceback):
        r"""
            Args:
                exc_type (any):
                exc_value (any):
                traceback (any):
                
            Returns:
                bool:
        """
        cmds.undoInfo(closeChunk=True)
        if self.__q_app:
            self.__q_app[0].restoreOverrideCursor()
        return False


class FreezedShapeEditor(object):
    r"""
        withコンテキスト制御型クラス。
        与えられた引数がAbstractEditableShapeのサブクラスの場合に有効。
        with文内ではインスタンス作成時に渡されたオブジェクトがフリーズされた
        状態のものが渡されるため、正確なバウンディングボックスの計算や
        最近接点や法線の取得などが可能になる。
    """
    def __init__(self, node):
        r"""
            Args:
                node (str or AbstractNode):操作対象となる元ノード。
        """
        n = asObject(node)
        if n.isType('transform'):
            shapes = n.shapes(ni=True)
            if not shapes:
                raise ValueError(
                    'The given node "%s" has no editable shape.' % node
                )
            shape = shapes[0]
        else:
            shape = n
        if not isinstance(shape, AbstractEditableShape):
            raise ValueError(
                'The given node "%s" is not editable shape.' % node
            )
        self.__shape = shape
        self.__freezed = None

    def __enter__(self):
        self.__freezed = self.__shape.createFreezedShape()
        return self.__freezed[-1]

    def __exit__(self, exc_type, exc_value, traceback):
        r"""
            Args:
                exc_type (any):
                exc_value (any):
                traceback (any):
                
            Returns:
                bool:
        """
        if self.__freezed:
            self.__freezed[0].delete()
        return False
editFreezedShape = FreezedShapeEditor


class AbstractNodeStr(str):
    r"""
        Mayaのノード/アトリビュートの情報を持つ文字列を拡張した拡張クラス。
        cmds:に渡せば通常通りだが、このクラスの派生オブジェクト間
        でやりとりするとAPIの機能も使用できる。
    """
    def name(self):
        r"""
            上書き名を返すメソッド。
            継承するクラスは必ずここをカスタマイズし、文字列を返すこと。
            
            Returns:
                str:
        """
        return self

    def __call__(self):
        r"""
            名前を返す。name()と同義。
            
            Returns:
                str:
        """
        return self.name()

    def __repr__(self):
        r"""
            Returns:
                str:
        """
        return "<%s '%s'>" % (self.__class__.__name__, self.name())

    def __str__(self):
        r"""
            Returns:
                str:
        """
        return self.name()

    def __unicode__(self):
        r"""
            Returns:
                str:
        """
        return verutil.String(self.name())

    def __eq__(self, other):
        r"""
            Args:
                other (any):
                
            Returns:
                bool:
        """
        return self.name() == other

    def __ne__(self, other):
        r"""
            Args:
                other (any):
                
            Returns:
                bool:
        """
        return self.name() != other

    def __hash__(self):
        r"""
            Returns:
                hash:
        """
        return self.name().__hash__()

    def __len__(self):
        r"""
            Returns:
                int:
        """
        return self.name().__len__()

    def __add__(self, other):
        r"""
            Args:
                other (str):
                
            Returns:
                str:
        """
        return self.name() + other

    def __radd__(self, other):
        r"""
            Args:
                other (str):
                
            Returns:
                str:
        """
        return other + self.name()

    def __getitem__(self, key):
        r"""
            スライスのオーバーライド。
            
            Args:
                key (slice):
                
            Returns:
                str:
        """
        return self.name()[key]

    def __contains__(self, item):
        r"""
            in判定のオーバーライド。
            
            Args:
                item (any):
                
            Returns:
                bool:
        """
        return self.name().__contains__(item)

    def find(self, key):
        r"""
            findのオーバーライド。
            
            Args:
                key (str):
                
            Returns:
                int:
        """
        return self.name().find(key)

    def replace(self, old, new, count=-1):
        r"""
            replaceメソッドのオーバーライド。name()の戻り値に対して行う。
            
            Args:
                old (str):
                new (str):
                count (int):
                
            Returns:
                str:
        """
        return self.name().replace(old, new, count)

    def split(self, sep=None, maxsplit=-1):
        r"""
            splitのオーバーライド。name()の戻り値に対してsplitを行う。
            
            Args:
                sep (str):分割文字
                maxsplit (int):最大分割数
                
            Returns:
                str:
        """
        return self.name().split(sep, maxsplit)

    def rsplit(self, sep=None, maxsplit=-1):
        r"""
            rsplitのオーバーライド。name()の戻り値に対してsplitを行う。
            
            Args:
                sep (str):分割文字
                maxsplit (int):最大分割数
                
            Returns:
                str:
        """
        return self.name().rsplit(sep, maxsplit)

    def startswith(self, key):
        r"""
            与えれた文字列がこの名前の先頭にマッチするかどうか
            
            Args:
                key (str):
                
            Returns:
                bool:
        """
        return self.name().startswith(key)

    def endswith(self, key):
        r"""
            与えれた文字列がこの名前の末尾にマッチするかどうか
            
            Args:
                key (str):
                
            Returns:
                bool:
        """
        return self.name().endswith(key)


class ChildAttributes(AbstractNodeStr):
    r"""
        複数のアトリビュートのリストをまとめて取り扱うクラス。
        子アトリビュートを持つアトリビュートに対して使用する。
    """
    def __new__(cls, parentAttr):
        r"""
            初期化関数。
            
            Args:
                parentAttr (Attribute):親アトリビュートオブジェクト。
                
            Returns:
                ChildAttributes:
        """
        if isinstance(parentAttr, ChildAttributes):
            return parentAttr

        plug = parentAttr._plug()
        if not plug.isCompound():
            return
        num = plug.numChildren()
        if num == 0:
            return

        obj = super(ChildAttributes, cls).__new__(cls, parentAttr())
        obj.__parentattr = parentAttr
        obj.__child_attrs = [Attribute(plug.child(x)) for x in range(num)]
        return obj

    def __call__(self, attrName=None):
        r"""
            コールメソッドのオーバーライド。
            
            Args:
                attrName (str):
                
            Returns:
                any:
        """
        if not attrName:
            return super(ChildAttributes, self).__call__()
        return self.findAttrFromText(attrName)

    def name(self):
        r"""
            親アトリビュート名を返す。
            
            Returns:
                str:
        """
        return self.__parentattr.name()

    def __getitem__(self, key):
        r"""
            任意のインデックス（またはスライス）のアトリビュートを返す
            
            Args:
                key (int):
                
            Returns:
                list:
        """
        return self.__child_attrs[key]

    def __repr__(self):
        r"""
            オブジェクトの正式名を返す。
            
            Returns:
                str:
        """
        return "<%s : Contains %s attributes>" % (
            self.__class__.__name__, len(self)
        )

    def __iter__(self):
        return self.__child_attrs.__iter__()

    def __len__(self):
        r"""
            アトリビュートの数を返す
            
            Returns:
                int:
        """
        return self.__child_attrs.__len__()

    def set(self, *values, **keywords):
        r"""
            値を一度にセットするメソッド。
            
            Args:
                *values (tuple):
                **keywords (dict):setAttrと同じ
        """
        for attr, value in zip(self.__child_attrs, values):
            attr.set(value, **keywords)

    def get(self):
        r"""
            値を一度にまとめて返すメソッド。
            
            Returns:
                list:
        """
        return [x.get() for x in self.__child_attrs]

    def __rshift__(self, others):
        r"""
            rshiftのオーバーライド。自身のアトリビュートたちを相手側の
            アトリビュートのリストへインデックス順に接続する。
            
            Args:
                others (list):
        """
        for src, dst in zip(self.__child_attrs, others):
            src >> dst

    def __rrshift__(self, other):
        r"""
            rrshiftのオーバーライド。自身にアトリビュートが接続される。
            other:が単一アトリビュートの場合、そのアトリビュートからこのクラスが
            持つアトリビュートすべてに接続される。
            リストの場合は少ない数の方に合わせた分だけ接続される。
            
            Args:
                other (str or list):
        """
        if isinstance(other, (list, tuple, ChildAttributes)):
            for src, dst in zip(other, self.__child_attrs):
                src >> dst
        else:
            for attr in self.__child_attrs:
                other >> attr

    def disconnect(self, keepValue=False):
        r"""
            子アトリビュートのソース側からの接続をすべて外す。
            
            Args:
                keepValue (bool):接続解除後値を保持するかどうか
        """
        for attr in self.__child_attrs:
            attr.disconnect(keepValue)

    def findAttrFromText(self, text):
        r"""
            与えられたテキストに該当する名前のアトリビュートを返す
            
            Args:
                text (str):
                
            Returns:
                Attribute:
        """
        text = '.' + text
        for attr in self:
            if attr.attrName().endswith(text):
                return attr

class Attribute(AbstractNodeStr):
    r"""
        アトリビュートを取り扱うクラス。
        
        Inheritance:
            AbstractNodeStr:@date        2017/01/22 0:02[Eske](eske3g@gmail.com)
    """
    MFnAttributes = [
        OpenMaya.MFnUnitAttribute, OpenMaya.MFnNumericAttribute,
        OpenMaya.MFnEnumAttribute, OpenMaya.MFnMatrixAttribute,
        OpenMaya.MFnTypedAttribute, OpenMaya.MFnCompoundAttribute,
        OpenMaya.MFnAttribute,
    ]
    def __new__(cls, attr, node=None):
        r"""
            初期化を行う。
            引数nodeはattrがAttributeクラスかOpenMaya.MPlugのインスタンスの
            場合のみNoneを指定可能。
            
            Args:
                attr (str or OpenMaya.MPlug):
                node (AbstractNode or None):
                
            Returns:
                Attribute:
        """
        if isinstance(attr, Attribute):
            return attr

        if isinstance(attr, OpenMaya.MPlug):
            # MPlugが渡された場合はMPlugをそのまま利用する。
            obj = super(Attribute, cls).__new__(cls, attr.name())
            obj.__plug = attr
            node = None
        else:
            obj = super(Attribute, cls).__new__(cls, node+'.'+attr)
            try:
                obj.__plug = node._node().findPlug(attr)
            except:
                # Aliasアトリビュート用の処理
                aliaslist = []
                n = node._node()
                n.getAliasList(aliaslist)
                if attr in aliaslist:
                    index = aliaslist.index(attr) - 1
                    obj.__plug = n.findPlug(aliaslist[index])
                else:
                    raise ValueError(
                        '%s : Failed to find attribute : %s' % (
                            cls.__name__, attr
                        )
                    )
        obj.__node = node
        obj.__mfnattr = None
        obj.__is_locked = False
        return obj

    def _plug(self):
        r"""
            データ提供元となっているMPlugオブジェクトを返す。
            
            Returns:
                OpenMaya.MPlug:
        """
        return self.__plug

    def _mfnAttr(self):
        r"""
            MFnAttributeオブジェクトを返すメソッド。
            
            Returns:
                OpenMaya.MFnAttribute:
        """
        if self.__mfnattr:
            return self.__mfnattr
        obj = self.__plug.attribute()
        for mfnattr in self.MFnAttributes:
            try:
                m = mfnattr(obj)
            except:
                continue
            self.__mfnattr = m
            return self.__mfnattr

    def __enter__(self):
        r"""
            with文用。アトリビュートのロックが解除される
            
            Returns:
                self:
        """
        self.__is_locked = self.isLocked()
        self.setLock(False)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        r"""
            with文終了後、アトリビュートのロック状態が復元される。
            
            Args:
                exc_type (any):
                exc_value (any):
                traceback (any):
                
            Returns:
                bool:
        """
        if self.__is_locked:
            self.setLock(self.__is_locked)
        return False

    def node(self):
        r"""
            ノードオブジェクトを返す。
            
            Returns:
                AbstractNode:
        """
        if not self.__node:
            self.__node = AbstractNode(self._plug().node())
        return self.__node

    def nodeName(self):
        r"""
            このアトリビュートが属するノード名を返すメソッド。
            
            Returns:
                str:
        """
        return self.node().name()

    def name(self):
        r"""
            ノード名＋アトリビュート名を返すメソッド。
            
            Returns:
                str:
        """
        return self.nodeName() + '.' + self.attrName()

    def attrName(self, isLongName=True):
        r"""
            アトリビュート名のみを返すメソッド。
            
            Args:
                isLongName (bool):Falseの場合、ショートネームを返す。
                
            Returns:
                str:
        """
        return self._plug().partialName(
            False, False, False, False, False, isLongName
        )

    def aliasName(self):
        r"""
            エイリアス名を返すメソッド。
            
            Returns:
                str:
        """
        return self._plug().partialName(
            False, False, False, True, False, True
        )

    def setAlias(self, aliasName):
        r"""
            エイリアス名をセットするメソッド。
            
            Args:
                aliasName (str):セットするエイリアス名。
        """
        cmds.aliasAttr(aliasName, self.name())

    def type(self):
        r"""
            アトリビュートのタイプを返す。
            
            Returns:
                str:
        """
        return cmds.getAttr(self(), type=True)

    def __rshift__(self, other):
        r"""
            >>演算子サポート。other側のアトリビュートへコネクトする。
            
            Args:
                other (Attribute or str):コネクトされる側のアトリビュート名
        """
        if isinstance(other, (ChildAttributes, list, tuple)):
            for attr in other:
                self.connect(attr, True)
        else:
            self.connect(other, True)

    def __rrshift__(self, other):
        r"""
            >>演算子サポート。自身に接続される場合に呼ばれる。
            
            Args:
                other (Attribute or str):コネクトする側のアトリビュート名。
        """
        cmds.connectAttr(verutil.String(other), self.name(), f=True)

    def connect(self, dstAttr, f=False):
        r"""
            このアトリビュートからdstAttrへ接続する。
            
            Args:
                dstAttr (str):接続対象となるアトリビュート名
                f (bool):強制的に接続するかどうか
        """
        cmds.connectAttr(self.name(), verutil.String(dstAttr), f=f)

    def setLock(self, state):
        r"""
            このアトリビュートをロックする。
            
            Args:
                state (bool):
        """
        cmds.setAttr(self.name(), l=bool(state))

    def isLocked(self):
        r"""
            ロックされているかどうかを返す。
            
            Returns:
                bool:
        """
        return self._plug().isLocked()

    def setKeyable(self, state):
        r"""
            keyableにする。
            
            Args:
                state (bool):
        """
        cmds.setAttr(self.name(), k=bool(state))

    def isKeyable(self):
        r"""
            keyableかどうかを返す。
            
            Returns:
                bool:
        """
        return self._plug().isKeyable()

    def setChannelBox(self, state):
        r"""
            ChannelBox表示にする。
            
            Args:
                state (bool):
        """
        if self.isKeyable():
            return
        cmds.setAttr(self.name(), cb=bool(state))

    def isChannelBox(self):
        r"""
            ChannelBox表示になっているかどうかを返す。
            
            Returns:
                bool:
        """
        return self._plug().isChannelBoxFlagSet()

    def min(self):
        r"""
            Numeric型の最小値を返すメソッド。
            
            Returns:
                float:
        """
        mfnattr = self._mfnAttr()
        if not isinstance(mfnattr, OpenMaya.MFnNumericAttribute):
            return None
        if not mfnattr.hasMin():
            return None

        d = getMDouble()
        mfnattr.getMin(d.pointer())
        return d()

    def max(self):
        r"""
            Numeric型の最大値を返すメソッド。
            
            Returns:
                float:
        """
        mfnattr = self._mfnAttr()
        if not isinstance(mfnattr, OpenMaya.MFnNumericAttribute):
            return None
        if not mfnattr.hasMax():
            return None
        d = getMDouble()
        mfnattr.getMax(d.pointer())
        return d()

    def set(self, *value, **keywords):
        r"""
            値をセットするメソッド。
            引数はsetAttrと同じ。
            
            Args:
                *value (any):
                **keywords (dict):
        """
        attr = self.name()
        try:
            cmds.setAttr(attr, *value, **keywords)
        except Exception as e:
            cmds.setAttr(attr, *value, type=cmds.getAttr(attr, type=True))

    def get(self):
        r"""
            値を返すメソッド。
            
            Returns:
                any:
        """
        return cmds.getAttr(self.name())

    def isArray(self):
        r"""
            このアトリビュートが配列かどうか
            
            Returns:
                bool:
        """
        return self._plug().isArray()

    def elementAt(self, index):
        r"""
            このアトリビュートが配列の場合、任意のインデックスのAttribute
            オブジェクトを返す。
            該当しな場合はエラーを返す。
            
            Args:
                index (int):
                
            Returns:
                Attribute:
        """
        if not self.isArray():
            raise ValueError('The attribute "%s" is not array type.' % self)
        plug = self._plug()
        if index < 0:
            index = plug.numElements() + index
            index = 0 if index < 0 else index

        return Attribute(plug.elementByLogicalIndex(index))

    def numElements(self):
        r"""
            このアトリビュートが配列の場合、その要素数を返すメソッド。
            
            Returns:
                int:
        """
        return self._plug().numElements()

    def nextElement(self):
        r"""
            このアトリビュートが配列の場合、最後の配列＋１のエレメントを返す。
            
            Returns:
                Attribute:
        """
        return self.elementAt(self._plug().numElements() + 1)

    def listArray(self):
        r"""
            マルチアトリビュートの場合の配列を返すメソッド。
            
            Returns:
                list:
        """
        plug = self._plug()
        return  [
            Attribute(plug.elementByLogicalIndex(x))
            for x in range(plug.numElements())
        ]

    def index(self):
        r"""
            リストのエレメントの場合、そのインデックスを返す。
            エレメントではない場合はNoneを返す。
            
            Returns:
                int:
        """
        plug = self._plug()
        if plug.isElement():
            return plug.logicalIndex()
    
    def children(self):
        r"""
            子アトリビュートがある場合、そのChildAttributesを返す。
            
            Returns:
                ChildAttributes:
        """
        return ChildAttributes(self)

    def __invert__(self):
        r"""
            マルチアトリビュートの場合はアトリビュートのリストを、
            子アトリビュートがある場合、そのChildAttributeを返す。
            listArray:, childrenメソッドのシュガーシンタックス。
            
            Returns:
                ChildAttributes:
        """
        if self.isArray():
            return self.listArray()
        return self.children()

    def storeState(self):
        r"""
            アトリビュートの状態（keyable・lock・channelBox）を返す。
            このメソッドを実行すると、ロック状態が解除される。
            戻り値の辞書データをrestoreStateへ渡すと元の状態に戻る。
            
            Returns:
                dict:
        """
        attr = self.name()
        data = {
            'keyable' : self.isKeyable(),
            'lock' : self.isLocked(),
            'channelBox' : self.isChannelBox()
        }
        if data['lock']:
            self.setLock(False)
        return data

    def restoreState(self, state):
        r"""
            state情報を保持したDictを受け取って、その状態に復元する。
            
            Args:
                state (dict):アトリビュートの状態を保持した辞書
        """
        cmds.setAttr(self.name(), **state)

    def isSrc(self):
        r"""
            このアトリビュートがコネクションのソースとなっているかどうか
            
            Returns:
                bool:
        """
        return self._plug().isSource()

    def isDst(self):
        r"""
            このアトリビュートがコネクションのデスティネーションとなっているか
            どうか
            
            Returns:
                bool:
        """
        return self._plug().isDestination()

    def isConnected(self, srcAttr=None):
        r"""
            このアトリビュートに何かが接続されているかどうか。
            srcAttrに指定されている場合は、そのアトリビュートととの接続が
            あるかどうかを調べる。
            
            Args:
                srcAttr (str):ソースのアトリビュート名
                
            Returns:
                bool:
        """
        if not srcAttr:
            return self._plug().isConnected()
        return cmds.isConnected(srcAttr, self.name())

    def isConnecting(self, dstAttr):
        r"""
            このアトリビュート引数dstAttrに繋がっているかどうかを返す。
            
            Args:
                dstAttr (str):
                
            Returns:
                bool:
        """
        return cmds.isConnected(self.name(), dstAttr)

    def source(self, **keywords):
        r"""
            ソースオブジェクトを返すメソッド。
            引数はlistConnectionsと同じ。
            
            Args:
                **keywords (dict):
                
            Returns:
                AbstractNode:
        """
        if not self.isDst():
            return
        sources = cmds.listConnections(
            self.name(), s=True, d=False, **keywords
        )
        if not sources:
            return
        if 'p' in keywords or 'plug' in keywords:
            return asAttr(sources[0])
        else:
            return asObject(sources[0])

    def sources(self, **keywords):
        r"""
            このアトリビュートがマルチアトリビュートの場合、ソースオブジェクト
            をリストで返す。
            マルチではない場合はsourceが呼ばれるが、必ずリストで返ってくる点が
            sourceメソッドとの違い。
            引数はlistConnectionsと同じ。
            
            Args:
                **keywords (dict):
                
            Returns:
                list:
        """
        if not self.isArray():
            return [self.source(**keywords)]
        sources = cmds.listConnections(
            self.name(), s=True, d=False, **keywords
        )
        if not sources:
            return []
        if 'p' in keywords or 'plugs' in keywords:
            return toAttrs(sources)
        else:
            return toObjects(sources)

    def destinations(self, **keywords):
        r"""
            デスティネーションのオブジェクトリストを返すメソッド。
            引数はlistConnectionsと同じ。
            
            Args:
                **keywords (dict):
                
            Returns:
                AbstractNode:
        """
        if not self.isSrc():
            return []
        
        sources = cmds.listConnections(
            self.name(), s=False, d=True, **keywords
        )
        if not sources:
            return []
        if 'p' in keywords or 'plugs' in keywords:
            return toAttrs(sources)
        else:
            return toObjects(sources)

    def disconnect(self, keepValue=False):
        r"""
            このアトリビュートに接続されているアトリビュートを解除する。
            keepValueがTrueの場合、接続時の値を保持する。
            アトリビュートが配列の場合でkeepValueがFalseの場合、その番号
            のアトリビュートは消去される。
            
            Args:
                keepValue (bool):
        """
        plug = self._plug()
        # attrobj = OpenMaya.MFnAttribute(plug.attribute())
        attrobj = self._mfnAttr()
        plugs = cmds.listConnections(
            plug.name(), s=True, d=False, p=True, c=True
        )
        if not plugs:
            return

        behavior = None
        if keepValue:
            behavior = attrobj.disconnectBehavior()
            attrobj.setDisconnectBehavior(OpenMaya.MFnAttribute.kNothing)
        elif plug.isArray():
            behavior = attrobj.disconnectBehavior()
            attrobj.setDisconnectBehavior(OpenMaya.MFnAttribute.kDelete)

        for i in range(0, len(plugs), 2):
            cmds.disconnectAttr(plugs[i+1], plugs[i])

        if behavior is not None:
            attrobj.setDisconnectBehavior(behavior)


class AbstractNode(AbstractNodeStr):
    r"""
        すべてのMayaノードを操作するための機能を提供する抽象クラス。
    """
    InvalidNamePtn = re.compile('^\d|[^\w]+')
    def __new__(cls, nodeName):
        r"""
            初期化。
            
            Args:
                nodeName (str or MObject or AbstractNode):
                
            Returns:
                AbstractNode:
        """
        if isinstance(nodeName, AbstractNode):
            # AbstractNodeクラスの派生だった場合は、そのまま返す。
            return nodeName

        if isinstance(nodeName, OpenMaya.MObject):
            # MObjectが渡された場合は、直接変換を試みる。
            obj = super(AbstractNode, cls).__new__(cls, nodeName)
            try:
                nodefn = obj.dagNodeFn()()
                nodefn.setObject(nodeName)
                obj.__node = nodefn
                
                # メソッドのオーバーライド
                obj.name = obj.__node.partialPathName
            except Exception as e:
                try:
                    obj.__node = obj.nodeFn()(nodeName)
                except Exception as e:
                    obj.__node = OpenMaya.MFnDependencyNode(nodeName)
                # メソッドのオーバーライド
                obj.name = obj.__node.name
            return obj

        # 渡された値が文字列の場合。
        if nodeName.find('.') > -1:
            # 引数がアトリビュート名付きの場合は、そのまま文字列として返す。
            return nodeName
    
        obj = super(AbstractNode, cls).__new__(cls, nodeName)

        mobject = OpenMaya.MObject()
        dagpath = OpenMaya.MDagPath()
        mslist = OpenMaya.MSelectionList()
        mslist.add(nodeName)
        try:
            mslist.getDagPath(0, dagpath, mobject)
            nodefn = obj.dagNodeFn()()
            nodefn.setObject(dagpath)
            obj.__node = nodefn

            # メソッドのオーバーライド
            obj.name = obj.__node.partialPathName
        except Exception as e:
            mslist.getDependNode(0, mobject)
            try:
                obj.__node = obj.nodeFn()(mobject)
            except Exception as e:
                obj.__node = OpenMaya.MFnDependencyNode(mobject)
            
            # メソッドのオーバーライド
            obj.name = obj.__node.name
        return obj

    def dagNodeFn(self):
        r"""
            初期化に使用するDAG用のノード編集用のクラスを返す。
            場合によっては上書きして使用する。
            
            Returns:
                OpenMaya.MFnDagNode:
        """
        return OpenMaya.MFnDagNode

    def nodeFn(self):
        r"""
            初期化に使用するDG用のノード編集用のクラスを返す。
            場合によっては上書きして使用する。
            dagNodeFnよりも優先度は低く、dagNodeFnで失敗した場合にこちらが
            使用される。
            
            Returns:
                OpenMaya.MFnDependencyNode:
        """
        return OpenMaya.MFnDependencyNode

    def _node(self):
        r"""
            このノードのMfnオブジェクト。
            
            Returns:
                OpenMaya.MFnDependencyNode:
        """
        return self.__node

    def shortName(self):
        r"""
            ショートネームを返す。
            
            Returns:
                str:
        """
        return self().split('|')[-1]

    def isDag(self):
        r"""
            このノードがDAGノードかどうかを返す。
            
            Returns:
                bool:
        """
        return isinstance(self.__node, OpenMaya.MFnDagNode)

    def rename(self, newName):
        r"""
            名前を変更するメソッド。
            
            Args:
                newName (str):新しい名前
                
            Returns:
                self:
        """
        if newName.endswith('#'):
            newName = newName[:-1]
            suffix = '#'
        else:
            suffix = ''
        newName = self.InvalidNamePtn.sub('_', newName)
        cmds.rename(self.name(), newName+suffix)
        return self

    def __call__(self, attr=None, value=None, **keywords):
        r"""
            指定したアトリビュートを参照、編集できるコールメソッド
            のオーバーライド。
            attr:を指定すると、そのアトリビュートの値が帰る。
            attr:とvalueを指定すると、そのアトリビュートにvalueをセット出来る。
            また、セットする際、**keywordsを引数として使用可能。
            
            Args:
                attr (str):アトリビュート名。
                value (str):セットする値。
                **keywords (dict):setAttrの引数と同じ
                
            Returns:
                any:attrのみ指定した場合はその値を返す。
        """
        if attr is None:
            # 何も指定しない場合は名前を返す。
            return self.name()
    
        node_attr = self.name() + '.' + attr
        if value is None:
            # attrのみ指定している場合は、アトリビュートの値を返す。
            return cmds.getAttr(node_attr, **keywords)

        # それ以外の場合はアトリビュートに値をセットする。=====================
        # その際、アトリビュートがロックされていた場合は、ロックを解除する。
        islocked = cmds.getAttr(node_attr, l=True)
        if islocked:
            cmds.setAttr(node_attr, l=False)
        if isinstance(value, (list, tuple)):
            cmds.setAttr(node_attr, *value, **keywords)
        else:
            cmds.setAttr(node_attr, value, **keywords)
        if islocked:
            cmds.setAttr(node_attr, l=True)
        # +====================================================================

    def __nonzero__(self):
        r"""
            真偽テストの上書きメソッド。
            真偽判定基準がノードが存在するかどうかに変更している。
            
            Returns:
                bool:
        """
        return self.exists()

    def __div__(self, attributeName):
        r"""
            アトリビュート名付きの文字列を返す(Python2用)
            
            Args:
                attributeName (str):アトリビュート名
                
            Returns:
                str:
        """
        return self.name() + '.' + attributeName

    def __truediv__(self, attributeName):
        r"""
            アトリビュート名付きの文字列を返す(Python3用)
            
            Args:
                attributeName (str):アトリビュート名
                
            Returns:
                str:
        """
        return self.__div__(attributeName)

    def addAttr(self, attrName, attrType, k=True, cb=True, **keywords):
        r"""
            アトリビュートを追加する。
            
            Args:
                attrName (any):[str]追加するアトリビュート名
                attrType (any):[str]追加するアトリビュートのタイプ
                k (True):[bool]keyableかどうか
                cb (True):[bool]ChannelBoxに表示するどうか
                **keywords (dict):addAttrの引数と同じ
                
            Returns:
                any:
                
            Brief:
                基本的にはadd～Attrを使用するため、ほぼ内部仕様専用。
        """
        cmds.addAttr(self(), ln=attrName, at=attrType, **keywords)
        attr = self.attr(attrName)
        
        if cb:
            k = False
        attr.setKeyable(k)
        if not k:
            attr.setChannelBox(cb)
        return attr

    def addFloatAttr(
        self, attrName, min=0, max=1, default=0, k=True, cb=False, **keywords
    ):
        r"""
            Double型のアトリビュートを追加するメソッド。
            
            Args:
                attrName (any):アトリビュート名
                min (float):最小値
                max (float):最大値
                default (float):初期値
                k (bool):Keyableかどうか
                cb (bool):チャンネルボックスに表示するかどうか
                **keywords (dict):addAttrの引数と同じ
                
            Returns:
                Attribute:
        """
        if min is not None:
            keywords['min'] = min
        if max is not None:
            keywords['max'] = max

        return self.addAttr(attrName, 'double', k, cb, dv=default, **keywords)

    def addIntAttr(
        self, attrName, min=0, max=1, default=0, k=True, cb=False, **keywords
    ):
        r"""
            Double型のアトリビュートを追加するメソッド。
            
            Args:
                attrName (str):アトリビュート名
                min (float):最小値
                max (float):最大値
                default (float):初期値
                k (bool):Keyableかどうか
                cb (bool):チャンネルボックスに表示するかどうか
                **keywords (dict):addAttrの引数と同じ
                
            Returns:
                Attribute:
        """
        if min is not None:
            keywords['min'] = min
        if max is not None:
            keywords['max'] = max

        return self.addAttr(attrName, 'long', k, cb, dv=default, **keywords)

    def addAngleAttr(
        self, attrName, default=0, k=True, cb=False, **keywords
    ):
        r"""
            Args:
                attrName (str):アトリビュート名
                default (float):初期値
                k (bool):Keyableかどうか
                cb (bool):チャンネルボックスに表示するかどうか
                **keywords (dict):addAttrの引数と同じ
        """
        return self.addAttr(
            attrName, 'doubleAngle', k, cb, dv=default, **keywords
        )


    def addMatrixAttr(self, attrName, default=None, **keywords):
        r"""
            matrix型アトリビュートを追加する。
            
            Args:
                attrName (str):アトリビュート名
                default (list):デフォルトとなる16個のfloatを持つlist
                **keywords (dict):addAttrの引数と同じ
                
            Returns:
                Attribute:
        """
        cmds.addAttr(self(), ln=attrName, dt='matrix', **keywords)
        attr = self.attr(attrName)
        if default:
            self(attr, default, type='matrix')
        return attr

    def addBoolAttr(
        self, attrName, default=True, k=True, cb=False, **keywords
    ):
        r"""
            bool型のアトリビュートを追加する。
            
            Args:
                attrName (str):アトリビュート名
                default (bool):デフォルト値
                k (bool):Keyableかどうか
                cb (bool):チャンネルボックスに表示するかどうか
                **keywords (dict):addAttrの引数と同じ
                
            Returns:
                Attribute:
        """
        return self.addAttr(attrName, 'bool', k, cb, dv=default, **keywords)

    def addDisplayAttr(
        self, attrName='display', default=True, k=False, cb=True
    ):
        r"""
            表示・非常時のアトリビュートを追加するメソッド。
            
            Args:
                attrName (str):アトリビュート名
                default (bool):初期値（Trueでshow）
                k (bool):Keyableかどうか
                cb (bool):チャンネルボックスに表示するかどうか
                
            Returns:
                Attribute:
        """
        attr = self.addAttr(
            attrName, 'enum', k=k, cb=cb, en='hide:show'
        )
        attr.set(default)
        return attr

    def addEnumAttr(
        self, attrName, items, default=0, k=True, cb=False, **keywords
    ):
        r"""
            列挙型のアトリビュートを追加する。
            
            Args:
                attrName (str):アトリビュート名
                items (list):列挙する項目名のリスト
                default (int):初期値
                k (bool):Keyableかどうか
                cb (bool):チャンネルボックスに表示するかどうか
                **keywords (dict):addAttrの引数と同じ
                
            Returns:
                Attribute:
        """
        attr = self.addAttr(
            attrName, 'enum', en=':'.join(items), k=k, cb=cb, **keywords
        )
        attr.set(default)
        return attr

    def addMessageAttr(self, attrName, **keywords):
        r"""
            メッセージアトリビュートを追加する。
            
            Args:
                attrName (str):追加するアトリビュート名
                **keywords (dict):addAttrの引数と同じ
                
            Returns:
                Attribute:
        """
        return self.addAttr(attrName, 'message', k=False, cb=False, **keywords)

    def addStringAttr(self, attrName, default=None, l=False, **keywords):
        r"""
            文字列型アトリビュートを追加する。
            
            Args:
                attrName (str):追加するアトリビュート名
                default (str):初期値
                l (bool):ロックするかどうか
                **keywords (dict):addAttrの引数と同じ
                
            Returns:
                Attribute:
        """
        cmds.addAttr(self(), ln=attrName, dt='string', **keywords)
        attr = self.attr(attrName)
        if default:
            attr.set(default, type='string')
        if l:
            attr.setLock(True)
        return attr

    def listAttr(self, attr=None, **keywords):
        r"""
            保持するアトリビュートのリストを返すメソッド。
            引数にasStr=Trueを渡すとAttributeクラスではなく、アトリビュート名の
            文字列を持つリストを返す。
            
            Args:
                attr (str):
                **keywords (dict):
                
            Returns:
                list:[Attribute]
        """
        nodename = self()
        if 'asStr' in keywords:
            del keywords['asStr']
            attrs = cmds.listAttr(
                *([nodename] if attr is None else [nodename + '.' + attr]),
                **keywords
            )
            return attrs if attrs else []

        mult = keywords.pop('m', False)
        mult = keywords.pop('multi', mult)

        attrs = cmds.listAttr(
            *([nodename] if attr is None else [nodename + '.' + attr]),
            **keywords
        )
        if not attrs:
            return []

        attrlist = [self.attr(x) for x in attrs]
        if not mult:
            return attrlist
        result = []
        for at in attrlist:
            if at.isArray():
                result.extend(at.listArray())
            else:
                result.append(at)
        return result

    def attr(self, attr):
        r"""
            指定した名前のAtributeオブジェクトを返すメソッド。
            
            Args:
                attr (str):アトリビュート名。
                
            Returns:
                Attribute:
        """
        if not '.' in attr:
            result = index_reobj.search(attr)
            if not result:
                return Attribute(attr, self)
        components = attr.split('.')
        result = index_reobj.search(components[0])
        if not result:
            cur_attr = Attribute(components[0], self)
        else:
            cur_attr = Attribute(result.group(1), self).elementAt(
                int(result.group(2))
            )

        for c in components[1:]:
            cur_attr = cur_attr.children().findAttrFromText(c)
        return cur_attr

    def editAttr(self, attrlist, k=True, l=False, cb=False):
        r"""
            アトリビュートの状態を編集するメソッド。
            
            Args:
                attrlist (list):アトリビュートのリスト
                k (bool):Keyableにするかどうか
                l (bool):Lockするかどうか
                cb (bool):ChannelBoxに表示するかどうか
        """
        if not isinstance(attrlist, (list, tuple)):
            attrlist = [attrlist]
        for attr in attrlist:
            if attr.endswith(':a'):
                attrs = self.attr(attr[:-2])
                for at in attrs.children():
                    at.setKeyable(k)
                    at.setLock(l)
                    at.setChannelBox(cb)
                continue
            cmds.setAttr(self + '.' + attr, k=k, l=l, cb=cb)
    
    def deleteAttr(self, attr):
        r"""
            任意のダイナミックアトリビュートを削除する。
            削除に成功した場合はTrueを返す。
            
            Args:
                attr (str):
                
            Returns:
                bool:
        """
        try:
            cmds.deleteAttr(self(), at=attr)
            return True
        except:
            return False

    def hasAttr(self, attr):
        r"""
            任意のアトリビュートがあるかどうかを返すメソッド。
            
            Args:
                attr (str):
                
            Returns:
                bool:
        """
        return self.__node.hasAttribute(attr)

    def clearConnections(self, src=True, dst=True):
        r"""
            ノードに接続されているコネクションを全てはずす。
            
            Args:
                src (bool):入力側全てのコネクションをはずす。
                dst (bool):出力側全てのコネクションをはずす。
        """
        node_name = self()
        for flags, state in zip(((1, 0), (0, 1)), (src, dst)):
            connections = cmds.listConnections(
                node_name, s=flags[0], d=flags[1], c=True, p=True
            )
            if not connections:
                continue

            for i in range(0, len(connections), 2):
                cmds.disconnectAttr(
                    connections[i+flags[0]], connections[i+flags[1]]
                )

    def isShared(self):
        r"""
            sharedノードかどうかを返すメソッド。
            
            Returns:
                bool:
        """
        return self.__node.isShared()

    def isLocked(self):
        r"""
            ノードがロックされているかどうかを返す。。
            
            Returns:
                bool:
        """
        return self.__node.isLocked()

    def setLocked(self, isLocked):
        r"""
            Args:
                isLocked (any):
        """
        cmds.lockNode(self, l=isLocked)

    def exists(self):
        r"""
            ノードが存在するかどうかを返すメソッド。
            
            Returns:
                bool:
        """
        try:
            return cmds.objExists(self.name())
        except:
            return False

    def select(self, **keywords):
        r"""
            自身を選択する。
            
            Args:
                **keywords (dict):selectコマンドと同じ
                
            Returns:
                self:
        """
        cmds.select(self(), *keywords)
        return self

    def delete(self):
        r"""
            自身を削除する
        """
        cmds.delete(self.name())

    def deleteHistory(self):
        r"""
            自身のヒストリを削除する。
        """
        cmds.delete(self.name(), ch=True)

    def type(self):
        r"""
            ノードタイプを返すメソッド。
            
            Returns:
                str:
        """
        return self._node().typeName()

    def isType(self, types):
        r"""
            与えられた文字列のタイプかどうかを返すメソッド。
            
            Args:
                types (str or list or tuple):
                
            Returns:
                bool:
        """
        nodetype = self.type()
        if isinstance(types, (list, tuple)):
            return nodetype in types
        else:
            return nodetype == types
    
    def isSubType(self, type):
        r"""
            Args:
                type (str):
        """
        typelist = cmds.nodeType(self(), i=True)
        return type in typelist

    def namespace(self):
        r"""
            ネームスペースを返す。
            
            Returns:
                str:
        """
        return self._node().parentNamespace()

    def listConnections(self, plug=None, **keywords):
        r"""
            引数はlistConnectionsに使用するものと同じものが使える。
            
            Args:
                plug (str):捜査ノード名
                **keywords (dict):
                
            Returns:
                list:
        """
        node = self() if plug is None else self/plug
        result = cmds.listConnections(node, **keywords) or []
        if 'p' in keywords or 'plugs' in keywords:
            return toAttrs(result)
        else:
            return toObjects(result)

    def sources(self, plug=None, **keywords):
        r"""
            このノードのソース側のコネクションを返す。
            引数keywordsにはlistConnectionsに使用するものと同じものが使える。
            
            Args:
                plug (str):アトリビュート名（任意）
                **keywords (dict):
                
            Returns:
                list:
        """
        keywords['s'] = True
        keywords['d'] = False
        return self.listConnections(plug, **keywords)

    def destinations(self, plug=None, **keywords):
        r"""
            このノードのデスティネーション側のコネクションを返す。
            引数keywordsにはlistConnectionsに使用するものと同じものが使える。
            
            Args:
                plug (str):アトリビュート名（任意）
                **keywords (dict):
                
            Returns:
                list:
        """
        keywords['s'] = False
        keywords['d'] = True
        return self.listConnections(plug, **keywords)


class FourByFourMatrix(AbstractNode):
    r"""
        fourByFourMatrixノードを操作するためのクラス。
    """
    def setMatrix(self, matrix):
        r"""
            16個のFloatのリストで表される行列をセットする
            
            Args:
                matrix (list):[float x 16]
        """
        for i, j in [(x, y) for x in range(4) for y in range(4)]:
            self('in%s%s' % (i, j), matrix[4 * i + j])

    def matrix(self):
        r"""
            このノードの16個のアトリビュートの値をリストとして返す。
            
            Returns:
                list:[float x 16]
        """
        return [
            [self('in%s%s' % (x, y)) for x in range(4) for y in range(4)]
        ]


class BlendShape(AbstractNode):
    r"""
        blendShapeノードを操作するためのクラス。
    """
    def nodeFn(self):
        r"""
            MFnBlendShapeDeformer使用のためのオーバーライド用メソッド。
            
            Returns:
                OpenMayaAnim.MFnBlendShapeDeformer:
        """
        return OpenMayaAnim.MFnBlendShapeDeformer

    def attr(self, attrName):
        r"""
            ウェイトアトリビュートの要素も検索対象に拡大した
            Attributeオブジェクトを返す上書きメソッド。
            
            Args:
                attrName (str):
                
            Returns:
                Attribute:
        """
        try:
            return super(BlendShape, self).attr(attrName)
        except:
            index = self.indexFromText(attrName)
            if index is None:
                raise AttributeError('No attribute found : %s' % attrName)
            return self.attr('weight').elementAt(index)

    def indexFromText(self, text):
        r"""
            与えられたアトリビュート名に該当するウェイトのインデックス
            を返すメソッド。
            
            Args:
                text (str):
                
            Returns:
                int:
        """
        attrlist = self.listAttrNames()
        if text in attrlist:
            return attrlist.index(text)

    def setWeight(self, index, value):
        r"""
            ウェイトをセットするためのメソッド。
            
            Args:
                index (int):
                value (float):
        """
        if not isinstance(index, verutil.BaseString):
            self._node().setWeight(index, value)

        index = self.indexFromText(index)
        if index is not None:
            self._node().setWeight(index, value)

    def weight(self, index):
        r"""
            指定したインデックスのウェイトを返すメソッド。
            
            Args:
                index (int):
                
            Returns:
                float:
        """
        if not isinstance(index, verutil.BaseString):
            return self._node().weight(index)
        index = self.indexFromText(index)
        if index is not None:
            return self._node().weight(index)

    def listWeightAttr(self):
        r"""
            ウェイト用のアトリビュートのリストを返す
            
            Returns:
                Attribute:
        """
        return self.attr('weight').listArray()

    def listAttrNames(self):
        r"""
            ウェイトアトリビュートの要素のエイリアスをリストで返す
            
            Returns:
                list:
        """
        return [x.aliasName() for x in self.listWeightAttr()]

    def addInbetween(
        self, baseNode, targetList, name=None, o='local'
    ):
        r"""
            このblendShapeのウェイト要素の終末に新しくinbetweenタイプの
            ターゲットを追加するメソッド。
            
            Args:
                baseNode (str):
                targetList (list):
                name (str):
                o (str):
        """
        bs = self.name()
        last_index = self.attr('weight').numElements()
        num = len(targetList)
        cmds.blendShape(
            bs, e=True, o=o, t=(baseNode, last_index, targetList[-1], 1)
        )
        span = round(1.0 / num, 3)
        for i in range(num-1):
            cmds.blendShape(
                bs, e=True, ib=True,
                t=(baseNode, last_index, targetList[i], span * (i + 1))
            )

        if name:
            self.attr('w').elementAt(last_index).setAlias(name)

    def duplicateTargets(self, geo):
        r"""
            このBlendShapeのフェイシャルターゲットを全てコピーする。
            コピーする際にはgeoが使用され、全てのtargetアトリビュートを
            アクティブにしながらgeoをコピーしていく。
            geoとこのBlendShapeが無関係の場合はコピーされるgeoは
            なんの変化もないままtargetの数だけコピーされるだけなので注意。
            
            Args:
                geo (str):コピーするジオメトリ
                
            Returns:
                list:
        """
        attrs = self.listWeightAttr()
        created = []
        for attr in attrs:
            attr.set(0)
        for name, attr in zip(self.listAttrNames(), attrs):
            attr.set(1)
            new_nodes = duplicate(geo)
            attr.set(0)
            for new in new_nodes:
                new.rename(name)
                created.append(asObject(new()))
        return created

class SkinCluster(AbstractNode):
    r"""
        skinClusterの編集などを行う機能を提供するクラス。
    """
    InfluenceList, IndexWithInfluence, InfluenceWithIndex = range(3)
    def nodeFn(self):
        r"""
            MFnSkinCluster使用のためのオーバーライド用メソッド。
            
            Returns:
                OpenMayaAnim.MFnSkinCluster:
        """
        return OpenMayaAnim.MFnSkinCluster

    def _influences(self, returnAs=0):
        r"""
            接続されているインフルエンスを返す。
            influencesと違い文字列のリストで返すため１０倍ほど高速。
            returnAsが
                1の場合、インデックスをキーとしたインフルエンス、
                2の場合、インフルエンスをキーとしたインデックスの辞書を
            返す。
            
            Args:
                returnAs (int):
                
            Returns:
                dict:
        """
        if returnAs == 0:
            inf = cmds.listConnections(self/'matrix', s=True, d=False)
            return inf if inf else []
        else:
            infset = cmds.listConnections(
                self/'matrix', s=True, d=False, p=True, c=True
            )
            if not infset:
                return []
            index_pattern = re.compile('\[(\d+)\]')
            inflist = {}
            for i in range(0, len(infset), 2):
                index = int(index_pattern.search(infset[i]).group(1))
                inf = infset[i+1].split('.', 1)[0]
                if returnAs == self.IndexWithInfluence:
                    inflist[index] = inf
                else :
                    inflist[inf] = index
            return inflist

    def influences(self):
        r"""
            接続されているインフルエンスを返す。
            
            Returns:
                list:
        """
        inf = self._influences()
        return [asObject(x) for x in  inf]

    def bindFlags(self):
        flags = {
            x:self(y) for x, y in (
                ('mi', 'maxInfluences'), ('omi', 'maintainMaxInfluences'),
                ('nw', 'normalizeWeights'), ('sm', 'skinningMethod'),
                ('wd', 'weightDistribution'),
            )
        }
        flags['tsb'] = True
        return flags

    def rebind(self, objects, copyWeight=True):
        r"""
            このskinClusterに使用されているインフルエンスと設定を使用して
            objectsをバインドする。
            
            Args:
                objects (list):バインドされるオブジェクトのリスト
                copyWeight (bool):バインド後、ウェイトをコピーする
                
            Returns:
                list:作成されたskinクラスターのリスト
        """
        objects = objects if isinstance(objects, (list, tuple)) else [objects]
        influences = self._influences()
        results = []
        flags = self.bindFlags()
        for object in objects:
            sc = cmds.skinCluster(influences, object, **flags)[0]
            if copyWeight:
                cmds.copySkinWeights(
                    ss=self(), ds=sc,
                    nm=True, sa='closestPoint', ia='closestJoint'
                )
            results.append(sc)
        return [SkinCluster(x) for x in results]

    def addInfluences(self, influences):
        r"""
            インフルエンスを追加する。
            
            Args:
                influences (list):追加するインフルエンスの名前のリスト
        """
        orig_influences = self._influences()
        sc = self()
        for inf in [verutil.String(x) for x in influences]:
            if inf in orig_influences:
                continue
            cmds.skinCluster(sc, e=True, lw=True, wt=0, ai=inf)
            try:
                cmds.setAttr(inf+'.lockInfluenceWeights', 0)
            except:
                pass

    def removeInfluences(self, influences):
        r"""
            インフルエンスを削除する。
            
            Args:
                influences (list):削除するインフルエンスの名前のリスト
        """
        orig_influences = self._influences()
        sc = self()
        for inf in [verutil.String(x) for x in influences]:
            if not inf in orig_influences:
                continue
            cmds.skinCluster(sc, e=True, ri=inf)

    def resetInfluences(self, influences, isRefresh=True):
        r"""
            influencesの初期値を現在の位置でリセットする。
            
            Args:
                influences (list):インフルエンスのリスト
                isRefresh (bool):リセット後描画をリフレッシュする
        """
        orig_influences = self._influences(self.InfluenceWithIndex)
        for inf in toObjects(influences):
            if not inf in orig_influences:
                continue
            world_inv_mtx = inf('worldInverseMatrix')
            self(
                'bindPreMatrix[%s]' % orig_influences[inf], world_inv_mtx,
                type='matrix'
            )
        if isRefresh:
            cmds.dgdirty(a=True)

    def listWeights(self):
        r"""
            このスキンクラスターのウェイトリストを辞書で返す。
            戻り値はコンポーネントのインデックスをキーとした辞書オブジェクト。
            対応する値は
                コンポーネントに対応するアトリビュート名をキー、値をウェイト値
            とする辞書。
            
            Returns:
                dict:
        """
        weightlist = {}
        sc = self.name()
        index_ptn = re.compile('\[(\d+)\]')
        for attr in cmds.listAttr(self/'wl', m=True):
            index = index_ptn.search(attr)
            if not index:
                continue
            index = int(index.group(1))
            wlist = weightlist.setdefault(index, {})
            if not '.' in attr:
                continue
            w = cmds.getAttr(sc + '.' + attr)
            wlist[attr] = w
        return weightlist

    def fixBrokenLimitInfluence(
        self, limit=4, checkOnly=False, isSelecting=True, withWeightList=False
    ):
        r"""
            limit以上のインフルエンスがバインドされている頂点をlimit内に
            収まるように修正する。
            
            Args:
                limit (int):
                checkOnly (bool):チェックのみかどうか
                isSelecting (bool):修正された頂点を選択するかどうか
                withWeightList (bool):戻り値にウェイトのリストを含めるかどうか
                
            Returns:
                list or dict:
        """
        sc = self.name()
        mesh = self.attr('outputGeometry[0]').destinations(type='mesh')
        null_result = {} if withWeightList else []
        if not mesh:
            print('Warning : No mesh was found. : {}'.format(self))
            return null_result
        weightlist = self.listWeights()
        if not weightlist:
            return null_result
        # +====================================================================

        # 上限数以上のインフルエンスを持つウェイトリストを振り分ける。+========
        errored_list = {}
        for index, wlist in weightlist.items():
            if len(wlist) > limit:
                errored_list['{}.vtx[{}]'.format(mesh[0] , index)] = [
                    sc + '.' + x for x in wlist.keys()
                ]
        if not errored_list:
            return null_result
        # +====================================================================

        # チェックのみの場合はここで終了。
        e_list = list(errored_list.keys())
        if checkOnly:
            if isSelecting:
                cmds.select(e_list, r=True)
            return errored_list if withWeightList else e_list

        # +====================================================================
        for vtx, errored in errored_list.items():
            weightlist = {}
            # ウェイト値の高い順にアトリビュートを並べるための辞書を ----------
            # 作成する。

            for attr in errored:
                weight = cmds.getAttr(attr)
                if weight in weightlist:
                    weightlist[weight].append(attr)
                else:
                    weightlist[weight] = [attr]
            valuelist = list(weightlist.keys())
            valuelist.sort()
            valuelist.reverse()
            # ----------------------------------------------------------------

            # ウェイトの高い順にアトリビュートとその値を並列に並べる。--------
            weightattrs = []
            values = []
            for value in valuelist:
                for attr in weightlist[value]:
                    weightattrs.append(attr)
                    values.append(value)
            # ----------------------------------------------------------------

            # limitよりも多いアトリビュートの値を０にセットする。-------------
            for attr in weightattrs[limit:]:
                cmds.setAttr(attr, 0)
            weightattrs = weightattrs[:limit]
            values = values[:limit]
            # ----------------------------------------------------------------

            # 全体の合計が１になるように、残ったウェイトを調整する。----------
            ratio = 1.0 / sum(values)
            values = [x*ratio for x in values]
            n = 1.0 - sum(values)
            if n != 0:
                values[0] += n
            for attr, value in zip(weightattrs, values):
                cmds.setAttr(attr, value)
            # ----------------------------------------------------------------
        # +====================================================================

        self('maxInfluences', limit)
        if isSelecting:
            cmds.select(errored_list.keys(), r=True)
        return errored_list if withWeightList else e_list


class Controller(AbstractNode):
    r"""
        controllerノードの編集などを行うクラス
    """
    def object(self):
        r"""
            紐付けられているコントローラとして振る舞うノードを返す
            
            Returns:
                AbstractNode:
        """
        return self.attr('controllerObject').source()

    def parent(self):
        r"""
            親のcontrollerノードを返す。
            
            Returns:
                Controller:
        """
        parent = cmds.controller(self(), q=True, p=True)
        if parent:
            return Controller(parent)

    def addChild(self, *objects):
        r"""
            Args:
                *objects (tuple):
                
            Returns:
                list:
        """
        ctrls = [x for x in objects if getController(x)]
        if not ctrls:
            return []
        cmds.controller(ctrls, self.object(), p=True)
        return ctrls

    def index(self):
        r"""
            このコントローラが親コントローラの何番目の子かを返す。
            親がない場合は-1を返す。
            
            Returns:
                str:
        """
        return cmds.controller(self(), q=True, idx=True)

    def setAllowCycle(self, state):
        r"""
            兄弟間のピックアップウォークの循環を許可するかの設定する
            
            Args:
                state (bool):
        """
        self('cycleWalkSibling', bool(state))


class DagNode(AbstractNode):
    r"""
        DAGノードの基本となるベースクラス。
        階層を辿るための拡張機能が付いている。
    """
    def fullName(self):
        r"""
            ノードのフルパスの名前を返す。
            
            Returns:
                str:
        """
        return self._node().fullPathName()

    def isIntermediate(self):
        r"""
            自身がintermediateオブジェクトであるかどうか
            
            Returns:
                bool:
        """
        return self._node().isIntermediateObject()

    def isInstance(self):
        r"""
            自身がインスタンスかどうか
            
            Returns:
                bool:
        """
        return self._node().isInstanced()

    def removeIntermediatesFromList(self, nodelist, flags={}):
        r"""
            与えられたノードリストからintermediateオブジェクトを除く。
            
            Args:
                nodelist (list):
                flags (dict):
                
            Returns:
                list:
        """
        if 'ni' in flags or 'noIntermediate' in flags:
            return (
                [asObject(x) for x in nodelist if not cmds.getAttr(x+'.io')]
                if nodelist else []
            )
        return [asObject(x) for x in nodelist] if nodelist else []

    def hasChild(self):
        r"""
            子を持っているかどうか
            
            Returns:
                bool:
        """
        return self._node().childCount() > 0

    def children(self, **keywords):
        r"""
            このノードの子ノードを返すメソッド。
            keywords:にはlistRelativesに入るものが使用可能。
            
            Args:
                **keywords (dict):
                
            Returns:
                list:[AbstractNode]
        """
        if not self._node().childCount():
            return []
        return self.removeIntermediatesFromList(
            cmds.listRelatives(self.name(), c=True, pa=True, **keywords),
            keywords
        )

    def allChildren(self, **keywords):
        r"""
            このノードのすべての子ノードを返すメソッド。
            keywords:にはlistRelativesに入るものが使用可能。
            
            Args:
                **keywords (dict):
                
            Returns:
                list:[AbstractNode]
        """
        if not self._node().childCount():
            return []
        return self.removeIntermediatesFromList(
            cmds.listRelatives(self.name(), ad=True, pa=True, **keywords),
            keywords
        )

    def hasParent(self):
        r"""
            親が存在するかどうかを返す
            
            Returns:
                bool:
        """
        return self._node().parentCount() > 0

    def parents(self, **keywords):
        r"""
            このノードの親のリストを返すメソッド。
            
            Args:
                **keywords (dict):
                
            Returns:
                list:
        """
        if not self._node().parentCount():
            return None
        parents = cmds.listRelatives(self.name(), ap=True, pa=True, **keywords)
        return toObjects(parents) if parents else []

    def parent(self, **keywords):
        r"""
            このノードの親を返すメソッド。
            parents:と違い、こちらは複数の親が見つかっても、最初の１つめ
            だけを返す。
            
            Args:
                **keywords (dict):
                
            Returns:
                AbstractNode:
        """
        parents = self.parents(**keywords)
        return parents[0] if parents else None

    def unparent(self):
        r"""
            自身をワールド空間へペアレントするメソッド。
            
            Returns:
                self:
        """
        mayaCmds.parent(self.name(), w=True)
        return self

    def applyColor(self, color=None):
        r"""
            wireframeカラーを設定する。
            
            Args:
                color (list or tuple or int):
        """
        colorUtil.applyColor(self.name(), color)

    def hide(self):
        r"""
            ノードを非表示にする。
            
            Returns:
                self:
        """
        try:
            self('visibility', 0)
        except:
            pass
        return self

    def show(self):
        r"""
            ノードを表示する
            
            Returns:
                self:
        """
        try:
            self('visibility', 1)
        except:
            pass
        return self

    def orderNumber(self):
        parent = self.parent()
        if not parent:
            members = cmds.ls(assemblies=True)
        else:
            members = parent.children(type='transform')
        my_name = self()
        for i, m in enumerate(members):
            print(m)
            if m == my_name:
                return i
        raise RuntimeError(
            'Can not be detected number of order : {}'.format(my_name)
        )

    def reorder(self, number):
        r"""
            Args:
                number (any):
        """
        number += 1
        my_name = self()
        cmds.reorder(my_name, f=True)
        if number < 1:
            return
        cmds.reorder(my_name, r=number)


class ObjectSet(AbstractNode):
    r"""
        ObjectSet用のクラス。一部DagNodeのメソッドを上書きしている。
    """
    def nodeFn(self):
        r"""
            ObjectSet使用のためのオーバーライド用メソッド。
            
            Returns:
                OpenMaya.MFnSet:
        """
        return OpenMaya.MFnSet

    def text(self):
        r"""
            セット用テキストを返す。
            
            Returns:
                str:
        """
        return self('annotation')

    def setText(self, text):
        r"""
            セット用テキストを設定する。
            
            Args:
                text (str):
        """
        self('annotation', text, type='string')

    def addChild(self, *nodelist):
        r"""
            このセットにメンバーを追加するメソッド。
            しているので、処理速度は低速。
            
            Args:
                *nodelist (tuple):
                
            Returns:
                self:
        """
        setname = self.name()
        for node in nodelist:
            cmds.sets(node, e=True, add=setname)
        return self

    def removeChild(self, *nodelist):
        r"""
            このセットからメンバーを除去するメソッド。
            メンバテストを行っているため、処理速度は低速。
            
            Args:
                *nodelist (tuple):
                
            Returns:
                self:
        """
        setname = self.name()
        nodelist = [x for x in nodelist if cmds.sets(x, im=setname)]
        for node in nodelist:
            cmds.sets(node, e=True, rm=setname)
        return self

    def clear(self):
        r"""
            セットのメンバーを削除する
        """
        self._node().clear()

    def hasChild(self):
        r"""
            メンバーがいるかどうかを返す
            
            Returns:
                list:
        """
        return []

    def children(self):
        r"""
            メンバーを返す
            
            Returns:
                list:
        """
        members = cmds.sets(self.name(), q=True)
        return [asObject(x) for x in members] if members else []

    def allChildren(self, includeSets=False):
        r"""
            全ての子を返す。
            
            Args:
                includeSets (bool):セットも含めるかどうか
                
            Returns:
                list:
        """
        result = []
        sets = []
        for child in self.children():
            if child.isType('objectSet'):
                sets.append(child)
                if includeSets:
                    result.append(child)
                continue
            result.append(child)

        for s in sets:
            result.extend(s.allChildren())
        return result


class ShadingEngine(ObjectSet):
    r"""
        shadingEngine用クラス
    """
    pass


class Transform(DagNode):
    r"""
        transformノード用クラス。
    """
    WorldSpace = {True:OpenMaya.MSpace.kWorld, False:OpenMaya.MSpace.kObject}
    def dagNodeFn(self):
        r"""
            MFnTransform使用のためのオーバーライド用メソッド。
            
            Returns:
                OpenMaya.MFnTransform:
        """
        return OpenMaya.MFnTransform

    def attr(self, attr):
        r"""
            アトリビュートを返すメソッド。
            任意のアトリビュートがない場合はShapeの方も探す。
            
            Args:
                attr (str):
                
            Returns:
                Attribute:
        """
        try:
            return super(Transform, self).attr(attr)
        except:
            for shape in self.shapes(ni=True):
                try:
                    return Attribute(asObject(shape).attr(attr))
                except:
                    pass
        return None

    def position(self, world=True):
        r"""
            ノードのtranslate座標を返す。
            xform:(node, q=True, t=True)と同義。
            
            Args:
                world (bool):ワールド空間で返すかどうか
                
            Returns:
                list:[float, float, float]
        """ 
        return cmds.xform(self(), q=True, ws=world, t=True)

    def setPosition(self, position, world=True):
        r"""
            ノードを任意のポジションへ移動するメソッド。
            xform:(node, t=position)と同義
            
            Args:
                position (list):[float, float, float]
                world (bool):
                
            Returns:
                self:
        """
        cmds.xform(self(), ws=world, t=position)
        return self

    def distance(self, targetNode):
        r"""
            targetNodeとの距離を返す。targetNodeはTransformクラス。
            
            Args:
                targetNode (Transform):
                
            Returns:
                float:
        """
        pos_a = targetNode.position()
        pos_b = self.position()
        return (MVector(pos_a) - MVector(pos_b)).length()

    def matrix(self, world=True):
        r"""
            ノードのmatrixを返す。
            xform:(node, q=True, m=True)と同義。
            
            Args:
                world (bool):ワールド空間で返すかどうか
                
            Returns:
                list:[float x 16]
        """
        return cmds.xform(self(), q=True, ws=world, m=True)

    def setMatrix(
        self, matrix=identityMatrix(), world=True, flags=0b1111
    ):
        r"""
            マトリックスを適応する。
                xform :(node, m=matrix)と同義
                matrix:を特に指定しない場合は初期値のマトリクスが適応される。
            また、flagsによりt,r,s,shのいずれかに適応するかどうかをビット指定に
            より可能。
            
            Args:
                matrix (list):[float x 16]
                world (bool):ワールド空間で適応するかどうか
                flags (bin):4bit、左からt,r,s,shを合わせるかどうか
                
            Returns:
                self:
        """
        if flags == 0b1111:
            # 全てのフラグがOnの場合は単純にマトリクスをセットする。
            cmds.xform(self(), ws=world, m=matrix)
            return self
        tgt_mtx = MMatrix(matrix)
        if world:
            parent = self.parent()
            if parent:
                tgt_mtx *= MMatrix(parent.inverseMatrix())

        trs_mtx = MTransformationMatrix(tgt_mtx)
        wflg = OpenMaya2.MSpace.kWorld
        trs_mtx.reorderRotation(self._node().rotationOrder())
        if flags & 8:
            # translateをセット。
            self('t', [x for x in trs_mtx.translation(wflg)])
        if flags & 4:
            # rotateをセット。
            self(
                'r', [toDegree(x) for x in trs_mtx.rotation(False)]
            )
        if flags & 2:
            # scaleをセット。
            self('s', [x for x in trs_mtx.scale(wflg)])
        if flags & 1:
            # shearをセット。
            self('sh', [x for x in trs_mtx.shear(wflg)])
        return self

    def inverseMatrix(self, world=True):
        r"""
            ノードのInverseMatrixを返す。
            
            Args:
                world (bool):ワールド空間で返すかどうか
                
            Returns:
                list:float x 16
        """
        return (
            cmds.getAttr(self()+'.worldInverseMatrix') if world
            else cmds.getAttr(self()+'.inverseMatrix')
        )

    def fitTo(self, target, flags=0b1111):
        r"""
            targetにこのノードの位置を合わせる。
            引数flagsはt,r,s,shを合わせるかどうかのフラグ。
            
            Args:
                target (Transform):
                flags (bin):左からt,r,s,shを合わせるかどうか
        """
        target = asObject(target)
        self.setMatrix(target.matrix(), True, flags)

    def lockTransform(self, k=False, l=True):
        r"""
            Translate・Rotate・Sacleアトリビュートをロックする。
            引数のデフォルト値が違うだけで、実質unlockTransformとほぼ同じ。
            
            Args:
                k (bool):キーアブルにするかどうか
                l (bool):ロックするかどうか
                
            Returns:
                any:
                
            Brief:
        """
        for attr in ('t', 'r', 's'):
            for ax in ('x', 'y', 'z'):
                cmds.setAttr(self + '.' + attr + ax, k=k, l=l)
        cmds.setAttr(self + '.v', k=False)
        return self

    def unlockTransform(self, k=True, l=False):
        r"""
            Translate・Rotate・Sacleアトリビュートをロック解除する。
            引数のデフォルト値が違うだけで、実質lockTransformとほぼ同じ。
            
            Args:
                k (bool):キーアブルにするかどうか
                l (bool):ロックするかどうか
                
            Returns:
                self:
        """
        for attr in ('t', 'r', 's'):
            for ax in ('x', 'y', 'z'):
                cmds.setAttr(self + '.' + attr + ax, k=k, l=l)
            cmds.setAttr(self + '.' + attr, k=k, l=l)
        cmds.setAttr(self + '.v', k=True, l=False)
        return self

    def rotatePivot(self, ws=True):
        r"""
            rotatePivotの位置を返す。
            
            Args:
                ws (bool):Trueの場合ワールド空間での座標を返す。
                
            Returns:
                list:
        """
        pos = self._node().rotatePivot(self.WorldSpace[ws])
        return [pos.x, pos.y, pos.z]

    def setRotatePivot(self, pos, ws=True):
        r"""
            rotatePivotの位置をセットする。
            
            Args:
                pos (list):３つのスカラー値を持つリスト。
                ws (bool):ワールド空間かどうか
                
            Returns:
                self:
        """
        self._node().setRotatePivot(
            OpenMaya.MPoint(*pos), self.WorldSpace[ws], True
        )
        return self

    def scalePivot(self, ws=True):
        r"""
            scalePivotの位置を返す。
            
            Args:
                ws (bool):Trueの場合ワールド空間での座標を返す。
                
            Returns:
                list:
        """
        pos = self._node().scalePivot(self.WorldSpace[ws])
        return [pos.x, pos.y, pos.z]

    def setScalePivot(self, pos, ws=True):
        r"""
            scalePivotの位置をセットする。
            
            Args:
                pos (list):３つのスカラー値を持つリスト。
                ws (bool):ワールド空間かどうか
        """
        self._node().setScalePivot(
            OpenMaya.MPoint(*pos), self.WorldSpace[ws], True
        )

    def pivot(self, ws=True):
        r"""
            rotatePivotとscalePivot両方を返す
            
            Args:
                ws (bool):ワールド空間かどうか
                
            Returns:
                list:[tuple, tuple]
        """
        return [self.rotatePivot(ws), self.scalePivot(ws)]

    def setPivot(self, pos, ws=True):
        r"""
            ピボットを設定するメソッド。
            
            Args:
                pos (list):[float, float, float]
                ws (bool):ワールド空間で適応するかどうか
                
            Returns:
                self:
        """
        self.setRotatePivot(pos)
        self.setScalePivot(pos)
        return self

    def freeze(self, t=True, r=True, s=True):
        r"""
            フリーズトランスフォームをかける。
            
            Args:
                t (bool):translateにかけるかどうか
                r (bool):rotateにかけるかどうか
                s (bool):scaleにかけるかどうか
                
            Returns:
                self:
        """
        cmds.makeIdentity(self.name(), a=True, t=t, r=r, s=s)
        return self

    def reset(self, t=True, r=True, s=True):
        r"""
            リセットトランスフォームをかける。
            
            Args:
                t (bool):translateにかけるかどうか
                r (bool):rotateにかけるかどうか
                s (bool):scaleにかけるかどうか
                
            Returns:
                self:
        """
        cmds.makeIdentity(self.name(), t=t, r=r, s=s)
        return self

    def shapes(self, typ=[], ni=True):
        r"""
            このノードが持つシェイプを返す
            
            Args:
                typ (list):タイプフィルタ
                ni (bool):IntermediateObjectを含まないかどうか
                
            Returns:
                list:
        """
        return self.removeIntermediatesFromList(
            cmds.listRelatives(
                self.name(), shapes=True, pa=True, type=typ, ni=ni
            ),
            {'ni':ni}
        )

    def addChild(self, *nodelist,  **keywords):
        r"""
            引数で指定したノードをこのノードの子にするメソッド。
            keywordsの引数はparentコマンドと同じ。
            
            Args:
                *nodelist (tuple):
                **keywords (dict):
        """
        try:
            mayaCmds.parent([verutil.String(x) for x in nodelist], self(), **keywords)
            return self
        except Exception as e:
            print([verutil.String(x) for x in nodelist])
            print(self)
            raise RuntimeError(e)

    def ungroup(self, world=False):
        r"""
            自身のグループ化を解除する。
            戻り値として解除後の子の名前のリストを返す。
            
            Args:
                world (bool):Trueの場合解除後の子をワールドに配置する
                
            Returns:
                list:
        """
        children = self.children()
        mayaCmds.ungroup(self())
        return [asObject(x()) for x in children]

    def isOpposite(self):
        r"""
            ジョイントのX軸が子(または親)と反対方向を向いているかどうかを返す。
            
            Returns:
                bool:
        """
        factor = 1
        if self.hasChild():
            hir_node = self.children(type='transform')[0]
        else:
            if not self.hasParent():
                return False
            hir_node = self.parent()
            factor = -1

        world_matrix = self.matrix()
        x_vector = mathlib.Vector(world_matrix[:3])
        joint_vector = mathlib.Vector(world_matrix[12:15])

        hir_vector = mathlib.Vector(hir_node.matrix()[12:15])
        to_hir_vector = hir_vector - joint_vector

        x_vector.normalize()
        to_hir_vector.normalize()
        theta = x_vector * to_hir_vector
        return (theta*factor) <= 0


class Joint(Transform):
    r"""
        Jointノード用のクラス。
    """
    def setInverseScale(self, jointOnly=True):
        r"""
            自身の親ノードとインバーススケールの接続を行う。
            接続を行った場合はTrueを返す。
            
            Args:
                jointOnly (bool):
                
            Returns:
                bool:
        """
        if not self.hasParent():
            return False
        plug = self.attr('inverseScale')
        if plug.source():
            return False
        flag = {'type':'joint'} if jointOnly else {}
        try:
            self.parent(**flag).attr('scale') >> plug
        except Exception as e:
            return False
        return True

    def setMatrix(
        self, matrix=identityMatrix(), world=True, flags=0b1111
    ):
        r"""
            マトリックスを適応する。
            xform :(node, m=matrix)と同義
            matrix:を特に指定しない場合は初期値のマトリクスが適応される。
            また、flagsによりt,r,s,shのいずれかに適応するかどうかを
            ビット指定により可能。
            
            Args:
                matrix (list):[float x 16]
                world (bool):ワールド空間で適応するかどうか
                flags (bin):左からt,r,s,shを合わせるかどうか
        """
        ssc = self('ssc')
        super(Joint, self).setMatrix(matrix, world, flags)
        self('ssc', ssc)

    def setRadius(self, value):
        r"""
            radiusを変更するメソッド。
            
            Args:
                value (float):
        """
        self('radius', value)

    def hideDisplay(self):
        r"""
            ジョイントの描画を消す。
        """
        self('radius', 0, k=False, cb=False)
        self('drawStyle', 2)


class IkHandle(Transform):
    r"""
        ikHandleノード用クラス。
    """
    def setPoleVectorNode(self, node):
        r"""
            ポールベクターを設定する。
            
            Args:
                node (str):
        """
        return cmds.poleVectorConstraint(node, self())


class Shape(DagNode):
    r"""
        シェイプ用のクラス。
    """
    pass


class AbstractEditableShape(Shape):
    r"""
        編集可能なシェイプを操作するクラス。
        フリーズされた状態の自身のコピーを作成するメソッドを持っており、
        正確なバウンディングボックスの計測や法線の取得などに使用できる。
    """
    def inOutPlugs(self):
        r"""
            再実装用メソッド。
            戻り値としてこのシェイプの形状情報を受取るアトリビュート名と
            出力するアトリビュート名を持つtupleを返す必要がある。
            
            Returns:
                list(str, str):
        """
        return ('', '')

    def createFreezedShape(self):
        input_plug, output_plug = self.inOutPlugs()
        trs = cmds.createNode('transform')
        shape = cmds.createNode(self.type(), p=trs)
        trs_geo = createUtil('transformGeometry')
        trs_geo.attr('outputGeometry') >> shape+'.'+input_plug
        self.attr(output_plug) >> trs_geo.attr('inputGeometry')
        self.attr('parentMatrix') >> trs_geo.attr('transform')
        cmds.delete(trs, ch=True)
        return toObjects([trs, shape])


class Mesh(AbstractEditableShape):
    r"""
        meshノード用のクラス。
    """
    def dagNodeFn(self):
        r"""
            MFnMesh使用のためのオーバーライド用メソッド。
            
            Returns:
                OpenMaya.MFnMesh:
        """
        return OpenMaya.MFnMesh

    def inOutPlugs(self):
        r"""
            Returns:
                list(str, str):
        """
        return ('inMesh', 'worldMesh')

    def vertexCount(self):
        r"""
            頂点数を返す
            
            Returns:
                int:
        """
        return self._node().numVertices()

    def edgeCount(self):
        r"""
            エッジ数を返す
            
            Returns:
                int:
        """
        return self._node().numEdges()

    def faceCount(self):
        r"""
            面の数を返す
            
            Returns:
                int:
        """
        return self._node().numPolygons()

    def faceVertexCount(self):
        r"""
            フェースバーテックス数を返す
            
            Returns:
                int:
        """
        return self._node().numFaceVertices()

    def uvCount(self):
        r"""
            UV数を返す
            
            Returns:
                int:
        """
        return self._node().numUVs()

    def closestPoint(self, position, world=True):
        r"""
            引数positionからの最接近位置を返す。
            
            Args:
                position (list):位置を表す３つの数字を持つリスト
                world (bool):ワールド空間かどうか
                
            Returns:
                list:
        """
        space = OpenMaya.MSpace.kWorld if world else OpenMaya.MSpace.kObject
        s = OpenMaya.MPoint(*position)
        d = OpenMaya.MPoint()
        self._node().getClosestPoint(s, d, space)
        pos = [d.x, d.y, d.z]
        return pos

    def closestUV(self, position, world=True, uvSetName=None):
        r"""
            引数positionからの最接近UVを返す。
            
            Args:
                position (list):位置を表す３つの数字を持つリスト
                world (bool):ワールド空間かどうか
                uvSetName (str):UVセット名
                
            Returns:
                list:
        """
        space = OpenMaya.MSpace.kWorld if world else OpenMaya.MSpace.kObject
        pos = OpenMaya.MPoint(*position)
        sutil.createFromList([0, 0], 2)
        uv = sutil.asFloat2Ptr()
        self._node().getUVAtPoint(pos, uv, space, uvSetName)
        return [sutil.getFloat2ArrayItem(uv, 0, x ) for x in range(2)]

    def closestNormal(self, position, world=True):
        r"""
            与えられた位置から最も近い面のノーマルを返す。
            
            Args:
                position (list):位置を表す３つの数字を持つリスト
                world (bool):ワールドかどうか
                
            Returns:
                list:3次元ベクトルを表すリスト
        """
        space = OpenMaya.MSpace.kWorld if world else OpenMaya.MSpace.kObject
        vec = OpenMaya.MVector()
        pos = OpenMaya.MPoint(*position)
        self._node().getClosestNormal(pos, vec, space)
        return [vec.x, vec.y, vec.z]


class NurbsSurface(AbstractEditableShape):
    r"""
        NURBSサーフェース用のクラス。
    """
    def dagNodeFn(self):
        r"""
            MFnNurbsSurface使用のためのオーバーライド用メソッド。
            
            Returns:
                OpenMaya.MFnNurbsSurface:
        """
        return OpenMaya.MFnNurbsSurface

    def inOutPlugs(self):
        r"""
            Returns:
                list(str, str):
        """
        return ('create', 'worldSpace')

    def closestPoint(self, position, world=True):
        r"""
            引数positionからの最接近位置を返す。
            
            Args:
                position (list):位置を表す３つの数字を持つリスト
                world (bool):ワールド空間かどうか
                
            Returns:
                list:
        """
        space = OpenMaya.MSpace.kWorld if world else OpenMaya.MSpace.kObject
        s = OpenMaya.MPoint(*position)
        d = self._node().closestPoint(s, None, None, False, 1.0e-3, space)
        return [d.x, d.y, d.z]

    def closestUV(self, position, world=True):
        r"""
            引数positionからの最接近UVを返す。
            
            Args:
                position (list):位置を表す３つの数字を持つリスト
                world (bool):ワールド空間かどうか
                
            Returns:
                list:
        """
        space = OpenMaya.MSpace.kWorld if world else OpenMaya.MSpace.kObject
        pos = OpenMaya.MPoint(*self.closestPoint(position, False))
        uutil = OpenMaya.MScriptUtil()
        u = uutil.asDoublePtr()
        vutil = OpenMaya.MScriptUtil()
        v = vutil.asDoublePtr()
        self._node().getParamAtPoint(pos, u, v, False, space)
        return [uutil.getDouble(u), vutil.getDouble(v)]

    def pointOnUV(self, uv, world=True):
        r"""
            引数UVで指定した箇所の３D空間での座標を返す
            
            Args:
                uv (list):UとVの値を持つリスト
                world (bool):ワールド空間かどうか
                
            Returns:
                list:
        """
        space = OpenMaya.MSpace.kWorld if world else OpenMaya.MSpace.kObject
        pos = OpenMaya.MPoint()
        self._node().getPointAtParam(uv[0], uv[1], pos, space)
        return [pos.x, pos.y, pos.z]

    def closestNormal(self, position, world=True):
        r"""
            与えられた位置から最も近い面のノーマルを返す。
            
            Args:
                position (list):位置を表す３つの数字を持つリスト
                world (bool):ワールドかどうか
                
            Returns:
                list:3次元ベクトルを表すリスト
        """
        space = OpenMaya.MSpace.kWorld if world else OpenMaya.MSpace.kObject
        uv = self.closestUV(position, world)
        vec = self._node().normal(uv[0], uv[1], space)
        return [vec.x, vec.y, vec.z]


class NurbsCurve(AbstractEditableShape):
    r"""
        Nurbsカーブ用のクラス
    """
    def dagNodeFn(self):
        r"""
            変換クラスを返す。
            
            Returns:
                OpenMaya.MFnNurbsCurve:
        """
        return OpenMaya.MFnNurbsCurve

    def inOutPlugs(self):
        r"""
            Returns:
                list(str, str):
        """
        return ('create', 'worldSpace')
 
    def length(self):
        r"""
            カーブの長さを返す
            
            Returns:
                float:
        """
        return self._node().length()

    def degree(self):
        r"""
            degreeを返す
            
            Returns:
                int:
        """
        return self._node().degree()

    def findParam(self, length):
        r"""
            任意の長さに対応するパラメータ値を返す
            
            Args:
                length (float):
                
            Returns:
                float:
        """
        return self._node().findParamFromLength(length)

    def point(self, param, world=True):
        r"""
            任意のパラメータ値の３D空間上での座標を返す
            
            Args:
                param (float):
                world (bool):ワールド空間かどうか
                
            Returns:
                list:３つのfloat
        """
        m_point = OpenMaya.MPoint()
        self._node().getPointAtParam(
            param, m_point,
            OpenMaya.MSpace.kWorld if world else OpenMaya.MSpace.kObject
        )
        return [m_point.x, m_point.y, m_point.z]

    def pointFromLength(self, length, world=True):
        r"""
            カーブ上の任意の長さの地点の3D空間上での座標を返す
            
            Args:
                length (float):
                world (bool):ワールド空間かどうか
                
            Returns:
                list:３つのfloat
        """
        return self.point(self.findParam(length), world)
    
    def closestPoint(self, position, world=True):
        r"""
            任意の座標から最も近いカーブ状の位置を返す。
            
            Args:
                position (tuple):任意の座標
                world (bool):ワールド空間かどうか
                
            Returns:
                list:３つのfloat
        """
        space = OpenMaya.MSpace.kWorld if world else OpenMaya.MSpace.kObject
        s = OpenMaya.MPoint(*position)
        d = self._node().closestPoint(s, None, 1.0e-3, space)
        return [d.x, d.y, d.z] 

    def closestParam(self, position, world=True):
        r"""
        Args:
            position (any):
            world (any):
    """
        space = OpenMaya.MSpace.kWorld if world else OpenMaya.MSpace.kObject
        pos = self.closestPoint(position, True)
        s = OpenMaya.MPoint(*pos)
        uutil = OpenMaya.MScriptUtil()
        u = uutil.asDoublePtr()
        d = self._node().getParamAtPoint(s, u, space)
        return uutil.getDouble(u)

    def normal(self, param, world=True):
        r"""
            Args:
                param (any):
                world (any):
        """
        v = self._node().normal(
            param, OpenMaya.MSpace.kWorld if world else OpenMaya.MSpace.kObject
        )
        return [v.x, v.y, v.z]

    def tangent(self, param, world=True):
        r"""
            Args:
                param (any):
                world (any):
        """
        v = self._node().tangent(
            param, OpenMaya.MSpace.kWorld if world else OpenMaya.MSpace.kObject
        )
        return [v.x, v.y, v.z]

    def simpleRebuild(self, span=2, degree=3):
        r"""
            任意の設定に応じて簡易リビルドを行う。
            
            Args:
                span (int):スパン数
                degree (int):degree数
        """
        degrees = (1, 2, 3, 5, 7)
        if span < 1:
            raise ValueError('span flag requires more than 1.')
        if not degree in degrees:
            raise ValueError(
                'degree flag must be a theese value : {}'.format(degrees)
            )
        length = self.length()
        num = span+degree
        unit_len = length / float(num-1)
        positions = []
        for i in range(num):
            positions.append(self.pointFromLength(unit_len*i))
        self.deleteHistory()
        crv = cmds.curve(
            self(), d=degree, p=positions, worldSpace=True, replace=True
        )


class ImplicitObject(Shape):
    r"""
        implicitSphere, Box, Coneを取扱うクラス。
        
        Inheritance:
            Shape:@date        2017/07/11 4:39[Eske](eske3g@gmail.com)
    """
    def setSize(self, size):
        r"""
            大きさを指定する。
            引数sizeには一つのfloatか3つのfloatを持つリストを渡す。
            
            Args:
                size (float or list):
        """
        if not isinstance(size, (list, tupe)):
            size =  [size, size, size]
        self('size', size)


# /////////////////////////////////////////////////////////////////////////////
# Nodeクラスを取り扱うための関数セット。                                     //
# /////////////////////////////////////////////////////////////////////////////
ClassTable = {
    'transform' : Transform, 'dagContainer':Transform,
    'shape' : Shape,
    'joint' : Joint, 'ikHandle' : IkHandle,
    'objectSet' : ObjectSet, 'shadingEngine':ShadingEngine,
    'fourByFourMatrix' : FourByFourMatrix,
    'mesh' : Mesh, 'nurbsCurve' : NurbsCurve, 'nurbsSurface' : NurbsSurface,
    'skinCluster':SkinCluster,
    'blendShape' : BlendShape,
    'implicitSphere':ImplicitObject,
    'implicitBox':ImplicitObject,
    'implicitCone':ImplicitObject,
    'controller':Controller,
}

def asObject(nodeName, nodeType=None):
    r"""
        AbstractNodeクラスに変換する。
        nodeType:が指定されている場合は、その型への変換を試みる。
        変換に失敗した場合はNoneを返す。
        
        Args:
            nodeName (str):
            nodeType (AbstractNode):
            
        Returns:
            AbstractNode:
    """
    try:
        name = verutil.String(nodeName)
        if nodeType:
            return nodeType(name)
        if not cmds.objExists(name):
            return
        types = cmds.nodeType(name, i=True)
        types.reverse()
        for t in types:
            cls = ClassTable.get(t)
            if cls:
                return cls(name)
        return AbstractNode(nodeName)
    except Exception as e:
        print('[Error] : {}'.format(e.args[0]))
        return


def asAttr(nodeName):
    r"""
        与えられたノード名.アトリビュート名に対するAttributeを返す
        取得に失敗した場合は、そのままの文字列を返す。
        
        Args:
            nodeName (str):
            
        Returns:
            Attribute:
    """
    if not '.' in nodeName:
        return asObject(nodeName)

    try:
        comp = nodeName.split('.')
        node = asObject(comp[0])
        return node.attr('.'.join(comp[1:]))
    except:
        nodeName

def toAttrs(attrlist):
    r"""
        アトリビュート名のリストをAttributeオブジェクトへ変換する。
        
        Args:
            attrlist (list):”ノード名.アトリビュート名”のリスト
            
        Returns:
            list:
    """
    newlist = [asAttr(x) for x in attrlist]
    return [x for x in newlist if x]


def toObjects(nodelist):
    r"""
        複数の文字列リストをAbstractNodeクラスへ変換する。
        
        Args:
            nodelist (list or str):
            
        Returns:
            list(AbstractNode):
    """
    if nodelist is None:
        return []
    if isinstance(nodelist, (list, tuple)):
        return [asObject(x) for x in nodelist]
    else:
        return [asObject(nodelist)]


def ls(*nodes, **keywords):
    r"""
        cmds.lsと同様だが、戻り値がAbstractNodeのリストになる。
        
        Args:
            *nodes (tuple):
            **keywords (dict):
            
        Returns:
            list:
    """
    return [
        asObject(x) for x in cmds.ls(*nodes, **keywords)
    ]


def selected(nodelist=None, **keywords):
    r"""
        選択ノードをオブジェクト形式のリストにして返すメソッド。
        引数nodelistにノード名のリストを入れた場合は、そちらの項目の
        変換が優先される。
        
        Args:
            nodelist (list):
            **keywords (dict):lsコマンドの引数と同じ
            
        Returns:
            list:
    """
    return (
        ls(sl=True, **keywords) if not nodelist else toObjects(nodelist)
    )


def createNode(nodeType, **keywords):
    r"""
        ノードを作成する関数。作成されたノードはAbstractNodeオブジェクト
        として返ってくる。
        引数はcreateNodeコマンドと同じ。
        
        Args:
            nodeType (str):
            **keywords (dict):
            
        Returns:
            AbstractNode:
    """
    return asObject(cmds.createNode(nodeType, **keywords))


def createUtil(nodeType, **keywords):
    r"""
        createNodeの拡張関数。ノードを作成しAbstractNodeオブジェクトとして返す。
        引数はcreateNodeコマンドと同じ。
        作成されたオブジェクトはihiアトリビュートが0になり、ChannelBoxから
        見ることが出来ない。
        
        Args:
            nodeType (str):
            **keywords (dict):
            
        Returns:
            AbstractNode:
    """
    result = createNode(nodeType, **keywords)
    result('ihi', 0)
    return result


def shadingNode(nodeType, **keywords):
    r"""
        シェーディングノードを作成し、AbstractNodeオブジェクトとして返す。
        引数はshadingNodeコマンドと同じ。
        
        Args:
            nodeType (str):
            **keywords (any):
            
        Returns:
            AbstractNode:
    """
    return asObject(cmds.shadingNode(nodeType, **keywords))


def listConnections(*nodelist, **keywords):
    r"""
        Gris用listConnectionsのラッパ関数。戻り値はAbstractNodeのリスト。
        引数はlistConnectionsと同じ。
        
        Args:
            *nodelist (tuple):
            **keywords (dict):
            
        Returns:
            list:
    """
    con = cmds.listConnections(nodelist, **keywords) or []
    if 'p' in keywords or 'plugs' in keywords:
        return toAttrs(con)
    else:
        return [asObject(x) for x in con]


def listRelatives(*nodelist, **keywords):
    r"""
        Gris用listRelativesのラッパ関数。戻り値はAbstractNodeのリスト。
        引数はlistRelativesと同じ。
        
        Args:
            *nodelist (tuple):
            **keywords (dict):
            
        Returns:
            list:
    """
    keywords['pa'] = True
    if 'path' in keywords:
        del keywords['path']
    return toObjects(cmds.listRelatives(nodelist, **keywords) or [])


def sources(nodelist=None, **keywords):
    r"""
        引数nodelistの入力コネクション側のリストを返す。
        引数はlistConnectionsと同じ。
        
        Args:
            nodelist (list):
            **keywords (dict):
            
        Returns:
            list:
    """
    return listConnections(nodelist, s=True, d=False, **keywords) or []


def destinations(nodelist=None, **keywords):
    r"""
        引数nodelistの出力コネクション側のリストを返す。
        引数はlistConnectionsと同じ。
        
        Args:
            nodelist (list):[]
            **keywords (dict):
            
        Returns:
            list:
    """
    return listConnections(nodelist, s=False, d=True, **keywords) or []


def duplicate(*nodes, **keywords):
    r"""
        duplicateコマンドを行う。
        デフォルトの挙動はrrがTrueになるようになっている。
        rc:がTrueの場合のみ、rrの操作が可能になる。
        戻り値はAbstractNode化されたオブジェクトのリスト。
        
        Args:
            *nodes (tuple):
            **keywords (dict):
            
        Returns:
            list:
    """
    rc = keywords.pop('renameChildren', False)
    rc = keywords.pop('rc', rc)
    if not rc:
        rr = keywords.pop('returnRootsOnly', True)
        rr = keywords.pop('returnRootsOnly', rr)
        keywords['rr'] = rr
    keywords['rc'] = rc
    return [
        asObject(x) for x in cmds.duplicate(*nodes, **keywords)
    ]


def parent(*nodes, **keywords):
    r"""
        親子付を行う。戻り値はAbstractNode化されたオブジェクトのリスト。
        引数はparentコマンドと同じ。
        
        Args:
            *nodes (tuple):
            **keywords (dict):
            
        Returns:
            list:
    """
    return toObjects(cmds.parent(*nodes, **keywords))


def rename(node, newName):
    r"""
        ノードのリネームを行う。戻り値はAbstractNodeとなる。
        
        Args:
            node (str):操作対象ノード名
            newName (str):新しい名前
            
        Returns:
            AbstractNode:
    """
    return asObject(cmds.rename(node, newName))


def lattice(*nodes, **keywords):
    r"""
        ラティスを作成する。戻り値がAbstractNodeとなる。
        引数はlatticeコマンドと同じ。
        
        Args:
            *nodes (tuple):
            **keywords (dict):
            
        Returns:
            list:ラティス、ベースノード、FFDを持つリスト
    """
    return toObjects(cmds.lattice(*nodes, **keywords))


def cluster(*nodes, **keywords):
    r"""
        クラスタを作成する。戻り値がAbstractNodeになる。
        引数はclusterコマンドと同じ。
        
        Args:
            *nodes (tuple):
            **keywords (dict):
            
        Returns:
            list(AbstractNode):
    """
    return toObjects(cmds.cluster(*nodes, **keywords))


def blendShape(*nodes, **keywords):
    r"""
        ブレンドシェイプを作成する。戻り値がBlendShapeになる。
        引数はblendShapeコマンドと同じ。
        
        Args:
            *nodes (tuple):
            **keywords (dict):
            
        Returns:
            list(BlendShape):
    """
    return toObjects(cmds.blendShape(*nodes, **keywords))


def ikHandle(**keywords):
    r"""
        ikHandleを作成する。戻り値がAbstractNodeになる。
        引数はikHandleコマンドと同じ。
        
        Args:
            **keywords (dict):
            
        Returns:
            list:
    """
    return toObjects(cmds.ikHandle(**keywords))


def createIkHandle(name='', parent=None, **keywords):
    r"""
        IKハンドルを作成する。
        標準のIK作成コマンドに加え、親の指定も可能。
        その他引数はikHandleコマンドと同じ。
        
        Args:
            name (str):
            parent (str):
            **keywords (dict):
            
        Returns:
            list:IKハンドル、エンドエフェクタを持つリスト
    """
    ik, ee = cmds.ikHandle(**keywords)
    if parent:
        ik = cmds.parent(ik, parent)[0]
    if name:
        ik = cmds.rename(ik, name)
    return toObjects([ik, ee])


def getController(object):
    r"""
        指定したノードに紐づけされているcontrollerノードを返す。
        見つからない場合はNoneを返す。
        
        Args:
            object (str):ノード名
            
        Returns:
            Controller:
    """
    o = asObject(object)
    if o.isType('controller'):
        return o
    ctrls = o.attr('message').destinations(type='controller', p=True)
    for ctrl in ctrls:
        if ctrl.attrName() == 'controllerObject':
            return Controller(ctrl.nodeName())


def setController(*nodes):
    r"""
        オブジェクトにコントローラを割り当てる。
        戻り値としてControllerクラスのリストを返す
        
        Args:
            *nodes (tuple):
            
        Returns:
            list:
    """
    nodes = selected(nodes)
    cmds.controller(*nodes)
    controllers = []
    for n in nodes:
        c = getController(n)
        if not c:
            continue
        # c('visibilityMode', 2)
        controllers.append(c)
    return controllers


if mayaCmds.MAYA_VERSION < 2017:
    setController = lambda x : []


def getShapes(targetNode, shapeType, noIntermediate=True):
    r"""
        targetNodeから、引数shapeTypeで指定するノードタイプのシェイプを返す。
        targetNodeがTransformの場合、その子のシェイプが該当するタイプのノードを
        返す。
        targetNodeがshapeTypeそのものの場合は、リスト化してから返す。

        Args:
            targetNode (str):
            shapeType (str):
            noIntermediate (bool):
        
        Returns:
            list: shapeTypeに該当するAbstractNodeのリスト。
    """
    node = asObject(targetNode)
    if node.isSubType('transform'):
        return node.children(typ=shapeType, ni=noIntermediate)
    elif node.isType(shapeType):
        return [node]
    return []
    

# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////


# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////
def MMatrixToFloat(mmatrix):
    r"""
        MMatrixを16個の要素のdoubleからなるリストとして返す。
        
        Args:
            mmatrix (OpenMaya.MMatrix):
            
        Returns:
            floatx16:
    """
    f = sutil.getDouble4ArrayItem
    mtx = mmatrix.matrix
    return [f(mtx, 0, x) for x in range(16)]
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////