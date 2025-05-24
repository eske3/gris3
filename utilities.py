# -*- coding:utf-8 -*-
import re

from maya import cmds
from gris3 import func, grisNode
from gris3.toHumanIK import MCPJointTable

UncleanedData = ['rigData_grp', 'renderData_grp']


def matchBaseSkeleton(sourceNamespace='', attributeMatching=True):
    def matchTransformableAttribute(src, dst):
        # Transfer transformation attributes.------------------------------
        for attr in ['t', 'r', 's']:
            for axis in func.Axis:
                value = cmds.getAttr('%s.%s%s' % (src, attr, axis))
                cmds.setAttr('%s.%s%s' % (dst, attr, axis), value)
        for attr in ['shxy', 'shxz', 'shyz']:
            value = cmds.getAttr('%s.%s' % (src, attr))
            cmds.setAttr('%s.%s' % (dst, attr), value)
        # -----------------------------------------------------------------

    def matchWorldPosition(src, dst):
        cmds.delete(cmds.parentConstraint(src, dst))

    method = (
        matchTransformableAttribute if attributeMatching else matchWorldPosition
    )

    if not sourceNamespace:
        selected = cmds.ls(sl=True)
        if not selected:
            return
        if not cmds.referenceQuery(selected[0], inr=True):
            return
        filepath = cmds.referenceQuery(selected[0], f=True)
        sourceNamespace = cmds.file(filepath, q=True, ns=True)

    def match(parent, namespace):
        children = cmds.listRelatives(parent, c=True, type='transform')
        if not children:
            return
        
        for child in children:
            source = namespace + ':' + child
            if not cmds.objExists(source):
                continue

            method(source, child)

            # Skip this process if the nodet type is not joint.----------------
            if (
                cmds.nodeType(child) != 'joint' or
                cmds.nodeType(source) != 'joint'
            ):
                match(child, namespace)
                continue
            # -----------------------------------------------------------------

            # Transfer joint attributes.---------------------------------------
            for attr in ['ra', 'jo']:
                for axis in func.Axis:
                    value = cmds.getAttr('%s.%s%s' % (source, attr, axis))
                    cmds.setAttr('%s.%s%s' % (child, attr, axis), value)

            r = cmds.getAttr('%s.radius' % source)
            cmds.setAttr('%s.radius' % child, r)
            # -----------------------------------------------------------------

            match(child, namespace)
    
    match('world_trs', sourceNamespace)


# /////////////////////////////////////////////////////////////////////////////
# There are functions for the low asset.                                     //
# /////////////////////////////////////////////////////////////////////////////
def parentLowGeometry(topNode='all_grp'):
    if not cmds.objExists(topNode):
        return

    root = grisNode.getGrisRoot()
    mobj = re.compile('_geo\d*')
    low_dispset = root.allSet().displaySet().addSet('low')

    for node in cmds.listRelatives(topNode, c=True, type='transform'):
        targetJoint = mobj.sub('', node)
        if not cmds.objExists(targetJoint) or node == targetJoint:
            continue

        try:
            node = cmds.parent(node, targetJoint)
        except:
            continue
        low_dispset.addChild(node)

def renameFromParentBaseJoint(root='world_trs'):
    # Creates an all_grp if it doesn't exist.
    if not cmds.objExists('all_grp'):
        cmds.createNode('transform', n='all_grp')
    joints = cmds.listRelatives('world_trs', ad=True, pa=True)

    for j in joints:
        child = cmds.listRelatives(j, c=True, type='transform', pa=True)
        if not child:
            continue

        for c in child:
            meshes = cmds.listRelatives(c, c=True, type='mesh', pa=True)
            if not meshes:
                continue

            for mesh in meshes:
                if cmds.getAttr(mesh + '.io'):
                    cmds.delete(mesh)
            newgeo = cmds.rename(c, j + '_geo')
            cmds.parent(newgeo, 'all_grp')

    cmds.select('all_grp', r=True, ne=True)
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////

def parentMCPGeometry(topNode='render_grp'):
    mobj = re.compile('_geo\d*')
    for node in cmds.listRelatives(topNode, c=True, type='transform'):
        targetJoint = mobj.sub('', node)
        simple_name = targetJoint.split('_jnt')[0]
        simple_name = simple_name[0].upper() + simple_name[1:]
        targetJoint = MCPJointTable.get(targetJoint, simple_name)
        if not cmds.objExists(targetJoint):
            continue
        node = cmds.parent(node, targetJoint)

# /////////////////////////////////////////////////////////////////////////////
# For modelers.                                                              //
# /////////////////////////////////////////////////////////////////////////////
def cleanup(nodes=None):
    if not isinstance(nodes, (list, tuple)):
        nodes = [nodes]
    if not nodes:
        nodes = cmds.ls(sl=True)
    cmds.makeIdentity(nodes, a=True, t=True, r=True, s=True)
    cmds.cluster(nodes)
    cmds.delete(nodes, ch=True)

    all_children = cmds.listRelatives(nodes, ad=True, type='transform')
    all_children.extend(nodes)
    cmds.xform(all_children, os=True, piv=[0, 0, 0])

    cmds.displaySmoothness(polygonObject=1)

def cleanupFacialTarget():
    all_children = cmds.listRelatives(
        'facialTarget_grp', ad=True, pa=True, type='mesh'
    )
    if not all_children:
        return

    target_meshes = []
    deleted = []
    # Delete intermediate objects.---------------------------------------------
    for child in all_children:
        if cmds.getAttr('%s.io' % child):
            deleted.append(child)
        else:
            target_meshes.append(child)
    if deleted:
        cmds.delete(deleted)
    # -------------------------------------------------------------------------

    for child in target_meshes:
        # Remove matrials.-----------------------------------------------------
        sg_connections = cmds.listConnections(
            child, type='shadingEngine', d=True, s=False, p=True, c=True
        )
        if sg_connections:
            for i in range(0, len(sg_connections), 2):
                cmds.disconnectAttr(sg_connections[i], sg_connections[i+1])
        # ---------------------------------------------------------------------

        # Delete uvs of the polygon objects.-----------------------------------
        uvsets = cmds.polyUVSet(child, q=True, auv=True)
        if not uvsets:
            continue
        if len(uvsets) > 1:
            for uvset in uvsets[1:]:
                cmds.polyUVSet(child, uvs=uvset, delete=True)
        cmds.polyMapDel(child, ch=False)
        # ---------------------------------------------------------------------

    # Freeze transformations.--------------------------------------------------
    categories = cmds.listRelatives('facialTarget_grp', c=True)
    for category in categories:
        top_grps = cmds.listRelatives(category, c=True)
        if not top_grps:
            continue

        for top_grp in top_grps:
            children = cmds.listRelatives(top_grp, c=True)
            if not children:
                continue
            cleanup(children)
    # -------------------------------------------------------------------------

def cleanupAll():
    if not cmds.objExists('all_grp'):
        return

    children = cmds.listRelatives('all_grp', c=True)
    if not children:
        return

    cleaned = [x for x in children if not x in UncleanedData]
    cleanup(cleaned)
    
    cleanupFacialTarget()
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////



