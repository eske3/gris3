#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    GRIS用のファイルのリンク機能を提供するモジュール。
    ファイルリンクはリンカーと呼び、拡張子は.grslnkとする。
    シンボリックリンクがWindowsでは使いづらいため、独自規格のもので運用。

    Dates:
        date:2026/05/19 11:00[Eske](eske3g@gmail.com)
        update:2026/05/19 11:00 Eske Yoshinob[eske3g@gmail.com]

    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
import re
import json
from ..exporter import core
from .. import fileUtil

Version = '1.0.0'


class FileLinker(object):
    r"""
        リンカーを作成、編集、参照する機能を提供するクラス。
    """
    Extension = '.grslnk'
    Ext_Ptn = re.compile('{}$'.format(Extension))

    def __init__(self, filepath):
        r"""
            引数filepathにはリンカーのパスを渡す。このパスは存在の可否は問わない。

            Args:
                filepath(str): リンクのパス
        """
        self.__filepath = None
        self.setPath(filepath)

    def setPath(self, filepath):
        if not self.Ext_Ptn.search(filepath.lower()):
            filepath = filepath + self.Extension
        self.__filepath = filepath

    def path(self, withExtension=False):
        r"""
            Returns:
                str:
        """
        if withExtension:
            return self.__filepath
        return self.Ext_Ptn.sub('', self.__filepath)

    def linkedPath(self):
        r"""
            リンカーが指しているファイルパスをフルパスで返す。
            戻り値はパス区切りがすべて「/」に変換されて返す。

            Returns:
                str:
        """
        path = self.path(True)
        if not os.path.isfile(path):
            return None
        with open(path, 'r') as f:
            text = f.read()
            data = json.loads(text)
        if data.get('application') != self.Extension:
            return None
        dl = data.get('datalist')
        file = dl.get('target')
        if not os.path.isabs(file):
            file = os.path.join(os.path.dirname(path), file)
        return fileUtil.toStandardPath(file)

    def makeLink(self, sourceFile):
        r"""
            引数sourceFileをリンクとして登録する。

            Args:
                sourceFile(str):
        """
        if not os.path.exists(sourceFile):
            raise IOError(
                'The specified source file does not exist. : {}'.format(
                    sourceFile
                )
            )
        filepath = self.path(True)
        commons = fileUtil.getCommonParentPath(filepath, sourceFile)
        data = core.getJsonMeta(Version)
        data['application'] = self.Extension
        data['datalist'] = {'target': commons[-1]}
        with open(filepath, 'w') as f:
            text = json.dumps(data, indent=4, ensure_ascii=False)
            f.write(text)


def getFileLinker(filepath, linkerObj=FileLinker):
    r"""
        引数filepathをFileLinkerオブジェクトにして返す。
        もし拡張子がリンカーではなかった場合はNoneを返す。
        リンカーオブジェクトかどうかの判断基準は拡張子

        Args:
            filepath(str): 操作対象となるファイルのパス
            linkerObj(FileLinker, type): 判定対象となるFileLinkerクラス

        Returns:
             FileLinker:
    """
    if linkerObj.Ext_Ptn.search(filepath.lower()):
        return linkerObj(filepath)
    return None

