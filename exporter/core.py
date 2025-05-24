#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    エクスポーターのベースとなる基底クラスを持つモジュール。
    
    Dates:
        date:2017/01/21 23:55[Eske](eske3g@gmail.com)
        update:2025/01/21 17:36 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
import re
import shutil

def getJsonMeta(version):
    r"""
        jsonに書き出すためのメタ情報を作成して返す。
        
        Args:
            version (float):バージョン
            
        Returns:
            dict:
    """
    import getpass, datetime
    return {
        'author':getpass.getuser(),
        'application':'unknown',
        'creationData':datetime.datetime.now().strftime('%Y/%m/%d-%H:%M:%S'),
        'version':version,
        'datalist':None
    }


def getMayaJsonMeta(version):
    r"""
        jsonに書き出すためのメタ情報を作成して返す。
        getJsonMetaで作成された情報に加えて、mayaで作成されたという情報と、
        mayaのバージョンも付与した辞書オブジェクトとなる。

        Args:
            version (float):バージョン
            
        Returns:
            dict:
    """
    from maya import cmds
    meta_info = getJsonMeta(version)
    meta_info['application'] = 'maya'
    meta_info['applicationVersion'] = cmds.about(v=True)
    return meta_info


class AbstractExporter(object):
    r"""
        エクスポーターのベースとなるクラス。
    """
    Extensions = ['py', 'pyc']
    def __init__(self):
        self.__exportpath = ''
        self.__shape = ''
        self.__isRemapIndex = True

    def checkExtension(self, path):
        r"""
            メンバ変数Extensionsに該当する拡張子を付加して返すメソッド。
            
            Args:
                path (str):
                
            Returns:
                str:
        """
        path, ext = os.path.splitext(path)
        if not ext in self.Extensions:
            path += '.' + self.Extensions[0]
        return path

    def setExportPath(self, path):
        r"""
            出力先のディレクトリをセットするメソッド。
            
            Args:
                path (str):
        """
        self.__exportpath = self.checkExtension(path)

    def exportPath(self):
        r"""
            出力先のディレクトリパスを返すメソッド。
            
            Returns:
                str:
        """
        return self.__exportpath

    def checkDirectoryExists(self):
        r"""
            出力先のディレクトリがあるかどうかをチェックするメソッド。
        """
        parent_dir = os.path.dirname(self.exportPath())
        if not os.path.isdir(parent_dir):
            raise IOError(
                "The specified directory was not found. : %s" % parent_dir
            )

    def export(self):
        r"""
            エクスポートを実行するメソッド。オーバーライド専用。
        """
        pass


class BasicExporter(object):
    r"""
        エクスポーターの基底クラス。
    """
    def __init__(self):
        self.__export_dir = ''
        self.__basename = ''
        self.__extension = ''
        self.__isOverwrite = False
        self.__make_current = True
        self.setSearchingExtensions()

    def setIsMakingCurrent(self, state):
        r"""
            カレントファイルを生成するかどうかを指定する。
            
            Args:
                state (bool):
        """
        self.__make_current = bool(state)

    def isMakingCurrent(self):
        r"""
            カレントファイルを生成するかどうかを返す。
            
            Returns:
                bool:
        """
        return self.__make_current

    def setExportDir(self, path):
        r"""
            書き出し先のディレクトリパスをセットする。
            
            Args:
                path (str):
        """
        self.__export_dir = path

    def exportDir(self):
        r"""
            書き出し先のディレクトリパスを返す。
            
            Returns:
                str:
        """
        return self.__export_dir

    def setBasename(self, name):
        r"""
            書き出すファイルのベースとなるファイル名をセットする。
            
            Args:
                name (str):
        """
        self.__basename = name

    def basename(self):
        r"""
            書き出すファイルのベースとなるファイル名を返す。
            
            Returns:
                str:
        """
        return self.__basename

    def setExtension(self, extension):
        r"""
            書き出すファイルの拡張子をセットする。
            
            Args:
                extension (str):
        """
        self.__extension = extension

    def extension(self):
        r"""
            書き出すファイルの拡張子を返す。
            
            Returns:
                str:
        """
        return self.__extension

    def setSearchingExtensions(self, extensions=None):
        r"""
            最新ファイルを探す際に使用する拡張子のリストをセットする。
            
            Args:
                extensions (list):
        """
        self.__searching_extensions = extensions

    def searchingExtensions(self):
        r"""
            最新ファイルを探す際に使用する拡張子のリストを返す。
            
            Returns:
                list:
        """
        return self.__searching_extensions

    def setIsOverwrite(self, state):
        r"""
            既存のファイルがある場合、上書きするかどうかを指定する。
            
            Args:
                state (bool):
        """
        self.__isOverwrite = bool(state)

    def isOverwrite(self):
        r"""
            既存のファイルがある場合、上書きをするかどうか。
            
            Returns:
                bool:
        """
        return self.__isOverwrite
    # =========================================================================

    @classmethod
    def getLatestFile(
            self, parentDir, basename,
            extension, targetExtensions=None, isOverwrite=False, padding=2
        ):
        r"""
            最新ファイルを取得する
            
            Args:
                parentDir (str):ファイルを格納しているディレクトリパス
                basename (str):ベースとなる名前
                extension (str or list):対象となる拡張子
                targetExtensions (list):検索対象となる拡張子
                isOverwrite (bool):上書きするかどうか
                padding (int):バージョンの桁数
                
            Returns:
                str:
        """
        all_files = os.listdir(parentDir)
        startfile = os.path.join(
            parentDir, '%s.v01.%s' % (basename, extension)
        )
        if not all_files:
            return startfile
        if targetExtensions is None:
            targetExtensions = [extension]
        file_ptn = re.compile(
            '%s\.v(\d+)\.(%s)$' % (basename, '|'.join(targetExtensions))
        )
        target_files = {}
        for file in all_files:
            result = file_ptn.search(file)
            if not result:
                continue
            ver = int(result.group(1))
            target_files.setdefault(ver, []).append(file)
        numbers = list(target_files.keys())
        if not numbers:
            return startfile

        numbers.sort()
        latest_file = target_files[numbers[-1]][-1]
        if not isOverwrite:
            latest_file = (
                '%s.v%s.%s' % (
                    basename,
                    str(numbers[-1] + 1).zfill(padding),
                    extension
                )
            )
        return os.path.join(parentDir, latest_file)

    @classmethod
    def getCurFile(self, parentDir, basename, extension):
        r"""
            与えられた引数をベースに最新ファイルのパスを返す
            
            Args:
                parentDir (str):ファイルを格納するディレクトリパス
                basename (str):ベースとなる名前
                extension (str):拡張子
                
            Returns:
                str:
        """
        return os.path.join(parentDir, '%s.cur.%s' % (basename, extension))

    def export(self, file):
        r"""
            ファイルを書き出す、オーバーライド用メソッド。
            
            Args:
                file (str):
        """
        pass

    def execute(self):
        r"""
            書き出しを実行するエントリーメソッド。
        """
        print('=' * 80)
        print('Export file into %s' % self.exportDir())
        print('  + File Base Name : %s' % self.basename())
        print('  + File extension : %s' % self.extension())
        print('  + Is override    : %s' % self.isOverwrite())
        print('=' * 80)
        latest_file = self.getLatestFile(
            self.exportDir(), self.basename(), self.extension(),
            self.searchingExtensions(),
            isOverwrite=self.isOverwrite()
        )
        cur_file = os.path.join(
            self.exportDir(),
            '%s.cur.%s' % (self.basename(), self.extension())
        )
        self.export(latest_file)

        if not self.isMakingCurrent():
            return
        print('Make current file :')
        print('    ' + latest_file)
        print('    -> %s' % cur_file)
        shutil.copy2(latest_file, cur_file)


class JsonExporter(BasicExporter):
    Version = '1.0.0'
    def __init__(self):
        super(JsonExporter, self).__init__()
        self.setExtension('json')
        self.__main_data = None

    def setMainData(self, data):
        self.__main_data = data

    def mainData(self):
        return self.__main_data
        
    def makeData(self):
        return []

    def export(self, file):
        data = getMayaJsonMeta(self.Version)
        data['datalist'] = self.makeData()
        self.setMainData(data)
        import json
        with open(file, 'w') as f:
            datatext = json.dumps(data, indent=4)
            f.write(datatext)
