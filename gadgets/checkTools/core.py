#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2024/05/09 18:03 Eske Yoshinob[eske3g@gmail.com]
        update:2024/05/29 14:19 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3.tools import checkUtil
from ... import uilib, lib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


DefaultPrefix = __package__ + '.checkModules'
Version = '1.0.0'


class AbstractCategoryOption(QtWidgets.QWidget):
    OK, Error, Warning = range(3)
    checkingWasFinished = QtCore.Signal(int, int)

    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):
        """
        super(AbstractCategoryOption, self).__init__(parent)
        self.__is_built = False
        self.__id = -1

    def category(self):
        return ''

    def setId(self, id):
        r"""
            チェックツールFramework無いで識別するためのIDをセットする。
            基本的には内部使用専用。
            
            Args:
                id (int):
        """
        self.__id = id
    
    def id(self):
        r"""
            チェックツールFramework内で識別するためのIDを返す。
            基本的には内部使用専用。
            
            Returns:
                int:
        """
        return self.__id

    def createHeader(self):
        label = QtWidgets.QLabel('+ ' + self.category())
        label.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        label.setStyleSheet('font-size : 14pt;')
        layout = QtWidgets.QGridLayout(self)
        exec_btn = uilib.OButton(uilib.IconPath('uiBtn_play'))
        exec_btn.clicked.connect(self.doCheck)
        
        exec_label = QtWidgets.QLabel('Start to check')
        parent = QtWidgets.QWidget()
        
        layout.addWidget(label, 0, 0, 1, 2)
        layout.addWidget(exec_btn, 1, 0, 1, 1, QtCore.Qt.AlignLeft)
        layout.addWidget(exec_label, 1, 1, 1, 1, QtCore.Qt.AlignLeft)
        layout.addWidget(parent, 2, 0, 1, 2)
        layout.setColumnStretch(1, 1)
        return parent

    def createUI(self):
        if self.__is_built:
            return
        self.__is_built = True
        parent = self.createHeader()
        self.buildUI(parent)

    def buildUI(self, parent):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        pass

    def getResultFromData(self, checkedResults):
        r"""
            受け取ったcheckedResultのリストの内容に応じて、問題なしか警告か
            エラーかを返す。
            
            Args:
                checkedResults (list):checkUtil.CheckResultのリスト
        """
        if not checkedResults:
            return self.OK
        warnings = 0
        for checked_result in checkedResults:
            for result in checked_result[1]:
                if result.status == checkUtil.CheckedResult.Error:
                    return self.Error
                if result.status == checkUtil.CheckedResult.Warning:
                    warnings += 1
        if warnings:
            return self.Warning
        return self.OK

    def execCheck(self):
        r"""
            チェック自体を行うオーバーライド専用メソッド。
            チェックした結果
                問題がなければAbstractCategoryOption.OK
                警告があればAbstractCategoryOption.Warning
                問題があればAbstractCategoryOption.Error
            を返す。
            
            Returns:
                int:
        """
        return AbstractCategoryOption.Error

    def doCheck(self):
        r"""
            チェックを行う。内部使用専用メソッド。
            チェック完了後、execCheckの結果をcheckingWasFinishedシグナルに
            送出する。
        """
        result = self.execCheck()
        self.checkingWasFinished.emit(self.id(), result)

    def setOptions(self, **optionData):
        r"""
            カテゴリ設定データから渡されるオプションを処理するオーバーライド
            専用メソッド。
            受け取るデータは辞書形式で、処理自体はサブクラスの方で実装する。

            Args:
                optionData (dict):
        """
        pass


class CategoryManager(object):
    ObjectName = 'CategoryOption'

    def __init__(self):
        self.__installed = {}

    def install(self, moduleName, prefix=DefaultPrefix):
        r"""
            モジュールをインストールする。
            戻り値は登録されたモジュールを呼び出すためのキー
            
            Args:
                moduleName (str):
                prefix (str):
                
            Returns:
                str:
        """
        pfx = prefix + '.' if prefix else ''
        mod_name = pfx + moduleName
        if mod_name in self.__installed:
            return mod_name
        mod = lib.importModule(mod_name, True)
        if not hasattr(mod, self.ObjectName):
            raise AttributeError(
                'Specified module "{}" has no attribute "{}".'.format(
                    moduleName, self.ObjectName
                )
            )
        cls = getattr(mod, self.ObjectName)
        self.__installed[mod_name] = cls
        return mod_name

    def listInstalled(self):
        return {x: y for x, y in self.__installed}

    def listInstalledNames(self):
        return sorted(list(self.__installed.keys()))

    def getCategoryObject(self, key):
        r"""
            Args:
                key (str):
        """
        return self.__installed[key]
