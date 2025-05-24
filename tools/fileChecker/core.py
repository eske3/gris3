# !/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2021/06/08 15:21 shunsuke komori[eske3g@gmail.com]
        update:2021/07/20 19:07 shunsuke komori[eske3g@gmail.com]

    License:
        Copyright 2021 shunsuke komori[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from abc import ABCMeta, abstractmethod
from collections import OrderedDict


class DataChckerManager(object):
    def __init__(self):
        self.__header_checkers = []
        self.__all_checkers = []

    def install(self, module_name):
        if not hasattr(module_name, 'DataChecker'):
            raise ValueError(
                (
                    'Failed to install.The given module "{}" '
                    'has no object "DataChecker".'
                ).format(module_name)
            )
        obj = module_name.DataChecker()
        if obj.checker_type() == AbstractMayaDataChecker.HeaderChecker:
            self.__header_checkers.append(obj)
        else:
            self.__all_checkers.append(obj)
        return obj

    def header_checkers(self):
        return self.__header_checkers[:]

    def all_checkers(self):
        return self.__all_checkers

    def check_file(self, filepath):
        header_lines = []
        results = OrderedDict()
        with open(filepath, 'r') as f:
            text = f.readline()
            while text:
                if text.startswith('createNode'):
                    break
                header_lines.append(text.strip())
                text = f.readline()

            # ヘッダー部分のチェック。
            for checker in self.header_checkers():
                results[checker.label()] = checker.check(header_lines)
            if not self.all_checkers():
                return results

            # 全体チェックを開始。
            all_lines = []
            while text:
                all_lines.append(text.strip())
                text = f.readline()

        for checker in self.all_checkers():
            results[checker.label()] = checker.check(all_lines)
        return results


class AbstractMayaDataChecker(
    ABCMeta('AbstractMayaDataChecker', (object,), {})
):
    HeaderChecker, AllChecker = range(2)

    @abstractmethod
    def label(self):
        return ''

    def checker_type(self):
        return self.HeaderChecker

    @abstractmethod
    def check(self, header_lines):
        r"""
            与えられた構文をチェックし、問題がないかどうかを返すチェックメソッド。
            戻り値はtupleで、1項目には
            ・問題がない場合は１
            ・警告は0
            ・エラーがある場合は-1
            を入れる。
            2項目にはエラーや警告の内容をテキストで入れる。

            Args:
                header_lines (list):Mayaファイルの構文リスト

            Returns:
                tuple(int, str):問題ない場合は1，警告は0、エラーは-1を返す。
        """
        return 1, ''
