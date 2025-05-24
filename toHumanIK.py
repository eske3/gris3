#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ベーシックなヒューマノイドリグにモーションキャプチャ骨のモーションをベイク
    する機能を提供する簡易スクリプト。
    
    このスクリプトは仮スクリプトであり、将来的には各モジュールにベイクを行うよう
    な設計にすべき。
    
    Dates:
        date:2022/11/16 20:11 Eske Yoshinob[eske3g@gmail.com]
        update:2022/11/16 20:11 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2022 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import re
from maya import cmds, mel

from gris3 import node, func
from gris3.tools import jointEditor

# /////////////////////////////////////////////////////////////////////////////
# Expression template.                                                       //
# /////////////////////////////////////////////////////////////////////////////
Expression_template = '''
vector $start = <<%(start)s.tx, %(start)s.ty, %(start)s.tz>>;
vector $middle = <<%(middle)s.tx, %(middle)s.ty, %(middle)s.tz>>;
vector $end = <<%(end)s.tx, %(end)s.ty, %(end)s.tz>>;

vector $start_to_end = $end - $start;
vector $start_to_middle = $middle - $start;

float $length = mag($start_to_end);

float $h = dot($start_to_middle, $start_to_end) / $length;
vector $target_aim = $start_to_middle - (unit($start_to_end) * $h);
$target_aim = unit($target_aim) * $length;
vector $target_pos = $middle + $target_aim;

%(target)s.tx = $target_pos.x;
%(target)s.ty = $target_pos.y;
%(target)s.tz = $target_pos.z;
'''
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////

FingerPositions = ['Root', 'Base', 'Middle', 'Distal', 'End']

class Namespace(object):
    r"""
        設定したネームスペースを任意の文字列に付加する機能を提供するクラス
    """
    def __init__(self, namespace):
        r"""
            Args:
                namespace (str):
        """
        self.__namespace = namespace
    def __call__(self, name):
        r"""
            Args:
                name (str):
        """
        return self.__namespace + ':' + name


class JointName(object):
    def __init__(self):
        self.position = ''
        self.__namespace = ''

    def setNamespace(self, namespace):
        r"""
            Args:
                namespace (str):
        """
        self.__namespace = namespace

    def namespace(self):
        return self.__namespace

    def name(self, basename):
        r"""
            Args:
                basename (str):
        """
        namelist = [basename, 'jnt']
        if self.position:
            namelist.append(self.position)
        if self.namespace():
            namelist[0] = self.namespace() + ':' + namelist[0]
        return '_'.join(namelist)

    def __call__(self, basename):
        r"""
            Args:
                basename (str):
        """
        return self.name(basename)


class HumanIkName(object):
    r"""
        任意の位置名とベースの名前からhumanIK用の名前を生成して返すクラス。
    """
    def __init__(self):
        self.position = ''

    def __call__(self, basename):
        r"""
            Args:
                basename (str):
        """
        return '%s%s' % (self.position, basename)


class TemporaryTransform(object):
    def __init__(self, nodelist, namespace):
        r"""
            Args:
                nodelist (list):
                namespace (str):
        """
        ns = Namespace(namespace)
        self.__node = cmds.createNode('addDoubleLinear')
        for node in nodelist:
            for attr, dv in zip(['t' ,'r', 's'], [0, 0, 1]):
                for axis in ['x', 'y', 'z']:
                    trsattr = '%s.%s%s' % (ns(node), attr, axis)
                    mattr = '%s.%s__%s%s' % (self.__node, node, attr, axis)
                    cmds.addAttr(
                        self.__node, ln='%s__%s%s' % (node, attr, axis),
                        at='double'
                    )

                    con = cmds.listConnections(trsattr, p=True)
                    if not con:
                        value = cmds.getAttr(trsattr)
                        cmds.setAttr(mattr, value)
                        cmds.setAttr(trsattr, dv)
                        continue

                    cmds.connectAttr(con[0], mattr)
                    cmds.disconnectAttr(con[0], trsattr)
                    cmds.setAttr(trsattr, dv)

        self.__nodelist = nodelist
        self.__ns = ns

    def restore(self):
        attrs = cmds.listAttr(self.__node, ud=True)
        for attr in attrs:
            node, at = attr.split('__')
            node = self.__ns(node)

            conn = cmds.listConnections(
                '%s.%s' % (self.__node, attr),
                s=True, d=False, p=True, scn=True
            )
            if not conn:
                value = cmds.getAttr('%s.%s' % (self.__node, attr))
                cmds.setAttr('%s.%s' % (node, at), value)
                continue

            cmds.connectAttr(conn[0], '%s.%s' % (node, at))
        cmds.delete(self.__node)


# File name table.=============================================================
name = JointName()
hikname = HumanIkName()
MCPJointTable = {
    'hip_jnt_C' : 'Spine',
    'spineA_jnt_C' : 'Spine1',
    'spineB_jnt_C' : 'Spine2',
    'spineC_jnt_C' : 'Spine3',

    'neck_jnt_C' : 'Neck',
    'neckTwsta_jnt_C' : 'Neck',
    'neckTwstb_jnt_C' : 'Neck',
    'neckTwstc_jnt_C' : 'Neck',
    
    'head_jnt_C': 'Head',
    'eye_jnt_L' : 'Head',
    'eye_jnt_R' : 'Head',
    'headEnd_jnt_C': 'Head_End',
}
for src_side, dst_side in zip(['L', 'R'], ['Left', 'Right']):
    name.position = src_side
    hikname.position = dst_side

    matching_list = {
        
        'Shoulder' : ['clavicle'],
        'Arm': ['uparm', 'uparmTwista', 'uparmTwistb', 'uparmTwistc'],
        'ForeArm' : ['lowarm', 'lowarmTwista', 'lowarmTwistb', 'lowarmTwistc'],
        'Hand' : ['hand'],

        'UpLeg' : ['thigh', 'thighTwista', 'thighTwistb', 'thighTwistc'],
        'Leg' : ['lowleg', 'lowlegTwista', 'lowlegTwistb', 'lowlegTwistc'],
        'Foot' : ['foot'],
        'ToeBase': ['toe'],
    }
    for key in matching_list:
        for part in matching_list[key]:
            MCPJointTable[name(part)] = hikname(key)

    indexes = [None, 1, 2, 3, 4]
    # make a thumb matching list in the list.
    for pos, index in zip(FingerPositions[1:], indexes[1:]):
        MCPJointTable[name('thumb%s' % pos)] = hikname('HandThumb%s' % index)

    # Copy other fingers.
    for block in ('index', 'middle', 'ring', 'pinky'):
        for pos, index in zip(FingerPositions, indexes):
            if not index:
                format = 'InHand%s'
            else:
                format = 'Hand%%s%s' % index

            MCPJointTable[name('%s%s' % (block, pos))] = hikname(
                format % block.capitalize()
            )
# =============================================================================


class HumanIK(object):
    r"""
        このクラスはhumanリグからHIK用の骨を生成する機能を提供するクラス。
        humanリグはbasicHumanプリセットで作成される必要があります。
    """
    Root = 'root'
    Top_node = 'reference'
    WorldControllers = [
        'layout_ctrl',
        'world_ctrl', 'worldOffset_ctrl',
        'local_ctrl', 'localOffset_ctrl'
    ]
    CharacterizeationList = {
        'Head' : 15,
        'Hips' : 1,
        'HipsTranslation' : 49,
        'LeftArm' : 9,
        'LeftArmRoll' : 45,
        'LeftFoot' : 4,
        'LeftForeArm' : 10,
        'LeftForeArmRoll' : 46,
        'LeftHand' : 11,
        'LeftHandIndex1' : 54,
        'LeftHandIndex2' : 55,
        'LeftHandIndex3' : 56,
        'LeftHandMiddle1' : 58,
        'LeftHandMiddle2' : 59,
        'LeftHandMiddle3' : 60,
        'LeftHandPinky1' : 66,
        'LeftHandPinky2' : 67,
        'LeftHandPinky3' : 68,
        'LeftHandRing1' : 62,
        'LeftHandRing2' : 63,
        'LeftHandRing3' : 64,
        'LeftHandThumb1' : 50,
        'LeftHandThumb2' : 51,
        'LeftHandThumb3' : 52,
        'LeftInHandIndex' : 147,
        'LeftInHandMiddle' : 148,
        'LeftInHandPinky' : 150,
        'LeftInHandRing' : 149,
        'LeftLeg' : 3,
        'LeftLegRoll' : 42,
        'LeftShoulder' : 18,
        'LeftToeBase' : 16,
        'LeftUpLeg' : 2,
        'LeftUpLegRoll' : 41,
        'Neck' : 20,
        'Reference' : 0,
        'RightArm' : 12,
        'RightArmRoll' : 47,
        'RightFoot' : 7,
        'RightForeArm' : 13,
        'RightForeArmRoll' : 48,
        'RightHand' : 14,
        'RightHandIndex1' : 78,
        'RightHandIndex2' : 79,
        'RightHandIndex3' : 80,
        'RightHandMiddle1' : 82,
        'RightHandMiddle2' : 83,
        'RightHandMiddle3' : 84,
        'RightHandPinky1' : 90,
        'RightHandPinky2' : 91,
        'RightHandPinky3' : 92,
        'RightHandRing1' : 86,
        'RightHandRing2' : 87,
        'RightHandRing3' : 88,
        'RightHandThumb1' : 74,
        'RightHandThumb2' : 75,
        'RightHandThumb3' : 76,
        'RightInHandIndex' : 153,
        'RightInHandMiddle' : 154,
        'RightInHandPinky' : 156,
        'RightInHandRing' : 155,
        'RightLeg' : 6,
        'RightLegRoll' : 44,
        'RightShoulder' : 19,
        'RightToeBase' : 17,
        'RightUpLeg' : 5,
        'RightUpLegRoll' : 43,
        'Spine' : 8,
        'Spine1' : 23,
        'Spine2' : 24,
        'Spine3' : 25,
    }

    BakeSet = {
        #'worldCtrl' : ['reference', 'world_ctrl'],
        
        'hip' : ['Spine', 'spineHip_ctrl_C'],
        'spineA' : ['Spine1', 'spineA_ctrl_C'],
        'spineB' : ['Spine2', 'spineB_ctrl_C'],
        'spineC' : ['Spine3', 'spineC_ctrl_C'],
        
        'neck' : ['Neck', 'headNeck_ctrl_C'],
        'head' : ['Head', 'head_ctrl_C'],

        # For the ik arms.
        'leftShoulder' : ['LeftShoulder', 'clavicle_ctrl_L'],
        'rightShoulder' : ['RightShoulder', 'clavicle_ctrl_R'],
        'leftArm' : ['LeftHand', 'armIk_ctrl_L'],
        'rightArm' : ['RightHand', 'armIk_ctrl_R'],
        'leftElbow' : ['LeftForeArm', 'armMidlimbsBendCtrl_ctrl_L'],
        'rightElbow' : ['RightForeArm', 'armMidlimbsBendCtrl_ctrl_R'],

        # For the fk arms.
        'leftFkArm':['LeftArm', 'armUparmFK_ctrl_L'],
        'rightFkArm':['RightArm', 'armUparmFK_ctrl_R'],
        'leftFkForearm':['LeftForeArm', 'armLowarmFk_ctrl_L'],
        'rightFkForearm':['RightForeArm', 'armLowarmFk_ctrl_R'],
        'leftFkHand':['LeftHand', 'armHandFk_ctrl_L'],
        'rightFkHand':['RightHand', 'armHandFk_ctrl_R'],

        # For the ik legs.
        'leftFoot' : ['LeftFoot', 'legIk_ctrl_L'],
        'rightFoot' : ['RightFoot', 'legIk_ctrl_R'],
        'leftKnee' : ['LeftLeg', 'legMidlimbsBendCtrl_ctrl_L'],
        'rightKnee' : ['RightLeg', 'legMidlimbsBendCtrl_ctrl_R'],
        
        'leftToe' : ['LeftToeBase', 'legToe_ctrl_L'],
        'rightToe' : ['RightToeBase', 'legToe_ctrl_R'],

        # For the fk legs.
        'leftFkThigh' : ['LeftUpLeg', 'legThighFK_ctrl_L'],
        'rightFkThigh' : ['RightUpLeg', 'legThighFK_ctrl_R'],
        'leftFkLowleg' : ['LeftLeg', 'legLowlegFk_ctrl_L'],
        'rightFkLowleg' : ['RightLeg', 'legLowlegFk_ctrl_R'],
        'leftFkFoot' : ['LeftFoot', 'legFootFk_ctrl_L'],
        'rightFkFoot' : ['RightFoot', 'legFootFk_ctrl_R'], 
        'leftFkToe' : ['LeftToeBase', 'legToeFk_ctrl_L'],
        'rightFkToe' : ['RightToeBase', 'legToeFk_ctrl_R'],
        
    }
    def __init__(self, namespace='', rootJoint='hip_jnt_C'):
        r"""
            Args:
                namespace (str):
                rootJoint (str):
        """
        self.__namespace = namespace
        self.__root_joint = rootJoint
        self.__tmptrs = None
        self.__extranodes = []
        self.__attach_elbow = True
        self.__attach_knee = True

    def targetNamespace(self):
        return self.__namespace

    def setIsAttaching(self, elbow, knee):
        r"""
            Args:
                elbow (bool):
                knee (bool):
        """
        self.__attach_elbow = bool(elbow)
        self.__attach_knee = bool(knee)

    def copyJoint(self, source, name, parent=None):
        r"""
            Args:
                source (str):
                name (str):
                parent (str):
        """
        copied = func.copyNode(source, parent=parent)
        copied = cmds.rename(copied, name)
        return node.asObject(copied)

    def convert(self):
        target_ns = self.targetNamespace()
        ns = Namespace(target_ns)
        # Set world_trs to the initialized position.
        if target_ns:
            self.__tmptrs = TemporaryTransform(self.WorldControllers, target_ns)
            cmds.select(ns('all_anmSet'), r=True)
            all_ctrls = cmds.ls(sl=True)
            # Remove a keyframe for the all controllers.
            cmds.cutKey(clear=True)

            # Reset transform attributes.--------------------------------------
            for ctrl in all_ctrls:
                for attr,  value in zip(['t', 'r', 's'], [0, 0, 1]):
                    if not cmds.attributeQuery(attr, ex=True, n=ctrl):
                        continue
                    attrs = cmds.listAttr('%s.%s' % (ctrl, attr), k=True)
                    if not attrs:
                        continue
                    for at in attrs:
                        try:
                            cmds.setAttr('%s.%s' % (ctrl, at), value)
                        except:
                            pass
            # -----------------------------------------------------------------

        fbx_sidelabel = {'L':'Left', 'R':'Right'}
        def convertExtraJoints(jointName, parent):
            r"""
                Args:
                    jointName (str):
                    parent (str):
            """
            name = func.Name(jointName)
            if name.position() in fbx_sidelabel:
                side_label = fbx_sidelabel[name.position()]
            else:
                side_label = ''

            basename = name.name()
            if basename.find(':') > -1:
                basename = basename.split(':')[-1]
            capitalized_name = basename[0].upper() + basename[1:]

            fbx_name = side_label + capitalized_name
            copied = self.copyJoint(
                jointName, fbx_name, parent
            )
            self.__extranodes.append([jointName, copied])
            
            children = cmds.listRelatives(jointName, c=True, type='joint')
            if not children:
                return
            for child in children:
                convertExtraJoints(child, copied)

        name = JointName()
        name.setNamespace(target_ns)
        name.position = 'C'
        hikname = HumanIkName()

        # Create root node.
        root = func.createLocator(n=self.Top_node)

        # Hip translation and 2 hips for upper body and lower body.============
        hip_pos = cmds.xform(name('hip'), q=True, ws=True, rp=True)
        hip_trs = node.createNode('joint', n='HipsTranslation', p=root)
        hip_trs.setPosition(hip_pos)
        hip_trs.setRadius(1.2)

        hip = node.createNode('joint', n='Hips', p=hip_trs)
        hip.setRadius(3)
        # =====================================================================

        # Copy spine joints.===================================================
        spine = self.copyJoint(name('hip'), 'Spine', parent=hip_trs)
        tmp = cmds.duplicate(spine, po=True)[0]
        cst = cmds.orientConstraint(tmp, spine)
        cmds.setAttr('%s.jo' % spine, 0, 0, 0)
        cmds.delete(cst, tmp)

        spine1 = self.copyJoint(name('spineA'), 'Spine1', parent=spine)
        spine2 = self.copyJoint(name('spineB'), 'Spine2', parent=spine1)
        spine3 = self.copyJoint(name('spineC'), 'Spine3', parent=spine2)
        # =====================================================================
        
        # Copy head joints.====================================================
        neck = self.copyJoint(name('neck'), 'Neck', parent=spine3)
        head = self.copyJoint(name('head'), 'Head', parent=neck)
        head_end = self.copyJoint(name('headEnd'), 'Head_End', parent=head)
        # =====================================================================

        clavicle, uparm, lowarm, hand = {}, {}, {}, {}
        thigh, lowleg, foot, toe, toeend = {}, {}, {}, {}, {}
        uparmTwst, lowarmTwst, thighTwst, lowlegTwst = {}, {}, {}, {}
        for src_side, dst_side in zip(['L', 'R'], ['Left', 'Right']):
            name.position = src_side
            hikname.position = dst_side

            # Copy arm joints.=================================================
            clavicle[src_side] = self.copyJoint(
                name('clavicle'), hikname('Shoulder'), spine3
            )
            uparm[src_side] = self.copyJoint(
                name('uparm'), hikname('Arm'), clavicle[src_side]
            )
            lowarm[src_side] = self.copyJoint(
                name('lowarm'), hikname('ForeArm'), uparm[src_side]
            )
            hand[src_side] = self.copyJoint(
                name('hand'), hikname('Hand'), lowarm[src_side]
            )
            # =================================================================
            
            # Copy leg joints.=================================================
            thigh[src_side] = self.copyJoint(
                name('thigh'), hikname('UpLeg'), hip
            )
            lowleg[src_side] = self.copyJoint(
                name('lowleg'), hikname('Leg'), thigh[src_side]
            )
            foot[src_side] = self.copyJoint(
                name('foot'), hikname('Foot'), lowleg[src_side]
            )
            toe[src_side] = self.copyJoint(
                name('toe'), hikname('ToeBase'), foot[src_side]
            )
            
            locator = func.createLocator(n=hikname('Toe_End'))
            func.fitTransform(name('toeEnd'), locator, rotate=False)
            toeend[src_side] = cmds.parent(locator, toe[src_side])[0]
            # =================================================================

            # Splits both uparm, lowarm, thigh and lowleg.=====================
            joint = jointEditor.splitJoint(joints=lowarm[src_side])[0][0]
            uparmTwst[src_side] = cmds.rename(joint, hikname('ArmRoll'))
            
            joint = jointEditor.splitJoint(joints=hand[src_side])[0][0]
            lowarmTwst[src_side] = cmds.rename(joint, hikname('ForeArmRoll'))

            joint = jointEditor.splitJoint(joints=lowleg[src_side])[0][0]
            thighTwst[src_side] = cmds.rename(joint, hikname('UpLegRoll'))

            joint = jointEditor.splitJoint(joints=foot[src_side])[0][0]
            lowlegTwst[src_side] = cmds.rename(joint, hikname('LegRoll'))
            # =================================================================

            # Copy fingers.====================================================
            indexes = [None, 1, 2, 3, 4]
            parent = hand[src_side]
            # Copy thumb.
            for pos, index in zip(FingerPositions[1:], indexes[1:]):
                new_joint = self.copyJoint(
                    name('thumb%s' % pos),
                    hikname('HandThumb%s' % index),
                    parent
                )
                parent = new_joint

            # Copy other fingers.
            for block in ('index', 'middle', 'ring', 'pinky'):
                parent = hand[src_side]
                for pos, index in zip(FingerPositions, indexes):
                    if not index:
                        format = 'InHand%s'
                    else:
                        format = 'Hand%%s%s' % index

                    new_joint = self.copyJoint(
                        name('%s%s' % (block, pos)),
                        hikname(format % block.capitalize()),
                        parent
                    )
                    parent = new_joint
            # =================================================================

        # Convert an extra joints.=============================================
        world_trs = ns('world_trs')
        children = cmds.listRelatives(
            world_trs, c=True, type='joint'
        )
        name.position = 'C'
        for child in children:
            if child == name('hip'):
                continue
            convertExtraJoints(child, self.Top_node)
        # =====================================================================

        all_joints = cmds.listRelatives(root, ad=True, pa=True, type='joint')
        for joint in all_joints:
            cmds.setAttr('%s.segmentScaleCompensate' % joint, 0)

        return root

    def upArmToHorizontal(self):
        hikname = HumanIkName()
        for side, x_factor in zip(['Left', 'Right'], [1, -1]):
            hikname.position = side
            uparm_vector = func.Vector(
                cmds.xform(hikname('Arm'), q=True, ws=True, rp=True)
            )
            hand_vector = func.Vector(
                cmds.xform(hikname('Hand'), q=True, ws=True, rp=True)
            )
            arm_vector = hand_vector - uparm_vector
            arm_vector.z = 0

            angle = (arm_vector ^ func.Vector([x_factor * 1, 0, 0])) * x_factor
            cmds.rotate(0, 0, angle, hikname('Arm'), r=True, ws=True)

    def addNamespace(self):
        assetName = cmds.getAttr('%s.assetName' % self.Root)
        namespace = cmds.namespace(add=(assetName + 'MCP'))

        all_members = cmds.listRelatives(
            self.Top_node, ad=True, type='transform'
        )
        all_members.append(self.Top_node)
        for m in all_members:
            org_name = m.split(':')[-1]
            cmds.rename(m, '%s:%s' % (namespace, org_name))

    def deleteAllLayer(self):
        all_layer = [
            x for x in cmds.ls(type='displayLayer') if x != 'defaultLayer'
        ]
        if all_layer:
            cmds.delete(all_layer)

    def finalize(self):
        self.upArmToHorizontal()
        self.addNamespace()
        self.deleteAllLayer()


    def createCharacter(self):
        # Create character node.
        char = mel.eval('CreateHIKCharacterWithName("Character1")')
        
        # Map all joints to character.
        for key in self.CharacterizeationList:
            command = (
                'setCharacterObject('
                '"%(name)s","%(char)s",%(index)s,0);'
            ) % {
                'name':key, 'char':char,
                'index':self.CharacterizeationList[key],
            }
            mel.eval(command)

        # Connect character to reference node.
        cmds.addAttr('reference', ln='character', at='message')
        cmds.connectAttr('%s.message' % char, 'reference.character')


    def setupMCPBakingSystem(self):
        cst_grp = cmds.createNode('transform', p='reference', n='cst_grp')
        ns = Namespace(self.targetNamespace())
        gl_bake_set = {x:y for x, y in self.BakeSet.items()}
        for s in ['left', 'right']:
            if not self.__attach_elbow:
                del gl_bake_set[s+'Elbow']
            if not self.__attach_knee:
                del gl_bake_set[s+'Knee']
            
        # Local functions.+++++++++++++++++++++++++++++++++++++++++++++++++++++
        def const(key, cst=cmds.parentConstraint, **keywords):
            r"""
                Args:
                    key (str):
                    cst (func):
                    **keywords (dict):
            """
            if key not in gl_bake_set:
                return
            constraint = cst(
                gl_bake_set[key][0], ns(gl_bake_set[key][1]), **keywords
            )
            cmds.parent(constraint, cst_grp)

        def createAimDetactionSystem(start, middle, end, ctrl, xFactor):
            r"""
                Args:
                    start (str):
                    middle (str):
                    end (str):
                    ctrl (str):
                    xFactor (float):
            """
            vector_nodes = []
            for p in [start, middle, end]:
                trs = cmds.createNode('transform', n='pos#')
                cmds.pointConstraint(p, trs)
                vector_nodes.append(trs)

            aim_target = cmds.createNode('transform', n='tgt#')

            expression_str = Expression_template % {
                'start':vector_nodes[0],
                'middle':vector_nodes[1],
                'end':vector_nodes[2],
                'target':aim_target,
            }
            cmds.expression(s=expression_str, o='', ae=1, uc='all')

            vector_nodes.append(aim_target)

            return vector_nodes
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        sides = list(zip(['left', 'right'], ['L', 'R']))

        baked_set = [x[1] for x in gl_bake_set.values()]

        # Add target to detect direction of the roll controller ---------------
        # for the arms and the legs.
        roll_detect_nodes = []
        for side, s in sides:
            if s == 'L':
                x_factor = 1
            else:
                x_factor = -1

            c_side = side.capitalize()

            for tgt_part, aim_tgtname, part in zip(
                    ['Arm', 'UpLeg'], ['Hand', 'Foot'], ['arm', 'leg'],
                ):
                pv_target = '%sIkPv_trs_%s' % (part, s)
                parent = '%s%s' % (c_side, tgt_part)

                trs = cmds.createNode('transform', p=parent)
                func.fitTransform(ns(pv_target), trs)

                aim_tgt = '%s%s' % (c_side, aim_tgtname)
                ctrl = '%sIkRole_ctrl_%s' % (part, s)
                cst = cmds.aimConstraint(
                    aim_tgt, ns(ctrl),
                    aimVector=[1 * x_factor, 0, 0],
                    upVector=[0, 0, 1 * x_factor],
                    worldUpType='object', worldUpObject=trs, skip=['y', 'z']
                )
                cmds.parent(cst, cst_grp)
                
                baked_set.append(ctrl)

        if roll_detect_nodes:
            grp = cmds.createNode(
                'transform', n='rollAimingSystem_grp', p='reference'
            )
            cmds.parent(roll_detect_nodes, grp)
        # ---------------------------------------------------------------------

        #const('worldCtrl')
        const('hip', mo=True)

        const('spineA', cmds.orientConstraint)
        const('spineB', cmds.orientConstraint)
        const('spineC', cmds.orientConstraint)

        const('neck', cmds.orientConstraint)
        const('head', cmds.orientConstraint)

        for side, s in sides:
            const('%sFoot' % side, mo=True)
            const('%sArm' % side, mo=True)
            const('%sShoulder' % side, cmds.orientConstraint)
            const('%sToe' % side, cmds.orientConstraint)

            const('%sElbow' % side, cmds.pointConstraint, mo=True)
            const('%sKnee' % side, cmds.pointConstraint, mo=True)

            # Connects fk controllers.-----------------------------------------
            for part in [
                    'Arm', 'Forearm', 'Hand', 'Thigh', 'Lowleg', 'Foot', 'Toe'
                ]:
                const('%sFk%s' % (side, part), cmds.orientConstraint)
            # -----------------------------------------------------------------

            # Connects all fingers.--------------------------------------------
            for category in ['thumb', 'index', 'middle', 'ring', 'pinky']:
                source = '%sInHand%s' % (side.capitalize(), category.capitalize())
                target = '%sRoot_ctrl_%s' % (category, s)
                if cmds.objExists(source) and target:
                    cst = cmds.orientConstraint(source, ns(target))
                    cmds.parent(cst, cst_grp)

                    baked_set.append(target)
                
                for part, part_index in zip(
                        FingerPositions[1:4], range(1, 4)
                    ):
                    source = '%sHand%s%s' % (
                        side.capitalize(), category.capitalize(), part_index
                    )
                    target = '%s%s_ctrl_%s' % (category, part, s)
                    cst = cmds.orientConstraint(source, ns(target))
                    cmds.parent(cst, cst_grp)
                    
                    baked_set.append(target)
            # -----------------------------------------------------------------

        # ---------------------------------------------------------------------
        extra_bakeset = []
        for node in self.__extranodes:
            conn = cmds.listConnections(
                '%s.message' % node[0], s=False, d=True, p=True
            )
            if not conn:
                continue
            for c in conn:
                if not c.endswith('mcpBakeSourceNode'):
                    continue
                target = c.split('.')[0]
                cmds.parentConstraint(node[1], target)
                extra_bakeset.append(target)
        # ---------------------------------------------------------------------

        # Connects from mcp joint.
        all_nodes = cmds.listRelatives('reference', ad=True, type='transform')
        target_namespace = cmds.getAttr( '%s.assetName' % ns('root')) + 'MCP'
        mcp_ns = Namespace(target_namespace)
        for node in all_nodes:
            if not cmds.objExists(mcp_ns(node)):
                continue
            cmds.parentConstraint(mcp_ns(node), node)

        # Bake animations.=====================================================
        # Create bake set.
        bkset = cmds.sets(
            [ns(x) for x in baked_set], n='bakeSet', text='forBake'
        )
        if extra_bakeset:
            cmds.sets(extra_bakeset, e=True, add=bkset)

        modelpanels = [
            x for x in cmds.lsUI(p=True) if cmds.modelPanel(x, ex=True)
        ]
        for panel in modelpanels:
            cmds.isolateSelect(panel, state=1)
        start_frame = int(
            cmds.findKeyframe(mcp_ns('HipsTranslation'), w='first')
        )
        end_frame = int(
            cmds.findKeyframe(mcp_ns('HipsTranslation'), w='last')
        )
        print('Framerange : {} - {}'.format(start_frame, end_frame))

        baked_nodes = cmds.sets(bkset, q=True)
        cmds.bakeResults(
            baked_nodes,
            simulation=True, t=(start_frame, end_frame), sampleBy=1,
            disableImplicitControl=False, preserveOutsideKeys=False,
            sparseAnimCurveBake=False,
            removeBakedAttributeFromLayer=True, bakeOnOverrideLayer=False,
            controlPoints=False, shape=False
        )

        cmds.delete(self.Top_node, bkset)
        for panel in modelpanels:
            cmds.isolateSelect(panel, state=0)
        # =====================================================================

        time_offset = -start_frame + 101
        cmds.playbackOptions(min=101, max=end_frame + time_offset)

        referenced_all = cmds.listRelatives(mcp_ns(self.Top_node), ad=True)
        for nodes in (baked_nodes, referenced_all):
            cmds.keyframe(
                nodes, e=True, iub=True, o='over', r=True, tc=time_offset
            )

        if self.__tmptrs:
            self.__tmptrs.restore()


def parentMCPGeometry(topNode='render_grp'):
    r"""
        Args:
            topNode (str):
    """
    mobj = re.compile('_geo\d*')
    for node in cmds.listRelatives(topNode, c=True, type='transform'):
        targetJoint = mobj.sub('', node)
        simple_name = targetJoint.split('_jnt')[0]
        simple_name = simple_name[0].upper() + simple_name[1:]
        targetJoint = MCPJointTable.get(targetJoint, simple_name)
        if not cmds.objExists(targetJoint):
            continue
        node = cmds.parent(node, targetJoint)


def startToBake(namespace=None, attachElbow=True, attachKnee=True):
    r"""
        Args:
            namespace (str):
            attachElbow (bool):
            attachKnee (bool):
    """
    if  not namespace:
        nslist = [
            x.split(':', 1)[0] for x in cmds.ls(sl=True) if ':' in x
        ]
        if not nslist:
            return False
        namespace = nslist[0]
    hik = HumanIK(namespace)
    hik.convert()
    hik.setIsAttaching(attachElbow, attachKnee)
    hik.setupMCPBakingSystem()

