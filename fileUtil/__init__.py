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
import os
import shutil
import re
import sys

from gris3 import lib

# /////////////////////////////////////////////////////////////////////////////
# Osに応じたモジュールの選別を行う。                                         //
# /////////////////////////////////////////////////////////////////////////////
_names = sys.builtin_module_names
if 'nt' in _names:
    from gris3.fileUtil.fileutilwin import *
elif 'posix' in _names:
    from gris3.fileUtil.fileutilposix import *
else:
    raise ImportError('No os specific module found.')
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////



# /////////////////////////////////////////////////////////////////////////////
# パス表記の正規化用関数。                                                   //
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
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////



# /////////////////////////////////////////////////////////////////////////////
# シーケンスにまつわる便利関数集。                                           //
# /////////////////////////////////////////////////////////////////////////////
# シーケンスを特定するための書式を定義した正規表現文字列。
SeqFormat = '(^.*)([\._])(\d+)\.([a-zA-Z\d]+$)'
#SeqFormat = '(^.*)([\.])(\d+)\.([a-zA-Z\d]+$)'
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
    zfill = lambda num, pad : str(num).zfill(pad)

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
    keylist = {x[0] : x for x in result.keys()}
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
        if int(end_num) - int(start_num) +1 == num:
            mult_list.append(''.join(formatlist))
            continue

        indexlist = [[numlist[0]]]
        lastindex = numlist[0]
        for i in range(1, num):
            sub = numlist[i] - numlist[i-1]
            if sub == 1:
                continue

            if lastindex == numlist[i-1]:
                single_formatlist[2] = zfill(lastindex, key[3])
                mult_list.append(''.join(single_formatlist))
                lastindex = numlist[i]
            else:
                formatlist[3] = zfill(lastindex, key[3])
                formatlist[5] = zfill(numlist[i-1], key[3])
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
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////



# /////////////////////////////////////////////////////////////////////////////
# ファイルサイズにまつわる関数・変数。                                       //
# /////////////////////////////////////////////////////////////////////////////
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
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////



# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////
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
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////



# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////
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
            path = normpath(os.path.join(directory, dirpath))

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
        self.__copyfilelist.append((normpath(srcFile), normpath(dstDir)))

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
        for dirpath in self.__dirlist :
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
                        compareFiles(src_file, dst_file)
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
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////



# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////
class VersionManager(object):
    r"""
        任意のディレクトリ下にあるファイルから、任意の名前のバージョンファイルを
        検出し、操作する機能を提供するクラス。
        バージョン表記にはメジャーバージョンとマイナーバージョンの2種類があり、
        それぞれの表記はv00、v00-00となる。
    """
    MajorPadding = 2
    MinorPadding = 2
    def __init__(self):
        self.__root_path = ''
        self.__name_format = ''
        self.__extensions = []
        self.__as_minor = True
        
        # 検出されたバージョンファイルリストのキャッシュ。
        self.__list = {}

    def setRootPath(self, path):
        r"""
            ルートディレクトリのパスを設定するメソッド。
            
            Args:
                path (str):ルートディレクトリのパス。
        """
        self.__root_path = path
        self.__list = {}

    def rootPath(self):
        r"""
            ルートディレクトリを返すメソッド。
            
            Returns:
                str:
        """
        return self.__root_path

    def setNameFormat(self, format):
        r"""
            バージョンよりも前の名前を指定するメソッド。
            
            Args:
                format (str):
        """
        self.__name_format = format
        self.__list = {}

    def nameFormat(self):
        r"""
            バージョンよりも前の名前フォーマットを返すメソッド。
            
            Returns:
                str:
        """
        return self.__name_format

    def setAsMinorVersion(self, state):
        r"""
            マイナーバージョンとして取り扱うかどうかを指定するメソッド。
            
            Args:
                state (bool):
        """
        self.__as_minor = bool(state)
        self.__list = {}

    def asMinorVersion(self):
        r"""
            マイナーバージョンとして取り扱うかどうかを返すメソッド。
            
            Returns:
                bool:
        """
        return self.__as_minor

    def setExtensions(self, *extensions):
        r"""
            拡張子をセットするメソッド。
            
            Args:
                *extensions (str):
        """
        self.__extensions = extensions
        self.__list = {}

    def extensions(self):
        r"""
            セットされている拡張子を返すメソッド。
            
            Returns:
                list:
        """
        return self.__extensions

    def setSettingsFromFileName(self, filename):
        r"""
            与えられたファイルネームから諸設定を行うメソッド。
            変更される設定は
            ・nameFormat
            ・extensions
            まだ戻り値としてメジャーバージョン（とマイナーバージョン）を返す。
            
            Args:
                filename (str):
                
            Returns:
                tuple(int, int):
        """
        name_re = '(?P<name>^.*)'
        ext_re = '(?P<ext>[a-zA-Z\d]+)$'
        for ver_re in self.makeVersionExpressions():
            re_obj = re.compile('\.'.join((name_re, ver_re, ext_re)))
            result = re_obj.search(filename)
            if not result:
                continue
            formats = result.groupdict()
            self.setNameFormat(formats.get('name'))
            self.setExtensions(formats.get('ext'))
            major = formats.get('major')
            minor = formats.get('minor', None)

            if minor is not None:
                self.setAsMinorVersion(True)
            else:
                self.setAsMinorVersion(False)
                minor = 0

            return (int(major), int(minor))
            
        self.setNameFormat('')
        self.setExtensions()
        return 0, 0


    def makeVersionExpressions(self):
        r"""
            バージョンを取るための正規表現を返すメソッド。
            正規表現はメジャーバージョン用とマイナーバージョン用の2種類を
            タプルで返す。
            
            Returns:
                tuple(str, str):
        """
        major_ver_re = '\d' * self.MajorPadding
        minor_ver_re = '\d' * self.MinorPadding
        return (
            'v(?P<major>%s)' % major_ver_re,
            'v(?P<major>%s)-(?P<minor>%s)' % (major_ver_re, minor_ver_re),
        )

    def makeReglarExpression(self):
        r"""
            名前検知用正規表現オブジェクトを作成して返す。
            
            Returns:
                _sre.SRE_Pattern:
        """
        major_ver_re, minor_ver_re = self.makeVersionExpressions()
        ext_re = '(' + '|'.join(self.extensions()) + ')$'

        return re.compile(
            '\.'.join(
                (
                    '^' + self.nameFormat(),
                    minor_ver_re if self.asMinorVersion() else major_ver_re,
                    ext_re
                )
            )
        )

    def search(self, force=False):
        r"""
            入力データからバージョンファイルを検出するメソッド。
            現在設定されている内容でもう一度このメソッドを実行してもキャッシュ
            済みデータを返すのみで、再実行は行わない。
            
            Args:
                force (bool):現在の設定で強制的に再検索を行う。
                
            Returns:
                list:
        """
        if self.__list and not force:
            return self.__list

        self.__list = {}
        if not os.path.isdir(self.rootPath()):
            return self.__list

        re_obj = self.makeReglarExpression()
        as_minor = self.asMinorVersion()

        for file in os.listdir(self.rootPath()):
            obj = re_obj.search(file)
            if not obj:
                continue
            version = int(obj.group(1))
            if as_minor:
                minor = int(obj.group(2))
                if not version in self.__list:
                    self.__list[version] = {minor : file}
                else:
                    self.__list[version][minor] = file
            else:
                if version in self.__list:
                    self.__list[int(version)].append(file)
                else:
                    self.__list[int(version)] = [file]
        return self.__list

    def listMajorVersions(self):
        r"""
            現在のルートパスのメジャーバージョンのリストを返すメソッド。
            
            Returns:
                list:
        """
        ver_list = self.search()
        versions = list(ver_list.keys())
        versions.sort()
        return versions

    def listMinorVersions(self, majorVersion=None):
        r"""
            指定されたメジャーバージョン下のマイナーバージョンのリストを返す。
            
            Args:
                majorVersion (int):
                
            Returns:
                list:
        """
        if not self.asMinorVersion():
            return []
        ver_list = self.search()
        if not majorVersion:
            versions = self.listMajorVersions()
            if not versions:
                return []
            majorVersion = versions[-1]
        else:
            if not majorVersion in ver_list:
                return []
        minor_versions = list(ver_list[majorVersion].keys())
        minor_versions.sort()
        return minor_versions

    def makeName(self, majorVersion=0, minorVersion=0, isCurrent=False):
        r"""
            設定された情報からファイル名を作成する。
            isCurrentがTrueの場合、majorVersion・minorVersionに関わらず
            curファイル名で返す。
            このメソッドを使用する場合はrootPathの設定は不要。
            
            Args:
                majorVersion (int):
                minorVersion (int):
                isCurrent (bool):
                
            Returns:
                str:
        """
        major_str = str(majorVersion).zfill(self.MajorPadding)
        minor_str = str(minorVersion).zfill(self.MinorPadding)
        extensions = self.extensions()
        if not extensions:
            raise RuntimeError('The extension was not sepcified.')
        if isCurrent:
            ver = 'cur'
        elif not self.asMinorVersion():
            ver = 'v' + major_str
        else:
            ver = 'v%s-%s' % (major_str, minor_str)
        return '.'.join([self.nameFormat(), ver, extensions[0]])

    def latestVersion(self):
        r"""
            最新バージョンのファイル名を返す。
            
            Returns:
                str:
        """
        ver_list = self.search()
        major_versions = self.listMajorVersions()
        if not major_versions:
            return self.makeName()

        if not self.asMinorVersion():
            # メジャーバージョンのみの設定の場合。-----------------------------
            return ver_list[major_versions[-1]]
            # -----------------------------------------------------------------

        # マイナーバージョン込みの設定の場合。---------------------------------
        minor_versions = self.listMinorVersions(major_versions[-1])
        if not minor_versions:
            return self.makeName(major_versions[-1])
        return ver_list[major_versions[-1]][minor_versions[-1]]
        # ---------------------------------------------------------------------

    def nextMajorVersion(self):
        r"""
            最新版の次のメジャーバージョンを返す。
            
            Returns:
                str:
        """
        major_versions = self.listMajorVersions()
        new_version = major_versions[-1] + 1 if major_versions else 0
        return self.makeName(new_version)

    def versionUpOfMinor(self):
        r"""
            最新のメジャーバージョンのマイナーバージョンを一つアップ
            した名前を返す。
            
            Returns:
                str:
        """
        major_versions = self.listMajorVersions()
        return self.makeName(major_versions[-1] + 1, 0)

    def nextMinorVersion(self):
        r"""
            最新版の次のマイナーバージョンを返す。
            
            Returns:
                str:
        """
        major_versions = self.listMajorVersions()
        if not major_versions:
            return self.makeName()
        minor_versions = self.listMinorVersions(major_versions[-1])
        new_version = minor_versions[-1] + 1 if minor_versions else 0

        as_minor = self.asMinorVersion()
        self.setAsMinorVersion(True)
        new_version = self.makeName(major_versions[-1], new_version)
        self.setAsMinorVersion(as_minor)
        return new_version


class VersionDataManager(object):
    r"""
        ファイル（データ）のバージョン管理を行う機能を提供するクラス。
        管理されるファイル名の命名規則はVersionManagerで取り扱う規則に準ずる。
        また、入力ファイルはマイナーバージョン付きのものに限る。
        このクラスでは、マイナーバージョン付きファイルから、次の
        メジャーバージョンファイル名の生成を行える。
        また、マイナーバージョン付きファイルのバージョンアップ名の作成、
        並びにファイルのリネームを行う機能までサポートする。
    """
    def __init__(self):
        self.__updateEnabled = True
        self.__sourcefilename = ''
        self.__majorver = 0
        self.__minorver = 0
        self.__vmanager = VersionManager()

    def setUpdateEnabled(self, state):
        r"""
            メジャーバージョンをアップデートするかどうかを指定する。

            Args:
                state (bool):
        """
        self.__updateEnabled = bool(state)

    def updateEnabled(self):
        r"""
            メジャーバージョンをアップデートするかどうかを返すメソッド。
            
            Returns:
                bool:
        """
        return self.__updateEnabled

    def setSourceFile(self, filepath):
        r"""
            データ管理を行うためのソースとなるファイルパスを設定する。
            
            Args:
                filepath (str):ソースファイルのフルパス。
        """
        try:
            rootdir, self.__sourcefilename = os.path.split(filepath)
        except:
            rootdir, self.__sourcefilename = '', ''
        self.__vmanager.setRootPath(rootdir)
        self.__majorver, self.__minorver = (
            self.__vmanager.setSettingsFromFileName(self.__sourcefilename)
        )

    def versionManager(self):
        r"""
            ヴァージョン管理オブジェクトを返す。
            
            Returns:
                VersionManager:
        """
        return self.__vmanager

    def rootPath(self):
        r"""
            ルートディレクトリを返す。
            
            Returns:
                str:
        """
        return self.versionManager().rootPath()

    def sourceMajorVersion(self):
        r"""
            ソースファイルのメジャーバージョンを返す。
            
            Returns:
                str:
        """
        return self.__majorver

    def sourceMinorVersion(self):
        r"""
            ソースファイルのメジャーバージョンを返す。
            
            Returns:
                str:
        """
        return self.__minorver

    def sourceFileName(self):
        r"""
            ソースファイル名を返す。
            
            Returns:
                str:
        """
        return self.__sourcefilename

    def sourceFilePath(self):
        r"""
            ソースファイルのフルパスを返す。
            
            Returns:
                str:
        """
        return os.path.join(self.rootPath(), self.sourceFileName())

    def majorVersionName(self):
        r"""
            ソースファイルのメジャーバージョンに対する、次のバージョンの
            ファイル名を返すメソッド。
            返ってくる名前はメジャーバージョンのみ。
            updateEnabledがFalseの場合は現行バージョンのメジャーバージョン名が
            返ってくる。
            
            Returns:
                str:
        """
        self.__vmanager.setAsMinorVersion(False)
        return self.__vmanager.makeName(
            self.sourceMajorVersion() + (1 if self.updateEnabled() else 0)
        )

    def majorVersionPath(self, parentDir=None):
        r"""
            次のメジャーバージョン名を持ったフルパスを返すメソッド。
            引数parentDirに親ディレクトリを指定した場合は、その親ディレクトリ
            込みのフルパスを、指定がない場合はrootPathを含めたフルパスを返す。
            
            Args:
                parentDir (str):

            Returns:
                str:
        """
        return os.path.join(
            parentDir if parentDir else self.rootPath(),
            self.majorVersionName()
        )

    def minorVersionName(self):
        r"""
            ソースファイルのメジャーバージョンに対する、次のマイナーバージョンの
            ファイル名を返す。
            返ってくる名前はマイナーバージョンつきのもの。
            
            Returns:
                str:
        """
        self.__vmanager.setAsMinorVersion(True)
        return self.__vmanager.makeName(
            self.sourceMajorVersion() + (1 if self.updateEnabled() else 0)
        )

    def minorVersionPath(self):
        r"""
            新しいマイナーバージョン名を持ったフルパスを返す。
            
            Returns:
                str:
        """
        return os.path.join(self.rootPath(), self.minorVersionName())

    def newMinorVersionPathExists(self):
        r"""
            新しいマイナーバージョン名のパスがすでに存在するかどうかを返す。
            
            Returns:
                str:
        """
        return os.path.exists(self.minorVersionPath())

    def renameSourceFile(self):
        r"""
            ソースファイルのメジャーバージョンを上げた状態のマイナー
            バージョン付きファイル名へリネームするメソッド。
            新しい名前のファイルがすでに存在する場合は、そのファイル
            （ディレクトリ）を削除してからリネームを実行する。
        """
        src_file = self.sourceFilePath()
        new_file = self.minorVersionPath()
        if not os.path.exists(src_file):
            return

        if os.path.exists(new_file):
            if new_file == src_file:
                return
            try:
                 deleteFiles(new_file)
            except:
                return

        try:
            os.rename(src_file, new_file)
        except:
            return
        else:
            return new_file
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////