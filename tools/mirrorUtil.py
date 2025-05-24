#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    モーションのミラーを行う機能を提供するモジュール。
    現在は仮実装。
    
    Dates:
        date:2023/08/18 17:30 Eske Yoshinob[eske3g@gmail.com]
        update:2024/02/03 14:08 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2023 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import re
from .. import node
from . import selectionUtil
cmds = node.cmds

StandaloneTrs = {
    '0DEFAULT': ((1, 1, 1), (-1, -1, -1), (1, 1, 1)),
    
    ('spineIk_ctrl_C', 'spineHipIk_ctrl_C'):
    ((-1, 1, 1), (1, -1, -1), (1, 1, 1)),

    ('spineHip_ctrl_C', ):((-1, 1, 1), (1, -1, -1), (1, 1, 1)),
    re.compile('spine[A-Z]+_ctrl_C'):((1, 1, 1), (-1, 1, -1), (1, 1, 1)),
    ('spineHipShake_ctrl_C', 'headNeck_ctrl_C', 'head_ctrl_C'):
    ((1, -1, 1), (-1, 1, -1), (1, 1, 1)),
}
PairTrs = {
    '0DEFAULT': ((-1, -1, -1), (1, 1, 1), (1, 1, 1)),
    ('armIk_ctrl', 'legIk_ctrl'): ((-1, 1, 1), (1, -1, -1), (1, 1, 1)),
}
LR_PTN = re.compile('_[LR]$')


def getName(name):
    r"""
        与えられた名前nameのネームスペースなどを削除し、位置を表す文字列L/Rを
        削除した状態のものを返す。

        Args:
            name (str):
        
        Returns:
            str:
    """
    splited = name.rsplit(':', -1)[-1]
    if not LR_PTN.search(name):
        return splited
    return LR_PTN.sub('', splited)


def swap(nodelist=None, isMirror=False):
    r"""
        対象コントローラのポーズをスワップ、またはミラーリングする。

        Args:
            nodelist (list):操作対象ノードのリスト
            isMirror (bool):Trueの場合Mirror
            reducePairNodes (bool):ペアとなるノードが重複している場合、統一する
    """
    def getFactors(target, factorDic):
        r"""
            Args:
                target (node.AbstractNode):
                factorDic (dict):
        """
        sn = getName(target)
        re_typ = type(re.compile('a'))
        for key, factors in factorDic.items():
            if isinstance(key, re_typ):
                if not key.search(sn):
                    continue
            elif sn not in key:
                continue
            return factorDic[key]
        else:
            return factorDic['0DEFAULT']

    def swapValue(tgtA, tgtB, attr, factor, isMirror):
        r"""
            Args:
                tgtA (node.AbstractNode):
                tgtB (node.AbstractNode):
                attr (str):
                factor (float):
                isMirror (bool):
        """
        a_val = tgtA(attr)
        if not isMirror:
            b_val = tgtB(attr)
            tgtA(attr, b_val * factor)
        tgtB(attr, a_val * factor)

    nodelist = node.selected(nodelist)
    pairlist = {}
    standalones = []
    for n in nodelist:
        r = LR_PTN.search(n)
        if not r:
            standalones.append(n)
            continue
        substr = '_R' if r.group() == '_L' else '_L'
        rev = LR_PTN.sub(substr, n)
        rev = node.asObject(rev)
        if not rev:
            continue
        if rev in pairlist:
            continue
        pairlist[n] = rev
    
    # シングルノードのミラー処理。=============================================
    for n in standalones:
        factorlist = getFactors(n, StandaloneTrs)
        for attr, factor in zip('trs', factorlist):
            for ax, f in zip('xyz', factor):
                at = attr + ax
                if not n(at, k=True) or n(at, l=True):
                    continue
                n(at, n(at) * f)
    # =========================================================================
    
    # =========================================================================
    for tgt_a, tgt_b in pairlist.items():
        a_attrs = set(cmds.listAttr(tgt_a, k=True, sn=True, s=True))
        b_attrs = set(cmds.listAttr(tgt_b, k=True, sn=True, s=True))
        matching_attrs = list(a_attrs & b_attrs)
        if not matching_attrs:
            continue
        factorlist = getFactors(tgt_a, PairTrs)
        a_values, b_values = {}, {}
        for attr, factor in zip('trs', factorlist):
            for ax, f in zip('xyz', factor):
                at = attr + ax
                if at not in matching_attrs:
                    continue
                swapValue(tgt_a, tgt_b, at, f, isMirror)
                del matching_attrs[matching_attrs.index(at)]
        for attr in matching_attrs:
            swapValue(tgt_a, tgt_b, attr, 1, isMirror)
    # =========================================================================
