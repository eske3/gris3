#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    コントローラカーブを書き出す機能を提供するモジュール
    
    Dates:
        date:2017/01/21 12:05[Eske](eske3g@gmail.com)
        update:2022/07/17 15:39 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import datetime, re

from .. import mayaCmds as cmds
from ..exporter import core

if cmds.MAYA_VERSION < 2016:
    TranferedAttributes = [
        'overrideEnabled', 'overrideDisplayType', 'overrideLevelOfDetail',
        'overrideVisibility', 'overrideColor',
    ]
else:
    TranferedAttributes = [
        'overrideEnabled', 'overrideDisplayType', 'overrideLevelOfDetail',
        'overrideVisibility', 'useObjectColor', 'wireColorRGB',
    ]

RootName = '____CONTROL_CURVES____'

Attr = '.originalNodeName'

class Exporter(core.AbstractExporter):
    Extensions = ['ma']
    def __init__(self):
        super(Exporter, self).__init__()
        self.__exported_curves = []

    def setExportedNodes(self, nodes):
        r"""
            書き出すノードをセットする
            
            Args:
                nodes (list):
        """
        self.__exported_curves = []

        for node in [cmds.ls(nodes, transforms=True, shapes=True)]:
            nodetype = cmds.nodeType(node)
            if nodetype == 'nurbsCurve':
                self.__exported_curves.append(node)
                continue
            else:
                curves = cmds.listRelatives(
                    node, c=True, pa=True, type='nurbsCurve'
                )
                if curves:
                    self.__exported_curves.extend(curves)

    def exportedCurves(self):
        r"""
            書き出すカーブのリストを返す。
            
            Returns:
                list:
        """
        return self.__exported_curves

    def export(self):
        exported_curves = self.exportedCurves()
        finished = []
        if not exported_curves:
            raise RuntimeError('No nurbs curves were specified.')

        temporary = cmds.createNode('transform', n=RootName)
        for curve in exported_curves:
            name = curve.split('|')[-1]
            if name in finished:
                continue

            # Copy a curve shape from an original to a created.================
            shape = cmds.createNode('nurbsCurve', p=temporary)
            cmds.connectAttr(curve + '.local', shape + '.create')
            cmds.delete(shape, ch=True)
            # =================================================================

            # Copy a special attributes.=======================================
            for attr in TranferedAttributes:
                value = cmds.getAttr(curve + '.' + attr)
                if isinstance(value, (list, tuple)):
                    cmds.setAttr(shape + '.' + attr, *value[0])
                else:
                    cmds.setAttr(shape + '.' + attr, value)
            # =================================================================

            # Adds custom attr to memory a original node name.=================
            cmds.addAttr(shape, ln=Attr[1:], dt='string')
            cmds.setAttr(
                shape + Attr, name, type='string', l=True
            )
            # =================================================================
            
            #cmds.rename(shape, name)
            finished.append(name)

        cmds.select(temporary, r=True)
        result = cmds.file(
            self.exportPath(), es=True, f=True, type='mayaAscii',
            ch=False, chn=False, con=False, exp=False, sh=False
        )
        cmds.delete(temporary)
        # =====================================================================

def importCurveFile(filepath):
    r"""
        カーブをインポートする
        
        Args:
            filepath (str):入力ファイルパス
    """
    namespace = 'TEMPORARY_CURVE_NAME_%s' % datetime.datetime.now().strftime(
        '%Y%m%d%H%M%S'
    )
    cmds.file(filepath, i=True, ra=True, rpr=namespace)
    temporary = namespace + '_' + RootName
    if not cmds.objExists(temporary):
        raise RuntimeError('Specified file is not curve file.')
    
    for curve in cmds.listRelatives(
        temporary, c=True, type='nurbsCurve', pa=True
    ):
        node_name = cmds.getAttr(curve + Attr)
        for dstcurve in cmds.ls(node_name):
            srcattr = curve + '.local'
            dstattr = dstcurve + '.create'
            if cmds.listConnections(dstattr, s=True, d=False):
                continue

            cmds.connectAttr(srcattr, dstattr)
            cmds.delete(dstcurve, ch=True)

            for attr in TranferedAttributes:
                value = cmds.getAttr(curve + '.' + attr)
                if isinstance(value, (list, tuple)):
                    cmds.setAttr(dstcurve + '.' + attr, *value[0])
                else:
                    cmds.setAttr(dstcurve + '.' + attr, value)

    cmds.delete(temporary)

def listCtrlNames(filepath):
    r"""
        与えられたmaのファイルパス内にあるコントローラカーブ名のリストを返す。

        Args:
            filepath (str):検索対象ファイルパス（MayaAscii）

        Returns:
            list:
    """
    ptn = re.compile(
        'setAttr\s.*?"{}"\s.*?"string"\s"(.*?)";'.format(Attr)
    )
    text = ''
    shapelist = []
    with open(filepath, 'r') as f:
        while(True):
            text = f.readline()
            if not text:
                break
            r = ptn.search(text)
            if r:
                shapelist.append(r.group(1))
    return shapelist


def listCtrls(filepath):
    r"""
        与えられたmaのファイルパス内にあるコントローラのリストを返す。
        listCtrlSnamesと違い、こちらは親のTransform名を返す。
        （ただしシーン中に存在する場合）

        Args:
            filepath (str):検索対象ファイルパス（MayaAscii）

        Returns:
            list:
    """
    from gris3 import node
    results = []
    for shape in listCtrlNames(filepath):
        s = node.asObject(shape)
        results.append(s.parent()() if s else shape)
    return results