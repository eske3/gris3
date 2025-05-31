#!/usr/bin/python
# -*- coding: utf-8 -*-
r'''
    @file     archiver.py
    @brief    ジョイントの編集機能を提供するGUI。
    @class    ArchiveDataView       : アーカイブを行うためのUIを提供するクラス。
    @class    ArchiveProgressWidget : アーカイブ経過表示ウィジェット
    @class    RigDataArchiver       : ジョイントの作成、編集を行うためのツールを提供するクラス。
    @class    MainGUI               : ここに説明文を記入
    @function coordinateFiles       : ScriptManagerに表示するファイルのフィルタ用関数。
    @function showWindow            : ウィンドウを作成するためのエントリ関数。
    @date     2017/06/15 16:35[Eske](eske3g@gmail.com)
    @update   2020/04/07 15:10[eske3g@gmail.com]
    このソースの版権は[EskeYoshinob]にあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[EskeYoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
import re, os
from gris3 import lib, uilib, node
from gris3.uilib import factoryUI
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


def coordinateFiles(files, extensions, format):
    # type: (list,list,str) -> dict
    r'''
        @brief  ScriptManagerに表示するファイルのフィルタ用関数。
        @param  files(list)      : ファイルPASのリスト
        @param  extensions(list) : 拡張子のリスト
        @param  format(str)      : 
        @return (dict):
    '''
    reobj = re.compile(format % '|'.join(extensions))
    matchedFiles = {}
    files = [os.path.basename(x) for x in files]
    files.sort()
    for file in files:
        r = reobj.search(file)
        if not r:
            continue
        data = {
            'ver':r.group(3) if r.group(3) else 'cur',
            'sep':r.group(2), 'name':file, 'ext':r.group(3),
            'simpleName':reobj.sub(r'\1\2\3', file)
        }
        if r.group(1) in matchedFiles:
            matchedFiles[r.group(1)].append(data)
        else:
            matchedFiles[r.group(1)] = [data]
    return matchedFiles

class ArchiveDataView(QtWidgets.QWidget):
    r'''
        @brief    アーカイブを行うためのUIを提供するクラス。
        @inherit  QtWidgets.QWidget
        @function view : ファイル一覧表示用のウィジェットを返す
        @date     2019/10/29 11:04[eske3g@gmail.com]
        @update   2020/04/07 15:10[eske3g@gmail.com]
    '''
    def __init__(self, parent=None):
        # type: (QtWidgets.QWidget) -> any
        r'''
            @brief  初期化を行う
            @param  parent(QtWidgets.QWidget) : 親ウィジェット
            @return (any):
        '''
        super(ArchiveDataView, self).__init__()
        label = QtWidgets.QLabel('Archive')
        arc_btn = uilib.OButton(uilib.IconPath('uiBtn_save'))
        arc_btn.setSize(64)
        arc_btn.setBgColor(166, 49, 32)
        self.buttonClicked = arc_btn.clicked

        self.__view = factoryUI.ModuleBrowserWidget()
        self.__view.setExtensions('zip')
        self.__view.setCoordinator(coordinateFiles)
        self.__view.setVersionFormat('^(.*?)(\.|)(v\d+|)\.(%s)$')

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(arc_btn, 1, 0, 1, 1, QtCore.Qt.AlignRight)
        layout.addWidget(
            label, 2, 0, 1, 1, QtCore.Qt.AlignTop|QtCore.Qt.AlignHCenter
        )
        layout.addWidget(self.__view, 0, 1, 4, 1)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(0, 1)
        layout.setRowStretch(3, 1)

    def view(self):
        # type: () -> factoryUI.ModuleBrowserWidget
        r'''
            @brief  ファイル一覧表示用のウィジェットを返す
            @return (factoryUI.ModuleBrowserWidget):
        '''
        return self.__view

class ArchiveProgressWidget(QtWidgets.QWidget):
    r'''
        @brief    アーカイブ経過表示ウィジェット
        @inherit  QtWidgets.QWidget
        @function setup      : プログレスバーの最小・最大値を設定する
        @function setMessage : ステータス進行表示用メッセージを設定する
        @function goNext     : プログレスバーを次のステップへ進める
        @date     2019/10/29 11:04[eske3g@gmail.com]
        @update   2020/04/07 15:10[eske3g@gmail.com]
    '''
    def __init__(self, parent=None):
        # type: (QtWidgets) -> any
        r'''
            @brief  初帰化を行う
            @param  parent(QtWidgets) : 親ウィジェット
            @return (any):
        '''
        super(ArchiveProgressWidget, self).__init__(parent)
        self.__message = QtWidgets.QLabel('Processing...')
        self.__progress = QtWidgets.QProgressBar()
        cancel_btn = uilib.OButton(uilib.IconPath('uiBtn_x'))
        cancel_btn.setToolTip('Cancel archiving')
        cancel_btn.setBgColor(180, 32, 58)
        cancel_btn.setSize(32)

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(self.__progress, 0, 0, 1, 2)
        layout.addWidget(self.__message, 1, 0, 1, 1)
        layout.addWidget(cancel_btn, 1, 1, 1, 1)
        layout.setColumnStretch(0, 1)
        layout.setRowStretch(2, 1)

        self.buttonClicked = cancel_btn.clicked

    def setup(self, minValue, maxValue):
        # type: (int,int) -> any
        r'''
            @brief  プログレスバーの最小・最大値を設定する
            @param  minValue(int) : 最小値
            @param  maxValue(int) : 最大値
            @return (any):
        '''
        self.__progress.setRange(minValue, maxValue)
        self.__progress.setValue(minValue)

    def setMessage(self, message):
        # type: (str) -> any
        r'''
            @brief  ステータス進行表示用メッセージを設定する
            @param  message(str) : 
            @return (any):
        '''
        self.__message.setText(message)

    def goNext(self, message=None):
        # type: (str) -> any
        r'''
            @brief  プログレスバーを次のステップへ進める
            @param  message(str) : プログレスバーに変更を加えるメッセージ
            @return (any):
        '''
        self.__progress.setValue(self.__progress.value()+1)
        if message:
            self.__progress.setFormat('%p% : '+message)

class RigDataArchiver(uilib.ClosableGroup):
    r'''
        @brief    ジョイントの作成、編集を行うためのツールを提供するクラス。
        @inherit  uilib.ClosableGroup
        @function view           : ファイル一覧表示用のウィジェットを返す
        @function refreshView    : ファイルビューワの更新を行う
        @function setupProgress  : プログレスバーの初期状態を変更する
        @function updateProgress : プログレスバーの状況を更新する
        @function finished       : アーカイブ終了時のUI更新処理
        @function archive        : アーカイブを実行する
        @function cancel         : アーカイブ処理を中断する。
        @date     2017/07/01 4:07[Eske](eske3g@gmail.com)
        @update   2020/04/07 15:10[eske3g@gmail.com]
    '''
    def __init__(self, parent=None):
        # type: (QtWidgets.QWidget) -> any
        r'''
            @brief  初期化を行う。
            @param  parent(QtWidgets.QWidget) : 親ウィジェット
            @return (any):
        '''
        super(RigDataArchiver, self).__init__('Archive Rig Project')
        self.setIcon(uilib.IconPath('uiBtn_save'))

        self.__stacked = QtWidgets.QStackedWidget()
        self.__dataview = ArchiveDataView()
        self.__dataview.buttonClicked.connect(self.archive)

        self.__progress = ArchiveProgressWidget()
        self.__progress.buttonClicked.connect(self.cancel)
        
        self.__stacked.addWidget(self.__dataview)
        self.__stacked.addWidget(self.__progress)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.__stacked)

        from gris3 import qtArchive
        self.__archiver = qtArchive.ArchiverThread(self)
        self.__archiver.StageChanged.connect(self.updateProgress)
        self.__archiver.MessageSent.connect(self.__progress.setMessage)
        self.__archiver.NumberOfStepsDecided.connect(self.setupProgress)
        self.__archiver.finished.connect(self.finished)
        self.__progress.setup(0, 0)

        self.setExpanding(False)

    def view(self):
        # type: () -> factoryUI.ModuleBrowserWidget
        r'''
            @brief  ファイル一覧表示用のウィジェットを返す
            @return (factoryUI.ModuleBrowserWidget):
        '''
        return self.__dataview.view()

    def refreshView(self):
        r'''
            @brief  ファイルビューワの更新を行う
            @return (any):
        '''
        self.view().refresh()

    def setupProgress(self, numberOfSteps):
        # type: (int) -> any
        r'''
            @brief  プログレスバーの初期状態を変更する
            @param  numberOfSteps(int) : 総ステップ数
            @return (any):
        '''
        self.__progress.setup(0, numberOfSteps)

    def updateProgress(self, stage, message):
        # type: (int,str) -> any
        r'''
            @brief  プログレスバーの状況を更新する
            @param  stage(int)   : ステップ数
            @param  message(str) : 表示するメッセージ
            @return (any):
        '''
        self.__progress.goNext(message)

    def finished(self):
        r'''
            @brief  アーカイブ終了時のUI更新処理
            @return (any):
        '''
        self.__stacked.setCurrentIndex(0)
        self.refreshView()

    def archive(self):
        r'''
            @brief  アーカイブを実行する
            @return (any):
        '''
        self.__archiver.setup()
        self.__archiver.start()
        self.__stacked.setCurrentIndex(1)

    def cancel(self):
        r'''
            @brief  アーカイブ処理を中断する。
            @return (any):
        '''
        self.__archiver.stop()
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        self.__archiver.wait()
        self.__stacked.setCurrentIndex(0)
        self.refreshView()
        QtWidgets.QApplication.restoreOverrideCursor()

class MainGUI(uilib.AbstractSeparatedWindow):
    r'''
        @brief    ここに説明文を記入
        @inherit  uilib.AbstractSeparatedWindow
        @function centralWidget : ここに説明文を記入
        @date     2017/06/27 18:31[s_eske](eske3g@gmail.com)
        @update   2020/04/07 15:10[eske3g@gmail.com]
    '''
    def centralWidget(self):
        r'''
            @brief  ここに説明文を記入
            @return (any):None
        '''
        return RigDataArchiver()


def showWindow():
    r'''
        @brief  ウィンドウを作成するためのエントリ関数。
        @return (any):QtWidgets.QWidget
    '''
    from gris3.uilib import mayaUIlib
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(480, 320)
    widget.show()
    return widget