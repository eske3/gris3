#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2024/05/29 12:29 Eske Yoshinob[eske3g@gmail.com]
        update:2025/08/25 21:14 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
from ... import lib
from . import core
DataType = 'grisCheckToolPreset'


def listCategories(modulePrefix=core.DefaultPrefix, objectName=None):
    r"""
        Args:
            modulePrefix (str):
            objectName (str):
    """
    objectName = (
        core.CategoryManager.ObjectName if objectName is None else objectName
    )
    mod = lib.importModule(modulePrefix, True)
    if not hasattr(mod, '__file__'):
        return []
    parent_path = os.path.dirname(mod.__file__)
    results = []
    for file in os.listdir(parent_path):
        module_name, ext = os.path.splitext(file)
        try:
            cls = core.CategoryManager.testModule(
                core.CategoryManager.getModuleName(module_name, modulePrefix),
                objectName
            )
        except core.CheckCategoryModuleError:
            continue
        except Exception as e:
            raise e
        results.append(module_name)
    results.sort()
    return results


class CategoryOptionTemplateCreator(object):
    r"""
        checkToolsに表示するカテゴリを定義するためのデータ作成を補助する
        ユーティリティクラス。
    """
    def __init__(self):
        self.__categorylist = []

    def addCategory(self, categoryName, modulePrefix=None, **options):
        r"""
            カテゴリを追加する。
            
            Args:
                categoryName (str):カテゴリ名
                modulePrefix (str):モジュールのプレフィックス
                **options (dict):カテゴリモジュールに渡すためのオプション
        """
        data = {
            'moduleName':categoryName, 
            'options':options
        }
        if modulePrefix:
            data['modulePrefix'] = modulePrefix
        self.__categorylist.append(data)

    def categoryList(self):
        return self.__categorylist[:]

    def clearCategoryList(self):
        del self.__categorylist[:]

    @staticmethod
    def getCategoryOptionTemplate(
        categoryList=None, defaultModulePrefix='-default', toJson=True
    ):
        r"""
            ui.FrameworkのsetCategoryFromDataに渡すためのデータのテンプレートを
            生成して返す。
            引数categoryListにはFrameworkのaddCategoryに渡すためのカテゴリ一覧を
            渡す。categoryListの中身はaddCategoryで生成する内容と同じで、
                moduleName : カテゴリ名
                options: カテゴリモジュールに渡す任意オプションの辞書
                modulePrefix: GRIS標準外のカテゴリモジュールのプレフィックス
            を格納した辞書を持つリストとなる。
            
            Args:
                categoryList (list):登録するカテゴリーのリスト
                defaultModulePrefix (str):
                toJson (bool):結果をjson化されたテキストに変換するかどうか
                
            Returns:
                str or list:
        """
        categoryList = categoryList if categoryList else []
        data = {
            'version':core.Version,
            'dataType':DataType,
            'defaultModulePrefix': defaultModulePrefix,
            'categoryList':categoryList,
        }
        if not toJson:
            return data
        import json
        return json.dumps(data, indent=4)

    def getCategoryOption(self, defaultModulePrefix='-default', toJson=True):
        r"""
            ui.FrameworkのsetCategoryFromDataに渡すためのデータを生成して返す。
            addCategoryメソッドで登録されたデータを使用して生成される。
            
            Args:
                defaultModulePrefix (str):
                toJson (bool):結果をjson化されたテキストに変換するかどうか
                
            Returns:
                str or list:
        """
        return self.getCategoryOptionTemplate(
            self.categoryList(), defaultModulePrefix, toJson
        )
