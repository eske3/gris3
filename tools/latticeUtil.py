#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    lattice用のユーティリティを持つモジュール
    
    Dates:
        date:2018/01/20 9:00[Eske](eske3g@gmail.com)
        update:2024/02/16 13:40 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2018 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import json
from ... import node, verutil
cmds =  node.cmds

def asDataList(latticeList=None):
    r"""
        任意のlatticeを書き出せる情報に変換する。
        
        Args:
            latticeList (list):書き出すLatticeのリスト
            
        Returns:
            list:
    """
    latticeList = [
        x for x in node.selected(latticeList, dag=True, type='lattice')
        if not x('io')
    ]
    data = []
    for lattice in latticeList:
        # FFDを検出し、見つからない場合は終了。
        ffd = lattice.attr('latticeOutput').destinations(type='ffd')
        if not ffd:
            continue
        ffd = ffd[0]

        # 適応先のノードを検出し、見つからない場合は終了。
        target = ffd.attr('outputGeometry[0]').destinations()
        if not target:
            continue

        # FFDに繋がったbaseを検出し、見つからない場合は終了。
        base = ffd.attr('baseLatticeMatrix').source(shapes=True)
        if not base:
            continue

        lat_trs = lattice.parent()  # latticeの親トランスフォームノード
        base_trs = base.parent()    # baseの親トランスフォームノード
        l_data = {}
        trs_data = {}
        # ノードのアトリビュートを収集してくる。===============================
        for n, keyword, attrlist, tgt_dict in (
            (
                ffd, 'ffd', (
                    'local',
                    'localInfluenceS', 'localInfluenceT', 'localInfluenceU',
                    'outsideLattice', 'outsideFalloffDist',
                    'usePartialResolution', 'partialResolution',
                    'envelope'
                ),
                l_data
            ),
            (
                lattice, 'lattice', (
                    'sDivisions', 'tDivisions', 'uDivisions'
                ),
                l_data
            ),
            (
                lat_trs, 'latticeTrs', ('matrix', 'worldMatrix'), trs_data
            ),
            (
                base_trs, 'baseTrs', ('matrix', 'worldMatrix'), trs_data
            ),
        ):
            tgt_dict[keyword] = {
                'name' : n(),
                'attr' : {x : n(x) for x in attrlist}
            }
        # =====================================================================

        # latticeShapeのポイント値を収集してくる。=============================
        points = {}
        for s in range(lattice('sDivisions')):
            for t in range(lattice('tDivisions')):
                for u in range(lattice('uDivisions')):
                    attr = 'pt[%s][%s][%s]'%(s, t, u)
                    pt = lattice(attr)[0]
                    points[attr] = pt
        # =====================================================================

        data.append(
            {
                'target':target[0](), 'shape':l_data, 'transform':trs_data,
                'points':points
            }
        )
    return data


def asDataText(latticeList=None):
    r"""
        asDataListと同様lattice情報を返す。こちらはテキストで返す。
        
        Args:
            latticeList (list):
            
        Returns:
            str:
    """
    return json.dumps(asDataList(latticeList))


def restoreFromData(dataList, retargetList=None):
    r"""
        asDataList関数で変換されたlattice情報を元に再構築する。
        引数retargetListにはdataと同じ数のノード名のリストを渡せる。
        data内と同時にretargetListも呼び出され、retargetListの
        オブジェクトにlatticeが適応される。
        
        Args:
            dataList (list):asData関数で生成されたリストオブジェクト
            retargetList (list):
    """
    if isinstance(dataList, verutil.BaseString):
        dataList = json.loads(dataList)

    if not retargetList:
        retargetList = [x['target'] for x in dataList]

    for data, target in zip(dataList, retargetList):
        target = node.asObject(target)
        if not target:
            continue
        ffd, lat, base = node.toObjects(cmds.lattice(target))
        lat_shape = lat.children(type='lattice')[0]
        base_shape = base.children(type='baseLattice')[0]

        # transformの復元。
        for trs, keyword in ((lat, 'latticeTrs'), (base, 'baseTrs')):
            trs.setMatrix(data['transform'][keyword]['attr']['worldMatrix'])
            trs.rename(data['transform'][keyword]['name'])

        # 各種アトリビュートの復元。
        for n in (ffd, lat_shape):
            d = data['shape'][n.type()]['attr']
            for attr, value in d.items():
                n(attr, value)
            ffd.rename(data['shape'][n.type()]['name'])




'''
# Ex.
import traceback
from pprint import pprint
try:
    from gris3.tools import latticeUtil
    reload(latticeUtil)
    #datalist = latticeUtil.asDataList(['ffd1LatticeShape'])
    datatext = latticeUtil.asDataText(['ffd1LatticeShape'])
    latticeUtil.restoreFromData(datalist)
    latticeUtil.restoreFromData(datatext)
except:
    traceback.print_exc()

latticeUtil.asDataText()
'''
