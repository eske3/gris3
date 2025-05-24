#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    コントローラに関する便利関数を収録したモジュール。
    
    Dates:
        date:2017/07/19 21:49[Eske](eske3g@gmail.com)
        update:2020/07/16 15:50 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import re
from gris3 import node, system

class DefaultAttrManager(object):
    r"""
        コントローラーのデフォルト値に関する管理を行なうクラス。
    """
    StoredAttrName = '__gris_default_attr_values__'
    StoredMatrixAttrNames = (
        '__gris_default_local_matrix__', '__gris_default_world_matrix__'
    )
    def __init__(self, nodeObject):
        r"""
            Args:
                nodeObject (str):対象ノード名
        """
        self.__obj = node.AbstractNode(nodeObject)
    
    def nodeObject(self):
        r"""
            初期化時に登録されたAbstractNodeインスタンスを返す。
            
            Returns:
                node.AbstractNode:
        """
        return self.__obj

    def setDefault(self):
        r"""
            keyableなアトリビュートの現在の値をデフォルト値として保存する。
        """
        obj = self.nodeObject()
        data = [
           x.attrName() + '=' + str(x.get())
           for x in obj.listAttr(k=True, s=True) if not x.isArray()
        ]
        if not data:
            # 特に記憶するデータがない場合で、かつ保持用アトリビュートが
            # ある場合は削除する。
            if obj.hasAttr(self.StoredAttrName):
                self.deleteAttr(self.StoredAttrName)
        else:
            if not obj.hasAttr(self.StoredAttrName):
                obj.addStringAttr(self.StoredAttrName, l=True)
            obj.editAttr(self.StoredAttrName, l=False)
            obj(self.StoredAttrName, ';'.join(data), type='string')
            obj.editAttr(self.StoredAttrName, l=True)

        if (
            not obj.isDag()
            or not obj.hasAttr('matrix')
            or not obj.hasAttr('worldMatrix')
        ):
            return
        # このノードがDagNodeの場合はマトリクスを保持する。
        for attr, stored in zip(
            ('matrix', 'worldMatrix'), self.StoredMatrixAttrNames
        ):
            if not obj.hasAttr(stored):
                obj.addMatrixAttr(stored)
            obj(stored, obj(attr), type='matrix')

    def listStoredData(self):
        r"""
            任意のノードに保持されているアトリビュートと値をセットで持つ
            リストを格納したリストを返す。
        """
        casttable = {'True':True, 'False':False}
        obj = self.nodeObject()
        if not obj.hasAttr(self.StoredAttrName):
            return []
        castdata = lambda x, y : (
            x, casttable[y] if y in casttable else float(y)
        )
        return [
            castdata(*y.split('='))
            for y in obj(self.StoredAttrName).split(';')
        ]

    def listStoredMatrixes(self):
        r"""
            DAGノード限定で保持さているローカルとワールドのマトリクス
            をリストで返す。
            
            Returns:
                list:
        """
        obj = self.nodeObject()
        result = []
        for attr in self.StoredMatrixAttrNames:
            if not obj.hasAttr(attr):
                return
            result.append(obj(attr))
        return result

    def restoreData(self, filter='.*'):
        r"""
            保持されているデータを元にデータを戻す。
            
            Args:
                filter (str):対象アトリビュートを定義する正規表現文字列
        """
        filter_ptn = re.compile(filter)
        error_reports = []
        obj = self.nodeObject()
        data = self.listStoredData()
        if not data:
            return
        for attr, value in data:
            if not filter_ptn.search(attr):
                continue
            try:
                obj(attr, value)
            except Exception as e:
                error_reports.append((attr, e.args[0]))
        if error_reports:
            print(
                'Errors found in storing a data to attributes below. : %s' % (
                    obj()
                )
            )
            for error in error_reports:
                print('    [%s] %s' % (error[0], error[1]))

def restoreToDefault(nodelist=None, filter='.*'):
    r"""
        選択ノード（または引数nodelistで指定されたノードのリスト）に
        対し登録されているデフォルト状態へ復元する。
        
        Args:
            nodelist (list):
            filter (str):
    """
    nodelist = node.selected(nodelist)
    for n in nodelist:
        m = DefaultAttrManager(n)
        m.restoreData(filter)

def __reverseCtrl():
    r"""
        暫定ミラーツール。検証用
    """
    name = system.GlobalSys().nameRule()
    attrlist = 'trs'
    factorlist = (-1, 1, 1)
    for ctrl in node.selected():
        n = name(ctrl)
        opp = node.asObject(n.mirroredName())
        if not opp:
            continue

        for at, f in zip(attrlist, factorlist):
            srcv = ctrl(at)[0]
            dstv = opp(at)[0]
            ctrl(at, [f*x for x in dstv])
            opp(at, [f*x for x in srcv])
