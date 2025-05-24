#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    スキニングに関するユーティリティモジュール。
    
    Dates:
        date:2017/03/11 1:12[Eske](eske3g@gmail.com)
        update:2024/06/07 13:10 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import re
from maya.api import OpenMaya

from .. import node, mathlib, verutil
from . import modelingSupporter
cmds = node.cmds

def findSkinCluster(skinObject):
    r"""
        melのfindRelatedSkinClusterのPythonラッパー関数。
        接続されたskinClusterを返す。
        
        Args:
            skinObject (str):スキニングされたオブジェクト。
            
        Returns:
            str:
    """
    from maya import mel
    return node.asObject(mel.eval('findRelatedSkinCluster("%s")' % skinObject))


def listSkinClustersFromSelected(targetNodes=None):
    r"""
        選択オブジェクトについているSkinClusterをリストする。
        targetNodesをリストで指定した場合は、そのノードについている
        SkinClusterを返す。
        
        Args:
            targetNodes (list):
            
        Returns:
            list:
    """
    result = []
    for n in node.selected(targetNodes):
        sc = findSkinCluster(n)
        if sc:
            result.append(sc)
    return result


def listSkinFromInfluence(influence):
    r"""
        インフルエンスが接続しているskinClusterの一覧を返す。
        戻り値はskinClusterと、それが影響を与えているジオメトリをセットにした
        リスト。

        Args:
            influence (str):インフルエンス名
        
        Returns:
            list
    """
    con = cmds.listConnections(
        influence, s=False, d=True, p=True, type='skinCluster'
    ) or {}
    sclist = []
    for c in con:
        n, attr = c.split('.', 1)
        if not attr.startswith('matrix['):
            continue
        sclist.append(n)
    sclist = list(set(sclist))
    sclist.sort()
    result = []
    for sc in sclist:
        geometories = node.toObjects(cmds.skinCluster(sc, q=True, g=True))
        if not geometories:
            continue
        for geo in geometories:
            try:
                p = geo.parent()
            except:
                p = geo
            result.append([sc, p])
    return result


def listWeights(target):
    sc = findSkinCluster(target)
    if not sc:
        return {}
    return  sc.listWeights()


def showBindSkinOption():
    r"""
        バインドオプションを開く
    """
    from maya import mel
    mel.eval('SmoothBindSkinOptions')


def bindFromBinded(targets, source, copyWeight=True):
    r"""
        sourceに使用されているインフルエンスを使用してtargetsにバインド
        する。copyWeightがTrueの場合、バインド後にウェイトのコピーも
        行う。
        戻り値として、生成されたskinClusterを返す。
        
        Args:
            targets (list):バインドされるオブジェクトのリスト
            source (str):ソースオブジェクト
            copyWeight (bool):ウェイトをコピーするかどうか
            
        Returns:
            list:
    """
    sc = findSkinCluster(source)
    results = sc.rebind(targets, copyWeight)
    return results


def selectInfluences(skinClusters):
    r"""
        あたえられたskinClusterにバインドされているインフルエンスを選択
        する関数。
        
        Args:
            skinClusters (list):node.SkinClusterを持つリスト
    """
    influences = []
    for sc in skinClusters:
        influences.extend(sc._influences())
    if influences:
        cmds.select(influences, r=True)


def swapInfluence(srcInf, dstInf, vertices=None):
    r"""
        任意の頂点のsrcInfに該当するインフルエンスをdstInfに入れ替える。
        
        Args:
            srcInf (str):入れ替えられるインフルエンス
            dstInf (str):入れ替えるインフルエンス
            vertices (list):変更する頂点のリスト
    """
    if vertices is None:
        vertices = cmds.filterExpand(sm=31)
    else:
        vertices = cmds.filterExpand(vertices, sm=31)
    index_pattern = re.compile('\[(\d+)\]')
    vtx_indecies = {}
    # 頂点番号を抽出し、所属するシェイプのグループに登録する。=================
    for vtx in vertices:
        shape = cmds.listRelatives(vtx, p=True)[0]
        index = int(index_pattern.search(vtx).group(1))
        if shape in vtx_indecies:
            vtx_indecies[shape].append(index)
        else:
            vtx_indecies[shape] = [index]
    # =========================================================================

    # =========================================================================
    for shape in vtx_indecies:
        sc = findSkinCluster(shape)
        inflist = sc._influences(sc.InfluenceWithIndex)
        src_index = inflist.get(srcInf)
        dst_index = inflist.get(dstInf)
        if not src_index or not dst_index:
            continue

        for vtx in vtx_indecies[shape]:
            src_attr = 'wl[%s].weights[%s]' % (vtx, src_index)
            dst_attr = 'wl[%s].weights[%s]' % (vtx, dst_index)
            sc(dst_attr, sc(src_attr))
            sc(src_attr, 0)
    # =========================================================================


def replaceInfluence(srcInf, dstInf, skinCluster):
    sc = node.asObject(skinCluster)
    if not sc.isType('skinCluster'):
        return False
    influences = sc._influences(2)
    src_name = verutil.String(srcInf)
    dstInf = node.asObject(dstInf)
    if not getattr(dstInf, 'matrix'):
        return False
    if not src_name in influences:
        return False
    if not dstInf.hasAttr('lockInfluenceWeights'):
        dstInf.addBoolAttr(
            'lockInfluenceWeights', sn='liw', default=False, cb=False, k=False
        )
    index = influences[src_name]
    dstInf.attr('wm[0]') >> sc.attr('matrix[{}]'.format(index))
    dstInf.attr('liw') >> sc.attr('lockWeights[{}]'.format(index))
    dstInf.attr('objectColorRGB') >> sc.attr('influenceColor[{}]'.format(index))
    sc('bindPreMatrix[{}]'.format(index), dstInf('wim'),  type='matrix')
    return True

    
def replaceAllInfluence(srcInf, dstInf):
    sclist = [
        x.split('.', 1)[0] for x in 
        cmds.listConnections(
            srcInf+'.wm', s=False, d=True, p=True, type='skinCluster'
        ) or []
        if '.matrix[' in x
    ]
    for sc in sclist:
        replaceInfluence(srcInf, dstInf, sc)



# /////////////////////////////////////////////////////////////////////////////
# 便利機能                                                                   //
# /////////////////////////////////////////////////////////////////////////////
def bindToFace(falloff=0.0, hierarchy=True):
    r"""
        選択フェースに対し、選択ジョイントをboxelBindingしたウェイトを
        適応する。
        
        Args:
            falloff (float):folloff値。値が小さいほど柔らかくなる。
            hierarchy (bool):選択ジョイントの子もウェイトに含めるかどうか
    """
    selected = cmds.ls(sl=True)
    faces = cmds.filterExpand(selected,sm=34)
    joints = cmds.ls(selected,type='joint')
    if hierarchy:
        joints.extend(cmds.listRelatives(joints, ad=True, pa=True))
    verticies = cmds.polyListComponentConversion(faces,tv=True)
    modelingSupporter.extractPolyFace(True, faces)
    duplicated = cmds.ls(sl=True)
    sc = cmds.skinCluster(
        joints, duplicated,
        tsb=True, bm=3, nw=1, wd=1, omi=False, mi=5, hmf=0.1, dr=4
    )[0]
    cmds.geomBind(sc, bm=3, gvp=(256,1), falloff=0.0, mi=5)
    cmds.select(duplicated, verticies)
    cmds.copySkinWeights(
        noMirror=True,
        surfaceAssociation='closestPoint', influenceAssociation='closestJoint'
    )
    cmds.delete(duplicated)


def transferObjectsWeights(sourceNodes=None, target=None):
    r"""
        sourceNodesの各頂点に最も近いtargetの頂点にウェイトを転送する。
        基本的にsourceNodesはtargetの一部と全く同じ形状であることが
        望ましい。
        
        Args:
            sourceNodes (list):ウェイト転送元となるオブジェクト
            target (str):ウェイト転送先のオブジェクト名
    """
    def closestPoint(vec, veclist):
        r"""
            最も近い頂点を探してくるローカル関数
            
            Args:
                vec (MVector):入力ベクトル
                veclist (list):頂点名とその位置ベクトルを持つリスト
                
            Returns:
                tuple:(頂点名, そこまでの長さ)
        """
        shortest = (veclist[0][0], (vec-veclist[0][1]).length())
        for vtx, vec2 in veclist[1:]:
            l = (vec - vec2).length()
            if l < shortest[1]:
                shortest = (vtx, l)
        return shortest

    if not sourceNodes or not target:
        selected = [
            x for x in node.selected(dag=True, type='mesh') if not x('io')
        ]
        if not target:
            target = selected[-1]
        if not sourceNodes:
            sourceNodes = selected[:-1]

    # ターゲットの頂点座標をキャッシュする
    target = node.asObject(target)
    msel = OpenMaya.MSelectionList()
    msel.add(target())
    dagpath = msel.getDagPath(0)
    mit_vtx = OpenMaya.MItMeshVertex(dagpath)
    vtx_fmt = target() + '.vtx[{}]'
    tgt_vts_info = []
    for vtx in mit_vtx:
        vec = node.MVector(list(vtx.position(OpenMaya.MSpace.kWorld))[:3])
        tgt_vts_info.append((vtx_fmt.format(vtx.index()), vec))
    for vtx in cmds.ls(target+'.vtx[*]', fl=True):
        vec = node.MVector(cmds.pointPosition(vtx))
        tgt_vts_info.append((vtx, vec))

    for src in sourceNodes:
        selectionlist = []
        verts = []
        vtx_fmt = src() + '.vtx[{}]'
        msel = OpenMaya.MSelectionList()
        msel.add(src())
        dagpath = msel.getDagPath(0)
        mit_vtx = OpenMaya.MItMeshVertex(dagpath)
        for vtx in mit_vtx:
            verts.append(vtx_fmt.format(vtx.index()))
            vec = node.MVector(
                list(vtx.position(OpenMaya.MSpace.kWorld))[:3]
            )
            t_vtx, length = closestPoint(vec, tgt_vts_info)
            selectionlist.append(t_vtx)
        cmds.select(verts)
        cmds.select(selectionlist, add=True)
        cmds.copySkinWeights(
            noMirror=True, surfaceAssociation='closestPoint', 
            influenceAssociation='closestJoint'
        )


def getStoredModel(target):
    r"""
        storeWeightModel関数でコピーされたオブジェクトが紐づけされているか
        どうかをチェックし、紐づけされたノードがある場合、それを返す。
        
        Args:
            target (node.DagNode):
            
        Returns:
            list:
    """
    dst = target.attr('message').destinations(p=True)
    return [
        node.asObject(x.nodeName()) for x in dst if x.endswith('.storedWeight')
    ]


def storeWeightModel(targets=None, tmpGrp='__tempStored_grp__'):
    r"""
        バインドされているオブジェクトのコピーを作成し、そのコピーにウェイトを
        コピーする便利関数。
        コピーを取っておくと、後にrestoreWeightModel関数でコピーから
        元オブジェクトへ再度ウェイトを転送し直してウェイトを復元できる。
        
        コピーされたオブジェクトと元オブジェクトはstoredWeightアトリビュートを
        介して接続されており、後にrestoreWeightModelを呼んでウェイトを復元する
        際に利用される。
        
        Args:
            targets (list):スキニングされたオブジェクトの一覧
            tmpGrp (str):コピーオブジェクトを格納しておくグループ名
            
        Returns:
            list:作成されたコピーとその親ノードのリスト
    """
    targets = node.selected(targets, type='transform')
    grp = node.asObject(tmpGrp)
    results = []
    origins = []
    if not grp:
        grp = node.createNode('transform', n=tmpGrp)
    for tgt in targets:
        strmdl = getStoredModel(tgt)
        if strmdl:
            for sm in strmdl:
                cmds.delete(sm.parent())
        parent = tgt.parent()
        space = node.createNode(
            'transform', p=grp, n='SPC_'+tgt.shortName()
        )
        space.fitTo(parent)
        space('v', 0)
        new_tgt = cmds.duplicate(tgt, rr=True)
        new_tgt = node.parent(new_tgt, space)[0]
        plug = new_tgt.addMessageAttr('storedWeight')
        tgt.attr('message') >> plug
        bindFromBinded([new_tgt], tgt)
        results.append([new_tgt, space])
        origins.append(tgt)
    if origins:
        cmds.select(origins)


def restoreWeightModel(
    targets=None, deleteHistory=True, tmpGrp='__tempStored_grp__'
):
    r"""
        storeWeightModelで作成されたコピーオブジェクトのウェイトを
        元オブジェクトに再度転送する関数。
        deleteHistoryがTrueの場合、targetsのヒストリを削除してからウェイトを
        移す。（推奨）
        tmpGrpにはコピーオブジェクトを格納している仮グループ名を指定する。
        指定されたノードは、復元実行後に空の場合削除される。
        
        Args:
            targets (list):
            deleteHistory (bool):
            tmpGrp (str):コピーオブジェクトを格納しておくグループ名
    """
    targets = node.selected(targets, type='transform')
    deleting = []
    for tgt in targets:
        strmdl = getStoredModel(tgt)
        if not strmdl:
            continue
        if deleteHistory:
            cmds.delete(tgt, ch=True)
        bindFromBinded([tgt], strmdl[0])
        for sm in strmdl:
            deleting.append(sm.parent())
    grp = node.asObject(tmpGrp)
    if deleting:
        cmds.delete(deleting)
    if grp and not grp.hasChild():
        cmds.delete(grp)
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////

# /////////////////////////////////////////////////////////////////////////////
# 実機向け機能。                                                             //
# /////////////////////////////////////////////////////////////////////////////
def selectBrokenLimitVertices(
    targetNodes=None, numberOfLimit=4, withFix=False, isSelecting=True
):
    r"""
        任意の数以上のインフルエンスがある頂点を選択する。
        isSelectingがFalseの場合は選択を行わず、該当頂点のみを返す。
        
        Args:
            targetNodes (list):
            numberOfLimit (int):チェックインフルエンスの最大数
            withFix (bool):選択と同時に修正も行うかどうか
            isSelecting (bool): 選択するかどうか

        Returns:
            dict:
    """
    check_only = withFix == False
    targetNodes = node.selected(targetNodes)
    result = {}
    for n in targetNodes:
        sc = findSkinCluster(n)
        vertices = sc.fixBrokenLimitInfluence(numberOfLimit, check_only, False)
        if vertices:
            result[n] = vertices
    if isSelecting:
        r_verts = []
        for vts in result.values():
            r_verts.extend(vts)
        cmds.select(r_verts, r=True)
    return result


class BindedVtxConstraint(object):
    r"""
        任意の頂点のウェイトを取得し、ウェイト情報から擬似的に任意の頂点に
        固定されているような仕組みを提供するクラス。
    """

    Version = 1.0
    VersionAttrName = 'grisBindedConstVer'
    def __init__(self, nodeName):
        r"""
            Args:
                nodeName (any):
        """
        root = node.Transform(nodeName)
        self.__root = root if root.hasAttr(self.VersionAttrName) else None

    def isValid(self):
        return bool(self.__root)

    def root(self):
        return self.__root

    @classmethod
    def listNodes(cls, *rootNodes):
        r"""
            Args:
                *rootNodes (any):
        """
        all_nodes = cmds.ls(*rootNodes, type='dagContainer')
        if not all_nodes:
            all_nodes = cmds.ls(type='dagContainer')
        if not all_nodes:
            return []
        cst_nodes = [
            BindedVtxConstraint(x) for x in all_nodes
            if cmds.attributeQuery(cls.VersionAttrName, ex=True, n=x)
        ]
        return cst_nodes

    def multMatrices(self):
        addmtx = self.__node.attr('wtAddMatrix').source()
        ptn = re.compile('\.matrixIn$')
        if not addmtx:
            return []
        result = []
        for attr in [
            x for x in cmds.listAttr(addmtx+'.wtMatrix', m=True)
            if ptn.search(x)
        ]:
            mltmtx = cmds.listConnections(addmtx/attr, s=True, d=False)
            if mltmtx:
                result.extend(mltmtx)
        return result

    def listData(self):
        root = self.root()
        inputnodes = root.attr('inputMatrix').sources()
        weights = root.listAttr('inputWeight', m=True)
        weightlist = {}
        results = {}
        for n, w in zip(inputnodes, weights):
            if not n:
                continue
            weightlist[n()] = w.get()

        offset = root('position')[0]
        results['offsetPosition'] = offset
        results['influenceWeight'] = weightlist
        return {root() : results}
        

    @classmethod
    def create(cls, targetVertex, name, position=None):
        # スキンクラスターの検索。=============================================
        r"""
            Args:
                targetVertex (any):
                name (any):
                position (any):
        """
        shapes = cmds.listRelatives(targetVertex, p=True, pa=True)
        sc = None
        for shape in shapes:
            sc = findSkinCluster(shapes[0])
            if sc:
                break
        if not sc:
            return
        # =====================================================================

        from .. import system
        rule = system.GlobalSys().nameRule()
        n = rule()
        n.setName(name)
        n.setPosition(position)

        # ウェイトから行列計算。===============================================
        influences = sc.attr('matrix').sources()
        weights = cmds.skinPercent(sc, targetVertex, q=True, v=True)
        mltmtxlist = []
        inputlist = []
        for i, w in zip(influences, weights):
            if w == 0:
                continue
            mltmtx = node.createUtil('multMatrix')
            mltmtxlist.append((mltmtx, w))
            inputlist.append((i, w, mltmtx))
        if not mltmtxlist:
            return
        contains = [x[0] for x in mltmtxlist]

        addmtx = node.createUtil('wtAddMatrix')
        contains.append(addmtx)
        for i, data in enumerate(mltmtxlist):
            mltmtx, w = data
            mltmtx.attr('matrixSum') >> '%s.wtMatrix[%s].matrixIn'%(addmtx, i)
            addmtx('wtMatrix[%s].weightIn'%i, w)

        mltmtx = node.createUtil('multMatrix', n=n.convertType('mltmtx')())
        fbfmtx = node.createUtil(
            'fourByFourMatrix', n=n.convertType('fbfmtx')()
        )
        fbfmtx.attr('output') >> mltmtx/'matrixIn[0]'
        addmtx.attr('matrixSum') >> mltmtx/'matrixIn[1]'
        decmtx = node.createUtil(
            'decomposeMatrix', n=n.convertType('decmtx')()
        )
        mltmtx.attr('matrixSum') >> decmtx/'inputMatrix'
        contains.extend([mltmtx, fbfmtx, decmtx])
        # =====================================================================

        n.setNodeType('vtxCst')
        root = cmds.container(name=n(), type='dagContainer', addNode=contains)
        root = node.Transform(root)
        root.attr('pim') >> mltmtx/'matrixIn[2]'
        for attr in ['t', 'r', 's', 'sh']:
            ~decmtx.attr('o'+attr) >> ~root.attr(attr)
        root.lockTransform()
        # root('blackBox', 1, l=True)

        # バージョン情報の追記。
        ver_plug = root.addFloatAttr(
            cls.VersionAttrName, min=None, max=None,
            default=cls.Version, k=False
        )
        ver_plug.setLock(True)

        # 入力用アトリビュートの作成。=========================================
        cmds.addAttr(root(), ln='inputVert', sn='iv', at='double3')
        for ax in 'XYZ':
            cmds.addAttr(
                root(), ln='inputVert'+ax, sn='iv'+ax.lower(), at='double',
                p='inputVert'
            )
        root.editAttr(['iv:a'], k=False, l=False)
        index_pattern = re.compile('\[(\d+)\]')
        r = index_pattern.search(targetVertex)
        '%s.vrts[%s]'%(shape, r.group(1)) >> root.attr('iv')

        cmds.addAttr(root(), ln='position', sn='p', at='double3')
        for ax in 'XYZ':
            cmds.addAttr(
                root(), ln='position'+ax, sn='p'+ax.lower(), at='double',
                p='position'
            )
        root.editAttr(['p:a'], k=True, l=False)
        cmds.addAttr(
            root(), ln='inputMatrix', sn='imx', m=True, dt='matrix'
        )
        cmds.addAttr(
            root(), ln='inputInverseMatrix', sn='iim', m=True, dt='matrix'
        )
        cmds.addAttr(
            root(), ln='inputWeight', sn='iwt', m=True, at='double'
        )
        cmds.addAttr(root(), at='message', ln='wtAddMatrix', h=True)
        
        # 内部コネクション。---------------------------------------------------
        addmtx.attr('message') >> root/'wtAddMatrix'
        
        # 頂点座標の入力。
        root.attr('positionX') >> fbfmtx/'in30'
        root.attr('positionY') >> fbfmtx/'in31'
        root.attr('positionZ') >> fbfmtx/'in32'
        root('p', cmds.pointPosition(targetVertex))

        # インフルエンスの接続
        for i, data in enumerate(inputlist):
            inf, w, mltmtx = data
            tgt = '%s.inputMatrix[%s]'%(root, i)
            inf.attr('wm') >> tgt
            tgt >> mltmtx.attr('matrixIn[1]')
            
            root('inputInverseMatrix[%s]'%i, inf('wim'), type='matrix')
            root.attr('inputInverseMatrix[%s]'%i) >> mltmtx.attr('matrixIn[0]')
            root('inputWeight[%s]'%i, w)
            (
                root.attr('inputWeight[%s]'%i) >>
                '%s.wtMatrix[%s].weightIn'%(addmtx, i)
            )
        # ---------------------------------------------------------------------
        # =====================================================================

        return root

# import traceback
# try:
    # from gris3 import node, func
    # from gris3.tools import skinUtility
    # from maya import cmds
    # reload(skinUtility)
    # skinUtility.BindedVtxConstraint.create(cmds.filterExpand(sm=31)[0], 'chorker', 'C')
# except:
    # traceback.print_exc()
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////












