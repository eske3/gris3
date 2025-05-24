#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    アニメーションやポーズのライブラリを作成、管理するための機能。
    
    Dates:
        date:2017/03/17 3:10[Eske](eske3g@gmail.com)
        update:2021/01/19 17:34 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
from gris3 import uilib
from gris3.uilib import mayaUIlib
from ...ui import imageViewer
from . import core
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

# 入力ダイアログに関するクラス、定数、関数。///////////////////////////////////
class InputDialog(uilib.BlackoutDisplay):
    r"""
        入力ダイアログ機能を提供するクラス
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(InputDialog, self).__init__(parent)
        self.__accpept_callback = None
        self.__thumbnail_path = ''

        self.__title = QtWidgets.QLabel()
        self.__title.setStyleSheet(
            'QLabel{font-size:24px; font-family:arial black;}'
        )
        
        self.__message = QtWidgets.QLabel()
        self.__message.setStyleSheet('QLabel{font-size:20px}')
        self.__default_color = (
            self.__message.palette()
            .color(self.__message.foregroundRole())
        )

        self.__inputfield = QtWidgets.QLineEdit()
        self.__inputfield.returnPressed.connect(self.finishEditing)
        self.__button = QtWidgets.QPushButton()
        self.__button.clicked.connect(self.finishEditing)

        self.__thumbnail = QtWidgets.QLabel()
        self.__thumbnail.setStyleSheet('QLabel{border:1px solid #f0f0f0;}')
        # 全体を囲むグループ。=================================================
        self.__grp = QtWidgets.QFrame(self)
        self.__grp.resize(600, 400)

        layout = QtWidgets.QGridLayout(self.__grp)
        layout.addWidget(self.__title, 0, 0, 1, 2)
        layout.addWidget(self.__message, 1, 0, 1, 2)
        layout.addWidget(self.__thumbnail, 2, 0, 3, 1)

        layout.addWidget(self.__inputfield, 2, 1, 1, 1)
        layout.addWidget(self.__button, 3, 1, 1, 1)

        layout.setRowStretch(4, 1)
        layout.setRowStretch(5, 1)
        # =====================================================================

    def setAcceptCallback(self, callback):
        r"""
            Args:
                callback (function):
        """
        self.__accpept_callback = callback

    def setText(self, text):
        r"""
            入力フィールドにテキストをセットする
            
            Args:
                text (str):
        """
        self.__inputfield.setText(text)

    def setMessage(self, message, asError=False):
        r"""
            メッセージとして表示するテキストを設定する
            
            Args:
                message (str):
                asError (bool):エラーとして表示するかどうか
        """
        color = (
            QtGui.QColor(220, 35, 83)
            if asError else self.__default_color
        )
        palette = self.__message.palette()
        palette.setColor(self.__message.foregroundRole(), color)
        self.__message.setPalette(palette)
        self.__message.setText(message)

    def setTitle(self, title):
        r"""
            ウィンドウタイトルを設定する
            
            Args:
                title (str):
        """
        self.__title.setText(title)

    def setButtonLabel(self, label):
        r"""
            ボタンラベルを設定する
            
            Args:
                label (str):
        """
        self.__button.setText(label)

    def grabViewCapture(self):
        r"""
            ビューのキャプチャをサムネイルとして作成する。
        """
        import tempfile, shutil
        ntf = tempfile.NamedTemporaryFile()
        filename = ntf.name
        ntf.close()
        filename += '.png'
        mayaUIlib.write3dViewToFile(filename, 1024, 1024)

        # 大きさを整える。=====================================================
        pixmap = QtGui.QPixmap(filename)
        rect = pixmap.rect()
        aspect_ratio = rect.width() / float(rect.height())
        center = rect.center()
        if aspect_ratio > 1:
            # 横長の場合。
            rect.setWidth(rect.height())
        elif aspect_ratio < 1:
            # 縦長の場合。
            rect.setHeight(rect.width())
        rect.moveCenter(center)
        pixmap = pixmap.copy(rect).scaled(
            QtCore.QSize(256, 256),
            transformMode=QtCore.Qt.SmoothTransformation
        )
        self.__thumbnail.setPixmap(pixmap)
        self.__thumbnail_path = filename
        try:
            os.remove(filename)
        except:
            pass
        # =====================================================================

    def show(self):
        cur_pos = QtGui.QCursor().pos()
        pos = self.mapFromGlobal(cur_pos)
        pos.setY(pos.y() - 20)
        self.__grp.move(pos)
        self.grabViewCapture()
        super(InputDialog, self).show()

    def finishEditing(self):
        input_text = self.__inputfield.text()
        if not input_text:
            self.setMessage('Input some text.', True)
            return
        self.hide()
        if self.__accpept_callback: 
            callback = self.__accpept_callback
            self.__accpept_callback = None
            try:
                self.__thumbnail.pixmap().save(self.__thumbnail_path)
            except Exception as e:
                raise IOError('Failed to create a thumbnail.')
            callback(input_text, self.__thumbnail_path)
            self.__thumbnail_path = ''


Dialog = None
def showPoseCreatorDialog(
    callback, text='', title='', message='', buttonLabel='OK'
):
    r"""
        ダイアログを表示する関数。
        
        Args:
            callback (function):OKボタンに該当する動作を定義する関数
            text (str):入力フィールドに表示する文字列。
            title (str):タイトルラベル
            message (str):メッセージラベル
            buttonLabel (str):ボタンのラベル
    """
    global Dialog
    if not Dialog:
        Dialog = InputDialog()
    Dialog.setAcceptCallback(callback)
    Dialog.setText(text)
    Dialog.setTitle(title)
    Dialog.setMessage(message)
    Dialog.setButtonLabel(buttonLabel)
    Dialog.show()
# /////////////////////////////////////////////////////////////////////////////


class StandardDataEditor(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(StandardDataEditor, self).__init__(parent)
        self.buildUI()

    def tag(self):
        return ''
    
    def buildUI(self):
        pass

class PoseEditor(StandardDataEditor):
    def buildUI(self):
        btn = QtWidgets.QPushButton('Restore Pose')
        btn.setToolTip('Restore pose to selected namespace.')
        btn.clicked.connect(self.restorePose)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(btn)

    def tag(self):
        return 'pose'

    def restorePose(self):
        pass


class DataViewContext(uilib.ConstantWidget):
    r"""
        データの詳細表示を行うコンテキストUIを提供するクラス。
    """
    def buildUI(self):
        r"""
            GUIを構築する
        """
        self.resize(480, 300)
        self.setHiddenTrigger(self.HideByCursorOut)
        self.__filedata = None
        self.__datamanger = None
        self.__editors = []

        titlebar = QtWidgets.QLabel()
        titlebar.setStyleSheet('QLabel{font-size:20px;}')
        
        # 情報ウィジェット。===================================================
        info_widget = QtWidgets.QWidget()

        icon_image = QtWidgets.QLabel()
        icon_image.setStyleSheet('QLabel{border : 1px solid #000000;}')

        cmn_widget = self.__createCommonOperator()

        self.__stacked = QtWidgets.QStackedWidget()

        layout = QtWidgets.QGridLayout(info_widget)
        layout.setContentsMargins(10, 0, 10, 10)
        layout.addWidget(icon_image, 0, 0, 2, 1)
        layout.addWidget(cmn_widget, 0, 1, 1, 1)
        layout.addWidget(self.__stacked, 1, 1, 1, 1)
        # =====================================================================

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.addWidget(titlebar)
        layout.addWidget(info_widget)
        layout.addStretch()

        self.setTitle = titlebar.setText
        self.setPixmap = icon_image.setPixmap

    def __createCommonOperator(self):
        r"""
            共通操作ウィジェットを作成する・
            
            Returns:
                QtWidgets.QWidget:
        """
        widget = QtWidgets.QGroupBox('Common Operation')

        select_btn = QtWidgets.QPushButton('Select target nodes')
        select_btn.clicked.connect(self.selectTargetNodes)

        layout = QtWidgets.QVBoxLayout(widget)
        layout.addWidget(select_btn)
        return widget

    def installDataEditor(self, editor):
        self.__editors.append(editor.tag())
        self.__stacked.addWidget(editor)

    def showEditorByType(self, editorType):
        if editorType not in self.__editors:
            raise ValueError(
                'The specified type "{}" is not suported.'.format(editorType)
            )
        index = self.__editors.index(editorType)
        self.__stacked.setCurrentIndex(index)

    def setDataManager(self, dataManager, fileData, pixmap):
        r"""
            dataManagerを登録する初期化メソッド。
            
            Args:
                dataManager (animLibrary.core.GlobalDataManager):
                fileData (dict):
                pixmap (QtGui.QPixmap):
        """
        datatype = fileData.get('dataType')
        if not datatype:
            self.__datamanger = None
            return
        self.__datamanger = dataManager
        self.__filedata = fileData
        self.setTitle(
            '+ ' + fileData.get('dataName', 'Untitled') + '  - ' + datatype
        )
        self.setPixmap(pixmap)
        self.showEditorByType(datatype)

    def selectTargetNodes(self):
        self.__datamanger.selectTargetNode(self.__filedata.get('fileName'))

    def show(self):
        r"""
            ウィジェットを表示する。
            setDataManagerを通してからでないと起動できない。
        """
        if self.__datamanger:
            super(DataViewContext, self).show()


class DataView(imageViewer.ImageViewer):
    r"""
        データを可視化したビューとして表示する。
    """
    DefaultIcon = uilib.IconPath('uiBtn_noImage')
    itemIsClicked = QtCore.Signal(str)
    poseEditorRequested = QtCore.Signal(str, QtGui.QPixmap)
    itemIsDeleted = QtCore.Signal(list)
    GridOffset = QtCore.QSize(28, 28)
    def __init__(self, rootdir, parent=None):
        r"""
            Args:
                rootdir (str):データ管理を行うルートディレクトリパス
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(DataView, self).__init__(rootdir, parent)
        self.setStyleSheet(
            'QListView{background:#202020;}'
        )

    def setDataList(self, dataList):
        r"""
            core.DataManagerから提供されるファイルデータをセットする。
            このデータは各種データを持つ辞書をリスト化したもの。
            
            Args:
                dataList (list):
        """
        model = self.model()
        model.removeRows(0, model.rowCount())

        for data in dataList:
            self.addData(data)

    def addData(self, data):
        r"""
            辞書データを元にアイテムを追加する。
            
            Args:
                data (dict):
        """
        model = self.model()
        row = model.rowCount()

        item = QtGui.QStandardItem(data['dataName'])
        item.setData(data['fileName'])
        icon = os.path.join(self.rootDir(), data['fileName'], 'thumb.png')
        icon = icon if os.path.exists(icon) else self.DefaultIcon
        item.setIcon(QtGui.QIcon(icon))
        model.setItem(row, 0, item)


class DataManager(QtWidgets.QWidget):
    r"""
        データを表示・編集するビュー機能を提供する。
    """
    createPoseRequested = QtCore.Signal(str)
    def __init__(self, rootdir, parent=None):
        r"""
            Args:
                rootdir (str):ルート階層のパス
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(DataManager, self).__init__(parent)
        icon_size = 28
        
        self.__view = DataView(rootdir)
        self.itemIsClicked = self.__view.itemIsClicked
        self.setDataList = self.__view.setDataList
        self.addData = self.__view.addData

        # 編集用のGUI。========================================================
        editbar_group = QtWidgets.QWidget()
        add_btn = uilib.OButton()
        add_btn.setIcon(uilib.IconPath('uiBtn_plus'))
        add_btn.setSize(icon_size)
        add_btn.setBgColor(28, 128, 99)
        add_btn.setToolTip('Create a new pose from selected node.')

        sel_btn = uilib.OButton()
        sel_btn.setIcon(uilib.IconPath('uiBtn_select'))
        sel_btn.setSize(icon_size)
        sel_btn.setCheckable(True)
        sel_btn.toggled.connect(self.__view.activateSelecting)

        editbar_layout = QtWidgets.QHBoxLayout(editbar_group)
        editbar_layout.setContentsMargins(0, 0, 0, 0)
        editbar_layout.addWidget(QtWidgets.QLabel('Create New Pose'))
        editbar_layout.addWidget(add_btn)
        editbar_layout.addStretch()
        editbar_layout.addWidget(sel_btn)
        # =====================================================================

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(editbar_group)
        layout.addWidget(self.__view)
        
        self.createPoseRequested = add_btn.clicked
        self.itemIsDeleted = self.__view.itemIsDeleted
        self.poseEditorRequested = self.__view.poseEditorRequested

    def view(self):
        r"""
            このウィジェットが持つビューを返す。
            
            Returns:
                DataView:
        """
        return self.__view

class MainWidget(QtWidgets.QWidget):
    r"""
        メインとなるGUIを提供するクラス。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QWidget):親ウィジェット
        """
        super(MainWidget, self).__init__(parent)
        self.setWindowTitle('Gris Anim Library')
        self.__tab = QtWidgets.QTabWidget()
        self.__current_tag = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.__tab)
        
        self.__data_manager = core.GlobalDataManager()
        self.__context = DataViewContext(self)
        self.__context.installDataEditor(PoseEditor())
        self.initialize()

    def globalDataManager(self):
        r"""
            データマネージャーを返す。
            
            Returns:
                gris3.animLibrary.core.GlobalDataManager:
        """
        return self.__data_manager

    def addNewTab(self, data, tag):
        r"""
            タブを新規で追加する。
            
            Args:
                data (any):
                tag (str):タブの名前
                
            Returns:
                core.GlobalDataManager:
        """
        gl_data_man = self.globalDataManager()
        data_man = DataManager(gl_data_man.rootDir(), self)
        data_man.setDataList(data)
        data_man.itemIsClicked.connect(gl_data_man.readDataFromFile)
        data_man.createPoseRequested.connect(self.createPose)
        data_man.poseEditorRequested.connect(self.editPose)
        data_man.itemIsDeleted.connect(self.deleteData)
        self.__tab.addTab(data_man, tag)

        return data_man

    def initialize(self):
        r"""
            初期化を行う。
        """
        datalist = self.globalDataManager().fileDataList()
        tags = datalist.tags()
        if not tags:
            self.addNewTab([], 'all')
            return

        for tag in tags:
            data = datalist.dataList(tag)
            if not data:
                continue
            self.addNewTab(data, tag)

    def currentTag(self):
        r"""
            現在のタブ名を返す
            
            Returns:
                str:
        """
        return self.__tab.tabText(self.__tab.currentIndex())

    def createPose(self):
        r"""
            新規でポーズを登録するUIを表示する。
        """
        if not core.checkSelection():
            raise RuntimeError('Nothing selected.')
        showPoseCreatorDialog(
            self.createNewPoseCallback,
            '', 'Create a new pose', 'Enter a pose name', 'Create'
        )

    def editPose(self, fileName, pixmap):
        r"""
            既存のポーズを編集するUIを表示する。
            
            Args:
                fileName (str):
                pixmap (QtGui.QPixmap):
        """
        dm = self.globalDataManager()
        datalist = dm.fileDataList()
        if not datalist:
            return
        data = datalist.findData(fileName)
        if not data:
            return
        dm.setDataManager(core.PoseDataManager())
        self.__context.setDataManager(dm, data, pixmap)
        self.__context.show()

    def createNewPoseCallback(self, poseName, thumbnailPath):
        r"""
            createPoseで表示するUIから呼ばれるコールバック。
            
            Args:
                poseName (str):
                thumbnailPath (str):キャプチャされたサムネイルのパス
        """
        dm = self.globalDataManager()
        dm.setDataManager(core.PoseDataManager())
        dm.setTags(self.currentTag())
        dm.write(poseName, thumbnailPath)

        data_man = self.__tab.currentWidget()
        data_man.addData(dm.fileDataList()[-1])

    def deleteData(self, fileList):
        r"""
            渡されたファイルデータの情報を削除する。
            
            Args:
                fileList (list):
        """
        dm = self.globalDataManager()
        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        try:
            dm.deleteDataFromFile(self.currentTag(), fileList)
        except Exception as e:
            raise e
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()


class SeparatedWidget(uilib.AbstractSeparatedWindow):
    r"""
        単独ウィンドウ版を作成する
    """
    def centralWidget(self):
        r"""
            UIの作成を行う。
            
            Returns:
                MainWidget:
        """
        self.resize(800, 800)
        return MainWidget(self)


def showWindow():
    r"""
        単独で動くPoseManagerウィンドウを表示する。
        
        Returns:
            SeparatedWidget:
    """
    w = SeparatedWidget(mayaUIlib.MainWindow)
    w.show()
    return w