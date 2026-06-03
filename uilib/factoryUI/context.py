#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Factory用のコンテクストメニューを提供するクラス。

    Dates:
        date:2017/01/21 23:48[Eske](eske3g@gmail.com)
        update:2026/05/16 19:13 eske yoshinob[eske3g@gmail.com]

    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
from ... import uilib
from ...fileUtil import fileManager, fileLinker
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


def listFilenamesFromData(
        fileData, includeChildren=True, expandLinkedPath=True
):
    r"""
        Args:
            fileData(list):
            includeChildren(bool):

        Returns:
            list:
    """
    if expandLinkedPath:
        get_path = lambda x: x[1] if x[1] else x[0]
    else:
        get_path = lambda x: x[0]

    results = []
    for data in fileData:
        file = get_path(data)
        if file not in results:
            results.append(file)
        if not includeChildren:
            continue
        files = [get_path(x) for x in data[-1]]
        results.extend([x for x in files if x not in results])
    return results


class ContextOption(QtWidgets.QWidget):
    r"""
        コンテクストメニューの追加オプションを定義する基底クラス。
    """

    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ContextOption, self).__init__(parent)
        self.__path = ''
        self.__filedata = []

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

    def setFileData(self, fileData):
        r"""
            処理を行うファイル名のリストをセットする。
            引数fileDataの中身は
                ・選択アイテムのパス
                ・リンクの指すパス（選択アイテムがリンカーの場合）
                ・子のファイル（includeChildrenがTrueの場合）
            の３つのデータを持つtupleのリスト。

            Args:
                fileData (list):
        """
        self.__filedata = fileData

    def fileNames(self, includeChildren=True, expandLinkedPath=False):
        r"""
            操作対象となるファイルリストを返す。
            includeChildrenがTrueの場合、操作対象ファイルの子ファイルも合わせて返す。
            expandLinkedPathがTrueの場合、戻り値の中にある操作対象ファイルのうち、
            リンカーファイルはリンク先のパスに変換する。

            Args:
                includeChildren (bool):
                expandLinkedPath (bool):

            Returns:
                list:
        """
        return listFilenamesFromData(
            self.__filedata, includeChildren, expandLinkedPath
        )

    def files(self, includeChildren=True, expandLinkedPath=False):
        r"""
            操作対象となるファイルのフルパスのリストを返す。
            引数はfileNamesと同じ内容。

            Args:
                includeChildren (bool):
                expandLinkedPath (bool):

            Returns:
                list:
        """
        p = self.path()
        return [
            os.path.join(p, x)
            for x in self.fileNames(includeChildren, expandLinkedPath)
        ]

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
    fileChanged = QtCore.Signal()

    def __init__(self, moduleBrowser):
        r"""
            引数moduleBrowserにはModuleBrowserを渡す必要がある。

            Args:
                moduleBrowser (ModuleBrowser):
        """
        self.__manager = None
        self.__discarded_manager = None
        self.__filedata = []
        self.__context_option = None
        super(BrowserContext, self).__init__(moduleBrowser)
        self.setObjectName('GRIS_BROWSER_CONTEXT')

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
        self.setScalable(True)
        self.resize(uilib.hires(400), uilib.hires(160))
        btn_size = 48

        # ラベル。
        self.__file_label = QtWidgets.QLabel('Manage File')
        self.__file_label.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        self.__file_label.setMinimumWidth(10)

        self.__linked_label = QtWidgets.QLabel('Path')
        self.__linked_label.setStyleSheet('QLabel{font-size:12;}')
        self.__linked_label.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        self.__linked_label.setMinimumWidth(10)

        # ツールバー。=========================================================
        toolbar = QtWidgets.QGroupBox('Tool')
        toolbar.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )

        # Discardボタン。
        discard_btn = uilib.OButton(uilib.IconPath('uiBtn_trush'))
        discard_btn.setSize(btn_size)
        discard_btn.setBgColor(180, 49, 11)
        discard_btn.setToolTip('Discard selected files.')
        discard_btn.clicked.connect(self.discard)

        # Restore用マネージャ起動ボタン。
        disman_btn = uilib.OButton(uilib.IconPath('uiBtn_discarded'))
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
        self.__cur_btn = cur_btn

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
        layout.addWidget(self.__file_label)
        layout.addWidget(self.__linked_label)
        layout.addSpacing(20)
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

    def extensions(self):
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

    def hasLinker(self):
        for data in self.__filedata:
            if data[1]:
                return True
            for subdata in data[-1]:
                if subdata[1]:
                    return True
        return False

    def setFileData(self, fileData):
        r"""
            処理を行うファイル名のリストをセットする。
            引数fileDataの中身は
                ・選択アイテムのパス
                ・リンクの指すパス（選択アイテムがリンカーの場合）
                ・子のファイル（includeChildrenがTrueの場合）
            の３つのデータを持つtupleのリスト。

            Args:
                fileData (list):
        """
        self.__filedata = fileData[:]
        if self.__context_option:
            self.__context_option.setFileData(self.__filedata)

        cur_btn_enabled = not self.hasLinker()
        label = ''
        linked = ''
        if fileData:
            fl = fileLinker.getFileLinker(
                os.path.join(self.path(), fileData[0][0])
            )
            if fl:
                name = os.path.basename('{} (link)'.format(fl.path()))
                linked = 'Link to : {}'.format(
                    os.path.basename(fl.linkedPath())
                )
            else:
                name = fileData[0][0]
            label = '<span style="font-size:15pt;">{}</span>'.format(name)

            num = len(fileData)
            for data in fileData:
                num += len(data[-1])

            if num > 1:
                label = (
                    '{} <span style="font-size:8pt;">+ {} files...</span>'
                ).format(label, num-1)

        self.__cur_btn.setEnabled(cur_btn_enabled)
        self.__file_label.setText(label)
        self.__linked_label.setText(linked)

    def fileNames(self, includeChildren=True, expandLinkedPath=False):
        r"""
            操作対象となるファイルリストを返す。
            includeChildrenがTrueの場合、操作対象ファイルの子ファイルも合わせて返す。
            expandLinkedPathがTrueの場合、戻り値の中にある操作対象ファイルのうち、
            リンカーファイルはリンク先のパスに変換する。

            Args:
                includeChildren (bool):
                expandLinkedPath (bool):

            Returns:
                list:
        """
        return listFilenamesFromData(
            self.__filedata, includeChildren, expandLinkedPath
        )

    def discard(self):
        r"""
            ファイルをゴミ箱に処理するメソッド。
        """
        self.__manager.discard(self.fileNames())
        self.fileChanged.emit()
        self.hide()

    def showDiscardedFileManager(self):
        r"""
            ゴミ箱処理されたファイルの操作を行うGUIを表示する
        """
        if not self.__discarded_manager:
            from ...ui import discardedFileManager
            self.__discarded_manager = discardedFileManager.MainGUI(self)
            self.__discarded_manager.resize(
                uilib.hires(600), uilib.hires(600)
            )
            self.__discarded_manager.main().fileRestored.connect(
                self.fileChanged.emit
            )
        manager = self.__discarded_manager.main()
        manager.setWorkdir(self.__manager.path())
        self.hide()
        self.__discarded_manager.show()

    def toCurrent(self):
        r"""
            選択ファイルをカレントファイルに変更する。
        """
        fileManager.toCurrent(
            self.path(), self.fileNames()
        )
        self.hide()
        self.fileChanged.emit()

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
        Mayaのファイルに関する情報を表示する。
    """
    def __init__(self, moduleBrowser):
        self.__requires = False
        super().__init__(moduleBrowser)


    def buildUI(self):
        super(MayaAsciiBrowserContext, self).buildUI()
        self.__grp = uilib.ClosableGroup('Maya file information')
        self.__grp.setIcon(uilib.IconPath('unit'))
        self.__grp.expanded.connect(self.updateRequires)

        model = QtGui.QStandardItemModel()
        self.__info_list = QtWidgets.QTreeView()
        self.__info_list.setVerticalScrollMode(
            QtWidgets.QAbstractItemView.ScrollPerPixel
        )
        self.__info_list.setHorizontalScrollMode(
            QtWidgets.QAbstractItemView.ScrollPerPixel
        )
        self.__info_list.setIconSize(QtCore.QSize(32, 32))
        self.__info_list.setHeaderHidden(True)
        self.__info_list.setRootIsDecorated(False)
        self.__info_list.setModel(model)
        self.__info_list.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)

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
        model: QtGui.QStandardItemModel = self.__info_list.model()
        if not isShown:
            return
        if self.__requires:
            return
        names = self.fileNames(includeChildren=False, expandLinkedPath=True)
        if not names:
            return

        model.removeRows(0, model.rowCount())
        from ...tools.fileChecker import core, requires_checker
        checker = core.DataChckerManager()
        checker.install(requires_checker)
        parent_path = self.path()
        is_single = len(names) == 1

        for name in names:
            data = checker.check_file(os.path.join(parent_path, name))
            if not data:
                continue

            if not is_single:
                parent_item = QtGui.QStandardItem(name)
                parent_item.setIcon(QtGui.QIcon(uilib.IconPath('unit')))
                model.setItem(model.rowCount(), 0, parent_item)
            else:
                parent_item = model.invisibleRootItem()
            for d in [x.strip() for x in data['Requires'][1].split('\n')[1:]]:
                item = QtGui.QStandardItem(d)
                parent_item.setChild(parent_item.rowCount(), 0, item)
        self.__info_list.expandAll()
        self.__requires = True

    def show(self):
        self.__grp.setExpanding(False)
        self.__requires = False
        super(MayaAsciiBrowserContext, self).show()

