#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    プロジェクトのデータをzipでアーカイブするモジュール

    Dates:
        date:2019/01/18 19:51 Eske Yoshinob[eske3g@gmail.com]
        update:2026/05/19 22:50 Eske Yoshinob[eske3g@gmail.com]

    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .pyside_module import QtCore
import zipfile, os, datetime, re
from .fileUtil import fileLinker


class ArchiverThread(QtCore.QThread):
    StageChanged = QtCore.Signal(int, str)
    MessageSent = QtCore.Signal(str)
    ErrorOccurred = QtCore.Signal(str)
    NumberOfStepsDecided = QtCore.Signal(int)

    def __init__(self, parent=None):
        r"""

        Args:
            parent(QtCore.QObject): 親オブジェクト
        """
        super(ArchiverThread, self).__init__(parent)
        self.__mutex = QtCore.QMutex()
        self.__stopped = False
        self.__step = 0
        self.setup()

    def setup(self):
        r"""
        初期設定を行うメソッド。このスレッドのstartを呼ぶ前に必ずこのメソッドを先に使用する。
        """
        self.__stopped = False
        self.__step = 0

    def stop(self):
        r"""
        スレッドを中止するためのメソッド。
        """
        with QtCore.QMutexLocker(self.__mutex):
            self.__stopped = True

    def saveStop(self, zipFile):
        r"""

        Args:
            zipFile(zipfile.ZipFile):

        Returns:
            bool:
        """
        if not self.__stopped:
            return False
        try:
            zipFile.close()
            os.remove(zipFile.filename)
        except Exception as e:
            self.ErrorOccurred.emit(e.args[0])
        return True

    def changeStep(self, message=''):
        r"""
        任意のメッセージを送信しつつ、ステップを一つ進める。

        Args:
            message(str):
        """
        self.StageChanged.emit(self.__step, message)
        self.__step += 1

    def run(self):
        r"""
        プロジェクトデータをzipアーカイブする。
        どのプロジェクトをアーカイブするかは
            factoryModules.FactorySettings
        による
        """
        zipped_filelist = []
        def defaultFilter(rootpath, namelist):
            r"""
            アーカイブから除くファイルを決定するフィルタ

            Args:
                rootpath(str): 探索ルートパス
                namelist(list): フィルタリングするファイルパスのリスト

            Returns:
                list:
            """
            if os.path.basename(rootpath).startswith('.'):
                return []
            return [
                x for x in namelist if
                    not x.endswith('.pyc') and
                    not x.startswith('.') and
                    x != 'incrementalSave'
            ]

        def currentFilter(rootpath, namelist):
            r"""
            curファイルとその名前の最新バージョンファイルを検出する

            Args:
                rootpath(str): 探索ルートパス
                namelist(list): フィルタリングするファイルパスのリスト

            Returns:
                list:
            """
            filtered = defaultFilter(rootpath, namelist)
            if not filtered:
                return filtered
            filtered.sort()
            # カレントファイルの収集。=============================================
            cur_ptn = re.compile(
                '(^.*?\.)cur(\.\w+(|{})$)'.format(
                    fileLinker.FileLinker.Extension
                )
            )
            linkers, file_list, patterns, targets = [], [], [], []
            for f in filtered:
                if not cur_ptn.search(f):
                    targets.append(f)
                    continue
                fl = fileLinker.getFileLinker(os.path.join(rootpath, f))
                file_list.append(f)
                if fl:
                    linkers.append(fl)
                else:
                    patterns.append(re.compile(cur_ptn.sub(r'\1v(\\d+)\2', f)))
            # =====================================================================

            # カレントファイルに属する最新バージョンのファイルを収集。=============
            for fl in linkers:
                # カレントファイルがリンカーの場合、リンク先を取得する。
                file_list.append(fl.linkedPath(True))
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
                file_list.append(filtered[key][-1])
            # =====================================================================
            return file_list

        def message(msg, output=True, indent=0):
            r"""
            メッセージ出力用のローカル関数。

            Args:
                msg(str): 出力するメッセージ
                output(bool): printするかどうか
                indent(int): メッセージのインデント

            Returns:
                str: 整形済み文字列
            """
            msg = '{}[ARCHIVE PROJECT] {}'.format(' '*indent*4, msg)
            if output:
                print(msg)
            return msg

        def collectZippedFiles(dirname, filter):
            r"""
            zipへの書き込みを行う

            Args:
                dirname(str): ディレクトリ名
                filter(func): フィルタリングを行う関数

            Returns:
                bool:
            """
            zipgen = os.walk(dirname)
            result = []
            for z_data in zipgen:
                if self.__stopped:
                    return False
                for f in filter(z_data[0], z_data[2]):
                    if self.__stopped:
                        return False
                    writefile = os.path.join(z_data[0], f)
                    result.append(writefile)
            return result

        from . import factoryModules
        self.MessageSent.emit('Start to archive')
        st = factoryModules.FactorySettings()
        if not st.settingTest():
            self.ErrorOccurred.emit('The Project settings is not enough.')

        # ルートのzipファイルの作成。==========================================
        rootpath = st.rootPath()
        if not os.path.isdir(rootpath):
            self.ErrorOccurred.emit(
                'No root directory was detected : %s' % rootpath
            )
        archive_dir = os.path.join(rootpath, 'archives')
        if not os.path.isdir(archive_dir):
            os.makedirs(archive_dir)

        base = '{}_{}{}_'.format(st.project(), st.assetType(), st.assetName())
        zip_file = zipfile.ZipFile(
            os.path.join(
                archive_dir,
                (base + datetime.datetime.now().strftime('%Y%m%d_%H%M%S.zip'))
            ),
            'w', zipfile.ZIP_DEFLATED
        )
        # =====================================================================

        current = os.getcwd()
        os.chdir(rootpath)
        self.MessageSent.emit('Collects a script files')
        # スクリプトの収集。===================================================
        filelist = collectZippedFiles(st.assetPrefix(), defaultFilter)
        num = len(filelist)
        zipped_filelist.append(('Archive a script files.', filelist))
        if self.saveStop(zip_file):
            return
        # =====================================================================

        # モジュールに関連するファイルの収集。=================================
        self.MessageSent.emit('Collects a files are related an earch modules.')
        others = []
        for ilist in st.listModulesAsDict().values():
            if self.saveStop(zip_file):
                return
            others.extend(
                [x.name() for x in ilist if x.moduleName() != 'workspace']
            )
        filelist = []
        for other in others:
            filelist.extend(collectZippedFiles(other, currentFilter))
            if self.saveStop(zip_file):
                return
        num += len(filelist)
        zipped_filelist.append(
            ('Archive files related an earch modules.', filelist)
        )
        # =====================================================================

        # その他のファイルの収集。=============================================
        self.MessageSent.emit('Collects an other files.')
        files = os.listdir(rootpath)
        filelist = []
        for file in defaultFilter(rootpath, files):
            if self.saveStop(zip_file):
                return
            if os.path.isdir(os.path.join(rootpath, file)):
                continue
            filelist.append(file)
        num += len(filelist)
        zipped_filelist.append(('Archive an other files.', filelist))
        self.NumberOfStepsDecided.emit(num)
        # =====================================================================

        for message, filelist in zipped_filelist:
            self.MessageSent.emit(message)
            for file in filelist:
                if self.saveStop(zip_file):
                    return
                self.changeStep('Archive : %s' % file)
                zip_file.write(file)

        os.chdir(current)
        zip_file.close()