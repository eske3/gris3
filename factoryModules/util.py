#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Factoryに関する補足作業を行う便利関数のセット。`
    現状では仕様変更に伴うパッチに近い。

    Dates:
        date:2026/05/19 11:00[Eske](eske3g@gmail.com)
        update:2026/05/19 11:00 Eske Yoshinob[eske3g@gmail.com]

    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""

import os
from ..fileUtil import fileManager, fileLinker, operator


def makeLinkInDir(parent, extensions, coordinator=None):
    r"""
    引数parent内にあるファイルの各バージョンファイルの最新版をcurファイルにリンクする。

    Args:
        parent(str):
        extensions(list):
        coordinator(function):
    """
    if coordinator is None:
        coordinator = fileManager.coordinateFiles

    filedata = coordinator(os.listdir(parent), extensions)
    print('# Operates in {}'.format(parent))
    for name, datalist in filedata.items():
        cur = None
        ver_list = {}
        is_link = False
        for data in datalist:
            if data['ver'] == 'cur':
                cur = data['name']
                is_link = data['isLinker']
                if is_link:
                    break
                continue
            ver_list[data['ver']] = data['name']
        if is_link or not cur or not ver_list:
            continue
        cur_file = os.path.join(parent, cur)

        keys = list(ver_list.keys())
        keys.sort()
        target = os.path.join(parent, ver_list[keys[-1]])
        print('  + Make link')
        print('    {}'.format(cur_file))
        print('     --> {}'.format(target))
        fl = fileLinker.FileLinker(cur_file)
        fl.makeLink(target)
        origin = fl.path()
        if os.path.exists(origin):
            operator.deleteFiles(origin)
    print('=' * 80)
    print()


def listProjectDirAndExtensions(projectPath):
    r"""
    任意のFactoryプロジェクトの各モジュールディレクトリのパスと、その内部に格納されている
    ファイルの拡張子のリストをセットにした辞書を返す。

    Args:
        projectPath(str):

    Returns:
        dict: ディレクトリパスをキー、拡張子のリストを値とする辞書
    """
    from .. import factory
    settings = factory.FactoryData()
    settings.setRootPath(projectPath)
    dirlist = []
    relink_dirs = {}

    for info_list in settings.listModulesAsDict().values():
        dirlist.extend(
            [x.name() for x in info_list if x.moduleName() != 'workspace'])

    lnk_ext = fileLinker.FileLinker.Extension
    for d in dirlist:
        d_path = os.path.join(settings.rootPath(), d)
        if not os.path.isdir(d_path):
            continue
        files = os.listdir(d_path)
        if not files:
            continue
        extensions = [
            os.path.splitext(x)[-1] for x in files
        ]
        extensions = list(set(extensions))
        if lnk_ext in extensions:
            del extensions[extensions.index(lnk_ext)]
        if not extensions:
            continue
        relink_dirs[d_path] = [x[1:] for x in extensions]

    return relink_dirs


def relinkProjectFiles(projectPath, coordinator=None):
    r"""
    Factoryプロジェクトの各factoryModuleのデータを格納しているディレクトリ内にあるファイル
    のうち、バージョンファイルをcurファイルとしてFileLinkerを用いて紐づけを一括で行う。

    Args:
        projectPath(str):
        coordinator(function):
    """
    relink_dirs = listProjectDirAndExtensions(projectPath)
    if not relink_dirs:
        return

    for path, ext in relink_dirs.items():
        makeLinkInDir(path, ext, coordinator)