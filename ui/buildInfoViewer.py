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

from PySide2.QtWidgets import QStyle

from ..uilib import factoryUI, extendedUI
from .. import lib, uilib, buildInfo, style
from ..gadgets import scriptViewer
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class BuildInfoViewStyle(QtWidgets.QStyledItemDelegate):
    ExtraColor = QtGui.QColor(*uilib.Color.SubColor)

    def __init__(self, parent=None):
        super(BuildInfoViewStyle, self).__init__(parent)
        self.__border_row = -1

    def setBorderRow(self, row):
        self.__border_row = row

    def sizeHint(self, option, index):
        depth = index.data(QtCore.Qt.UserRole + 2)
        if depth and depth > 0:
            factor = 2.5
        else:
            factor = 2
        height = int(option.fontMetrics.boundingRect('f').height() * factor)
        return QtCore.QSize(option.rect.width(), height)

    def paint(self, painter, option, index):
        opt = type(option)(option)
        self.initStyleOption(opt, index)
        opt.text = ''
        opt.icon = QtGui.QIcon()
        style = (
            opt.widget.style() if opt.widget else QtWidgets.QApplication.style()
        )
        style.drawControl(
            QtWidgets.QStyle.CE_ItemViewItem, opt, painter, opt.widget
        )
        painter.setRenderHints(QtGui.QPainter.Antialiasing)
        pen = painter.pen()
        default_color = painter.pen().color()

        text = index.data()
        ext_cst = ''
        data = index.data(QtCore.Qt.UserRole + 1)
        font = QtGui.QFont(option.font)
        font_m = QtGui.QFontMetrics(font)
        offset = font_m.boundingRect('K').width()
        rect = QtCore.QRect(option.rect)
        is_top = not index.parent().isValid()

        # 境界線の描画
        if self.__border_row == index.row() and is_top:
            painter.drawLine(
                option.rect.bottomLeft(), option.rect.bottomRight()
            )

        alignment = QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
        if index.column() == 0:
            # alignment = QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            # rect.setRight(rect.right() - offset)
            # if is_top:
            #     pen.setColor(self.FontColor)
            font.setBold(is_top)
            depth = index.data(QtCore.Qt.UserRole + 2)
            if depth and depth > 0:
                buffer = data.split('.')
                text = buffer[-1]
                ext_cst = '.'.join(buffer[:-1])
                if ext_cst:
                    alignment = QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom
                    rect.setLeft(rect.left() + offset * 2)
        else:
            # alignment = QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
            rect.setLeft(rect.left() + offset)
            font.setBold(False)
        painter.setPen(pen)
        painter.setFont(font)
        painter.drawText(rect, alignment, text)

        if ext_cst:
            pen.setColor(self.ExtraColor)
            painter.setPen(pen)
            painter.drawText(
                option.rect, QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop, ext_cst
            )

        pen.setColor(default_color)
        painter.setPen(pen)



class BuildInfoView(QtWidgets.QTreeView):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(BuildInfoView, self).__init__(parent)
        self.setItemDelegate(BuildInfoViewStyle())
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        model = QtGui.QStandardItemModel(0, 2)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Category')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Data')
        self.setModel(model)
        self.setColumnWidth(0, 300)

    def setLogData(self, logData):
        r"""
            Args:
                logData (dict):buildInfo.BuildInfoManagerの持つLODのログ情報
        """
        model = self.model()
        model.removeRows(0, model.rowCount())
        delegate : BuildInfoViewStyle = self.itemDelegate()
        delegate.setBorderRow(-1)

        row = 0
        for tag in buildInfo.BuildInfoManager.DataTags[:-2]:
            val = logData.get(tag)
            tag_item = QtGui.QStandardItem()
            tag_item.setText(lib.title(tag))
            tag_item.setData(tag)
            val_item = QtGui.QStandardItem(val)
            model.setItem(row, 0, tag_item)
            model.setItem(row, 1, val_item)
            row += 1

        build_timer : buildInfo.BuildTimer = logData.get('buildTimer')
        if not build_timer:
            return
        tag_item = QtGui.QStandardItem('Build Time')
        tag_item.setData('buildTime')
        val_item = QtGui.QStandardItem(build_timer.elapsedTime())
        model.setItem(row, 0, tag_item)
        model.setItem(row, 1, val_item)
        delegate.setBorderRow(row)
        row += 1

        process_item = QtGui.QStandardItem('Build Process Time')
        process_item.setData('buildProcessTime')
        model.setItem(row, 0, process_item)

        def add_process_items(parent_item, process, depth):
            row = 0
            for key, proc_data in process.items():
                label_item = QtGui.QStandardItem(lib.title(key))
                label_item.setData(key)
                parent_item.setChild(row, 0, label_item)
                sub_proc = proc_data.get('subProcesses')
                if not sub_proc:
                    label_item.setData(depth, QtCore.Qt.UserRole + 2)
                    c_val_item = QtGui.QStandardItem(proc_data['elapsed'])
                    c_val_item.setData(proc_data['elapsed'])
                    c_val_item.setData(depth, QtCore.Qt.UserRole + 2)
                    parent_item.setChild(row, 1, c_val_item)
                else:
                    add_process_items(label_item, sub_proc, depth+1)
                row += 1
        add_process_items(process_item, build_timer.listProcesses(), 0)
        self.expandAll()

    def drawBranches(self, painter, rect, index):
        if index.model().hasChildren(index):
            super(BuildInfoView, self).drawBranches(painter, rect, index)


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