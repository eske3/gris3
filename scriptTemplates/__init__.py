#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    各種スクリプトを作成する際のテンプレートを作成する機能を提供するモジュール
    
    Dates:
        date:2020/10/20 15:34 eske yoshinob[eske3g@gmail.com]
        update:2020/10/20 17:42 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2020 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os

class AbstractScriptTemplate(object):
    def __init__(self):
        self.__template_path = os.path.dirname(__file__)
        self.__script_root_path = os.path.dirname(self.__template_path)
        self.__filename = ''

    def rootPath(self):
        r"""
            gris3本体が格納されているディレクトリパスを返す。
            
            Returns:
                str:
        """
        return self.__script_root_path

    def creationPath(self):
        r"""
            書き出し先のディレクトリパスを返す再実装用メソッド。
            このパスはgirs3本体からの相対パスとなる。
            
            Returns:
                str:
        """
        raise NotImplementedError('Reimplement this method.')

    def templateName(self):
        r"""
            取り扱うテンプレートのファイル名を返す再実装用メソッド。
            ~/~のようにセパレータを挟むとscriptTemplatesディレクトリからの
            相対パスとして取り扱う。
            名前だけの場合はscriptTemplates/templates内のファイル名として
            取り扱う。
            
            Returns:
                str:
        """
        raise NotImplementedError('Reimplement this method.')

    def setFileName(self, name):
        r"""
            書き出すファイル名を設定する。

            Args:
                name (str):
        """
        if not name.lower().endswith('.py'):
            name += '.py'
        self.__filename = name

    def fileName(self):
        r"""
            作成するファイルの名前を返す。
            
            Returns:
                str:
        """
        return self.__filename

    def optionDict(self):
        r"""
            テンプレートからスクリプト作成時に渡すオプション情報
            を持つ辞書オブジェクトを返す再実装用メソッド。
            
            Returns:
                dict:
        """
        return {}

    def templatePath(self):
        r"""
            スクリプト作成時に使用するテンプレートのパスを返す。

            Returns:
                str:
        """
        name = self.templateName()
        if not '/' in name:
            name = os.path.join('templates', name)
        return os.path.join(self.__template_path, name)

    def writeFilePath(self):
        r"""
            書き出し先のファイルのフルパスを返す。

            Returns:
                str:
        """
        filename = self.fileName()
        if not filename:
            raise RuntimeError('A file name is not specified.')
        return os.path.join(self.rootPath(), self.creationPath(), filename)

    def createScriptText(self):
        r"""
            リグのモジュールを追加するための機能を提供するクラス。

            Returns:
                str:作成されたファイルのフルパス
        """
        template = self.templatePath()
        if not os.path.isfile(template):
            raise IOError(
                'The source template file does not exist : %s'%template
            )
        with open(template, 'r') as f:
            text = f.read()
        return text.format(**self.optionDict())

    def create(self):
        r"""
            リグのモジュールを追加するための機能を提供するクラス。

            Returns:
                str:作成されたファイルのフルパス
        """
        write_path = self.writeFilePath()
        if os.path.exists(write_path):
            raise IOError(
                'The given file name "%s" is aready exists in "%s"'%(
                    self.fileName(),
                    os.path.join(self.rootPath(), self.creationPath())
                )
            )
        text = self.createScriptText()
        with open(write_path, 'w') as f:
            f.write(text)
        print('Create script in "{}".'.format(write_path))
        return write_path


class RigUnitCreator(AbstractScriptTemplate):
    r"""
        リグのモジュールを追加するための機能を提供するクラス。
    """
    def __init__(self, category=None, baseName=None):
        r"""
            Args:
                category (str):モジュールのカテゴリ名
                baseName (str):モジュールのベースとなる名前
        """
        super(RigUnitCreator, self).__init__()
        self.setCategory(category)
        self.setBaseName(baseName)

    def creationPath(self):
        r"""
            書き出し先のディレクトリ名を返す。
            基本的にはgris3のディレクトリからの相対パスとなる。
            
            Returns:
                str:
        """
        return 'rigScripts'

    def templateName(self):
        r"""
            テンプレートの名前を返す。
            
            Returns:
                str:
        """
        return 'rigUnit_template'

    def setCategory(self, category):
        r"""
            リグのカテゴリを設定する。
            
            Args:
                category (str):
        """
        self.__category = category

    def category(self):
        r"""
            設定されているリグのカテゴリを返す。
            
            Returns:
                str:
        """
        return self.__category

    def setBaseName(self, baseName):
        r"""
            作成するリグのベースとなる名前を設定する。
            
            Args:
                baseName (str):
        """
        self.__basename = baseName

    def baseName(self):
        r"""
            設定されているリグのベースとなる名前を返す。
            
            Returns:
                str:
        """
        return self.__basename

    def optionDict(self):
        cat = self.category()
        n = self.baseName()
        opt = {}
        for key, var, value in (
            ('category', 'Category', cat),
            ('basename', 'BaseName', n),
        ):
            if value:
                opt[key] = "%s = '%s'\n"%(var, value)
            else:
                opt[key] = ''
        return opt
