#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    SubstancePainterで書き出したrman用テクスチャをPxrSurfaceに適用する。
    
    Dates:
        date:2020/10/03 21:29[eske3g@gmail.com]
        update:2020/10/03 21:38 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2020 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
import re
from maya import cmds
from gris3 import node

def getNameFromMat(matName):
    r"""
        任意の名前をカテゴライズ用のラベルにして返す。
        
        Args:
            matName (str):マテリアル名
            
        Returns:
            str:
    """
    ptn = re.compile('^(.*)_')
    r = ptn.search(matName)
    if not r:
        return
    return r.group(1)

def setupAlphaTexture(textureNode):
    r"""
        enter description
        
        Args:
            textureNode (str):enter description
            
        Returns:
            any:
    """
    textureNode('ail', True)

def doNothing(textureNode):
    r"""
        何も行わない関数。
        
        Args:
            textureNode (str):
    """
    pass
    
def joinPath(*paths):
    newpath = os.path.join(*paths)
    return newpath.replace('\\', '/')

TextureTypeTable = {
    'DiffuseColor':(
        'dff', 'file/ftn/outColor', 'fle',
        ['diffuseColor'], doNothing
    ),
    'Normal':(
        'nml', 'PxrNormalMap/filename/resultN', 'pxrNml',
        ['diffuseBumpNormal', 'specularBumpNormal'], doNothing
    ),
    'SpecularRoughness':(
        'rgh', 'file/ftn/outAlpha', 'fle',
        ['specularRoughness'], setupAlphaTexture
    ),
    'SpecularFaceColor':(
        'spc', 'file/ftn/outColor', 'fle',
        ['specularFaceColor'], doNothing
    ),
}

def createAndConnectTexture(
    texPath, nodeinfo, mat, tag, targetAttrs, postAction, finishedTextures
):
    r"""
        enter description
        
        Args:
            texPath (str):テクスチャのパス
            nodeinfo (str):作成するノード、アトリビュート情報
            mat (node.AbstractNode): 操作対象PxrSurface
            tag (str):名前につけるサフィックス
            targetAttrs (list):接続先のアトリビュート
            postAction (function):テクスチャ作成後に実行する関数
            finishedTextures (dict):処理済みノードのリスト
    """
    def searchTex(path, nodeType):
        r"""
            既に作成済みテクスチャがある場合、そのテクスチャの出力
            アトリビュートを返す。
            
            Args:
                path (str):テクスチャパス
                nodeType (str):ノードの種類
                
            Returns:
                dict:
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

class TextureData(str):
    r"""
        enter description
    """
    def __init__(self, key, dataTable=TextureTypeTable):
        r"""
            Args:
                key (str):
                dataTable (dict):
        """
        super(TextureData, self).__init__(key)
        self.__cat_data = {}
        self.__data_table = dataTable

    def addData(self, cat, dirpath, texName):
        r"""
            データのカテゴリとテクスチャパスを追加する。
            
            Args:
                cat (str):カテゴリ名
                dirpath (str):テクスチャを格納しているディレクトリパス
                texName (str):テクスチャ名
        """
        self.__cat_data[cat] = joinPath(dirpath, texName)

    def categories(self):
        r"""
            登録されているカテゴリを一覧で返す。
            戻り値のリストはソート済みの状態で返される。
            
            Returns:
                list:
        """
        categories = self.__cat_data.keys()
        categories.sort()
        return categories

    def texturePath(self, category):
        r"""
            与えられたカテゴリに対応するテクスチャパスを返す。
            Args:
                category (str):

            Returns:
                str:テクスチャパス
        """
        return self.__cat_data.get(category)

    def dataTable(self):
        return self.__data_table

    def applyTexture(self, material):
        r"""
            テクスチャをマテリアルに適用する。
            
            Args:
                material (str):操作対象マテリアル名
        """
        table = self.dataTable()
        finished_textures = {}
        print('=') * 80
        print('# Material : %s' % material)
        for cat in self.categories():
            print('  Map type : %s' % cat)
            table_data = table.get(cat)
            if not table_data:
                continue
            typ, nodeinfo, tag, target_attrs, postAction = table_data
            tex_path = self.texturePath(cat)
            print('  Texture  : %s' % tex_path)
            createAndConnectTexture(
                tex_path, nodeinfo, material, tag,  target_attrs, postAction,
                finished_textures
            )
            print('')
        print('=') * 80

class TextureDataList(object):
    r"""
        enter description
    """
    UDIM_PTN = re.compile('(.*)\.(\d{4})\.png$', re.IGNORECASE)
    def __init__(self, dataObj=TextureData, matNameCategolizer=getNameFromMat):
        r"""
            enter description
            
            Args:
                dataObj (TextureData):このクラスが管理に使用するクラス
                matNameCategolizer (function):マテリアルの名前仕分け用関数
        """
        self.__materiallist = {}
        self.__categolizer = matNameCategolizer
        self.__data_obj = dataObj

    def textureData(self, key):
        r"""
            enter description
            
            Args:
                key (str):
                
            Returns:
                TextureData:
        """
        return self.__materiallist.setdefault(key, self.__data_obj(key))

    def addData(self, dirPath, texName):
        r"""
            enter description
            
            Args:
                dirPath (str):テクスチャ格納パス
                texName (str):テクスチャ名
        """
        r = self.UDIM_PTN.search(texName)
        if not r:
            return
        name, udim = r.groups()
        project, name, typ = name.split('_')
        data = self.textureData(name)
        data.addData(typ, dirPath, texName)

    def dataTypes(self):
        r"""
            enter description
            
            Returns:
                list:
        """
        return self.__materiallist.keys()

    def applyTexture(self, material):
        r"""
            enter description
            
            Args:
                material (str):操作対象マテリアル名

        """
        name = self.__categolizer(material)
        data = self.textureData(name)
        data.applyTexture(material)

def assignTextureToPxrSurface(texDirs, matList=None):
    r"""
        enter description
        
        Args:
            texDirs (str/list):走査対象テクスチャ格納パス
            matList (list):操作対象となるマテリアルのリスト
            
        Returns:
            any:
    """
    matList = node.selected(matList, type='PxrSurface')
    datalist = TextureDataList()
    if not isinstance(texDirs, (list, tuple)):
        texDirs = [texDirs]
    for d in texDirs:
        if not os.path.isdir(d):
            continue
        for t in os.listdir(d):
            datalist.addData(d, t)

    for mat in matList:
        datalist.applyTexture(mat)

def createPxrSrfFromTexturePath(dirpath, new=False, checkTexture=False):
    def do_nothing(typ, basename, filepath, mat):
        pass

    def create_set_texture(typ, in_plug, out_plug, node_type, filepath):
        suffix = {
            'PxrTexture':'pxrTex', 'PxrNormalMap':'pxrNml'
        }.get(node_type)
        map = mat.attr(in_plug).source(type=node_type)
        if not map:
            map = node.shadingNode(
                node_type, n='{}{}_{}'.format(basename, typ, suffix),
                asTexture=True
            )
            map.attr(out_plug) >> mat/in_plug
        map('filename', filepath, type='string')
        return map

    def create_roughness(typ, basename, filepath, mat):
        map = create_set_texture(
            typ, 'specularRoughness', 'resultR', 'PxrTexture', filepath
        )

    def create_normal(typ, basename, filepath, mat):
        map = create_set_texture(
            typ, 'bumpNormal', 'resultN', 'PxrNormalMap', filepath
        )
        map('orientation', 1)

    def create_opacity(typ, basename, filepath, mat):
        pass

    def create_glow(typ, basename, filepath, mat):
        map = create_set_texture(
            typ, 'glowColor', 'resultRGB', 'PxrTexture', filepath
        )

    TextureTypeProcess = {
        'DiffuseColor':do_nothing,
        'Displacement':do_nothing,
        'GlowColor':create_glow,
        'Metaric':do_nothing,
        'Normal':create_normal,
        'Presence':create_opacity,
        'SpecularRoughness':create_roughness,
    }
    if not os.path.isdir(dirpath):
        return
    basename = os.path.basename(dirpath)
    
    # パターンに沿ったテクスチャが存在するかどうかのチェック。=================
    textures = [x for x in os.listdir(dirpath) if x.lower().endswith('.png')]
    texture_set = {}
    type_ptn = re.compile('_([a-zA-Z]+)\.\d+\.png')
    udim_ptn = re.compile('(.*\.)(\d{4})(\.png)')
    for tex in textures:
        r = type_ptn.search(tex)
        if not r:
            continue
        typ = r.group(1)
        f = TextureTypeProcess.get(typ)
        if not f:
            continue
        if typ not in texture_set:
            texture_set[typ] = [f, tex, 0]
        texture_set[typ][-1] += 1
    if not texture_set and checkTexture:
        return
    for typ, data in texture_set.items():
        # 同じカテゴリのテクスチャが複数枚ある場合はUDIMとして設定する。
        if data[2] > 1:
            data[1] = udim_ptn.sub(r'\1<UDIM>\3', data[1])
        texture_set[typ] =  data[:2]
    # =========================================================================

    # マテリアルが存在しない場合は作成する。===================================
    # (newフラグがOnの場合のみ)
    mat = node.asObject(basename+'_pxrSrf')
    if not mat:
        if not new:
            print(
                'Warning : "{}" was not detected. skip map creation,'.format(
                    basename
                )
            )
            return
        mat = node.shadingNode(
            'PxrSurface', asShader=True, n=basename+'_pxrSrf'
        )
        sg = node.asObject(basename+'_sg')
        if not sg:
            sg = node.asObject(
                cmds.sets(
                    name=basename+'_sg',
                    renderable=True, noSurfaceShader=True, empty=True,
                )
            )
            mat.attr('outColor') >> (sg/'surfaceShader', sg/'rman__surface')
        else:
            mat.attr('outColor') >> sg/'rman__surface'
    else:
        sg = mat.attr('outColor').destinations(type='shadingEngine')
        sg = sg[0] if sg else None

    if not texture_set:
        return mat
    # =========================================================================

    # normal、roughness, emmisiveの作成。
    for typ in ('Normal', 'SpecularRoughness', 'GlowColor'):
        data = texture_set.get(typ)
        if not data:
            continue
        f, tex = data
        f(typ, basename, joinPath(dirpath, tex), mat)
    
    # Displacementの設定。
    data = texture_set.get('Displacement')
    if data and sg:
        tex = data[-1]
        disp = sg.attr('rman__displacement').source(type='PxrDisplace')
        if not disp:
            disp = node.shadingNode(
                'PxrDisplace', asShader=True,
                n='{}Displacement_pxrDsp'.format(basename)
            )
            disp.attr('outColor') >> sg/'rman__displacement'
        map = disp.attr('dispScalar').source(type='PxrTexture')
        if not map:
            map = node.shadingNode(
                'PxrTexture', asTexture=True,
                n='{}Displacement_pxrTex'.format(basename)
            )
            map.attr('resultR') >> disp/'dispScalar'
        map('linearize', 1)
        map('filename', joinPath(dirpath, tex), type='string')

    # DiffuseとMetaricのマップのチェック。
    dff_met_keys = ('DiffuseColor', 'Metaric')
    for typ in dff_met_keys:
        if not texture_set.get(typ):
            return mat
    buffer = []
    
    # Diffuse、SpecularFaceならびにSpecularEdgeのテクスチャ設定。
    dff_metaric = [None, None]
    needs_dff_metarics = [[], []]
    for attr, key, values, dff_inplug in (
        (
            'diffuseColor', 'DiffuseColor',
            {'topRGB':(0, 0, 0)},
            'bottomRGB'
        ),
        (
            'specularFaceColor', 'SpecularFace',
            {'bottomRGB':(0.04, 0.04, 0.04)},
            'topRGB'
        ),
        (
            'specularEdgeColor', 'SpecularEdge',
            {'bottomRGB':(1, 1, 1)},
            'topRGB'
        )
    ):
        map = mat.attr(attr).source(type='PxrBlend')
        if not map:
            map = node.shadingNode(
                'PxrBlend', asTexture=True,
                n='{}{}_pxrBld'.format(basename, key)
            )
            map.attr('resultRGB') >> mat/attr
        for at, val in values.items():
            map(at, val)
        for i, in_plug in enumerate((dff_inplug, 'topA')):
            in_plug = map.attr(in_plug)
            tmp_map = in_plug.source(type='PxrTexture')
            if tmp_map:
                dff_metaric[i] = tmp_map
            needs_dff_metarics[i].append(in_plug)

    for map, plugs, typ, outplug, is_linearize in zip(
        dff_metaric, needs_dff_metarics, dff_met_keys,
        ('resultRGB', 'resultR'), (True, False)
    ):
        if not map:
            map = node.shadingNode(
                'PxrTexture', asTexture=True,
                n='{}{}_pxrTex'.format(basename, typ)
            )
        map('linearize', is_linearize)
        f, tex = texture_set.get(typ)
        map('filename', joinPath(dirpath, tex), type='string')
        map.attr(outplug) >> plugs

    # 一部の設定をクリア。
    for attr in (
        'roughSpecularFaceColor', 'roughSpecularEdgeColor',
        'clearcoatFaceColor', 'clearcoatEdgeColor'
    ):
        mat(attr, (0, 0, 0))


def createPxrSrfFromDir(rootdir, new=False):
    result = []
    if not os.path.isdir(rootdir):
        return result
    mat = createPxrSrfFromTexturePath(rootdir, new, True)
    if mat:
        result.append(mat)
        return result
    for subfile in os.listdir(rootdir):
        result.extend(
            createPxrSrfFromDir(joinPath(rootdir, subfile), new)
        )
    return result
