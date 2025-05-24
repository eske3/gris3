#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ジョイントの作成や編集を行う便利機能を提供するモジュール。
    
    Dates:
        date:2017/01/22 0:00[Eske](eske3g@gmail.com)
        update:2020/12/23 10:45 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import node, mathlib, verutil
from ..tools import util
cmds = node.cmds

Axislist = [
    '+X', '+Y', '+Z', '-X', '-Y', '-Z'
]
VectorList = {
    '+X':[1, 0, 0],
    '+Y':[0, 1, 0],
    '+Z':[0, 0, 1],
    '-X':[-1, 0, 0],
    '-Y':[0, -1, 0],
    '-Z':[0, 0, -1],
}

def axisToVector(axis):
    r"""
        文字列(+-XYZ)をリストのベクトルに変換する。
        
        Args:
            axis (str):
            
        Returns:
            list:
    """
    return VectorList.get(axis, [1, 0, 0])

def reconnectInverseScale(selected=None, connectToTransform=False):
    r"""
        与えられたジョイントのリストに対し、ジョイントの直上の親の
        scaleを自身のinverseScaleに接続しなおす。
        
        Args:
            selected (list):ジョイントのリスト
            connectToTransform (bool):
    """
    if not selected:
        selected = node.selected(selected, type='joint')

    node_type = 'transform' if connectToTransform else 'joint'
    for joint in selected:
        parent = joint.parent(type=node_type)
        if not parent:
            continue

        parent_attr = parent.attr('scale')
        inv_scle_attr = joint.attr('inverseScale')
        if cmds.isConnected(parent_attr, inv_scle_attr):
            continue
        try:
            parent_attr >> inv_scle_attr
        except Exception as e:
            pass

def createJoint(selected=None, perObjects=True):
    r"""
        ジョイントを作成する関数。
        selectedに指定したノードの階層化に作成する。指定がない場合は選択
        ノード下に作成する。
        選択もない場合はワールド下に作成する。
        
        Args:
            selected (list):選択オブジェクトのリスト
            perObjects (bool):選択オブジェクト毎にジョイントを作成するか
            
        Returns:
            list:
    """
    selected = node.selected(selected, type='transform')
    results  = []
    not_selected = False
    if not selected:
        selected = ['']
        not_selected = True

    if perObjects or not_selected:
        for sel in selected:
            creationFlags = {}
            if cmds.objExists(sel):
                creationFlags = {'parent' : sel}
            else:
                sel = None
            results.append(node.createNode('joint', **creationFlags))

            if not sel:
                continue
            if cmds.nodeType(sel) == 'joint':
                results[-1]('radius', cmds.getAttr(sel + '.radius'))
    else:
        pos, size = util.positionCenter([x.rotatePivot() for x in selected])
        jnt = node.createNode('joint')
        jnt.setPosition(pos)
        size = max(size)
        jnt.setRadius(size*0.1)

    if results:
        cmds.select(results)
    return results

def createJointOnCenter(components=None):
    r"""
        コンポーネントの中心にジョイントを作成する。
        
        Args:
            components (list):コンポーネントのリスト
            
        Returns:
            node.Joint:
    """
    if not components:
        components = cmds.filterExpand(sm=util.ComponentMask)
    center, size = util.getComponentCenter(components)
    joint = node.createNode('joint')
    size = max(size)
    if size <= 0:
        verts = cmds.filterExpand(components, sm=31)
        if len(verts) > 0:
            new_center, size = util.getComponentCenter(
                cmds.polyListComponentConversion(verts[0], tf=True)
            )
            size = max(size)
        else:
            size = 1.0
    joint.setRadius(size*0.1)
    joint.setPosition(center)
    return joint

def createJointFromSelected(perComponents=True):
    r"""
        ノードかコンポーネントの選択状況に応じて適切な位置にジョイントを作成する
        
        Args:
            perComponents (bool):
            
        Returns:
            list:
    """
    components = cmds.filterExpand(sm=util.ComponentMask)
    if components:
        if not perComponents:
            result = [createJointOnCenter(components)]
            if result:
                cmds.select(result, r=True)
            return result
        result = []
        for comp in components:
            result.append(createJointOnCenter(comp))
        if result:
            cmds.select(result, r=True)
        return result
    else:
        return createJoint(perObjects=perComponents)

def arrangeJointRadius(startJoint=None, endJoint=None):
    r"""
        開始ジョイントから終了ジョイントまでのradiusを整列する。
        終了ジョイントは開始ジョイントの下階層である必要がある。
        
        Args:
            startJoint (str):開始ジョイント
            endJoint (str):終了ジョイント
    """
    joints = node.selected(type='joint')
    if not startJoint:
        startJoint = joints[0]
        if not endJoint:
            endJoint = joints[1]
    else:
        if not endJoint:
            endJoint = joints[0]
    jointlist = [endJoint]
    while(True):
        jointlist.append(jointlist[-1].parent(type='joint'))
        if not jointlist[-1]:
            # 一番上階層まで到達した場合はエラー
            raise ValueError(
                'The end joint "%s" is not "%s"s child.' % (
                    endJoint, startJoint
                )
            )
        if jointlist[-1] == startJoint:
            break
    jointlist.reverse()
    lengthlist = [node.MVector(x.position()) for x in jointlist]
    lengthlist = [
        (lengthlist[i]-lengthlist[i+1]).length()
        for i in range(0, len(lengthlist)-1)
    ]
    total_length = float(sum(lengthlist))
    start_radius = startJoint('radius')
    end_radius = endJoint('radius')
    sub_radius = start_radius - end_radius
    ratio = 0.0
    for j, l in zip(jointlist[1:-1], lengthlist):
        ratio += l/total_length
        j('radius', start_radius-(sub_radius*ratio))

def arrangeJointRadiusChain(jointList=None):
    r"""
        開始ジョイントから終了ジョイントまでのradiusを整列する。
        この関数では各ジョイントのリストを渡すとジョイントの末端を
        検知して自動でその末端までに整列処理を行う。
        
        Args:
            jointList (list):操作を行うジョイントのリスト
    """
    from gris3.tools import util
    jointList = node.selected(type='joint')
    for joint in jointList:
        chain = util.listSingleChain(joint)
        arrangeJointRadius(chain[0], chain[-1])

def splitJoint(numberOfJoints=1, joints=None):
    r"""
        ジョイントを任意の数のジョイントで分割する。
        
        Args:
            numberOfJoints (int):分割するジョイント数
            joints (list):分割されるジョイントノードのリスト
            
        Returns:
            list:
    """
    joints = node.selected(joints, type='transform')
    result = []

    for joint in joints:
        newjoints = []
        parent = joint.parent()
        if not parent:
            continue

        # 親から子へのジョイントの大きさを検出する。===========================
        if parent.hasAttr('radius'):
            parent_radius = parent('radius')
        else:
            parent_radius = 1.0

        if joint.hasAttr('radius'):
            radius = joint('radius')
        else:
            radius = 1.0

        sub_radius = (radius - parent_radius) / numberOfJoints
        # =====================================================================

        baseVector = mathlib.Vector(parent.rotatePivot())
        jVector    = mathlib.Vector(joint.rotatePivot())
        pjVector   = (jVector - baseVector) / (numberOfJoints + 1)

        for i in range(numberOfJoints):
            baseVector += pjVector
            newJoint = node.createNode('joint', p=parent())
            newJoint.setPosition((baseVector.x, baseVector.y, baseVector.z))
            newJoint('radius', parent_radius + (sub_radius * i))
            newJoint.setInverseScale()
            parent = newJoint
            newjoints.append(newJoint)

        parent.addChild(joint)
        result.append(newjoints)

    return result

class OrientationModifier(object):
    r"""
        ジョイントの軸を制御するための機能を提供するクラス。
    """
    PrimaryMode   = [
        'firstChild', 'origin', 'vector', 'node'
   ]
    SecondaryMode = [
        'origin', 'vector', 'node', 'surface'
   ]
    def __init__(self):
        self.__apply_to_children = True
        self.__isFreeze        = False
        self.__freeze_only     = False

        self.__primaryAxis     = '+X'
        self.__primaryAimAxis  = '+Y'
        self.__primaryMode     = 'firstChild'
        self.__target          = ''

        self.__secondaryAxis   = '+Z'
        self.__secondaryMode   = 'origin'
        self.__upTarget        = []
        self.__targetUpAxis    = '+Z'

    def setApplyToChildren(self, state):
        r"""
            子供へも影響を与えるかどうかを指定する。
            
            Args:
                state (bool):
        """
        self.__apply_to_children = bool(state)

    def applyToChildren(self):
        r"""
            子供へも影響を与えるかどうかを返す。
            
            Returns:
                bool:
        """
        return self.__apply_to_children

    def setIsFreeze(self, state):
        r"""
            フリーズをかけるかどうかを指定する。
            
            Args:
                state (bool):
        """
        self.__isFreeze = bool(state)

    def isFreeze(self):
        r"""
            処理実行後、フリーズをかけるかどうか。
            
            Returns:
                bool:
        """
        return self.__isFreeze

    def setPrimaryAxis(self, axis):
        r"""
            プライマリ軸を指定する。
            
            Args:
                axis (str):AxisListにある６種の文字列のいずれか
        """
        if not axis in Axislist:
            raise ValueError(
                'The Axis must be in a following list : %s' % Axislist
         )
        self.__primaryAxis = axis

    def primaryAxis(self):
        r"""
            プライマリ軸がどの方向かを返す。
            
            Returns:
                str:AxisListにある６種の文字列のいずれか
        """
        return self.__primaryAxis

    def primaryVector(self):
        r"""
            プライマリ軸をベクトルで返す。
            
            Returns:
                list:
        """
        return axisToVector(self.primaryAxis())

    def setPrimaryAimAxis(self, axis):
        r"""
            プライマリ軸を向ける軸を指定する。
            
            Args:
                axis (str):AxisListにある６種の文字列のいずれか
        """
        if not axis in Axislist:
            raise ValueError(
                'The Axis must be in a following list : %s' % Axislist
         )
        self.__primaryAimAxis = axis

    def primaryAimAxis(self):
        r"""
            プライマリ軸を向ける軸を変えす。
            
            Returns:
                str:AxisListにある６種の文字列のいずれか
        """
        return self.__primaryAimAxis

    def primaryAimVector(self):
        r"""
            プライマリ軸を向ける軸をベクターで返す。
            
            Returns:
                list:
        """
        return axisToVector(self.primaryAimAxis())

    def setPrimaryMode(self, mode):
        r"""
            プライマリ軸を向ける方法を指定する。
            指定出来るものはこのクラスのPrimaryModeの値のいずれか。
            
            Args:
                mode (str):
        """
        if not mode in self.PrimaryMode:
            raise ValueError(
                'The secondary mode must be in a following list : %s' % \
                self.PrimaryMode
         )
        self.__primaryMode = mode

    def primaryMode(self):
        r"""
            プライマリ軸を向ける方法を返す。
            
            Returns:
                str:
        """
        return self.__primaryMode

    def setTarget(self, node=''):
        r"""
            プライマリ軸を向けるターゲットノードを指定する。
            
            Args:
                node (str):
        """
        self.__target = node

    def target(self):
        r"""
            プライマリ軸を向けるターゲットノードを返す。
            
            Returns:
                node.AbstractNode:
        """
        if isinstance(self.__target, (list, tuple)):
            return [x for x in node.toObjects(self.__target) if x]
        else:
            return node.asObject(self.__target)

    def setSecondaryAxis(self, axis):
        r"""
            セカンダリ軸を指定する。
            
            Args:
                axis (str):AxisListにある６種の文字列のいずれか
        """
        if not axis in Axislist:
            raise ValueError(
                'The Axis must be in a following list : %s' % Axislist
         )
        self.__secondaryAxis = axis

    def secondaryAxis(self):
        r"""
            セカンダリ軸がどの方向かを返す。
            
            Returns:
                str:AxisListにある６種の文字列のいずれか
        """
        return self.__secondaryAxis

    def secondaryVector(self):
        r"""
            セカンダリ軸をベクトルで返す。
            
            Returns:
                list:
        """
        return axisToVector(self.secondaryAxis())

    def setSecondaryMode(self, mode):
        r"""
            セカンダリ軸を向ける方法を指定する。
            指定出来るものはこのクラスのPSecondaryModeの値のいずれか。
            
            Args:
                mode (str):
        """
        if not mode in self.SecondaryMode:
            raise ValueError(
                'The secondary mode must be in a following list : %s. got %s' % (
                    self.SecondaryMode, mode
               )
         )
        self.__secondaryMode = mode

    def secondaryMode(self):
        r"""
            セカンダリ軸を向ける方法を返す。
            
            Returns:
                str:
        """
        return self.__secondaryMode

    def setUpTarget(self, node=''):
        r"""
            アップ軸を向けるターゲットノードを指定する。
            
            Args:
                node (str or list):
        """
        self.__upTarget = node

    def upTarget(self):
        r"""
            アップ軸を向けるターゲットノードを返す。
            
            Returns:
                node.Transform:
        """
        if isinstance(self.__upTarget, (list, tuple)):
            return [x for x in node.toObjects(self.__upTarget) if x]
        else:
            return node.asObject(self.__upTarget)

    @staticmethod
    def closestTarget(joint, upTargets):
        r"""
            jointに最も近いノードをupTargetsから探し出す。
            upTargetsがlistではない場合、または一つしかない場合は
            そのままの値を返す
            
            Args:
                joint (node.Transform):検査対象ノードオブジェクト
                upTargets (list): 検出対象となるノードのリスト
                
            Returns:
                node.Transform:
        """
        if not isinstance(upTargets, (list, tuple)):
            return upTargets
        if len(upTargets) == 1:
            return upTargets[0]

        pos = node.MVector(joint.position())
        lengthlist = {}
        for tgt in upTargets:
            t_pos = node.MVector(tgt.position())
            lengthlist.setdefault((t_pos-pos).length(), []).append(tgt)
        key = min(lengthlist.keys())
        return lengthlist[key][0]

    def setTargetUpAxis(self, axis):
        r"""
            ターゲットのup軸を設定する
            
            Args:
                axis (str):
        """
        self.__targetUpAxis = axis

    def targetUpAxis(self):
        r"""
            設定されたターゲットのup軸を返す
            
            Returns:
                str:
        """
        return self.__targetUpAxis

    def targetUpVector(self):
        r"""
            ターゲットのup軸のベクトルを返す
            
            Returns:
                list:
        """
        return axisToVector(self.targetUpAxis())
    # =========================================================================

    def setFreezeOnly(self, state):
        r"""
            処理をせずフリーズのみを行うかどうかを設定する。
            
            Args:
                state (bool):
        """
        self.__freeze_only = bool(state)

    def freezeOnly(self):
        r"""
            処理をせずフリーズのみかどうかを返す。
            
            Returns:
                bool:
        """
        return self.__freeze_only

    def _alignAxis(self, selected=None, surf=None):
        r"""
            実行メソッドの本体。
            execute内でセカンダリ合わせのモードがsurfになっているかどうかに
            よって挙動が変化するため一度executeを通している。
            
            Args:
                selected (list):操作対象ノードをリストで指定
                surf (node.AbstractEditableShape):方向合わせに使用するノード
        """
        class TransformNode(verutil.String):
            r"""
                初期位置保持機能を持つTransformノード向けのローカルクラス。
            """
            def __new__(cls, name, unLock=False):
                r"""
                    初期化メソッド。インスタンス作成時の位置情報を保持。
                    
                    Args:
                        name (str):ノード名
                        unLock (bool):
                        
                    Returns:
                        TransformNode:
                """
                object = super(TransformNode, cls).__new__(cls, name)
                object.initialMatrix = cmds.getAttr('%s.worldMatrix' % name)
                return object

            def restore(self):
                r"""
                    初期化時に保持していた状態へ復元するメソッド。
                """
                attr = ['t', 'r', 's']
                axis = ['x', 'y', 'z']
                lockedlist = []

                ssc = None
                if cmds.attributeQuery('ssc', ex=True, n=self):
                    ssc = cmds.getAttr(self + '.ssc')

                for at in attr:
                    for ax in axis:
                        nodeattr = '%s.%s%s' % (self, at, ax)
                        if not cmds.getAttr(nodeattr, l=True):
                            continue

                        lockedlist.append(nodeattr)
                        cmds.setAttr(nodeattr, l=False)
                cmds.xform(self, ws=True, m=self.initialMatrix)

                for attr in lockedlist:
                    cmds.setAttr(attr, l=True)
                if ssc is not None:
                    cmds.setAttr(self + '.ssc', ssc)

        def __freeze(selectedJoints):
            r"""
                指定ジョイント階層化すべてのの回転フリーズを行う。
                
                Args:
                    selectedJoints (list):
            """
            allTransform = cmds.listRelatives(
                selectedJoints, ad=True, type='transform'
            )
            if allTransform:
                allTransform.extend(selectedJoints)
                allTransform.reverse()
            else:
                allTransform = selectedJoints
            cmds.makeIdentity(selectedJoints, a=True, r=True)

        if self.applyToChildren():
            allChildren = cmds.listRelatives(
                selected, type='joint', ad=True, pa=True
         )
            if allChildren:
                allChildren.reverse()
                selected.extend(node.toObjects(allChildren))

        target = self.target()
        upTarget = self.upTarget()
        sec_mode = self.secondaryMode()

        if self.freezeOnly():
            # フリーズのみの場合はフリーズ処理だけ実行して終了。
            __freeze(selected)
            cmds.select(selected, r=True)
            return

        if not target and self.primaryMode() == 'node':
            raise RuntimeError('Aim target is not spcified.')
            return

        if not upTarget and sec_mode == 'node':
            raise RuntimeError('Up target is not spcified.')
            return

        for joint in selected:
            if not joint.hasAttr('ssc'):
                continue
            ssc = joint('ssc')

            children = joint.children(type='transform')
            if not children:
                if not joint.hasParent():
                    # 親も子もいない場合は何もしない。
                    continue
                # 子がいない場合はjoとrotateを０にして終了する。
                # cmds.makeIdentity(joint, a=True, r=True, jo=True)
                if not joint.isType('joint'):
                    continue
                joint('r', (0, 0, 0))
                joint('jo', (0, 0, 0))
                continue

            # ジョイントの親の代理ノードの作成と設定。=========================
            parent_proxy = node.createNode('transform')
            parent_proxy.setMatrix(joint('parentMatrix'))
            # =================================================================

            # ジョイントの代理ジョイントの作成と設定。=========================
            joint_proxy = node.createNode('joint', p=parent_proxy)
            matrix = joint.matrix()
            joint_proxy.setMatrix(matrix)
            # =================================================================

            # プライマリジョイントの設定。=====================================
            primaryVector = self.primaryVector()
            pri_mode = self.primaryMode()
            if pri_mode == 'firstChild':
                target = children[0]
            elif pri_mode in ('origin', 'vector'):
                tgtProxy = node.createNode('transform', p=parent_proxy)
                tgtProxy.setMatrix(matrix)
                target = node.createNode('transform', p=tgtProxy)

                vector = self.primaryAimVector()
                if pri_mode == 'origin':
                    target('t', vector)
                else:
                    vector_offset = matrix[:]
                    vector_offset[12] += vector[0]
                    vector_offset[13] += vector[1]
                    vector_offset[14] += vector[2]
                    target.setMatrix(vector_offset)
            else:
                target = self.closestTarget(joint_proxy, target)
            # =================================================================

            # セカンダリジョイントの設定。=====================================
            cstraintArgs = {
                'offset'     :[0, 0, 0],
                'weight'     :1,
                'aimVector'  :primaryVector,
                'upVector'   :self.secondaryVector(),
                'worldUpType':'none'
            }

            if sec_mode == 'origin':
                posProxy = node.createNode('transform', p=parent_proxy)
                posProxy.setMatrix(matrix)
                l_upTarget = node.createNode('transform', p=posProxy)
                l_upTarget('t', self.targetUpVector())
                cstraintArgs['worldUpType']   = 'object'
                cstraintArgs['worldUpObject'] = l_upTarget
            elif sec_mode == 'vector':
                cstraintArgs['worldUpType'] = 'vector'
                cstraintArgs['worldUpVector'] = self.targetUpVector()
            elif sec_mode == 'node':
                cstraintArgs['worldUpType']   = 'object'
                cstraintArgs['worldUpObject'] = self.closestTarget(
                    joint_proxy, upTarget
                )
            elif sec_mode == 'surface':
                cstraintArgs['worldUpType'] = 'vector'
                cstraintArgs['worldUpVector'] = surf.closestNormal(
                    joint_proxy.position()
                )
            # =================================================================

            cmds.delete(cmds.aimConstraint(target, joint_proxy, **cstraintArgs))
            cmds.makeIdentity(joint_proxy, a=True, r=True)

            # 子ノードのTransformアトリビュートをすべてアンロックする。========
            allChildren = (
                [TransformNode(x) for x in joint.children(type='transform')]
                if joint.hasChild() else []
            )
            # =================================================================

            # Set value is gotten from proxy to joint attributes.--------------
            for attr in ('r', 'jo', 'ra'):
                for ax in ('x', 'y', 'z'):
                    dstattr = joint.attr(attr + ax)
                    srcattr = joint_proxy.attr(attr + ax)
                    locked = dstattr.isLocked()
                    if locked:
                        dstattr.setLock(False)
                    dstattr.set(srcattr.get())
                    
                    if locked:
                        dstattr.setLock(True)
            # -----------------------------------------------------------------

            # Restore position of all children.
            for child in allChildren:
                child.restore()

            cmds.delete(parent_proxy)

            joint('ssc', ssc)

        if self.isFreeze():
            __freeze(selected)

    def execute(self, selected=None):
        r"""
            実行メソッド。
            
            Args:
                selected (list):操作対象ノードをリストで指定
        """
        pre_selections = cmds.ls(sl=True)
        selected = node.selected(selected, type='joint')
        if self.secondaryMode() != 'surface':
            self._alignAxis(selected)
        else:
            uptarget = self.upTarget()
            if not uptarget:
                raise RuntimeError('The up target is invalid.')
            uptarget = uptarget[0]
            with node.editFreezedShape(uptarget) as surf:
                self._alignAxis(selected, surf)
        if pre_selections:
            cmds.select(pre_selections, r=True, ne=True)

class JointMirror(object):
    r"""
        ジョイントのミラーを行うクラス。
    """
    MirrorFlags = {'X' : 'myz', 'Y' : 'mxz', 'Z' : 'mxy'}
    def __init__(self):
        self.__apply_to_children = True

        self.__mirror_behavior = True
        self.__mirror_axis = 'X'
        self.__search_str = '_L'
        self.__replaced_str= '_R'

        self.__is_replacing_parent = True
        self.__parent_searching_str = '_L'
        self.__parent_relaced_str = '_R'

    def setApplyToChildren(self, state):
        r"""
            子も含めて適応するかどうかを設定する。
            
            Args:
                state (bool):
        """
        self.__apply_to_children = bool(state)

    def applyToChildren(self):
        r"""
            子も含めて適応するかどうかを返す。
            
            Returns:
                bool:
        """
        return self.__apply_to_children

    def setMirrorBehavior(self, state):
        r"""
            behaviorでミラーリングするかどうかを設定する。
            
            Args:
                state (bool):
        """
        self.__mirror_behavior = bool(state)

    def mirrorBehavior(self):
        r"""
            behaviorでミラーリングするかどうかを返す。
            
            Returns:
                bool:
        """
        return self.__mirror_behavior

    def setMirrorAxis(self, axis):
        r"""
            ミラー軸を設定する。
            
            Args:
                axis (str):
        """
        if axis not in self.MirrorFlags:
            lib.error('The axis must be "X", "Y" or "Z".')
        self.__mirror_axis = axis

    def mirrorAxis(self):
        r"""
            セットされているミラー軸を返す。
            
            Returns:
                str:
        """
        return self.__mirror_axis

    def setSearchingString(self, searchingString):
        r"""
            ミラージョイントの名前の置換対象文字列をセットする。
            
            Args:
                searchingString (str):
        """
        self.__search_str = searchingString

    def searchingString(self):
        r"""
            ミラージョイントの名前の置換対象文字列を返す。
            
            Returns:
                str:
        """
        return self.__search_str

    def setReplacedString(self, replacedString):
        r"""
            ミラージョイントの名前の置換後の文字列をセットする。
            
            Args:
                replacedString (str):
        """
        self.__replaced_str = replacedString

    def replacedString(self):
        r"""
            ミラージョイントの名前の置換後の文字列を返す。
            
            Returns:
                str:
        """
        return self.__replaced_str

    def setIsReplacingParent(self, state):
        r"""
            ミラージョイントの親も置換処理によって変更するかどうかを設定する。
            
            Args:
                state (bool):
        """
        self.__is_replacing_parent = bool(state)

    def isReplacingParent(self):
        r"""
            ミラージョイントの親も置換処理によって変更するかどうか
            
            Returns:
                bool:
        """
        return self.__is_replacing_parent

    def setParentSearchingString(self, searchingString):
        r"""
            ミラージョイントの親の名前を置換処理によって見つけるための
            置換対象文字列をセットする。
            
            Args:
                searchingString (str):
        """
        self.__parent_searching_str = searchingString

    def parentSearchingString(self):
        r"""
            ミラージョイントの親の名前を置換処理によって見つけるための
            置換対象文字列を返す。
            
            Returns:
                str:
        """
        return self.__parent_searching_str

    def setParentReplacedString(self, replacedString):
        r"""
            ミラージョイントの親の名前を置換処理によって見つけるための
            置換後の文字列をセットする。
            
            Args:
                replacedString (str):
        """
        self.__parent_relaced_str = replacedString

    def parentReplacedString(self):
        r"""
            ミラージョイントの親の名前を置換処理によって見つけるための
            置換後の文字列を返す。
            
            Returns:
                str:
        """
        return self.__parent_relaced_str
    # =========================================================================

    @staticmethod
    def mirrorJoint(
            joint,
            applyToChildren,
            isMirrorBehavior, mirrorPlane,
            searchingString, replacedString,
            isReplacingParent,
            parentSearchingString, parentReplacedString,
            newParent = ''
        ):
        r"""
            ジョイントのミラーを行う。こちらは引き数を渡して即実行可能
            なスタティックメソッド。
            
            Args:
                joint (list):
                applyToChildren (str):
                isMirrorBehavior (bool):
                mirrorPlane (str):
                searchingString (str):
                replacedString (str):
                isReplacingParent (str):
                parentSearchingString (str):
                parentReplacedString (str):
                newParent (str):
                
            Returns:
                node.DagNode:
        """
        joint = node.asObject(joint)
        cmd_flags = {mirrorPlane : True, 'mb' : isMirrorBehavior}
        orig_rotation = list(joint('r')[0])

        parent_proxy = node.createNode('transform')
        joint_proxy  = node.createNode('joint', p=parent_proxy)
        joint_proxy.fitTo(joint)

        tmp_m_joint = node.asObject(
            cmds.mirrorJoint(joint_proxy, **cmd_flags)[0]
        )
        n_joint = node.duplicate(joint, po=True)[0]
        n_joint.rename(joint.replace(searchingString, replacedString))

        # ロックされているアトリビュートを一時的にアンロックする。=============
        n_jointLockedAttrs = []
        for attr in ('t', 'r', 's', 'jo'):
            for ax in ('xyz'):
                plug = n_joint.attr(attr+ax)
                if plug.isLocked():
                    n_jointLockedAttrs.append(plug)
                    plug.setLock(False)
        # =====================================================================

        # ミラー先の親を確定する。=============================================
        origin_parent = joint.parent()
        new_parent = node.asObject(newParent)
        if not new_parent:
            if (
                isReplacingParent and origin_parent and
                '|' not in origin_parent
            ):
                replaced_parent = node.asObject(
                    origin_parent.replace(
                        parentSearchingString, parentReplacedString, 1
                    )
                )
                if replaced_parent != origin_parent and replaced_parent:
                    parent = replaced_parent
                else:
                    parent = None
            else:
                parent = None
        else:
            parent = new_parent
        # =====================================================================

        if parent:
            parent.addChild(n_joint)
        n_joint.fitTo(tmp_m_joint)

        # jointOrient値を決定するために代理ジョイントを作成する。
        if not parent and origin_parent:
            parent = origin_parent

        m_parent_proxy = node.createNode('transform', p=parent_proxy)
        if parent:
            m_parent_proxy.fitTo(parent)
        n_joint_proxy  = node.createNode('transform', p=m_parent_proxy)
        cmds.parentConstraint(tmp_m_joint, n_joint_proxy)

        n_joint_rot_proxy = node.createNode('transform', p=n_joint_proxy)
        n_joint_rot_proxy('r', orig_rotation)

        mtx = node.MTransformationMatrix(
            node.MMatrix(n_joint_rot_proxy('inverseMatrix'))
            *node.MMatrix(n_joint_proxy('matrix'))
        )
        n_joint('jo', [node.toDegree(x) for x in mtx.rotation(False)])
        n_joint('r', orig_rotation)

        # アトリビュートのロック状態の復元。===================================
        for lockedAttr in n_jointLockedAttrs:
            cmds.setAttr(lockedAttr, l=True)
        cmds.delete(parent_proxy)
        # =====================================================================

        # =====================================================================
        if applyToChildren and joint.hasChild():
            for child in joint.children(type='joint'):
                JointMirror.mirrorJoint(
                    child,
                    applyToChildren,
                    isMirrorBehavior, mirrorPlane,
                    searchingString, replacedString,
                    '',
                    '', '',
                    newParent = n_joint
                )
        # =====================================================================
        return n_joint

    def execute(self, selected=None):
        r"""
            クラスの設定に従ってミラーリングを実行する。
            
            Args:
                selected (list):
        """
        selected_joints = node.selected(type='transform')
        results = []
        for joint in selected_joints:
            results.append(
                self.mirrorJoint(
                    joint,
                    self.applyToChildren(),
                    self.mirrorBehavior(), self.MirrorFlags[self.mirrorAxis()],
                    self.searchingString(), self.replacedString(),
                    self.isReplacingParent(),
                    self.parentSearchingString(), self.parentReplacedString()
                )
            )
        cmds.select([x() for x in results])


def mirrorJoints(jointlist=None):
    r"""
        選択ジョイントの反対側のジョイントをミラーリングする。
        引数jointListがNoneの場合は現在選択しているジョイントに対して実行する。
        反対側の条件は_L(R)が_R(L)に置き換わる事。
        
        Args:
            jointlist (list):
    """
    jointlist = node.selected(jointlist, type='transform')
    for joint in jointlist:
        all_children = joint.allChildren(type='transform')
        all_children.append(joint)
        all_children.reverse()
        for child in all_children:
            rev = child.replace('_L', '_R')
            if child == rev:
                continue
            util.mirror([child(), rev])


def mirrorJointsAlternately(jointlist=None):
    r"""
        ジョイントをミラーリングする。
        引数jointListがNoneの場合は現在選択しているジョイントに対して実行する。
        jointlistのn番目のジョイントのミラーリングをn+1番目のジョイントに
        適応する。
        
        Args:
            jointlist (list):
    """
    jointlist = node.selected(jointlist, type='transform')
    if len(jointlist) % 2:
        raise ValueError(
            'Specify a mirrored joint and a mirroring joint.'
        )
    util.mirror(jointlist)


def createHalfRotater(nodes=None):
    r"""
        引数nodesの半分の回転を行うノードを作成する。
        戻り値では作成されたhalfRotaterとpairBlendのtupleを持つリストを返す。
        
        Args:
            nodes (list):
            
        Returns:
            list:
    """
    result = []
    for j in node.selected(nodes, type='transform'):
        halfrot_j = node.asObject(cmds.duplicate(j, po=True)[0])
        halfrot_j.editAttr([x+y for x in 'trs' for y in 'xyz'], l=False)
        newNames  = j.split('_')
        if halfrot_j.hasAttr('radius'):
            halfrot_j('radius', halfrot_j('radius')*1.5)
        pb = node.createUtil('pairBlend', n='%sHalfRot_pb' % j)
        pb('weight', 0.5)
        pb('rotInterpolation', 1)
        pb('inRotate1', halfrot_j('r')[0])

        if not halfrot_j.hasAttr('rotationWeight'):
            weight_attr = halfrot_j.addFloatAttr(
                'rotationWeight', min=0, max=1, smn=-10, smx=10, default=0.5
            )
        else:
            weight_attr = halfrot_j.attr('rotationWeight')
        weight_attr >> pb/'weight'

        ~j.attr('r') >> ~pb.attr('ir2')
        ~pb.attr('or') >> ~halfrot_j.attr('r')
        ~j.attr('t') >> ~halfrot_j.attr('t')
        ~j.attr('s') >> ~halfrot_j.attr('s')
       
        result.append((halfrot_j, pb))
    if result:
        cmds.select([x[0] for x in result], ne=True, r=True)
    return result

def fixOrientation(jointlist=None):
    r"""
        ジョイントのX軸を子の方向へ向ける。
        
        Args:
            jointlist (list):捜査対象ジョイントのリスト。
    """
    jointlist = node.selected(jointlist)
    om = OrientationModifier()
    om.setApplyToChildren(False)

    for joint in jointlist:
        alljoints = joint.allChildren(type='transform')
        alljoints.append(joint)
        alljoints.reverse()
        for joint in alljoints:
            if not joint.isType('joint'):
                om.setFreezeOnly(False)
                continue
            try:
                om.setPrimaryAxis('-X' if joint.isOpposite() else '+X')
                om.setFreezeOnly(False)
            except Exception as e:
                om.setFreezeOnly(True)
            om.execute([joint])

def parentChain(jointList=None, isReverse=True):
    r"""
        与えられたTransformのリスト順番に親子付けする。
        isReverseがFalseの場合選択順番と親子関係が逆になる。
        デフォルトは選択順が早いものほど親になる。
        
        Args:
            jointList (list):Transformノード名のリスト
            isReverse (bool):
    """
    jointList = node.selected(jointList, type='transform')
    num = len(jointList)
    if num < 2:
        return
    if isReverse:
        jointList.reverse()
    for i in range(0, num-1):
        cmds.parent(jointList[i], jointList[i+1])


def parentBasedDirection(nodelist=None, direction=[0, 1, 0], threshold=45):
    r"""
        引数directionで指定された向きに沿って、nodelistをチェイン上にペアレント
        する。
        
        Args:
            nodelist (list):操作対象となるTransformのリスト
            direction (list):ペアレント方向を指定するベクトル
            threshold (float):子供を見つける際の検索最大角度。デフォルトは45°
            
        Returns:
            list:ペアレント化した際のトップノードのリスト
    """
    import math
    t = math.sin(math.radians(threshold))
    vectors = {x:node.MVector(x.position()) for x in nodelist}
    parentlist = []
    processing = [x for x in vectors]
    d = node.MVector(direction).normalize()
    
    for j in vectors:
        lines = {}
        for tgt in processing:
            if j is tgt:
                continue
            src_vec = vectors[j]
            tgt_vec = vectors[tgt]
            vec = (tgt_vec - src_vec)
            # 内積がしきい値以下の場合、このノードの処理を終了。
            l = vec.length()
            if (vec.normalize()*d) < t:
                continue
            lines.setdefault(l, []).append(tgt)
        if not lines:
            continue
        llist = list(lines.keys())
        llist.sort()
        child = lines[llist[0]][0]
        del processing[processing.index(child)]
        
        for plist in parentlist:
            if child in plist:
                plist.insert(plist.index(child), j)
                break
            elif j in plist:
                plist.insert(plist.index(j)+1, child)
                break
        else:
            parentlist.append([j, child])

    chained_list = []
    for plist in parentlist:
        for clist in chained_list:
            if clist[-1] == plist[0]:
                clist.extend(plist[1:])
                break
        else:
            chained_list.append(plist)
        
    selections = []
    for plist in chained_list:
        selections.append(plist[0])
        parentChain(plist)
    if selections:
        cmds.select(selections)
    return selections


class CameraBasedParentTool(util.CameraInfo):
    r"""
        任意のカメラの向きと入力ベクトルに従って、ワールド空間上での軸を生成。
        その軸方向に従ってTransformをペアレントする機能を提供するクラス。
    """
    def parent(self, newVector, start, end, nodelist=None):
        r"""
            引数start, endの方向とカメラの向きからワールド空間上での軸を特定し、
            その軸の向きに従って引数nodelistをチェイン状にペアレントする。

            Args:
                newVector (list):入力ベクトル
                start (QtCore.QPoint):ドラッグ開始座標
                end (QtCore.QPoint):ドラッグ終了座標
                nodelist (list):parent対象ノードリスト(Transform)
                
            Returns:
                list:ペアレント化した際のトップノードのリスト
        """
        camera, view = self.cameraView()
        nodelist = node.selected(type='transform')
        drawn_vec = self.getDrawnVector(start, end)
        return parentBasedDirection(nodelist, drawn_vec)
