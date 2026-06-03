#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Windows用のファイルユーティリティ。Windowsのみ動作する。

    Dates:
        date:2017/01/22 0:04 Eske Yoshinob[eske3g@gmail.com]
        update:2026/05/19 11:28 Eske Yoshinob[eske3g@gmail.com]

    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
import subprocess


def toCompared(filepath):
    r"""
        ファイルパスの文字列比較用に、パスをすべて小文字化して返す。

        Args:
            filepath(str):

        Returns:
            str:
    """
    return filepath.lower().replace('\\', '/')


def compareFrontPath(srcPath, dstDir):
    r"""
        引数srcPathのパスがdstDirと前方一致しているかどうかを返す。
        これはつまりsrcPathがdstDir内にあるかどうかを調べることと同義。

        Args:
            srcPath(str):
            dstDir(str):

        Returns:
            bool:
    """
    return toCompared(srcPath).startswith(toCompared(dstDir))


def compareEndPath(srcPath, dstFile):
    r"""
        引数srcPathのパスがdstFileと後方一致しているかどうかを返す。

        Args:
            srcPath(str):
            dstFile(str):

        Returns:
            bool:
    """
    return toCompared(srcPath).endswith(toCompared(dstFile))


def openFile(filepath):
    r"""
        fielpathをエクスプローラーで表示する。

        Args:
            filepath(str):
    """
    p = subprocess.Popen(
        ['explorer.exe', '/root,%s' % os.path.normpath(filepath)],
        shell=False
    )


def openDir(filepath):
    r"""
        fielpathを格納しているディレクトリをエクスプローラーで表示する。

        Args:
            filepath(str):
    """
    p = subprocess.Popen(
        ['explorer.exe', os.path.normpath(filepath)],
        shell=False
    )


def openFileInDefaultApp(filepath):
    r"""
        ファイルfielpathをデフォルトのアプリで開く。

        Args:
            filepath(str):
    """
    p = subprocess.Popen(
        [
            'explorer.exe', os.path.normpath(filepath.encode('shift_jis')
            )
        ],
        shell=False
    )
    p.wait()