#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ここに説明文を記入
    
    Dates:
        date:2017/03/18 16:08[Eske](eske3g@gmail.com)
        update:2023/04/25 07:51 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
import json
import time
import codecs
import shutil
from abc import ABCMeta, abstractmethod
from gris3 import node, lib, verutil
Version = 0.5

def checkSelection():
    r"""
        ノードが選択されているかどうかを返す。
        
        Returns:
            bool:
    """
    return True if node.cmds.ls(sl=True) else False

class Namespace(object):
    r"""
        ネームスペース付きノード名を提供するクラス
    """
    def __init__(self, namespace):
        r"""
            Args:
                namespace (str):管理するネームスペース
        """
        self.__namespace =  namespace + ':' if namespace else ''

    def __call__(self, nodeName, attr=None):
        r"""
            引数nodeNameに設定されているネームスペースを付加して返す
            
            Args:
                nodeName (str):ノード名
                attr (str):アトリビュート名(任意)
                
            Returns:
                str:ネームスペース付きノード名
        """
        name = '|'.join([self.__namespace+x for x in nodeName.split('|')])
        return name + '.' + attr if attr else name
            

class AbstractDataManager(object):
    r"""
        選択されたノードのデータを書き出す機能を提供する抽象クラス
    """
    __metaclass__ = ABCMeta
    def __init__(self):
        self.setWorkDir('')
        self.setFileName()
        self.setDataName('')

    def setWorkDir(self, dirpath):
        r"""
            ワークディレクトリのパスをセットする。
            
            Args:
                dirpath (str):
        """
        self.__workdir = dirpath

    def workDir(self):
        r"""
            セットされたワークディレクトリのパスを返す。
            
            Returns:
                str:
        """
        return self.__workdir

    def setFileName(self, filename=''):
        r"""
            セーブするディレクトリ名を設定する。
            
            Args:
                filename (str):
        """
        self.__filename = filename

    def fileName(self):
        r"""
            セットされたセーブするディレクトリ名を返す。
            
            Returns:
                str:
        """
        return self.__filename

    def setDataName(self, name):
        r"""
            データ名をセットする。
            
            Args:
                name (str):
        """
        self.__dataname = name

    def dataName(self):
        r"""
            データ名を返す。
            
            Returns:
                str:
        """
        return self.__dataname

    @abstractmethod
    def writeMethod(self, selectedNodeList, rootdir):
        r"""
            書き込みを行うための実装を行う抽象メソッド。
            
            Args:
                selectedNodeList (list):
                rootdir (str):書き出し先のディレクトリパス。
        """
        pass

    def setupReading(self, namespaces, rootDir):
        r"""
            データ読み込み前に実行される、準備動作用のメソッド。
            このメソッドで返されたデータがreadMethodの第2引数に渡る。
            
            Args:
                namespaces (list):
                rootDir (str):読み込み元先のディレクトリパス。
                
            Returns:
                None:
        """
        return None

    @abstractmethod
    def readMethod(self, namespace, data):
        r"""
            データを読み込むための実装を行う抽象メソッド。
            
            Args:
                namespace (str):適応ネームスペース
                data (any):setupReadingの戻り値
        """
        pass

    @classmethod
    @abstractmethod
    def dataType(self):
        r"""
            クラスが取扱うデータタイプ文字列を返す抽象メソッド。
            
            Returns:
                str:
        """
        return ''

    def write(self, namespace, thumbnailPath, selectedNodeList):
        r"""
            書き込み実行を行うエントリメソッド。
            
            Args:
                namespace (str):データ元のネームスペース
                thumbnailPath (str):サムネイルのパス。
                selectedNodeList (list):
                
            Returns:
                str:
        """
        import getpass
        # データのチェック。===================================================
        workdir = self.workDir()
        filename = self.fileName()
        dataname = self.dataName()
        if not os.path.isdir(workdir):
            raise IOError('The directory to write data was not found.')
        if not filename:
            raise ValueError('No file name is specified.')
        if not dataname:
            raise ValueError('No data name is specified.')
        # =====================================================================

        # 継承クラスによるデータの書き出し。===================================
        rootdir = os.path.join(workdir, filename)
        if not os.path.exists(rootdir):
            os.makedirs(rootdir)
        self.writeMethod(selectedNodeList, rootdir)
        self.applyThumbnail(thumbnailPath, rootdir)
        # =====================================================================

        # メタデータの作成。===================================================
        meta_data = {
            'namespace':namespace, 'dataName':dataname,
            'creationTime':time.time(),
            'creator':getpass.getuser(), 'version':Version,
            'dataType':self.dataType()
        }
        with codecs.open(
            os.path.join(rootdir, 'meta.json'), 'wb', 'utf-8'
        ) as f:
            f.write(
                json.dumps(
                    meta_data, indent=4, sort_keys=True, ensure_ascii=False
                )
            )
        # =====================================================================

    @abstractmethod
    def applyThumbnail(self, thumbnailPath):
        r"""
            渡されたサムネイルファイルを任意の箇所に保存する。
            
            Args:
                thumbnailPath (str):サムネイルのパス。
        """
        pass

    def read(self, namespaces):
        r"""
            データを読み込む。
            
            Args:
                namespaces (list):対象ネームスペーススペースのリスト
        """
        workdir = self.workDir()
        filename = self.fileName()
        rootdir = os.path.join(workdir, filename)
        setup_data = self.setupReading(namespaces, rootdir)
        for ns in namespaces:
            self.readMethod(Namespace(ns), setup_data)

    def selectMethod(self, namespaces, setup_data):
        r"""
            任意のノードを選択する。
            
            Args:
                namespaces (list):
                setup_data (dict):
        """
        print('The operation "Select target" is not supported.')

    def selectTargetNode(self, namespaces):
        r"""
            捜査対象ノードを選択するエントリメソッド。
            下準備の後、selectMethodが呼ばれる。
            
            Args:
                namespaces (list):対象ネームスペーススペースのリスト
        """
        workdir = self.workDir()
        filename = self.fileName()
        rootdir = os.path.join(workdir, filename)
        setup_data = self.setupReading(namespaces, rootdir)
        self.selectMethod([Namespace(x) for x in namespaces], setup_data)


class PoseDataManager(AbstractDataManager):
    r"""
        選択されたノードのkeyableなアトリビュートを保存する
        機能を提供するクラス。
    """
    @classmethod
    def dataType(self):
        r"""
            このクラスがポーズを取扱うクラスである事を返す。
            
            Returns:
                str:
        """
        return 'pose'

    def writeMethod(self, selectedNodeList, rootdir):
        r"""
            各ノードのkeyableアトリビュートの値を書き出す。
            
            Args:
                selectedNodeList (list):
                rootdir (str):書き出し先のディレクトリパス。
        """
        posedata = {}
        for name, srcnode in selectedNodeList:
            keyable_attrs = srcnode.listAttr(k=True)
            datalist = {}
            for attr in keyable_attrs:
                datalist[attr.attrName()] = attr.get()
            posedata[name] = datalist

        with open(os.path.join(rootdir, 'pose.json'), 'w') as f:
            json.dump(
                posedata, f, sort_keys=True, indent=4, ensure_ascii=False
            )
        # スクリーンキャプチャの書き出し。
        # from gris3.uilib import mayaUIlib
        # mayaUIlib.write3dViewToFile(
            # os.path.join(rootdir, 'thumb.png'), 256, 256
        # )

    def applyThumbnail(self, thumbnailPath, rootdir):
        r"""
            渡されたサムネイルファイルを任意の箇所に保存する。
            
            Args:
                thumbnailPath (str):サムネイルのパス。
                rootdir (str):ワークディレクトリのパス。
        """
        shutil.move(
            thumbnailPath, os.path.join(rootdir, 'thumb.png')
        )
    
    def setupReading(self, namespaces, rootDir):
        r"""
            ポーズ情報のデータを読み込む
            
            Args:
                namespaces (list):適応対象ネームスペースのリスト
                rootDir (str):
                
            Returns:
                dict:
        """
        with open(os.path.join(rootDir, 'pose.json'), 'r') as f:
            posedata = json.load(f)
        return posedata

    def readMethod(self, namespaceObject, data):
        r"""
            あたえられたネームスペースオブジェクトに対し、ポーズ
            をロードする
            
            Args:
                namespaceObject (Namespace):[]
                data (dict):
        """
        cmds = node.cmds
        for nodename, attrs in data.items():
            for attr, value in attrs.items():
                try:
                    cmds.setAttr(namespaceObject(nodename, attr), value)
                except:
                    pass

    def selectMethod(self, namespaceObjects, setup_data):
        r"""
            jsonファイルで指定されているノードを選択する。
            
            Args:
                namespaceObjects (list):Namespaceオブジェクトのリスト
                setup_data (dict):
        """
        cmds = node.cmds
        selection_list = []
        for ns in namespaceObjects:
            for nodename in setup_data.keys():
                n = ns(nodename)
                if cmds.objExists(n):
                    selection_list.append(n)
        if selection_list:
            cmds.select(selection_list, r=True, ne=True)


class FileDataList(object):
    r"""
        DataManagerで管理するmetaデータを元に、ファイル情報を
        持つ機能を提供するクラス。
    """
    def __init__(self, fileDataList, rootDir):
        r"""
            初期化を行う。第1引数はDataManager.metaDataの
            'fileData'キーのよって返されるリストデータ。
            
            Args:
                fileDataList (list):
                rootDir (str):
        """
        self.__datalist = fileDataList
        self.__rootdir = rootDir

    def __nonzero__(self):
        r"""
            データが空ならばFalseを返す。
            
            Returns:
                bool:
        """
        return True if self.__datalist else False

    def __iter__(self):
        r"""
            イテレータ。初期化時に与えらたfileDataListを返す。
            
            Returns:
                iter:
        """
        return self.__datalist.__iter__()

    def __getitem__(self, key):
        r"""
            fileDataListの任意の番号の辞書オブジェクトを返す。
            
            Args:
                key (slice):
                
            Returns:
                dict:
        """
        return self.__datalist[key]

    def rootDir(self):
        r"""
            セットされているルートディレクトリのパスを返す。
            
            Returns:
                str:
        """
        return self.__rootdir

    def tags(self):
        r"""
            タグの一覧を返す。
            一度実行すると、二度目移行はキャッシュ済みデータを返す。
            
            Returns:
                tuple:
        """
        from itertools import chain
        taglist = list(set(chain.from_iterable([x['tagList'] for x in self])))
        taglist.sort()
        taglist = tuple(taglist)
        return taglist

    def dataList(self, tagFilter=''):
        r"""
            データのリストを返す。tagFilterによりtagListによるフィルタが可能。
            
            Args:
                tagFilter (str):
                
            Returns:
                list:
        """
        datalist = []
        tagfilter_func = (
            (lambda x, y : x in y) if tagFilter else (lambda x, y : True)
        )
        for data in self:
            if not tagfilter_func(tagFilter, data['tagList']):
                continue
            datalist.append(data)
        return datalist

    def deleteData(self, fileName):
        r"""
            データをメタデータから削除するメソッド。
            
            Args:
                fileName (str):ファイルネーム
                
            Returns:
                bool:
        """
        for i, data in enumerate(self):
            if data['fileName'] == fileName:
                del self.__datalist[i]
                return True
        return False

    def findData(self, fileName):
        r"""
            与えれたファイル名を持つデータを返す。
            
            Args:
                fileName (str):
                
            Returns:
                dict:
        """
        for data in self:
            if data['fileName'] == fileName:
                return data

class GlobalDataManager(object):
    r"""
        データを統合管理するマネージャ。
        データの書き出しやメタデータの管理を行う。
    """
    RootDirectoryName = 'grisPrefs/grisAnimLibrary'
    DataManagers = {
        x.dataType() : x for x in [
            PoseDataManager
        ]
    }
    def __init__(self):
        self.__writer = None
        self.__rootdir = os.path.normpath(node.cmds.internalVar(uad=True))
        self.setTags('all')
        self.__cached_metadata = None
        self.__cached_filedata = None

    def setTags(self, *tags):
        r"""
            保存する際のタグを定義する。タグは複数定義可能。
            
            Args:
                *tags (any):
        """
        self.__tag = tags

    def tags(self):
        r"""
            定義されたタグのリストをtupleで返す。
            
            Returns:
                tuple:
        """
        return self.__tag

    def setRootDir(self, dirpath):
        r"""
            データを格納するルートディレクトリをセットする。
            
            Args:
                dirpath (str):
        """
        self.__rootdir = dirpath

    def rootDir(self):
        r"""
            データを格納するルートディレクトリを返す。
            デフォルトではMayaのアプリケーションディレクトリ直下。
            
            Returns:
                str:
        """
        return os.path.normpath(
            os.path.join(self.__rootdir, self.RootDirectoryName)
        )

    def setDataManager(self, writer):
        r"""
            書き出しに用いるwriterオブジェクトをセットする。
            
            Args:
                writer (AbstractDataManager):
        """
        if not isinstance(writer, tuple(self.DataManagers.values())):
            raise ValueError(
                'DataManager object must be a subclass of "%s".' % (
                    AbstractDataManager.__name__
                )
            )
        self.__writer = writer

    def writer(self):
        r"""
            書き出しに用いられるwriterオブジェクトを返す。
            
            Returns:
                AbstractDataManager:
        """
        return self.__writer

    @staticmethod
    def getSelectedList(targetNodes=None):
        r"""
            任意の指定したノードか選択ノードをネームスペースとノード名
            に分離する。
            
            Args:
                targetNodes (list):
                
            Returns:
                lib.ListDict:
        """
        nslist = lib.ListDict()
        selected = node.selected(targetNodes)
        if not selected:
            raise RuntimeError('No object was selected.')
        for n in selected:
            hir = n.split('|')
            h_nslist = []
            namelist = []
            for h in hir:
                splitted = h.split(':', 1)
                if len(splitted) == 1:
                    ns = ''
                    name = splitted[0]
                else:
                    ns, name = splitted
                namelist.append(name)
                h_nslist.append(ns)
            nslist[h_nslist[-1]] = ('|'.join(namelist),  n)
        return nslist

    def getSelected(self, targetNodes=None):
        r"""
            任意の指定したノードか選択ノードをネームスペースとノード名に
            分離する。
            ネームスペースが複数ある場合はエラーを返す。
            
            Args:
                targetNodes (list):
                
            Returns:
                tuple:
        """
        nslist = self.getSelectedList(targetNodes)
        if len(nslist) != 1:
            raise RuntimeError('More than 2 namespaces selected.')
        return (list(nslist.keys())[0], list(nslist.values())[0])

    def metaDataFile(self):
        r"""
            メタデータを格納するファイルパスを返す。
            
            Returns:
                str:
        """
        return os.path.join(self.rootDir(), 'meta.json')

    def metaData(self):
        r"""
            メタデータを返す。
            
            Returns:
                dict:
        """
        if self.__cached_metadata:
            return self.__cached_metadata

        metafile = self.metaDataFile()
        if not os.path.exists(metafile):
            return {}

        with codecs.open(metafile, 'r', 'utf-8') as f:
            try:
                self.__cached_metadata = json.load(f)
            except ValueError as e:
                self.__cached_metadata = {}
            except Exception as e:
                self.__cached_metadata = None
                raise e
        return self.__cached_metadata

    def writeMetaData(self, metaData):
        r"""
            与えられた辞書オブジェクトをメタデータとして書き出す。
            
            Args:
                metaData (dict):
        """
        metafile = self.metaDataFile()
        with codecs.open(metafile, 'wb', 'utf-8') as f:
            json.dump(metaData, f, indent=4, ensure_ascii=False)

    def write(self, dataName, thumbnailPath, targetNodes=None):
        r"""
            書き出し実行を行う。書き出しにはsetDataManagerで
            writerオブジェクトを事前いセットすること。
            またこのメソッド呼び出し前にsetupメソッドを呼ぶ必要があり、
            第1引数にはsetupメソッドの戻り値の2つ目の辞書データを渡す。
            
            Args:
                dataName (str):
                thumbnailPath (str):渡されるサムネイルのパス。
                targetNodes (list):
        """
        # ルートディレクトリの設定。（ない場合は作成する。) ===================
        rootdir = self.rootDir()
        if not os.path.exists(rootdir):
            os.makedirs(rootdir)
        # =====================================================================

        # writerの設定。=======================================================
        writer = self.writer()
        if not writer:
            raise RuntimeError(
                'DataManager object was not specified.Use setDataManager method.'
            )
        writer.setWorkDir(rootdir)
        # =====================================================================

        ns, selected = self.getSelected(targetNodes)
        dataname_tag = '_'.join((ns, dataName))

        # メタ情報の読み込み。=================================================
        metafile = self.metaDataFile()
        metadata = self.metaData()
        filename_data = metadata.get('fileData', [])
        # =====================================================================

        # ファイル名のランダム生成。===========================================
        import string
        import random
        existing_files = os.listdir(rootdir)
        all_letters = string.digits+verutil.LETTERS+'!@#$%^&()_+-={}[]'
        while(True):
            filename = ''.join(
                [
                    random.choice(all_letters)
                    for x in range(random.randint(5, 20))
                ]
            )
            if not filename in existing_files:
                break
        writer.setFileName(filename)
        # =====================================================================

        # 書き出し。===========================================================
        writer.setDataName(dataName)
        writer.write(ns, thumbnailPath, selected)
        
        if os.path.exists(thumbnailPath):
            if os.path.isdir(thumbnailPath):
                shutil.rmtree(thumbnailPath)
            else:
                os.remove(thumbnailPath)
        # =====================================================================

        # タグデータの登録。===================================================
        filename_data.append(
            {
                'fileName':filename, 'tagList':self.tags(),
                'dataName':dataName, 'dataType':writer.dataType(),
            }
        )
        metadata['fileData'] = filename_data
        self.writeMetaData(metadata)
        # =====================================================================

    def fileDataList(self):
        r"""
            メタデータが持つファイル情報のデータを返す。
            
            Returns:
                FileDataList:
        """
        if not self.__cached_filedata:
            metadata = self.metaData()
            self.__cached_filedata = FileDataList(
                metadata.get('fileData', []), self.rootDir()
            )
        return self.__cached_filedata

    def applyDataFromFile(self, fileName, method, targetNodes=None):
        r"""
            与えれたファイル名fileNameのデータを任意のノードに適応する。
            
            Args:
                fileName (str):ファイル名
                method (str):
                targetNodes (list):読み込みデータ適応先のノード
        """
        namespaces = list(
            set([x.namespace() for x in node.selected(targetNodes)])
        )
        datalist = self.fileDataList()
        if not datalist:
            return
        data = datalist.findData(fileName)
        if not data:
            return
        datatype = data['dataType']
        manager = self.DataManagers.get(datatype)
        if not manager:
            return
        manager = manager()
        if not hasattr(manager, method):
            return
        exec_method = getattr(manager, method)

        manager.setWorkDir(datalist.rootDir())
        manager.setFileName(fileName)
        with node.DoCommand():
            exec_method(namespaces)

    def readDataFromFile(self, fileName, targetNodes=None):
        r"""
            与えれたファイル名fileNameのデータを読み込む。
            
            Args:
                fileName (str):ファイル名
                targetNodes (list):読み込みデータ適応先のノード
        """
        self.applyDataFromFile(fileName, 'read', targetNodes)
        
    def selectTargetNode(self, fileName, targetNodes=None):
        r"""
            与えれたファイル名fileNameのデータに従い選択を行う
            
            Args:
                fileName (str):ファイル名
                targetNodes (list):選択の適応先のノード
        """
        self.applyDataFromFile(fileName, 'selectTargetNode', targetNodes)

    def deleteDataFromFile(self, tag, fileList):
        r"""
            filelistのアイテムからtagを削除する。
            この操作によってfileListが登録されているタグが空になった
            場合は、ファイル自体を削除する。
            
            Args:
                tag (str):
                fileList (list):
        """
        rootdir = self.rootDir()
        metadata = self.metaData()
        filedata = metadata.get('fileData')
        if not filedata:
            return

        # 削除データの探索。===================================================
        removing_files = []
        removing_data = []
        for data in filedata:
            filename = data['fileName']
            if not filename in fileList:
                continue
            taglist = data['tagList']
            if not tag in taglist:
                continue
            del taglist[taglist.index(tag)]
            if not taglist:
                removing_files.append(filename)
                removing_data.append(data)
        # =====================================================================

        # 探索データに基づき、実データを削除する。=============================
        for data in removing_data:
            del filedata[filedata.index(data)]
        for file in removing_files:
            try:
                shutil.rmtree(os.path.join(rootdir, file))
            except:
                pass
        # =====================================================================

        # 更新されたmetaデータを保存する。=====================================
        self.writeMetaData(metadata)
        # =====================================================================

'''
# EX.//////////////////////////////////////////////////////////////////////////
# ポーズ登録。
dm = core.DataManager()
dm.setDataManager(core.PoseDataManager())
dm.setTags('facial')
dm.write(u'表情:笑顔'

# データの読み出し。
datalist = dm.fileDataList()
for data in datalist.dataList():
    pprint(data)
# /////////////////////////////////////////////////////////////////////////////
'''