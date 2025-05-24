#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    プロジェクトのデータをzipでアーカイブするモジュール
    
    Dates:
        date:2019/01/18 19:51[Eske](eske3g@gmail.com)
        update:2024/11/08 10:56 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2019 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import zipfile, os, datetime, re


class ZipWriter(object):
    r"""
        コンテキスト制御型のzip書き込み制御クラス。
    """
    def __init__(
        self, zipPath, archivedPath, fileMode='w', option=zipfile.ZIP_DEFLATED
    ):
        r"""
            Args:
                zipPath (str):
                archivedPath (str):
                fileMode (str):
                option (int):
        """
        self.current = None
        self.archived_path = archivedPath
        self.options = (zipPath, fileMode, option)
        self.zip = None

    def __enter__(self):
        self.zip = zipfile.ZipFile(
            self.options[0], self.options[1], self.options[2]
        )
        self.current = os.getcwd()
        os.chdir(self.archived_path)
        return self.zip

    def __exit__(self, exc_type, exc_value, traceback):
        r"""
            Args:
                exc_type (any):
                exc_value (any):
                traceback (any):

            Returns:
                bool:
        """
        os.chdir(self.current)
        self.zip.close()
        return False


def message(msg, output=True, indent=0):
    r"""
        メッセージ出力用の関数。
        
        Args:
            msg (str):出力するメッセージ
            output (bool):printするかどうか
            indent (int):
            
        Returns:
            str:整形済み文字列
    """
    msg = '%s[ARCHIVE PROJECT] %s' % (' '*indent*4, msg)
    if output:
        print(msg)
    return msg


def defaultFilter(rootpath, namelist):
    r"""
        writeToZip関数に渡す標準フィルタ関数。
        pycや__pycache__、.から始まる隠しファイル、incrementalSaveなどを
        除外する。
        
        Args:
            rootpath (str):
            namelist (list):
            
        Returns:
            list:
    """
    if os.path.basename(rootpath).startswith('.'):
        return []
    return [
        x for x in namelist if
        not x.endswith('.pyc') and
        not x.startswith('.') and
        not x == '__pycache__' and
        x != 'incrementalSave'
    ]


def writeToZip(dirname, zip, filter):
    r"""
        引数zipで指定したZipFileオブジェクトを用いて、dirname下のデータを
        アーカイブする。
        引数filterは、与えられたディレクトリとファイル情報から取捨選択する
        フィルタ関数で、書式は
            def filter(rootpath: str, namelist: list) -> list
        となる。
        戻り値はroopath内にある、ファイルリストとなる。
        
        Args:
            dirname (str):
            zip (zipfile.ZipFile):
            filter (function):
    """
    zipgen = os.walk(dirname)
    for z_data in zipgen:
        for f in filter(z_data[0], z_data[2]):
            writefile = os.path.join(z_data[0], f)
            message('Write as zip : %s' % writefile, indent=1)
            zip.write(writefile)


def archiveProject():
    r"""
        プロジェクトデータをzipアーカイブする。
        
        Returns:
            any:
            
        Brief:
            どのプロジェクトをアーカイブするかは
            
            factoryModules:.FactorySettings
            による
    """
    def currentFilter(rootpath, namelist):
        r"""
            Args:
                rootpath (str):
                namelist (list):
        """
        filtered = defaultFilter(rootpath, namelist)
        filtered.sort()
        if not filtered:
            return filtered
        # カレントファイルの収集。=============================================
        cur_ptn = re.compile('(^.*?\.)cur(\.\w+$)')
        filelist, patterns, targets = [], [], []
        for f in filtered:
            if not cur_ptn.search(f):
                targets.append(f)
                continue
            filelist.append(f)
            patterns.append(re.compile(cur_ptn.sub(r'\1v(\d+)\2', f)))
        # =====================================================================

        # カレントファイルに属する最新バージョンのファイルを収集。=============
        for ptn in patterns:
            filtered = {}
            for tgt in targets:
                mobj = ptn.search(tgt)
                if not mobj:
                    continue
                filtered.setdefault(mobj.group(1), []).append(tgt)
            if not filtered:
                continue
            key = sorted(filtered.keys())[-1]
            filelist.append(filtered[key][-1])
        # =====================================================================
        return filelist

    from gris3 import factoryModules
    st = factoryModules.FactorySettings()
    if not st.settingTest():
        raise RuntimeError(
            message('The Project settings is not enough.', False)
        )

    # ルートのzipファイルの作成。==============================================
    rootpath = st.rootPath()
    if not os.path.isdir(rootpath):
        raise IOError(
            message('No root directory was detected : %s' % rootpath, False)
        )
    print('#'.ljust(80, '='))
    print('Start archive in %s' % rootpath)
    print('#'.ljust(80, '='))
    archive_dir = os.path.join(rootpath, 'archives')
    if not os.path.isdir(archive_dir):
        os.makedirs(archive_dir)
    # =========================================================================

    base = '{}_{}{}_'.format(st.project(), st.assetType(), st.assetName())
    with ZipWriter(
        os.path.join(
            archive_dir,
            (base + datetime.datetime.now().strftime('%Y%m%d_%H%M%S.zip'))
        ),
        rootpath, 'w', zipfile.ZIP_DEFLATED
    ) as zip:
        # スクリプトの収集。===================================================
        writeToZip(st.assetPrefix(), zip, defaultFilter)
        # =====================================================================

        # モジュールに関連するファイルの収集。=================================
        others = []
        for ilist in st.listModulesAsDict().values():
            others.extend(
                [x.name() for x in ilist if x.moduleName() != 'workspace']
            )
        for other in others:
            writeToZip(other, zip, currentFilter)
        # =====================================================================

        # その他のファイルの収集。=============================================
        files = os.listdir(rootpath)
        for file in defaultFilter(rootpath, files):
            if os.path.isdir(os.path.join(rootpath, file)):
                continue
            zip.write(file)
            message('Write as zip : %s' % file, indent=1)
        # =====================================================================
    
    print('#'.ljust(80, '='))
    print('Done')
    print('#'.ljust(80, '='))
