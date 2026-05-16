#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Factory用のブラウザ機能を提供するモジュール。

    Dates:
        date:2017/01/21 23:48[Eske](eske3g@gmail.com)
        update:2026/05/16 19:13 eske yoshinob[eske3g@gmail.com]

    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
import time

from . import context
from ... import uilib
from ...fileUtil import fileManager
from ...uilib import extendedUI

QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class ModuleBrowserModel(QtGui.QStandardItemModel):
    r"""
        ModuleBrowser専用のItemModelを提供するクラス。
    """

    def __init__(self, itemview=None):
        r"""
            Args:
                itemview (QtWidgets.QAbstractItemView):
        """
        super(ModuleBrowserModel, self).__init__(0, 2)
        self.setHeaderData(0, QtCore.Qt.Horizontal, 'File')
        self.setHeaderData(1, QtCore.Qt.Horizontal, 'Date')
        self.__itemview = itemview

    def setItemView(self, itemview):
        r"""
            ModuleBrowserをセットする。

            Args:
                itemview (ModuleBrowser):
        """
        self.__itemview = itemview

    def itemView(self):
        r"""
            セットされているModuleBrowserを返す。

            Returns:
                ModuleBrowser:
        """
        return self.__itemview

    def mimeData(self, indexes):
        r"""
            専用mimeDataを返す

            Args:
                indexes (QtCore.QIndexList):

            Returns:
                QtCore.QMimeData:
        """
        filepathes = self.__itemview.selectedPathes()
        filelist = []
        for file in filepathes:
            url = QtCore.QUrl.fromLocalFile(file)
            filelist.append(url)
        mimedata = QtCore.QMimeData()
        mimedata.setUrls(filelist)

        return mimedata


class ModuleBrowser(extendedUI.FilteredView):
    r"""
        ファイルを一覧するためのクラス。
    """

    @classmethod
    def removeCurFilter(self, filepath):
        r"""
            _curの付くファイルを取り除いた状態のファイル名を返すフィルタ

            Args:
                filepath (str):

            Returns:
                bool:
        """
        fileinfo = filepath.split('.')
        if len(fileinfo) < 2:
            return True
        if fileinfo[-2].endswith('_cur'):
            return False
        return True

    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ModuleBrowser, self).__init__(parent)
        self.__child = None
        self.__path = ''
        self.__customFilters = []
        self.__coordinator = fileManager.coordinateFiles
        self.__extensions = ['ma']
        self.__context = None
        self.__extra_context = None
        self.__browser_context = context.BrowserContext
        self.__version_format = ''
        self.setVersionFormat(fileManager.VersionFileReTemplte)
        self.setExtensionVisibles(False)

        view = self.view()
        view.setColumnWidth(0, uilib.hires(220))
        view.model().sourceModel().setItemView(self)
        self.clicked = view.clicked
        self.doubleClicked = view.doubleClicked
        self.setRootIsDecorated = view.setRootIsDecorated

    def createView(self):
        r"""
            Returns:
                QtWidgets.QTreeView:
        """
        icon_size = uilib.hires(28)
        view = QtWidgets.QTreeView()
        view.setVerticalScrollMode(QtWidgets.QTreeView.ScrollPerPixel)
        view.setHorizontalScrollMode(QtWidgets.QTreeView.ScrollPerPixel)
        view.setAlternatingRowColors(True)
        view.setSelectionMode(QtWidgets.QTreeView.ExtendedSelection)
        view.setDragEnabled(True)
        view.setIconSize(QtCore.QSize(icon_size, icon_size))
        view.clicked.connect(self.setPathToChild)
        view.doubleClicked.connect(self.openInExplorer)
        view.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
        view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        view.customContextMenuRequested.connect(self.showContext)
        return view

    def createModel(self):
        return ModuleBrowserModel()

    def setLabel(self, label):
        r"""
            ビューのヘッダラベルを変更する

            Args:
                label (str):
        """
        self.model().setHeaderData(0, QtCore.Qt.Horizontal, label)

    def setChild(self, childBrowser):
        r"""
            子のブラウザをセットする。

            Args:
                childBrowser (ModuleBrowser):
        """
        self.__child = childBrowser

    def child(self):
        r"""
            セットされている子のブラウザを返す。

            Returns:
                ModuleBrowser:
        """
        return self.__child

    def installCustomFilter(self, filter):
        r"""
            カスタムフィルタを追加する

            Args:
                filter (function):
        """
        self.__customFilters.append(filter)

    def customFilter(self, filepath):
        r"""
            セットされているカスタムフィルタを使用してファイルの判定を行う

            Args:
                filepath (str):

            Returns:
                bool:
        """
        for filter in self.__customFilters:
            if not filter(filepath):
                return False
        return True

    def setCoordinator(self, function):
        r"""
            ファイルリストのフィルタリング関数をセットするメソッド。
            セットする関数は以下のフォーマットに則っている必要がある。
            def coordinate(filelist: list, extensions: list, versionFormat:str): -> dict
            引数
                files(list): ファイル操作する対象のパスリスト
                extensions(list): フィルタをかける拡張子のリスト
                versionFormat(str):バージョン表記となる箇所を特定する正規表現
            戻り値は辞書型で
                キー： バージョン表記の無い、各バージョンファイルをまとめる見出しとなる名前
                値： 各種データを持つ辞書
            となる。
            辞書の値には以下のキーを持つ辞書型を定義する。
                'ver':バージョン番号
                'sep':バージョンを区切るセパレータ文字
                'name': 元のファイル名
                'ext': 拡張子
                'simpleName': 拡張子を抜いたシンプルな名前

            Args:
                function (function):
        """
        self.__coordinator = function

    def coordinate(self, filelist, extensions, versionFormat):
        r"""
            ファイルリストのフィルタリングを実行するメソッド。
            フィルタリングにはsetCoodinatorでセットされたメソッドを使用する。

            Args:
                filelist (list):
                extensions (list):
                versionFormat (str):正規表現

            Returns:
                dict:
        """
        return self.__coordinator(filelist, extensions, versionFormat)

    def setVersionFormat(self, format):
        r"""
            バージョン表記のフォーマットを設定する

            Args:
                format (str):
        """
        self.__version_format = format

    def versionFormat(self):
        r"""
            バージョン表記のフォーマットを返す

            Returns:
                str:
        """
        return self.__version_format

    def setExtensionVisibles(self, state):
        r"""
            拡張子を表示するかどうかを設定する。

            Args:
                state (bool):
        """
        self.__extenstion_visibles = bool(state)

    def extensionVisibles(self):
        r"""
            拡張子を表示するかどうか

            Returns:
                bool:
        """
        return self.__extenstion_visibles

    def setExtraContext(self, contextOption):
        r"""
            コンテキストに追加するオプションを定義するクラスをセットする
            インスタンスではなくクラスのタイプオブジェクトを渡す。

            Args:
                contextOption (ContextOption):
        """
        self.__extra_context = contextOption

    def refresh(self):
        r"""
            内容を更新する。
        """

        def setFiles(dirpath, offset, parentItem):
            r"""
                ファイルをビューにセットするローカル関数

                Args:
                    dirpath (str):ディレクトリパス
                    offset (str):ルートパスからのオフセットパス
                    parentItem (QtGui.QStandardItem): 親アイテム
            """
            filedatalist = self.coordinate(
                [os.path.join(dirpath, x) for x in os.listdir(dirpath)],
                self.__extensions, self.versionFormat()
            )
            if not filedatalist:
                return
            parent_path = dirpath
            # ディレクトリパスに対する処理。===================================
            for d in filedatalist.pop('/dir', []):
                local_dir = os.path.join(offset, d)
                icon = uilib.Icon(uilib.IconPath('folder'))
                item = QtGui.QStandardItem(d)
                item.setIcon(icon)
                item.setData(local_dir)
                parentItem.setChild(parentItem.rowCount(), 0, item)
                setFiles(
                    os.path.join(dirpath, d), local_dir, item
                )
            # =================================================================
            # 通常ファイルに対する処理。=======================================
            keys = list(filedatalist.keys())
            keys.sort()
            for filename in keys:
                filelist = filedatalist[filename]
                icon = QtGui.QIcon(
                    provider.icon(
                        QtCore.QFileInfo(
                            os.path.join(parent_path, filelist[0]['name'])
                        )
                    )
                )
                item = QtGui.QStandardItem()
                item.setIcon(icon)
                for file in filelist:
                    if file['ver'] == 'cur':
                        item.setText(filename)
                        item.setData(os.path.join(offset, file['name']))
                        continue
                    fileitem = QtGui.QStandardItem(file['simpleName'])
                    fileitem.setData(os.path.join(offset, file['name']))
                    fileitem.setIcon(icon)

                    try:
                        t = os.path.getmtime(
                            os.path.join(parent_path, file['name'])
                        )
                        update_time = time.strftime(
                            '%Y/%m/%d %H:%M:%S', time.localtime(t)
                        )
                    except Exception as e:
                        print(e.args[0])
                        update_time = 'unknown'
                    t_item = QtGui.QStandardItem(update_time)

                    row = item.rowCount()
                    item.setChild(row, 0, fileitem)
                    item.setChild(row, 1, t_item)
                else:
                    if item.text():
                        row = parentItem.rowCount()
                        parentItem.setChild(row, 0, item)
                        parentItem.setChild(row, 1, QtGui.QStandardItem())
            # =================================================================

        model = self.view().model().sourceModel()
        model.removeRows(0, model.rowCount())
        root_item = model.invisibleRootItem()
        if not os.path.isdir(self.path()):
            return
        provider = QtWidgets.QFileIconProvider()
        setFiles(self.path(), '', root_item)

    def setPath(self, path):
        r"""
            ルートパスをセットする。

            Args:
                path (str):
        """
        self.__path = path
        self.refresh()

    def path(self):
        r"""
            セットされているルートパスを返す。
            セットされているパスが存在しない場合は空文字列を返す。

            Returns:
                str:
        """
        return self.__path if os.path.isdir(self.__path) else ''

    def setExtensions(self, extensions):
        r"""
            対応拡張子のリストをセットする。

            Args:
                extensions (list):
        """
        if not isinstance(extensions, (list, tuple)):
            extensions = [extensions]
        self.__extensions = extensions[:]
        self.refresh()

    def selectedPathes(self):
        r"""
            選択されたアイテムのファイルパスのリストを返す

            Returns:
                list:
        """
        path = self.path()
        selectionModel = self.view().selectionModel()
        pathlist = []
        for index in [
            x for x in selectionModel.selectedIndexes() if x.column() == 0
        ]:
            pathes = [path, index.data(QtCore.Qt.UserRole + 1)]
            pathlist.append(os.path.join(*pathes))
        return pathlist

    def selectedItems(self, includeChildren=False):
        r"""
            選択アイテムの中身のデータをリストで返すメソッド。

            Args:
                includeChildren (bool):

            Returns:
                list:
        """
        selectionModel = self.view().selectionModel()
        # 子階層を含まない場合。===============================================
        if not includeChildren:
            return [
                x.data(QtCore.Qt.UserRole + 1)
                for x in selectionModel.selectedIndexes() if x.column() == 0
            ]
        # =====================================================================

        model = self.view().model()
        items = []
        for index in selectionModel.selectedIndexes():
            if index.column() != 0:
                continue
            items.append(index.data(QtCore.Qt.UserRole + 1))
            i = 0
            while (True):
                child_index = model.index(i, 0, index)
                if not child_index.isValid():
                    break
                items.append(child_index.data(QtCore.Qt.UserRole + 1))
                i += 1
        items = list(set(items))
        return items

    def openInExplorer(self):
        r"""
            選択アイテムをエクスプローラーで開くメソッド。
        """
        pathes = self.selectedPathes()
        if len(pathes) != 1:
            return
        name, ext = os.path.splitext(pathes[0])
        if ext.lower() in ('.mb', '.ma'):
            from gris3.ui import fileLoader
            fileLoader.showAssistance(pathes[0], self)
        else:
            from gris3 import fileUtil
            fileUtil.openFile(pathes[0])

    def setPathToChild(self):
        r"""
            子のブラウザへパスを渡す
        """
        pathes = self.selectedPathes()
        if len(pathes) != 1:
            return
        if not self.child():
            return
        self.child().setPath(pathes[0])

    def setBrowserContext(self, context):
        r"""
            コンテキストメニューに使用するContextオブジェクトを設定する。

            Args:
                context (BrowserContext):
        """
        self.__browser_context = context

    def showContext(self, point):
        r"""
            コンテキストメニューを表示するメソッド。

            Args:
                point (QtCore.QPoint):
        """
        if not self.__context:
            self.__context = self.__browser_context(self)
            self.__context.setCoordinator(self.__coordinator)
            self.__context.setExtensions(self.__extensions)
            self.__context.setVersionReTemplate(self.versionFormat())
            self.__context.setContextOption(self.__extra_context)
        self.__context.setPath(self.path())
        self.__context.setFileNames(self.selectedItems(True))
        self.__context.show()

