#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2023/01/04 21:53 Eske Yoshinob[eske3g@gmail.com]
        update:2023/01/04 21:53 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2023 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
from .. import uilib
from ..uilib import mayaUIlib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class ImageViewer(QtWidgets.QListView):
    DefaultIcon = uilib.IconPath('uiBtn_noImage')
    itemIsClicked = QtCore.Signal(str)
    poseEditorRequested = QtCore.Signal(str, QtGui.QPixmap)
    itemIsDeleted = QtCore.Signal(list)
    GridOffset = QtCore.QSize(28, 28)
    IconMaxSize = 256

    def __init__(self, rootdir='', parent=None):
        r"""
            Args:
                rootdir (str):データ管理を行うルートディレクトリパス
                parent (QtWidgets.QWidget):親ウィジェット
        """
        iconsize = QtCore.QSize(228, 228)
        super(ImageViewer, self).__init__(parent)
        self.__rootdir = rootdir
        self.__oldpos = None
        self.__start_pos = None
        self.__pressed_button = None
        self.setAlternatingRowColors(True)
        self.setViewMode(QtWidgets.QListView.IconMode)
        self.setSelectionMode(QtWidgets.QListView.NoSelection)
        self.setSpacing(5)
        self.setResizeMode(QtWidgets.QListView.Adjust)
        self.setDragEnabled(False)
        self.setIconSize(iconsize)
        self.setGridSize(iconsize+self.GridOffset)

        # アイテムモデルの設定。
        model = self.createItemModel()
        self.setModel(model)
        selmodel = QtCore.QItemSelectionModel(model)
        self.setSelectionModel(selmodel)
        self.clicked.connect(self.storeData)

    def createItemModel(self):
        return QtGui.QStandardItemModel()

    def setRootDir(self, rootdir):
        self.__rootdir = rootdir

    def rootDir(self):
        return self.__rootdir

    def storeData(self, index):
        r"""
            Args:
                index (QtCore.QModelIndex):
        """
        if self.selectionMode() != self.NoSelection:
            return
        self.itemIsClicked.emit(
            index.model().itemFromIndex(index).data()
        )

    def activateSelecting(self, state):
        r"""
            Args:
                state (bool):
        """
        self.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
            if state else QtWidgets.QAbstractItemView.NoSelection
        )
        if not state:
            self.clearSelection()

    def deleteSelected(self):
        r"""
            選択アイテムを削除する。
            このメソッド内ではアイテムの削除だけを行い、削除したデータ名の一覧を
            itemIsDeletedシグナルにのせて送出する。
        """
        if self.selectionMode() == QtWidgets.QAbstractItemView.NoSelection:
            return
        selmodel = self.selectionModel()
        model = self.model()
        rows = [x.row() for x in selmodel.selectedIndexes()]
        rows = list(set(rows))
        rows.sort()
        rows.reverse()
        filelist = []
        for row in rows:
            filelist.append(model.item(row, 0).data())
            model.removeRow(row)
        self.itemIsDeleted.emit(filelist)

    def mousePressEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        self.__start_pos = event.pos()
        self.__pressed_button = event.buttons()
        if self.__pressed_button == QtCore.Qt.RightButton:
            self.__oldpos = event.pos()
            return
        self.__oldpos = None
        super(ImageViewer, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        def is_starting_daragging():
            return (self.__start_pos - cur_pos).manhattanLength() <= 10
        cur_pos = event.pos()
        if self.__oldpos:
            if self.__start_pos:
                if is_starting_daragging():
                    return
                else:
                    self.__start_pos = None

            size = cur_pos.x() - self.__oldpos.x()
            icon_size = self.iconSize() + QtCore.QSize(size, size)
            if 36 < icon_size.width() <= self.IconMaxSize:
                self.setIconSize(icon_size)
                self.setGridSize(icon_size+self.GridOffset)
            self.__oldpos = cur_pos
        else:
            if is_starting_daragging():
                super(ImageViewer, self).mouseMoveEvent(event)
                return
            mimedata = self.model().mimeData(
                self.selectionModel().selectedIndexes()
            )
            drag = QtGui.QDrag(self)
            drag.setMimeData(mimedata)
            drop_action = drag.exec_(QtCore.Qt.CopyAction)

    def mouseReleaseEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        isvalid = True if self.__start_pos else False
        pressed = self.__pressed_button
        self.__oldpos = None
        self.__start_pos = None
        self.__pressed_button = None
        if isvalid:
            if pressed == QtCore.Qt.RightButton:
                index = self.indexAt(event.pos())
                if not index.model():
                    return
                item = index.model().itemFromIndex(index)
                pixmap = item.icon().pixmap(
                    QtCore.QSize(self.IconMaxSize, self.IconMaxSize)
                )
                self.poseEditorRequested.emit(item.data(), pixmap)
                return
        super(ImageViewer, self).mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        key = event.key()
        mod = event.modifiers()
        if mod == QtCore.Qt.NoModifier:
            if key in (QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Delete):
                self.deleteSelected()
                return
        super(ImageViewer, self).keyPressEvent(event)