#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ここに説明文を記入
    
    Dates:
        date:2017/04/22 14:50[Eske](eske3g@gmail.com)
        update:2022/01/09 21:35 Eske[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from collections import OrderedDict
from maya import OpenMayaUI
from gris3 import node, func, lib
cmds = func.cmds

# /////////////////////////////////////////////////////////////////////////////
# パラメーター                                                               //
# /////////////////////////////////////////////////////////////////////////////
ParameterPreset = OrderedDict()
ParameterPreset['feathery'] = {
    'stiffness' : 0.85,
    'mass' : 0.01,
    'drag' : 0.6,
    'damp' : 0.05,
    'gravity' : 0.98,
}
ParameterPreset['soft'] = {
    'stiffness' : 0.25,
    'mass' : 5.0,
    'drag' : 0.35,
    'damp' : 0.1,
    'gravity' : 9.8,
}
ParameterPreset['mid'] = {
    'stiffness' : 0.5,
    'mass' : 5.0,
    'drag' : 0.35,
    'damp' : 0.1,
    'gravity' : 9.8,
}
ParameterPreset['hard'] = {
    'stiffness' : 1.2,
    'mass' : 5.0,
    'drag' : 0.35,
    'damp' : 0.1,
    'gravity' : 9.8,
}
ParameterPreset['heavy'] = {
    'stiffness' : 0.45,
    'mass' : 100.0,
    'drag' : 0.35,
    'damp' : 1,
    'gravity' : 98,
}
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////

def getFrameRange():
    r"""
        シーンのフレームレンジを返す。
        
        Returns:
            startFrame, endFrame:
    """
    return (
        cmds.playbackOptions(q=True, min=True),
        cmds.playbackOptions(q=True, max=True)
    )

class SpringSimulatorRoot(node.Transform):
    r"""
        シミュレーション用ノードを格納するルートグループ
    """
    def initialize(self):
        self.lockTransform()
        baked_member_plug = self.addMessageAttr('bakedJoints', m=True)
        member_plug = baked_member_plug.nextElement
        cst_plug = self.addMessageAttr('constraintGroup')
        return baked_member_plug, member_plug, cst_plug

    def bakedMemberPlug(self):
        return self.attr('bakedJoints')

    def memberPlug(self):
        return self.bakedMemberPlug().nextElement

    def constraintGroupPlug(self):
        return self.attr('constraintGroup')

    def bakedJoints(self):
        r"""
            ベイク用ジョイントのリストを返す。
            
            Returns:
                list:
        """
        baked_nodes = []
        for joint in cmds.listConnections(
            self/'bakedJoints', s=True, d=False
        ):
            joint = node.asObject(joint)
            if joint:
                baked_nodes.append(joint)
        return baked_nodes

class SpringSimulator(object):
    r"""
        シミュレーションを実行するための機能を提供するクラス。
        このクラスはクラシックヘアーベースで動作する。
    """
    HairSystemAttrs = {
        'simulationMethod': 2,
        'evaluationOrder': 0,
        'drag': 0,
        'friction': 0,
        'mass': 5,
        'dynamicsWeight': 0,
        'gravity': 9.8,
        'stretchResistance' : 10,
        'compressionResistance' : 10,
        'bendResistance' : 0,
        'twistResistance' : 0,
        'restLengthScale' : 1.0,

        'startCurveAttract' : 0,
        'drag' : 0.05,
        'tangentialDrag' : 0.1,
        'motionDrag' : 0.1,
        'drag' : 0.12,
        'stretchDamp' : 0.1,
    }
    HairSystemAttrsArray = {
        'clumpWidthScale': [(0.0, 1.0, 3), (1.0, 0.2, 3)],
        'clumpCurl': [(0.0, 0.5, 1)],
        'clumpFlatness': [(0.0, 0.0, 1)],
        'hairWidthScale': [(0.8, 1.0, 3),(1.0, 0.2, 3)]
    }
    HairSystemHiddenAttrs = [
        'sim', 'cld', 'cos', 'scd', 'cdg', 'ghe', 'wid', 'stc', 'rpl',
        'ncn', 'dwd', 'wds', 'dpq', 'ssg', 'cwd', 'ctw', 'bnf', 'hwd',
        'bmp', 'opc', 'hcr', 'hcg', 'hcb', 'hpc', 'thn', 'tlc', 'spr',
        'spg', 'spb', 'spp', 'csd', 'dfr', 'sra', 'chr', 'csr', 'cvr',
        'mst', 'ms1', 'ms2', 'leh', 'crl', 'crf', 'nmt', 'noi', 'dno',
        'nof', 'nfu', 'nfv', 'nfw', 'scm', 'scp', 'scr', 'nuc', 'nvc',
        'cin', 'inr', 'cti', 'stf', 'v'
    ]

    FollicleAttrs = {
        'parameterU': 0.5,
        'parameterV': 0.5,
        'restPose': 3,
        'segmentLength': 1.0,
        'sampleDensity': 1.0,
        'degree': 1,
        'collide': 0
    }
    FollicleAttrsArray = {
        'stiffnessScale': [(0.0, 1.0, 3),(1.0, 0.2, 3)],
        'clumpWidthScale': [(0.0, 1.0, 3),(1.0, 0.2, 3)],
        'attractionScale': [(0.0, 1.0, 3),(1.0, 0.2, 3)]
    }

    def __init__(self):
        r"""
            ここに説明文を記入
            
            Returns:
                any:
        """
        self.__hirlist = {}
        self.__pre_selections = []
        self.__displayflags = None

    def setup(self, targets=None):
        r"""
            シミュレーションを行うためのセットアップを行う。
            
            Args:
                targets (list):シミュレーション対象となるノードのリスト
        """
        self.__pre_selections = cmds.ls(sl=True)
        self.__hirlist = {}
        def searchHir(object, jointlist):
            r"""
                シミュレーション対象となるTransformノードチェーンを検出する
                
                Args:
                    object (node.Transform):
                    jointlist (list):出力先となるリスト
            """
            children = object.children(type='transform')
            if not children:
                return

            if children[0].listAttr(k=True):
                jointlist.append(children[0])
            searchHir(children[0], jointlist)

            for child in children[1:]:
                analyze(child)

        def analyze(object):
            r"""
                階層構造と解析を行う。
                
                Args:
                    object (node.Transform):
            """
            if not object.listAttr(k=True):
                # Keyableアトリビュートがない場合は子を探索する。
                for child in object.children(type='transform'):
                    analyze(child)
                return

            jointlist = [object]
            # 親を特定し、そのグループに入れる。===============================
            if object.hasParent():
                parent = object.parent()
                pname = parent()
            else:
                pname = None
            if pname in self.__hirlist:
                self.__hirlist[pname].append(jointlist)
            else:
                self.__hirlist[pname] = [jointlist]
            # =================================================================

            searchHir(object, jointlist)

        targets = node.selected(targets, type='transform')
        for target in targets:
            analyze(target)

    def hierarchyList(self):
        return self.__hirlist

    def createSimulatedSystem(self, simOption=None):
        r"""
            シミューレーション用のノードを作成する。
            simOptionはここで作成されるhairSystemに渡すアトリビュートの
            辞書オブジェクト。
            辞書のキーはhairSystemのアトリビュート名、値は設定したい
            値を入れておく。
            
            Args:
                simOption (dict):hairSystemに渡すオプション
                
            Returns:
                SpringSimulatorRoot:シミュレーション用ノードをまとめるグループ
        """
        hir_list = self.hierarchyList()
        if not hir_list:
            raise RuntimeError(
                'Simulated nodes were not detected.'
                '(Execute setup method before simulating.)'
            )
        # ルートノードの作成。=================================================
        temp_root = SpringSimulatorRoot(
            node.createNode('curveVarGroup', n='simulated_grp').name()
        )
        baked_member_plug, member_plug, cst_plug = temp_root.initialize()
        # =====================================================================

        hairsystem_attrs = {x:y for x, y in self.HairSystemAttrs.items()}
        hairsystem_attrs['startFrame'] = cmds.playbackOptions(q=True, min=True)
        if isinstance(simOption, dict):
            hairsystem_attrs.update(simOption)

        # マスターのhairSystemのセットアップ。=================================
        master_hairsys = node.createNode(
            'hairSystem', p=temp_root, n=temp_root+'Shape'
        )
        # master_hairsys('active', 1)
        for attr, value in hairsystem_attrs.items():
            master_hairsys(attr, value)
        for attr, valuearray in self.HairSystemAttrsArray.items():
            for i, value in enumerate(valuearray):
                master_hairsys('%s[%s]' % (attr, i), value)

        # アトリビュートの表示・非表示の設定。
        for attr in cmds.listAttr(master_hairsys, k=True):
            try:
                cmds.setAttr('{}.{}'.format(master_hairsys, attr), k=False)
            except:
                pass
        for attr in simOption.keys():
            cmds.setAttr(master_hairsys/attr, k=True)
        'time1.o' >> master_hairsys.attr('cti')
        # =====================================================================

        temp_cst_grp = node.createNode(
            'transform', n='springSimCst_grp#', p=temp_root
        )
        temp_cst_grp/'message' >> cst_plug

        for parent in hir_list:
            label = parent+'_posProxy#' if parent else 'world_posProxy#'
            parent_proxy = node.createNode(
                'transform', n=label, p=temp_root
            )
            if parent:
                cmds.parentConstraint(parent, parent_proxy)

            for objectlist in hir_list[parent]:
                if len(objectlist) < 2:
                    continue
                # シミュレーション用ジョイントの作成。=========================
                positions = []
                p = parent_proxy
                jointchain = []
                for object in objectlist:
                    joint = node.createNode(
                        'joint', n=object+'SpringSimProxy', p=p
                    )
                    m_plug = joint.addMessageAttr('bakeTarget')
                    object.attr('message') >> m_plug
                    joint.fitTo(object)
                    positions.append(joint.position())
                    cmds.cutKey(object, cl=True)
                    joint.attr('message') >> member_plug()
                    p = joint
                    jointchain.append(joint)
                jointchain[0].freeze()
                # =============================================================

                # カーブの作成。===============================================
                curve = node.asObject(
                    cmds.rename(
                        cmds.curve(d=1, p=positions),
                        jointchain[0]+'SpringSimCrv'
                    )
                )

                start_crv = node.asObject(cmds.duplicate(curve)[0])
                rest_crv = node.asObject(cmds.duplicate(curve)[0])
                parent_proxy.addChild(start_crv, rest_crv, curve)
                curve.freeze()
                curve.reset()
                # =============================================================

                # hairSystemの作成。===========================================
                hairsys = node.createNode('hairSystem', p=parent_proxy)
                master_hairsys.attr('cti') >> hairsys.attr('cti')

                for attr in hairsystem_attrs:
                    master_hairsys/attr >> hairsys.attr(attr)
                for attr, valuearray in self.HairSystemAttrsArray.items():
                    for i, value in enumerate(valuearray):
                        (
                            master_hairsys.attr('%s[%s]' % (attr, i))
                            >> hairsys.attr('%s[%s]' % (attr, i))
                        )
                # =============================================================

                # follicleの作成。=============================================
                fol = node.createNode('follicle', p=parent_proxy)
                for attr, value in self.FollicleAttrs.items():
                    fol(attr, value)
                for attr, valuearray in self.FollicleAttrsArray.items():
                    for i, value in enumerate(valuearray):
                        fol('%s[%s]' % (attr, i), value)
                for attr in cmds.listAttr(fol, k=True):
                    try:
                        cmds.setAttr('{}.{}'.format(fol, attr), k=False)
                    except:
                        pass
                fol.attr('oha') >> hairsys.attr('ih[0]')
                hairsys.attr('oh[0]') >> fol.attr('crp')
                start_crv.attr('worldSpace[0]') >> fol.attr('startPosition')
                rest_crv.attr('worldSpace[0]') >> fol.attr('restPosition')
                # =============================================================

                # 出力結果のカーブのセットアップ。=============================
                tg = node.createNode('transformGeometry')
                tg('invertTransform', 1)
                fol.attr('outCurve') >> tg.attr('inputGeometry')
                parent_proxy.attr('matrix') >> tg.attr('transform')
                tg.attr('outputGeometry') >> curve.attr('create')
                # =============================================================

                # IKの作成、及び設定。=========================================
                ik = node.ikHandle(
                    sj=jointchain[0], ee=jointchain[-1], sol='ikSplineSolver',
                    createCurve=False, curve=curve(), parentCurve=False
                )[0]
                parent_proxy.addChild(ik)
                # =============================================================

        for joint in temp_root.bakedJoints():
            target = joint.attr('bakeTarget').source()
            cst = cmds.parentConstraint(joint, target, mo=False)
            temp_cst_grp.addChild(*cst)

        return temp_root

    def determineRootNode(self, rootNode):
        r"""
            引数で与えれたノードがSpringSimulatorRootかどうかをチェックする。
            SpringSimulatorRoot:の場合はそのクラスのインスタンスに変換して返す。
            
            Args:
                rootNode (str):
                
            Returns:
                SpringSimulatorRoot:
        """
        rootNode = SpringSimulatorRoot(str(rootNode))
        if (
            not rootNode
            or not rootNode.hasAttr('bakedJoints')
            or not rootNode.hasAttr('constraintGroup')
        ):
            raise ValueError(
                'The given root "%s" is not spring simulation root.' % rootNode
            )
        return rootNode

    def bake(self, roots=None, start=None, end=None):
        r"""
            シミューレーションのターゲットをベイクする。
            
            Args:
                roots (list):SpringSimulatorRootのリスト
                start (float):シミューレーション開始フレーム
                end (float):シミューレーション終了フレーム
        """
        cur_time = cmds.currentTime(q=True)
        if not start:
            start = cmds.playbackOptions(q=True, min=True)
        if not end:
            end = cmds.playbackOptions(q=True, max=True)

        if not roots:
            roots = cmds.ls(sl=True)
        rootlist = [self.determineRootNode(x) for x in roots]

        baked_nodes = []
        for root in rootlist:
            root('startFrame', start)
            for joint in root.bakedJoints():
                target = joint.attr('bakeTarget').source()
                if target:
                    baked_nodes.append(target)

        cmds.cutKey(baked_nodes, cl=True)
        cmds.bakeResults(
            baked_nodes,
            simulation=True, time=(start, end),
            sampleBy=1, disableImplicitControl=True,
            preserveOutsideKeys=True,
            sparseAnimCurveBake=False,
            removeBakedAttributeFromLayer=False,
            bakeOnOverrideLayer=False,
            attribute=['tx', 'ty', 'tz', 'rx', 'ry', 'rz']
        )
        cmds.currentTime(cur_time)
        
        for root in rootlist:
            root.delete()

    def hideObjects(self):
        r"""
            ビュートでオブジェクトの表示を全て非表示にする。
            
            Returns:
                any:
        """
        try:
            view = OpenMayaUI.M3dView.active3dView()
            premask = view.objectDisplay()
            view.setObjectDisplay(0)
            dcmd = premask
        except:
            dcmd = None
        self.__displayflags = (view, premask)
        return True

    def restoreHiddenObject(self):
        r"""
            hideObjects実行前の状態に戻す。
            
            Returns:
                any:
        """
        if not self.__displayflags:
            return
        self.__displayflags[0].setObjectDisplay(self.__displayflags[1])
        self.__displayflags = None

    def simulate(self):
        r"""
            シミューレーションをセットアップからベイクまで一通り実行
            
            Returns:
                any:
                
            Brief:
                する場合に使用するメソッド。
        """
        temp_root = self.createSimulatedSystem()
        self.bake(temp_root)
        temp_root.delete()

    def restoreSelection(self):
        r"""
            setup実行前のオブジェクトの選択を復元する。
            
            Returns:
                any:
        """
        if self.__pre_selections:
            cmds.select(
                [x for x in self.__pre_selections if cmds.objExists(x)],
                ne=True
            )

class NSpringSimulator(SpringSimulator):
    NucleusAttrs = {
        'spaceScale' : 0.01,
        'gravity': 9.8,
        'subSteps': 8,
    }
    def createSimulatedSystem(self, simOption=None):
        r"""
            シミューレーション用のノードを作成する。
            simOptionはここで作成されるhairSystemに渡すアトリビュートの
            辞書オブジェクト。
            辞書のキーはhairSystemのアトリビュート名、値は設定したい
            値を入れておく。
            
            Args:
                simOption (dict):hairSystemに渡すオプション
                
            Returns:
                SpringSimulatorRoot:シミュレーション用ノードをまとめるグループ
        """
        hir_list = self.hierarchyList()
        if not hir_list:
            raise RuntimeError(
                'Simulated nodes were not detected.'
                '(Execute setup method before simulating.)'
            )
        # ルートノードの作成。=================================================
        temp_root = SpringSimulatorRoot(
            node.createNode('curveVarGroup', n='simulated_grp').name()
        )
        baked_member_plug, member_plug, cst_plug = temp_root.initialize()
        # =====================================================================

        hairsystem_attrs = {x:y for x, y in self.HairSystemAttrs.items()}
        hairsystem_attrs['startFrame'] = cmds.playbackOptions(q=True, min=True)
        if isinstance(simOption, dict):
            hairsystem_attrs.update(simOption)

        # マスターのhairSystemのセットアップ。=================================
        master_hairsys = node.createNode(
            'hairSystem', p=temp_root, n=temp_root+'Shape'
        )
        for attr, value in hairsystem_attrs.items():
            master_hairsys(attr, value)
        for attr, valuearray in self.HairSystemAttrsArray.items():
            for i, value in enumerate(valuearray):
                master_hairsys('%s[%s]' % (attr, i), value)

        # アトリビュートの表示・非表示の設定。
        for attr in cmds.listAttr(master_hairsys, k=True):
            try:
                cmds.setAttr('{}.{}'.format(master_hairsys, attr), k=False)
            except:
                pass
        for attr in simOption.keys():
            cmds.setAttr(master_hairsys/attr, k=True)
        'time1.o' >> master_hairsys.attr('cti')
        # =====================================================================

        # nucleusの作成。======================================================
        ncl = node.Transform(
            node.createNode('nucleus', n='hairN_ge', p=temp_root)
        )
        'time1.o' >> ncl.attr('currentTime')
        for attr, value in self.NucleusAttrs.items():
            ncl(attr, value)
        n_index = 0

        # nucleusとの接続。
        master_hairsys('active', 1)
        ncl.attr('noao[0]') >> master_hairsys/'nxst'
        master_hairsys.attr('stf') >> ncl/'stf'
        master_hairsys.attr('cust') >> ncl/'niao[0]'
        master_hairsys.attr('stst') >> ncl/'nias[0]'
        # =====================================================================

        temp_cst_grp = node.createNode(
            'transform', n='springSimCst_grp#', p=temp_root
        )
        temp_cst_grp/'message' >> cst_plug

        for hindex, parent in enumerate(hir_list):
            label = parent+'_posProxy#' if parent else 'world_posProxy#'
            parent_proxy = node.createNode(
                'transform', n=label, p=temp_root
            )
            if parent:
                cmds.parentConstraint(parent, parent_proxy)

            for objectlist in hir_list[parent]:
                if len(objectlist) < 2:
                    continue
                # シミュレーション用ジョイントの作成。=========================
                positions = []
                p = temp_root
                jointchain = []
                for object in objectlist:
                    joint = node.createNode(
                        'joint', n=object+'SpringSimProxy', p=p
                    )
                    m_plug = joint.addMessageAttr('bakeTarget')
                    object.attr('message') >> m_plug
                    joint.fitTo(object)
                    positions.append(joint.position())
                    cmds.cutKey(object, cl=True)
                    joint.attr('message') >> member_plug()
                    p = joint
                    jointchain.append(joint)
                jointchain[0].freeze()
                # =============================================================

                # カーブの作成。===============================================
                curve = node.asObject(
                    cmds.rename(
                        cmds.curve(d=1, p=positions),
                        jointchain[0]+'SpringSimCrv'
                    )
                )

                start_crv = node.asObject(cmds.duplicate(curve)[0])
                rest_crv = node.asObject(cmds.duplicate(curve)[0])
                parent_proxy.addChild(start_crv, rest_crv, curve)
                curve.freeze()
                curve.reset()
                # =============================================================

                # follicleの作成。=============================================
                fol = node.createNode('follicle', p=parent_proxy)
                for attr, value in self.FollicleAttrs.items():
                    fol(attr, value)
                for attr, valuearray in self.FollicleAttrsArray.items():
                    for i, value in enumerate(valuearray):
                        fol('{}[{}]'.format(attr, i), value)
                for attr in cmds.listAttr(fol, k=True):
                    try:
                        cmds.setAttr('{}.{}'.format(fol, attr), k=False)
                    except:
                        pass
                fol.attr('oha') >> '{}.ih[{}]'.format(master_hairsys, hindex)
                '{}.oh[{}]'.format(master_hairsys, hindex) >> fol.attr('crp')
                (
                    start_crv.attr('worldMatrix[0]')
                    >> fol.attr('startPositionMatrix')
                )
                start_crv.attr('local') >> fol.attr('startPosition')
                rest_crv.attr('local') >> fol.attr('restPosition')
                # =============================================================

                # 出力結果のカーブのセットアップ。=============================
                tg = node.createNode('transformGeometry')
                tg('invertTransform', 1)
                fol.attr('outCurve') >> tg.attr('inputGeometry')
                parent_proxy.attr('matrix') >> tg.attr('transform')
                tg.attr('outputGeometry') >> curve.attr('create')
                # =============================================================

                # IKの作成、及び設定。=========================================
                ik = node.ikHandle(
                    sj=jointchain[0], ee=jointchain[-1], sol='ikSplineSolver',
                    createCurve=False, curve=curve(), parentCurve=False
                )[0]
                parent_proxy.addChild(ik)
                # ツイスト制御案（うまくいっていない気もするのでコメントアウト）
                # ik('dWorldUpType', 1)
                # ik('dTwistControlEnable', 1)
                # ik('dWorldUpAxis', 3)
                # mltmtx = node.createNode('multMatrix')
                # mtx = node.identityMatrix()
                # mtx[14] = 1
                # mltmtx('matrixIn[0]', mtx, type='matrix')
                # parent_proxy.attr('wm') >> mltmtx/'matrixIn[1]'
                # mltmtx.attr('matrixSum') >> ik/'dWorldUpMatrix'
                # =============================================================

        for joint in temp_root.bakedJoints():
            target = joint.attr('bakeTarget').source()
            cst = cmds.parentConstraint(joint, target, mo=False)
            temp_cst_grp.addChild(*cst)

        return temp_root