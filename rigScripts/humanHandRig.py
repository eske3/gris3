#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    手(指)を作成するための機能を提供するモジュール。
    
    Dates:
        date:2017/02/01 1:45[Eske](eske3g@gmail.com)
        update:2020/10/20 15:22 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import rigScripts, node
func = rigScripts.func
cmds = func.cmds

Category = 'Basic Human'
BaseName = 'hand'

class JointCreator(rigScripts.JointCreator):
    r"""
        手(指)のジョイント作成機能を提供するクラス。
    """
    def process(self):
        r"""
            ジョイント作成プロセスとしてコールされる。
        """
        from gris3.tools import jointEditor
        name = self.basenameObject()
        parent = self.parent()
        
        xFactor = -1 if self.positionIndex() == 3 else 1

        # 親指。---------------------------------------------------------------
        name.setName('thumbBase')
        thumbBase = node.createNode('joint', n=name(), p=parent)
        thumbBase.setPosition((xFactor * 57.5, 112.0, 1.5))

        name.setName('thumbMiddle')
        thumbMiddle = node.createNode('joint', n=name(), p=thumbBase)
        thumbMiddle.setPosition((xFactor * 59.9, 109.2, 4.2))

        name.setName('thumbDistal')
        thumbDistal = node.createNode('joint', n=name(), p=thumbMiddle)
        thumbDistal.setPosition((xFactor * 62.7, 105.8, 5.4))

        name.setName('thumbEnd')
        thumbEnd = node.createNode('joint', n=name(), p=thumbDistal)
        thumbEnd.setPosition((xFactor * 65.0, 103.3, 6.7))
        # ---------------------------------------------------------------------

        # 人差し指。-----------------------------------------------------------
        name.setName('indexRoot')
        indexRoot = node.createNode('joint', n=name(), p=parent)
        indexRoot.setPosition((xFactor * 59.5, 112.7, 0.5))

        name.setName('indexBase')
        indexBase = node.createNode('joint', n=name(), p=indexRoot)
        indexBase.setPosition((xFactor * 65.0, 108.5, 1.5))

        name.setName('indexMiddle')
        indexMiddle = node.createNode('joint', n=name(), p=indexBase)
        indexMiddle.setPosition((xFactor * 68.3, 104.8, 2.3))

        name.setName('indexDistal')
        indexDistal = node.createNode('joint', n=name(), p=indexMiddle)
        indexDistal.setPosition((xFactor * 70.5, 102.6, 2.8))

        name.setName('indexEnd')
        indexEnd = node.createNode('joint', n=name(), p=indexDistal)
        indexEnd.setPosition((xFactor * 72.3, 100.6, 3.2))
        # ---------------------------------------------------------------------
        
        # 中指。---------------------------------------------------------------
        name.setName('middleRoot')
        middleRoot = node.createNode('joint', n=name(), p=parent)
        middleRoot.setPosition((xFactor * 59.4, 112.9, -1.2))

        name.setName('middleBase')
        middleBase = node.createNode('joint', n=name(), p=middleRoot)
        middleBase.setPosition((xFactor * 65.1, 108.4, -1.2))

        name.setName('middleMiddle')
        middleMiddle = node.createNode('joint', n=name(), p=middleBase)
        middleMiddle.setPosition((xFactor * 68.7, 104.4, -1.3))

        name.setName('middleDistal')
        middleDistal = node.createNode('joint', n=name(), p=middleMiddle)
        middleDistal.setPosition((xFactor * 71.1, 102.0, -1.4))

        name.setName('middleEnd')
        middleEnd = node.createNode('joint', n=name(), p=middleDistal)
        middleEnd.setPosition((xFactor * 73.5, 99.6, -1.4))
        # ---------------------------------------------------------------------
        
        # 薬指。---------------------------------------------------------------
        name.setName('ringRoot')
        ringRoot = node.createNode('joint', n=name(), p=parent)
        ringRoot.setPosition((xFactor * 59.4, 112.8, -2.6))

        name.setName('ringBase')
        ringBase = node.createNode('joint', n=name(), p=ringRoot)
        ringBase.setPosition((xFactor * 64.7, 108.2, -3.7))

        name.setName('ringMiddle')
        ringMiddle = node.createNode('joint', n=name(), p=ringBase)
        ringMiddle.setPosition((xFactor * 67.9, 104.4, -4.5))

        name.setName('ringDistal')
        ringDistal = node.createNode('joint', n=name(), p=ringMiddle)
        ringDistal.setPosition((xFactor * 69.9, 102.2, -5.0))

        name.setName('ringEnd')
        ringEnd = node.createNode('joint', n=name(), p=ringDistal)
        ringEnd.setPosition((xFactor * 71.8, 100.2, -5.5))
        # ---------------------------------------------------------------------

        # 小指。---------------------------------------------------------------
        name.setName('pinkyRoot')
        pinkyRoot = node.createNode('joint', n=name(), p=parent)
        pinkyRoot.setPosition((xFactor * 59.4, 112.7, -4.1))

        name.setName('pinkyBase')
        pinkyBase = node.createNode('joint', n=name(), p=pinkyRoot)
        pinkyBase.setPosition((xFactor * 63.4, 108.1, -5.9))

        name.setName('pinkyMiddle')
        pinkyMiddle = node.createNode('joint', n=name(), p=pinkyBase)
        pinkyMiddle.setPosition((xFactor * 65.9, 105.2, -7.2))

        name.setName('pinkyDistal')
        pinkyDistal = node.createNode('joint', n=name(), p=pinkyMiddle)
        pinkyDistal.setPosition((xFactor * 67.3, 103.3, -7.9))

        name.setName('pinkyEnd')
        pinkyEnd = node.createNode('joint', n=name(), p=pinkyDistal)
        pinkyEnd.setPosition((xFactor * 68.8, 101.5, -8.7))
        # ---------------------------------------------------------------------

        # Fix orientation.-----------------------------------------------------
        om = jointEditor.OrientationModifier()
        om.setSecondaryMode('vector')
        om.setApplyToChildren(True)
        if xFactor < 0:
            om.setPrimaryAxis('-X')
            om.setTargetUpAxis('-Z')
        else:
            om.setPrimaryAxis('+X')
            om.setTargetUpAxis('+Z')
        om.execute([thumbBase])

        om.setTargetUpAxis('+X')
        om.execute((indexRoot, middleRoot, ringRoot, pinkyRoot))
        # ---------------------------------------------------------------------

        # Unit setting.--------------------------------------------------------
        unit = self.unit()
        unit.addMember('thumbBase', [thumbBase])
        unit.addMember(
            'extraBase', (indexRoot, middleRoot, ringRoot, pinkyRoot)
        )
        # ---------------------------------------------------------------------

        self.asRoot(thumbBase, indexRoot, middleRoot, ringRoot, pinkyRoot)
        for finger in (thumbBase, indexRoot, middleRoot, ringRoot, pinkyRoot):
            for child in finger.allChildren(type='joint'):
                child.setRadius(0.5)
            finger.setRadius(0.55)


class RigCreator(rigScripts.RigCreator):
    r"""
        手(指)のリグ作成機能を提供するクラス。
    """
    def createBaseController(self, joint, ctrlGrp, xFactor, animSet):
        r"""
            根本のコントローラを作成し、そのコントローラをと子ノードを返す。
            子が居ない場合はNoneを返す。
            
            Args:
                joint (node.Transform):
                ctrlGrp (node.Transform):
                xFactor (int):場所(LかRか)による係数
                animSet (grisNode.AnimSet):

            Returns:
                tuple:作成されたコントローラと、jointの子または親のタプル
                
        """
        # シェイプに関する設定。===============================================
        creator = func.PrimitiveCreator()
        creator.setCurveType('sphere')
        creator.setColorIndex(self.colorIndex('extra'))
        other = (
            joint.children()[0] if joint.hasChild()
            else joint.parent()
        )
        length = (
            func.Vector(joint.position()) - func.Vector(other.position())
        ).length()
        creator.setSize(length*0.1)
        creator.setTranslation((0, 0, length*0.5*xFactor))
        # =====================================================================

        name = func.Name(joint)
        name.setNodeType('ctrl')
        spacename = name.convertType('ctrlSpace')
        ctrl, space = func.createFkController(
            joint, ctrlGrp, name(), spacename(), skipTranslate=False
        )
        creator.create(parentNode=ctrl)
        animSet.addChild(ctrl)
        return ctrl, other if joint.hasChild() else None

    def createChildController(
        self, joint, ctrlGrp, xFactor, shapeCreator, animSet
    ):
        r"""
            末端のジョイントまで再帰的にFKコントローラを作成する。
            
            Args:
                joint (node.Transform):
                ctrlGrp (node.Transform):
                xFactor (int):X軸の正負
                shapeCreator (func.PrimitiveCreator):
                animSet (grisNode.AnimSet):
                
            Returns:
                list:作成されたコントローラのスペースノードのリスト
        """
        result = []
        if not joint.hasChild():
            return result
        children = joint.children()
        size = (
            func.Vector(joint.position()) - func.Vector(children[0].position())
        ).length() * -xFactor
        shapeCreator.setSize(size)

        name = func.Name(joint())
        name.setNodeType('ctrl')
        ctrl, ctrlspace = func.createFkController(
            joint, ctrlGrp, name(), name.convertType('ctrlSpace')(),
            skipTranslate=False, isLockTransform=False, calculateWithSpace=True
        )
        cmds.select(ctrlspace)
        ctrlspace.freeze(False, True, False)
        ctrlspace('ssc', joint('ssc'))
        shapeCreator.create(parentNode=ctrl)
        self.addLockedList(ctrlspace)
        animSet.addChild(ctrl)
        result.append(ctrlspace)

        for child in children:
            result.extend(
                self.createChildController(
                    child, ctrl, xFactor, shapeCreator, animSet
                )
            )
        return result

    def createControllers(
        self, rootjoint, ctrlGrp, xFactor, hasBase=False
    ):
        r"""
            コントローラを作成する。
            
            Args:
                rootjoint (node.Transform):
                ctrlGrp (node.Transform):
                xFactor (int):X軸の正負
                hasBase (bool):ベースコントローラを作成するかどうか
        """
        unit = self.unit()
        root_anim_set = self.animSet()
        name = func.Name(rootjoint)
        anim_set = root_anim_set.addSet(name.name(), unit.positionIndex())

        if hasBase:
            ctrls = self.createBaseController(
                rootjoint, ctrlGrp, xFactor, anim_set
            )
            if not ctrls:
                return
            ctrlGrp, rootjoint = ctrls

        # 子階層の全てのコントローラを作成。===================================
        creator = func.PrimitiveCreator()
        creator.setCurveType('pin')
        creator.setColorIndex(self.colorIndex('sub'))
        creator.setRotation((0, 180, 0))
        ctrlspaces = self.createChildController(
            rootjoint, ctrlGrp, xFactor, creator, anim_set
        )
        # =====================================================================

        # all用のコントローラを作成する。======================================
        # シェイプに関する設定。-----------------------------------------------
        creator.setCurveType('circle')
        creator.setRotation([180 * xFactor, 0, 0])
        creator.setColorIndex(self.colorIndex('key'))
        
        other = ctrlGrp if len(ctrlspaces) == 1 else ctrlspaces[-1]
        size = (
            func.Vector(ctrlspaces[0].position())
            -func.Vector(other.position())
        ).length() * 0.5
        creator.setSize(size)
        # ---------------------------------------------------------------------

        name = func.Name(rootjoint)
        name.setName(name.name()+'All')
        name.setNodeType('ctrlSpace')
        ctrlspace = func.createSpaceNode(n=name(), p=ctrlGrp)
        ctrlspace.fitTo(rootjoint)
        ctrlspace('ssc', rootjoint('ssc'))
        ctrlspace.lockTransform()
        ctrl = node.createNode(
            'transform', n=name.convertType('ctrl')(), p=ctrlspace
        )
        ctrl.editAttr(['t:a', 's:a'], k=False, l=True)
        ctrl('v', 1, k=False)
        creator.create(parentNode=ctrl)
        anim_set.addChild(ctrl)

        ctrl.attr('ry') >> [x/'ry' for x in ctrlspaces]
        ctrl.attr('rx') >> ctrlspaces[0].attr('rx')
        ctrl.attr('rz') >> ctrlspaces[0].attr('rz')
        # =====================================================================

    def process(self):
        r"""
            コントローラ作成プロセスとしてコールされる
        """
        unit = self.unit()
        unitname = self.unitName()
        basename = unitname.name()
        side = unit.positionIndex()
        anim_set = self.animSet()
        
        x_factor = -1 if side == 3 else 1

        thumbjoints = unit.getMember('thumbBase')
        extrajoints = unit.getMember('extraBase')
        alljoints = thumbjoints + extrajoints
        if not alljoints:
            raise RuntimeError(
                'No joint was found for the hand rig "%s".' % unitname
            )

        parents = set([x.parent() for x in alljoints])
        if not parents:
            raise RunttimeError('No parent node was not found for the hand.')
        if len(parents) > 1:
            raise RuntimeError(
                'A multiple parent nodes  were found for the hand.'
            )
        parent_src_finger = list(parents)[0]

        # Create parent proxy for controller.
        ctrl_parent_grp = self.createCtrlParentProxy(
            alljoints[0], name=basename
        )
        mltmtx = self.createParentMatrixNode(alljoints[0].parent())
        func.createDecomposeMatrix(
            ctrl_parent_grp, [mltmtx.attr('matrixSum')]
        )
        ctrl_parent_grp.lockTransform()
        # =====================================================================

        for joints, flag in ((thumbjoints, False), (extrajoints, True)):
            for joint in joints:
                self.createControllers(joint, ctrl_parent_grp, x_factor, flag)
