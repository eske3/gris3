#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    機械系の仕組みを作るための機能を提供するモジュール。
    
    Dates:
        date:2017/07/18 2:13[Eske](eske3g@gmail.com)
        update:2021/07/26 12:55 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import node, func
cmds = node.cmds


def createThreeAxisRig(joint, aimVector=(1, 0, 0), upVector=(0, 1, 0)):
    r"""
        任意のジョイントに対し、各軸で動くサブジョイントを作成する。
        戻り値として作成された2軸ジョイントと1軸ジョイントを持つ
        タプルを返す。
        
        Args:
            joint (str):
            aimVector (tuple):アイムを表すベクトル
            upVector (tuple):アップを表すベクトル
            
        Returns:
            tuple:
    """
    def createAxisRotater(
        driver, target, aimVector, upVector, oneAxisJoint=None
    ):
        r"""
            aimConstraintを特定軸のみ動く仕組みを作るローカル関数。
            
            Args:
                driver (node.Tranform):ドライバとなるジョイント
                target (node.Transform):軸固定されるターゲット
                aimVector (tuple):aimVectorを表すベクトル
                upVector (tuple):upVectorを表すベクトル
                oneAxisJoint (node.Tranfsorm):
                
            Returns:
                node.Tranfsorm:生成されたコンストレインノード
        """
        cst = node.createUtil('aimConstraint', p=target)
        for plug in cst.listAttr(k=True):
            plug.setKeyable(False)

        # aimベクトルの設定。
        cst('target[0].targetTranslate', aimVector)
        if oneAxisJoint:
            driver.attr('matrix') >> cst/'target[0].targetParentMatrix'
        else:
            cst(
                'target[0].targetParentMatrix', driver('matrix'), type='matrix'
            )

        # upベクトルの仕組みの作成。
        offset_mtx = (
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            upVector[0], upVector[1], upVector[2], 1
        )
        up_mtx = node.createUtil('multMatrix')
        up_mtx('matrixIn[0]', offset_mtx, type='matrix')
        if oneAxisJoint:
            oneAxisJoint.attr('matrix') >> up_mtx/'matrixIn[1]'
        else:
            driver.attr('matrix') >> up_mtx/'matrixIn[1]'
        up_mtx.attr('matrixSum') >> cst/'worldUpMatrix'

        # コンストレインの設定。
        cst('aimVector', aimVector)
        cst('upVector', upVector)
        cst('worldUpType', 1)
        if target.isType('joint'):
            target.attr('jo') >> cst/'constraintJointOrient'
            target.attr('inverseScale') >> cst/'inverseScale'
        target.attr('translate') >> cst/'constraintTranslate'
        ~cst.attr('constraintRotate') >> ~target.attr('r')
        
        return cst

    joint = node.asObject(joint, node.Joint)

    # 2軸で動くジョイントを作成する。
    twoaxis_joint = node.duplicate(joint, po=True)[0]
    twoaxis_joint.clearConnections()

    # 1軸で動くジョイントを作成する。
    oneaxis_joint = node.duplicate(twoaxis_joint)[0]

    # rotateの接続。===========================================================
    aimcst = createAxisRotater(joint, oneaxis_joint, upVector, aimVector)
    # aimコンストレインの設定を変更する。
    pmtx = node.MMatrix(aimcst('target[0].targetParentMatrix'))
    offset = aimcst('target[0].targetTranslate')[0]
    offset_mtx = node.MMatrix(
        [
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            offset[0], offset[1], offset[2], 1
        ]
    )
    r = offset_mtx * pmtx
    v = r[12] - joint('tx'), r[13]-joint('ty'), r[14]-joint('tz')

    pma = node.createUtil('plusMinusAverage')
    pma('input3D[0]', v)
    ~joint.attr('t') >> ~pma.attr('input3D[1]')
    pma.attr('output3D') >> aimcst/'target[0].targetTranslate'
    aimcst('target[0].targetParentMatrix', node.MMatrix(), type='matrix')

    createAxisRotater(
        joint, twoaxis_joint, aimVector, upVector, oneaxis_joint
    )
    # =========================================================================

    # translate, scaleの接続。
    for subjoint in (oneaxis_joint, twoaxis_joint):
        for attr in 'ts':
            ~joint.attr(attr) >> ~subjoint.attr(attr)
        subjoint.editAttr(['t:a', 'r:a', 's:a'], k=False, l=True)

    return (twoaxis_joint, oneaxis_joint)


def wfCreateThreeAxisRig(
    jointlist=None, aimVector=(1, 0, 0), upVector=(0, 1, 0)
):
    r"""
        ワークフローの命名規則に沿った仕様用の作成関数。
        作成された２つのジョイントに対し、リネームも込みで行う。
        
        Args:
            jointlist (list):適応対象ジョイントのリスト
            aimVector (list):エイムを向けるベクトル
            upVector (list):アップを向けるベクトル
            
        Returns:
            list:
    """
    from gris3 import system
    nr = system.GlobalSys().nameRule()
    jointlist = node.selected(jointlist)
    targets = [(x, nr(x())) for x in jointlist]
    result = []
    for joint, name in targets:
        two, one = createThreeAxisRig(joint, aimVector, upVector)
        name.setSuffix('TwoAx')
        two.rename(name())
        name.setSuffix('OneAx')
        one.rename(name())
        result.append(
            (node.asObject(two()), node.asObject(one()))
        )
    return result

    
def setupActuator(actA, actB, aimA, upA, aimB=None, upB=None):
    r"""
        向かい合う2つのTransformが常に向き合うようにセットアップする。
        この動作は動力シリンダー系に使用できる。
        
        Args:
            actA (str):TransformノードA
            actB (str):TransformノードB
            aimA (tuple):actBの方に向けるactAのベクトル
            upA (tuple):actAのアップベクトル
            aimB (tuple):actAの方に向けるactBのベクトル
            upB (tuple):actBのアップベクトル
            
        Returns:
            tuple:actAおよびactBに使用されたコンストレイン
    """
    def doConst(a, b, aim, up, a_parents, b_parents):
        r"""
            ローカルのコンストレインを行う
            
            Args:
                a (str):エイミングする対象ノード
                b (str):エイミングされるノード
                aim (tuple):bの方に向けるaのベクトル
                up (tuple):aのアップベクトル
                a_parents (list):aの親のリスト
                b_parents (list):bの親のリスト
                
            Returns:
                any:(node.Constraint):生成されたコンストレインノード
        """
        c = func.localConstraint(
            cmds.aimConstraint, a, b, aim=aim, upVector=up, worldUpType='none'
        )
        for parents, attr, m, f in (
            (a_parents, 'target[0].targetParentMatrix', 'm', lambda x:x),
            (b_parents, 'cpim', 'im', reversed)
        ):
            if not parents:
                c(
                    attr, node.identityMatrix(),
                    type='matrix'
                )
            else:
                if len(parents) == 1:
                    plug = parents[0].attr(m)
                else:
                    mltmtx = node.createUtil('multMatrix')
                    for i, p in enumerate(f(parents)):
                        p = node.asObject(p)
                        p.attr(m) >> '%s.matrixIn[%s]'%(mltmtx, i)
                    plug = mltmtx.attr('matrixSum')
                plug >> c/attr
        return c
    csts = []
    i_mtx = node.identityMatrix()
    if not aimB:
        aimB = [-x for x in aimA]
    if not upB:
        upB = [-x for x in upA]
    a_parents, b_parents = func.listCommonParentPathList(actA, actB)
    a_parents = node.toObjects(a_parents[:-1])
    b_parents = node.toObjects(b_parents[:-1])

    csts.append(doConst(actB, actA, aimA, upA, b_parents, a_parents))
    csts.append(doConst(actA, actB, aimB, upB, a_parents, b_parents))
    return csts
