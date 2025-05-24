#!/usr/bin/python
# -*- coding: utf-8 -*-
r'''
    @file     qtArchive.py
    @brief    プロジェクトのデータをzipでアーカイブするモジュール
    @class    ArchiverThread : enter description
    @date     2019/01/18 19:51[Eske](eske3g@gmail.com)
    @update   2019/10/29 11:50[eske3g@gmail.com]
    このソースの版権は[EskeYoshinob]にあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[EskeYoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
from gris3.pyside2 import QtCore
import zipfile, os, datetime, re

class ArchiverThread(QtCore.QThread):
    r'''
        @brief    enter description
        @inherit  QtCore.QThread
        @function setup      : 初期設定を行うメソッド。このスレッドのstartを呼ぶ前に
        @function stop       : スレッドを中止するためのメソッド。
        @function saveStop   : enter description
        @function changeStep : enter description
        @function run        : プロジェクトデータをzipアーカイブする。
        @date     2019/09/24 15:37[eske3g@gmail.com]
        @update   2019/10/29 11:50[eske3g@gmail.com]
    '''
    StageChanged = QtCore.Signal(int, str)
    MessageSent = QtCore.Signal(str)
    ErrorOccurred = QtCore.Signal(str)
    NumberOfStepsDecided = QtCore.Signal(int)
    def __init__(self, parent=None):
        # type: (QtCore.QObject) -> any
        r'''
            @brief  初期化を行う
            @param  parent(QtCore.QObject) : 親オブジェクト
            @return (any):
        '''
        super(ArchiverThread, self).__init__(parent)
        self.__mutex = QtCore.QMutex()
        self.setup()

    def setup(self):
        r'''
            @brief  初期設定を行うメソッド。このスレッドのstartを呼ぶ前に
                    必ずこのメソッドを先に使用する。
                    引数filelistにはパブリッシュを実行するための定義xmlファイル
                    のリストを渡す。
            @return (any):
        '''
        self.__stopped = False
        self.__step = 0

    def stop(self):
        r'''
            @brief  スレッドを中止するためのメソッド。
            @return (any):
        '''
        with QtCore.QMutexLocker(self.__mutex):
            self.__stopped = True

    def saveStop(self, zip):
        r'''
            @brief  enter description
            @param  zip(any) : enter description
            @return (any):
        '''
        if not self.__stopped:
            return False
        try:
            zip.close()
            os.remove(zip.filename)
        except Exception as e:
            self.ErrorOccurred.emit(e.args())
        return True

    def changeStep(self, message=''):
        r'''
            @brief  enter description
            @param  message(any) : enter description
            @return (any):
        '''
        self.StageChanged.emit(self.__step, message)
        self.__step += 1

    def run(self):
        r'''
            @brief  プロジェクトデータをzipアーカイブする。
                    どのプロジェクトをアーカイブするかは
                        factoryModules.FactorySettings
                    による
            @return (any):
        '''
        zipped_filelist = []
        def defaultFilter(rootpath, namelist):
            # type: (str,list) -> list
            r'''
                @brief  アーカイブから除くファイルを決定するフィルタ
                @param  rootpath(str)  : 探索ルートパス
                @param  namelist(list) : フィルタリングするファイルパスのリスト
                @return (list):
            '''
            if os.path.basename(rootpath).startswith('.'):
                return []
            return [
                x for x in namelist if
                    not x.endswith('.pyc') and
                    not x.startswith('.') and
                    x != 'incrementalSave'
            ]

        def currentFilter(rootpath, namelist):
            # type: (str,list) -> list
            r'''
                @brief  curファイルとその名前の最新バージョンファイルを検出する
                @param  rootpath(str)  : 探索ルートパス
                @param  namelist(list) : フィルタリングするファイルパスのリスト
                @return (list):
            '''
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
                patterns.append(re.compile(cur_ptn.sub(r'\1v(\\d+)\2', f)))
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

        def message(msg, output=True, indent=0):
            # type: (str,bool,int) -> str
            r'''
                @brief  メッセージ出力用のローカル関数。
                @param  msg(str)     : 出力するメッセージ
                @param  output(bool) : printするかどうか
                @param  indent(int)  : メッセージのインデント
                @return str : 整形済み文字列
            '''
            msg = '%s[ARCHIVE PROJECT] %s' % (' '*indent*4, msg)
            if output:
                print(msg)
            return msg

        def collectZippedFiles(dirname, filter):
            # type: (str,zip,func) -> bool
            r'''
                @brief  zipへの書き込みを行う
                @param  dirname(str) : ディレクトリ名
                @param  filter(func) : フィルタリングを行う関数
                @return (bool):
            '''
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

        from gris3 import factoryModules
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
        zip = zipfile.ZipFile(
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
        if self.saveStop(zip):
            return
        # =====================================================================

        # モジュールに関連するファイルの収集。=================================
        self.MessageSent.emit('Collects a files are related an earch modules.')
        others = []
        for ilist in st.listModulesAsDict().values():
            if self.saveStop(zip):
                return
            others.extend(
                [x.name() for x in ilist if x.moduleName() != 'workspace']
            )
        filelist = []
        for other in others:
            filelist.extend(collectZippedFiles(other, currentFilter))
            if self.saveStop(zip):
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
            if self.saveStop(zip):
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
                if self.saveStop(zip):
                    return
                self.changeStep('Archive : %s' % file)
                # if os.getcwd() != rootpath:
                    # os.chdir(rootpath)
                zip.write(file)

        os.chdir(current)
        zip.close()