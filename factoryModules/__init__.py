#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    FactoryのDepartment（部署）を定義するための機能を提供するモジュール。
    gris3.factoryモジュール内のクラスよりもGUI向けに再構成されている。
    コマンドのみで操作を行う場合はgrid3.factoryモジュールを使用する。
    
    Dates:
        date:2017/01/21 12:04[Eske](eske3g@gmail.com)
        update:2021/02/09 20:15 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os, inspect
from .. import lib, uilib, factory, settings, verutil
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

ModuleInfo = factory.ModuleInfo

# /////////////////////////////////////////////////////////////////////////////
# Factoryに関する情報を格納、制御するクラスおよび関数。                      //
# /////////////////////////////////////////////////////////////////////////////
class startManualy(object):
    r"""
        通常FactorySettingsはシングルトンインスタンスだが、このクラスを使用して
        with文を通すと、その中では引数factoryDataが返ってくるように変更できる。
        これはConstructorManagerなど一部のクラスがFactorySettingsを呼びに行く際
        に、任意のファクトリーセッティングを使用させる際に使用する。
    """
    def __init__(self, factoryData):
        r"""
            Args:
                factoryData (factory.FactoryData):使用するFactoryData
        """
        self.__data = factoryData

    def __enter__(self):
        if not isinstance(self.__data, factory.FactoryData):
            raise ValueError(
                (
                    '[Factory]The given obj must be type "factory.FactoryData"'
                    ' to starting manualy of Factory Settings.'
                    'Given "%s".'
                ) % (self.__data)
            )
        FactorySettings.ManualConstructor = self.__data
        
    def __exit__(self, exe_type, exc_value, traceback):
        r"""
            Args:
                exe_type (any):
                exc_value (any):
                traceback (any):
        """
        self.__data = None
        FactorySettings.ManualConstructor = None
        return False


class FactorySettingsMeta(uilib.QtSingletonMeta):
    def __new__(cls, name, objects, dict=None):
        r"""
            Args:
                name (str):クラス名
                objects (tuple):親クラスのtuple
                dict (dict):アトリビュートのリスト
        """
        dict = dict or {}
        dict['ManualConstructor'] = None
        return super(FactorySettingsMeta, cls).__new__(
            cls, name, objects, dict
        )

    def __call__(self, *args, **keywords):
        r"""
            シングルトン制御ならびに、このメタクタスを使用したクラスに
            ManualConstructorアトリビュートがある場合でかつその中身が空では
            ない場合はそのオブジェクトを返す仕様に変更する。

            Args:
                *args (tuple):
                **keywords (dict):
        """
        if self.ManualConstructor:
            return self.ManualConstructor
        return super(FactorySettingsMeta, self).__call__(*args, **keywords)


class FactorySettingsSingletonObject(
    FactorySettingsMeta('FactorySettingsSingleton', QtCore.QObject)
):
    r"""
        シングルトン制御と特殊処理を行うためのメタクラスを持つ
        QObjectのサブクラス。
        FactorySettingsクラスで多重継承する必要から作成しており、ここでしか使用
        していない。
    """
    pass


class FactorySettings(FactorySettingsSingletonObject, factory.FactoryData):
    r"""
        Factoryの設定を保持・参照できる機能を提供するクラス。
        FactoryDataクラスにQtとの連携機能を追加している。
        このクラスはシングルトンであり、様々なところからアクセスできるように
        なっている。
    """
    isChanged = QtCore.Signal()
    def __init__(self):
        FactorySettingsSingletonObject.__init__(self)
        factory.FactoryData.__init__(self)

    def setRootPath(self, rootpath, emitSignal=True):
        r"""
            プロジェクトルートを設定するメソッド。
            ルート設定後はisChangedシグナルを送出するが、emitSignalフラグを
            Falseにした場合は送出しない。ただし、こちらはUIの挙動に影響する
            可能性があるので、慎重に行うこと。
            
            Args:
                rootpath (str):ルートパス（ディレクトリパス）
                emitSignal (bool):
        """
        super(FactorySettings, self).setRootPath(rootpath)
        if emitSignal:
            self.isChanged.emit()

    def updateRootPath(self):
        r"""
            現在のルートパスのままパス変更通知のシグナルを送るメソッド。
        """
        self.isChanged.emit()

    def listModules(self):
        r"""
            FactoryModuleManagerと照合して、該当するモジュールを返す。
            リストを返し、そのリスト内には適切な設定がされた各該当モジュールが
            格納されている。
            
            Returns:
                list:
        """
        fmm = FactoryModuleManager()

        modulelist = fmm.moduleNameList()
        result = []
        for module_name, datalist in self.listModulesAsDict().items():
            for data in datalist:
                module = modulelist.get(module_name)
                if not module:
                    continue

                root_path = os.path.join(self.rootPath(), data.name())
                obj = module()
                obj.setRootPath(root_path)
                if data.alias():
                    obj.setAliasName(data.alias())
                result.append(obj)

        return result

    def settingTest(self):
        r"""
            設定がすべてセットされているかどうかをboolで返す。
            
            Returns:
                bool:
        """
        if not self.xmlObject():
            print('[Factory Setting Test WARNING] xmlObject was not found.')
            return False
        
        if not self.listModules():
            print('[Factory Setting Test WARNING] module was not found.')
            return False

        if not self.assetName(False):
            print('[Factory Setting Test WARNING] asset name was not found.')
            return False
        if not self.assetType(False):
            print('[Factory Setting Test WARNING] asset type was not found.')
            return False
        if not self.project(False):
            print('[Factory Setting Test WARNING] project was not found.')
            return False
        if not self.constructorName(False):
            print(
                '[Factory Setting Test WARNING] constructor name '
                'was not found.'
            )
            return False
        return True


def createFactoryDirectory():
    r"""
        現在設定されているFactorySettingsからディレクトリを作成する
    """
    fs = FactorySettings()
    root = fs.rootPath()
    if not os.path.isdir(root):
        raise IOError('A factory directory does not exist.')
    if not fs.settingTest():
        raise RuntimeError('The factory settings is not enough.')
    
    factory.createFactoryDirectory(fs)
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////


class AbstractFactoryTabMixin(object):
    r"""
        Factory内のタブを定義する際に使用する、多重継承専用クラス。
        基本的に何らかのQWidgetとセットで継承する事。
        また、継承されたクラスの__init__内ではcustomInitメソッドを呼び出す
        ようにする事。
    """
    def customInit(self):
        r"""
            Factory内のタブ
        """
        self.__is_changed = True

    def setChangedSignal(self):
        r"""
            refreshメソッドが呼ばれた際にアップデートを促すためのフラグを立てる
        """
        self.__is_changed = True

    def refreshState(self):
        r"""
            UI構築後に、管理ウィジェットから更新が必要な時に呼びされる
            オーバーライド用メソッド。
        """
        pass

    def refresh(self, force=False):
        r"""
            強制的に更新をかける場合に呼ばれるメソッド。
            __is_changed変数Trueの場合（UIが構築済みの場合）のみrefreshStateを
            コールして、更新を促す。
            
            Args:
                force (bool):強制的に更新する。
        """
        if not force and not self.__is_changed:
            return
        self.__is_changed = False
        self.refreshState()


class AbstractDepartmentGUI(QtWidgets.QWidget):
    r"""
        Factory内に表示するGUIのベースを提供するクラス。
        AbstractDepartmentクラスのGUIメソッドでは、このクラスを継承した
        クラスを返すこと。
    """
    def __init__(self, workspaceDir, module, parent=None):
        r"""
            第１引数にはワークスペースとなるディレクトリパスが渡される。
            引数moduleには、このクラスを呼び出したAbstractDepartment
            クラスのインスタンが渡される。
            
            Args:
                workspaceDir (str):
                module (AbstractDepartment):
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(AbstractDepartmentGUI, self).__init__(parent)
        self.__workspace_dir = workspaceDir
        self.__module = module

    def workspaceDir(self):
        r"""
            作業ディレクトリのパスを返す。
            
            Returns:
                str:
        """
        return self.__workspace_dir

    def module(self):
        r"""
            登録されているデパートメントオブジェクトを返す。
            
            Returns:
                AbstractDepartment:
        """
        return self.__module

    def init(self):
        r"""
            代理初期化関数。
            このクラスを継承するクラスが初期化する際にはこちらのメソッドを
            使用する。
            このクラスを使用するfactoryモジュールのFactoryTabクラス内で
            必要な処理を行った後に、このメソッドが呼び出される。
        """
        pass
    
    def refreshState(self):
        r"""
            タブが選択された際に呼ばれる更新用の上書き専用メソッド。
            GUIの更新などに使用可能。
        """
        pass


class AbstractDepartment(object):
    r"""
        Factoryのセクションを定義する機能を提供するクラス。
    """
    def __init__(self):
        self.__directory_name = 'department'
        self.__root_path = ''
        self.__aliasname = ''
        self.__icon  = None
        self.init()

    def init(self):
        r"""
            初期化関数内で呼ばれるオーバーライド用メソッド。
        """
        pass

    def label(self):
        r"""
            Factoryのリストに表示されるときの名前を返すメソッド。
            
            Returns:
                str:
        """
        return 'Department'

    def setAliasName(self, name):
        r"""
            Factoryのリストに表示されるときのエイリアス名をセットする。
            
            Args:
                name (str):
        """
        self.__aliasname = name

    def listLabel(self):
        r"""
            Factoryのリストに表示されるときの名前を返すメソッド。
            UI内では実際にはこちらが呼ばれ、aliasがセットされている場合は
            エリアス名を、それ以外の場合はlabelメソッドが使用される。
            
            Returns:
                str:
        """
        return self.__aliasname if self.__aliasname else self.label()
      
    def icon(self):
        r"""
            Factory一覧に表示するアイコンパスを返す。
            このパスはモジュールと同一ディレクトリに"icon.png"があれば
            そのイメージを使用する。
            
            Returns:
                QtGui.QIcon:
        """
        if not self.__icon:
            iconpath = os.path.join(
                os.path.dirname(inspect.getfile(self.__class__)),
                'icon.png'
            )
            if not os.path.exists(iconpath):
                iconpath = uilib.IconPath('uiBtn_default')
            self.__icon = QtGui.QIcon(iconpath)
        return self.__icon

    def priority(self):
        r"""
            Factoryのリストに表示する際の優先度を返すメソッド。
            数字が高い方がリストの上に表示される。
            -1の場合はリストの下方へ回される。
            
            Returns:
                int:
        """
        return -1

    def directoryName(self):
        r"""
            操作対象ディレクトリ名を返すメソッド。
            このパラメータは呼び出し時に上書き可能。
            
            Returns:
                str:
        """
        return self.__directory_name

    def setDirectoryName(self, directoryName):
        r"""
            操作対象ディレクトリ名を設定するメソッド。
            
            Args:
                directoryName (str):ディレクトリ名
        """
        self.__directory_name = directoryName

    def setRootPath(self, rootPath):
        r"""
            ルートパスを設定するメソッド。
            基本的にこのメソッドはFactorySettingsクラスのlistModules内で呼ばれる。
            
            Args:
                rootPath (str):ルートパス（ディレクトリ）
        """
        self.__root_path = rootPath

    def rootPath(self):
        r"""
            設定されているルートパスを返すメソッド。
            
            Returns:
                str:
        """
        return self.__root_path

    def GUI(self):
        r"""
            Factoryで表示するGUI作成クラスを返すメソッド。
            返すのはクラスオブジェクトであり、インスタンスではないので注意。
            Noneを返す場合、FactoryではGUIを表示しない。
            
            Returns:
                AbstractDepartmentGUI:
        """
        return None


class FactoryModuleManager(object):
    r"""
        FactoryModule一覧を管理するクラス。
        モジュールリストはこのクラスの最初の生成時に作成されるが、このクラスは
        シングルトンなのでリストの更新を行うにはreloadメソッドを呼ぶ必要がある。
    """
    def __new__(cls):
        r"""
            初期化メソッド。シングルトン化の処理に使用。
            
            Returns:
                FactoryModuleManager:
        """
        if hasattr(cls, '__singleton'):
            return cls.__singleton
        cls.__singleton = super(FactoryModuleManager, cls).__new__(cls)
        cls.isFirstInitialization = True
        return cls.__singleton

    def reload(self, isReload=False):
        r"""
            モジュールリストを更新するメソッド。
            
            Args:
                isReload (bool):モジュールをリロードするかどうか。
        """
        self.__modulelist = {}
        p = settings.GlobalPref()
        pathlist = [
            (inspect.getmodule(self.__class__).__name__,
            os.path.dirname(__file__))
        ]
        pathlist += p.listFactoryModules()
        for mod_name, root in pathlist:
            for module in lib.loadPythonModules(root, mod_name, 1):
                if not 'Department' in dir(module):
                    continue
                if isReload:
                    verutil.reload_module(module)
                self.__modulelist[
                    module.__name__.split('.')[-1]
                ] = module.Department

    def __init__(self):
        r"""
            初期化時に一度だけモジュールリストが更新される。
        """
        if not self.isFirstInitialization:
            return
        self.isFirstInitialization = True
        self.reload()

    def moduleList(self):
        r"""
            モジュールリストを返すメソッド。
            
            Returns:
                list:
        """
        return list(self.__modulelist.values())[:]

    def sortedModuleList(self):
        r"""
            モジュールのリストを、priorityメソッド順に並べて返す。
            
            Returns:
                list:
        """
        d = {}
        for mod in self.__modulelist.values():
            p = mod.priority()
            if p in d:
                d[p].append(mod)
            else:
                d[p] = [mod]
        keys = list(d.keys())
        keys.sort()
        keys.reverse()
        result = []
        for key in keys:
            result.extend(d[key])

        return result

    def moduleNameList(self):
        r"""
            モジュール名をキーとしたモジュールの辞書を返す。
            
            Returns:
                dict:
        """
        result = {}
        for key in self.__modulelist:
            result[key] = self.__modulelist[key]
        return result