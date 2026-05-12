#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    フェイシャル構成をレイヤー化するための機能を提供するモジュール。
    
    Dates:
        date:2017/02/25 13:10[Eske](eske3g@gmail.com)
        update:2025/06/01 22:27 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from ... import node, func
cmds = node.cmds


ColorData = {
    'L': (0.044, 0.011, 0.88),
    'R': (0.973, 0.02, 0.115),
    'C': (0.7, 0.873, 0.207),
}


class LayerOperator(object):
    r"""
        フェイシャルの構造をレイヤー化するための機能を提供するためのクラス。
        このクラスを継承したサブクラスを用いてフェイシャルの機能ごとにレイヤ化
        する。
    """
    def __init__(self, constructor, extCst, animSet, root_group):
        r"""
            Args:
                constructor (constructors.BasicConstructor):
                extCst (basicfacialSystem.core.ExtraConstructor):
                animSet (grisNode.AnimSet):
                root_group (node.Transform):
        """
        self.__constructor = constructor
        self.__extCst = extCst
        self.__anim_set = animSet
        self.__root_grp = root_group
        self.__ctrl_parent = None
        self.__hidden_ctrls = []

    def out(self, text, isPrint=True):
        r"""
            メッセージ出力用。メッセージにサフィックスを追加する
            
            Args:
                text (str):元メッセージ
                isPrint (bool):メッセージをprintするかどうか
                
            Returns:
                str:サフィックスのついたメッセージ
        """
        message = '[FacialSetup : {}] {}'.format(self.prefix(), text)
        if isPrint:
            print(message)
        return message

    def constructor(self):
        r"""
            インストール先のコンストラクタを返す。
            
            Returns:
                constructors.BasicConstructor:
        """
        return self.__constructor

    def extraConstructor(self):
        r"""
            レイヤを登録しているエクストラコンストラクタを返す。
            
            Returns:
                basicfacialSystem.core.ExtraConstructor:
        """
        return self.__extCst

    def animSet(self):
        r"""
            フェイシャルのセットを返す。
            
            Returns:
                grisNode.AnimSet:
        """
        return self.__anim_set

    def setTargetObjects(self, target):
        r"""
            操作対象となるコピーされたフェイシャルメッシュを設定する。
            
            Args:
                target (node.Transform):
        """
        self.__target = target

    def targetObjects(self):
        r"""
            操作対象となるコピーされたフェイシャルメッシュのリストを返す。
            
            Returns:
                node.Transform:
        """
        return self.__target
    
    def setRootGroup(self, rootGrp):
        r"""
            このフェイシャルをまとめるためのグループノードを設定する。
            
            Args:
                rootGrp (node.Transform):
        """
        self.__root_grp = rootGrp

    def rootGroup(self):
        r"""
            このフェイシャルをまとめるためのグループノードを返す。
            
            Returns:
                node.Transform:
        """
        return self.__root_grp

    def setCtrlParent(self, ctrl):
        r"""
            Args:
                ctrl (str):
        """
        self.__ctrl_parent = ctrl

    def ctrlParent(self):
        r"""
            Returns:
                node.Transform:
        """
        return node.asObject(self.__ctrl_parent)

    def prefix(self):
        r"""
            カテゴリを表すプレフィックス用文字列。
            サブクラスは必ずオーバーライドし、空文字列以外を返す必要がある。
            
            Returns:
                str:
        """
        return ''

    def preSetup(self):
        r"""
            レイヤー用のフェイシャルジオメトリの設定が完了した後に呼び出される。
            上書き専用メソッド。
        """
        pass

    def postPreSetup(self):
        r"""
            ConstructorのpreSetup完了後に呼ばれる上書き専用メソッド。
        """
        pass

    def setup(self):
        pass

    def addHiddenCtrl(self, *ctrls):
        r"""
            Args:
                *ctrls (any):
        """
        self.__hidden_ctrls.extend(ctrls)

    def hiddenCtrls(self):
        return self.__hidden_ctrls

    def postProcess(self):
        pass

    def createSetupParts(self, parentGrp):
        r"""
            このレイヤーを動作さえる上で必要なノードを作成するUtilityメソッド。
            このメソッドの目的は、リグに必要な要素を作成することなので、
            constructorやextraConstructor、animSetなどリグに必要となるメソッドは
            すべてNoneを返す。
            そのため基本的には引数parentGrpの情報以外は使用できない。
            
            Args:
                parentGrp (node.Transform):
        """
        pass


class LayerManager(object):
    r"""
        レイヤー管理を行うための機能を提供するクラス。
    """
    DefaultCageGroup = 'faceCage_grp'
    BaseGroupName = 'FacialSetup_grp'

    def __init__(self, constructor, extraConstrcutor, *layerOperators):
        r"""
            Args:
                constructor (constructors.BasicConstructor):
                extraConstrcutor (basicfacialSystem.core.ExtraConstructor):
                *layerOperators (LayerOperator):
        """
        super(LayerManager, self).__init__()
        self.__constructor = constructor
        self.__extCst = extraConstrcutor
        self.__layers = list(layerOperators)
        self.__process_objects = []

    def clearLayers(self):
        r"""
            追加済みのレイヤーすべてを削除する。
        """
        self.__layers = []

    def addLayers(self, *layerOperators):
        r"""
            処理するためのレイヤーを追加する。
            
            Args:
                *layerOperators (LayerOperator):
        """
        self.__layers.extend(layerOperators)

    def removeLayers(self, *layerOperators):
        r"""
            追加済みのレイヤーを削除する。
            
            Args:
                *layerOperators (LayerOperator):
        """
        for l in layerOperators:
            if l not in self.__layers:
                continue
            idx = self.__layers.index(l)
            del self.__layers[idx]

    def layers(self):
        r"""
            追加済みのレイヤー一覧を返す。
            
            Returns:
                list (LayerOperator):
        """
        return self.__layers

    def createSetupParts(self, rootGroup):
        r"""
            layerOperatorごとに必要なノード郡を作成するための便利メソッド。
            
            Args:
                rootGroup (node.Transform):
        """
        for l in self.layers():
            l(self.__constructor, self.__extCst, None, None).createSetupParts(
                rootGroup
            )

    def processObjects(self):
        r"""
            setupによって事前処理を行った、登録済みlayerオブジェクトの一覧を
            返す。
            
            Returns:
                list (LayerOperator):
        """
        return self.__process_objects

    def copyFacialGroup(self, facialGrp, rootGrp, prefix, facialGeos):
        r"""
            フェイシャルグループを複製する。
            フェイシャルグループはブレンドシェイプなどで変形させる顔ジオメトリを
            まとめたグループを指す。
            
            Args:
                facialGrp (node.Transform):複製するフェイシャルグループ
                rootGrp (node.Transform):複製後の親
                prefix (str):名前につけるプレフィックス
                facialGeos (list):
                
            Returns:
                list:
        """
        def copyNode(target, prefix, parent):
            r"""
                再帰的にノード構造をコピーする。
                
                Args:
                    target (node.Transform):コピー対象ノード
                    prefix (str):ノードタイプにつけるプレフィックス
                    parent (node.Transform):コピー先の親ノード
                    
                Returns:
                    list:コピーされたノード名
            """
            if target.shapes():
                pfx = prefix+'Mesh' if prefix else 'cage'
                if not target in facialGeos:
                    facialGeos.append(target)
                return [func.copyMeshNode(target, pfx, parent)]
            pfx = prefix+'Grp' if prefix else 'cageGrp'
            grp = func.copyNode(target, pfx, parent)
            result = []
            for child in target.children():
                result.extend(copyNode(child, prefix, grp))
            return result

        grpname = (
            prefix + self.BaseGroupName if prefix else self.DefaultCageGroup
        )
        r = [node.createNode('transform', n=grpname, p=rootGrp)]
        if prefix:
            r.append(
                node.createNode('transform', n=prefix+'FacialMesh_grp', p=r[0])
            )
        else:
            r.append(r[0])
        
        for child in facialGrp.children():
            r.extend(copyNode(child, prefix, r[1]))
        return r

    def setup(
        self,
        facialGrp, rootGroup, cageGroup, ctrlParent, animSet,
        layerInitializer=None
        
    ):
        r"""
            facialGrpに対し、登録されたlayerOperator毎に複製を作成する。
            また、その際各layerOperatorのインスタンスを作成し後の処理のために
            保持する処理も行う。
            
            引数layerInitializerは関数オブジェクトを受け取る。
            この関数は各layerOperatorインスタン時に呼ばれ、layerOperatorの
            インスタンスに対して初期化処理を加えたい場合に用いる。

            Args:
                facialGrp (node.Transform):コピー元となる顔メッシュのグループ
                rootGroup (node.Transform):フェイシャルをまとめるためのグループ
                cageGroup (node.Transform):ケージを格納するためのグループ
                ctrlParent (node.Transform):コントローラの親となるノード
                animSet (grisNode.AnimSet): コントローラを登録するanimSet
                layerInitializer (function): layerOperatorインスタンス編集用関数
        """
        copied_list = []
        self.__process_objects = []
        pre_copied = None
        layers = self.layers()
        layers.append('skinned')
        str_type = type('')
        parentlist = [rootGroup for x in layers]
        parentlist[-1] = cageGroup
        facial_targets = []
        for l_operator, parent in zip(layers, parentlist):
            if isinstance(l_operator, str_type):
                pfx = None
                lo_obj = None
            else:
                lo_obj = l_operator(
                    self.__constructor, self.__extCst, animSet, rootGroup
                )
                if layerInitializer:
                    layerInitializer(lo_obj)
                lo_obj.setCtrlParent(ctrlParent)
                self.__process_objects.append(lo_obj)
                pfx = lo_obj.prefix()
            copied = self.copyFacialGroup(
                facialGrp, parent, pfx, facial_targets
            )
            if lo_obj:
                lo_obj.setTargetObjects(copied[1:])
                lo_obj.setRootGroup(copied[0])
            copied_list.append(copied)
            if not pre_copied:
                pre_copied = copied
                continue
            for s, d in zip(pre_copied[2:], copied[2:]):
                s.attr('outMesh') >> d.attr('inMesh')
            pre_copied = copied
        return facial_targets, copied_list

    def preSetupLayers(self):
        r"""
            登録済みレイヤーのpreSetupを呼び出す。
        """
        for lo_obj in self.processObjects():
            lo_obj.preSetup()

    def postPreSetupLayers(self):
        r"""
            登録済みレイヤーのpostPreSetupを呼び出す。
        """
        for lo_obj in self.processObjects():
            lo_obj.postPreSetup()

    def setupLayers(self):
        r"""
            登録済みレイヤーのpreSetupを呼び出す。
        """
        for lo_obj in self.processObjects():
            lo_obj.setup()

    def postProcessLayers(self):
        r"""
            登録済みレイヤーのポストプロセスを呼び出す。
        """
        for lo_obj in self.processObjects():
            lo_obj.postProcess()

    def connectVisibility(self, visibl_plug):
        r"""
            各レイヤーのコントローラを、表示制御アトリビュートに接続する。
            
            Args:
                visibl_plug (node.Attribute):表示・非表示を制御するアトリビュート
        """
        for lo_obj in self.processObjects():
            for ctrl in [x for x in node.toObjects(lo_obj.hiddenCtrls()) if x]:
                visibl_plug >> ctrl/'v'

