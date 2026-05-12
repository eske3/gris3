#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    レンダーセットアップのフローを自動化する機能を提供する。
    
    Dates:
        date:2022/08/06 14:42 Eske Yoshinob[eske3g@gmail.com]
        update:2022/08/06 15:12 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2022 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import re
from maya.app.renderSetup.model import renderSetup
from maya.app.renderSetup.model import selector
from maya.app.renderSetup.model import typeIDs
from maya import cmds, mel

from gris3 import node

def mel_setup():
    if mel.eval('whatIs applyPresetToNode').startswith('Mel procedure'):
        return
    mel.eval('source "others/presetMenuForDir.mel";')


def createCollection(obj, name, ptn=None):
    r"""
        与えられたコレクション[obj]にコレクションを追加する。
        既に該当する名前のコレクションがある場合は、作成せずにその
        コレクションを返す。

        Args:
            obj (maya.app.renderSetup.model.renderLayer.RenderLayer):
            name (str):
            ptn (_sre.SRE_Pattern):
    """
    if not ptn:
        ptn = re.compile(name+'\d*$')
    clist = obj.getCollections()
    for c in clist:
        if ptn.match(c.name()):
            return c
    return obj.createCollection(name)


def setupRenderLayers(
    layer_types, startIndexOfShaderOverwrite=1
):
    r"""
        Args:
            layer_types (list):レンダーレイヤー名のリスト
            startIndexOfShaderOverwrite (int):shaderOverrideを開始する番号
            
        Returns:
            dict:作成されたレイヤーの情報。
    """
    # レンダーレイヤーの作成。=================================================
    r_setup = renderSetup.instance()
    layers = []
    collections = []
    shader_collections = []
    shader_overrides = []
    for i in range(startIndexOfShaderOverwrite):
        shader_collections.append(None)
        shader_overrides.append(None)

    # レイヤーの作成。
    for name in layer_types:
        try:
            l = r_setup.getRenderLayer(name)
        except Exception as e:
            layers.append(r_setup.createRenderLayer(name))
        else:
            layers.append(l)

    # コレクションの作成。
    basename = 'modelCollection'
    ptn = re.compile(basename+'\d*$')
    for l in layers:
        collections.append(createCollection(l, basename, ptn))

    # シェーダー上書きコレクションの作成。
    basename = 'shaderCollection'
    ptn = re.compile(basename+'[\d]*$')
    s_basename = 'shaderOverride'
    s_ptn = re.compile(s_basename+'[\d]*$')
    for collection in collections[startIndexOfShaderOverwrite:]:
        # コレクションの設定
        override_c = createCollection(collection, basename, ptn)
        sel = override_c.getSelector()
        sel.setPattern('*')
        sel.setFilterType(selector.Filters.kShadingEngines)
        shader_collections.append(override_c)
        
        # オーバーライドの設定。
        overrides = override_c.getOverrides()
        for over in overrides:
            if s_ptn.search(over.name()):
                shader_overrides.append(over)
                break
        else:
            over = override_c.createOverride(
                'shaderOverride', typeIDs.shaderOverride
            )
            shader_overrides.append(over)
    # =========================================================================

    data = {}
    for typ, layer, col, s_col, over in zip(
        layer_types, layers, collections, shader_collections, shader_overrides
    ):
        data[typ] = {
            'layer':layer, 'collection':col, 'shaderOverride':(s_col, over)
        }
    return data


def createMetalAndShadingShader(*presetNames):
    new_shaders = []
    for basename in presetNames:
        name = basename + '_pxrSrf'
        shader = node.asObject(name)
        if shader:
            new_shaders.append((basename, shader))
            continue
        shader = node.shadingNode(
            'PxrSurface', asShader=True, n=basename+'_pxrSrf'
        )
        sets = cmds.sets(
            renderable=True, noSurfaceShader=True, empty=True, name=basename+'_sg'
        )
        shader.attr('outColor') >> (sets+'.surfaceShader')
        shader.attr('outColor') >> (sets+'.rman__surface')
        new_shaders.append((basename, shader))

    mel_setup()
    for preset, shader_info in zip(presetNames, new_shaders):
        mel.eval(
            'applyPresetToNode "{}" "" "" "{}" 1;'.format(
                shader_info[1], preset
            )
        )
    return new_shaders


def setupMechaRenders(*presetNames):
    shaders = createMetalAndShadingShader(*presetNames)
    data = setupRenderLayers(['color']+[x[0] for x in shaders])
    for name, shader in shaders:
        over = data[name]['shaderOverride'][1]
        over.setShader(shader())

    cmds.select([x[1] for x in shaders])
    return data

#setupMechaRenders('metal', 'shading')


'''
# 追加例：シェーダーマスク用のレイヤー作成パターン。
import re
from gris3 import node
from materialManager import renderSetup

# 作成したいレイヤー名のリスト。
layers = [
    'gold', 'lightGold', 'darkGold',
    'extraGold', 'extraLightGold', 'extraDarkGold',
    'purple', 'lightPurple',
    'extraPurple', 'extraLightPurple',
    'clearRed', 'clearBlue', 'clearYellow', 'clearPurple'
]

with node.DoCommand():
    data = renderSetup.setupRenderLayers([x+'Mask' for x in layers], 0)
    for type_name, d in data.items():
        d['shaderOverride'][1].setShader('maskWhite_pxrCst')
        layer = d['layer']
        basename = 'blackMaskCollection'
        ptn = re.compile(basename+'\d*$')
        collection = renderSetup.createCollection(layer, basename, ptn)

        basename = 'shaderBlackMaskCollection'
        ptn = re.compile(basename+'[\d]*$')
        s_basename = 'shaderBlackMaskOverride'
        s_ptn = re.compile(s_basename+'[\d]*$')
        override_c = renderSetup.createCollection(collection, basename, ptn)
        sel = override_c.getSelector()
        sel.setPattern('*')
        sel.setFilterType(renderSetup.selector.Filters.kShadingEngines)
        
        # オーバーライドの設定。
        over = override_c.createOverride(
            'shaderOverride', renderSetup.typeIDs.shaderOverride
        )
        over.setShader('maskBlack_pxrCst')



# 任意のマテリアルにアサインされているオブジェクトを選択する。=================
# シーン中のSGを全て取得する。
from maya import cmds
from gris3 import node
sglist = []
for mat in node.ls(type='PxrSurface'):
    sglist.extend(mat.attr('outColor').destinations(type='shadingEngine'))

# 選択マテリアルにアサインされているオブジェクトを選択。
mat = node.selected()
sgs = []
for m in mat:
    sgs.extend(m.attr('outColor').destinations(type='shadingEngine'))
cmds.select(sgs)
cmds.select([x.parent() for x in node.selected()])

# それ以外のオブジェクトを選択。
cmds.select(sglist)
cmds.select(sgs, d=True)
cmds.select([x.parent() for x in node.selected()])
# =============================================================================
'''