#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2023/08/24 13:30 Eske Yoshinob[eske3g@gmail.com]
        update:2023/08/24 15:04 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2023 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import node
from ..mayaCmds import Mel
from maya import mel, cmds
plugin = 'mayaHIK'
char_name = 'character'
if not cmds.pluginInfo(plugin, q=True, l=True):
    cmds.loadPlugin(plugin)
mel = Mel()

HIK_HUMAN_TEMPLATE = {
    "J_C_hip": "Hips",
    "J_C_spineA": "Spine",
    "J_C_spineB": "Spine1",
    "J_C_spineC": "Spine2",
    "J_L_clavicle": "LeftShoulder",
    "J_R_clavicle": "RightShoulder",
    "J_L_uparm": "LeftArm",
    "J_R_uparm": "RightArm",
    "J_L_lowarm": "LeftForeArm",
    "J_R_lowarm": "RightForeArm",
    "J_L_hand": "LeftHand",
    "J_R_hand": "RightHand",
    "J_L_thumbBase": "LeftHandThumb1",
    "J_R_thumbBase": "RightHandThumb1",
    "J_L_thumbMiddle": "LeftHandThumb2",
    "J_R_thumbMiddle": "RightHandThumb2",
    "J_L_thumbDistal": "LeftHandThumb3",
    "J_R_thumbDistal": "RightHandThumb3",
    "J_L_indexBase": "LeftHandIndex1",
    "J_R_indexBase": "RightHandIndex1",
    "J_L_indexMiddle": "LeftHandIndex2",
    "J_R_indexMiddle": "RightHandIndex2",
    "J_L_indexDistal": "LeftHandIndex3",
    "J_R_indexDistal": "RightHandIndex3",
    "J_L_middleBase": "LeftHandMiddle1",
    "J_R_middleBase": "RightHandMiddle1",
    "J_L_middleMiddle": "LeftHandMiddle2",
    "J_R_middleMiddle": "RightHandMiddle2",
    "J_L_middleDistal": "LeftHandMiddle3",
    "J_R_middleDistal": "RightHandMiddle3",
    "J_L_ringBase": "LeftHandRing1",
    "J_R_ringBase": "RightHandRing1",
    "J_L_ringMiddle": "LeftHandRing2",
    "J_R_ringMiddle": "RightHandRing2",
    "J_L_ringDistal": "LeftHandRing3",
    "J_R_ringDistal": "RightHandRing3",
    "J_L_pinkyBase": "LeftHandPinky1",
    "J_R_pinkyBase": "RightHandPinky1",
    "J_L_pinkyMiddle": "LeftHandPinky2",
    "J_R_pinkyMiddle": "RightHandPinky2",
    "J_L_pinkyDistal": "LeftHandPinky3",
    "J_R_pinkyDistal": "RightHandPinky3",
    "J_L_thigh": "LeftUpLeg",
    "J_R_thigh": "RightUpLeg",
    "J_L_lowleg": "LeftLeg",
    "J_R_lowleg": "RightLeg",
    "J_L_foot": "LeftFoot",
    "J_R_foot": "RightFoot",
    "J_L_toe": "LeftToeBase",
    "J_R_toe": "RightToeBase",
    "J_C_neck": "Neck",
    "J_C_head": "Head"
}


def createSetCharacter(charName):
    r"""
        HIK用キャラクターノードをカレントに設定する。
        ない場合は作成してからカレントにセットする。
        
        Args:
            charName (str):
            
        Return:
            node.AbstractNode: 設定されたキャラクターノード。
    """
    ch_n = node.ls(charName, type='HIKCharacterNode')
    char = None
    if ch_n:
        current = mel.hikGetCurrentCharacter()
        if ch_n[0] != current:
            mel.hikSetCurrentCharacter(ch_n[0]) 
        print('# Set character : {}'.format(charName))
        char = ch_n[0]
    else:
        ch_n = mel.hikCreateCharacter(charName)
        print('# Create character : {}'.format(ch_n))
        char = node.asObject(ch_n)
    return char


def getHumanIkIdMap():
    r"""
        ヒューマンIKのノード名と対応するIDのマップを返す。

        Returns:
            dict:
    """
    result = {}
    for i in range(cmds.hikGetNodeCount()):
        name = cmds.GetHIKNodeName(i)
        if not name:
            break
        result[name] = i
    return result


def adjustPropertyStateParams(charName):
    def getRollValue(charaName, rollType, default):
        rollSk = mel.hikGetSkNode(charName, cmds.hikGetNodeIdFromName(rollType))
        return default if rollSk else 1.0

    def setRollValue(charName, side, part, val=0.4):
        rollVal = getRollValue(charName, '{}{}'.format(side, part), val)
        propertyState('{}{}Ex'.format(side, part), rollVal)

    if not charName('InputCharacterizationLock'):
        return
    propertyState = node.asObject(
        mel.hikGetProperty2StateFromCharacter(charName)
    )
    if not propertyState:
        return

    for side in ('Left', 'Right'):
        s = side.lower()
        for part in ('ForeArmRoll', 'ArmRoll'):
            setRollValue(charName, side, part)
    
        for part in ('ElbowRoll', 'ShoulderRoll'):
            propertyState('{}{}'.format(s, part), 0.0)
        
        for part in ('UpLegRoll', 'LegRoll'):
            setRollValue(charName, side, part)

        for part in ('HipRoll', 'KneeRoll'):
            propertyState('{}{}'.format(s, part), 0.0)

    # Adjust Contacts positions
    tX = charName('LeftFootTx') - charName('LeftUpLegTx')
    tY = charName('LeftFootTy') - charName('LeftUpLegTy')
    tZ = charName('LeftFootTz') - charName('LeftUpLegTz')
    import math
    tLen = math.sqrt(tX * tX + tY * tY + tZ * tZ)
    # FEET
    footBottomToAnkle = charName('LeftFootTy')
    left_toe_base = mel.hikGetSkNode(
        charName, cmds.hikGetNodeIdFromName('LeftToeBase')
    )
    if footBottomToAnkle < 0:
        # Feet seem to be below the floor floor
        # Issue a warning and guess a better footBottomToAnkle value because
        # that value plays a major role in retargetting setups
        if left_toe_base:
            footBottomToAnkle = (
                charName('LeftFootTy') - charName('LeftToeBaseTy')
            )
        else:
            footBottomToAnkle = 0
    footBottomToAnkle = abs(footBottomToAnkle)
    propertyState('FootBottomToAnkle', footBottomToAnkle)
    # Check if we have a toe..
    if left_toe_base:
        footLength = abs(
            2.0 * (charName('LeftToeBaseTz') - charName('LeftFootTz'))
        )
    else:
        footLength = tLen / 3.0

    # Basic mode
    for attr in ('CtrlPullLeftFoot', 'CtrlPullRightFoot'):
        cmds.setAttr(mel.hikGetSrcOnEffector(propertyState/attr), 0.0)
    
    for attr in (
        'FootBackToAnkle', 'FootMiddleToAnkle', 'FootFrontToMiddle',
        'FootInToAnkle', 'FootOutToAnkle'
    ):
        factor = 2.0 if attr == 'FootMiddleToAnkle' else 4.0
        propertyState(attr, footLength / factor)

    # HAND
    handHeight = tLen / 25.0
    height = handHeight if handHeight > 0.5 else 0.5
    propertyState('HandBottomToWrist', height)
    propertyState('HandBackToWrist', 0.01)

    # Basic mode
    for attr in ('CtrlChestPullLeftHand', 'CtrlChestPullRightHand'):
        cmds.setAttr(mel.hikGetSrcOnEffector(propertyState/attr), 0.0)

    # Check of we have a finger..
    if mel.hikGetSkNode(charName, mel.hikGetNodeIdFromName('LeftFingerBase')):
        handLength = 2.0 * (
            charName('LeftHandTx') - charName('LeftFingerBaseTx')
        )
        handLength = abs(handLength)
    else:
        handLength = footLength * 0.66
    for attr in (
        'HandMiddleToWrist', 'HandFrontToMiddle', 'HandInToWrist',
        'HandOutToWrist'
    ):
        propertyState(attr, handLength * 0.5)

    # Finger tips
    fingerFffectorSize = tLen * .0125
    for side in ('Left', 'Right'):
        for member in ('Foot', 'Hand'):
            for finger in (
                'Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'ExtraFinger'
            ):
                propertyState(side+member+finger+'Tip', fingerFffectorSize)


def lockCharacter(charNode):
    charNode('InputCharacterizationLock', True)
    mel.hikPostCharacterisationStep(charNode)
    adjustPropertyStateParams(charNode)
    for i in range(cmds.hikGetNodeCount()):
        hik_n = node.asObject(mel.hikGetSkNode(charNode, i))
        if not hik_n:
            continue
        try:
            hik_n('v', k=False, cb=True)
        except:
            pass
    mel.hikSetInactiveStanceInput(charNode)


def registerJoints(charNode, hikMappingDic, namespace):
    hik_id_map = getHumanIkIdMap()
    for joint_name, part in hikMappingDic.items():
        hik_id = hik_id_map[part]
        mel.hikSetCharacterObject(namespace+joint_name, charNode, hik_id, 0)
    lockCharacter(charNode)


def createFloorHik(charNode):
    #Create plane 
    # pm.polyPlane(sx=1, sy=1)
    # floor = pm.selected()[0]
    # floor.scale.set([1000,1000,1000])
    # pm.makeIdentity(a=True, t=True, r=True, s=True)
    
    #Enable FloorContact
    hik_properties = node.ls(
        cmds.listHistory(charNode), type='HIKProperty2State'
    )[0]
    hik_properties('FloorContact' ,True)

    #Connect plane and HIK
    if not cmds.objExists(mel.hikGetControlRig(charNode)):
        raise RuntimeError('ControlRig doesn\'t exsit')
    solver = mel.hikGetSolverFromCharacter(charNode)
    print('--> %s' % solver)
    hik_pin = cmds.listConnections(solver, type='HIKPinning2State')
    print(':: %s' % hik_pin)
    hik_effector = cmds.listConnections(hik_pin, type='HIKEffector2State')
    print(hik_effector)
    # HIKEffector2StateNode = pm.ls(sl=True)[0]
    # return HIKEffector2StateNode
    
    # pm.connectAttr(floor.worldMatrix, HIKEffector2StateNode.leftFootFloorGX)
    # pm.connectAttr(floor.worldMatrix, HIKEffector2StateNode.rightFootFloorGX)


def setupHuman(charName, hikMappingDic=None, namespace=''):
    r"""
        Args:
            charName (str):
            hikMappingDic (dict):
            namespace (str):
    """
    if namespace and not namespace.endswith(':'):
        namespace = namespace + ':'
    char = createSetCharacter(charName)
    registerJoints(char, hikMappingDic, namespace)
    mel.hikCreateControlRig()
    # createFloorHik(char)
