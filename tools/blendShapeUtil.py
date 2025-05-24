#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2024/09/25 14:32 Eske Yoshinob[eske3g@gmail.com]
        update:2024/09/25 15:24 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import node
from . import cleanup
cmds = node.cmds


def createBlendShapeForFacial(geometry, blendShape, facialGroup):
    r"""
        Args:
            geometry (str):
            blendShape (str):
            facialGroup (str):
    """
    f_grp = node.asObject(facialGroup)
    if not f_grp or not hasattr(f_grp, 'children'):
        return
    facial_targets = f_grp.children()
    if not facial_targets:
        return
    facial_targets.append(geometry)
    bs = cmds.blendShape(facial_targets, frontOfChain=True, n=blendShape)[0]


def duplicateTargets(geometry, blendShape, parent=None):
    r"""
        Args:
            geometry (str):
            blendShape (str):
            parent (str):
    """
    bs = node.asObject(blendShape)
    if not bs.isType('blendShape'):
        raise AttributeError(
            'The specified node "{}" is not blendShape.'.format(blendShape)
        )
    duplicated = bs.duplicateTargets(geometry)
    all_duplicated = cmds.listRelatives(
        duplicated, ad=True, pa=True, type='transform'
    ) or []
    all_duplicated = duplicated + all_duplicated
    cleanup.deleteUnusedIO(all_duplicated, False)
    for geo in all_duplicated:
        if not geo.isType('transform'):
            continue
        geo.unlockTransform()
    
    parent = node.asObject(parent)
    if not parent or not hasattr(parent, 'children'):
        return
    children = {x.shortName(): x for x in parent.children()}
    for geo in duplicated:
        name = geo.shortName()
        if name in children:
            geo.fitTo(children[name])
            cmds.delete(children[name])
        cmds.parent(geo, parent)

