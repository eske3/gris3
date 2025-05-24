#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Constructorに拡張機能を追加するExtraConstructor。
    funcと違い、リグの仕様に関わる拡張機能が追加される。
    
    Dates:
        date:2021/08/04 20:05 eske yoshinob[eske3g@gmail.com]
        update:2021/10/09 03:51 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2021 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import extraConstructor, node, func
cmds = node.cmds

class ExtraConstructor(extraConstructor.ExtraConstructor):
    DefaultPositionDataA = {
        'L':(0, (0.269, 0.438, 0.895)),
        'R':(180, (0.957, 0.387, 0.693)),
    }
    def _preProcess(self):
        cst = self.constructor()
        cst.alignJointOnSurface = self.alignJointOnSurface

    def alignJointOnSurface(
        self, joints, surfaceName, ctrlRoot, setupRoot,
        basename, blendAttrName, globalBlendAttr,
        sc, scModifier=None
    ):
        r"""
            任意のNurbsSurfaceにジョイントチェーンを追従させる機能を提供する。
            
            Args:
                joints (list):
                surfaceName (str):追従させるNurbsSurface名
                ctrlRoot (node.Transform):コントローラを格納するグループ
                setupRoot (node.Transform):セットアップデータを格納するグループ
                basename (str):生成されるノードのベース名
                blendAttrName (str):個別コントローラの追従率変更アトリビュート名
                globalBlendAttr (str):全体追従率制御のノードのアトリビュート名
                sc (ShapeCreator):
                scModifier (dict):
        """
        constructor = self.constructor()
        surface = node.asObject(surfaceName)
        fitter = func.SurfaceFitter(surface)
        ctrls = []
        if not scModifier:
            scModifier = self.DefaultPositionDataA
        if '.' not in globalBlendAttr:
            raise ValueError(
                '"globalBlendAttr" must be specified a "nodeName.attrName".'
            )
        global_ctrl, attr_name = globalBlendAttr.split('.', 1)
        global_ctrl = node.asObject(global_ctrl)
        if global_ctrl.hasAttr(attr_name):
            f_plug = global_ctrl.attr(attr_name)
        else:
            f_plug = global_ctrl.addFloatAttr(
                attr_name, default=1, min=0, max=1
            )

        # Z軸を表す行列を作成。
        z_mtx = node.identityMatrix()
        z_mtx[12:15] = [0, 0, 1]
        z_mtx = node.MMatrix(z_mtx)

        def createProxyAndFitSrf(jnt, parent):
            r"""
                Args:
                    jnt (any):
                    parent (any):
            """
            proxy = func.copyNode(jnt, 'jntProxy', parent)
            return fitter.fit(proxy)[0]

        def createCtrlAndFit(
            jnt, parent, setup_parent, fitted=None, parentInverseMatrix=None
        ):
            r"""
                Args:
                    jnt (node.Transform):対象ジョイントのトップ
                    parent (node.Transform):コントローラの親
                    setup_parent (node.Transform):セットアップ用ノードの親
                    fitted (list):コントローラを追従させるノードとその親ノード
                    parentInverseMatrix (str or None):コントローラの親の逆行列
            """
            name = func.Name(jnt)
            nt = name.convertType
            
            # さーフェイースにはりつくジョイントの作成。=======================
            if not fitted:
                proxy, spacer = createProxyAndFitSrf(jnt, setup_parent)
            else:
                proxy, spacer = fitted
            ctrllist = []
            if not jnt.hasChild():
                return ctrllist
            children = jnt.children(type='joint')
            child_fitted = createProxyAndFitSrf(children[0], setup_parent)
            fitted_children = [None for x in children]
            fitted_children[0] = child_fitted

            # up軸を確定させる。-----------------------------------------------
            mtx = proxy.matrix()
            # normal = node.MVector(spacer.matrix()[8:11]).normal()
            # dot_list = []
            # for i in range(3):
                # v = node.MVector(mtx[i*4:i*4+3]).normal()
                # dot_list.append(v * normal)
            # up_axis = [0, 0, 0]
            # abs_dot_list = [abs(x) for x in dot_list]

            tgt_mtx = z_mtx * node.MMatrix(spacer.matrix())
            p_matrix = node.MMatrix(mtx)
            up_axis = list(
                node.MVector(
                    list(tgt_mtx * p_matrix.inverse())[12:15]
                ).normal()
            )
            # -----------------------------------------------------------------

            cmpmtx = node.createUtil('composeMatrix', n=nt('upCmpmtx')())
            spacer.attr('r') >> cmpmtx/'ir'
            pmm = node.createUtil('pointMatrixMult', n=nt('upPmm')())
            cmpmtx.attr('outputMatrix') >> pmm/'inMatrix'
            pmm('ip', (0, 0, 1))
            
            cst = node.createUtil(
                'aimConstraint', n=nt('aimCst')(), p=spacer
            )
            cst('aimVector', (-1 if jnt.isOpposite() else 1, 0, 0))
            cst('upVector', up_axis)
            cst('worldUpType', 3)
            proxy.attr('t') >> cst/'ct'
            proxy.attr('rp') >> cst/'crp'
            proxy.attr('rpt') >> cst/'crt'
            proxy.attr('jo') >> cst/'cjo'
            proxy.attr('ro') >> cst/'cro'
            spacer.attr('im') >> cst/'cpim'
            child_fitted[0].attr('t') >> cst/'tg[0].tt'
            child_fitted[-1].attr('m') >> cst/'tg[0].tpm'
            pmm.attr('o') >> cst/'worldUpVector'
            ~cst.attr('cr') >> ~proxy.attr('r')
            # =================================================================
            
            # コントローラの作成。=============================================
            data = scModifier.get(
                name.position(), self.DefaultPositionDataA['L']
            )
            sc.setRotation((data[0], 0.0, 0.0))
            sc.setColorIndex(data[1])
            constructor.toController(jnt, basename)
            ctrls = constructor.connectController(jnt, parent, sc)
            p = ctrls[0].addFloatAttr(blendAttrName, default=1, min=0, max=1)
            mdl = node.createUtil('multDoubleLinear')
            p >> mdl/'input1'
            f_plug >> mdl/'input2'
            ctrllist.append(ctrls)
            
            cst = func.localConstraint(
                cmds.parentConstraint, proxy, ctrls[-1],
                parents=[[spacer/'matrix']]
            )
            pim_mltmtx = node.createUtil('multMatrix')
            if parentInverseMatrix:
                parentInverseMatrix >> [cst/'cpim', pim_mltmtx/'matrixIn[0]']
            else:
                pim_mltmtx('matrixIn[0]', cst('cpim'), type='matrix')
            ctrls[1].attr('im') >> pim_mltmtx/'matrixIn[1]'
            pim_mltmtx('matrixIn[2]', ctrls[0]('im'), type='matrix')
            pim_plug = pim_mltmtx.attr('matrixSum')
            func.blendSelfConnection(
                ctrls[-1], mdl/'output', skipScale=True,
                blendMode=1,
            )
            # =================================================================

            for child, f in zip(children, fitted_children):
                ctrllist.extend(
                    createCtrlAndFit(
                        child, ctrls[0], setup_parent, f, pim_plug
                    )
                )
            return ctrllist

        for jnt in node.toObjects(joints):
            ctrllist = createCtrlAndFit(jnt, ctrlRoot, setupRoot)
            ctrls.append(ctrllist)
        return ctrls
