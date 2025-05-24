#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2021/10/12 11:31 eske yoshinob[eske3g@gmail.com]
        update:2023/11/13 15:28 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2021 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import re
from ... import node, func
from maya import cmds, mel

# For the human arm and leg Ik/Fk switch.                                    //
# /////////////////////////////////////////////////////////////////////////////
NodeMatchingTable = {
    'arm': {
        'ik_trs': [
            {
                'input': 'armIk_ctrlProxy',
                'output': 'armIk_ctrl',
                'target': 'hand_fkJnt',
            }
        ],

        'ik_rot': [
            {
                'input': 'armIk_ctrlProxy',
                'output': 'armIk_ctrl',
                'target': 'hand_fkJnt',
            },
            {
                'input': 'armHandRot_ikJnt',
                'output': 'armHandRot_ctrl',
                'target': 'hand_fkJnt',
            }
        ],
        'ikPv': {
            'armIkRole_ctrl': {
                'aimTarget': 'armEnd_loc',
                'rotationUp': 'lowarm_fkJnt',
            },
        },
        'fkMatch': [
            [
                'armUparmFK_ctrl', {
                    'target': 'uparm_ikJnt', 'input': 'uparm_fkJnt'
                },
            ],
            [
                'armLowarmFk_ctrl', {
                    'target': 'lowarm_ikJnt', 'input': 'lowarm_fkJnt'
                },
            ],
            [
                'armHandFk_ctrl', {
                    'target': 'hand_ikJnt', 'input': 'hand_fkJnt',
                },
            ]
        ],
        'scaling': [
            ('uparmScale_ctrl', 'armUparmFK_ctrl'),
            ('lowarmScale_ctrl', 'armLowarmFk_ctrl'),
            ('handScale_ctrl', 'armHandFk_ctrl'),
        ],
        'ikScalingFactor': {
            'srcNode': 'lowarm_ikJnt',
            False : ['uparmScale_ctrl', 'lowarmScale_ctrl'],
            True : ['armUparmFK_ctrl', 'armLowarmFk_ctrl'],
        }
    },

    'leg': {
        'ik_trs': [
            {
                'input': 'leg{suffix}Ik_ctrlProxy',
                'output': 'leg{suffix}Ik_ctrl',
                'target': 'foot{suffix}_fkJnt',
            }
        ],
        'ik_rot': [
            {
                'input': 'leg{suffix}Ik_ctrlProxy',
                'output': 'leg{suffix}Ik_ctrl',
                'target': 'foot{suffix}_fkJnt',
            },
        ],
        'ikPv': {
            'leg{suffix}IkRole_ctrl': {
                'aimTarget': 'leg{suffix}End_loc',
                'rotationUp': 'lowleg{suffix}_fkJnt',
            },
        },
        'toeIkMatch': {
            'fkMatch':[
                [
                    'leg{suffix}Toe_ctrl', {
                        'target': 'toe{suffix}_fkJnt',
                        'input': 'toe{suffix}_ikJnt'
                    },
                ]
            ],
            'postProcess': [
                ('leg{suffix}Step_ctrl', 'ry', 0),
            ]
        },
        'fkMatch': [
            [
                'leg{suffix}ThighFK_ctrl', {
                    'target': 'thigh{suffix}_ikJnt',
                    'input': 'thigh{suffix}_fkJnt'
                },
            ],
            [
                'leg{suffix}LowlegFk_ctrl', {
                    'target': 'lowleg{suffix}_ikJnt',
                    'input': 'lowleg{suffix}_fkJnt'
                },
            ],
            [
                'leg{suffix}FootFk_ctrl', {
                    'target': 'foot{suffix}_ikJnt',
                    'input': 'foot{suffix}_fkJnt',
                },
            ],
            [
                'leg{suffix}Toe{l_suffix}Fk_ctrl', {
                    'target': 'toe{suffix}_ikJnt', 'input': 'toe{suffix}_fkJnt',
                },
            ]
        ],
        'scaling': [
            ('thigh{suffix}Scale_ctrl', 'leg{suffix}ThighFK_ctrl'),
            ('lowleg{suffix}Scale_ctrl', 'leg{suffix}LowlegFk_ctrl'),
            ('foot{suffix}Scale_ctrl', 'leg{suffix}FootFk_ctrl'),
            ('toe{suffix}Scale_ctrl', 'leg{suffix}Toe{l_suffix}Fk_ctrl'),
        ],
        'ikScalingFactor': {
            'srcNode': 'lowleg{suffix}_ikJnt',
            False : ['thigh{suffix}Scale_ctrl', 'lowleg{suffix}Scale_ctrl'],
            True : ['leg{suffix}ThighFK_ctrl', 'leg{suffix}LowlegFk_ctrl'],
        }
    },

    # 四足の手足系。
    'quadFrontLeg': {
        'ik_trs': [
            {
                'input': 'quadFrontLegIk_ctrlProxy',
                'output': 'quadFrontLegIk_ctrl',
                'target': 'wrist_fkJnt',
            }
        ],
        'ik_rot': [
            {
                'input': 'quadFrontLegIk_ctrlProxy',
                'output': 'quadFrontLegIk_ctrl',
                'target': 'wrist_fkJnt',
            }
        ],
        'ikPv': {
            'quadFrontLegIkRole_ctrl': {
                'aimTarget': 'quadFrontLegEnd_loc',
                'rotationUp': 'lowarm_fkJnt',
                'aimFactor': -1,
            },
        },
        'toeIkMatch': {
            'fkMatch':[
                [
                    'quadFrontLegToe_ctrl', {
                        'target': 'hand_fkJnt', 'input': 'hand_ikJnt'
                    },
                ]
            ],
            'postProcess': [
                ('quadFrontLegStep_ctrl', 'ry', 0),
                ('quadFrontLegStep_ctrl', 'useHeelRotation', 0),
            ]
        },
        'fkMatch': [
            [
                'quadFrontLegUparmFK_ctrl', {
                    'target': 'uparm_ikJnt', 'input': 'uparm_fkJnt'
                },
            ],
            [
                'quadFrontLegLowarmFk_ctrl', {
                    'target': 'lowarm_ikJnt', 'input': 'lowarm_fkJnt'
                },
            ],
            [
                'quadFrontLegWristFk_ctrl', {
                    'target': 'wrist_ikJnt', 'input': 'wrist_fkJnt',
                },
            ],
            [
                'quadFrontLegHandFk_ctrl', {
                    'target': 'hand_ikJnt', 'input': 'hand_fkJnt',
                },
            ]
        ],
        'scaling': [
            ('uparmScale_ctrl', 'quadFrontLegUparmFK_ctrl'),
            ('lowarmScale_ctrl', 'quadFrontLegLowarmFk_ctrl'),
            ('wristScale_ctrl', 'quadFrontLegWristFk_ctrl'),
            ('handScale_ctrl', 'quadFrontLegHandFk_ctrl'),
        ],
        'ikScalingFactor': {
            'srcNode': 'lowarm_ikJnt',
            False : ['uparmScale_ctrl', 'lowarmScale_ctrl'],
            True : ['quadFrontLegUparmFK_ctrl', 'quadFrontLegLowarmFk_ctrl'],
        }
    },

    'quadBackLeg': {
        'preProcess': [
            ('quadBackLegIk_ctrl', 'footAiming', 0),
        ],
        'ik_trs': [
            {
                'input': 'quadBackLegIk_ctrlProxy',
                'output': 'quadBackLegIk_ctrl',
                'target': 'ball_fkJnt',
            }
        ],
        'ik_rot': [
            {
                'input': 'quadBackLegIk_ctrlProxy',
                'output': 'quadBackLegIk_ctrl',
                'target': 'ball_fkJnt',
            },
        ],
        'ikPv': {
            'quadBackLegIkRole_ctrl': {
                'aimTarget': 'quadBackLegEnd_loc',
                'rotationUp': 'lowleg_fkJnt',
            },
        },
        'toeIkMatch': {
            'fkMatch':[
                [
                    'quadBackLegToe_ctrl', {
                        'target': 'toe_fkJnt', 'input': 'toe_ikJnt'
                    },
                ]
            ],
            'postProcess': [
                ('quadBackLegStep_ctrl', 'ry', 0)
            ]
        },
        'fkMatch': [
            [
                'quadBackLegThighFK_ctrl', {
                    'target': 'thigh_ikJnt', 'input': 'thigh_fkJnt'
                },
            ],
            [
                'quadBackLegLowlegFk_ctrl', {
                    'target': 'lowleg_ikJnt', 'input': 'lowleg_fkJnt'
                },
            ],
            [
                'quadBackLegFootFk_ctrl', {
                    'target': 'foot_ikJnt', 'input': 'foot_fkJnt',
                },
            ],
            [
                'quadBackLegBallFk_ctrl', {
                    'target': 'ball_ikJnt', 'input': 'ball_fkJnt',
                },
            ],
            [
                'quadBackLegToeFk_ctrl', {
                    'target': 'toe_ikJnt', 'input': 'toe_fkJnt',
                },
            ]
        ],
        'footRotationMatch': {
            'target': 'quadBackLegBall_ctrl', 'input': 'foot_fkJnt'
        },
        'scaling': [
            ('thighScale_ctrl', 'quadBackLegThighFK_ctrl'),
            ('lowlegScale_ctrl', 'quadBackLegLowlegFk_ctrl'),
            ('footScale_ctrl', 'quadBackLegFootFk_ctrl'),
            ('ballScale_ctrl', 'quadBackLegBallFk_ctrl'),
            ('toeScale_ctrl', 'quadBackLegToeFk_ctrl'),
        ],
        'ikScalingFactor': {
            'srcNode': 'lowleg_ikJnt',
            False : ['thighScale_ctrl', 'lowlegScale_ctrl', 'footScale_ctrl'],
            True : [
                'quadBackLegThighFK_ctrl', 'quadBackLegLowlegFk_ctrl',
                'quadBackLegFootFk_ctrl'
            ],
        }
    },
}


def listSwitcher(switchers=None):
    r"""
        任意のリスト内にあるik/fkスイッチャーをフィルターして返す。
        戻ろ値はスイッチャーノードをキー、そのノードのパーツ部位、ベースの名前、
        ノードの部位を表す文字列、ネームスペースの情報を持つリストを値として
        持つOrderdedDict。
        
        Args:
            switchers (list or None):
            
        Returns:
            OrderedDict:
    """
    from collections import OrderedDict
    part_ptn = re.compile('\:?(arm|leg|quadBackLeg|quadFrontLeg)(.*)Param')
    switchers = node.selected(switchers)
    nodelist = OrderedDict()
    for switcher in switchers:
        if not switcher.hasAttr('ikBlend'):
            continue
        obj = part_ptn.search(switcher)
        if not obj:
            continue
        part = obj.group(1)
        suffix = obj.group(2)
        name = func.Name(switcher)
        s = '_' + name.position()

        # switcherのネームスペースを取得。
        ns = switcher.split(':')
        ns = ns[0] + ':' if len(ns) > 1 else ''

        nodelist[switcher] = [part, name, s, ns, suffix]
    return nodelist


def preProcess(info, namespace, side):
    r"""
        事前処理を行う。
        (info内には操作対象ノード、操作対象アトリビュート、設定する値)
        を持ったtupleを持つリストを格納し、アトリビュート設定を行っていく。
        アトリビュートの設定以外の複雑な処理は今のところ不可。

        Args:
            info (list):
            namespace (str):操作対象ノードのネームスペース
            side (str):位置を表す文字列。
    """
    if not info:
        return
    for key, attr, val in info:
        tgt = node.asObject(namespace + key + side)
        tgt(attr, val)


def connects(info, namespace, side, suffix, offsetMatrix, flags, setKey=False):
    r"""
        IKコントローラの位置合わせを行う。

        Args:
            info (list):NodeMatchingTable[パーツ名][ik_trs/ik_rot]の値
            namespace (str):操作対象ノードのネームスペース
            side (str):位置を表す文字列。
            offsetMatrix (node.MMatrix):全体移動のオフセット行列
            flags (bin):左から順にTRSShの設定を行うかどうかのフラグスイッチ
            setKey (bool):セットキーを行うかどうか
    """
    for i in info:
        input, output, target = [
            node.asObject(namespace + i[x].format(suffix=suffix) + side)
            for x in ['input', 'output', 'target']
        ]
        # input = node.asObject(
            # namespace + i['input'].format(suffix=suffix) + side
        # )
        # output = node.asObject(
            # namespace + i['output'].format(suffix=suffix) + side
        # )
        # target = node.asObject(
            # namespace + i[].format(suffix=suffix) + side
        # )
        if output.hasAttr('ikFkSwitchTarget'):
            tmp = output.attr('ikFkSwitchTarget').source()
            if tmp:
                target = tmp
        
        tgt_mtx = node.MMatrix(target.matrix())
        output_p_mtx = node.MMatrix(output.parent().inverseMatrix())
        m = list(tgt_mtx * offsetMatrix * output_p_mtx)
        output.setMatrix(m, False, flags=flags)
        if setKey:
            cmds.setKeyframe(output)


def aimIkRolePlane(info, namespace, side, suffix, setKey=False):
    r"""
        Args:
            info (list):
            namespace (str):
            side (str):
            setKey (bool):セットキーを行うかどうか
    """
    for key in info:
        factor = -1 if side.endswith('R') else 1
        target = node.asObject(namespace + key.format(suffix=suffix) + side)
        aim_target = node.asObject(
            namespace + info[key]['aimTarget'].format(suffix=suffix) + side
        )
        rotation_up = node.asObject(
            namespace + info[key]['rotationUp'].format(suffix=suffix) + side
        )
        aim_factor = info[key].get('aimFactor', 1)

        proxy = target.destinations(type='constraint')[0]
        space_proxy = proxy.parent()
        
        dmy_space = node.createNode('transform')
        dmy_space.fitTo(space_proxy)
        dmy = node.createNode('transform', p=dmy_space)

        cnst_attr = cmds.listAttr(target + '.r', k=True, sn=True)
        if not cnst_attr:
            continue
        cnst_attr = [x[-1] for x in cnst_attr]
        skip_attr = [x for x in 'xyz' if x not in cnst_attr]

        cmds.delete(
            cmds.aimConstraint(
                aim_target, dmy,
                aimVector=[factor * aim_factor, 0, 0], upVector=[0, 0, factor],
                worldUpType='object', worldUpVector=[0, 1, 0],
                worldUpObject=rotation_up, skip=skip_attr
            )
        )
        for axis in 'xyz':
            if axis in skip_attr:
                continue
            value = dmy('r'+axis)
            if setKey:
                cmds.setKeyframe(target, at='r'+axis, v=value)
            else:
                target('r'+axis, value)
        cmds.delete(dmy_space, dmy)


def fkMatching(
    info, namespace, side, suffix, offsetMatrix, flags=0b1110, setKey=False
):
    r"""
        FKコントローラをIKの骨にあわせる。
        
        Args:
            info (list):NodeMatchingTable[パーツ名][fkMatch]に対応する内容
            namespace (str):操作対象ノードのネームスペース
            side (str):位置を表す文字列。
            offsetMatrix (node.MMatrix):全体移動のオフセット行列
            flags (bin):左から順にTRSShの設定を行うかどうかのフラグスイッチ
            setKey (bool):セットキーを行うかどうか
    """
    for data in info:
        ctrl = node.asObject(
            namespace +
            data[0].format(suffix=suffix, l_suffix=suffix.lower()) +
            side
        )
        target = node.asObject(
            namespace + data[1]['target'].format(suffix=suffix) + side
        )
        input = node.asObject(
            namespace + data[1]['input'].format(suffix=suffix) + side
        )

        tgt_mtx = node.MMatrix(target.matrix())
        ctrl_p_mtx = node.MMatrix(ctrl.parent().inverseMatrix())
        m = list(tgt_mtx * offsetMatrix * ctrl_p_mtx)
        ctrl.setMatrix(m, False, flags=flags)
        if setKey:
            cmds.setKeyframe(ctrl)


def scaleMatching(nodelist, namespace, side, suffix, ikToFk=True, setKey=False):
    r"""
        FKとIKのスケールコントローラ情報をあわせる。
        
        Args:
            nodelist (list):対象ノードのリスト
            namespace (str):ネームスペース
            side (str):位置を表す文字列。
            ikToFk (bool):ikからfkへ切り替えるかどうか
            setKey (any):セットキーを行うかどうか
    """
    i, j = [1, 0] if ikToFk else [0, 1]
    for n in nodelist:
        src = node.asObject(
            ''.join([
                namespace, n[i].format(suffix=suffix, l_suffix=suffix.lower()),
                side
            ])
        )
        dst = node.asObject(
            ''.join([
                namespace, n[j].format(suffix=suffix, l_suffix=suffix.lower()),
                side
            ])
        )
        for axis in 'xyz':
            value = src('s'+axis)
            if setKey:
                cmds.setKeyframe(dst, at=('s'+axis), v=value)
            else:
                dst('s'+axis, value)


def getScalingFactor(part, namespace, side, suffix):
    r"""
        SoftIK用のスケール補正値を取得する。
        見つからない場合は1.0を返す。
        
        Args:
            part (str):操作対象部位(armかleg)
            namespace (str):操作対象ノードのネームスペース
            side (str):位置を表す文字列。
            
        Returns:
            float:
    """
    jname = ''.join(
        (
            namespace,
            NodeMatchingTable[part]['ikScalingFactor']['srcNode'].format(
                suffix=suffix
            ),
            side, '.scaleX'
        )
    )
    md = cmds.listConnections(
        jname, s=True, d=False, type='multDoubleLinear'
    )
    if not md:
        return 1.0
    return cmds.getAttr(md[0] + '.input1')


def fixStretchFactor(part, namespace, side, suffix, isIkToFk, setKey=False):
    r"""
        Args:
            part (str):操作対象部位(armかleg)
            namespace (str):操作対象ノードのネームスペース
            side (str):位置を表す文字列。
            isIkToFk (bool):IKからFKへのマッチングを行うかどうか
            setKey (bool):セットキーを行うかどうか
    """
    scaling_factor = getScalingFactor(part, namespace, side, suffix)
    for ctrl in NodeMatchingTable[part]['ikScalingFactor'][isIkToFk]:
        ctrl = node.asObject(
            ''.join([namespace, ctrl.format(suffix=suffix), side])
        )
        if isIkToFk:
            value = ctrl('scaleX') * scaling_factor
        else:
            value = ctrl('scaleX') / scaling_factor
        if setKey:
            cmds.setKeyframe(ctrl, at='scaleX', v=value)
        else:
            ctrl('scaleX', value)


def matchIkToFk(part, ns, s, suffix, offsetMatrix, setKey=False):
    r"""
        FKからIKへのスイッチをおこなう。
        
        Args:
            part (str):操作対象部位(armかleg)
            ns (str):操作対象ノードのネームスペース
            s (str):位置を表す文字列。
            offsetMatrix (node.MMatrix):全体移動のオフセット行列
            setKey (bool):セットキーを行うかどうか
    """
    preProcess(NodeMatchingTable[part].get('preProcess'), ns, s)
    # IKの位置をあわせる。=====================================================
    # IKコントローラの移動値をあわせる。
    connects(
        NodeMatchingTable[part]['ik_trs'], ns, s, suffix,
        offsetMatrix, 0b1000, setKey
    )
    # IKコントローラの回転値をあわせる。
    connects(
        NodeMatchingTable[part]['ik_rot'], ns, s, suffix,
        offsetMatrix, 0b0100, setKey
    )
    # =========================================================================
    
    # 足首の回転を合わせる。===================================================
    info = NodeMatchingTable[part].get('footRotationMatch')
    if info:
        tgt = node.asObject(ns + info['target'] + s)
        dmy = node.createNode('transform', p=tgt.parent())
        dmy.fitTo(node.asObject(ns + info['input'] + s))
        for ax in 'xyz':
            tgt('r' + ax, dmy('r' + ax))
        # dmy.delete()
    # =========================================================================

    # 回転プレーンコントローラをあわせる。
    aimIkRolePlane(NodeMatchingTable[part]['ikPv'], ns, s, suffix, setKey)

    # 足のつま先コントローラをあわせる。=======================================
    if 'toeIkMatch' not in NodeMatchingTable[part]:
        return
    match_info = NodeMatchingTable[part]['toeIkMatch']
    for tgt, attr, val in match_info.get('postProcess', []):
        t = tgt.format(suffix=suffix)
        if setKey:
            cmds.setKeyframe(ns + t + s, at=attr, v=val)
        else:
            cmds.setAttr(ns + t + s + '.'+attr, val)
    fkMatching(
        match_info['fkMatch'], ns, s, suffix,
        offsetMatrix, 0b0100, setKey
    )
    # =========================================================================
    # /////////////////////////////////////////////////////////////////////////


def matchIkFk(switchers=None, ikToFk=0, worldTrs='world_trs'):
    r"""
        IK・FKを切り替える。
        
        Args:
            switchers (list):
            ikToFk (int):0で自動、1でIK、2でFKにあわせる。
            worldTrs (str):全体移動、回転を行うTransformノード名
    """
    pre_selection = cmds.ls(sl=True)
    switchers = listSwitcher(switchers)

    for switcher, data in switchers.items():
        part, name, s, ns, suffix = data
        if ikToFk == 0:
            ik_state = True if switcher('ikBlend') > 0.5 else False
        elif ikToFk == 1:
            ik_state = False
        else:
            ik_state = True
        ik_to_fk = ik_state == False
        switcher('ikBlend', ik_to_fk)

        world_trs = node.asObject(ns+worldTrs)
        offset_mtx = node.MMatrix(
            world_trs.matrix() if world_trs else node.identityMatrix()
        )

        scaleMatching(
            NodeMatchingTable[part]['scaling'], ns, s, suffix, ik_to_fk
        )
        fixStretchFactor(part, ns, s, suffix, ik_to_fk)
        if ik_state:
            # IKからFKに切り替える。
            fkMatching(
                NodeMatchingTable[part]['fkMatch'], ns, s, suffix, offset_mtx
            )
        else:
            # FKからIKに切り替える。
            matchIkToFk(part, ns, s, suffix, offset_mtx)

    if pre_selection:
        cmds.select(pre_selection, r=True, ne=True)
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////


def bakeIkFk(
    switchers=None, ikToFk=True, startFrame=None, endFrame=None,
    worldTrs='world_trs'
):
    r"""
        Args:
            switchers (list):
            ikToFk (bool):Trueの場合IKからFKへベイクする。
            startFrame (int or None):
            endFrame (int or None):
            worldTrs (str):全体移動、回転を行うTransformノード名
    """
    switchers = listSwitcher(switchers)
    if startFrame is None:
        startFrame = int(cmds.playbackOptions(q=True, min=True))
    if endFrame is None:
        endFrame = int(cmds.playbackOptions(q=True, max=True))
    print('Bake from {} - {}'.format(startFrame, endFrame))
    
    is_autokey = cmds.autoKeyframe(q=True,state=True)
    if is_autokey:
        cmds.autoKeyframe(state=False)

    progressbar = mel.eval('$gMainProgressBar = $gMainProgressBar;')
    cmds.progressBar(
        progressbar,
        e=True, bp=True, status='Baking ...',
        minValue=0, maxValue=(endFrame-startFrame), isInterruptable=True
    )
    def _proc():
        for f in range(startFrame, endFrame+1):
            cmds.currentTime(f)
            for switcher, data in switchers.items():
                if cmds.progressBar(progressbar, q=True, ic=True):
                    return
                part, name, s, suffix, ns = data
                world_trs = node.asObject(ns+worldTrs)
                offset_mtx = node.MMatrix(
                    world_trs.matrix() if world_trs else node.identityMatrix()
                )

                scaleMatching(
                    NodeMatchingTable[part]['scaling'],
                    ns, s, suffix, ikToFk, True
                )
                fixStretchFactor(part, ns, s, suffix, ikToFk, True)
                if ikToFk:
                    fkMatching(
                        NodeMatchingTable[part]['fkMatch'], ns, suffix, s,
                        offset_mtx, setKey=True
                    )
                else:
                    matchIkToFk(part, ns, s, suffix, offset_mtx, True)
            cmds.progressBar(progressbar, e=True, step=1)
    try:
        _proc()
    except Exception as e:
        raise e
    finally:
        if is_autokey:
            cmds.autoKeyframe(state=True)
        cmds.progressBar(progressbar, e=True, endProgress=True)
    for switcher in switchers:
        switcher('ikBlend', ikToFk==False)
