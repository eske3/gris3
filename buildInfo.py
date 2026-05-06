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
import time, datetime, json, os
from . import info
from .exporter import core

def formatTime(seconds):
    r"""
        与えられた浮動小数点を読みやすい時間表示にして文字列として返す。

        Args:
            seconds (float): 時間を表す浮動小数点

        Returns:
            str:
    """
    if seconds < 60:
        return '{} sec'.format(round(seconds, 2))
    else:
        h, rem = divmod(seconds, 3600)
        m, s = divmod(rem, 60)
        return '{h}:{m:02d}:{s:02d}'.format(h=h, m=m, s=s)


class BuildTimer(object):
    def __init__(self):
        self.starttime = 0
        self.endtime = 0
        self.process_list = []

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
        self.starttime = time.time()
        self.process_list = []

    def stop(self):
        self.endProcess()
        self.endtime = time.time()

    def elapsedTime(self, isFormating=True):
        total_time = self.endtime - self.starttime
        if not isFormating:
            return total_time
        return formatTime(total_time)

    def elapsedTimeList(self):
        import copy
        return copy.deepcopy(self.process_list)


class BuildInfoManager(core.JsonExporter):
    Version = '1.0.0'

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
        data = {
            'grisVersion': gris_ver,
            'appVersion': self.getAppVersion(),
            'builtDay': current_time,
            'buildTime': buildTimer.elapsedTime(isFormating=False),
            'buildTimeData': buildTimer.elapsedTimeList(),
            'debugMode': debug_mode,
        }
        self.__data[lod] = data
        return data

    def makeData(self):
        return self.__data

    def load(self, file):
        if not os.path.exists(file):
            self.__data = {}
            return
        with open(file, 'r') as f:
            data = json.load(f)
            if data.get('dataType') != self.dataType():
                raise TypeError(
                    'The given file is not build data : {}'.format(file)
                )
        self.__data = data.get('datalist', {})
