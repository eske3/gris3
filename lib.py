#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2024/05/09 18:03 Eske Yoshinob[eske3g@gmail.com]
        update:2025/09/10 10:41 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
import sys
import re
import traceback
import shutil

from . import verutil
Codec = sys.getfilesystemencoding()


def getUserName():
    r"""
        ユーザー名を取得する。
        
        Returns:
            str:
    """
    import getpass
    return getpass.getuser()


class ParseArgs(dict):
    r"""
        キーワード引数を解析するクラス。
    """
    def value(self, flags, default=None):
        r"""
            flagsのキーワード（複数可）に該当する値を返すメソッド。
            
            Args:
                flags (list):
                default (any):
                
            Returns:
                any:
        """
        if not isinstance(flags, (list, tuple)):
            flags = [flags]
        for flag in flags:
            if flag in self:
                return self[flag]
        return default


# エンコード用フォーマットのリスト。
Lookup = (
    'utf_8',          'euc_jp',         'euc_jis_2004',   'euc_jisx0213',
    'shift_jis',      'shift_jis_2004', 'shift_jisx0213',
    'iso2022jp',      'iso2022_jp_1',   'iso2022_jp_2',   'iso2022_jp_3',
    'iso2022_jp_ext', 'latin_1',        'ascii',
)
# /////////////////////////////////////////////////////////////////////////////
# 拡張汎用クラスセット。                                                     //
# /////////////////////////////////////////////////////////////////////////////
class ListDict(dict):
    r"""
        各キーに対する値が強制的にリストとなる辞書。
        ListDict[key] = valueとした時にkeyがない場合はvalueは
        リストに変換され、keyがある場合は既存のリストに追加される。
    """
    def __init__(self, dictobj={}):
        r"""
            初期化を行う。値は全てリストに変換される。
            
            Args:
                dictobj (dict):
        """
        for x, y in dictobj.items():
            super(ListDict, self).__setitem__(x, [y])

    def append(self, key, value):
        r"""
            keyに該当する値のリストにvalueを追加する。
            
            Args:
                key (immutable):
                value (any):
                
            Returns:
                any:
        """
        if key in self:
            self[key].append(value)
        else:
            super(ListDict, self).__setitem__(key, [value])

    def extend(self, key, values):
        r"""
            keyに該当する値のリストに、リストであるvalueを結合する。
            
            Args:
                key (immutable):
                values (list):
        """
        if isinstance(values, (list, tuple)):
            raise ValueError(
                'extend method requeires a type "list" or "tuple".'
            )
        if key in self:
            self[key].extend(value)
        else:
            super(ListDict, self).__setitem__(key, list(values))

    def __setitem__(self, key, value):
        r"""
            appendと同じ。
            
            Args:
                key (immutable):
                value (any):
        """
        self.append(key, value)
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////


def errorout(israise=True):
    r"""
        エラーが発生した際、その詳細を表示する。
        
        Args:
            israise (bool):エラーを表示する際、raiseするかどうか
    """
    info = sys.exc_info()
    tb = info[2]
    # -------------------------------------------------------------------------

    # Get traceback informations as list.--------------------------------------
    tbfmt = [ x for x in traceback.format_tb(tb) ]
    tbinfo = traceback.extract_tb(tb)
    if len(tbinfo) == 0:
        return
    # -------------------------------------------------------------------------

    msg = '\n'.rjust(80, '-')
    msg += '# Python Error #\n'
    msg += '\n'.rjust(80, '-')
    msg += '    All Error Code List\n'
    msg += '    %s' % ('    '.join(
        ['+' + x.replace('    ', '        ') for x in tbfmt])
    )
    msg += '\n'.rjust(80, '-')
    msg += '    File       : %s\n' % tbinfo[-1][0]
    msg += '    Line       : %s in "%s"\n' % (tbinfo[-1][1], tbinfo[-1][2])
    msg += '    Error Type : %s\n' % type(info[1])
    msg += '    Message    : %s\n' % info[1]
    msg += '\n'.rjust(80, '-')


    # Call error if the argument "israise" is True.----------------------------
    print(msg)
    if israise == True:
        raise
    else:
        return msg
    # -------------------------------------------------------------------------

# /////////////////////////////////////////////////////////////////////////////
# モジュールのインポート用ユーティリティ関数セット。                         //
# /////////////////////////////////////////////////////////////////////////////
def pythonModuleNameFromPath(filepath):
    r"""
        与えられたPythonファイルパスのモジュール名を返す。
        __init__.py(c)は空文字列が返される。また拡張子がついている場合は
        その拡張子がはずされた状態で返し、ディレクトリの場合はディレクトリ名を
        返す。
        
        Args:
            filepath (str):
            
        Returns:
            str:
    """
    basename = os.path.basename(filepath)
    for extension in ('.py', '.pyc'):
        if basename == '__init__%s' % extension:
            continue

        if basename.endswith(extension):
            return '.'.join(basename.split('.')[:-1])

        if not os.path.isdir(filepath):
            continue

        initpath = os.path.join(filepath, '__init__%s' % extension)
        if os.path.isfile(initpath):
            return basename
    return ''


def importModule(moduleName, echoErrorMessage=False):
    r"""
        文字列で与えられたモジュールをインポートする関数。
        読み込みに失敗し、かつechoErrorMessageがFalseの場合、Noneを返す。
        
        Args:
            moduleName (str):モジュール名
            echoErrorMessage (bool):エラーを送出するかどうか
            
        Returns:
            module:
    """
    try:
        mod = __import__(moduleName)
    except Exception as e:
        if echoErrorMessage:
            errorout()
            # print('Importing Error in %s' % moduleName)
            # raise e
        return None

    components = moduleName.split('.')
    if len(components) > 1:
        for c in components[1:]:
            try:
                mod = getattr(mod, c)
            except Exception as e:
                if echoErrorMessage:
                    raise e
                return None
    return mod


def loadPythonModules(directory, prefix='', mode=1):
    r"""
        任意のディレクトリ下のモジュールをインポートするための関数。
        引数modeが0の場合、名前の一覧のみが返される。
        引数modeが1の場合、インポート済みモジュールのリストが返される。
        引数modeが2の場合、インポートされたモジュール名とモジュール本体
        をタプルとしたリストを返す。
        戻り値は読み込みに成功したモジュールのみがリストされる。
        
        Args:
            directory (str):ディレクトリパス
            prefix (str):インポートされたモジュールにつけるプレフィクス
            mode (int):読み込みモード
            
        Returns:
            list:
    """
    modulelist = []
    if prefix:
        prefix += '.'
    for m in os.listdir(directory):
        pyModuleName = pythonModuleNameFromPath(os.path.join(directory, m))
        if not pyModuleName:
            continue

        modulelist.append('%s%s' % (prefix, pyModuleName))

    modulelist = list(set(modulelist))
    modulelist.sort()
    if mode == 0:
        return modulelist

    loadedModulelist = []
    for mod in modulelist:
        module = importModule(mod, echoErrorMessage=True)
        if module:
            loadedModulelist.append((mod, module) if mode == 2 else module)
    return loadedModulelist
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////



# /////////////////////////////////////////////////////////////////////////////
#　文字列に関する関数セット。                                                //
# /////////////////////////////////////////////////////////////////////////////
def strToBoolean(text):
    r"""
        与えれた引数をBool方に変換する。
        Falseになる条件は引数ががFalseか0かoffかFalseかNoneの場合。
        それ以外はTrueを返す。
        
        Args:
            text (str):
    """
    if text in ('False', '0', 'off', False, None):
        return False
    else:
        return True


def encode(data, to_enc='utf_8'):
    r"""
        文字列をエンコードする関数。コーデックがわからない場合に使用する。
        内部的にはあらゆるコーデックで総当り方式を行っている。
        Pythonのバージョンが3以上の場合はそのまま返す。
        
        Args:
            data (str):エンコードしたい文字列。
            to_enc (str):コーデックがわかっている場合はここに指定する。
            
        Returns:
            str:
    """
    if verutil.PyVer >= 3:
        return data
    for codec in Lookup:
        try:
            data = data.encode(codec)
            return data
        except:
            pass
    return data


def decode(data, to_enc='utf_8'):
    r"""
        文字列をデコードする関数。コーデックがわからない場合に使用する。
        内部的にはあらゆるコーデックで総当り方式を行っている。
        Pythonのバージョンが3以上の場合はそのまま返す。
        
        Args:
            data (str):デンコードしたい文字列。
            to_enc (str):コーデックがわかっている場合はここに指定する。
            
        Returns:
            str:
    """
    if verutil.PyVer >= 3:
        return data
    for codec in Lookup:
        try:
            data = data.decode(codec)
            return data
        except:
            pass
    return data


def title(text):
    r"""
        与えられた文字列を読みやすい形に変換して返す。
        
        Args:
            text (str):
            
        Returns:
            str:
    """
    result = text[0].upper()
    upper = result.isupper()
    for t in text[1:]:
        if t.isupper():
            if upper:
                result += t
            else:
                result += ' ' + t
        else:
            result += t
            upper = False
    result = result.replace(' And ', ' and ')
    result = result.replace(' Or ', ' or ')
    result = result.replace(' In ', ' in ')
    result = result.replace(' On ', ' on ')
    result = result.replace(' To ', ' to ')
    result = result.replace(' Into ', ' into ')
    result = result.replace(' The ', ' the ')
    result = result.replace(' A ', ' a ')
    result = result.replace(' An ', ' an ')
    result = result.replace(' Am ', ' am ')
    result = result.replace(' Is ', ' is ')
    result = result.replace(' Was ', ' was ')
    result = result.replace(' Are ', ' are ')

    return result
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////


def normalizePath(path):
    r"""
        与えられたファイルパスのパス区切り文字を「/」に置き換える。

        Args:
            path (str):
        
        Returns:
            str:
    """
    return path.replace('\\', '/')


def getLatestFileName(basename, number, extension, friendfiles):
    r"""
        friendfilesの中から与えられた名前の最も番号の大きいファイル名を返す
        
        Args:
            basename (str):
            number (int):
            extension (str):
            friendfiles (list):
            
        Returns:
            str:
    """
    if number:
        nextnum = '1'
        regexpr = ['', '', '']

        # Check text format.
        findSharp, findStr = False, False
        for s in number:
            if findSharp:
                if findStr:
                    if s == '#':
                        break
                else:
                    if s == '#':
                        regexpr[1] += '\\d'
                    else:
                        findStr = True
                        regexpr[2] += s
            else:
                if s == '#':
                    regexpr[1] += '\\d'
                    findSharp = True
                else:
                    regexpr[0] += s
        if regexpr[1]:
            regexpr[1] += '+'

        mobj = re.compile('%s$' % ''.join(regexpr))
        basename = mobj.sub('', basename)

        # Define compiled match objects.---------------------------------------
        mobj         = re.compile(
            '^%s%s%s$' % (basename, ''.join(regexpr), extension)
        )
        basenameMobj, extMobj = None, None
        if basename:
            basenameMobj = re.compile('^%s' % basename)
        if extension:
            extMobj      = re.compile('%s$' % extension)
        numMobj      = re.compile('\d+')
        # ---------------------------------------------------------------------

        numlist      = []
        nextnum      = '1'
        padding      = len(regexpr[1]) / 2
        for file in friendfiles:
            matchedFile = mobj.search(file)
            if not matchedFile:
                continue
            matchedFile = matchedFile.group(0)
            if basenameMobj:
                matchedFile = basenameMobj.sub('', matchedFile)
            if extMobj:
                matchedFile = extMobj.sub('', matchedFile)

            number     = numMobj.search(matchedFile)
            if not number:
                continue
            numlist.append(int(number.group(0)))
        if numlist:
            numlist.sort()
            nextnum = str(numlist[-1] + 1)
        number = '%s%s%s' % (regexpr[0], nextnum.zfill(padding), regexpr[2])

    return basename + number + extension


def convNonreText(text):
    r"""
        入力テキストの正規表現オブジェクトへ渡すために変換する
        
        Args:
            text (str):
            
        Returns:
            str:
    """
    return text.replace(
        '(', '\('
    ).replace(
        ')', '\)'
    ).replace(
        '.', '\.'
    ).replace(
        '[', '\['
    ).replace(
        ']', '\]'
    ).replace(
        '-', '\-'
    ).replace(
        '+', '\+'
    ).replace(
        '^', '\^'
    ).replace(
        '$', '\$'
    ).replace(
        '!', '\!'
    ).replace(
        '?', '\?'
    )
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////

