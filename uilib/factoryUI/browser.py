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
import math

from . import context
from ... import uilib
from ... import fileUtil
from ...fileUtil import fileManager, fileLinker
from ...uilib import extendedUI

QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

class ModuleBrowserStyle(QtWidgets.QStyledItemDelegate):
    ExtraColor = QtGui.QColor(45, 164, 255)

    def sizeHint(self, option, index):
        r"""
            Args:
                option (QtWidgets.QStyleOptionViewItem):
                index(QtCore.QModelIndex):
        """
        opt = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        base = super(ModuleBrowserStyle, self).sizeHint(opt, index)
        font_h = opt.fontMetrics.height()
        factor = 3.5 if index.model().hasChildren(index) else 2.0
        height = int(font_h * factor)
        return QtCore.QSize(base.width(), height)

    def paint(self, painter, option, index):
        r"""
            Args:
                painter (QtGui.QPainter):
                option (QtWidgets.QStyleOptionViewItem):
                index(QtCore.QModelIndex):
        """
        opt = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        style = (
            opt.widget.style() if opt.widget else QtWidgets.QApplication.style()
        )
        painter.save()

        bg_opt = QtWidgets.QStyleOptionViewItem(opt)
        bg_opt.text = ''
        bg_opt.icon = QtGui.QIcon()
        style.drawControl(
            QtWidgets.QStyle.CE_ItemViewItem, bg_opt, painter, bg_opt.widget
        )

        painter.setFont(opt.font)
        painter.setRenderHints(QtGui.QPainter.Antialiasing)

        if opt.state & QtWidgets.QStyle.State_Selected:
            pen_color = opt.palette.color(QtGui.QPalette.HighlightedText)
        else:
            pen_color = opt.palette.color(QtGui.QPalette.Text)

        rect = QtCore.QRect(option.rect)
        font_height = opt.fontMetrics.height()
        offset = int(font_height * 0.25)
        rect.setX(rect.x() + offset)
        rect.setTop(rect.top() + offset)
        rect.setBottom(rect.bottom() - offset)

        icon = index.data(QtCore.Qt.DecorationRole)
        has_children = index.model().hasChildren(index)
        if icon:
            if has_children:
                icon_height = int(rect.height() * 0.6)
            else:
                icon_height = int(font_height * 1)
            icon_size = QtCore.QSize(icon_height, icon_height)
            icon_rect = QtCore.QRect(rect)
            icon_rect.setY(
                icon_rect.y() + ((rect.height() - icon_height) * 0.5)
            )
            icon_rect.setSize(icon_size)
            painter.drawPixmap(icon_rect, icon.pixmap(icon_size))

            rect.setX(rect.x() + icon_height * 1.1)
            rect.setTop(icon_rect.top())

        alignment = QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
        if has_children:
            alignment = QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop
            title_font = QtGui.QFont(opt.font)
            ps = title_font.pointSizeF()
            if ps > 0:
                title_font.setPointSize(ps * 1.25)
            else:
                px = max(1, title_font.pixelSize())
                title_font.setPixelSize(int(px * 1.25))
            title_h = QtGui.QFontMetrics(title_font).height()

            ext = index.data(QtCore.Qt.UserRole+2)
            num_children = index.model().rowCount(index)
            text ='Type : {} | {} item{}'.format(
                'link' if index.data(QtCore.Qt.UserRole+3) else ext,
                num_children, '' if num_children < 2 else 's'
            )
            sub_rect = QtCore.QRect(rect)
            sub_rect.setTop(sub_rect.top() + offset + title_h)
            pen = painter.pen()
            pen.setColor(self.ExtraColor)
            painter.setPen(pen)
            painter.setFont(opt.font)
            painter.drawText(sub_rect, alignment, text)

            painter.setFont(title_font)

        painter.setPen(pen_color)
        painter.drawText(rect, alignment, index.data())

        parent = index.parent()
        if parent.isValid():
            if index.row() == index.model().rowCount(parent) - 1:
                painter.drawLine(
                    option.rect.bottomLeft(), option.rect.bottomRight()
                )

        painter.restore()


class ModuleBrowserView(QtWidgets.QTreeView):
    def __init__(self, parent=None):
        super(ModuleBrowserView, self).__init__(parent)
        self.setItemDelegate(ModuleBrowserStyle())
        self.setAnimated(True)

    def _get_triangle_polygon(self, rect, isUp):
        e = math.sqrt(3)
        box = min(rect.width(), rect.height()) * 0.5
        side = min(box, (2.0 / e) * box)
        cx = rect.center().x()
        cy = rect.center().y()
        h = e / 2.0 * side

        left = cx - side / 2.0
        right = cx + side / 2.0

        if isUp:
            # 上向き三角形
            bottom = cy - h / 3.0
            p1 = QtCore.QPoint(cx, cy + 2.0 * h / 3.0)
            p2 = QtCore.QPoint(left, bottom)
            p3 = QtCore.QPoint(right, bottom)
        else:
            # 下向き三角形
            bottom = cy + h / 3.0
            p1 = QtCore.QPoint(cx, cy - 2.0 * h / 3.0)
            p2 = QtCore.QPoint(left, bottom)
            p3 = QtCore.QPoint(right, bottom)
        return QtGui.QPolygonF([p1, p2, p3])

    def drawBranches(self, painter, rect, index):
        r"""
            Args:
                painter (QtGui.QPainter):
                rect (QtGui.QRect):
                index(QtCore.QModelIndex):
        """
        if not index.model().hasChildren(index) or not self.rootIsDecorated():
            return
        is_expanded = self.isExpanded(index)
        painter.save()
        painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
        pen = painter.pen()
        brush = pen.color()
        if is_expanded:
            brush = QtCore.Qt.NoBrush
        else:
            pen = QtCore.Qt.NoPen
        painter.setBrush(brush)
        painter.setPen(pen)

        parent_index = index.parent()
        col = 1
        while True:
            if not parent_index.isValid():
                break
            parent_index = parent_index.parent()
            col += 1
        rect.setX(rect.width() / col * (col - 1))
        painter.drawPolygon(self._get_triangle_polygon(rect, is_expanded))
        painter.restore()


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
        file_paths = self.__itemview.selectedPathes()
        filelist = []
        for file in file_paths:
            url = QtCore.QUrl.fromLocalFile(file)
            filelist.append(url)
        mime_data = QtCore.QMimeData()
        mime_data.setUrls(filelist)

        return mime_data


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
        self.__extension_visibles = False
        self.__child = None
        self.__path = ''
        self.__customFilters = []
        self.__coordinator = fileManager.coordinateFiles
        self.__extensions = ['ma']
        self.__context = None
        self.__extra_context = None
        self.__browser_context = context.BrowserContext
        self.__version_format = ''
        self.setVersionFormat(fileManager.VersionFileReTemplate)

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
        view = ModuleBrowserView()
        view.setVerticalScrollMode(QtWidgets.QTreeView.ScrollPerPixel)
        view.setHorizontalScrollMode(QtWidgets.QTreeView.ScrollPerPixel)
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
                'isLinker': FileLinkerかどうか

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
        self.__extension_visibles = bool(state)

    def extensionVisibles(self):
        r"""
            拡張子を表示するかどうか

            Returns:
                bool:
        """
        return self.__extension_visibles

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

        def setFiles(dirpath, offset, parentItem, vFormat):
            r"""
                ファイルをビューにセットするローカル関数

                Args:
                    dirpath (str):ディレクトリパス
                    offset (str):ルートパスからのオフセットパス
                    parentItem (QtGui.QStandardItem): 親アイテム
            """
            filedatalist = self.coordinate(
                [os.path.join(dirpath, x) for x in os.listdir(dirpath)],
                self.__extensions, vFormat
            )
            if not filedatalist:
                return
            parent_path = dirpath
            # ディレクトリパスに対する処理。===================================
            for key in ('dir', 'file'):
                for d in filedatalist.pop('/'+key, []):
                    filepath = os.path.join(dirpath, d)
                    local_dir = os.path.join(offset, d)
                    if key == 'dir':
                        icon = uilib.Icon(uilib.IconPath('folder'))
                    else:
                        icon = QtGui.QIcon(
                            provider.icon(QtCore.QFileInfo(filepath))
                        )
                    item = QtGui.QStandardItem(d)
                    item.setIcon(icon)
                    item.setData(local_dir)
                    item.setData(key, QtCore.Qt.UserRole+2)
                    row = parentItem.rowCount()
                    parentItem.setChild(row, 0, item)
                    parentItem.setChild(row, 1, QtGui.QStandardItem())

                    if key == 'dir':
                        setFiles(filepath, local_dir, item, None)
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
                        item.setData(file['ext'], QtCore.Qt.UserRole+2)
                        item.setData(file['isLinker'], QtCore.Qt.UserRole+3)
                        continue
                    file_item = QtGui.QStandardItem(file['simpleName'])
                    file_item.setData(os.path.join(offset, file['name']))
                    file_item.setIcon(icon)
                    file_item.setData(file['isLinker'], QtCore.Qt.UserRole+3)

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
                    item.setChild(row, 0, file_item)
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
        setFiles(self.path(), '', root_item, self.versionFormat())

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

    def selectedPathes(self, isAbsPath=True):
        r"""
            選択されたアイテムのファイルパスのリストを返す

            Returns:
                list:
        """
        path = self.path()
        selection_model = self.view().selectionModel()
        pathlist = []
        for index in [
            x for x in selection_model.selectedIndexes() if x.column() == 0
        ]:
            name = index.data(QtCore.Qt.UserRole+1)
            filepath = os.path.join(path, name)
            result_path = filepath
            if index.data(QtCore.Qt.UserRole+3):
                fl = fileLinker.FileLinker(filepath)
                p = fl.linkedPath()
                if p:
                    if not isAbsPath:
                        cmn = fileUtil.getCommonParentPath(filepath, p)
                        if cmn[0]:
                            result_path = cmn[-1]
                    else:
                        result_path = p
                else:
                    result_path = name + fl.Ext_Ptn
            else:
                if not isAbsPath:
                    result_path = name
            pathlist.append(result_path)
        return pathlist

    def selectedItems(self, includeChildren=False):
        r"""
            選択アイテムの中身のデータをリストで返すメソッド。

            Args:
                includeChildren (bool):

            Returns:
                list:
        """
        if not includeChildren:
            # 子階層を含まない場合。
            return self.selectedPathes(False)

        parent_path = self.path()
        def get_path_from_index(index):
            r"""
                与えられたindexからパス情報を取得して返す。
                その際、ファイルがリンカーの時は内部パスに変換して返す。

                Args:
                    index (QModelIndex):

                Returns:
                    str:
            """
            filename = index.data(QtCore.Qt.UserRole + 1)
            if not index.data(QtCore.Qt.UserRole + 3):
                return filename
            filepath = os.path.join(parent_path, filename)
            fl = fileLinker.FileLinker(filepath)
            p = fl.linkedPath()
            if p:
                cmn = fileUtil.getCommonParentPath(filepath, p)
                if cmn[0]:
                    return cmn[-1]
            return filename + fl.Extension

        selection_model = self.view().selectionModel()
        model = self.view().model()
        items = []
        for index in selection_model.selectedIndexes():
            if index.column() != 0:
                continue
            data = get_path_from_index(index)
            if data not in items:
                items.append(data)
            i = 0

            while (True):
                child_index = model.index(i, 0, index)
                if not child_index.isValid():
                    break
                i += 1
                data = get_path_from_index(child_index)
                if data in items:
                    continue
                items.append(data)
        return items

    def openInExplorer(self):
        r"""
            選択アイテムをエクスプローラーで開くメソッド。
        """
        paths = self.selectedPathes()
        if len(paths) != 1:
            return
        name, ext = os.path.splitext(paths[0])
        if ext.lower() in ('.mb', '.ma') and os.path.isfile(paths[0]):
            from ...ui import fileLoader
            fileLoader.showAssistance(paths[0], self)
        else:
            from ... import fileUtil
            fileUtil.openFile(paths[0])

    def setPathToChild(self):
        r"""
            子のブラウザへパスを渡す
        """
        paths = self.selectedPathes()
        if len(paths) != 1:
            return
        if not self.child():
            return
        self.child().setPath(paths[0])

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
            self.__context.fileChanged.connect(self.refresh)
        self.__context.setPath(self.path())
        self.__context.setFileNames(self.selectedItems(True))
        self.__context.show()

