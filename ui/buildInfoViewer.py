#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ビルド時のログを読み込み、表示するビューワ機能を提供するモジュール。

    Dates:
        date:2026/05/07 02:06[Eske](eske3g@gmail.com)
        update:2026/05/07 02:06[Eske](eske3g@gmail.com)

    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
import re

from ..uilib import factoryUI, extendedUI
from .. import lib, uilib, buildInfo, style
from ..gadgets import scriptViewer
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

class BuildInfoView(QtWidgets.QTreeView):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(BuildInfoView, self).__init__(parent)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        model = QtGui.QStandardItemModel(0, 2)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Category')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Data')
        self.setModel(model)

    def setLogData(self, logData):
        r"""
            Args:
                logData (dict):buildInfo.BuildInfoManagerの持つLODのログ情報
        """
        model = self.model()
        model.removeRows(0, model.rowCount())
        row = 0
        for tag in buildInfo.BuildInfoManager.DataTags[:-2]:
            val = logData.get(tag)
            tag_item = QtGui.QStandardItem(lib.title(tag))
            val_item = QtGui.QStandardItem(val)
            model.setItem(row, 0, tag_item)
            model.setItem(row, 1, val_item)
            row += 1

        build_timer : buildInfo.BuildTimer = logData.get('buildTimer')
        if not build_timer:
            return
        tag_item = QtGui.QStandardItem('Build Time')
        val_item = QtGui.QStandardItem(build_timer.elapsedTime())
        model.setItem(row, 0, tag_item)
        model.setItem(row, 1, val_item)
        row += 1

        process_item = QtGui.QStandardItem('Build Process Time')
        model.setItem(row, 0, process_item)

        def add_process_items(parent_item, process):
            row = 0
            for key, proc_data in process.items():
                label_item = QtGui.QStandardItem(lib.title(key))
                parent_item.setChild(row, 0, label_item)
                sub_proc = proc_data.get('subProcesses')
                if not sub_proc:
                    val_item = QtGui.QStandardItem(proc_data['elapsed'])
                    parent_item.setChild(row, 1, val_item)
                else:
                    add_process_items(label_item, sub_proc)
                row += 1
        add_process_items(process_item, build_timer.listProcesses())


class BuildInfoViewer(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        super(BuildInfoViewer, self).__init__(parent)

    def addLod(self, lod, logData):
        r"""
            Args:
                lod (str): LODを表す文字列
                logData (dict):buildInfo.BuildInfoManagerの持つLODのログ情報

            Returns:
                BuildInfoView:
        """
        view = BuildInfoView()
        view.setLogData(logData)
        self.addTab(view, lod)
        return view

    def removeAllTabs(self):
        r"""
            すべてのタブと、その中身のウィジェットを削除する。
        """
        while self.count() > 0:
            w = self.widget(0)
            self.removeTab(0)
            w.deleteLater()

    def setBuildInfo(self, buildInfoManager):
        r"""
            ビルド情報オブジェクトからGUIを更新する。

            Args:
                buildInfoManager (buildInfo.BuildInfoManager):
        """
        self.removeAllTabs()
        for lod in buildInfoManager.listLods():
            lod_data = buildInfoManager.getLodData(lod)
            self.addLod(lod, lod_data)

    def loadBuildInfo(self, file):
        r"""
            ビルド情報ファイルを読み込み、GUIを更新する。

            Args:
                file (str):
        """
        bim = buildInfo.BuildInfoManager()
        bim.load(file)
        self.setBuildInfo(bim)


class MainGUI(uilib.ConstantWidget):
    def buildUI(self):
        self.setWindowTitle('Build Log')
        self.setStyleSheet(style.styleSheet())
        self.resize(600, 800)

        titlebar = uilib.TitleBarWidget(self)
        viewer = BuildInfoViewer()
        self.loadBuildInfo = viewer.loadBuildInfo

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(uilib.ZeroMargins)
        layout.addWidget(titlebar)
        layout.addWidget(viewer)


def showWindow(parent=None):
    r"""
        ビルド情報のログビューワを作成して返す。

        Args:
            parent (QtWidgets.QWidget):

        Returns:
            MainGUI:
    """
    if parent is None:
        from ..uilib import mayaUIlib
        parent = mayaUIlib.MainWindow
    w = MainGUI(parent)
    w.show()
    return w