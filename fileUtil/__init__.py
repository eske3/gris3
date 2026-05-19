#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ファイル操作を簡易的に行うためのラッパー関数を内包したモジュール。
    
    Dates:
        date:2017/01/22 0:04[Eske](eske3g@gmail.com)
        update:2022/08/18 14:24 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import sys


# /////////////////////////////////////////////////////////////////////////////
# Osに応じたモジュールの選別を行う。                                         //
# /////////////////////////////////////////////////////////////////////////////
_names = sys.builtin_module_names
if 'nt' in _names:
    from .fileutilwin import *
elif 'posix' in _names:
    from .fileutilposix import *
else:
    raise ImportError('No os specific module found.')
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////


def normpath(filepath):
    r"""
        バックスラッシュをスラッシュへ置き換える関数。
        
        Args:
            filepath (str):
            
        Returns:
            str:
    """
    if filepath.startswith('\\\\\\\\'):
        filepath = filepath.replace('\\\\\\\\', '//', 1)
    return os.path.normpath(filepath)


def toStandardPath(filepath):
    r"""
        '\\'をOS標準パス区切り文字の'/'に置き換えるメソッド。
        主にWindows用。
        
        Args:
            filepath (str):
            
        Returns:
            str:
    """
    filepath = os.path.normpath(filepath)
    if filepath.startswith('\\\\\\\\'):
        filepath = filepath.replace('\\\\\\\\', '//', 1)
    return filepath.replace('\\', '/')


# ファイルサイズの単位リスト。
FileSizeUnit = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'YB')
def calculateFileSize(dataSize):
    r"""
        ファイルサイズを計算するメソッド。容量に応じて最適なバイト表記の状態の
        文字列を返す。
        
        Args:
            dataSize (int):ファイル容量。(単位：バイト）
            
        Returns:
            float:
    """
    size = dataSize
    for fileSizeUnit in FileSizeUnit:
        if size < 1024:
            size = str(round(size, 2)) + fileSizeUnit
            break
        size /= 1024.0
    return size


def compareFiles(file1, file2, sizeTolerance=0.1, timeTolerance=0.1):
    r"""
        ２つのファイルの容量・更新日時比較を行う関数。
        ファイルサイズの誤差がsizeTolerance以内かつ、更新時間の誤差が
        timeTolerance内であればTrueを返す。
        
        Args:
            file1 (str):[]比較ファイル１のフルパス。
            file2 (str):[]比較ファイル２のフルパス。
            sizeTolerance (float):
            timeTolerance (float):

        Returns:
            bool:
    """
    stat1 = os.stat(file1)
    stat2 = os.stat(file2)
    return (
        abs(stat1.st_size - stat2.st_size) < sizeTolerance and
        abs(stat1.st_mtime - stat2.st_mtime) < timeTolerance
    )


def getCommonParentPath(file1, file2):
    r"""
        2つのファイルパスから、
            [共通親ディレクトリ, file1の相対パス, file2の相対パス]
        を返す。
        共通親ディレクトリが見つからない場合
            [None, file1, file2]
        を返す。

        Args:
            file1 (str):比較ファイル１のフルパス。
            file2 (str):]比較ファイル２のフルパス。

        Returns:
            list:
    """
    f1 = toStandardPath(file1)
    f2 = toStandardPath(file2)
    dir1 = os.path.dirname(f1)
    dir2 = os.path.dirname(f2)
    try:
        common_dir = os.path.commonpath([dir1, dir2])
    except ValueError:
        return [None, f1, f2]
    rel1 = os.path.relpath(f1, common_dir)
    rel2 = os.path.relpath(f2, common_dir)

    return [toStandardPath(x) for x in [common_dir, rel1, rel2]]
