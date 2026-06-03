# !/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ファイル操作を簡易的に行うためのラッパー関数を内包したモジュール。

    Dates:
        date:2026/05/19 11:41 Eske Yoshinob[eske3g@gmail.com]
        update:2026/05/19 11:41 Eske Yoshinob[eske3g@gmail.com]

    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import re
import os

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
                    self.__list[version] = {minor: file}
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

        from . import operator
        if os.path.exists(new_file):
            if new_file == src_file:
                return
            try:
                operator.deleteFiles(new_file)
            except:
                return

        try:
            os.rename(src_file, new_file)
        except:
            return
        else:
            return new_file