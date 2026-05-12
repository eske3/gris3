#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Grisの設定全般を取扱うクラスを提供するモジュール
    
    Dates:
        date:2017/07/08 5:34[Eske](eske3g@gmail.com)
        update:2021/08/03 08:15 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
from abc import ABCMeta, abstractmethod
import json
from .. import xmlUtil, lib, fileUtil


class AbstractPref(object):
    r"""
        サブカテゴリのXMLプレファレンスを取扱う抽象クラス。
    """
    __metaclass__ = ABCMeta
    def __init__(self, prefdir):
        r"""
            初期化を行う。
            
            Args:
                prefdir (str):プレファレンスディレクトリのパス
        """
        self.__prefpath = os.path.join(
            prefdir, self.fileName()+'.'+self.extension()
        )
        self.setup()

    def setup(self):
        r"""
            __init__後に呼ばれる再実装専用、セットアップメソッド。
        """
        pass

    @abstractmethod
    def fileName(self):
        r"""
            プレファレンスのファイル名を返す。(拡張子は不要）
            
            Returns:
                str:
        """
        return ''

    @abstractmethod
    def extension(self):
        r"""
            取扱う拡張子を返す。
            
            Returns:
                str:
        """
        return ''

    def prefFile(self):
        r"""
            捜査対象となる設定ファイルのパスを返す。
            
            Returns:
                str:
        """
        return self.__prefpath

    @abstractmethod
    def root(self):
        r"""
            設定ファイルのルートデータを返す
            
            Returns:
                any:
        """
        return

    def setupSave(self, data):
        r"""
            save内でファイルの保存実行前に呼ばれるメソッド。
            戻り値として引数dataを加工したものを返す。
            
            Args:
                data (various):
                
            Returns:
                various:
        """
        pass

    @abstractmethod
    def save(self):
        r"""
            設定ファイルを保存する。
            
            Returns:
                any:
        """
        return


class AbstractXmlPref(AbstractPref):
    r"""
        サブカテゴリのXMLプレファレンスを取扱う抽象クラス。
    """
    def setup(self):
        r"""
            初期化行う。
        """
        self.__xmlobj = None

    @abstractmethod
    def fileName(self):
        r"""
            プレファレンスのファイル名を返す。(拡張子は不要）
            
            Returns:
                str:
        """
        return ''

    def extension(self):
        r"""
            取扱う拡張子を返す。
            
            Returns:
                str:
        """
        return 'xml'

    def root(self):
        r"""
            設定ファイルのXMLオブジェクトのルートデータを返す。
            
            Returns:
                xmlUtil.Xml:
        """
        if not self.__xmlobj:
            self.__xmlobj = xmlUtil.createXmlTree(
                self.prefFile(), self.fileName()
            )
        return self.__xmlobj.root()

    def save(self):
        r"""
            設定の保存を行う。
        """
        if not self.__xmlobj:
            return
        self.setupSave(self.__xmlobj)
        self.__xmlobj.saveFile()


class AbstractJsonPref(AbstractPref):
    r"""
        サブカテゴリのjsonプレファレンスを取扱う抽象クラス。
    """
    __metaclass__ = ABCMeta
    def setup(self):
        r"""
            初期化を行う。
        """
        self.__data = None

    @abstractmethod
    def fileName(self):
        r"""
            プレファレンスのファイル名を返す。(拡張子は不要）
            
            Returns:
                str:
        """
        return ''

    def extension(self):
        r"""
            取扱う拡張子を返す。
            
            Returns:
                str:
        """
        return 'json'

    def root(self):
        r"""
            ルートデータを返す。
            
            Returns:
                dict:
        """
        if not self.__data:
            if os.path.exists(self.prefFile()):
                try:
                    with open(self.prefFile(), 'r') as f:
                        self.__data = json.loads(f.read())
                except Exception as e:
                    self.__data = {}
            else:
                self.__data = {}
        return self.__data

    def save(self):
        r"""
            設定の保存を行う。
        """
        if not self.__data:
            return
        data = self.setupSave(self.__data)
        with open(self.prefFile(), 'w') as f:
            jsondata = json.dumps(self.__data, ensure_ascii=False, indent=4)
            f.write(lib.encode(jsondata))


class ProjectHistory(AbstractJsonPref):
    r"""
        プロジェクトの設定履歴を管理するクラス。
    """
    def fileName(self):
        r"""
            プレファレンスのファイル名を返す。(拡張子は不要）
            
            Returns:
                str:
        """
        return 'projectHistory'

    def limit(self):
        r"""
            ファイル履歴を保持する最大数を返す。
            デフォルトは20
            
            Returns:
                int:
        """
        root = self.root()
        return root.setdefault('limit', 50)

    def setLimit(self, limit):
        r"""
            ファイル履歴を保持する最大数を指定する。
            
            Args:
                limit (int):
                
            Returns:
                any:
        """
        root = self.root()
        if limit < 1:
            raise ValueError('The limit of history must be greater than 1.')
        root['limit'] = int(limit)

    def addPath(self, path):
        r"""
            パスの履歴を追加する。
            
            Args:
                path (str):
                
            Returns:
                any:
        """
        path = fileUtil.toStandardPath(path)
        root = self.root()
        histories = root.setdefault('histories', [])
        if path in histories:
            del histories[histories.index(path)]
        histories.append(path)

    def pathes(self):
        r"""
            パスの履歴を参照する。(ないパスは省略する）
            
            Returns:
                list:
        """
        root = self.root()
        return [
            x for x in root.setdefault('histories', [])
            if os.path.exists(x)
        ]

    def setupSave(self, data):
        r"""
            履歴の保存最大数を設定する。
            
            Args:
                data (dict):
                
            Returns:
                dict:
        """
        limit = data.setdefault('limit', 50)
        histories = self.pathes()
        num = len(histories)
        if num > limit:
            histories = histories[num-limit:]
            data['histories'] = histories
        return data


class AppRelations(AbstractJsonPref):
    r"""
        プロジェクトの設定履歴を管理するクラス。
    """
    def fileName(self):
        r"""
            プレファレンスのファイル名を返す。(拡張子は不要）
            
            Returns:
                str:
        """
        return 'appRelations'

    def addRelation(self, command, extensions):
        r"""
            enter description
            
            Args:
                command (any):enter description
                extensions (any):enter description
        """
        root = self.root()
        

class GlobalPref(object):
    r"""
        Grisの全般設定を持つシングルトンクラス
    """
    PrefFileName = 'globalSettings.xml'
    SubPrefs = {
        'projectHistory' : ProjectHistory,
        'appRelations' : AppRelations,
    }
    def __new__(cls):
        r"""
            シングルトン化を行う。
            
            Returns:
                GrisGlobalPref:
        """
        if hasattr(cls, '__instance__'):
            return cls.__instance__
        obj = super(GlobalPref, cls).__new__(cls)
        cls.__instance__ = obj
        # ユーザー設定の設定。=================================================
        path = os.environ.get('GRIS_PREF_PATH')
        if not path:
            path = os.environ['HOME']
        obj.__prefdir = os.path.join(path, 'grisPrefs')
        if not os.path.exists(obj.__prefdir):
            os.makedirs(obj.__prefdir)

        # サブのプレファレンスの初期化を行う。
        obj.__subprefs = {
            name:typeobj(obj.__prefdir)
            for name, typeobj in cls.SubPrefs.items()
        }
        # =====================================================================

        # 全体設定の読み込み。=================================================
        obj.__pref_obj = xmlUtil.Xml(
            os.path.join(os.path.dirname(__file__), cls.PrefFileName)
        )
        obj.__constructors = {}
        obj.__rig_units = {}
        obj.__factories = {}
        if not obj.__pref_obj.isLoaded():
            return obj
        root = obj.__pref_obj.root()
        if root.tag != 'grisPref':
            return obj

        for tag, datalist in (
            ('constructorPrefix',  obj.__constructors),
            ('rigUnitPrefix',  obj.__rig_units),
            ('factoryModules',  obj.__factories),
        ):
            for e in root.listchildren(tag):
                prefix = e.text()
                mod = lib.importModule(prefix)
                if not mod:
                    continue
                f, ext = os.path.splitext(mod.__file__)
                # モジュールがパッケージではない場合はスルーする。
                if not ext.lower() in ('.py', '.pyc'):
                    continue
                rootpath = os.path.dirname(f)
                datalist[prefix] = rootpath
        # =====================================================================
        return obj

    def listConstructorPrefix(self):
        r"""
            ユーザー定義のコンストラクタのプレフィックスとパスを返す
            
            Returns:
                list:(プレフィックス、ルートパス)
        """
        return self.__constructors.items()

    def listRigUnitPrefix(self):
        r"""
            ユーザー定義のリグスクリプトのプレフィックスとパスを返す
            
            Returns:
                list:(プレフィックス、ルートパス)
        """
        return self.__rig_units.items()

    def listFactoryModules(self):
        r"""
            ユーザー定義のFactoryModuleのプレフィックスとパスを返す
            
            Returns:
                list:(プレフィックス、ルートパス)
        """
        return self.__factories.items()

    def prefdir(self):
        r"""
            プレファレンス保存先のディレクトリパスを返す。
            
            Returns:
                str:
        """
        return self.__prefdir

    def preffile(self):
        r"""
            プレファレンスファイル(xml)のパスを返す。
            
            Returns:
                str:
        """
        return os.path.join(self.prefdir(), self.PrefFileName)

    def subPref(self, category):
        r"""
            指定されたcategory設定クラスを返す。
            
            Args:
                category (str):
                
            Returns:
                XmlPref:
        """
        return self.__subprefs.get(category)

    def subPrefDir(self, *subpath):
        r"""
            全体設定のプレファレンスディレクトリ内にある、subpathで指定したサブディレクトリパスを返す。
            その際、指定されたディレクトリが無い場合は作成してからパスを返す。
            
            Args:
                subpath (str):サブディレクトリ階層のリスト
                
            Returns:
                str:プレファレンスのサブディレクトリパス
        """
        dir_path = os.path.join(self.prefdir(), *subpath)
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)
        return dir_path


def addPathToHistory(path, limit=None):
    r"""
        プロジェクト履歴に任意のパスを追加する。
        limitに任意の整数を設定すると、履歴を保持する上限に変更が加えられる。
        
        Args:
            path (str):履歴に追加するパス
            limit (int):履歴保持上限数
    """
    pref = GlobalPref().subPref('projectHistory')
    limit = limit if limit else pref.limit()
    pref.setLimit(limit)
    pref.addPath(path)
    pref.save()
