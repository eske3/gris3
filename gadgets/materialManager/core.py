#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2020/07/03 01:46 eske yoshinob[eske3g@gmail.com]
        update:2020/07/03 02:04 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2020 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from maya import cmds, OpenMaya

MatTypeTable = {
    'shadingEngine' : 'sg',
    'blinn':'bln', 'phong':'png', 'lambert':'lbt', 'surfaceShader':'ss',
    'PxrSurface':'pxrSrf', 'PxrConstant':'pxrCst', 'PxrLMPlastic':'pxrPls',
    'PxrLMGlass':'pxrGls', 'PxrLMMetal':'pxrMtl', 'PxrDisney':'pxrDsy',
}


class MaterialManager(object):
    ProxyAttrName = 'mm_shaderProxy'
    RmanAttrName = 'rman__surface'
    def __init__(self, shadingEngine=None):
        r"""
            Args:
                shadingEngine (str):シェーディングエンジン名
        """
        if not isinstance(shadingEngine, OpenMaya.MObject):
            if not shadingEngine:
                shadingEngine = cmds.ls(sl=True, et='shadingEngine')
                if not shadingEngine:
                    raise RuntimeError('No Shading Engine was specified.')
                shadingEngine = shadingEngine[0]
            msl = OpenMaya.MSelectionList()
            msl.add(shadingEngine)
            shadingEngine = OpenMaya.MObject()
            msl.getDependNode(0, shadingEngine)
        self.__dgnode = shadingEngine

    def dgNode(self):
        return OpenMaya.MFnDependencyNode(self.__dgnode)

    def __call__(self, attr=None):
        r"""
            Args:
                attr (str):
                
            Returns:
                str:名前＋アトリビュート名
        """
        return (
            self.dgNode().name() if not attr
            else self.dgNode().name() + '.' + attr
        )

    def __repr__(self):
        return self()

    def hasAttr(self, attrName):
        r"""
            任意のアトリビュートが存在するかどうかを返す
            
            Args:
                attrName (str):アトリビュート名
                
            Returns:
                bool:
        """
        return self.dgNode().hasAttribute(attrName)

    def listSrc(self, attrName):
        r"""
            任意のアトリビュートに接続されているソースノードを返す。
            
            Args:
                attrName (str):検索するアトリビュート名
                
            Returns:
                list:ソースノードのリスト(原則中身は一つか空)
        """
        src = cmds.listConnections(self(attrName), s=True)
        return src if src else []

    def setProxyShader(self, shader):
        r"""
            代理シェーダーをセットする
            
            Args:
                shader (str):
        """
        if not self.hasAttr(self.ProxyAttrName):
            cmds.addAttr(self(), ln=self.ProxyAttrName, at='message') 
        if cmds.isConnected(shader+'.message', self(self.ProxyAttrName)):
            return
        cmds.connectAttr(shader+'.message', self(self.ProxyAttrName), f=True)

    def getShader(self, attrName):
        r"""
            任意のアトリビュートに接続されているシェーダーを返す
            
            Args:
                attrName (str):アトリビュート名
                
            Returns:
                str:シェーダー名
        """
        if not self.hasAttr(attrName):
            return
        shader = self.listSrc(attrName)
        return shader[0] if shader else None

    def proxyShader(self):
        r"""
            セットされている代理シェーダーを返す。
            
            Returns:
                str:シェーダー名
        """
        return self.getShader(self.ProxyAttrName)

    def rmanShader(self):
        r"""
            renderman用シェーダーとして接続されているシェーダーを返す
            
            Returns:
                str:シェーダー名
        """
        return self.getShader(self.RmanAttrName)

    def currentShader(self):
        r"""
            現在シェーダーとして使用されているシェーダー名を返す
            
            Returns:
                str:シェーダー名
        """
        current_shader = self.listSrc('surfaceShader')
        return current_shader[0] if current_shader else None

    def swapShader(self):
        r"""
            現在のシェーダーと代理シェーダーを入れ替える
        """
        proxy = self.proxyShader()
        rman = self.rmanShader()
        current = self.currentShader()
        if current:
            self.setProxyShader(current)

        if not proxy and rman:
            proxy = rman
        if proxy:
            outplug = proxy + '.outColor'
            inplug = self('surfaceShader')
            if cmds.isConnected(outplug, inplug):
                return False
            cmds.connectAttr(outplug, inplug, f=True)
        return True

    def reconnectProxyToRmanPlug(self):
        proxy = self.proxyShader()
        if not proxy:
            return
        cmds.disconnectAttr(proxy+'.message', self(self.ProxyAttrName))
        if not cmds.isConnected(proxy+'.outColor', self(self.RmanAttrName)):
            cmds.connectAttr(proxy+'.outColor', self(self.RmanAttrName))


def select(*nodelist):
    r"""
        任意のノードを選択する
        
        Args:
            *nodelist (tuple):ノード名のリスト
    """
    nodelist = [x for x in nodelist if cmds.objExists(x)]
    if nodelist:
        cmds.select(nodelist)


def createScriptJob(event):
    r"""
        スクリプトジョブを作成する。
        ジョブはSelectionChangedに紐付けされる。
        
        Args:
            event (function):
    """
    return cmds.scriptJob(e=('SelectionChanged', event))


def killJob(id):
    r"""
        任意の番号のジョブを削除する。
        
        Args:
            id (int):
    """
    cmds.scriptJob(kill=id)


def selectedSGList():
    r"""
        選択中のオブジェクトにアサインされているシェーディングエンジンを特定
        して返す。

        Returns:
            list:
    """
    selected = cmds.ls(sl=True)
    shading_engines = []
    for sel in selected:
        setlist = cmds.listSets(ets=True, type=1, object=sel) 
        if not setlist:
            continue
        shading_engines.extend(setlist)
    return cmds.ls(shading_engines, type='shadingEngine')


def applyName(baseName, position, *nodelist):
    r"""
        Args:
            baseName (str):
            position (str):
            *nodelist (str):適用対象となるノード名のリスト
    """
    for node in nodelist:
        if not cmds.objExists(node):
            continue
        node_type = MatTypeTable.get(cmds.nodeType(node), 'mat')
        nameinfo = [x for x in (baseName, node_type, position) if x]
        new_name = '_'.join(nameinfo)
        
        if node == new_name:
            continue
        cmds.rename(node, new_name)
        print('Apply name : %s -> %s' % (node, new_name))


def applyNameFromData(shaderinfo):
    r"""
        Args:
            shaderinfo (dict):
    """
    for data in shaderinfo:
        applyName(
            data['baseName'], data['position'],
            data['sg'], data['currentMat'], data['proxyMat']
        )


def swapMaterialFromData(shaderinfo):
    r"""
        Args:
            shaderinfo (list):辞書のリスト
    """
    for data in shaderinfo:
        mm = MaterialManager(data['sg'])
        mm.swapShader()


def assignShaderToRmanPlug(shaderinfo):
    for data in shaderinfo:
        mm = MaterialManager(data['sg'])
        mm.reconnectProxyToRmanPlug()


def applyMaterialToSG(shadingEngines):
    r"""
        Args:
            shadingEngines (str):シェーディングエンジン名
    """
    selected_materials = cmds.ls(sl=True, materials=True)
    if not selected_materials:
        return

    print('Apply material "%s" to' % selected_materials[0])

    for sg in shadingEngines:
        outplug = selected_materials[0] + '.outColor'
        inplug = sg + '.surfaceShader'
        if cmds.isConnected(outplug, inplug):
            continue

        cmds.connectAttr(outplug, inplug, f=True)
        print('    %s' % sg)


def listShadingEngines():
    r"""
        シーン中のシェーディングエンジンをリストする。
        戻り値はMaterialManagerクラスのリスト。
        
        Returns:
            list(MaterialManager):
    """
    from collections import OrderedDict
    ns_sglist = OrderedDict()
    result = OrderedDict({'':[]})
    sglist = cmds.ls(type='shadingEngine')
    for sg in sglist:
        if ':' in sg:
            ns, name = sg.rsplit(':', 1)
        else:
            ns, name = ('', sg)
        ns_sglist.setdefault(ns, []).append(sg)
    
    for ns, sglist in ns_sglist.items():
        slist = OpenMaya.MSelectionList()
        [slist.add(x) for x in sglist]
        result_list = []
        for i in range(slist.length()):
            mobject = OpenMaya.MObject()
            slist.getDependNode(i, mobject)
            mm = MaterialManager(mobject)
            if not mm.dgNode().isShared():
                result_list.append(mm)
        if not result_list:
            continue
        result[ns] = result_list
    return result
