#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Factoryでビルド時の情報を作成、編集、閲覧する機能を提供するモジュール。

    Dates:
        date:2026/05/06 9:52[Eske](eske3g@gmail.com)
        update:2026/05/06 9:52[Eske](eske3g@gmail.com)

    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import time, datetime, json, os, copy
from . import info
from .exporter import core

def formatTime(seconds, numDigits=2):
    r"""
        与えられた浮動小数点を読みやすい時間表示にして文字列として返す。

        Args:
            seconds (float): 時間を表す浮動小数点

        Returns:
            str:
    """
    if seconds < 60:
        return '{} sec'.format(round(seconds, numDigits))
    else:
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        return '{h}:{m:02d}:{s:02d}'.format(h=h, m=m, s=s)


class BuildTimer(object):
    def __init__(self):
        self.__starttime = 0.0
        self.__endtime = 0.0
        self.__num_digits = 2
        self.process_list = []

    def setNumberDigits(self, numDigits):
        self.__num_digits = numDigits

    def setStartTime(self, startTime):
        self.__starttime = startTime

    def setEndTime(self, endTime):
        self.__endtime = endTime

    @staticmethod
    def _end_proc(datalist):
        if not datalist:
            return
        last_data = datalist[-1]
        if 'endTime' in last_data:
            return
        last_data['endTime'] = time.time()

    def _start_proc(self, processName, datalist):
        self._end_proc(datalist)
        data = {
            'name': processName, 'startTime': time.time(), 'subProcesses': []
        }
        datalist.append(data)

    def endProcess(self):
        if not self.process_list:
            return
        self._end_proc(self.process_list)

    def startProcess(self, processName):
        self.endProcess()
        self._start_proc(processName, self.process_list)

    def startSubProcess(self, processName):
        if not self.process_list:
            return
        last_data = self.process_list[-1]
        self._start_proc(processName, last_data['subProcesses'])

    def endSubProcess(self, processName):
        if not self.process_list:
            return
        last_data = self.process_list[-1]
        self._end_proc(last_data['subProcesses'])

    def start(self):
        self.setStartTime(time.time())
        self.process_list = []

    def stop(self):
        self.endProcess()
        self.setEndTime(time.time())

    def elapsedTime(self, isFormating=True):
        total_time = self.__endtime - self.__starttime
        if not isFormating:
            return total_time
        return formatTime(total_time, self.__num_digits)

    def elapsedTimeList(self):
        return copy.deepcopy(self.process_list)

    def listProcesses(self):
        r"""
            各プロセスでの経過時間を持つ辞書オブジェクトを返す。
            本クラスでは各プロセスの開始時間と終了時間をデータとして持つが、このメソッドが
            返す情報は経過時間のみ。
            戻り値はOrderedDict、経過プロセス順にデータを返す。

            Returns:
                OrderedDict:
        """
        from collections import OrderedDict
        def get_proc_data(datalist):
            temp = {}
            for data in datalist:
                elapsed = formatTime(
                    data['endTime'] - data['startTime'], self.__num_digits
                )
                key = data['name']
                l = temp.setdefault(data['startTime'], [])
                l.append({'name':key, 'elapsed':elapsed, 'subProcesses':None})

                if len(data['subProcesses']) <= 1:
                    continue
                l[-1]['subProcesses'] = get_proc_data(data['subProcesses'])

            keys = list(temp.keys())
            keys.sort()
            result = OrderedDict()
            for key in keys:
                for val in temp[key]:
                    result[val['name']] = {
                        'elapsed':val['elapsed'],
                        'subProcesses':val['subProcesses']
                    }
            return result

        return get_proc_data(self.process_list)


class BuildInfoManager(core.JsonExporter):
    Version = '1.0.0'
    DataTags = [
        'grisVersion',
        'appVersion',
        'builtDay',
        'debugMode',
        'buildTime',
        'buildTimeData',
    ]

    def __init__(self):
        super(BuildInfoManager, self).__init__()
        self.__data = {}

    def dataType(self):
        return 'GrisBuildInfomation'

    @staticmethod
    def getAppVersion():
        r"""
            アプリのバージョンを返す。
            現状はMaya バージョン．マイナーバージョン
            の文字列を返す。

            Returns:
                str:
        """
        from maya import cmds
        return '{} {}.{}'.format(
            cmds.about(a=True), cmds.about(mjv=True), cmds.about(mnv=True)
        )

    def setInformation(self, lod, buildTimer, debugMode=None):
        r"""
            ビルド時の情報を作成して返す。
            asStringがTrueの場合、jsonフォーマットでテキスト化された文字列を返す。
            Falseの場合は辞書データとして返す。

            Args:
                lod (str):ビルド情報として登録するLOD
                buildTimer (BuildTimer):
                debugMode (str):実行時のモード（デバッグモードではない場合は-が入る）

            Returns:
                dict:
        """
        gris_ver = info.Version
        current_time = datetime.datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
        debug_mode = '-' if debugMode is None else debugMode
        data = {}
        for tag, val in zip(
            self.DataTags, (
                    gris_ver, self.getAppVersion(),
                    current_time,
                    debug_mode,
                    buildTimer.elapsedTime(isFormating=False),
                    buildTimer.elapsedTimeList(),
                )
        ):
            data[tag] = val

        self.__data[lod] = data
        return data

    def listLods(self):
        return list(self.__data.keys())

    def getLodData(self, lod):
        data = self.__data.get(lod)
        if not data:
            return None
        data = copy.deepcopy(data)
        build_time_data = data.pop(self.DataTags[5])
        build_time  = data.pop(self.DataTags[4])
        build_timer = BuildTimer()
        build_timer.setEndTime(build_time)
        build_timer.process_list = build_time_data
        data['buildTimer'] = build_timer
        return data

    def makeData(self):
        r"""
            書き出し用の上書きメソッド。
            各lodのビルド情報を持つ辞書を返す。

            Returns:
                dict:
        """
        return self.__data

    def load(self, file):
        r"""
            ビルドログファイルを読み込む。
            指定のファイルがない場合は-1、指定のファイルが指定の‐フォマットではなかった
            場合は0、読み込みに成功した場合は1を返す。

            Args:
                file (str):ビルドログのファイルパス

            Returns:
                int:
        """
        self.__data = {}
        if not os.path.exists(file):
            return -1
        with open(file, 'r') as f:
            data = json.load(f)
            if data.get('dataType') != self.dataType():
                return 0
                # raise TypeError(
                #     'The given file is not build data : {}'.format(file)
                # )
        self.__data = data.get('datalist', {})
        return 1
