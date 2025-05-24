#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2024/08/26 11:39 Eske Yoshinob[eske3g@gmail.com]
        update:2025/04/01 13:26 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from collections import OrderedDict
import json
from .. import node, grisNode

cmds = node.cmds
Version = '1.0.0'
GroupPrefix = '__grsFacialMemoryGrp__'
TagAttr = '__grsFacialName__'


def listBlendShapeValues(blendShapeName, removeZeroValue=True):
    r"""
        引数blendShapeNameのフェイシャル用アトリビュート名とその値をセットに
        して返す。
        戻り値はOrderedDictで、
            キーにアトリビュート名
            値にはそのアトリビュートの現在の値
        の状態で、blendShapeノードのアトリビュート順に格納されている。
        
        Args:
            blendShapeName (str):
            removeZeroValue (bool):
            
        Returns:
            OrderedDict:
    """
    bs = node.asObject(blendShapeName)
    datalist = OrderedDict()
    for attr in bs.listAttrNames():
        value = bs(attr)
        if removeZeroValue and value == 0:
            continue
        datalist[attr] = value
    return datalist


class FacialMemoryManagerRoot(grisNode.AbstractTopGroup):
    r"""
        セットアップデータを格納するgroupに関するクラス
    """
    BasicName = 'grsFacialMemory'
    NodeType = 'geometryVarGroup'
    BasicAttrs = [
        (
            {'ln':'grsFacialMemoryVersion', 'dt':'string'}, {'l':True},
            [Version, {'type':'string'}]
        ),
        (
            {'ln':'grsFacialBlendShapeName', 'dt':'string'}, {'l':True}, None
        ),
        (
            # 同一シーン内に複数のマネージャがあった場合の管理用タグ。
            # 現在は未使用。
            {'ln':'grsFacialBlendShapeTag', 'dt':'string'}, {'l':True}, None
        )
    ]
    def __init__(self, nodeName):
        super(FacialMemoryManagerRoot, self).__init__()
        self.__data_cache = None

    def setBlendShapeName(self, blendShapeName):
        r"""
            操作対象となるブレンドシェイプ名を設定する。
            
            Args:
                blendShapeName (str):
        """
        with self.attr('grsFacialBlendShapeName') as attr:
            attr.set(blendShapeName)

    def blendShapeName(self):
        r"""
            設定されている操作対象となるブレンドシェイプ名を返す。
            
            Returns:
                str:
        """
        return self('grsFacialBlendShapeName')

    def blendShape(self):
        r"""
            設定されている操作対象ブレンドシェイプをオブジェクト形式で返す。
            
            Returns:
                node.BlendShape:
        """
        return node.asObject(self.blendShapeName())

    def listExpressions(self):
        r"""
            このノードが保持する表情データノートのリストを返す。
            戻り値はOrderedDictで、表情名をキーとし、それに対応するTransformを
            値とする。
            
            Returns:
                OrderedDict:
        """
        datalist = grisNode.listNodes(
            DataTransform, self.children(type='transform')
        )
        result = OrderedDict()
        for x in datalist:
            result[x.expression()] = x
        return result

    def listExpressionData(self, useCache=False):
        r"""
            このノードが保持する表情データノートのリストを返す。
            戻り値は辞書型で、表情名をキーとし、それに対応するblendShapeの
            アトリビュート名と値の辞書を値としたデータ。
            
            Returns:
                dict:
        """
        if useCache and self.__data_cache:
            return self.__data_cache
        expressions = self.listExpressions()
        datalist = OrderedDict()
        for exp, data in expressions.items():
            datalist[exp] = data.values()
        if useCache:
            self.__data_cache = datalist
        else:
            self.__data_cache = None
        return datalist

    def addExpression(self, expressionName):
        r"""
            引数expressionNameで指定された表情データを作成する。
            戻り値は作成された表情データ、DataTransform。
            既に表情データが存在する場合は、既存のデータを返す。
            
            Args:
                expressionName (str):
            
            Returns:
                DataTransform:
        """
        expressions = self.listExpressions()
        if expressionName in expressions:
            return expressions[expressionName]
        exp = grisNode.createNode(
            DataTransform, n='facialExpression#', p=self()
        )
        exp.setExpression(expressionName)
        return exp

    def setExpressionFromCurrentState(self, expression):
        r"""
            現在のblendShapeのアトリビュート値を用いて、引数expressionで
            指定した表情データとして登録する。
            
            Args:
                expression (str):設定したい表情名
        """
        bs_name = self.blendShapeName()
        if not bs_name:
            raise RuntimeError('No blend shape node specified.')
        values = listBlendShapeValues(bs_name)
        exp = self.addExpression(expression)
        exp.setValues(values)

    def clearExpressions(self):
        r"""
            保持する表情データノードをすべて破棄する。
        """
        datanodes = self.listExpressions().values()
        if datanodes:
            cmds.delete(list(datanodes))

    def removeExpression(self, expression):
        r"""
            引数expressionで指定した表情データを削除する。
            
            Args:
                expression (str):削除する表情名
        """
        datanodes = self.listExpressions()
        removed = datanodes.get(expresion)
        if removed:
            cmds.delete(removed)

    def setExpressionFromDataList(self, datalist):
        r"""
            引数datalistで指定した辞書データを元に、表情と対応値を一括設定する。
            datalistは
            　キー：表情名
            　値：表情に対応するblendShapeのアトリビュート名と値の辞書
            を持つ。
            
            Args:
                datalist (str):
        """
        for exp, data in datalist.items():
            exp = self.addExpression(exp)
            exp.setValues(data)

    def updateExpressionFromDataList(self, expressionlist):
        r"""
            引数expressionlistで指定された表情名のリストで更新を行う。
            expressionlist内に既存の表情があった場合、その値は保持する。
            既存の表情リストとexpressionlistが順番も含めて全く同じだった場合は
            何もせずに0を返す。
            それ以外の場合は1を返す。
            
            Args:
                expressionlist (list): 表情名のリスト
            
            Returns:
                int: 更新の必要がなかった場合は0を、更新された場合は1を返す。
        """
        datalist = self.listExpressionData()
        if datalist and len(expressionlist) == len(datalist):
            for n_exp, o_exp in zip(expressionlist, datalist.keys()):
                if n_exp != o_exp:
                    break
            else:
                return 0
        self.clearExpressions()
        new_data = OrderedDict()
        for exp in expressionlist:
            new_data[exp] = datalist.get(exp, None)
        self.setExpressionFromDataList(new_data)
        return 1
        
    def applyExpression(self, expression):
        r"""
            引数expressionで指定した表情パラメータをblendShapeに適用する。
            
            Args:
                expression (str):表情名
        """
        bs = self.blendShape()
        if not bs:
            return
        values = self.listExpressionData().get(expression)
        for attr in bs.listAttrNames():
            v = 0
            if values is None:
                continue
            if attr in values:
                v = values[attr]
            bs(attr, v)


class DataTransform(node.Transform, grisNode.AbstractGrisNode):
    r"""
        表情を構成するアトリビュート名と値の情報を持つデータを制御するクラス。
    """
    NodeType = 'transform'
    BasicAttrs = [
        ({'ln':TagAttr, 'dt':'string'}, {'l':True}, None),
        ({'ln':'grsExpressionValues', 'dt':'string'}, {'l':True}, None),
    ]

    def setExpression(self, expression):
        r"""
            表情名を設定する。

            Args:
                expression (str):
        """
        with self.attr(TagAttr) as attr:
            attr.set(expression)

    def expression(self):
        r"""
            設定されている表情名を返す。

            Returns:
                str:
        """
        return self(TagAttr)

    def setValues(self, datalist):
        r"""
            表情を構成するblendShapeのアトリビュート名と値を設定する。
            引数datalistは
                キー：blendShapeのアトリビュート名
                値：対応するアトリビュートの値
            とする辞書オブジェクト。

            Args:
                datalist (dict):
        """
        data_to_text = '' if datalist is None else json.dumps(datalist)
        with self.attr('grsExpressionValues') as attr:
            attr.set(data_to_text)

    def values(self):
        r"""
            表情を構成するblendShapeのアトリビュート名と値の辞書を返す。
            戻り値は
                キー：blendShapeのアトリビュート名
                値：対応するアトリビュートの値
            とする辞書オブジェクト。

            Returns:
                dict:
        """
        data_text = self('grsExpressionValues')
        if not data_text:
            return None
        data = json.loads(data_text)
        return data


def createManagerNode(parent=None):
    r"""
        フェイシャル情報を保持するノードを作成する。
        
        Args:
            parent (str):
    """
    root = grisNode.createNode(FacialMemoryManagerRoot, parent=parent)
    return root


def listManagerNode():
    r"""
        フェイシャル情報を保持するノードを返す。
        
        Returns:
            FacialMemoryManagerRoot:
    """
    root = grisNode.listNodes(FacialMemoryManagerRoot)
    if not root:
        return
    return root
