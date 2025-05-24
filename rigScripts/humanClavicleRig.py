#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    UNITY用の鎖骨を作成するための機能を提供するモジュール。
    
    Dates:
        date:2017/02/01 1:01[Eske](eske3g@gmail.com)
        update:2023/01/24 11:12 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import rigScripts, node
from gris3.tools import jointEditor
func = rigScripts.func
cmds = func.cmds

Category = 'Basic Human'
BaseName = 'clavicle'

class JointCreator(rigScripts.JointCreator):
    r"""
        鎖骨のジョイント作成機能を提供するクラス。
    """
    def process(self):
        r"""
            ジョイント作成プロセスとしてコールされる。
        """
        name = self.basenameObject()
        parent = self.parent()
        
        if self.position() == 'R':
            x_factor = -1
        else:
            x_factor = 1

        # Clavicle.
        name.setName(self.name())
        clavicle = node.createNode('joint', n=name(), p=parent)
        clavicle.setPosition((x_factor * 3.0, 153.9, -2.1))
        clavicle.setRadius(1)

        # Uparm proxy.
        name.setName('uparm')
        uparm = node.createNode('joint', n=name(), p=clavicle)
        uparm.setPosition((x_factor * 18.2, 151.4, -4.7))
        uparm.setRadius(1.4)

        # Fix orientation.-----------------------------------------------------
        om = jointEditor.OrientationModifier()
        om.setSecondaryMode('vector')
        om.setApplyToChildren(False)
        if x_factor < 0:
            om.setPrimaryAxis('-X')
            om.setTargetUpAxis('+Z')
        else:
            om.setPrimaryAxis('+X')
            om.setTargetUpAxis('-Z')
        om.execute((clavicle, uparm))
        cmds.delete(uparm)
        # ---------------------------------------------------------------------

        # Unit setting.--------------------------------------------------------
        unit = self.unit()
        unit.addMember('clavicle', clavicle)
        # ---------------------------------------------------------------------

        self.asRoot(clavicle)
        clavicle.select()


class RigCreator(rigScripts.RigCreator):
    def process(self):
        r"""
            リグ作成の実装メソッド。
        """
        unit = self.unit()
        if unit.positionIndex() == 3:
            x_factor = -1
            rotFactor = 180
        else:
            x_factor = 1
            rotFactor = 0

        unitname = self.unitName()
        basename = unitname.name()
        side = unit.position()
        anim_set = self.animSet()

        clavicle_jnt = unit.getMember('clavicle')
        
        # Get controller size.
        clavicle_vector = func.Vector(clavicle_jnt.position())
        child_vector = None
        if not clavicle_jnt.hasParent():
            relative_node = (
                clavicle_jnt.parent() if clavicle_jnt.hasParent() else None
            )
        else:
            relative_node = clavicle_jnt.children()[0]
        if relative_node:
            relative_vector = func.Vector(relative_node.position())
            child_vector = clavicle_vector - relative_vector
            ctrl_size = child_vector.length() * 0.5
        else:
            ctrl_size = 10

        # Create root nodes.===================================================
        # Create parent proxy for rig.
        ctrl_parent_proxy = self.createCtrlParentProxy(
            clavicle_jnt, name=basename,
        )
        # =====================================================================

        # Create controllers.==================================================
        unitname.setName(basename)
        unitname.setNodeType('ctrlSpace')
        space = unitname()

        unitname.setNodeType('ctrl')
        ctrl = unitname()
        ctrl, space = func.createFkController(
            clavicle_jnt, parent=ctrl_parent_proxy,
            name=ctrl, spaceName=space,
            skipTranslate=False
        )
        ctrl.editAttr(['v'], k=False, l=False)
        # =====================================================================

        # Setup parent proxy node.=============================================
        parent_matrix = self.createParentMatrixNode(clavicle_jnt.parent())
        decmtx = func.createDecomposeMatrix(
            ctrl_parent_proxy, ['%s.matrixSum' % parent_matrix],
            withMultMatrix=False
        )
        ctrl_parent_proxy.lockTransform()
        # =====================================================================

        # /////////////////////////////////////////////////////////////////////
        # Add shapes to the all controllers.                                 //
        # /////////////////////////////////////////////////////////////////////
        # Adds shape to the bend controllers.----------------------------------
        creator = func.PrimitiveCreator()
        creator.setSizes(
            [ctrl_size, ctrl_size * 0.5 * x_factor, ctrl_size * 0.5]
        )
        if child_vector:
            matrix = clavicle_jnt.matrix()
            # Gets a Y Vector.
            y_vector = func.Vector([matrix[4], matrix[5], matrix[6]]).norm()
            pos = child_vector * -0.5
            pos.y = (child_vector.x * 0.5)
            pos.z = 0
            creator.setTranslation(pos)
            creator.setRotation([180, 90 * x_factor, 0])
        creator.setColorIndex(self.colorIndex('main'))
        creator.setCurveType('pyramid')
        creator.create(parentNode=ctrl)
        # ---------------------------------------------------------------------
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////

        # /////////////////////////////////////////////////////////////////////
        # Post precesses.                                                    //
        # /////////////////////////////////////////////////////////////////////
        # Add controller to the anim set.======================================
        anim_set.addChild(ctrl)
        # =====================================================================
        # /////////////////////////////////////////////////////////////////////
        #                                                                    //
        # /////////////////////////////////////////////////////////////////////