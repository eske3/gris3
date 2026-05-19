#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ファイルの管理を行う機能を提供するモジュール。
    
    Dates:
        date:2017/01/22 0:04[Eske](eske3g@gmail.com)
        update:2022/08/05 12:34 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
import re

from . import fileLinker, operator
from .. import exporter
from .. import fileInfoManager
from .. import fileUtil

VersionFileReTemplate = '^(.*)([_\.])(v\d+|cur)\.({})$'

def coordinateFiles(files, extensions, extFormat=VersionFileReTemplate):
    r"""
        Args:
            files (list):ファイル操作する対象のパスリスト
            extensions (list):フィルタをかける拡張子のリスト
            extFormat (str):バージョン表記となる箇所を特定する正規表現
            
        Returns:
            dict:
    """
    if extFormat is None:
        reobj = None
    else:
        reobj = re.compile(extFormat.format('|'.join(extensions)))
    matched_files = {}
    files.sort()
    for filepath in files:
        file = os.path.basename(filepath)
        if file.startswith('.'):
            continue
        if os.path.isdir(filepath):
            matched_files.setdefault('/dir', []).append(file)
            continue

        linker = fileLinker.getFileLinker(filepath)
        if linker:
            file = os.path.basename(linker.path())
        if reobj:
            r = reobj.search(file)
            if r:
                data = {
                    'ver': r.group(3), 'sep': r.group(2), 'name': file,
                    'ext': r.group(4),
                    'simpleName': reobj.sub(r'\1\2\3', file),
                    'isLinker': bool(linker)
                }
                matched_files.setdefault(r.group(1), []).append(data)
                continue

        matched_files.setdefault('/file', []).append(file)
    return matched_files


class FileManager(object):
    r"""
        ファイル管理を行うクラス。
    """
    def __init__(self):
        self.__path = ''
        self.__coordinator = coordinateFiles
        self.__extensions = []
        self.__version_template = ''
        self.setExtensions(['ma'])
        self.setVersionReTemplate(VersionFileReTemplate)

    def setPath(self, path):
        r"""
            管理するディレクトリパスをセットするメソッド。
            
            Args:
                path (str):
        """
        if not os.path.isdir(path):
            raise IOError('"%s" is not directory')
        self.__path = path

    def setCoordinator(self, function):
        r"""
            Args:
                function (function):
        """
        self.__coordinator = function

    def setExtensions(self, extensions):
        r"""
            フィルターする拡張子のリストをセットするメソッド。
            
            Args:
                extensions (list):
        """
        self.__extensions = extensions[:]

    def extensions(self):
        r"""
            セットされている拡張子のリストを返すメソッド。
            
            Returns:
                list:
        """
        return self.__extensions

    def setVersionReTemplate(self, template):
        r"""
            バージョンに基づく判別を行うための正規表現をセットする。
            
            Args:
                template (str):
        """
        self.__version_template = template

    def versionReTemplate(self):
        r"""
            バージョンに基づく判別を行うための正規表現を返す。
            
            Returns:
                str:
        """
        return self.__version_template

    def path(self):
        r"""
            セットされている管理するディレクトリパスを返すメソッド。
            
            Returns:
                str:
        """
        return self.__path

    def discard(self, filelist):
        r"""
            引数で指定したファイルをゴミ箱へ送るメソッド。
            
            Args:
                filelist (list):
        """
        workdir = self.path()
        discarder = fileInfoManager.FileDiscarder()
        discarder.setWorkdir(workdir)
        discarder.moveTo([os.path.join(workdir, x) for x in filelist])


def toCurrent(parentDir, filepaths):
    r"""
        任意のファイルをカレントファイルに登録する。
        カレントファイルはfileLinker.FileLinkerとして作成され、任意のファイルのパスを
        指すようになる。
        これに伴い、任意のファイルをコピーしてカレントファイルとしてリネームするという機能は
        廃止となる。
        
        Args:
            parentDir (str):親ディレクトリパス
            filepaths (list):カレントへ変更するファイル一覧。
    """
    from collections import OrderedDict
    current_list = OrderedDict()
    for file in filepaths:
        filename, ext = os.path.splitext(file)
        name, path, cur = exporter.getLatestAndCurrent(parentDir, filename, ext)
        src = fileUtil.toStandardPath(os.path.join(parentDir, file))
        cur = fileUtil.toStandardPath(cur)
        if src == cur:
            continue
        current_list.setdefault(cur, []).append(src)
    print('##  To current file ##'.ljust(80, '='))
    for cur, files in current_list.items():
        files.sort()
        print('# Change current file from "{}"'.format(files[-1]))
        print('     to "{}"'.format(cur))
        cur_lnk = fileLinker.FileLinker(cur)
        cur_lnk.makeLink(files[-1])
        if os.path.exists(cur):
            operator.deleteFiles(cur)
    print('=' * 80)
