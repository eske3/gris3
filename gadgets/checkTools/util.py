#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2024/05/29 12:29 Eske Yoshinob[eske3g@gmail.com]
        update:2024/05/29 14:13 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .core import Version
DataType = 'grisCheckToolPreset'


class CategoryOptionTemplateCreator(object):
    def __init__(self):
        self.__categorylist = []

    def addCategory(self, categoryName, modulePrefix=None, **options):
        r"""
            Args:
                categoryName (str):
                modulePrefix (str):
                **options (dict):
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
            渡す。
            
            Args:
                categoryList (list):登録するカテゴリーのリスト
                defaultModulePrefix (str):
                toJson (bool):結果をjson化されたテキストに変換するかどうか
                
            Returns:
                str or list:
        """
        categoryList = categoryList if categoryList else []
        data = {
            'version':Version,
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
