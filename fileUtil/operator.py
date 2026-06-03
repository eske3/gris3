# !/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ファイル操作を簡易的に行うためのラッパー関数を内包したモジュール。

    Dates:
        date:2026/05/19 11:35 Eske Yoshinob[eske3g@gmail.com]
        update:2026/05/19 11:35 Eske Yoshinob[eske3g@gmail.com]

    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
import shutil
from .. import fileUtil


def createDirectory(rootDirectories, nameText):
    r"""
        指定されたディレクトリ下に、与えられた文字列から生成した名前の
        ディレクトリを作成する関数。

        Args:
            rootDirectories (list):ディレクトリが作られる親ディレクトリのリスト。
            nameText (str):ディレクトリ名。

        Returns:
            bool:作成成功したかどうか
    """
    # テキストの解析。==========================================================
    textlist = nameText.split('\n')
    analyzed = []
    for text in textlist:
        text = text.strip()
        if not text:
            continue

        texts = text.split(',')
        parent = ''
        for t in texts:
            if t.find('/') > -1:
                parent = (
                    '/'.join([parent, t]) if parent else os.path.dirname(t)
                )
                analyzed.append(t)
                continue
            analyzed.append(
                '/'.join([parent, t]) if parent else t
            )
    # =========================================================================

    result = False
    for directory in rootDirectories:
        for dirpath in analyzed:
            path = fileUtil.normpath(os.path.join(directory, dirpath))

            if os.path.isdir(path):
                continue

            try:
                os.makedirs(path)
            except Exception as e:
                print(e.args)
            else:
                result = True
    return result


def deleteFiles(*filelist):
    r"""
        任意のファイルを削除する。

        Args:
            *filelist (str):
    """
    for file in filelist:
        if os.path.isdir(file):
            os.removedirs(file)
        else:
            os.remove(file)


class FileCopy(object):
    r"""
        複数のファイルコピーを行うクラス。
    """

    def __init__(self):
        # コピー元・コピー先（ディレクトリ）の対となるタプルを格納するリスト。
        self.__copyfilelist = []

        self.__check_sameness = True
        self.__file_couples = []
        self.__dirlist = []

    def addCopyFile(self, srcFile, dstDir):
        r"""
            コピー対象のファイルとコピー先を追加する。

            Args:
                srcFile (str):
                dstDir (str):
        """
        self.__copyfilelist.append(
            (fileUtil.normpath(srcFile), fileUtil.normpath(dstDir))
        )

    def clearCopyFileList(self):
        r"""
            コピーリストをクリアする。
        """
        self.__copyfilelist = []

    def copyFileList(self):
        r"""
            コピーリストを返す。

            Returns:
                list:
        """
        return self.__copyfilelist

    def setCheckSameness(self, state):
        r"""
            コピー先とソースのファイルが同名の場合、同一性のチェックを
            行うかどうかを設定するメソッド。

            Args:
                state (bool):
        """
        self.__check_sameness = bool(state)

    def checkSameness(self):
        r"""
            コピー先とソースのファイルの同一性のチェックをするかどうかを
            返すメソッド。

            Returns:
                bool:
        """
        return self.__check_sameness

    def preparing(self):
        r"""
            コピー準備を行う。
        """

        def checkFile(srcFile, dstDir):
            r"""
                ファイルのチェックを行う。

                Args:
                    srcFile (str):
                    dstDir (str):
            """
            filename = os.path.basename(srcFile)
            dst_file = os.path.join(dstDir, filename)
            if os.path.isdir(srcFile):
                self.__dirlist.append(dst_file)
                for file in os.listdir(srcFile):
                    checkFile(os.path.join(srcFile, file), dst_file)
            else:
                self.__file_couples.append((srcFile, dst_file))

        # ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        self.__file_couples = []
        self.__dirlist = []

        for srcfile, dstdir in self.copyFileList():
            if os.path.isfile(dstdir):
                # コピー先にファイルが存在する場合はエラーを返す。
                raise IOError(
                    'The destination path already exists as file : %s' % dstdir
                )
        for srcfile, dstdir in self.copyFileList():
            checkFile(srcfile, dstdir)

        print(
            '    Number of copying directories : {}'.format(len(self.__dirlist))
        )
        print(
            '    Number of copying files       : {}'.format(
                len(self.__file_couples)
            )
        )

    def copy(self):
        r"""
            コピーを行う。
        """
        for dirpath in self.__dirlist:
            print('  Create Directory : {}'.format(dirpath))
            os.makedirs(dirpath)
        for src_file, dst_file in self.__file_couples:
            dst_dir = os.path.dirname(dst_file)
            if not os.path.isdir(dst_dir):
                os.makedirs(dst_dir)
            else:
                if self.checkSameness():
                    if (
                            os.path.exists(dst_file) and
                            fileUtil.compareFiles(src_file, dst_file)
                    ):
                        print('  Skip to copy : {}'.format(dst_file))
                        continue
            print('  Copy from {}'.format(src_file))
            print('     to {}'.format(dst_file))
            shutil.copy2(src_file, dst_file)

    def execute(self):
        r"""
            実行メソッド。
        """
        print('# Start to copy.'.ljust(80, '='))
        self.preparing()
        self.copy()
        print('=' * 80)
        print('')