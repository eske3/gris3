#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2024/03/21 14:35 Eske Yoshinob[eske3g@gmail.com]
        update:2024/03/21 15:03 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import node
cmds = node.cmds

class ConsecutiveMesh(object):
    def __init__(self):
        self.__unite = None

    def setPolyUnite(self, uniteNode):
        r"""
            Args:
                uniteNode (str):
        """
        self.__unite = node.asObject(uniteNode)

    def polyUnite(self):
        return self.__unite

    def __check_matrix(matrix):
        r"""
            Args:
                matrix (list):
        """
        if not isinstance(matrix, (list, tuple)):
            raise AttributeError(
                'The matrix you want to set must be type a list or tuple.'
            )
        if len(matrix) != 16:
            raise AttributeError(
                'The matrix you want to set contains only 16 float elements.'
            )
        return list(matrix)

    def __get_matrix_node(self, plug_name):
        r"""
            Args:
                plug_name (str):
        """
        u = self.polyUnite()
        if not u:
            raise AttributeError(
                'Set a polyUnite node before setting the matrix.'
            )
        if not u.hasAttr(plug_name):
            plug = u.addMessageAttr(plug_name)
        else:
            plug = u.attr(plug_name)
        fbf_mtx = plug.source(type='fourByFourMatrix')
        if not fbf_mtx:
            fbf_mtx = node.createNode('fourByFourMatrix')
            fbf_mtx/'message' >> plug
        return fbf_mtx

    def setBaseMatrix(self, matrix):
        r"""
            Args:
                matrix (list):
        """
        fbf_mtx = self.__get_matrix_node('gris_base_matrix')
        fbf_mtx.setMatrix(matrix)

    def baseMatrix(self):
        fbf_mtx = self.__get_matrix_node('gris_base_matrix')
        return fbf_mtx.matrix()[0]

    def setOffsetMatrix(self, matrix):
        r"""
            Args:
                matrix (list):
        """
        fbf_mtx = self.__get_matrix_node('gris_offset_matrix')
        fbf_mtx.setMatrix(matrix)

    def offsetMatrix(self):
        fbf_mtx = self.__get_matrix_node('gris_offset_matrix')
        return fbf_mtx.matrix()[0]

    def setBaseMesh(self, meshName):
        u = self.polyUnite()
        if not u:
            raise AttributeError(
                'Set a polyUnite node before setting the base mesh.'
            )
        if not u.hasAttr('gris_basemesh'):
            plug = u.addMessageAttr('gris_basemesh')
        else:
            plug = u.attr('gris_basemesh')
        meshName+'.message' >> plug

    def baseMesh(self):
        u = self.polyUnite()
        if not u:
            raise AttributeError(
                'Set a polyUnite node before setting the base mesh.'
            )
        if not u.hasAttr('gris_basemesh'):
            plug = u.addMessageAttr('gris_basemesh')
        else:
            plug = u.attr('gris_basemesh')
        return plug.source()

    def update(self, count=1):
        u = self.polyUnite()
        if not u:
            return
        base_mtx = self.baseMatrix()
        offset_mtx = self.offsetMatrix()
        base_mesh = self.baseMesh()
        for base_attr in ('inputMat', 'inputPoly'):
            for attr in cmds.listAttr(u/base_attr, m=True) or []:
                u.attr(attr).disconnect(False)
        mtx = base_mtx
        mesh_plug = base_mesh.attr('outMesh')
        for i in range(count):
            u('inputMat[{}]'.format(i), mtx, type='matrix')
            mesh_plug >> '{}.inputPoly[{}]'.format(u, i)
            
            mtx = node.multiplyMatrix((offset_mtx, mtx))

    def setCount(self, count):
        r"""
            Args:
                count (int):
        """
        if count < 1:
            raise AttributeError('A nuber of count must be greater than 1.')
        self.update(count)
