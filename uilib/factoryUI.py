#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Factory用に使用するのに便利なUIを提供するモジュール。
    
    Dates:
        date:2017/01/21 23:48[Eske](eske3g@gmail.com)
        update:2021/04/23 09:27 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
import subprocess
import time

from gris3.fileUtil import fileManager
from gris3 import uilib, fileUtil
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

# /////////////////////////////////////////////////////////////////////////////
# ファイルビューワーにまつわる関数・クラス。                                 //
# /////////////////////////////////////////////////////////////////////////////
class ContextOption(QtWidgets.QWidget):
    r"""
        enter description
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ContextOption, self).__init__(parent)
        self.__path = ''
        self.__filenames = []

    def setPath(self, path):
        r"""
            操作対象パスを設定する
            
            Args:
                path (str):
        """
        self.__path = path

    def path(self):
        r"""
            操作対象パスを返す
            
            Returns:
                str:
        """
        return self.__path

    def setFileNames(self, files):
        r"""
            操作対象となるファイルリストを設定する
            
            Args:
                files (list):
        """
        self.__filenames = files

    def fileNames(self):
        r"""
            操作対象となるファイルリストを返す
            
            Returns:
                list:
        """
        return self.__filenames

    def files(self):
        r"""
            操作対象となるファイルのフルパスのリストを返す
            
            Returns:
                list:
        """
        p = self.path()
        return [os.path.join(p, x) for x in self.fileNames()]

    def hiddenTrigger(self):
        r"""
            自動的にGUIを非表示にする。(内部使用専用)
            
            Returns:
                int:
        """
        return 1

    def isScalable(self):
        r"""
            GUIのスケーリングを許可しない
            
            Returns:
                bool:
        """
        return False

    def refresh(self):
        r"""
            内容を更新するヴァーチャルメソッド
        """
        pass

    def contextSize(self):
        r"""
            コンテキストの大きさを返す
            
            Returns:
                int:
        """
        return None


class BrowserContext(uilib.ConstantWidget):
    r"""
        ブラウザに表示するコンテキストメニュー機能を提供するクラス。
    """
    def __init__(self, moduleBrowser):
        r"""
            引数moduleBrowserにはModuleBrowserを渡す必要がある。

            Args:
                moduleBrowser (ModuleBrowser):
        """
        if not isinstance(moduleBrowser, ModuleBrowser):
            raise TypeError(
                '%s is not instance of ModuleBrowser' % moduleBrowser
            )
        super(BrowserContext, self).__init__(moduleBrowser)
        self.setObjectName('GRIS_BROWSER_CONTEXT')
        self.__context_option = None

    def setContextOption(self, contextOption=None):
        r"""
            オプションをセットする。
            この引数になるのはContextOptionクラス(インスタンスではない)
            
            Args:
                contextOption (ContextOption):
        """
        layout = self.layout()
        if not contextOption:
            layout.addStretch()
            self.__context_option = None
            self.setHiddenTrigger(self.HideByFocusOut)
            self.setScalable(False)
            return
        obj = contextOption()
        self.setHiddenTrigger(obj.hiddenTrigger())
        self.setScalable(obj.isScalable())
        size = obj.contextSize()
        obj.hideContext = self.close
        if isinstance(size, (list, tuple)) and len(size) == 2:
            self.resize(size[0], size[1])
        self.__context_option = obj
        layout.addWidget(obj)

    def buildUI(self):
        r"""
            GUIを作成する。
        """
        self.__manager = fileManager.FileManager()
        self.__discarded_manager = None
            
        self.__filenames = []
        self.resize(uilib.hires(200), uilib.hires(160))
        btn_size = 48

        # ラベル。
        label = QtWidgets.QLabel('Manage File')
        label.setStyleSheet('QLabel{font-size:18px;}')
        label.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )

        # ツールバー。=========================================================
        toolbar = QtWidgets.QGroupBox('Tool')
        toolbar.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        
        # Discardボタン。
        discard_btn = uilib.OButton(uilib.IconPath('uiBtn_discarded'))
        discard_btn.setSize(btn_size)
        discard_btn.setBgColor(180, 49, 11)
        discard_btn.setToolTip('Discard selected files.')
        discard_btn.clicked.connect(self.discard)
        
        # Restore用マネージャ起動ボタン。
        disman_btn = uilib.OButton(uilib.IconPath('uiBtn_discardedBack'))
        disman_btn.setSize(btn_size)
        disman_btn.setBgColor(25, 111, 160)
        disman_btn.setToolTip('Show discarded file manager.')
        disman_btn.clicked.connect(self.showDiscardedFileManager)
        
        # To currentボタン。
        cur_btn = uilib.OButton(uilib.IconPath('uiBtn_toCurrent'))
        cur_btn.setSize(btn_size)
        cur_btn.setBgColor(80, 80, 80)
        cur_btn.setToolTip('Change selected file to current.')
        cur_btn.clicked.connect(self.toCurrent)

        t_layout = QtWidgets.QHBoxLayout(toolbar)
        t_layout.setContentsMargins(2, 8, 2, 2)
        t_layout.setSpacing(2)
        t_layout.addWidget(discard_btn)
        t_layout.addWidget(disman_btn)
        t_layout.addSpacing(10)
        t_layout.addWidget(cur_btn)
        t_layout.addStretch()
        # =====================================================================

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(2)
        layout.addWidget(label)
        layout.addWidget(toolbar)

    def setVersionReTemplate(self, template):
        r"""
            Args:
                template (str):
        """
        self.__manager.setVersionReTemplate(template)

    def setCoordinator(self, coordinator):
        r"""
            ファイルリストのフィルタリング関数をセットするメソッド。
            セットする関数は特定のデータを持った辞書型を返す必要がある。
            
            Args:
                coordinator (function):
        """
        self.__manager.setCoordinator(coordinator)

    def setExtensions(self, extensions):
        r"""
            対象拡張子のリストを設定する
            
            Args:
                extensions (list):
        """
        self.__manager.setExtensions(extensions)

    def extensions():
        r"""
            対象拡張子のリストを返す

            Returns:
                list:
        """
        self.__manager.extensions()

    def setPath(self, path):
        r"""
            作業ディレクトリのパスをセットする。
            
            Args:
                path (str):
        """
        self.__manager.setPath(path)
        if self.__context_option:
            self.__context_option.setPath(path)

    def path(self):
        return self.__manager.path()

    def setFileNames(self, fileNames):
        r"""
            処理を行うファイル名のリストをセットするメソッド。
            
            Args:
                fileNames (list):
        """
        self.__filenames = fileNames[:]
        if self.__context_option:
            self.__context_option.setFileNames(self.__filenames)

    def fileNames(self):
        r"""
            処理を行うファイル名のリストを返すメソッド。
            
            Returns:
                list:
        """
        return self.__filenames

    def discard(self):
        r"""
            ファイルをゴミ箱に処理するメソッド。
        """
        self.__manager.discard(self.fileNames())
        self.parent().refresh()

    def showDiscardedFileManager(self):
        r"""
            ゴミ箱処理されたファイルの操作を行うGUIを表示する
        """
        if not self.__discarded_manager:
            from gris3.ui import discardedFileManager
            self.__discarded_manager = discardedFileManager.MainGUI(self)
            self.__discarded_manager.resize(
                uilib.hires(600), uilib.hires(600)
            )
        manager = self.__discarded_manager.main()
        manager.setWorkdir(self.__manager.path())
        self.hide()
        self.__discarded_manager.show()
    
    def toCurrent(self):
        r"""
            選択ファイルをカレントファイルに変更する。
        """
        fileManager.toCurrent(self.path(), self.fileNames())
        self.hide()

    def show(self):
        r"""
            このウィジェットを表示する
        """
        if self.__context_option:
            self.__context_option.refresh()
        super(BrowserContext, self).show()


class MayaAsciiBrowserContext(BrowserContext):
    r"""
        Maya Asciiファイル用のコンテキスト。
        Mayaのファイルに関する情報を表示する。（予定）
    """
    def buildUI(self):
        self.__requires = []
        super(MayaAsciiBrowserContext, self).buildUI()
        self.__grp = uilib.ClosableGroup('Maya file information')
        self.__grp.setIcon(uilib.IconPath('unit'))
        self.__grp.expanded.connect(self.updateRequires)

        model = QtCore.QStringListModel()
        self.__info_list = QtWidgets.QListView()
        self.__info_list.setModel(model)
        
        label = QtWidgets.QLabel('Requires')
        layout = QtWidgets.QHBoxLayout(self.__grp)
        layout.addWidget(label)
        layout.addWidget(self.__info_list)

        layout = self.layout()
        layout.addWidget(self.__grp)
        self.resize(uilib.hires(400), uilib.hires(400))
        self.__grp.setExpanding(False)

    def setContextOption(self, contextOption=None):
        super(MayaAsciiBrowserContext, self).setContextOption(contextOption)
        if contextOption is None:
            self.setScalable(True)

    def updateRequires(self, isShown):
        model = self.__info_list.model()
        if not isShown:
            return
        if self.__requires:
            return
        names = self.fileNames()
        if not names:
            return
        target_path = os.path.join(self.path(), names[-1])
        from ..tools.fileChecker import core, requires_checker
        checker = core.DataChckerManager()
        checker.install(requires_checker)
        data = checker.check_file(target_path)
        if not data:
            return
        self.__requires = [
            x.strip() for x in data['Requires'][1].split('\n')[1:]
        ]
        model.setStringList(self.__requires)

    def show(self):
        self.__grp.setExpanding(False)
        self.__requires = []
        super(MayaAsciiBrowserContext, self).show()


class ModuleBrowserModel(QtGui.QStandardItemModel):
    r"""
        ModuleBrowser専用のItemModelを提供するクラス。
    """
    def __init__(self, itemview):
        r"""
            Args:
                itemview (QtWidgets.QAbstractItemView):
        """
        super(ModuleBrowserModel, self).__init__(0, 2)
        self.setHeaderData(0, QtCore.Qt.Horizontal, 'File')
        self.setHeaderData(1, QtCore.Qt.Horizontal, 'Date')
        self.__itemview = itemview

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


class ModuleBrowser(QtWidgets.QTreeView):
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
    # =========================================================================

    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        icon_size = uilib.hires(28)
        super(ModuleBrowser, self).__init__(parent)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setHorizontalScrollMode(self.ScrollPerPixel)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setDragEnabled(True)
        self.setIconSize(QtCore.QSize(icon_size, icon_size))
        self.clicked.connect(self.setPathToChild)
        self.doubleClicked.connect(self.openInExplorer)
        self.setEditTriggers(self.NoEditTriggers)
        self.__child = None
        self.__path = ''
        self.__customFilters = []
        self.__coodinator = fileManager.coordinateFiles
        self.__extensions = ['ma']
        self.__context = None
        self.__extra_context = None
        self.__browser_context = BrowserContext
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContext)
        self.setVersionFormat(fileManager.VersionFileReTemplte)
        self.setExtensionVisibles(False)

        model = ModuleBrowserModel(self)
        self.setModel(model)
        self.setColumnWidth(0, uilib.hires(220))

        sel_model = QtCore.QItemSelectionModel(model)
        self.setSelectionModel(sel_model)

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
            セットする関数は特定のデータを持った辞書型を返す必要がある。
            
            Args:
                function (function):
        """
        self.__coodinator = function

    def coordinate(self, filelist, extensions, versionFormat):
        r"""
            ファイルリストのフィルタリングを実行するメソッド。
            フィルタリングにはsetCoodinatorでセットされたメソッドを使用する。
            
            Args:
                filelist (list):
                extensions (list):
                versionFormat (str):正規表現
                
            Returns:
                any:
        """
        return self.__coodinator(filelist, extensions, versionFormat)

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
                        os.path.join(parent_path, filelist[0]['name'])
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

        model = self.model()
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
        selectionModel = self.selectionModel()
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
        selectionModel = self.selectionModel()
        # 子階層を含まない場合。===============================================
        if not includeChildren:
            return [
                x.data(QtCore.Qt.UserRole + 1)
                for x in selectionModel.selectedIndexes() if x.column() == 0
            ]
        # =====================================================================

        root_index = self.model().indexFromItem(
            self.model().invisibleRootItem()
        )
        items = []
        for index in selectionModel.selectedIndexes():
            if index.column() != 0:
                continue
            items.append(index.data(QtCore.Qt.UserRole + 1))
            i = 0
            while(True):
                child_index = index.child(i, 0)
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
            self.__context.setCoordinator(self.__coodinator)
            self.__context.setExtensions(self.__extensions)
            self.__context.setVersionReTemplate(self.versionFormat())
            self.__context.setContextOption(self.__extra_context)
        self.__context.setPath(self.path())
        self.__context.setFileNames(self.selectedItems(True))
        self.__context.show()


class ModuleBrowserWidget(QtWidgets.QWidget):
    r"""
        ModuleBrowserの上位互換ウィジェット。
        リフレッシュボタンやエクスプローラーで開くボタンなどが追加されている他、
        メソッド的にもほぼModuleBrowserを踏襲している。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget): 親ウィジェット。
        """
        super(ModuleBrowserWidget, self).__init__(parent)
        
        self.__browser = ModuleBrowser()
        # ブラウザのメソッドをそのまま移植する。===============================
        self.setLabel = self.__browser.setLabel
        self.installCustomFilter = self.__browser.installCustomFilter
        self.customFilter = self.__browser.customFilter
        self.setCoordinator = self.__browser.setCoordinator
        self.coordinate = self.__browser.coordinate
        self.refresh = self.__browser.refresh
        self.setPath = self.__browser.setPath
        self.path = self.__browser.path
        self.setExtensions = self.__browser.setExtensions
        self.selectedPathes = self.__browser.selectedPathes
        self.selectedItems = self.__browser.selectedItems
        self.openInExplorer = self.__browser.openInExplorer
        self.showContext = self.__browser.showContext
        self.setBrowserContext = self.__browser.setBrowserContext
        self.clicked = self.__browser.clicked
        self.doubleClicked = self.__browser.doubleClicked
        self.setExtraContext = self.__browser.setExtraContext
        
        self.versionFormat = self.__browser.versionFormat
        self.setVersionFormat = self.__browser.setVersionFormat
        self.extensionVisibles = self.__browser.extensionVisibles
        self.setExtensionVisibles = self.__browser.setExtensionVisibles
        # =====================================================================

        # ツールバー。=========================================================
        refresh_btn = QtWidgets.QPushButton()
        refresh_btn.setFlat(True)
        refresh_btn.setIcon(uilib.Icon('uiBtn_reload'))
        refresh_btn.setToolTip('Refresh Browser')
        refresh_btn.clicked.connect(self.refresh)
        
        open_exp_btn = QtWidgets.QPushButton()
        open_exp_btn.setFlat(True)
        open_exp_btn.setIcon(uilib.Icon('uiBtn_directory'))
        open_exp_btn.setToolTip('Open Directory in Explorer...')
        open_exp_btn.clicked.connect(self.openRootDir)

        tool_layout = QtWidgets.QHBoxLayout()
        tool_layout.setContentsMargins(0, 0, 0, 0)
        tool_layout.setSpacing(2)
        tool_layout.setDirection(QtWidgets.QBoxLayout.RightToLeft)

        icon_size = uilib.hires(20)
        max_size = uilib.hires(24)
        for btn in (refresh_btn, open_exp_btn):
            btn.setIconSize(QtCore.QSize(icon_size, icon_size))
            btn.setMaximumSize(QtCore.QSize(max_size, max_size))
            tool_layout.addWidget(btn)
        tool_layout.addStretch()
        # =====================================================================

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        layout.addLayout(tool_layout)
        layout.addWidget(self.__browser)

    def browser(self):
        r"""
            セットされているブラウザオブジェクトを返すメソッド。
            
            Returns:
                ModuleBrowser:
        """
        return self.__browser

    def openRootDir(self):
        r"""
            ルートパスをExplorerで開くメソッド。
        """
        fileUtil.openDir(self.path())

    def copyPath(self):
        r"""
            選択ファイルのパスのリストをクリップボードへコピーする
        """
        QtWidgets.QApplication.clipboard().setText(
            '\n'.join(self.selectedPathes())
        )

    def keyPressEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        key = event.key()
        mod = event.modifiers()
        if mod == QtCore.Qt.ControlModifier:
            if key == QtCore.Qt.Key_C:
                self.copyPath()
                return
        super(ModuleBrowserWidget, self).keyPressEvent(event)


class FileView(QtWidgets.QWidget):
    r"""
        ファイルの一覧および保存をするためのUIを提供するクラス。
    """
    exportButtonClicked = QtCore.Signal(str, str)
    def __init__(self):
        super(FileView, self).__init__()

        browser = ModuleBrowserWidget()
        browser.installCustomFilter(ModuleBrowser.removeCurFilter)
        browser.clicked.connect(self.updateBasename)
        self.setBrowserContext = browser.setBrowserContext

        # ファイルパスに関するUI。=============================================
        basename_label = QtWidgets.QLabel('Basename')
        self.__basename = self.createBasenameEditor()

        self.__isOverwrite = QtWidgets.QCheckBox('Overwrite to latest')
        self.__isOverwrite.setChecked(False)
        
        exp_button = uilib.OButton()
        exp_button.setIcon(uilib.IconPath('uiBtn_export'))
        exp_button.setBgColor(48, 138, 158)
        exp_button.setSize(48)
        exp_button.clicked.connect(self.execute)

        grp = QtWidgets.QGroupBox()
        grp_layout = QtWidgets.QGridLayout(grp)
        grp_layout.setContentsMargins(2, 2, 2, 2)
        grp_layout.addWidget(basename_label, 0, 0, 1, 1)
        grp_layout.addWidget(self.__basename, 0, 1, 1, 1)
        grp_layout.addWidget(self.__isOverwrite, 1, 0, 1, 2)
        grp_layout.addWidget(exp_button, 0, 2, 2, 1)
        # =====================================================================

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(1)
        layout.addWidget(browser)
        layout.addWidget(grp)

        self.__browser = browser
        self.__button = exp_button

        self.addOptionWidget = grp_layout.addWidget
        self.addOptionLayout = grp_layout.addLayout

    def createBasenameEditor(self):
        r"""
            ベースネームを編集するウィジェットを作成し返す。
            返すウィジェットはsetTextとtextメソッドを持つ必要がある。
            
            Returns:
                QtWidgets.QWidget:
        """
        return QtWidgets.QLineEdit()

    def setExtensions(self, extensions):
        r"""
            ブラウザが対応する拡張子をセットする。
            
            Args:
                extensions (list):
        """
        self.browser().setExtensions(extensions)

    def browser(self):
        r"""
            ブラウザを返すメソッド。
            
            Returns:
                ModuleBrowserWidget:
        """
        return self.__browser

    def basenameEdit(self):
        r"""
            ベースネームをセットするためのウィジェットを返す。
            
            Returns:
                QtWidgets.QLineEdit:
        """
        return self.__basename

    def setBrowserLabel(self, label):
        r"""
            ブラウザのラ・ベルを設定する。
            
            Args:
                label (str):
        """
        self.browser().setLabel(label)

    def setButtonIcon(self, iconPath):
        r"""
            ボタンのアイコンを変更する。
            
            Args:
                iconPath (str):
        """
        self.__button.setIcon(iconPath)

    def setButtonLabel(self, label):
        r"""
            ボタンのツールチップを変更する。
            
            Args:
                label (str):
        """
        self.__button.setToolTip(label)

    def updateBasename(self):
        r"""
            ファイルのベースの名前を更新する
        """
        selected = self.__browser.selectedItems()
        if not selected:
            return
        name = os.path.basename(selected[0])
        self.__basename.setText(name)

    def setRootPath(self, path):
        r"""
            ルートディレクトリのパスをセットする
            
            Args:
                path (str):
        """
        self.__browser.setPath(path)
        path = self.__browser.path()
        self.setEnabled(bool(path))

    def path(self):
        r"""
            ルートディレクトリのパスを返す。
            
            Returns:
                str:
        """
        return self.browser().path()

    def filename(self):
        r"""
            ファイルネームを返す
            
            Returns:
                str:
        """
        return self.__basename.text()

    def isOverwrite(self):
        r"""
            上書きするかどうかを返すメソッド。
            
            Returns:
                bool:
        """
        return self.__isOverwrite.isChecked()

    def execute(self):
        r"""
            入力されている名前をexportButtonClickedシグナルで送出する
        """
        rootpath = self.path()
        filename = self.filename()
        if not filename:
            raise ValueError('The file name is empty.')

        if not os.path.isdir(rootpath):
            raise ValueError(
                'The parent directory was not found : %s' % rootpath
            )
        self.exportButtonClicked.emit(rootpath, filename)
        self.__isOverwrite.setChecked(False)
        self.browser().refresh()
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////



# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////
class ToolBar(QtWidgets.QScrollArea):
    r"""
        ドラッグによるスクロール可能なツールバー機能を提供する
    """
    def __init__(self, parent=None, isButtonGrouped=False):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
                isButtonGrouped (bool):ボタンをグループ化するかどうか
        """
        super(ToolBar, self).__init__(parent)
        self.setStyleSheet(
            'QScrollArea{'
            'background:transparent; border:none;'
            'margin : 0px;'
            '}'
        )
        self.setWidgetResizable(True)
        self.setContentsMargins(0, 0, 0, 0)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        self.__prepos  = None
        self.__ismoved = False
        self.__pressed_time = 0

        widget = QtWidgets.QWidget()
        widget.setStyleSheet(
            'QWidget{background:transparent;}'
        )
        self.__layout = QtWidgets.QHBoxLayout(widget)
        self.__layout.setSpacing(2)
        self.__layout.setContentsMargins(0, 0, 0, 0)
        self.__layout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.__layout.addStretch()

        self.setWidget(widget)
        self.setButtonSize(32)

        if isButtonGrouped:
            self.__btn_grp = QtWidgets.QButtonGroup()
            self.buttonClicked = self.__btn_grp.buttonClicked[int]
        else:
            self.__btn_grp = None
            self.buttonClicked = QtCore.Signal(int)

    def setAlighment(self, alignment):
        r"""
            ツールバーのボタン配置の整列方向を指定する
            
            Args:
                alignment (QtCore.Qt.Alignment):
        """
        self.__layout.setAlignment(alignment)

    def scroll(self, moveValues):
        r"""
            このウィジェットのビューポートをスクロールさせるメソッド。
            
            Args:
                moveValues (list):
        """
        h_scroll = self.horizontalScrollBar()
        v_scroll = self.verticalScrollBar()
        for scroll, value in zip(
            [h_scroll, v_scroll], [moveValues.x(), moveValues.y()]
        ):
            scroll.setValue(scroll.value() - value)

    def mousePressEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        button = event.button()
        self.__prepos = event.pos()
        super(ToolBar, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):                
        """
        if not self.__prepos:
            super(ToolBar, self).mouseMoveEvent(event)
            return
        current_pos = event.pos()
        delta = current_pos - self.__prepos
        self.__prepos = current_pos
        self.scroll(delta)
    
    def mouseReleaseEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        self.__prepos = None
        super(ToolBar, self).mouseReleaseEvent(event)

    def setButtonSize(self, size):
        r"""
            ボタンの大きさを指定する
            
            Args:
                size (int):
        """
        self.__size = size
        self.setMaximumHeight(uilib.hires(size+2))

    def addButton(self, icon=None, toolTip=''):
        r"""
            ボタンを追加する
            
            Args:
                icon (str):ボタンに配置するアイコン
                toolTip (str):ボタンに付けるツールチップ
                
            Returns:
                uilib.OButton:
        """
        btn = uilib.OButton(icon)
        btn.setSize(self.__size)
        btn.setToolTip(toolTip)
        btn.installEventFilter(self)
        index = self.__layout.count()-1
        self.__layout.insertWidget(index, btn)
        if self.__btn_grp:
            self.__btn_grp.addButton(btn, index)
            btn.setCheckable(True)
            if index == 0:
                btn.setChecked(True)
        else:
            btn.clicked.connect(self.clickedCallback)
        return btn

    def clickedCallback(self):
        r"""
            ボタンをクリックされた時に呼ばれるコールバック
        """
        index = self.__layout.indexOf(self.sender())
        self.buttonClicked.emit(index)

    def eventFilter(self, object, event):
        r"""
            Args:
                object (QtCore.QObject):
                event (QtCore.QEvent):
        """
        event_type = event.type()
        if event_type == QtCore.QEvent.MouseButtonPress:
            self.mousePressEvent(event)
            self.__ismoved = False
            self.__pressed_time = time.time()
            return False
        elif event_type == QtCore.QEvent.MouseMove:
            self.mouseMoveEvent(event)
            self.__ismoved = True
            return True
        elif event_type == QtCore.QEvent.MouseButtonRelease:
            if self.__ismoved:
                hold_time = time.time() - self.__pressed_time
                self.__ismoved = False
                self.mouseReleaseEvent(event)
                
                if hold_time > 0.4:
                    return True
            return False
        else:
            return False


class ToolTabWidget(QtWidgets.QWidget):
    r"""
        ツールバー付きのタブ機能を提供するクラス。
    """
    SaveColor = (62, 79, 210)
    ToolColor = (48, 156, 102)
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ToolTabWidget, self).__init__(parent)

        self.__tab = uilib.ScrolledStackedWidget(self)
        self.__toolbar = ToolBar(self, True)
        self.__toolbar.buttonClicked.connect(self.__tab.moveTo)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.__toolbar)
        layout.addWidget(self.__tab)
        
        self.setCurrentIndex = self.__tab.setCurrentIndex

    def setToolBarSize(self, size):
        r"""
            ツールバーのボタンサイズを設定する。
            
            Args:
                size (int):
        """
        self.__toolbar.setButtonSize(size)

    def addTab(self, widget, icon=None, toolTip=''):
        r"""
            タブを追加する。
            
            Args:
                widget (QtWidgets.QWidget):
                icon (str):アイコンのパス
                toolTip (str):ツールチップ
                
            Returns:
                uilib.OButton:
        """
        btn = self.__toolbar.addButton(icon, toolTip)
        self.__tab.addTab(widget)
        return btn
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////