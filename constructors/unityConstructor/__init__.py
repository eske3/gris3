# -*- coding: utf-8 -*-
r'''
    @file     __init__.py
    @brief    UNITY用アセットのコンストラクタ
    @class    Constructor : ここに説明文を記入
    @date        2017/01/22 0:11[Eske](eske3g@gmail.com)
    @update      2017/02/14 5:53[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
from gris3 import constructors, grisNode, node, system, func
cmds = func.cmds

class UnityOutputNameRule(system.BasicNameRule):
    def elements(self):
        if self.positionIndex() == 0:
            return [self.name()]
        else:
            return [self.name(), self.position()]

class Constructor(constructors.BasicConstructor):
    r'''
        @brief       ここに説明文を記入
        @inheritance constructors.BasicConstructor
        @date        2017/02/14 5:41[Eske](eske3g@gmail.com)
        @update      2017/02/14 5:53[Eske](eske3g@gmail.com)
    '''
    FactoryModules = (
        constructors.ModuleInfo('jointBuilder', None, None),
        constructors.ModuleInfo('cageManager', None, None),
        constructors.ModuleInfo('drivenManager', None, None),
        constructors.ModuleInfo('weightManager', None, None),
        constructors.ModuleInfo('extraJointManager', None, None),
        constructors.ModuleInfo('controllerExporter', None, None),
    )
    ScaledJointList = []
    def setupModelGroup(self):
        r'''
            @brief  レンダーモデルのセットアップ。
            @return None
        '''
        all_grp = grisNode.ModelAllGroup(self.ModelGroupName)
        all_grp.rename('model_grp')
        self.addInitialTopNode(all_grp)
        self.setModelGroup(all_grp())

        # all_grpをカレントのLODのDisplayセットとして登録する。================
        lod_dsp_set = self.lodDisplaySet()
        lod_dsp_set.addChild(all_grp())
        self.connectDisplayCtrlToSet()
        # =====================================================================

        self.modelGroup()/'message' >> self.root().attr('modelGroup')

    def setupSystem(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        super(Constructor, self).setupSystem()
        name_cls = system.GlobalSys().nameRule()
        root = grisNode.getGrisRoot()
        jnt_grp = root.baseJointGroup()
        world_trs = jnt_grp.worldTransform()

        # Constraintノード集約用グループを作成する。===========================
        cst_grp = node.createNode('transform', n='refCst_grp', p=root)
        cst_grp.lockTransform(True)
        # =====================================================================

        # rootに拡張グループを登録するアトリビュートを追加する。===============
        output_attr = root.addMessageAttr('outputGroup')
        model_attr = root.addMessageAttr('modelGroup')
        # =====================================================================

        # ベイク用ジョイントをまとめるセット。=================================
        outjoint_set = node.asObject(
            cmds.sets(
                n='bakedJoint_set', text='bakedJointSet', em=True
            )
        )
        self.root().allSet().addChild(outjoint_set)
        # =====================================================================

        hidden_attr = ('v', 'radius')
        # ローカル関数セット。+++++++++++++++++++++++++++++++++++++++++++++++++
        def copy(src, parent):
            copied = node.createNode('joint', p=parent())
            copied.editAttr(hidden_attr, k=False, l=False)
            copied.fitTo(src)
            copied('ssc', 0)
            copied.setRadius(src('radius'))
            copied.freeze(t=False, s=False)
            bs_attr = copied.addMessageAttr('baseSkeleton')
            src.attr('message') >> bs_attr
            outjoint_set.addChild(copied)
            copied.rename(UnityOutputNameRule(name_cls(src))())
            return copied
        
        def const(src, tgt, withScale=False):
            r'''
                @brief  srcからtgtへコンストレインをかける。
                @param  src : [node.Transform]
                @param  tgt : [node.Transform]
                @return None
            '''
            cst = cmds.parentConstraint(src(), tgt())
            if withScale:
                ~src.attr('s') >> ~tgt.attr('s')
            try:
                cst_grp.addChild(cst[0])
            except Exception as e:
                print('=' * 80)
                print('{} => {}'.format(src(), tgt()))
                print('{}'.format(cst))
                print('=' * 80)
                raise e

        def copyAndCst(src, dst, withScale=False):
            r'''
                @brief  srcをdstへコピーし、コンストレインをかける。
                @brief  srcに子がいなければ処理は終わる。
                @brief  （末端ジョイントは行わない）
                @brief  子階層まで再帰的に実行する。
                @param  src : [node.Transform]
                @param  dst : [node.Transform]
                @return None
            '''
            const(src, dst, withScale)
            for joint in src.children(type='transform'):
                joint_type = joint.type()
                if joint_type == 'transform':
                    imp = joint.children(type='implicitSphere')
                    if not imp:
                        continue
                    for j in joint.children(type='joint'):
                        copied = copy(j, dst)
                        copyAndCst(j, copied, True)
                    continue
                elif joint_type == 'joint':
                    if not joint.hasChild():
                        continue
                else:
                    continue
                copied = copy(joint, dst)
                copyAndCst(joint, copied, joint in self.ScaledJointList)
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        # Referenceロケータの作製。============================================
        ref_trs = node.createNode('transform', n='Reference')
        ref_shape = node.createNode('locator', p=ref_trs, n=ref_trs+'Shape')
        self.addInitialTopNode(ref_trs)
        ref_trs/'message' >> output_attr
        # =====================================================================
    
        copyAndCst(world_trs, ref_trs)
        disp_attr = jnt_grp.addDisplayAttr(default=False)
        disp_attr >> jnt_grp/'v'

        # ベイク用ジョイントのDisplayセットを追加。============================
        disp_ctrl = self.root().ctrlGroup().displayCtrl()
        disp_attr = disp_ctrl.addEnumAttr(
            'outJointDisplay', ('Normal', 'Template', 'Reference'),
            default=1, cb=True
        )

        outjoint_set = self.allDisplaySet().addSet('outputJoint')
        outjoint_set.addChild(ref_trs)
        disp_attr >> outjoint_set/'displayType'
        # =====================================================================

