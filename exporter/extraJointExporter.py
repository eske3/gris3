#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ExtraJointの書き出しや読み込みの機能を提供するクラス。
    
    Dates:
        date:2017/01/21 12:05[Eske](eske3g@gmail.com)
        update:2022/07/08 12:24 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import node
from .. import mathlib
from ..exporter import core
from ..tools import extraJoint
cmds = node.cmds

class Exporter(core.BasicExporter):
    r"""
        ExtraJointを書き出す機能を提供するクラス。
    """
    def __init__(self):
        super(Exporter, self).__init__()
        self.__extra_joints = []
        self.setExtension('json')

    def getShape(self, node):
        r"""
            ExtraJointのシェイプ"implicitSphere"を取得し名前を返す。
            見見つからなければNoneを返す。
            
            Args:
                node (gris3.node.Transform):ノード名
                
            Returns:
                gris3.node.AbstractNode:
        """
        shapes = cmds.listRelatives(node, shapes=True, type='implicitSphere')
        if not shapes:
            return
        if len(shapes) != 1:
            return
        return shapes[0]

    def setExtraJoints(self, nodelist):
        r"""
            ExtraJointのリストをセットする。
            
            Args:
                nodelist (list):
        """
        self.__extra_joints = [
            x() for x in extraJoint.listExtraJoints(nodelist)
        ]

    def extraJoints(self):
        r"""
            セットされたExtraJointのリストを返す。
            
            Returns:
                list:
        """
        return self.__extra_joints
    
    def export(self, file):
        r"""
            ファイルを書き出す。
            
            Args:
                file (str):出力ファイルパス。
                
            Returns:
                Bool:書き出しに成功した場合はTrueを返す。
        """
        from gris3 import system
        name_cls = system.GlobalSys().nameRule()
        extra_joints = extraJoint.listExtraJoints(self.extraJoints())
        if not extra_joints:
            return False

        datalist = []

        for joint in extra_joints:
            # joint = node.asObject(joint)
            shape = joint.shape()

            # 親情報の取得。===================================================
            parent = joint.parent() if joint.hasParent() else None
            length = -1
            if parent and parent.hasChild():
                children = parent.children()
                if len(children) > 1 and children[0] != joint:
                    length = (
                        mathlib.Vector(joint.position())\
                        -mathlib.Vector(parent.position())
                    ).length()
            # =================================================================

            # オフセット数を取得。=============================================
            offsets = cmds.listConnections(
                '%s.extraJointOffsets' % shape, s=True, d=False
            )
            num_offsets = len(offsets) if offsets else 0
            # =================================================================


            # ジョイント自身の名前、並びにノードの種類を取得。=================
            ctrl = joint.joint()
            node_type = ctrl.type()
            name = name_cls(ctrl)
            # =================================================================

            radius = joint.radius()
            j_size = ctrl('radius') if node_type=='joint' else 0.5
            
            tag = joint.tag()

            matrix = cmds.getAttr('%s.matrix' % joint)

            data = {
                'basename':name.name(), 'nodeType':node_type,
                'nodeTypeLabel':name.nodeType(), 'side':name.positionIndex(),
                'parent':parent, 'offset':num_offsets,
                'matrix':matrix, 'worldSpace':False,
                'radius':radius, 'jointSize':j_size,
                'parentLength':length, 'tag':tag
            }
            datalist.append(data)

        with open(file, 'w') as f:
            import json
            f.write(json.dumps(datalist, indent=4))
        return True


def loadExtraJointData(filepath):
    r"""
        jsonフィアルからExtraジョイントの情報を展開してリストとして返す。

        Args:
            filepath (str):入力ファイルパス
    """
    import json
    with open(filepath, 'r') as f:
        datalist = json.load(f)
    return datalist


def loadExtraJointScript(filepath):
    r"""
        jsonファイルからExtraジョイントを作成する。
        戻り値として作成されたExtraジョイントのリストを返す。

        Args:
            filepath (str):入力ファイルパス
            
        Returns:
            list:
    """
    datalist = loadExtraJointData(filepath)
    result = []
    for data in datalist:
        parent_length = data.pop('parentLength')
        print(data)
        result.append(extraJoint.create(**data))
    return result