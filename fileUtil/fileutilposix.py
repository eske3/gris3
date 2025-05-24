# -*- coding: utf-8 -*-
r'''
    @file     fileutilwin.py
    @brief    Windows用のファイルユーティリティ。Windowsのみ動作する。
    @function toCompared : ファイルパスの文字列比較用に、パスをすべて小文字化して返す。
    @function compareFrontPath : 引数srcPathのパスがdstDirと前方一致しているかどうかを返す。
    @function compareEndPath : 引数srcPathのパスがdstDirと後方一致しているかどうかを返す。
    @date        2017/01/22 0:04[Eske](eske3g@gmail.com)
    @update      2017/01/22 0:04[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''

import os
import subprocess

def toCompared(filepath):
    r'''
        @brief  ファイルパスの文字列比較用に、パスをすべて小文字化して返す。
        @param  filepath : [str]
        @return str
    '''
    return filepath.replace('\\', '/')


def compareFrontPath(srcPath, dstDir):
    r'''
        @brief  引数srcPathのパスがdstDirと前方一致しているかどうかを返す。
        @brief  これはつまりsrcPathがdstDir内にあるかどうかを調べることと同義。
        @param  srcPath : [str]
        @param  dstDir : [str]
        @return bool
    '''
    return toCompared(srcPath).startswith(toCompared(dstDir))


def compareEndPath(srcPath, dstFile):
    r'''
        @brief  引数srcPathのパスがdstDirと後方一致しているかどうかを返す。
        @param  srcPath : [str]
        @param  dstFile : [edit]
        @return bool
    '''
    return toCompared(srcPath).endswith(toCompared(dstDir))

def openFile(filepath):
    p = subprocess.Popen(
        ['open', os.path.normpath(filepath)],
        shell=False
    )

def openDir(filepath):
    p = subprocess.Popen(
        ['open', os.path.normpath(filepath)],
        shell=False
    )
