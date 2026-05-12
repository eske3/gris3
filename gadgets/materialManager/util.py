#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    マテリアル操作に関するユーティリティ
    
    Dates:
        date:2019/06/15 08:49[eske3g@gmail.com]
        update:2025/09/17 13:10 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2019 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
import math
from ... import node
from maya import cmds


def reassignShader():
    r"""
        Reference時に消えてしまったSGProxy接続を復帰させる。
    """
    from gris3 import node
    for sg in node.ls(type='shadingEngine'):
        if not sg.hasAttr('mm_shaderProxy'):
            continue
        proxy_plug = sg.attr('mm_shaderProxy')
        print('# %s' % sg)
        src_plug = sg.attr('surfaceShader')
        print('  -> Source plug : %s' % src_plug)
        src = src_plug.source()
        if not src:
            continue
        shader = node.ls(src.split('_')[0]+'*', type='lambert')
        if not shader:
            continue
        shader[0].attr('message') >> proxy_plug


def reassignShaderPfx():
    for sg in node.ls(type='shadingEngine'):
        if not sg.hasAttr('mm_shaderProxy'):
            continue
        proxy_plug = sg.attr('mm_shaderProxy')
        src_plug = sg.attr('surfaceShader')
        print(src_plug)
        src = src_plug.source()
        if not src:
            continue
        print('  => %s' % src)
        print('  => %s' % src.split('_')[0]+'*')
        shader = node.ls(src_plug.source().split('_')[0]+'*', type='PxrSurface')
        if not shader:
            continue
        shader[0].attr('message') >> proxy_plug


def assignShaderToRmanPlug():
    for sg in node.ls(type='shadingEngine'):
        if not sg.hasAttr('mm_shaderProxy'):
            continue
        plug = sg.attr('mm_shaderProxy')
        source = plug.source()
        if not source:
            continue
        plug.disconnect()
        source.attr('outColor') >> sg.attr('rman__surface')


def setupAlphaTexture(textureNode):
    r"""
        Args:
            textureNode (gris3.node.AbstractNode):enter description
            
        Returns:
            any:
    """
    textureNode('ail', True)


def doNothing(textureNode):
    r"""
        Args:
            textureNode (gris3.node.AbstractNode):
    """
    pass


TextureTypeTable = [
    (
        'nml', 'PxrNormalMap/filename/resultN', 'pxrNml',
        ['diffuseBumpNormal', 'specularBumpNormal'], doNothing
    ),
    (
        'rgh', 'file/ftn/outAlpha', 'fle',
        ['specularRoughness'], setupAlphaTexture
    ),
    (
        'spc', 'file/ftn/outColor', 'fle',
        ['specularFaceColor'], doNothing
    ),
]


def createAndConnectTexture(
    texPath, nodeinfo, mat, tag, targetAttrs, postAction, finishedTextures
):
    r"""
        enter description
        
        Args:
            texPath (str):テクスチャのパス
            nodeinfo (str):作成するノード、アトリビュート情報
            mat (any):(node.AbstractNode) : 操作対象PxrSurface
            tag (any):enter description
            targetAttrs (list):接続先のアトリビュート
            postAction (function):テクスチャ作成後に実行する関数
            finishedTextures (dict):処理済みノードのリスト
    """
    def searchTex(path, nodeType):
        r"""
            enter description
            
            Args:
                path (str):enter description
                nodeType (str):enter description
                
            Returns:
                any:
        """
        if not path in finishedTextures:
            return
        data = finishedTextures[path]
        if data['type'] != nodeType:
            return
        return data['plug']
        
    if not os.path.exists(texPath):
        return
    outplug = None
    nodetype, input_attr, output_attr = nodeinfo.split('/')
    for attr in targetAttrs:
        plug = mat.attr(attr)
        if plug.source():
            continue
        if not outplug:
            outplug = searchTex(texPath, nodetype)
            if not outplug:
                print('  + Create new texture node : %s' % texPath)
                basename = mat.split('_')[0]
                tex_node = node.asObject(
                    cmds.shadingNode(
                        nodetype, asTexture=True,
                        n='%s%s_%s' % (basename, nodetype.title(), tag)
                    )
                )
                tex_node(input_attr, texPath, type='string')
                postAction(tex_node)
                outplug = tex_node.attr(output_attr)
                finishedTextures[texPath] = {'type':nodetype, 'plug':outplug}
        outplug >> mat/attr
        print(
            '    -> make connection : %s to %s.%s' % (
                outplug, outplug.nodeName(), output_attr
            )
        )


def assignSPTexToPxrSurf(typeTable=TextureTypeTable):
    r"""
        Args:
            typeTable (str):enter description
    """
    print("# Assign substance painter's texture to PxrSurface.")
    finished_textures = {}
    for srf in node.ls(type='PxrSurface'):
        file_node = srf.attr('diffuseColor').source()
        if not file_node:
            continue
        filepath = file_node('ftn')
        dirpath, filename = os.path.split(filepath)
        nameinfo = filename.split('_')
        print('  # Assin to %s' % srf)
        for typ, nodeinfo, tag, target_attrs, postAction in typeTable:
            print typ
            nameinfo[1] = typ
            newpath = os.path.join(dirpath, '_'.join(nameinfo))
            createAndConnectTexture(
                newpath, nodeinfo, srf, tag, target_attrs, postAction,
                finished_textures
            )


def createTexPlane(path, extensions=['png']):
    r"""
        Args:
            path (str):
            extensions (list):
    """
    extensions=['.'+x for x in extensions]
    filelist = [
        x for x in os.listdir(path)
        if os.path.splitext(x)[-1].lower() in extensions
    ]
    num_column = int(math.sqrt(len(filelist)))
    col = 0
    row = 0
    for i, file in enumerate(filelist):
        mat = node.createNode('PxrSurface')
        sg = cmds.sets(renderable=True, noSurfaceShader=True, empty=True)
        mat.attr('outColor') >> sg+'.surfaceShader'
        fle = node.createNode('file')
        fle('ftn', os.path.join(path, file), type='string')
        fle.attr('outColor') >> mat/'diffuseColor'
        plane = node.asObject(
            cmds.polyPlane(w=1, h=1, sx=1, sy=1, ax=(0, 1, 0), cuv=2, ch=0)[0]
        )
        node.cmds.sets(plane, e=True, forceElement=sg)
        plane('t', [col, 0, row])
        col += 1
        if col > num_column:
            col = 0
            row += 1
# createTexPlane('D:/maya/projects/PocketMonster/elm/pokemon/uochildon/sourceimages')