#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Factoryの中核を担うConstructorシステムの機能とモジュールを提供する
    
    Dates:
        date:2017/01/22 0:11[Eske](eske3g@gmail.com)
        update:2022/07/12 12:19 Eske Yoshinob[eske3g@gmail.com]
        
    Brief:
        モジュールセット。
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
import re
from ..factoryModules import ModuleInfo
from ..tools import cleanup
from .. import lib, node, func, core, grisNode, rigScripts, settings, verutil
cmds = func.cmds

# /////////////////////////////////////////////////////////////////////////////
# 定数。                                                                     //
# /////////////////////////////////////////////////////////////////////////////
CurrentFilePattern = '[\._]cur\.[a-z\d]+$'
LOD_LIST = ('low', 'high')
LatestExecutedConstructor = None
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////

def mainModule(moduleName, isReload=False):
    r"""
        moduleNameの親ディレクトリをmainモジュールとしてインポートする
        
        Args:
            moduleName (str):
            isReload (bool):
            
        Returns:
            module:
    """
    import sys
    module = sys.modules[moduleName.split('.', 1)[0]]
    if isReload:
        verutil.reload_module(module)
    return module

# /////////////////////////////////////////////////////////////////////////////
# 各種ノード、スクリプトなどコンストラクタ依存のデータを作成する関数群。     //
# /////////////////////////////////////////////////////////////////////////////
def createRoot():
    r"""
        標準設定のアセット用ルートを作成する。
        Constructor:用モジュールでcreateRoot関数が定義されていない場合、
        この関数が呼ばれる。
        
        Returns:
            GrisRoot:.
    """
    from gris3 import grisNode
    root = grisNode.createNode(grisNode.GrisRoot)
    grisNode.nodeSetup(root)
    return root


def createRootCtrl(root, size=100):
    r"""
        標準設定のルートコントローラを作成する。
        Constructor:用モジュールでcreateRootCtrl関数が定義されていない
        場合、この関数が呼ばれる。
        
        Args:
            root (grisNode.GrisRoot):[]
            size (float):
            
        Returns:
            list:
    """
    creator = func.PrimitiveCreator()
    ctrl_grp = root.ctrlGroup()
    parent = ctrl_grp
    world_trs = root.baseJointGroup().worldTransform()
    name = func.Name()
    name.setNodeType('ctrlSpace')
    controllers = []
    for basename, colorIndex, curveType in zip(
            [
                'layout', 'layout',
                'world', 'worldOffset', 'local', 'localOffset'
            ],
            [
                None, None, 13, 4, 6, 15
            ],
            [
                '', '',
                'omniDirection', 'circleArrow', 'circleArrow', 'circleArrow'
            ]
        ):
        name.setName(basename)
        controller = node.createNode('transform', n=name(), p=parent)
        parent = controller
        controllers.append(controller)
        name.setNodeType('ctrl')
        if not colorIndex:
            continue
        curveType = curveType if curveType else 'circle'
        creator.setColorIndex(colorIndex)
        creator.setSizes([size, size, size])
        creator.create(curveType, controller)
        size *= 0.95

    # 一番上階層のノードをリネームし、各コントローラのチャンネルを操作する。===
    controllers[0].lockTransform()
    func.controlChannels(
        controllers[1:], ['v'], isKeyable=False, isLocked=False
    )
    # =========================================================================

    # ジョイントのルートとなるノードとの接続。=================================
    controllers.reverse()
    mtx_nodes = func.createDecomposeMatrix(
        world_trs, ['%s.matrix' % x for x in controllers]
    )
    name.setName('worldCtrl')
    for n, node_type in zip(mtx_nodes, ('dexMtx', 'mltMtx')):
        name.setNodeType(node_type)
        n.rename(name())
    controllers.reverse()
    disp_attr = controllers[2].addDisplayAttr()
    disp_attr.set(1)
    disp_attr >> world_trs+'.v'
    # =========================================================================

    # animセットを作成する。===================================================
    all_animset = root.allSet().animSet()
    animset = all_animset.addSet('worldCtrl')
    animset.addChild(*controllers[1:])
    # =========================================================================

    # 表示コントローラを作成。=================================================
    name.setName('display')
    name.setNodeType('ctrlSpace')
    disp_ctrlspace = node.createNode('transform', n=name(), p=controllers[-1])

    name.setNodeType('ctrl')
    disp_ctrl = grisNode.createNode(
        grisNode.DisplayCtrl, n=name(), p=disp_ctrlspace
    )
    disp_ctrl('displayType', 2)
    disp_ctrl('jointDisplay', 0)

    # 表示コントローラにシェイプを追加する。
    size *= 0.15
    creator.setColorIndex(23)
    creator.setSize(size)
    shape = creator.create('star', disp_ctrl)
    shape.setRotate(90, 0, 0)
    func.controlChannels(
        [disp_ctrlspace, disp_ctrl], ['t:a', 'r:a', 's:a', 'v'],
        isKeyable=False, isLocked=False
    )
    # =========================================================================
    
    ctrl_grp._setCtrls(controllers[0], controllers[-1], disp_ctrl)
    return controllers


def createConstructionScript(factorySet, module):
    r"""
        標準設定のコンストラクト用スクリプトを作成する。
        
        Args:
            factorySet (factoryModules.FactorySettings):
            module (gris3.constructors.standardConstructor):
            
        Returns:
            list:作成されたスクリプトファイルパスのリスト
    """
    import shutil
    fileptn = re.compile('^scriptTemplate_([a-zA-Z\d]+$|_init__)')
    dirpath = os.path.join(
        factorySet.rootPath(), factorySet.assetPrefix()
    )
    if not os.path.isdir(dirpath):
        os.makedirs(dirpath)

    module_rootdir = os.path.dirname(module.__file__)
    base_rootdir = os.path.dirname(__file__)
    result = []

    for rootdir in (module_rootdir, base_rootdir):
        count = 0
        for file in os.listdir(rootdir):
            r = fileptn.search(file)
            if not r:
                continue
            src = os.path.join(rootdir, file)
            name = r.group(1)
            name = '__init__.py' if name == '_init__' else 'setup_%s.py' % name
            filepath = os.path.join(dirpath, name)
            if os.path.exists(filepath):
                continue

            count += 1
            try:
                shutil.copy(src, filepath)
            except Exception as e:
                print('[Gris Constructor Error] {}'.format(e.args[0]))
            else:
                result.append(filepath)
        if count:
            break
    return result
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////


class ConstructorManager(object):
    r"""
        Consutructorを管理するシングルトンクラス。
    """
    def __new__(cls):
        if hasattr(cls, '__instance__'):
            return cls.__instance__
        obj = super(ConstructorManager, cls).__new__(cls)
        obj.__is_built = False
        cls.__instance__ = obj

        obj.__pathset = {__name__ : os.path.dirname(__file__)}
        return obj

    def __init__(self):
        if self.__is_built:
            return
        self.__is_built = True
        super(ConstructorManager, self).__init__()

        p = settings.GlobalPref()
        for prefix, path in p.listConstructorPrefix():
            self.addRootPath(prefix, path)
        self.reload()

    def __len__(self):
        r"""
            constructorのリストの数を返す。
            
            Returns:
                int:
        """
        return len(self.__constructors)

    def __getitem__(self, key):
        r"""
            引数で与えれた名前のconstructorモジュールを返す。
            
            Args:
                key (str):
                
            Returns:
                module:
        """
        return self.__constructors[key]

    def __contains__(self, item):
        r"""
            引数で与えられた名前のconstructorがあるかどうかを返す。
            
            Args:
                item (str):
                
            Returns:
                bool:
        """
        return item in self.__constructors

    def addRootPath(self, prefix, path):
        r"""
            construtorを検索するパスを追加する。
            
            Args:
                prefix (str):パスを取得する際に使用するキー
                path (str):ディレクトリパス
        """
        self.__pathset[prefix] = path

    def removeRootPath(self, prefix):
        r"""
            追加済みのconstrutor検索パスを削除する。
            
            Args:
                prefix (str):addRootPathで使用したキー
        """
        if not prefix in self.__pathset:
            return
        del self.__pathset[prefix]

    def reload(self):
        r"""
            constructorのリストを更新する。
        """
        self.__constructors = {}
        for prefix, rootpath in self.__pathset.items():
            if not os.path.isdir(rootpath):
                continue
            modules = lib.loadPythonModules(rootpath, prefix, 2)
            for name, mod in modules:
                verutil.reload_module(mod)
                if 'Constructor' in dir(mod):
                    self.__constructors[name.split('.')[-1]] = mod

    def names(self):
        r"""
            constroctorの名前をリストで返す。
            
            Returns:
                list:
        """
        keys = list(self.__constructors.keys())
        keys.sort()
        return keys

    def module(self, key):
        r"""
            引数の名前に該当するモジュールを返す。
            該当するキーが無ければNoneを返す。
            
            Args:
                key (str):
                
            Returns:
                module or None:
        """
        if not key in self:
            return
        return self[key]

    def getConstrucorCmd(self, key, funcName, defaultFunc, isReload=False):
        r"""
            keyで指定された名前のConstructorが持つコマンドなどを検索て、
            該当コマンドを返す。
            
            Args:
                key (str):Constructor名
                funcName (str):関数名
                defaultFunc (function):Constructorに関数がない場合に使用
                isReload (bool):
                
            Returns:
                function:
        """
        if not key in self:
            raise ValueError(
                'The specified name "%s" is not constructor' % key
            )
        module = self.module(key)
        if isReload:
            verutil.reload_module(module)
        if funcName in dir(module):
            return getattr(module, funcName)
        else:
            return defaultFunc

    def getRootCreatorCmd(self, key, isReload=False):
        r"""
            与えられたconstructorが持つアセットのルート作成用のコマンドを返す。
            もし該当Constructorがコマンドを持っていない場合は標準コマンドで
            あるcreateRootを返す。
            
            Args:
                key (str):Constructor名
                isReload (bool):該当Constructorをreloadするかどうか
                
            Returns:
                function:
        """
        return self.getConstrucorCmd(key, 'createRoot', createRoot, isReload)

    def getRootCtrlCreatorCmd(self, key, isReload=False):
        r"""
            与えられたconstructorが持つアセットのルートコントローラ作成用の
            コマンドを返す。
            もし該当Constructorがコマンドを持っていない場合は標準コマンドで
            あるcreateRootCtrlを返す。
            
            Args:
                key (str):Constructor名
                isReload (bool):該当Constructorをreloadするかどうか
                
            Returns:
                function:
        """
        return self.getConstrucorCmd(
            key, 'createRootCtrl', createRootCtrl, isReload
        )

    def getConstructionScriptCmd(self, key, isReload=False):
        r"""
            与えられたconstructorが持つコンストラクト用スクリプト作成用
            コマンドを返す。
            もし該当Constructorがコマンドを持っていない場合は標準コマンドで
            あるcreateConstructionScriptを返す。
            
            Args:
                key (str):Constructor名
                isReload (bool):該当Constructorをreloadするかどうか
                
            Returns:
                function:
        """
        cmd = self.getConstrucorCmd(
            key, 'createConstructionScript', createConstructionScript, isReload
        )
        return (cmd, self.module(key))

    def listLod(self, key, isReload=False):
        r"""
            コンストラクタで取扱うLODをリストで返す
            
            Args:
                key (str):Constructor名
                isReload (bool):該当Constructorをreloadするかどうか
                
            Returns:
                list:
        """
        return self.getConstrucorCmd(key, 'LOD_LIST', LOD_LIST, isReload)

    def getUtilityWidget(self, key, isReload=False):
        r"""
            コンストラクタで使用できる専用のウィジェットを返す。
            
            Args:
                key (str):Constructor名
                isReload (bool):
                
            Returns:
                method:
        """
        classname = 'FactoryUtility'
        if not key in self:
            raise ValueError(
                'The specified name "%s" is not constructor' % key
            )
        module = self.module(key)
        from importlib import import_module
        try:
            widget_module = import_module('.widgets', module.__name__)
        except Exception as e:
            print(e)
            return
        if isReload:
            verutil.reload_module(widget_module)
        if not hasattr(widget_module, classname):
            return
        return getattr(widget_module, classname)


class ExtraConstructorManager(object):
    r"""
        ExtraConstructorを管理するクラス。
    """
    def __init__(self, constructor):
        r"""
            Args:
                constructor (BasicConstructor):
        """
        self.__extraConstructors = []
        self.__constructor = constructor

    def constructor(self):
        r"""
            登録されてたConstructorを返す。
            
            Returns:
                list:
        """
        return self.__constructor

    def extraConstructors(self):
        r"""
            登録されているExtraConstructorを返す。
            
            Returns:
                list:
        """
        return self.__extraConstructors[:]

    def addExtraConstructor(self, constructorClass):
        r"""
            ExtraConstructorを追加する。
            引き数にはextraConstructor.ExtraConstructorクラスを継承した
            タイプオブジェクト
            
            Args:
                constructorClass (type):
                
            Returns:
                extraConstructor.ExtraConstructor:追加されたインスタンス
        """
        ext_cst = constructorClass(self.constructor())
        self.__extraConstructors.append(ext_cst)
        return ext_cst

    def installExtraConstructor(
        self, constructorName,  prefix='gris3.extraConstructor'
    ):
        r"""
            ExtraConstructorをインストールする。
            
            Args:
                constructorName (str):ExtraConstructor名
                prefix (str):: モジュールのプレフィックス
                
            Returns:
                extraConstructor.ExtraConstructor:
        """
        module = '.'.join((prefix, constructorName))
        mod = lib.importModule(module, True)
        if not mod:
            return
        verutil.reload_module(mod)
        return self.addExtraConstructor(mod.ExtraConstructor)

    def createSetupParts(self):
        for cst in self.extraConstructors():
            cst.createSetupParts()

    def extraConstructorUtilities(self):
        r"""
            ExstraConstructorの作成補助用GUIをリストする。
            戻り値はui作成用のクラス。
            
            Returns:
                list:
        """
        results = []
        for cst in self.extraConstructors():
            ui_class = cst.setupUtil()
            if not ui_class:
                continue
            results.append(ui_class)
        return results

    def executeMethod(self, method):
        r"""
            引数で与えられたメソッドを、各ExtraConstructorで実行する。
            
            Args:
                method (str):実行するメソッド名。
        """
        for cst in self.extraConstructors():
            if hasattr(cst, method):
                getattr(cst, method)()


class BasicConstructor(rigScripts.BaseCreator):
    r"""
        Constructorモジュールを定義する際に使用する基底クラス。
        メンバー変数FactoryModulesは、このコンストラクタが要求する
        FactoryModule:を表すリストである。
        リスト内にはModuleInfoクラスで定義したモジュールの情報を列挙する。
        メンバー変数ProcessListは、このコンストラクタが要求する
    """
    IsDebugMode = False
    DefaultDebugMode = 'Debug'
    DebugMode = ''
    DebugModeList = []
    FactoryModules = (
        ModuleInfo('jointBuilder', None, None),
        ModuleInfo('cageManager', None, None),
        ModuleInfo('drivenManager', None, None),
        ModuleInfo('weightManager', None, None),
        ModuleInfo('facial', None, None),
        ModuleInfo('extraJointManager', None, None),
        ModuleInfo('controllerExporter', None, None),
    )
    SpecialModules = {
        'model' : 'models',
        'workspace' : 'workScenes'
    }
    LodLow, LodHight = range(2)
    ProcessList = (
        ('preProcess', 'Start to Pre Process.', 'Pre Process was done.'),
        ('importJoints', 'Import joints.', 'Done to import.'),
        ('importModels', 'Import models.', 'Done to import models.'),
        ('finalizeBaseJoints', None, None),
        ('setupSystem', 'Setup system.', 'Done to setup system.'),
        (
            'createController',
            'Start controller creation.', 'Controller creation was done.'
        ),
        ('preSetup',  'Start pre setup.', 'Done.'),
        ('setup', 'Start setup.', 'Done.'),
        (
            'finalizeSetup',
            'Start to finalize setup.', 'Done finalizing setup.'
        ),
        ('postProcess', 'Start post process.', 'Done.'),
        ('finished', None, None),
    )
    ModelGroupName = 'all_grp'
    IsRearrangementModelGroup = True

    # createControllerNodeのオプション。=======================================
    ChainCtrl = 0b01
    IgnoreEndCtrl = 0b10
    # =========================================================================

    def __init__(self, factorySettings=None):
        r"""
            Args:
                factorySettings (factoryModules.FactorySettings):
        """
        super(BasicConstructor, self).__init__()
        # プロジェクトのルートとなるディレクトリを特定する。===================
        if not factorySettings:
            from gris3 import factoryModules
            factorySettings = factoryModules.FactorySettings()
        self.__projdir = factorySettings.rootPath()
        if not os.path.isdir(self.__projdir):
            raise IOError(
                'The root path of The Factory does not exist.'
            )
        # =====================================================================

        self.__lod = None
        self.__fs = factorySettings
        self.__topnodes = []
        self.__lockednodes = []
        self.__binded_joints = []
        self.__assetname = ''
        self.__assettype = ''
        self.__project = ''
        self.__model_grp = None
        self.__lod_dsp_set = {}
        self.__temp_ctrl_grp = None
        self.__controllers = {}
        self.__jointbbsize = (100, 100, 30)
        self.setCtrlTagAttached(True)
        self.__extraConstructor = ExtraConstructorManager(self)
        for method in (
            'installExtraConstructor', 'addExtraConstructor',
            'extraConstructorUtilities', 
        ):
            setattr(self, method, getattr(self.__extraConstructor, method))
        self.createExtraSetupParts = self.__extraConstructor.createSetupParts

        self.init()

    def lod(self):
        r"""
            このコンストラクタが取扱うLODの文字列を返す。
            
            Returns:
                str:
        """
        if self.__lod:
            return self.__lod
        if hasattr(self, 'LOD'):
            self.__lod = self.LOD
            return self.__lod
        import inspect
        module = inspect.getmodule(self.__class__)
        self.__lod = module.__name__.rsplit('.', 1)[-1].split('_', 1)[-1]
        return self.__lod

    def setModelGroup(self, grp):
        r"""
            レンダリングジオメトリを格納したグループノードを登録する。
            
            Args:
                grp (str):モデルのグループ名。
        """
        self.__model_grp = grisNode.ModelAllGroup(grp)

    def modelGroup(self):
        r"""
            レンダリングジオメトリを格納したグループノードを返す。
            
            Returns:
                node.Transform:
        """
        return self.__model_grp

    def lodDisplaySet(self, lod=None):
        r"""
            レンダーモデル表示制御用のセットを返す。
            
            Args:
                lod (str):任意のlod。指定がなければself.lod()を使用
                
            Returns:
                grisNode.DisplaySet:
        """
        if not lod:
            lod = self.lod()
        if not lod in self.__lod_dsp_set:
            self.__lod_dsp_set[lod] = (
                self.root().allSet().displaySet().addSet(lod)
            )
        return self.__lod_dsp_set[lod]

    def connectDisplayCtrlToSet(self, lod=None, asLow=False):
        r"""
            レンダーモデル表示制御用のセットdisplayCtrlを接続する。
            
            Args:
                lod (str):任意のlod。指定がなければself.lod()を使用
                asLow (bool):ローモデルとして登録するかどうか
        """
        lod_dsp_set = self.lodDisplaySet(lod)
        disp_ctrl = self.root().ctrlGroup().displayCtrl()
        if disp_ctrl:
            disp_ctrl.attr('displayType') >> lod_dsp_set.attr('displayType')
            switch_attr = disp_ctrl.attr('lod')
            if asLow:
                rev = func.createUtil('reverse')
                rev.attr('ox') >> lod_dsp_set.attr('display')
                display_plug = rev.attr('ix')
            else:
                display_plug = lod_dsp_set.attr('display')
            switch_attr >> display_plug

    def setupModelGroup(self):
        r"""
            レンダーモデルのセットアップ。
        """
        root = self.root()
        self.__model_grp = None
        try:
            all_grp = grisNode.ModelAllGroup(self.ModelGroupName)
        except Exception as e:
            raise e

        # all_grpが見つかった場合の処理。
        # all_grpとworld_trsに該当するノードを接続する。=======================
        world_trs = root.baseJointGroup().worldTransform()
        for attr in ('t', 'r', 's', 'sh', 'v'):
            s_plug = world_trs.attr(attr)
            d_plug = all_grp.attr(attr)
            if attr == 'v':
                s_children = [s_plug]
                d_children = [d_plug]
            else:
                s_children = s_plug.children()
                d_children = d_plug.children()
            for s, d in zip(s_children, d_children):
                if d.isLocked():
                    d.setLock(False)
                s >> d
                d.setLock(True)

        root.addChild(all_grp)
        self.setModelGroup(all_grp)
        # =====================================================================

        # all_grpをカレントのLODのDisplayセットとして登録する。================
        lod_dsp_set = self.lodDisplaySet()
        lod_dsp_set.addChild(all_grp)
        self.connectDisplayCtrlToSet()
        # =====================================================================

    def init(self):
        r"""
            __init__内で呼ばれる上書き用初期化メソッド。
        """
        pass

    def factorySettings(self):
        r"""
            ファクトリの設定内容を保持するオブジェクトを返す。
            
            Returns:
                factoryModules.FactorySettings:
        """
        return self.__fs

    def extraConstructorManager(self):
        r"""
            ExtraConstructorManagerを返す。
            
            Returns:
                ExtraConstructorManager:
        """
        return self.__extraConstructor

    def projdir(self):
        r"""
            プロジェクトのルートディレクトリパスを返す。
            
            Returns:
                str:
        """
        return self.__projdir

    def subdir(self, category):
        r"""
            プロジェクトのルートディレクトリから相対でサブファイルのパスを返す。
            引数には"joints/subJoints'のように/をセパレータにして表記する
            ことにより、サブディレクトリの下の階層も指示できる。
            
            Args:
                category (str):
                
            Returns:
                str:
        """
        return os.path.join(self.projdir(), category)

    def moduleDir(self, moduleName, tag=''):
        r"""
            引数moduleNameで指定したモジュールが管理するディレクトリを
            リストで返す。
            リストで返すのは、設定の中に複数の同一モジュールがある可能性
            があるためで、引数tagによりフィルタリングも可能。
            
            Args:
                moduleName (str):factoryModulesが内包するモジュール名
                tag (str):フィルタリング用タグ。
                
            Returns:
                list:
        """
        fs = self.factorySettings()
        module_info = fs.listModulesAsDict().get(moduleName)
        if not module_info:
            return []
        return [
            self.subdir(x.name())
            for x in module_info if x.tag() == tag
        ]

    def printProgress(self, message, NumberOfBreak=0, separator='='):
        r"""
            経過メッセージを成型してprintする。
            
            Args:
                message (str):
                NumberOfBreak (int):メッセージ表示後の空行の数
                separator (str):セパレータ用文字列
        """
        print(message.ljust(80, separator))
        if NumberOfBreak:
            print('\n' * NumberOfBreak)

    def isDebugMode(self):
        r"""
            デバッグモードかどうかを返す。
            こちらは古い仕様のため、基本的にはdebugModeメソッドの仕様を推奨。

            Returns:
                bool:
        """
        return self.IsDebugMode

    def debugMode(self):
        r"""
            デバッグモードの種類を返す。

            Returns:
                str:
        """
        return self.DebugMode

    def listDebugModes(self):
        r"""
            デバッグモードの種類を返す。

            Returns:
                list:
        """
        return [self.DefaultDebugMode] + self.DebugModeList

    def printDebug(self, message):
        r"""
            デバッグモード時のみメッセージをプリントする。
            
            Args:
                message (str):
        """
        if self.isDebugMode():
            print('[Debug Message] : {}'.format(message))

    def setCtrlTagAttached(self, state):
        r"""
            toControllerで作成されるコントローラにcontrollerタグするか
            どうかを指定する。
            
            Args:
                state (bool):
        """
        self.__ctrl_tag_attached = bool(state)

    def isCtrlTagAttached(self):
        r"""
            toControllerで作成されるコントローラをcontrollerタグに
            するかどうかを返す。
            
            Returns:
                bool:
        """
        return self.__ctrl_tag_attached

    def currentFiles(
        self, category, isFullPath=True, matchChar=CurrentFilePattern
    ):
        r"""
            引数category内のカレントファイルをリストする。
            引数categoryで指定する値はsubdirの引数と同じもの。
            また、カレントファイルのフォーマットの指示は引数matchCharで
            正規表現を使用して指示する。
            
            Args:
                category (str):
                isFullPath (bool):フルパスで返すかどうか
                matchChar (str):
                
            Returns:
                list:
        """
        if os.path.isabs(category):
            rootpath = self.subdir(category)
        else:
            rootpath = category
        if not os.path.isdir(rootpath):
            return []
        pattern = re.compile(matchChar, re.IGNORECASE)
        filelist = [
            x for x in os.listdir(rootpath) if pattern.search(x)
        ]
        if isFullPath:
            filelist = [os.path.join(rootpath, x) for x in filelist]
        return filelist

    def currentModuleFiles(
        self, moduleName, tag='', isFullPath=True, matchChar=CurrentFilePattern
    ):
        r"""
            引数moduleNameで指定したモジュールが管理するディレクトリ内の
            カレントファイルをリストする。
            カレントファイルのフォーマットの指示は引数matchCharで正規表現を
            使用して指示する。
            
            Args:
                moduleName (str):factoryModulesが内包するモジュール名
                tag (str):フィルタリング用のタグ
                isFullPath (bool):フルパスで返すかどうか
                matchChar (str):
                
            Returns:
                list:
        """
        dirlist = []
        for d in self.moduleDir(moduleName, tag):
            dirlist.extend(self.currentFiles(d, isFullPath, matchChar))
        return dirlist

    def loadSettings(self):
        r"""
            factoryModules.FactorySettingsから設定を読み込む。
            FactorySettings:へはプロジェクトルート下にある設定ファイルを
            適用してから読み込む。
        """
        fs = self.factorySettings()
        self.__assetname = fs.assetName()
        self.__assettype = fs.assetType()
        self.__project = fs.project()
        print('    Asset Name : {}'.format(self.__assetname))
        print('    Asset Type : {}'.format(self.__assettype))
        print('    Project    : {}'.format(self.__project))

    def assetName(self):
        r"""
            セットアップ中のアセット名を返す。
            
            Returns:
                str:
        """
        return self.__assetname

    def assetType(self):
        r"""
            セットアップ中のアセットタイプを返す。
            
            Returns:
                str:
        """
        return self.__assettype

    def project(self):
        r"""
            セットアップ中のアセットのプロジェクトを返す。
            
            Returns:
                str:
        """
        return self.__project

    def initialize(self):
        r"""
            execute内で最初に呼ばれる、シーン初期化用メソッド。
            新規シーンにする。
        """
        cmds.file(f=True, new=True)
        self.__topnodes = cmds.ls(assemblies=True)

    def addInitialTopNode(self, node):
        r"""
            finalize時に消去されないDAGノードを登録する。
            
            Args:
                node (str):
        """
        self.__topnodes.append(node)

    def preProcess(self):
        r"""
            処理開始前に最初に呼ばれる上書き用メソッド。
        """
        pass

    def finalizeBaseJoints(self):
        r"""
            ベースジョイントのファイナライズ処理を行う。
        """
        core.finalizeBaseSkeleton(True, True)

    def createSystemRootGroup(
        self, name, nodeType, position, parent, parentJoint='', isFollow=True,
        isReuse=False
    ):
        r"""
            システムに関するグループを作成する。
            isReuseがTrueの場合で作成する名前のノードがすでに存在する場合は
            そのノードを返す。
            
            Args:
                name (str):ベースとなる名前
                nodeType (str):ノードタイプを表す文字列
                position (int or str):位置を表す値
                parent (str):作成する親ノード名
                parentJoint (str):親としてコンストレインされるノード
                isFollow (bool):親にコンストレインされるかどうか
                isReuse (bool):
                
            Returns:
                node.Transform:作成されたグループノード
        """
        nameobj = func.Name()
        nameobj.setName(name)
        nameobj.setNodeType(nodeType)
        nameobj.setPosition(position)
        rootname = nameobj()
        if isReuse and cmds.objExists(rootname):
            # isReuseがTrueで、すでにノードが存在している場合は
            # そのノードを返す。
            return func.asObject(rootname)

        root = node.createNode('transform', n=rootname, p=parent)
        self.addLockedList(root)
        parentJoint = func.asObject(parentJoint)
        if parentJoint:
            if isFollow:
                self.constraintFromBaseJoint(root, parentJoint)
            else:
                root.fitTo(parentJoint)
        return root

    def createCtrlRoot(
        self, name, position=0, parentJoint='', isFollow=True,
        isReuse=False
    ):
        r"""
            コントローラを格納する親となるノードを作成する。
            作成される場所はctrlTopの直下。
            isReuseがTrueの場合で作成する名前のノードがすでに存在する場合は
            そのノードを返す。
            
            Args:
                name (str):ベースとなる名前
                position (int or str):位置を表す値
                parentJoint (str):親としてコンストレインされるノード
                isFollow (bool):親にコンストレインされるかどうか
                isReuse (bool):
                
            Returns:
                node.Transform:
        """
        return self.createSystemRootGroup(
            name, 'parentProxy', position, self.ctrlTop(), parentJoint,
            isFollow, isReuse
        )

    def createRigRoot(
        self, name, position=0, parentJoint='', isFollow=False,
        isReuse=False
    ):
        r"""
            リグを格納する親となるノードを作成する。
            作成される場所はrigGroupの直下。
            isReuseがTrueの場合で作成する名前のノードがすでに存在する場合は
            そのノードを返す。
            
            Args:
                name (str):ベースとなる名前
                position (int or str):位置を表す値
                parentJoint (str):親としてコンストレインされるノード
                isFollow (bool):親にコンストレインされるかどうか
                isReuse (bool):
                
            Returns:
                node.Transform:
        """
        return self.createSystemRootGroup(
            name+'Rig', 'grp', position, self.rigGroup(), parentJoint,
            isFollow, isReuse
        )

    def createSetupRoot(
        self, name, position=0, parentJoint='', isFollow=False,
        isReuse=False
    ):
        r"""
            セットアップ用dataを格納する親となるノードを作成する。
            作成される場所はsetupGroupの直下。
            isReuse:がTrueの場合で作成する名前のノードがすでに存在する場合は
            そのノードを返す。
            
            Args:
                name (str):[]ベースとなる名前
                position (int or str):位置を表す値
                parentJoint (str):親としてコンストレインされるノード
                isFollow (bool):親にコンストレインされるかどうか
                isReuse (bool):
                
            Returns:
                node.Transform:
        """
        return self.createSystemRootGroup(
            name+'Setup', 'grp', position, self.setupGroup(), parentJoint,
            isFollow, isReuse
        )

    def createAnimSet(self, name, position=0):
        r"""
            animSetを作成する。
            すでに存在している場合は、そのanimSetを返す。
            
            Args:
                name (str):ベースとなる名前
                position (int or str):位置を表す値
                
            Returns:
                grisNode.AnimSet:
        """
        return self.allAnimSet().addSet(name, position)

    def toController(
        self, name, animSetName, animSetPosition=0,
        option=0b00, nodeType='transform', filter=(lambda x:True)
    ):
        r"""
            与えれたベースジョイントに対応するコントローラを作成する。
            optionはビット指定で、それによって作成時の挙動が変わる。
            Constructor.ChainCtrl ： 子も含めて作成
            Constructor.IgnoreEndCtrl ：末端コントローラは作成しない。
            Constructor.ChainCtrlと併用した時に効果を発揮する。
            
            Args:
                name (str):ベースジョイント
                animSetName (str):animSetの名前
                animSetPosition (int or str):animSetの位置を表す文字
                option (bin):作成オプション
                nodeType (str):作成されるノードの種類
                filter (function):: 選別用のフィルタ関数。
                
            Returns:
                list:
        """
        is_ctrl_tag_attached = self.isCtrlTagAttached()
        def l_createCtrl(name, animSetName, animSetPosition, nodeType):
            r"""
                コントローラ作成用のローカル関数。
                
                Args:
                    name (str):
                    animSetName (str):
                    animSetPosition (int or str):
                    nodeType (str):
                    
                Returns:
                    node.AbstractNode:
            """
            anim_set = self.createAnimSet(animSetName, animSetPosition)
            nameobj = func.Name(name)
            nameobj.setNodeType('ctrl')

            ctrl = node.createNode(
                nodeType, n=nameobj(), p=self.temporaryCtrlGroup()
            )
            if nodeType == 'joint':
                ctrl.hideDisplay()
            cmds.setAttr('%s.v.' % ctrl, k=False)
            anim_set.addChild(ctrl)
            if is_ctrl_tag_attached:
                node.setController(ctrl)
            self.__controllers[nameobj()] = ctrl
            return ctrl

        result = []
        if option & self.ChainCtrl:
            topnode = func.asObject(name)
            all_children = topnode.allChildren()
            all_children.append(topnode)
            if option & self.IgnoreEndCtrl:
                all_children = [x for x in all_children if x.hasChild()]
            all_children = [x for x in all_children if filter(x)]
            nodelist = all_children
        else:
            nodelist = [name]
        for name in nodelist:
            result.append(
                l_createCtrl(name, animSetName, animSetPosition, nodeType)
            )
        if not option & self.ChainCtrl:
            return result[0]
        return result

    def parentAsController(self, controller, parent, shapeCreator=None):
        r"""
            コントローラノードをコントローラとして引数parentへ
            親子付する。この際controllerはparentからの相対距離は0となる。
            また、shapeCreatorが指定されている場合はそのシェイプも追加する。
            
            Args:
                controller (str):toControllerによって生成されたノード
                parent (str):親ノード
                shapeCreator (func.PrimitiveCreator):コントローラ形状定義クラス
                
            Returns:
                node.Transform:
        """
        ctrl = func.asObject(cmds.parent(controller, parent)[0])
        if ctrl.isType('joint'):
            ctrl('t', (0, 0, 0))
            cmds.makeIdentity(ctrl, a=True, r=True, s=True, jo=True)
        else:
            cmds.makeIdentity(ctrl, t=True, r=True, s=True)
        if shapeCreator:
            shapeCreator.create(parentNode=ctrl)
        return func.asObject(ctrl)

    def connectController(
            self, target, parent, shapeCreator=None, spacers=[],
            calcSpaces=False, option=0b00, filter=(lambda x:True)
        ):
        r"""
            引数target（ベースジョイント）に対して、toControllerで作成した
            ノードをコントローラとして接続する。
            spacesに文字列のリストを指定すると、その文字列をnodeTypeとする
            スペーサーをctrlとspaceの間に追加する。
            calcSpacesはスペーサーを動かした時にtargetに影響がでるかどうかを
            指定する。
            引数optionはtoControllerのオプションと同じビット指定。
            戻り値は作成されたコントローラとそのスペーサーを含むリストで、
            小階層から（コントローラ）から順に上階層に向かった並びになっている。
            
            Args:
                target (str):対象ノード
                parent (str):コントローラが作成される親
                shapeCreator (func.PrimitiveCreator]):
                spacers (list):
                calcSpaces (bool or list):
                option (bin):
                filter (function):
                
            Returns:
                list:作成されたコントローラとスペーサーのリスト
        """
        # ローカル関数セット。+++++++++++++++++++++++++++++++++++++++++++++++++
        id_matrix = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
        def l_connectCtrl(
            target, parent, shapeCreator=None, spacers=[], calcSpaces=False
        ):
            r"""
                コントローラ接続用のローカル関数。
                
                Args:
                    target (str):
                    parent (str):
                    shapeCreator (func.PrimitiveCreator):
                    spacers (list):
                    calcSpaces (bool or list):
                    
                Returns:
                    list:
            """
            result = []
            matrixlist = []
            calcflags = []
            num_spaces = len(spacers)+1
            if isinstance(calcSpaces, (list, tuple)):
                if num_spaces != len(calcSpaces):
                    raise ValueError(
                        'The number of calcSpaces is wrong : %s' % (
                            len(calcSpaces)
                        )
                    )
                calcflags = calcSpaces
            elif isinstance(calcSpaces, bool):
                calcflags = [calcSpaces for x in range(num_spaces)]
            else:
                raise RuntimeError(
                    'The given value for calcSpaces must be type '
                    '"bool" or "list".'
                )

            name = func.Name(target())
            target_type = target.type()

            name.setNodeType('ctrl')
            if not cmds.objExists(name()):
                return []

            # スペーサーの作成。===============================================
            name.setNodeType('ctrlSpace')
            space = node.createNode(target_type, n=name(), p=parent)
            if target_type == 'joint':
                space.hideDisplay()
                space('ssc', target('ssc'))
                space.setInverseScale(False)
            space.fitTo(target)
            self.addLockedList(space)
            result.append(space)
            # =================================================================

            # spacersの数だけnullを追加する。==================================
            temp_parent = space
            for s in spacers:
                name.setNodeType(s)
                auto_trs = node.createNode(
                    'transform', n=name(), p=temp_parent
                )
                self.addLockedList(auto_trs)
                result.append(auto_trs)
                temp_parent = auto_trs
            else:
                auto_trs = []

            # コントローラの作成。
            name.setNodeType('ctrl')
            ctrl = self.parentAsController(name(), result[-1], shapeCreator)
            # =================================================================

            # コントローラからtargetへの接続を行う。===========================
            if target_type == 'transform':
                result.append(ctrl)
                num_spaces += 1
                calcflags.insert(0, True)

            if num_spaces == 1:
                mtxplug = result[0].attr('matrix')
            else:
                result.reverse()
                mltmtx = func.createUtil('multMatrix')
                for n, flags in zip(result, enumerate(calcflags)):
                    plug = 'matrixIn[%s]' % flags[0]
                    if flags[1]:
                        n.attr('matrix') >> mltmtx/plug
                    else:
                        mltmtx(plug, n('matrix'), type='matrix')
                mtxplug = mltmtx.attr('matrixSum')

            if target_type == 'transform':
                func.createDecomposeMatrix(target, [mtxplug], False)
            elif target_type == 'joint':
                cst = func.fixConstraint(cmds.parentConstraint, ctrl, target)
                mtxplug >> cst/'target[0].targetParentMatrix'
                cst('constraintParentInverseMatrix', id_matrix, type='matrix')
                ~ctrl.attr('s') >> ~target.attr('s')
                result.insert(0, ctrl)
            # =================================================================
            return func.toObjects(result)

        types = ['joint', 'transform']
        def l_createControl(
            target, parent, shapeCreator, spacers, calcSpaces, ignoreEndCtrl,
            filter
        ):
            r"""
                再帰的にコントローラを作成するローカル関数。
                
                Args:
                    target (node.Transform):
                    parent (str):
                    shapeCreator (func.PrimitiveCreator):
                    spacers (list):
                    calcSpaces (bool or list):
                    ignoreEndCtrl (bool):
                    filter (function):フィルタ用の関数。
                    
                Returns:
                    list:
            """
            if not filter(target):
                return []
            if not target.hasChild() and ignoreEndCtrl:
                return []

            children = [x for x in target.children() if x.isType(types)]
            ctrls = l_connectCtrl(
                target, parent, shapeCreator, spacers, calcSpaces
            )
            if not ctrls:
                return []
            if not children:
                return [ctrls]
            result = [ctrls]

            for child in children:
                result.extend(
                    l_createControl(
                        child, ctrls[0], shapeCreator, spacers, calcSpaces,
                        ignoreEndCtrl, filter
                    )
                )
            return result
        # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        target = func.asObject(target)
        if not option & self.ChainCtrl:
            # 単体コントローラの場合。
            return l_connectCtrl(
                target, parent, shapeCreator, spacers, calcSpaces
            )

        # 下階層まで作成する場合。=============================================
        ignore_end_joint = option & self.IgnoreEndCtrl
        return l_createControl(
            target, parent, shapeCreator, spacers, calcSpaces,
            ignore_end_joint, filter
        )
        # =====================================================================        

    def createAngleDriver(self, target, name=None, position=0):
        r"""
            targetのangleDriverを任意のグループ内に作成する。
            
            Args:
                target (str):angleDriverのソースノード
                name (str):ベース名
                position (int or str):位置を表す値
                
            Returns:
                node.Transform:
        """
        target = func.asObject(target)
        name_obj = func.Name(target)
        name_obj.setNodeType('aglDrv')
        if name:
            name_obj.setName(name)
        if position:
            name_obj.setPosition(position)

        setup_grp = self.setupGroup()
        for grp in setup_grp.children():
            if grp == 'angleDriver_grp':
                p = grp
                break
        else:
            p = node.createNode('transform', n='angleDriver_grp', p=setup_grp)
            p.lockTransform()
        driver = func.createAngleDriverNode(target, name_obj(), p)
        driver.fitTo(target)
        return driver

    def createDistanceDriver(
        self, startNode, endNode, name=None, position=0, asLocal=False
    ):
        r"""
            startNodeとendNode間の伸縮率を図るdistanceDriverを作成する。
            
            Args:
                startNode (str):開始位置を表すTransformノード名
                endNode (str):終了位置を表すTransformノード名
                name (str):ベース名
                position (int):位置を表す０～９の数字
                
            Returns:
                node.Transform:
        """
        setup_grp = self.setupGroup()
        for grp in setup_grp.children():
            if grp == 'distanceDriver_grp':
                p = grp
                break
        else:
            p = node.createNode(
                'transform', n='distanceDriver_grp', p=setup_grp
            )
            p.lockTransform()
        if not name:
            name_obj = func.Name(
                startNode.split('.')[0] if '.' in startNode else startNode
            )
        else:
            name_obj = func.Name()
            name_obj.setName(name)
        name_obj.setNodeType('dstDrv')
        name_obj.setPosition(position)

        driver = func.createDistanceDriverNode(
            startNode, endNode, name_obj(), p, asLocal
        )
        return driver

    def createHalfRotater(self, *targets):
        r"""
            引数nodesの半分の回転を行うノードを作成する。
            targetsには名前ルールに則ったノード名である必要がある。
            
            Args:
                *targets (str):
                
            Returns:
                list:
        """
        from gris3.tools import jointEditor
        halfrotaters = jointEditor.createHalfRotater(targets)
        result = []
        for t, r in zip(targets, halfrotaters):
            name = func.Name(t)
            name.setName(name.name()+'HR')
            r[0].rename(name())
            
            name.setNodeType('hrpb')
            r[1].rename(name())

            result.append(func.asObject(r[0]()))
        return result

    def createMatrixConstraint(self, baseJoint, target):
        r"""
            ベースジョイントからローカルのコンストレインを行う。
            戻り値として作成されたdecomposeMatrixノードならびにmultMatrix
            ノードを返す。
            
            Args:
                baseJoint (str):
                target (str):
                
            Returns:
                list:
        """
        baseJoint = node.asObject(baseJoint)
        target = node.asObject(target)
        if baseJoint == self.jointRoot():
            for attr in ('t', 'r', 's', 'sh'):
                ~baseJoint.attr(attr) >> ~target.attr(attr)
            return

        offset_mtx = node.multiplyMatrix(
            [target.matrix(), baseJoint.inverseMatrix()]
        )
        nodeChain = func.listNodeChain(self.jointRoot(), baseJoint)
        nodeChain.reverse()

        mtx_nodes = func.createDecomposeMatrix(
            target, ['%s.matrix' % x for x in nodeChain[:-1]], startNumber=1
        )
        mtx_nodes[1]('matrixIn[0]', offset_mtx, type='matrix')
        return mtx_nodes

    def localWrap(self, geometories, cage, withIm=True):
        r"""
            ローカルスペースでのラップを行う。
            
            Args:
                geometories (list):ラップされるオブジェクトのリスト
                cage (str):ラップするケージ
                withIm (bool):中間オブジェクトを作成するかどうか
        """
        basenode_grp = func.asObject('baseNode_grp')
        in_plug = {
            'mesh':'inMesh', 'nurbsSurface':'create', 'nurbsCurve':'create',
            'lattice': 'latticeInput'
        }
        out_plug = {
            'mesh':'outMesh', 'nurbsSurface':'local', 'nurbsCurve':'local',
            'lattice': 'latticeOutput'
        }
        if not basenode_grp:
            basenode_grp = node.createNode(
                'transform', n='baseNode_grp', p=self.setupGroup()
            )
            basenode_grp.lockTransform()

        im_grp = node.asObject('im_grp')
        if not im_grp:
            im_grp = node.createNode(
                'transform', n='im_grp', p=self.setupGroup()
            )
            im_grp.lockTransform()
            cmds.hide(im_grp)

        surfaces = cmds.listRelatives(geometories, ad=True)
        if not surfaces:
            return
        surfaces = cmds.ls(surfaces, type=list(in_plug.keys()))
        if not surfaces:
            return

        wrapped_nodes = []
        reconnectings = []
        for surface in surfaces:
            if not withIm:
                wrapped_nodes.append(surface)
                continue

            facial_proxy = cmds.listConnections(
                '%s.message' % surface, s=False, p=True
            )
            if facial_proxy:
                facial_proxy = [
                    x.split('.')[0] for x in facial_proxy
                    if x.find('.facialProxy') > -1
                ]
                if facial_proxy:
                    wrapped_nodes.extend(facial_proxy)
                    continue

            node_type = cmds.nodeType(surface)
            if 'lattice' == node_type:
                trs, ffd, base = cmds.duplicate(
                    surface,
                    name='im_%s' % cmds.listRelatives(surface, parent=True)[0]
                )
                new_surf = cmds.listRelatives(
                    trs, shapes=True, path=True, type='lattice', ni=True
                )[0]
                otherShapes = [
                    x for x in cmds.listRelatives(trs, shapes=True, path=True)
                    if not x == new_surf
                ]
                if otherShapes:
                    cmds.delete(otherShapes)
                attrList = cmds.listConnections(
                    new_surf, s=False, d=True, p=True, c=True, type='ffd'
                )
                for src, dst in zip(attrList[0::2], attrList[1::2]):
                    cmds.disconnectAttr(src, dst)
                cmds.delete(ffd, base)
                cmds.parent(trs, im_grp)
            else:
                trs = node.createNode(
                    'transform', n='im_%s' % surface, p=im_grp
                )
                new_surf = node.createNode(node_type, n='%sShape' % trs, p=trs)

                cmds.connectAttr(
                    '%s.%s' % (surface, out_plug[node_type]),
                    '%s.%s' % (new_surf, in_plug[node_type])
                )
                cmds.delete(new_surf, ch=True)
            wrapped_nodes.append(surface)
            reconnectings.append(
                (surface, new_surf, out_plug[node_type], in_plug[node_type])
            )

        geometories = func.localWrap(wrapped_nodes, cage)
        for srf, im, outplug, inplug in reconnectings:
            input = cmds.listConnections(
                '%s.%s' % (srf, inplug), p=True, s=True, d=False
            )[0]
            cmds.connectAttr(input, '%s.%s' % (im, inplug))
            cmds.connectAttr(
                '%s.%s' % (im, outplug), '%s.%s' % (srf, inplug), f=True
            )
        cmds.parent(geometories['baseNode'], basenode_grp)

    def lattice(self, *args, **keywords):
        r"""
            ラティスを作成する。
            作成されたラティスのベースは然るべき階層に移動される。
            引数はcmds.latticeコマンドに渡される。
            戻り地はffd、lattice、baseの３つ。
            
            Args:
                *args (str):
                **keywords (str):
                
            Returns:
                list:
        """
        basenode_grp = func.asObject('lattice_grp')
        if not basenode_grp:
            basenode_grp = node.createNode(
                'transform', n='lattice_grp', p=self.setupGroup()
            )
            basenode_grp.lockTransform()

        # 名前に関するオプション設定の取得。===================================
        flags = {}
        for flagset in (('n', 'name'), ('p', 'position')):
            for f in flagset:
                if f in keywords:
                    flags[flagset[0]] = keywords[f]
                    break
            else:
                flags[flagset[0]] = ''
        for f in ('p', 'position'):
            if f in keywords:
                del keywords[f]
        # =====================================================================
        ffd, lat, bas = cmds.lattice(*args, **keywords)
        lattices = [
            ffd, cmds.parent(lat, basenode_grp), cmds.parent(bas, basenode_grp)
        ]
        if not flags['n']:
            return node.toObjects(lattices)

        n = func.Name()
        n.setName(flags['n'])
        n.setPosition(flags['p'])
        new_lattices = []
        for ffd, typ in zip(lattices, ('ffd', 'ffdLat', 'ffdBas')):
            n.setNodeType(typ)
            new_lattices.append(node.asObject(cmds.rename(ffd, n())))
        return new_lattices

    def createStaticJoint(self, n='static_bndJnt'):
        r"""
            バインド用のstaticジョイントを作成する。
            
            Args:
                n (str):任意の名前
                
            Returns:
                node.Joint:
        """
        bnd_jnt = node.asObject(n)
        if bnd_jnt:
            return bnd_jnt
        bindjnt_grp = self.setupGroup().bindJointGroup()
        return node.createNode('joint', n=n, p=bindjnt_grp)

    def createBindJoint(
        self, startJoint, endJoint=None, parent=None, namespace=''
    ):
        r"""
            bindJointを作成する関数。
            引数endJointはstartJointよりも下の階層のジョイントである必要がある。
            また-1を入れた場合はstartJointのbindJointのみを作成する。
            Noneの場合は末端まですべて作成する。
            endJointに正規表現オブジェクト、もしくは正規表現
            オブジェクトを内包するリストを渡すと、その正規表現にひっかかった
            ノードで作成を止める。
            
            このメソッドで作成されたバインドジョイントは、後に元ジョイントと
            コネクトするためのリストに登録される。
            
            Args:
                startJoint (str or list or tuple):[]開始ジョイント
                endJoint (str or int or None):
                parent (str):作成する親ノード
                namespace (str):
                
            Returns:
                node.Transform:
        """
        bindjnt_grp = self.setupGroup().bindJointGroup()
        self.__binded_joints.append(startJoint)
        return func.createBindJoint(
            startJoint, endJoint, parent, bindjnt_grp, namespace
        )

    def connectToBindJoint(self, topJoints=None):
        r"""
            createBindJointで作成されたバインドジョイントへの接続を行う。
            引数topJointsに指定がない場合はcreateBindJointメソッドで作成された
            バインドジョイントの接続を行う。
            
            Args:
                topJoints (str):
                
        """
        if not topJoints:
            topJoints = self.__binded_joints
        else:
            if isinstance(topJoint, (list, tuple)):
                topJoints = [topJoints]
        for joint in topJoints:
            func.connectToBindJoint(joint)

    def importFile(self, filepath, isCheck=True):
        r"""
            mayaファイルをインポートする。
            
            Args:
                filepath ():
                isCheck (bool):ファイルの存在をチェックするかどうか
                
            Returns:
                str:
        """
        filepath = filepath.replace('\\', '/')
        if isCheck and not os.path.exists(filepath):
            raise IOError('File was not found : %s' % filepath)
        print(' => Import file : {}'.format(filepath))
        return cmds.file(filepath, i=True, rnn=True)

    def assembleJoints(self):
        r"""
            importJoints内で呼ばれるオーバーライド専用メソッド。
            主にジョイントの親子の組み換えなどに使う。
        """
        pass

    def importJoints(self, tag=''):
        r"""
            任意ディレクトリのファイルをジョイントファイルとして読込む
            
            Args:
                tag (str):
        """
        files = self.currentModuleFiles('jointBuilder', tag)
        for file in files:
            self.importFile(file)
        self.assembleJoints()
        try:
            joint_root = self.jointRoot()
        except:
            return

        if self.__jointbbsize[0] > 0 or self.__jointbbsize(bb) > 0:
            return        
        bb = cmds.xform(joint_root, q=True, ws=True, bb=True)
        bb = [(bb[x+3] - bb[x]) for x in range(3)]
        self.__jointbbsize = bb

    def jointBoundBoxSizes(self):
        r"""
            ジョイント読み込み時のrootのバウンディングボックスを返す。
            
            Returns:
                list:
        """
        return self.__jointbbsize

    def importModels(self, lod=None, isCheck=True, calcBb=True, tag=''):
        r"""
            レンダーモデルを読み込む。
            引数lodは指定がなければself.lod()の戻り値を使用する。
            
            Args:
                lod (str):LOD
                isCheck (bool):
                calcBb (bool):
                tag (str):
        """
        if not lod:
            lod = self.lod()
        files = self.currentModuleFiles('model', tag)
        filename_pattern = re.compile(
            self.assetName()+'_'+lod+'\.cur\.[a-z\d]+$'
        )
        models = None
        for file in files:
            if not filename_pattern.search(os.path.basename(file)):
                continue
            models = self.importFile(file, isCheck)
            break
        if not models or not calcBb:
            return

        bblist = [[] for x in range(6)]
        for model in cmds.ls(models, assemblies=True):
            bb = cmds.xform(model, q=True, ws=True, bb=True)
            for i in range(6):
                bblist[i].append(bb[i])
        bb = [max(x) for x in bblist]
        self.__jointbbsize = [(bb[x+3] - bb[x]) for x in range(3)]

    def importCages(self, tag=''):
        r"""
            ケージを読み込み、cage_grpへ移す。
            
            Args:
                tag (str):
        """
        cage_files = self.currentModuleFiles('cageManager', tag)
        pre_top_nodes = cmds.ls(assemblies=True)
        cage_grp = self.root().setupGroup().cageGroup()
        for file in cage_files:
            self.importFile(file)
        post_top_nodes = cmds.ls(assemblies=True)
        cage_nodes = []
        for node in post_top_nodes:
            if node in pre_top_nodes:
                continue
            cage_nodes.append(node)
        if cage_nodes:
            cmds.parent(cage_nodes, cage_grp())

    def loadSkinWeights(self, filelist=[], tag=''):
        r"""
            指定したスキニング用ファイル（mel）をロードする。
            
            Args:
                filelist (list):ロードするファイルのリスト
                tag (str):
        """
        def listShapeFlow(shape):
            r"""
                Args:
                    shape (str):
            """
            for inplug in ('inMesh', 'worldMesh', 'local', 'worldSpace'):
                if not shape.hasAttr(inplug):
                    continue
                src = shape.attr(inplug).source(sh=True)
                if not src:
                    return []
                result = [src]
                result.extend(listShapeFlow(src))
                return result
            return []

        sc_name_pattern = re.compile('(^.*)_wgt')
        from gris3.exporter import skinWeightExporter
        if not filelist:
            filelist = self.currentModuleFiles('weightManager', tag)

        weighted_list = {}
        for file in filelist:
            rootpath, filename = os.path.split(file)
            mobj = sc_name_pattern.search(filename)
            if not mobj:
                continue
                print(
                    '[Warning] : No node name found from filename.'
                    'Skip loading weights : %s' % filename
                )
            namelist = [mobj.group(1), 'sc']

            rst = skinWeightExporter.Restorer()
            rst.setFile(file)
            rst.setSkinClusterName('_'.join(namelist))
            info = rst.analyzeInfo()
            shape = node.asObject(info.get('Skinned Shape'))
            if not shape:
                continue
            weighted_list[shape] = rst

        loading_order = []
        # inMesh > outMeshの接続がされている場合に備えて読み込み順序を操作する。
        for shape in weighted_list:
            if not shape in loading_order:
                loading_order.append(shape)
            srclist = listShapeFlow(shape)
            for src in srclist:
                if src not in loading_order or src not in weighted_list:
                    continue
                i = loading_order.index(src)
                s = loading_order.pop(i)
                loading_order.append(s)

        for shape in loading_order:
            rst = weighted_list[shape]
            print('# Load skin cluster from : {}'.format(rst.file()))
            rst.restore()

    def loadExtraJoints(self, filelist=[], tag=''):
        r"""
            指定したExtraジョイント用ファイル(json)をロードする。
            
            Args:
                filelist (list):ロードするファイルのリスト
                tag (str):
                
            Returns:
                list:
        """
        from gris3.exporter import extraJointExporter
        if not filelist:
            filelist = self.currentModuleFiles('extraJointManager', tag)
        extra_joints = []
        for file in filelist:
            extra_joints.extend(extraJointExporter.loadExtraJointScript(file))
        return extra_joints

    def loadDrivenKeys(self, filelist=[], tag=''):
        r"""
            ドリブンキーをインポートする。
            
            Args:
                filelist (list):ロードするファイルのリスト
                tag (str):
        """
        if not filelist:
            filelist = self.currentModuleFiles('drivenManager', tag)
        for file in filelist:
            self.importFile(file)

    def loadControllerCurves(self, filelist=[], tag=''):
        r"""
            コントローラとして使用するカーブの形状をロードする。
            
            Args:
                filelist (list):
                tag (str):
        """
        from gris3.exporter import curveExporter
        if not filelist:
            filelist = self.currentModuleFiles('controllerExporter', tag)
        for file in filelist:
            curveExporter.importCurveFile(file)

    def setupSystem(self):
        r"""
            GrisRootを特定し、存在すれば初期設定を行う。
            初期設定の内容は設定ファイルに従って、GrisRootにアセット名、
            アセットタイプ、プロジェクトをセットし、ルートコントローラを
            作成する。
        """
        root = self.root()
        if not root:
            return
        print('# Found Root Node : {}'.format(root))
        print('    Setup Root Node.')
        root.setAssetName(self.assetName())
        root.setAssetType(self.assetType())
        root.setProject(self.project())
        root.setCreationData()
        bb = self.jointBoundBoxSizes()
        ctrl_size = (bb[0]+bb[2])*0.25
        core.createRootCtrl(size=ctrl_size if ctrl_size > 0 else 100)

        name = func.Name()
        name.setName('temporaryCtrl')
        name.setNodeType('grp')
        self.__temp_ctrl_grp = node.createNode(
            'transform', n=name(), p=self.ctrlGroup()
        )
        self.__temp_ctrl_grp.lockTransform().hide()

    def temporaryCtrlGroup(self):
        r"""
            一時的に作成されるテンポラリコントローラ格納グループ名。
            
            Returns:
                node.Transform:
        """
        return self.__temp_ctrl_grp

    def createController(self):
        r"""
            セットアップ実行前にコントローラを作成処理をするための
            オーバーライド専用メソッド。
        """
        pass

    def preSetupForLOD(self):
        r"""
            本セットアップ前の事前準備を行う上書き用メソッド。
        """
        pass

    def editModelGroup(self):
        r"""
            モデルデータに対する編集処理を行う。
        """
        self.setupModelGroup()
        cleanup.deleteAllDisplayLayers()
        model_grp = self.modelGroup()
        if not model_grp:
            return

        # モデルデータの階層の修正。===========================================
        if self.IsRearrangementModelGroup:
            root = self.root()
            model_all_grp = node.createNode(
                'transform', n='modelAllGeo_grp', p=root
            )
            model_all_grp.lockTransform()
            model_all_grp.addChild(
                model_grp, model_grp.rigDataGroup(), model_grp.renderDataGroup()
            )
        # =====================================================================

        cleanup.disableOverrideEnables(model_grp)
        mdlset = model_grp.modelAllSet()
        if mdlset:
            mdlset.delete()
        model_grp.rename('render_grp')

    def preSetup(self):
        r"""
            本セットアップ前の事前準備を行う。
        """
        self.editModelGroup()

        # ケージのロード。
        self.importCages()
        self.preSetupForLOD()

    def buildRigsForAllUnits(self):
        r"""
            ユニットに属する全てのコントローラのビルドを行う。
        """
        core.createRigForAllUnit(False)

    def setup(self):
        r"""
            セットアップを行う上書き用メソッド。
        """
        self.buildRigsForAllUnits()

    def finalizeSetup(self):
        r"""
            セットアップのファイナライズ処理。
            このクラスではdisplay_ctrlがあれば、そのコントローラのjointDisplay
            アトリビュートを１にセットする。
        """
        disp_ctrl = node.asObject('display_ctrl')
        if disp_ctrl:
            if self.lod() == 'high':
                disp_ctrl('lod', 1)
            disp_ctrl('jointDisplay', 1)

    def deleteUnusedTopNodes(self, *excludes):
        r"""
            root以外のトップノードを全て削除する。
            
            Args:
                *excludes (str):削除しないノード名のリスト
        """
        root = self.root()
        if root:
            if not root.name() in self.__topnodes:
                self.__topnodes.append(root.name())
        if excludes:
            excludes = list(excludes) + self.__topnodes
        else:
            excludes = self.__topnodes
        current_topnodes = cmds.ls(assemblies=True)
        for node in current_topnodes:
            if not node in excludes:
                cmds.delete(node)

    def postProcessForLOD(self):
        r"""
            各LOD用の後処理を行う上書き用メソッド。
        """
        pass

    def postProcess(self):
        r"""
            後処理を行う。
        """
        root = self.root()
        self.connectToBindJoint()
        if root:
            root.setupGroup()('display', 0)
            dsp_set = root.allSet().displaySet()
            disp_ctrl = root.ctrlGroup().displayCtrl()
            if disp_ctrl:
                jnt_set = dsp_set.addSet('baseJoint')
                jnt_set.addChild(root.baseJointGroup().worldTransform())
                disp_ctrl.attr('jointDisplay') >> jnt_set.attr('displayType')

        self.loadControllerCurves()
        self.postProcessForLOD()
        self.storeDefaultToAllControllers()
        if not self.isDebugMode():
            self.lockControllersColor()
        cleanup.deleteDagPoses()

    def finished(self):
        r"""
            終了処理。クリーンナップやUndoQueueの整理などを行う。
        """
        self.deleteUnusedTopNodes()
        if not self.__temp_ctrl_grp.hasChild():
            self.__temp_ctrl_grp.delete()
        if not self.isDebugMode():
            self.lockLockedListNodes()
            self.lockControllersColor()
        root = self.root()
        if root:
            cmds.select(root(), r=True)
        cmds.dgdirty(a=True)
        cmds.flushUndo()

    def execute(self):
        r"""
            実行メソッド。
            リギング実行時はこのメソッドがUIから呼ばれる。
            基本的に末端ユーザーはこのメソッドを使用することはない。
            プロセスの実行順番はクラスのメンバ変数ProcessListの順に実行され、
            各プロセスの実行前・実行後に同名にメソッドがextraConstructorから
            実行される。
        """
        global LatestExecutedConstructor
        LatestExecutedConstructor = self
        import time
        starttime = time.time()

        print('# Start to setup.')
        self.loadSettings()
        self.initialize()
        self.printProgress('Done to initialize.', 2)

        for process, pre_comment, post_comment in self.ProcessList:
                if pre_comment:
                    self.printProgress(pre_comment)
                self.extraConstructorManager().executeMethod('_'+process)
                if hasattr(self, process):
                    getattr(self, process)()
                self.extraConstructorManager().executeMethod(process)
                if post_comment :
                    self.printProgress(post_comment , 2)
    
        endtime = time.time()
        print('')
        print('/' * 80)
        print('Construction was done : %s' % self.lod())
        print('   Setup time : %s' % round((endtime - starttime), 2))
        print('/' * 80)    
        return


class McpConstructor(BasicConstructor):
    r"""
        MCP用のアセットを作成するためのコンストラクタ。
        ただしこちらは仮バージョンのためあまり汎用性はない。
        使用するにはBasicHumanのリグモジュールを使用している必要がある。
        いつか正式版を出したい・・・
    """
    Lod = 'LL'
    ProcessList = (
        ('preProcess', 'Start to Pre Process.', 'Pre Process was done.'),
        ('importJoints', 'Import joints.', 'Done to import.'),
        ('importLowModels', 'Import models.', 'Done to import models.'),
        ('finalizeBaseJoints', None, None),
        ('setupSystem', 'Setup system.', 'Done to setup system.'),
        ('preSetup',  'Start pre setup.', 'Done.'),

        ('convertHumanIkJoint',  'Converting joint for humanIK.', 'Done.'),
        ('parentLowGeometry',  'Parent geometry to human IK joint.', 'Done.'),
        ('finalizeSetup',  'Finalize human IK joint.', 'Done.'),

        ('postProcess', 'Start post process.', 'Done.'),
        ('finished', None, None),
    )
    def __init__(self):
        super(McpConstructor, self).__init__()
        self.__converter = ''

    def importLowModels(self):
        r"""
            ローモデルを読み込む
        """
        self.importModels('low', calcBb=False)

    def convertHumanIkJoint(self):
        r"""
            ジョイントをHumanIK用のものに変換する。
        """
        from gris3 import toHumanIK
        verutil.reload_module(toHumanIK)
        self.__converter = toHumanIK.HumanIK()
        self.__converter.convert()

    def converter(self):
        r"""
            HumanIK用のコンバータークラスのインスタンスを返す。
            
            Returns:
                gris3.toHumanIK.HumanIK:
        """
        return self.__converter

    def parentLowGeometry(self):
        r"""
            命名規則の変換を行いつつHumanIK用の骨にモデルをペアレントする。
        """
        from gris3 import toHumanIK
        toHumanIK.parentMCPGeometry()

    def finalizeSetup(self):
        r"""
            コンバーターによるファイナライズを行う。
            
            Returns:
                bool:
        """
        if not self.converter():
            return False
        self.converter().finalize()
        return True

    def postProcess(self):
        r"""
            後処理を行う上書き用メソッド。
        """
        pass

    def finished(self):
        r"""
            修了後の処理。rootを削除する。
        """
        references = cmds.ls('*:reference')
        self.deleteUnusedTopNodes(*references)
        cmds.delete('root')
        if references:
            cmds.select(
                cmds.listRelatives(references, ad=True), references,
                r=True
            )


def currentConstructor(isReload=False, name=None):
    r"""
        現在のファクトリ設定に基づいたコンストラクタを返す。
        nameに任意の名前を入れるとその名前のオブジェクトを返す。
        Noneの場合はConstructorクラスを返す。
        
        Args:
            isReload (bool):モジュールをリロードするかどうか
            name (str):モジュールから読み込むコンストラクタ名
            
        Returns:
            function:
    """
    from gris3 import factoryModules
    cm = ConstructorManager()
    fs = factoryModules.FactorySettings()
    constructor_name = fs.constructorName()
    constructor = cm.module(constructor_name)

    if isReload:
        verutil.reload_module(constructor)
    if name is None:
        return constructor.Constructor
    return getattr(constructor, name)
