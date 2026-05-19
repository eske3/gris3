#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    シーケンスファイルを操作するための機能郡を低提供するモジュール。

    Dates:
        date:2017/01/22 0:04[Eske](eske3g@gmail.com)
        update:2022/08/18 14:24 Eske Yoshinob[eske3g@gmail.com]

    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
import re
from .. import lib

# シーケンスを特定するための書式を定義した正規表現文字列。
SeqFormat = '(^.*)([\._])(\d+)\.([a-zA-Z\d]+$)'
# SeqFormat = '(^.*)([\.])(\d+)\.([a-zA-Z\d]+$)'
SeqFormatREObj = re.compile(SeqFormat)
# シーケンスファイルかどうかの判定に使用する正規表現オブジェクト。
SeqMatchingREObj = re.compile('(.*)<(\d+)\-(\d+)>(\.[a-zA-Z\d]+$)')


def listSequence(files, convSingleSequence=False):
    r"""
        複数のシーケンスファイルを１つのファイルとしてまとめるフィルター関数。
        引数filesに複数ファイルのリストを渡すと、シーケンスは
        ひとまとめにされて返される。

        Args:
            files (list):
            convSingleSequence (bool):

        Returns:
            list:
    """
    num_obj = re.compile(SeqFormat)
    single_list = []
    mult_list = []
    result = {}
    zfill = lambda num, pad: str(num).zfill(pad)

    for file in files:
        searched = num_obj.search(file)
        if not searched:
            single_list.append(file)
            continue

        number = int(searched.group(3))
        key = (
            searched.group(1), searched.group(2), searched.group(4),
            len(str(searched.group(3)))
        )
        if key in result:
            result[key].append(number)
        else:
            result[key] = [number]

    # result.keys()を変数に入れてからソートし、それでfor文でまわすよりも ------
    # 高速だったため、回りくどいがこちらの方法を採用。
    keylist = {x[0]: x for x in result.keys()}
    key_keys = list(keylist.keys())
    key_keys.sort()
    # -------------------------------------------------------------------------

    for key_key in key_keys:
        key = keylist[key_key]
        numlist = result[key]
        # 変数keyはタプルになっており、以下の内容が入っている。
        # 　　key[0] : ナンバリングまでのファイル名
        # 　　key[1] : ナンバリングの区切り文字（.か_)
        # 　　key[2] : 拡張子
        # 　　key[3] : ナンバリングの桁数
        numlist.sort()
        num = len(numlist)
        single_formatlist = [
            key[0], key[1], zfill(numlist[0], key[3]), '.', key[2]
        ]
        formatlist = [
            key[0], key[1], '<',
            str(numlist[0]).zfill(key[3]), '-',
            str(numlist[-1]).zfill(key[3]), '>.', key[2]
        ]
        if num == 1:
            if convSingleSequence:
                single_list.append(''.join(single_formatlist))
                continue
            mult_list.append(''.join(formatlist))
            continue

        start_num = numlist[0]
        end_num = numlist[-1]
        if int(end_num) - int(start_num) + 1 == num:
            mult_list.append(''.join(formatlist))
            continue

        indexlist = [[numlist[0]]]
        lastindex = numlist[0]
        for i in range(1, num):
            sub = numlist[i] - numlist[i - 1]
            if sub == 1:
                continue

            if lastindex == numlist[i - 1]:
                single_formatlist[2] = zfill(lastindex, key[3])
                mult_list.append(''.join(single_formatlist))
                lastindex = numlist[i]
            else:
                formatlist[3] = zfill(lastindex, key[3])
                formatlist[5] = zfill(numlist[i - 1], key[3])
                mult_list.append(''.join(formatlist))
                lastindex = numlist[i]
        formatlist[3] = zfill(lastindex, key[3])
        formatlist[5] = zfill(numlist[-1], key[3])
        mult_list.append(''.join(formatlist))

    mult_list.extend(single_list)

    return mult_list


def numMask(pad):
    r"""
        linux系の連番ファイル表示用のマスク文字を返すメソッド。
        pad:が４の倍数の場合は# × pad / 4がそれ以外の場合は* × padが返ってくる。

        Args:
            pad (int):桁数

        Returns:
            str:
    """
    strType, pad = ('*', pad) if pad % 4 else ('#', pad / 4)
    return strType * pad


def absMatch(mobj, character):
    r"""
        Args:
            mobj (_sre.SRE_Pattern):
            character (str):

        Returns:
            _sre.SRE_Match:
    """
    mresult = mobj.search(character)
    if not mresult:
        return None
    if len(mresult.group(0)) != len(character):
        return None
    return mresult


def isSequenceFormat(filestring):
    r"""
        与えられたファイル文字列がシーケンスのフォーマットになっているか
        どうかを返す関数。

        Args:
            filestring (str):

        Returns:
            bool:
    """
    return SeqFormatREObj.search(filestring) != None


def isSequence(fileString):
    r"""
        与えられたファイルパスがシーケンスファイルかどうかを返す関数。
        SeqMatchingREObj:を使用して正規表現的にマッチするかどうかで判定する。

        Args:
            fileString (str):ファイルパス。

        Returns:
            bool:
    """
    return SeqMatchingREObj.search(fileString) != None


# =============================================================================
# Expand Sequenceならびに、戻り値フォーマット拡張用関数集。                  ==
# =============================================================================
def convFormatText(basename, ext, start, end, pad):
    r"""
        expandSequence用拡張関数。桁数部分を%0桁数dの形にして返す。

        Args:
            basename (str):ベースネーム
            ext (str):拡張子
            start (int):開始番号
            end (int):終了番号
            pad (int):桁数

        Returns:
            str:(桁部分を%0桁数dに置き換えられたファイル名、 開始番号、 終了番号)
    """
    return (basename + '%0' + str(pad) + 'd' + ext, start, end)


def convSeqNameInfo(basename, ext, start, end, pad):
    r"""
        expandSequence用拡張関数。
        ベース名、拡張子、開始番号、終了番号、桁数を返す。

        Args:
            basename (str):ベースネーム
            ext (str):拡張子
            start (int):開始番号
            end (int):終了番号
            pad (int):桁数

        Returns:
            tuple:
    """
    return (basename, ext, start, end, pad)


def expandSequence(fileString, formatFunc=None, **keywords):
    r"""
        シーケンスフォーマットになっているファイル名を表す文字列を連番の
        リストへ展開する。
        formatFuncがNoneの場合は、展開された連番ファイル名のリストを返す。
        formatFuncは展開されたシーケンス情報を任意の方法で整形して返すための
        フィルタ関数を設定できる。
        フィルタ関数はベース名、拡張子、開始番号、終了番号、桁数を受け取り、
        何らかの値を返すようにすること。

        Args:
            fileString (str):[]シーケンスフォーマットになっている文字列
            formatFunc (function):
            **keywords (any):formatFuncに渡す引数。

        Returns:
            any:formatFuncによる
    """
    result = []

    dirname = ''
    if os.path.isabs(fileString):
        dirname, fileString = os.path.split(fileString)

    re_result = absMatch(SeqMatchingREObj, fileString)
    if not re_result:
        return [os.path.join(dirname, fileString)]

    basename, ext = (re_result.group(1), re_result.group(4))

    startEnd = [int(re_result.group(2)), int(re_result.group(3))]
    pad = len(re_result.group(2))

    fileFormat = ''.join((basename, '%0', str(pad), 'd', ext))

    fileFormat = os.path.join(dirname, fileFormat)
    if not formatFunc:
        for i in range(startEnd[0], startEnd[1] + 1):
            result.append(fileFormat % i)
        return result
    else:
        return formatFunc(
            basename, ext, startEnd[0], startEnd[1], pad, **keywords
        )


# ============================================================================
#                                                                           ==
# ============================================================================


def expandAllFile(files):
    r"""
        ファイル名のリストを渡すと、シーケンス型のファイルは展開された状態の
        リストを返す。

        Args:
            files (list):

        Returns:
            list:
    """
    result = []
    for file in files:
        result.extend(expandSequence(file))

    return result


def listSequenceFromFilepath(filepath):
    r"""
        入力ファイルパス（フルパス）がシーケンスフォーマットだった場合同階層の
        シーケンスをリストで返すメソッド。
        シーケンスフォーマットではなかった場合は、入力ファイルパスのみを格納
        したリストを返す。

        Args:
            filepath (str):

        Returns:
            list:
    """
    parentdir, name = os.path.split(filepath)
    result = SeqFormatREObj.search(name)
    if not result:
        return [filepath]

    filename_format = lib.convNonreText(result.group(1) + result.group(2))
    ext_format = lib.convNonreText(result.group(4))
    format_re = re.compile(filename_format + '\d+\.' + ext_format)

    return [
        os.path.join(parentdir, x)
        for x in os.listdir(parentdir) if format_re.search(x)
    ]

