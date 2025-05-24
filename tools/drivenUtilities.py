# -*- coding: utf-8 -*-
r'''
    @file     drivenUtilities.py
    @brief    ドリブンキーに関する便利機能を提供するモジュール。
    @function hasDriven : ここに説明文を記入
    @function mirrorDriven : 選択しているL側のドリブンキーをR側に移植する。
    @function selectDrivenNode : 選択されたノード下にあるDrivenKeyのついているノードを返す。
    @date        2017/02/13 23:56[Eske](eske3g@gmail.com)
    @update      2017/09/03 23:07[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
import re
from gris3 import node
cmds = node.cmds

def hasDriven(obj):
    r'''
        @brief  ドリブンキーが入っているノードかどうかを判定する関数。
        @param  obj : [node.AbstractNode]
        @return bool
    '''
    anm_crv = obj.sources(scn=True)
    anm_crv = cmds.ls(
        anm_crv, type=[
            'animCurveUA', 'animCurveUL', 'animCurveUT', 'animCurveUU',
            'blendWeighted',
        ]
    )
    return True if anm_crv else False

def copyDrivenNetworks(attr):
    r'''
        @brief  引数attrに接続されているドリブンのノードネットワークをコピー
        @brief  する関数。
        @brief  戻り値は辞書で以下の情報を持つ
        @brief  inputPlugs
        @brief    ドライバの受けとなるカーブの入力アトリビュートをキーとし
        @brief    元々接続されていたドライバの出力アトリビュート名を値とする
        @brief    辞書
        @brief  outPlugs:
        @brief    ドリブンノードに接続する出力アトリビュート
        @param  attr : [node.Attribute]ドリブンアトリビュート
        @return dict
    '''
    blend_weighted = attr.source(type='blendWeighted')
    if blend_weighted:
        anim_curves = node.sources(
            blend_weighted/'input', type='animCurve'
        )
        if not anim_curves:
            return
    else:
        anim_curve = attr.source(type='animCurve')
        if not anim_curve:
            return
        anim_curves = [anim_curve]
    out_plugs = []
    input_plugs = {}
    new_curves = []
    for anim_curve in anim_curves:
        driver = anim_curve.attr('input').source(p=True)
        if not driver:
            continue
        new_curve = node.duplicate(anim_curve(), rc=True)[0]
        out_plugs.append(new_curve.attr('output'))
        input_plugs[new_curve.attr('input')] = driver()
    if not out_plugs:
        return
    if blend_weighted:
        new_blender = node.duplicate(blend_weighted, rc=True)[0]
        for i, plug in enumerate(out_plugs):
            plug >> '{}.input[{}]'.format(new_blender, i)
        out_plug = new_blender.attr('output')
    else:
        out_plug = out_plugs[0]
    result = {'inputPlugs':input_plugs, 'outPlug':out_plug}
    return result

def mirrorDriven(targets=None):
    r'''
        @brief  選択しているL側のドリブンキーをR側に移植する。
        @param  targets(None) : [list]
        @return None
    '''
    from gris3 import system
    scaled_attr = re.compile('translate[XYZ]')
    name_rule = system.GlobalSys().nameRule()
    result = []
    for n in [x for x in node.selected(targets) if hasDriven(x)]:
        name = name_rule(n)
        rev_node = name.mirroredName()
        if not rev_node:
            continue
        rev_node = node.asObject(rev_node())
        if not rev_node:
            continue

        result_texts = [
            '/' * 80, '# Copy to %s' % rev_node,
        ]
        for attr in n.listAttr(k=True):
            # blendWeightedがあるかどうかの確認。
            blend_weighted = attr.source(type='blendWeighted', scn=True)
            if blend_weighted:
                anim_curves = node.sources(
                    blend_weighted/'input', type='animCurve', scn=True
                )
                if not anim_curves:
                    continue
            else:
                anim_curve = attr.source(type='animCurve')
                if not anim_curve:
                    continue
                anim_curves = [anim_curve]

            attr_name = attr.attrName()
            out_plugs = []
            for anim_curve in anim_curves:
                driver = anim_curve.attr('input').source(p=True, scn=True)
                if not driver:
                    continue
                driver_name = name_rule(driver.nodeName())
                driver_name = driver_name.mirroredName()
                if not driver_name:
                    driver_name = driver.nodeName()
                    float_scale = -1.0
                else:
                    driver_name = driver_name()
                    float_scale = 1.0
                if not cmds.objExists(driver_name):
                    continue
                driver_attr = driver_name + '.' + driver.attrName()

                new_curve = node.rename(
                    cmds.duplicate(anim_curve(), rc=True)[0],
                    rev_node + '_' + attr_name
                )
                result_texts.append('    Copy Attr: %s' % attr_name)
                result_texts.append('    Driver : %s' % driver_attr)

                driver_attr >> new_curve.attr('input')
                # new_curve.attr('output') >> rev_node/attr_name
                out_plugs.append(new_curve.attr('output'))
                if scaled_attr.search(attr()):
                    result_texts.append(
                        "    Attribute's value was negative scaled."
                    )
                    result_texts.append('    Float Scaling : %s' % float_scale)
                    cmds.scaleKey(
                        new_curve,
                        scaleSpecifiedKeys=1,
                        timeScale=1, timePivot=0,
                        floatScale=float_scale, floatPivot=0,
                        valueScale=-1, valuePivot=0,
                        hierarchy='none', controlPoints=0, shape=0
                    )
                result.append(rev_node())
            if not out_plugs:
                continue
            if blend_weighted:
                new_blender = node.asObject(cmds.duplicate(blend_weighted)[0])
                for i, plug in enumerate(out_plugs):
                    plug >> '{}.input[{}]'.format(new_blender, i)
                out_plug = new_blender.attr('output')
            else:
                out_plug = out_plugs[0]
            out_plug >> rev_node/attr_name
        result_texts.append(('/' * 80) + '\n')
        print('\n'.join(result_texts))
    if result:
        cmds.select(result, ne=True, r=True)


def selectDrivenNode(topNodes=None, isSelecting=False):
    r'''
        @brief  選択されたノード下にあるDrivenKeyのついているノードを返す。
        @brief  引数isSelectingがTrueの場合は選択も行う。
        @param  topNodes(None) : [list]
        @param  isSelecting(False) : [edit]
        @return list
    '''
    topNodes = node.selected(topNodes)
    if not topNodes:
        raise RuntimeError('No object were specified.')

    all_nodes = []
    for n in topNodes:
        all_nodes.extend(n.allChildren())

    result = []
    for n in all_nodes:
        if not hasDriven(n):
            continue
        result.append(n)

    if result and isSelecting:
        cmds.select(result, r=True)
    else:
        cmds.select(cl=True)
    return result
