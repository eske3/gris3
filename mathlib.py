#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ベクトルや行列などを取り扱うクラスを持つ数学補助モジュール
    
    Dates:
        date:2017/01/22 0:02[Eske](eske3g@gmail.com)
        update:2020/12/08 11:36 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import math
import re
from . import verutil

def isnum(n):
    r"""
        与えられた値がスカラーかどうかを返すメソッド。
        
        Args:
            n (any):

        Returns:
            bool:
    """
    return isinstance(n, (int, float, verutil.Long, complex))


# /////////////////////////////////////////////////////////////////////////////
# Vector class.                                                              //
# /////////////////////////////////////////////////////////////////////////////
Axislist = [
    '+X', '+Y', '+Z', '-X', '-Y', '-Z'
]

AxisX = (1, 2)
AxisY = (0, 2)
AxisZ = (0, 1)

def axisToVector( axis ):
    r"""
        あたえられた文字列に該当するベクトルを返す。
        
        Args:
            axis (str):+(-)X, Y, Zのいずれか
            
        Returns:
            Vector:
    """
    if axis == '+Y':
        return Vector([0, 1, 0])
    elif axis == '+Z':
        return Vector([0, 0, 1])
    elif axis == '-X':
        return Vector([-1, 0, 0])
    elif axis == '-Y':
        return Vector([0, -1, 0])
    elif axis == '-Z':
        return Vector([0, 0, -1])
    else:
        return Vector([1, 0, 0])

class Vector(list):
    r"""
        ベクトル計算を行うためのクラス。
    """
    def __new__(cls, values):
        r"""
            3つの数字を持つリストを受取る。
            
            Args:
                values (list):
                
            Returns:
                Vector:
        """
        numberOfValues = len(values)
        if numberOfValues != 3:
            raise ValueError('The argument must includes 3 values as list.')

        return super(Vector, cls).__new__(cls, values)

    def __checkArg(self, value):
        r"""
            引数がVectorではない場合は例外を送出する
            
            Args:
                value (any):
        """
        if not isinstance(value, Vector):
            raise TypeError(
                'The value is not instance of Vector class. Except "%s"' % (
                    type(value)
                )
            )
    def __checkNumber(self, value):
        r"""
            引数が数字ではない場合は例外を送出する
            
            Args:
                value (any):
        """
        if not isnum(value):
            raise TypeError('The value must be numerical character.')
            

    def __set(self, values):
        r"""
            自身の持つベクトルを更新する
            
            Args:
                values (list):
        """
        for i in range(len(values)):
            self[i] = values[i]
       
    def __repr__(self):
        r"""
            このオブジェクトが持つベクトルを表示する文字列
            
            Returns:
                str:
        """
        return '<< %s >>' % (', '.join(str(x) for x in self))
    
    def __add__(self, vector):
        r"""
            加算の再実装メソッド。ベクトルの加算の結果を返す
            
            Args:
                vector (Vector):
                
            Returns:
                Vector:
        """
        self.__checkArg(vector)
        return Vector([ x + y for x, y in zip(self, vector) ])

    def __iadd__(self, vector):
        r"""
            加算の再実装メソッド。ベクトルの加算の結果を返す
            
            Args:
                vector (Vector):
                
            Returns:
                Vector:
        """
        return self.__add__(vector)

    def __sub__(self, vector):
        r"""
            除算の再実装メソッド。ベクトルの除算の結果を返す
            
            Args:
                vector (Vector):
                
            Returns:
                Vector:
        """
        self.__checkArg(vector)
        return Vector([ x - y for x, y in zip(self, vector) ])
    def __isub__(self, vector):
        r"""
            除算の再実装メソッド。ベクトルの除算の結果を返す
            
            Args:
                vector (Vector):
                
            Returns:
                Vector:
        """
        return self.__sub__(vector)

    def __mul__(self, value):
        r"""
            valueがVectorの場合は内積、スカラーならばスカラー倍のベクトルを返す。
            
            Args:
                value (Vector or float):
                
            Returns:
                Vector or float:
        """
        if isnum(value):
            return Vector([ x * value for x in self ])
        self.__checkArg(value)
        return self[0]*value[0] + self[1]*value[1] + self[2]*value[2]

    def __div__(self, value):
        r"""
            商の再実装メソッド。valueで割ったベクトルを返す
            
            Args:
                value (float):
                
            Returns:
                Vector:
        """
        self.__checkNumber(value)
        return Vector([ x / value for x in self ])

    def __idiv__(self, value):
        r"""
            商の再実装メソッド。valueで割ったベクトルを返す
            
            Args:
                value (float):
                
            Returns:
                Vector:
        """
        return self.__div__(value)

    def __truediv__(self, value):
        return self.__div__(value)

    def __itruediv__(self, value):
        return self.__idiv__(value)

    def __pow__(self, vector):
        r"""
            ベクトルの外積を返す。
            
            Args:
                vector (Vector):
                
            Returns:
                Vector:
        """
        self.__checkArg(vector)
        return Vector([
                self[1]*vector[2] - self[2]*vector[1],
                self[2]*vector[0] - self[0]*vector[2],
                self[0]*vector[1] - self[1]*vector[0]
            ]
        )
    def __ipow__(self, vector):
        r"""
            ベクトルの外積を返す。
            
            Args:
                vector (Vector):
                
            Returns:
                Vector:
        """
        return self.__pow__(vector)

    def __and__(self, vector):
        r"""
            ２つのベクトルのなす角を返す。
            
            Args:
                vector (Vector):
                
            Returns:
                float:
        """
        self.__checkArg(vector)
        theta = 1.0
        try:
            theta = math.acos(self.norm() * vector.norm())
        except ZeroDivisionError:
            return 0
        return math.degrees(theta)

    def __or__(self, vector):
        r"""
            2つのベクトルによって形成される三角形の垂線ベクトルを求める
            
            Args:
                vector (Vector):
                
            Returns:
                Vector:
        """
        ab = -(self * vector)
        ratios = [((self.length() ** 2) - ab), ((vector.length() ** 2) - ab)]
        ratios.append(sum(ratios))
        return (
            self * (ratios[1] / ratios[2]) + vector * (ratios[0] / ratios[2])
        )

    def __xor__(self, vector):
        r"""
            2つのベクトルのナス角を返す。
            
            Args:
                vector (Vector):
                
            Returns:
                float:
        """
        self.__checkArg(vector)
        theta = 1.0
        try:
            theta = math.acos(self.norm() * vector.norm())
        except ZeroDivisionError:
            return 0
        return math.degrees(theta)

    def __neg__(self):
        r"""
            正負逆のベクトルを返す。
            
            Returns:
                Vector:
        """
        return Vector([ -x for x in self ])

    def __invert__(self):
        r"""
            長さを返す。lengthのシュガーシンタックス。
            
            Returns:
                float:
        """
        return self.length()

    def length(self):
        r"""
            このベクトルの長さを返す。
            
            Returns:
                float:
        """
        return math.sqrt(sum([x*x for x in self]))

    def norm(self):
        r"""
            正規化された新しいVectorを返す。
            
            Returns:
                Vector:
        """
        l = self.length()
        return Vector([ x / l for x in self ])

    def normalize(self):
        r"""
            自身を正規化する。
        """
        self.__set(self.norm())

    @property
    def x(self):
        r"""
            X要素を返す。
            
            Returns:
                float:
        """
        return self[0]

    @x.setter
    def x(self, value):
        r"""
            X要素を代入する。
            
            Args:
                value (float):
        """
        self.__checkNumber(value)
        self[0] = value

    @property
    def y(self):
        r"""
            Y要素を返す。
            
            Returns:
                float:
        """
        return self[1]
    @y.setter
    def y(self, value):
        r"""
            Y要素を代入する。
            
            Args:
                value (float):
        """
        self.__checkNumber(value)
        self[1] = value

    @property
    def z(self):
        r"""
            Z要素を返す。
            
            Returns:
                float:
        """
        return self[2]
    @z.setter
    def z(self, value):
        r"""
            Z要素を代入する。
            
            Args:
                value (float):
        """
        self.__checkNumber(value)
        self[2] = value


class Axis(str):
    r"""
        与えれた行列の位置情報からベクトルを表す文字列を生成する。
    """
    Axislist = {0:'+x', 1:'-x', 2:'+y', 3:'-y', 4:'+z', 5:'-z'}
    BasicVectors = [
        Vector([1, 0, 0]),
        Vector([-1, 0, 0]),
        Vector([0, 1, 0]),
        Vector([0, -1, 0]),
        Vector([0, 0, 1]),
        Vector([0, 0, -1]),
    ]
    def __new__(cls, matrix):
        r"""
            Args:
                matrix (list):16個のfloatからなる行列を表す文字列
                
            Returns:
                Axis:
        """
        vec = Vector(matrix.translate())
        vec.normalize()

        dotProducts = [x * vec for x in Axis.BasicVectors]
        maxIndex = dotProducts.index(max(dotProducts))

        obj = super(Axis, cls).__new__(cls, Axis.Axislist[maxIndex])
        obj.__matrix = matrix
        return obj

    def asMatrix(self):
        r"""
            入力ソースとなった行列を返す。
            
            Returns:
                list:
        """
        return self.__matrix
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////


# /////////////////////////////////////////////////////////////////////////////
# 行列に関する機能群。                                                       //
# /////////////////////////////////////////////////////////////////////////////
def mirrorMatrix(matrix, axis):
    r"""
        入力行列に対してmirrorBehavior状態の行列を返す。
        
        Args:
            matrix (list):16個のfloatを持つlist
            axis (tuple):mirrorMatrix.X(Y,Z)のいずれか
            
        Returns:
            list:
    """
    matrix = matrix[:]
    for i in range(3):
        for j in axis:
            index = i*4+j
            matrix[index] *= -1
    matrix[15-sum(axis)] *= -1
    return matrix
mirrorMatrix.X = (1, 2)
mirrorMatrix.Y = (0, 2)
mirrorMatrix.Z = (0, 1)

class FMatrix(object):
    r"""
        4x4の行列を取り扱うクラス。
        
        Inheritance:
            object:@date        2017/01/22 0:02[Eske](eske3g@gmail.com)
    """
    MatrixSize = 4
    def __init__(self, *elements):
        r"""
            Args:
                *elements (list):16個のfloatのリスト
        """
        if not elements:
            # If no value was specified, return FMatrix instance as an
            # identity matrix.
            valuelist = [
                1, 0, 0, 0,
                0, 1, 0, 0,
                0, 0, 1, 0,
                0, 0, 0, 1
            ]
        elif len(elements) == 1:
            if isinstance(elements[0], (list, tuple)):
                valuelist = elements[0]
            elif isinstance(elements[0], self.__class__):
                valuelist = elements.asList()
        else:
            valuelist = elements

        if len(valuelist) != self.MatrixSize ** 2:
            raise ValueError(
                (
                    '%s requires list or tuple includes '
                    '16 elements.'
                ) % cls.name
            )
        valuelist = [float(x) for x in valuelist]

        self.__elements = valuelist
        self.__comparingThreshold = 0.000000000000001

    def __operandError(self, operandType, value):
        r"""
            Args:
                operandType (any):
                value (any):
        """
        mobj = re.compile("'.+'")
        selfType = mobj.search(str(self.__class__)).group(0)[1:-1]
        valueType = mobj.search(str(value.__class__)).group(0)[1:-1]
        raise TypeError(
            "unsupported operand type(s) for + : '%s' and '%s'" % (
                selfType, valueType
            )
        )

    def __str__(self):
        r"""
            Returns:
                str:
        """
        formatlist = []
        for i in range(self.MatrixSize):
            rows = []
            for j in range(self.MatrixSize):
                rows.append(str(self.__elements[self.MatrixSize * i + j]))
            formatlist.append('(%s)' % ', '.join(rows))
        return '[%s]' % (', '.join(formatlist))

    def __repr__(self):
        r"""
            Returns:
                str:
        """
        return self.__str__()

    def __add__(self, other):
        r"""
            Args:
                other (FMatrix):
                
            Returns:
                FMatrix:
        """
        if not isinstance(other, self.__class__):
            self.__operandError('+', other)
        return self.__class__(
            [x + y for x, y in zip(self.asList(), other.asList())]
        )
    
    def __sub__(self, other):
        r"""
            Args:
                other (FMatrix):
                
            Returns:
                FMatrix:
        """
        if not isinstance(other, self.__class__):
            self.__operandError('-', other)
        return self.__class__(
            [x - y for x, y in zip(self.asList(), other.asList())]
        )

    def __mul__(self, other):
        r"""
            Args:
                other (FMatrix or float):
                
            Returns:
                FMatrix:
        """
        if isinstance(other, (int, float)):
            return self.__class__(
                [x * other for x in self.asList()]
            )
        elif isinstance(other, self.__class__):
            return self.multiply(other)
        else:
            self.__operandError('*', other)

    def __eq__(self, other):
        r"""
            Args:
                other (FMatrix):
                
            Returns:
                bool:
        """
        if not isinstance(other, self.__class__):
            return False
        for x, y in zip(self.asList(), other.asList()):
            if abs(x - y) > self.__comparingThreshold:
                return False
        return True

    def setComparingThreshold(self, threshold):
        r"""
            比較を行う時の誤差範囲を設定するメソッド。
            
            Args:
                threshold (float):
        """
        self.__comparingThreshold = threshold

    def comparingThreshold(self):
        r"""
            比較を行う時の誤差範囲を返すメソッド。
            
            Returns:
                float:
        """
        return self.__comparingThreshold

    def columns(self):
        r"""
            各列をリストとして返すメソッド。
            
            Returns:
                list:
        """
        return [
            [
                self.__elements[y * self.MatrixSize + x]
                for x in range(self.MatrixSize)
            ]
            for y in range(self.MatrixSize)
        ]

    def rows(self):
        r"""
            各行をリストとして返すメソッド。
            
            Returns:
                list:
        """
        return [
            [
                self.__elements[x * self.MatrixSize + y]
                for x in range(self.MatrixSize)
            ]
            for y in range(self.MatrixSize)
        ]

    def printMatrix(self):
        r"""
            行列情報を見やすい形で表示する。
        """
        padding = max([len(str(x)) for x in self.__elements])
        columns = self.columns()
        texts = []
        for col in columns:
            texts.append(', '.join([str(x).ljust(padding) for x in col]))
        print('\n'.join(texts))

    def element(self, column, row):
        r"""
            指定された列、行番号に任意の値を返す。
            
            Args:
                column (int):列番号
                row (int):行番号
                
            Returns:
                float:
        """
        return self.__elements[self.MatrixSize * column + row]

    def setElement(self, column, row, value):
        r"""
            指定された列、行番号に任意の値を設定する。
            
            Args:
                column (int):列番号
                row (int):行番号
                value (float):整数
        """
        self.__elements[self.MatrixSize * column + row] = float(value)

    def asList(self):
        r"""
            行列の１６個の要素を持つリストを返す。
            
            Returns:
                list:
        """
        return self.__elements[:]

    def multiply(self, matrix):
        r"""
            行列の乗算の結果を返す。
            
            Args:
                matrix (FMatrix):
                
            Returns:
                FMatrix:
        """
        newElements = []
        cols = self.columns()
        rows = matrix.rows()

        return self.__class__(
            [sum([x * y for x, y in zip(col, row)])
                for col in cols for row in rows
            ]
        )

    def inverseMatrix(self):
        r"""
            逆行列を返す。
            
            Returns:
                FMatrix:
        """
        oMtx = self.columns()
        iMtx = self.__class__().columns()
        n = range(self.MatrixSize)

        # Gauss-Jordan method.-------------------------------------------------
        for k in n:
            # Selects pivot. then the element on (k, k) will be a max value.
            max = k
            for j in range(k+1, self.MatrixSize):
                if abs(oMtx[j][k]) > abs(oMtx[max][k]):
                    max = j

            # Swaps a column.
            if max != k:
                for i in n:
                    tmp = oMtx[max][i]
                    oMtx[max][i] = oMtx[k][i]
                    oMtx[k][i] = tmp
                    
                    tmp = iMtx[max][i]
                    iMtx[max][i] = iMtx[k][i]
                    iMtx[k][i] = tmp

            # Changes a value of an element on (k, k) to 1.
            tmp = oMtx[k][k]
            for i in n:
                oMtx[k][i] /= tmp
                iMtx[k][i] /= tmp

            # Changes a values of an elements with the exception of the
            # element on (k, k) to 0.
            for j in n:
                if j == k:
                    continue
                tmp = oMtx[j][k] / oMtx[k][k]
                for i in n:
                    oMtx[j][i] = oMtx[j][i] - oMtx[k][i] * tmp
                    iMtx[j][i] = iMtx[j][i] - iMtx[k][i] * tmp
        # ---------------------------------------------------------------------
        
        newElements = []
        for elm in iMtx:
            newElements.extend(elm)
        return self.__class__(newElements)

    def setTranslate(self, x=0.0, y=0.0, z=0.0):
        r"""
            この行列のオフセット値（移動値）を設定する。
            
            Args:
                z (float):
                x (float):
                y (float):
        """
        self.__elements[12] = x
        self.__elements[13] = y
        self.__elements[14] = z

    def translate(self):
        r"""
            行列のオフセット値（移動値）を表す3つのfloatを持つlistを返す。
            
            Returns:
                list:
        """
        return self.__elements[12:15]

    def isIdentify(self):
        r"""
            初期状態かどうかを返す
            
            Returns:
                bool:
        """
        return self == self.__class__()

# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////