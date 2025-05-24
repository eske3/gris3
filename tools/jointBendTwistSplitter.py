#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2023/04/10 17:42 Eske Yoshinob[eske3g@gmail.com]
        update:2023/04/10 23:03 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2023 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import node, verutil
cmds = node.cmds

GRIS_BEND_TWIST_ROOT_SPLITTER = ('grisJointBendTwistRootSplitterVersion', 1.0)
GRIS_BEND_TWIST_SPLITTER = ('grisJointBendTwistSplitterVersion', 1.0)

# プラグインのロード。
if not cmds.pluginInfo('quatNodes', q=True, l=True):
    cmds.loadPlugin('quatNodes')
    

def __bind_attr(ctnr, attrName, targetAttr, axis='XYZ'):
    r"""
        コンテナに任意のアトリビュートをバインドしてパブリッシュする
        ローカル関数。
        
        Args:
            ctnr (str):操作対象コンテナノード名
            attrName (str):パブリッシュするアトリビュート名
            targetAttr (str):パブリッシュに紐づけされるアトリビュート名
            axis (str):XYZなどの軸が複数ある場合用に指定するリストうにｔｙ
    """
    for ax in axis:
        attr = cmds.container(ctnr, e=True, publishName=attrName+ax)
        cmds.container(ctnr, e=True, bindAttr=(targetAttr+ax, attr))


def __createContainer(
    name, typeObj,
    parent=None, contaiedNodes=[],
    attrlist= [('outTwist', 'otw'), ('outBend', 'obd')]
):
    drv = cmds.container(
        name=name, type='dagContainer', addNode=contaiedNodes
    )
    if parent:
        drv = cmds.parent(drv, parent)[0]
    drv = typeObj(drv)
    plug = drv.addStringAttr(drv.CHECK_ATTR[0])
    plug.set(drv.CHECK_ATTR[1], type='string')
    plug.setLock(True)
    drv.lockTransform(k=False, l=False)
    drv('blackBox', 1, l=True)

    # 出力用アトリビュートの作成。---------------------------------------------
    for ln, sn in attrlist:
        cmds.addAttr(drv(), ln=ln, sn=sn, at='double3')
        for ax in 'XYZ':
            cmds.addAttr(
                drv(), ln = ln + ax, sn = sn + ax.lower(),
                at='doubleAngle', p=ln
            )
    # -------------------------------------------------------------------------
    drv.addFloatAttr(
        'twistRatio', min=-1000, max=1000, smn=0, smx=1, default=1
    )
    return drv


class AbstractSplitter(node.Transform):
    CHECK_ATTR = ''

    def __init__(self, nodeName):
        r"""
            Args:
                nodeName (str):
        """
        if verutil.PyVer < 3:
            super(AbstractSplitter, self).__init__(nodeName)
        else:
            super(AbstractSplitter, self).__init__()
        self.__is_valid = self.hasAttr(self.CHECK_ATTR[0])
        if self.__is_valid:
            self.__ver = self(self.CHECK_ATTR[0])
        else:
            self.__ver = ''

    def isValid(self):
        return self.__is_valid

    def version(self):
        return self.__ver

    def inputNode(self):
        input = self.attr('inRotate').source()
        if input:
            return input
        for attr in ~self.attr('inRotate'):
            input = attr.source()
            if input:
                return input
        raise ''

    def setTwistRatio(self, ratio):
        r"""
            Args:
                ratio (float):
        """
        self('twistRatio', ratio)

    def setDivision(self, numberOfDivisions):
        r"""
            Args:
                numberOfDivisions (int):
        """
        val = 1.0 / numberOfDivisions
        self.setTwistRatio(val)

    def connectBend(self, target):
        ~self.attr('outBend') >> ~target.attr('r')

    def connectTwist(self, targets):
        for tgt in targets:
            ~self.attr('outTwist') >> ~tgt.attr('r')

    def setupTwister(self, targets):
        self.connectBend(targets[0])
        self.connectTwist(targets[1:])
        self.setDivision(len(targets))


class RootSplitter(AbstractSplitter):
    CHECK_ATTR = GRIS_BEND_TWIST_ROOT_SPLITTER


class Splitter(AbstractSplitter):
    CHECK_ATTR = GRIS_BEND_TWIST_SPLITTER
    

def createRootSplitter(transform, parent=None, axis=(1, 0, 0)):
    r"""
        任意のTransformノードの回転を、を曲げとひねりに分解するノードを作成して
        返す。
        すでに作成済みの場合は、作成済みノードを返す。
        
        Args:
            transform (node.Transform):操作対象となるノード名
            parent (str):作成するノードを格納する親ノード名
            axis (list):
            
        Returns:
            RootSplitter:
    """
    target = node.asObject(transform)
    name = target.shortName() + '_rBndRllSpr'
    t_r = target.attr('r')
    t_ro = target.attr('ro')
    contained_nodes = []

    # ひねりの軸を定義し、そこから曲げ成分のみを抽出する。=====================
    # ひねり軸の定義。
    l_vec_cpsmtx = node.createUtil('composeMatrix', n=name+'InRotater')
    l_vec_pmm = node.createUtil('pointMatrixMult')
    t_r >> l_vec_cpsmtx/'inputRotate'
    t_ro >> l_vec_cpsmtx/'inputRotateOrder'
    l_vec_cpsmtx.attr('outputMatrix') >> l_vec_pmm/'im'
    l_vec_pmm('ip', axis)
    
    # 曲げ成分の回転を出力。
    ab = node.createUtil('angleBetween', n=name+'AB')
    ab('vector1', l_vec_pmm('o')[0])
    l_vec_pmm.attr('o') >> ab/'vector2'
    contained_nodes.extend([l_vec_cpsmtx, l_vec_pmm, ab])
    # =========================================================================
    
    # 全体回転から曲げ成分を引き、ひねり成分を抽出する。=======================
    aatq = node.createUtil('axisAngleToQuat')
    ab.attr('axis') >> aatq/'inputAxis'
    ab.attr('angle') >> aatq/'inputAngle'
    qi = node.createUtil('quatInvert')
    aatq.attr('outputQuat') >> qi/'inputQuat'
    e_t_q = node.createUtil('eulerToQuat')
    ~l_vec_cpsmtx.attr('inputRotate') >> ~e_t_q.attr('inputRotate')
    l_vec_cpsmtx.attr('inputRotateOrder') >> e_t_q.attr('inputRotateOrder')
    q_p = node.createUtil('quatProd')
    e_t_q.attr('outputQuat') >> q_p/'input1Quat'
    qi.attr('outputQuat') >> q_p/'input2Quat'
    q_slerp = node.createUtil('quatSlerp', n=name+'Slerp')
    q_slerp('input1Quat', q_p('outputQuat')[0])
    q_p.attr('outputQuat') >> q_slerp/'input2Quat'
    q_t_e = node.createUtil('quatToEuler', n=name+'OutTwist')
    q_slerp.attr('outputQuat') >> q_t_e/'inputQuat'
    contained_nodes.extend([aatq, qi, e_t_q, q_p, q_slerp, q_t_e])
    # =========================================================================
    
    # コンテナの作成。=========================================================
    drv = __createContainer(
        name, RootSplitter, parent, contained_nodes,
    )
    __bind_attr(drv, 'inRotate', l_vec_cpsmtx/'inputRotate')
    __bind_attr(drv, 'inRotateOrder', l_vec_cpsmtx/'inputRotateOrder', [''])
    ab/'euler' >> drv.attr('outBend')
    q_t_e/'outputRotate' >> drv.attr('outTwist')
    drv.attr('twistRatio') >> q_slerp/'inputT'
    # =========================================================================

    return drv


def createRootSplitterNodes(nodelist=None, parent=None, axis=(1, 0, 0)):
    r"""
        任意のTransformノードの回転を、を曲げとひねりに分解するノードを作成して
        返す。
        すでに作成済みの場合は、作成済みノードを返す。
        
        Args:
            nodelist (list):任意のTransformノードのリスト
            parent (str):作成するノードを格納する親ノード名
            axis (list):
    """
    nodelist = node.selected(nodelist, type='transform')
    results = []
    for n in nodelist:
        results.append(createRootSplitter(n, parent, axis))
    return results


def createSplitter(transform, parent=None, axis='x'):
    r"""
        Args:
            transform (node.Transform):
            parent (str):
            axis (str):
    """
    axis = axis.lower()
    axislist = ['x', 'y', 'z']
    if axis not in axislist:
        raise AttributeError('The axis must be either "x", "y" or "z".')
    target = node.asObject(transform)
    name = target.shortName() + '_bndRllSpr'
    contained_nodes = []
    
    e_t_q = node.createUtil('eulerToQuat', n=name+'InRotater')
    target.attr('r') >> e_t_q/'inputRotate'
    target.attr('rotateOrder') >> e_t_q/'inputRotateOrder'
    norm_q = node.createUtil('quatNormalize')
    for ax in [x.upper() for x in [axis, 'w']]:
        e_t_q.attr('outputQuat'+ax) >> norm_q/'inputQuat'+ax
    q_t_e = node.createUtil('quatToEuler')
    norm_q.attr('outputQuat') >> q_t_e/'inputQuat'
    pb = node.createUtil('pairBlend', n=name+'OutRotater')
    ~q_t_e.attr('outputRotate') >> ~pb.attr('inRotate2')
    pb('inRotate1', (0, 0, 0))
    contained_nodes.extend([e_t_q, norm_q, q_t_e, pb])

    # コンテナの作成。=========================================================
    drv = __createContainer(
        name, Splitter, parent, contained_nodes,
    )
    __bind_attr(drv, 'inRotate', e_t_q/'inputRotate')
    __bind_attr(drv, 'inRotateOrder', e_t_q/'inputRotateOrder', [''])
    pb/'outRotate' >> drv.attr('outTwist')
    drv.attr('twistRatio') >> pb/'weight'
    # =========================================================================
    
    return drv


def createSplitterNodes(nodelist=None, parent=None, axis='x'):
    r"""
        Args:
            nodelist (list):
            parent (str):
            axis (str):
    """
    nodelist = node.selected(nodelist, type='transform')
    results = []
    for n in nodelist:
        results.append(createSplitter(n, parent, axis))
    return results