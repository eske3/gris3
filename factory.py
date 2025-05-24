#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Factoryのデータを取扱うクラスを提供するモジュール。
    
    Dates:
        date:2017/07/08 8:23[Eske](eske3g@gmail.com)
        update:2020/10/20 05:56 eske yoshinob[eske3g@gmail.com]
        
    Brief:
        こちらのモジュールではfactoryModules内のものより、より低レベルな
        
        クラスを提供する。
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
import inspect
from gris3 import lib, xmlUtil

class ProjectSettingError(Exception):
    r"""
        プロジェクト設定を失敗したときに返す例外クラス。
    """
    pass

class ModuleInfo(object):
    r"""
        FactorySettings内で各モジュールの情報を保持するためのクラス。
    """
    def __init__(self, moduleName, name, alias, tag=''):
        r"""
            Args:
                moduleName (str):モジュール名
                name (str):操作対象ディレクトリ名
                alias (str):UI上での名前
                tag (str):振り分け用のタグ
        """
        self.__modulename = moduleName
        self.__name = name
        self.__alias = alias
        self.__tag = tag

    def __repr__(self):
        r"""
            表示名のオーバーライド。
            
            Returns:
                str:
        """
        return '<%s : "%s" / "%s" / "%s" / "%s">' % (
            str(self.__class__).split("'")[1],
            self.__modulename, self.__name, self.__alias, self.__tag
        )

    def moduleName(self):
        r"""
            モジュール名を返す。
            
            Returns:
                str:
        """
        return self.__modulename

    def name(self):
        r"""
            モジュールが管理するディレクトリの相対パスを表す文字
            
            Returns:
                str:
        """
        return self.__name

    def alias(self):
        r"""
            モジュールの別名を返す。
            
            Returns:
                str:
        """
        return self.__alias

    def tag(self):
        r"""
            Constructorで使用する際の振り分け用のタグを返す。
            
            Returns:
                str:
        """
        return self.__tag

class FactoryData(object):
    r"""
        Factoryの設定を保持・参照できる機能を提供するクラス。
    """
    TagName = 'grisFactoryWorkspace'
    def __init__(self):
        self.__rootpath = ''
        self.__xml_name = self.TagName + '.xml'
        self.__xml_obj = None

    def setRootPath(self, rootpath):
        r"""
            プロジェクトルートを設定するメソッド。
            
            Args:
                rootpath (str):ルートパス（ディレクトリパス）
        """
        if not os.path.isdir(rootpath):
            raise IOError('The root path must be a directory.')
        self.__rootpath = rootpath
        self.__xml_obj = None

    def rootPath(self):
        r"""
            プロジェクトルートを返すメソッド。
            
            Returns:
                str:： プロっジェクトのルートパス。
        """
        return self.__rootpath

    def subDirPath(self, *dirNames):
        r"""
            プロジェクトルートからの相対パスを引数として渡すとフルパスを返す。
            
            Args:
                *dirNames (tuple):
                
            Returns:
                str:
        """
        path = [self.rootPath()]
        path.extend(dirNames)
        return os.path.join(*path)

    def setXmlName(self, xmlName):
        r"""
            設定ファイルとなるXMLファイルを指定するメソッド。
            基本的には内部仕様専用。
            
            Args:
                xmlName (str):XMLファイル名。
        """
        self.__xml_name = xmlName

    def xmlName(self):
        r"""
            設定ファイルとなるXMLファイルの名前を返すメソッド。
            
            Returns:
                str:
        """
        return self.__xml_name

    def xmlPath(self):
        r"""
            設定ファイルとなるXMLパスを返すメソッド。
            
            Returns:
                str:
        """
        return os.path.join(self.rootPath(), self.xmlName())

    def xmlObject(self, new=False):
        r"""
            設定ファイルとなるXMLオブジェクトを返すメソッド。
            
            Args:
                new (bool):強制的に新規で作成するかどうか
                
            Returns:
                xmlUtil.Xml:
        """
        if self.__xml_obj and not new:
            return self.__xml_obj
        self.__xml_obj = None
        xml = xmlUtil.createXmlTree(self.xmlPath(), self.TagName, new=new)
        if not xml or not xml.isLoaded():
            return
        if xml.root().tag != self.TagName:
            return
        self.__xml_obj = xml
        return self.__xml_obj

    def getElement(self, tag):
        r"""
            設定ファイルのXMLファイルから、tagで指定した要素を返す。
            指定した要素がない場合は、そのタグの要素を追加してから返す。
            
            Args:
                tag (str):
                
            Returns:
                xmlUtil.XmlElement:
        """
        xml = self.xmlObject()
        if not xml:
            return
        root = xml.root()
        elements = root.listchildren(tag)
        if elements:
            return elements[0]
        return root.addChild(tag)

    def listModulesAsDict(self):
        r"""
            モジュールのリストを辞書型に格納して返すメソッド。
            
            Returns:
                dict:
        """
        xml = self.xmlObject()
        result = {}
        if not xml:
            return result

        for child in xml.root().listchildren('module'):
            name = child.get('name', '')
            if not name:
                continue
            alias = child.get('alias', '')
            tag = child.get('tag', '')

            info = ModuleInfo(name, child.text(), alias, tag)
            if name in result:
                result[name].append(info)
            else:
                result[name] = [info]
        return result

    def clearModules(self):
        r"""
            モジュールの情報を持つxmlからモジュールの情報をクリアする
        """
        root = self.xmlObject().root()
        for element in root.listchildren('module'):
            root.remove(element)

    def addModule(self, name, data):
        r"""
            モジュール情報を持つxmlにモジュールの情報を追加する。
            
            Args:
                name (str):
                data (ModuleInfo):
        """
        root = self.xmlObject().root()
        child = root.addChild('module', name=name)
        if data.tag():
            child.set('tag', data.tag())
        else:
            child.removeAttr('tag')
            
        if data.alias():
            child.set('alias', data.alias())
        else:
            child.removeAttr('alias')
            
        child.setText(data.name())

    def _getInfo(self, tag, withTest=True):
        r"""
            xmlファイルの情報からtagで指定された情報を返す。
            
            Args:
                tag (str):
                withTest (bool):
                
            Returns:
                str:
        """
        child = self.getElement(tag)
        text = child.text()
        if withTest and not text:
            raise ProjectSettingError('No %s name is specified.' % tag)
        return text

    def setConstructorName(self, constructorName):
        r"""
            constructor名をセットする。
            
            Args:
                constructorName (str):
        """
        child = self.getElement('constructor')
        child.setText(constructorName)

    def constructorName(self, withTest=True):
        r"""
            constructor名を返す。
            withTestがTrueで返す値が空文字の場合エラーを送出する。
            
            Args:
                withTest (bool):テストするかどうか
                
            Returns:
                str:
        """
        return self._getInfo('constructor', withTest)

    def setAssetName(self, assetName):
        r"""
            アセット名をセットする
            
            Args:
                assetName (str):
        """
        child = self.getElement('assetName')
        child.setText(assetName)

    def assetName(self, withTest=True):
        r"""
            アセット名を返す。
            withTestがTrueで返す値が空文字の場合エラーを送出する。
            
            Args:
                withTest (bool):テストするかどうか
                
            Returns:
                str:
        """
        return self._getInfo('assetName', withTest)

    def setAssetType(self, assetType):
        r"""
            アセットタイプをセットする。
            
            Args:
                assetType (str):
        """
        root = self.xmlObject().root()
        child = self.getElement('assetType')
        child.setText(assetType)

    def assetType(self, withTest=True):
        r"""
            アセットタイプを返す。
            
            Args:
                withTest (bool):テストするかどうか
                
            Returns:
                str:
        """
        return self._getInfo('assetType', withTest)

    def setProject(self, project):
        r"""
            プロジェクト名をセットする。
            
            Args:
                project (str):プロジェクト名
        """
        root = self.xmlObject().root()
        child = self.getElement('project')
        child.setText(project)

    def project(self, withTest=True):
        r"""
            Project名を返す。
            
            Args:
                withTest (bool):テストするかどうか
                
            Returns:
                str:
        """
        return self._getInfo('project', withTest)

    def assetPrefix(self):
        r"""
            スクリプト保存フォルダの名前を生成する。
            
            Returns:
                str:
        """
        return  '{}_{}{}{}'.format(
            self.project(), self.assetType(), self.assetName(), 'RiggingScript'
        )

    def saveFile(self):
        r"""
            設定をXMLファイルへ保存する。
        """
        self.xmlObject().saveFile()

    def setupPath(self):
        import sys
        path = self.rootPath()
        if path in sys.path:
            return
        sys.path.append(path)
        print('[Constructor Path] Add script path : %s' % path)

    def importScriptModule(self, name, isReload=False):
        r"""
            このプロジェクトディレクトリ内にある、リグビルド用スクリプトを
            インポートする。
            
            Args:
                name (str):スクリプト名
                isReload (bool):スクリプトをリロードするかどうか
                
            Returns:
                module:
        """
        from . import factoryModules
        self.setupPath()
        with factoryModules.startManualy(self):
            mod = lib.importModule(self.assetPrefix()+'.'+name)
            if isReload:
                reload(mod)
        return mod

    def listScripts(self, isReload=False):
        r"""
            このプロジェクトディレクトリ内にある、リグビルド用スクリプトの
            一覧をリストで返す。
            
            Args:
                isReload (bool):スクリプトをリロードするかどうか
                
            Returns:
                list:
        """
        script_dir = os.path.join(self.rootPath(), self.assetPrefix())
        if not os.path.isdir(script_dir):
            return
        modules = list(set([x.split('.')[0] for x in os.listdir(script_dir)]))
        result = []
        for mod_name in modules:
            mod = self.importScriptModule(mod_name, isReload)
            if not 'Constructor' in dir(mod):
                continue
            result.append(mod_name)
        return result

    def execScript(self, scriptName, isDebugMode=False, isReload=False):
        r"""
            リグビルド用のスクリプトを実行する。
            引数scriptNameに使用できる文字列はlistScriptsの戻り値によって
            得られるリストのいずれか。
            
            Args:
                scriptName (str):実行するスクリプト
                isDebugMode (bool):デバッグモードかどうか
                isReload (bool):スクリプトをリロードするかどうか
        """
        mod = self.importScriptModule(scriptName, isReload)
        from . import factoryModules
        with factoryModules.startManualy(self):
            c = mod.Constructor()
            c.execute()

def createFactoryDirectory(factotySettings):
    r"""
        引数factotySettingsからディレクトリを作成する
        
        Args:
            factotySettings (factoryModules.FactorySettings):
    """
    root = factotySettings.rootPath()
    directory_list = [factotySettings.assetPrefix()]

    for dirnames in factotySettings.listModulesAsDict().values():
        directory_list.extend([x.name() for x in dirnames])

    directories = [
        os.path.normpath(os.path.join(root, x)) for x in directory_list
    ]
    creating_directories = []
    for d in directories:
        if os.path.isfile(d) or os.path.islink(d):
            raise IOError(
                'A directory name "" is already exists as file.' % (
                    os.path.basename(d)
                )
            )
        if not os.path.isdir(d):
            creating_directories.append(d)
    # =========================================================================

    if not creating_directories:
        return

    # ディレクトリを作成する。=================================================
    print('# '.ljust(80, '='))
    print('# Create factory directories in')
    print('    '+root)
    for d in creating_directories:
        if not os.path.isdir(d):
            os.makedirs(d)
            print('    created : ' + d)
    print('# '.ljust(80, '='))
    # =========================================================================