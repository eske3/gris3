#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2024/04/29 14:18 Eske Yoshinob[eske3g@gmail.com]
        update:2024/04/29 18:52 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
import sys
import inspect
from collections import OrderedDict
from .. import lib, verutil


def listArgs(function):
    r"""
        与えられた関数の引数の情報を返す。
        戻り値は
            引数名 : デフォルト値
        のOrderedDict。

        Args:
            function (function):

        Returns:
            OrderedDict: 
    """
    sig = inspect.signature(function)
    results = OrderedDict()
    for p in sig.parameters.values():
        default = p.default 
        if default is inspect.Signature.empty:
            default = ''
        elif isinstance(default, verutil.BaseString) and not default:
            default = "''"
        results[p.name] = default
    return results


class ScriptManager(object):
    def __init__(self):
        self.__target_module = None
        self.__info = {}

    def resetInfo(self):
        self.__info = {}
        self.__info['syspath'] = ''
        self.__info['prefix'] = ''
        self.__info['name'] = ''
        self.__info['appendedPath'] = ''
        self.__info['module'] = None

    def info(self):
        return (
            self.__info['syspath'], self.__info['prefix'], self.__info['name']
        )

    def module(self):
        r"""
            解析して読み込んだモジュールを返す。
            
            Returns:
                module:
        """
        return self.__info['module']

    def setTargetModule(self, modulePath):
        r"""
            解析するモジュールのパスを設定する。
            
            Args:
                modulePath (str):
        """
        self.__target_module = modulePath
        self.resetInfo()

    def targetModule(self):
        r"""
            設定された解析モジュールのパスを返す。
            
            Returns:
                str:
        """
        return self.__target_module

    def analyzeModule(self):
        mod_path = self.targetModule()
        if not mod_path:
            return

        def _get_prefix(dirpath, prefixes):
            r"""
                Args:
                    dirpath (str):
                    prefixes (list):
            """
            subfiles = [
                os.path.splitext(x)[0] for x in os.listdir(dirpath)
            ]
            if '__init__' not in subfiles:
                return os.path.normpath(dirpath), prefixes
            d, f = os.path.split(dirpath)
            prefixes.append(f)
            return _get_prefix(d, prefixes)

        dirpath, mod_name = os.path.split(mod_path)
        if os.path.isdir(mod_path):
            # モジュール指定の場合、__init__があるかどうかのチェック
            subfiles = [
                os.path.splitext(x)[0] for x in os.listdir(mod_path)
            ]
            if '__init__' not in subfiles:
                return False
        else:
            # ファイルの場合、拡張子を取る。
            mod_name = os.path.splitext(mod_name)[0]

        # 親階層を辿り階層トップを走査。
        syspath, prefixes = _get_prefix(dirpath, [])
        self.__info['syspath'] = syspath
        self.__info['prefix'] = '.'.join(prefixes)
        self.__info['name'] = mod_name
        return True

    def load(self):
        syspath, prefix, module = self.info()
        if not module:
            return False
        if syspath not in sys.path:
            sys.path.append(syspath)
            self.__info['appendedPath'] = syspath
        if prefix:
            mod_name = prefix + '.' + module
        else:
            mod_name = module
        mod = lib.importModule(mod_name)
        self.__info['module'] = mod
        return True

    def listFunctions(self):
        f_type = type(lambda x:x)
        mod = self.module()
        result = []
        for f in dir(mod):
            obj = getattr(mod, f)
            if isinstance(obj, f_type):
                result.append(f)
        return result

    def getFunction(self, functionName):
        r"""
            指定した名前の関数オブジェクトを返す。

            Args:
                functionName (str):
            
            Returns:
                function:
        """
        return getattr(self.module(), functionName)
