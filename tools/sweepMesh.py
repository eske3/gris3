#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2024/02/19 13:24 Eske Yoshinob[eske3g@gmail.com]
        update:2024/02/28 17:36 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import node, verutil
from . import util, surfaceMaterialUtil, cleanup
cmds = node.cmds

PLUGIN_NAME = 'sweep'
IS_INVALID  = False
if not cmds.pluginInfo(PLUGIN_NAME, q=True, l=True):
    try:
        cmds.loadPlugin(PLUGIN_NAME)
    except:
        IS_INVALID = True


def _get_curve(name):
    r"""
        Args:
            name (any):
    """
    crv = node.asObject(name)
    if not crv:
        return
    if crv.isType('transform'):
        shape = crv.shapes(ni=True, typ='nurbsCurve')
        if not crv:
            return
        return shape[0]
    elif crv.isType('nurbsCurve'):
        return crv


def _get_mesh(targetMesh=None):
    r"""
        操作対象となるオブジェクトがメッシュの場合、シェイプオブジェクトを
        返す。
        該当しない場合はエラーを発生させる。
        
        Args:
            targetMesh (str):精査対象となるオブジェクト名
            
        Returns:
            node.Mesh:
    """
    targetMesh = node.selected(targetMesh, type=['mesh', 'transform'])
    if not targetMesh:
        raise RuntimeError('No target mesh specified.')
    if targetMesh[0].isType('transform'):
        targetMesh = targetMesh[0].shapes(ni=True, typ='mesh')
        if not targetMesh:
            raise RuntimeError('No target mesh specified.')
    return targetMesh[0]


def createSweepMesh(curves, sg, oneNodePerCurve=True):
    r"""
        Args:
            curves (list):操作対象カーブのリスト
            sg (str):生成されたメッシュにアサインするSG名
            oneNodePerCurve (bool):カーブごとにsweepMeshCreatorを作成するかどうか
    
        Returns:
            list: 生成されたメッシュとsweepMeshCreatorを持つリスト
    """
    sweep = None
    if oneNodePerCurve:
        sweep = node.createNode('sweepMeshCreator')
    results = []
    for i, crv in enumerate(curves):
        crv = _get_curve(crv)
        if not crv:
            continue
        if sweep:
            sn = sweep
            idx = i
        else:
            sn = node.createNode('sweepMeshCreator')
            idx = 0
        crv.attr('worldSpace[0]') >> '{}.inCurveArray[{}]'.format(sn, idx)
        trs = node.createNode('transform', n='sweep#')
        mesh = node.createNode('mesh', p=trs, n='sweepShape#')
        cmds.sets(mesh, e=True, forceElement=sg)
        sn.attr('outMeshArray[{}]'.format(idx)) >> mesh/'inMesh'
        results.append((trs, sn))
    return results


def convertSelection(targetNodes=None, toMesh=True, isSelecting=True):
    r"""
        任意のsweepオブジェクトまたはカーブに関連付けられた対象オブジェクトを
        選択する。
        
        Args:
            targetNodes (list):
            toMesh (bool):変換をメッシュにするかどうか
            isSelecting (bool):変換後のオブジェクトを選択するかどうか
            
        Returns:
            list:変換後のオブジェクト。
    """
    types = ['transform']
    # flags = {'s': False, 'd': True}
    flags = {'il':2}
    if toMesh:
        target_type = 'nurbsCurve'
        dst_type = 'mesh'
        future = True
        pdo = False
    else:
        target_type = 'mesh'
        dst_type = 'nurbsCurve'
        future = False
        pdo = True
    types.append(target_type)
    targetNodes = node.selected(targetNodes, type=types)
    shapes = []
    for n in targetNodes:
        if not n.isType('transform'):
            shapes.append(n)
            continue
        s = n.shapes(typ=target_type, ni=True)
        if not s:
            continue
        shapes.append(s[0])
    results = []
    
    # 新バージョン
    for shape in shapes:
        creator = [
            x for x in cmds.listHistory(shape, f=future, pdo=pdo, il=2) or []
            if cmds.nodeType(x) == 'sweepMeshCreator'
        ]
        if not creator:
            continue
        cnv = list(
            set(
                [
                    x for x in cmds.listHistory(creator, f=future, il=2) or []
                    if cmds.nodeType(x) == dst_type
                ]
            )
        )
        if not cnv:
            continue
        cnv = cmds.listRelatives(cnv, type='transform', pa=True, p=True)
        results.append(
            {target_type: shape.parent(), dst_type: cnv, 'sweep':creator}
        )
        
    if isSelecting:
        converted = []
        for x in results:
            if not x[dst_type]:
                continue
            converted.extend(x[dst_type])
        if converted:
            cmds.select(converted, r=True)
    return results


def convertSelectionToMesh(targetNodes):
    to_mesh = convertSelection(targetNodes, True, False)
    curves = [x['nurbsCurve'] for x in  to_mesh]
    to_crv = convertSelection(targetNodes, False, False)
    for crv_data in to_crv:
        for crv in crv_data['nurbsCurve']:
            if crv in curves:
                break
        else:
            for crv in crv_data['nurbsCurve']:
                to_mesh.append(
                    {
                        'nurbsCurve': node.asObject(crv),
                        'mesh':[crv_data['mesh']], 'sweep':crv_data['sweep']
                    }
                )
    return to_mesh


def selectEditing(targetNodes=None):
    r"""
        任意のsweepオブジェクトかカーブに対し、パラメータ変更できるように
        必要なオブジェクトとカーブを選択する。
        メッシュとカーブが選択されるため、ワイヤーフレームを見ながらAttributeで
        調整可能な状態にする。

        Args:
            targetNodes (list):
    """
    to_mesh = convertSelection(targetNodes, True, False)
    to_crv = convertSelection(targetNodes, False, False)
    keys = ('mesh', 'nurbsCurve')
    datalist = {x: [] for x in keys}
    for data in to_mesh + to_crv:
        for key in datalist:
            values = data[key]
            if isinstance(values, (list, tuple)):
                datalist[key].extend(values)
            else:
                datalist[key].append(values)
    cmds.select(cl=True)
    for key in keys:
        targets = list(set(datalist[key]))
        if targets:
            cmds.select(targets, add=True)


def sweepMesh(
    curves=None, taperList=None, profileCurve=0, oneNodePerCurve=True,
    material=None, **keywords
):
    r"""
        sweepMeshFromCurveの拡張関数。
        
        taperListにはTaperCurveを制御するための数字のリストを渡す。
        リストの各要素には[position, floatValue, (interplation)]を指定し、
        リストの順にインデックスされ設定されていく。
        
        profileCurveには０～４の数値を指定する。既存のNURBSカーブ名の場合は
        そのカーブを使用し、タイプは5に自動的に設定される。
        
        Args:
            curves (list):操作対象となるカーブのリスト
            taperList (list):テーパ曲線を制御するための数値のリスト
            profileCurve (str):断面形状を定義するカーブ名
            oneNodePerCurve (bool):カーブごとにsweepNodeを作成するかどうか
            material (any):
            **keywords (dict):sweepNodeに設定するアトリビュート
            
        Returns:
            list:{'sweep'sweepノード、'mesh'生成されたメッシュ、'curve'カーブ}
    """
    def _createCustomProfile(profileCurve, sweep_node):
        r"""
            断面形状の設定を行うローカル関数。
            
            Args:
                profileCurve (str):
                sweep_node (node.AbstractNode):
                
            Returns:
                tuple:カスタム場合nurbsCurveとsweepProfileConverterを返す。
        """
        if isinstance(profileCurve, int):
            sweep_node('sweepProfileType', profileCurve)
            return
        prf_crv = _get_curve(profileCurve)
        if not prf_crv:
            return
        sweep_node('sweepProfileType', 5)
        cnv = node.createNode('sweepProfileConverter')
        prf_crv.attr('local') >> cnv/'inObjectArray[0].curve'
        prf_crv.attr('worldMatrix[0]') >> cnv/'inObjectArray[0].worldMatrix'
        cnv.attr('sweepProfileData') >> sweep_node/'customSweepProfileData'
        return prf_crv, cnv

    # マテリアル適用。
    mat = node.asObject(material)
    shading_engine = node.asObject('initialShadingGroup')
    if mat:
        sg = mat.destinations(type='shadingEngine')
        if sg:
            shading_engine = sg[0]

    curves = node.selected(curves)
    sweep_nodes = createSweepMesh(
        curves, shading_engine, oneNodePerCurve=oneNodePerCurve
    )
    results = []
    for mesh, sn in sweep_nodes:
        for key, val in keywords.items():
            sn(key, val)

        # プロファイルカーブの設定。
        _createCustomProfile(profileCurve, sn)

        data = {'sweep': sn}
        data['mesh'] = (
            node.listConnections(sn/'outMeshArray', s=False, d=True) or {}
        )
        data['curve'] = (
            node.listConnections(sn/'inCurveArray', s=True, d=False) or {}
        )
        if len(taperList) > 1:
            for i, values in enumerate(taperList):
                template = 'taperCurve[{}].taperCurve_{{}}'.format(i)
                for val, attr in zip(
                    values, ['Position', 'FloatValue', 'Interp']
                ):
                    sn(template.format(attr), val)
        results.append(data)
    return results


def sweepHair(
    curves=None, taperList=None, profileCurve=0,
    interpolationMode=3, interpolationDistance=1,
    width=2.0, height=0.5, rotation=0, twist=0, material=None,
    meshInto=None, curveInto=None
):
    r"""
        Args:
            curves (list):操作対象となるカーブのリスト
            taperList (list):テーパ曲線を制御するための数値のリスト
            profileCurve (str):断面形状を定義するカーブ名
            interpolationMode (int):横方向の分割手法。
            interpolationDistance (float):横方向の分割距離
            width (float):生成される形状の幅
            height (float):生成される形状の厚み
            material (str):生成される形状にアサインされるマテリアル
            meshInto (str):生成される形状が格納されるグループ名
            curveInto (str):生成されるカーブが格納されるグループ名
    """
    results = sweepMesh(
        curves, [[0, 1, 1], [0.5, 1.0, 1], [1.0, 0.0, 1]], profileCurve,
        interpolationMode=interpolationMode,
        interpolationDistance=interpolationDistance,
        scaleProfileUniform=False, material=material
    )
    grps = [None, None]
    for n, cat in zip((meshInto, curveInto), ('mesh', 'curve')):
        if not n:
            continue
        grp = node.asObject(n)
        if not grp:
            grp = node.createNode('transform', n=meshInto)
        for r in results:
            r[cat] = node.parent(r[cat], grp)

    curves = []
    for data in results:
        sn = data['sweep']
        minmax = {'min': 0, 'max': 100000}
        for crv in data['curve']:
            curves.append(crv)
            for l, tgt, opt, dv in (
                ('width', 'scaleProfileX', minmax, width),
                ('height', 'scaleProfileY', minmax, height),
                ('taper', 'taper', {'min':0, 'max': 1000}, 1),
                ('rotation', 'rotateProfile', {'min':-360, 'max':360}, rotation),
                (
                    'twist', 'twist', {'min':-50, 'max':50, 'smn':-1, 'smx':1},
                    twist
                ),
                (
                    'vDistance', 'interpolationDistance',
                    {'min':0.001, 'max': 1000000, 'smx':10},
                    interpolationDistance
                ),
            ):
                flags = {x: y for x, y in opt.items()}
                flags['default'] = dv
                plug = crv.addFloatAttr(l, **flags)
                plug >> sn/tgt
    if curves:
        cmds.select(curves, r=True)
    return results


def centerBetweenCamToMesh(cameraMatrix, targetMesh, weight=0.5):
    r"""
        Args:
            cameraMatrix (list):カメラ行列
            targetMesh (str):対象となるメッシュオブジェクト
            weight (float):対象オブジェクトへ近づく割合
    """
    targetMesh = _get_mesh(targetMesh)
    cam_pos = node.MVector(cameraMatrix[12:15])
    mesh_pos = node.MVector(targetMesh.closestPoint(cam_pos))
    vec = (mesh_pos- cam_pos) * weight
    
    return list(cam_pos + vec)


def createProjectionCurve(
    cameraMatrix, positionList,
    targetMesh=None, rebuildMode=0, rebuiltSpan=0
):
    r"""
        与えられたカメラポジションからtargetMeshに対する投影カーブを作成する。
        
        Args:
            cameraMatrix (list):投影カメラの行列
            positionList (list):カーブのCV位置のリスト
            targetMesh (str):投影対象メッシュの名前
            rebuildMode (int):リビルド時のスパンを決定する手法
            rebuiltSpan (int):リビルド時のスパン数（0の場合リビルドなし）
    """
    crv_degree = 3
    targetMesh = _get_mesh(targetMesh)
    cam_pos = cameraMatrix[12:15]
    cp = targetMesh.closestPoint(cam_pos)
    cp = node.MVector(cp)
    src_curve = cmds.curve(d=1, p=positionList)
    prj_curves = cmds.polyProjectCurve(
        src_curve, targetMesh,
        ch=1, pointsOnEdges=0, curveSamples=50, automatic=1, tolerance=0.001
    )
    curves = node.toObjects(
        cmds.listConnections(
            prj_curves[0]+'.local',
            s=False, d=True, type='nurbsCurve', shapes=True
        )
    )
    distances = {}
    for crv in curves:
        cl_p = node.MVector(crv.closestPoint(cam_pos))
        distances.setdefault((cl_p - cp).length(), []).append(crv)
    key = min(distances.keys())
    curve = node.parent(distances[key][0].parent(), w=True)[0]
    cmds.delete(prj_curves, src_curve)

    cvs = cmds.ls(curve/'cv[*]', fl=True)
    orig_vec = node.MVector(positionList[-1]) - node.MVector(positionList[0])
    new_vec = (
        node.MVector(cmds.pointPosition(cvs[-1]))
        - node.MVector(cmds.pointPosition(cvs[0]))
    )
    if (orig_vec.normal() * new_vec.normal()) < 0:
        cmds.reverseCurve(curve, ch=1, rpo=1)
    piv_pos = cmds.pointPosition(cvs[0])
    curve.setPivot(piv_pos)

    if rebuiltSpan > 0:
        if rebuildMode == 0:
            crv_shape = curve.shapes(typ='nurbsCurve', ni=True)[0]
            rebuiltSpan = int(crv_shape.length() / rebuiltSpan) - crv_degree
            if rebuiltSpan < 1:
                rebuiltSpan = 1
        cmds.rebuildCurve(
            curve,
            ch=0, rpo=1, rt=0, end=1, kr=0, kcp=0, kep=1, kt=0,
            s=rebuiltSpan, d=crv_degree, tol=0.01
        )
    return curve


def duplicateHair(targetNodes=None):
    to_mesh = convertSelectionToMesh(targetNodes)
    results = []
    for data in to_mesh:
        crv = data['nurbsCurve']
        mesh = node.asObject(data['mesh'][0])
        intp_dist = crv('vDistance')
        width = crv('width')
        height = crv('height')
        rotation = crv('rotation')
        twist = crv('twist')
        mesh_grp = mesh.parent()
        crv_grp = crv.parent()
        new_curve = cmds.duplicate(crv, rr=True)[0]
        cleanup.deleteUnusedIO(new_curve, False)
        cleanup.deleteUnusedUserDefinedAttr(new_curve, False)
        
        mat = surfaceMaterialUtil.listMaterials([mesh])
        if mat:
            material = mat[0][0]
        else:
            material = None
        sweepHair(
            [new_curve], interpolationDistance=intp_dist,
            width=width, height=height, material=material,
            rotation=rotation, twist=twist,
            meshInto=mesh_grp
        )


def duplicateHairAll(targetNodes=None):
    to_mesh = convertSelectionToMesh(targetNodes)
    results = []
    for data in to_mesh:
        mesh = data['mesh'][0]
        duplicated = cmds.duplicate(mesh, un=True)
        for d in duplicated:
            d = node.asObject(d)
            if not d.isType('transform'):
                continue
            if not d.shapes(typ='nurbsCurve'):
                continue
            results.append(d)
    if results:
        cmds.select(results, r=True, ne=True)
    return results


def createHairFromJointChain(joints=None):
    def getPointsFromJointChain(joint, poslist):
        pos = joint.position()
        poslist.append(pos)
        for child in joint.children(type='transform'):
            getPointsFromJointChain(child, poslist)
            break
        return poslist

    joints = node.selected(joints)
    crvs = []
    for joint in joints:
        points = []
        getPointsFromJointChain(joint, points)
        crvs.append(cmds.curve(d=1, p=points))
    sweepHair(crvs)
