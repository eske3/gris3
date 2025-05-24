#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Mayaのファイルを開くためのオペレータを提供するモジュール
    
    Dates:
        date:2017/04/11 15:11[eske](eske3g@gmail.com)
        update:2020/11/22 17:47 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
from maya import OpenMayaUI
from gris3 import fileOperator, uilib
from gris3.uilib import fileUI
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

try:
    from gris3.uilib import mayaUIlib
    MayaWindow = mayaUIlib.MainWindow
except:
    MayaWindow = None

OptionMargins = QtCore.QMargins(2, 2, 2, 2)

def showAssistance(filepath, parent=None):
    r"""
        Mayaのファイル操作を行うGUIを開く。
        
        Args:
            filepath (str):mayaのファイルパス
            parent (QtWidgets.QWidget):親ウィジェット
            
        Returns:
            MayaFileOperationWidget:
    """
    assistance = MayaFileOperationWidget(MayaWindow)
    assistance.setPath(filepath)
    assistance.show()
    return assistance

SaveAll, Export = range(2)
def showSaveAssistance(filepath, mode, parent=None):
    r"""
        Mayaファイルのセーブまたはエクスポート操作を行うGUIを開く。
        戻り値としてファイル操作を行ったかどうかを返す。
        
        Args:
            filepath (str):セーブするファイルパスまたはディレクトリパス
            mode (bool):エクスポートかどうか
            parent (QtWidgets.QWidget):親ウィジェット
            
        Returns:
            bool:
    """
    option = MayaFileSaveWidget(MayaWindow)
    option.setPath(filepath)
    option.setSaveMode(mode)
    return option.exec_()

# /////////////////////////////////////////////////////////////////////////////
# Mayaのファイルがドロップされる時の裏制御を行うためのクラス、関数。         //
# /////////////////////////////////////////////////////////////////////////////
class FileDroppedMeta(uilib.QtSingletonMeta):
    def __call__(self, *args, **dict):
        obj = super(FileDroppedMeta, self).__call__(*args, **dict)
        try:
            obj.isHidden()
        except:
            pass
        return obj

class FileDroppedWidget(
    FileDroppedMeta('FileDroppedWidget', QtWidgets.QWidget)
):
    r"""
        mayaのファイルがドロップされる領域を作るクラス。
    """
    def __init__(self):
        self.__filelist = []

        super(FileDroppedWidget, self).__init__(MayaWindow)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAcceptDrops(True)

        self.__gradient = QtGui.QLinearGradient(0, 0, 0, 0)
        self.__gradient.setColorAt(0.0,  QtGui.QColor(0,  0,  0,  100))
        self.__gradient.setColorAt(0.1, QtGui.QColor(0,  0,  0,  90))
        self.__gradient.setColorAt(0.75, QtGui.QColor(0,  20, 40, 80))
        self.__gradient.setColorAt(1.0,  QtGui.QColor(46,208,237, 20))

    def dragEnterEvent(self, event):
        r"""
            ドラッグ時された時の処理。URLリストを持つもののみを通す。
            
            Args:
                event (QtCore.QEvent):
        """
        mimedata = event.mimeData()
        if mimedata.hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        r"""
            ドロップの処理。Mayaを開くオプションを表示する。
            
            Args:
                event (QtCore.QEvent):
        """
        mimedata = event.mimeData()
        if not mimedata.hasUrls():
            return
        self.__filelist = [x.toLocalFile() for x in mimedata.urls()]
        self.hide()

        for file in self.__filelist:
            showAssistance(file)

    def paintEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        rect = self.rect()
        self.__gradient.setFinalStop(0, rect.height())

        painter = QtGui.QPainter(self)
        painter.setPen(None)
        painter.setBrush(self.__gradient)
        painter.drawRect(rect)

    def show(self):
        r"""
            表示のオーバーライド。
            ドロップエリアをMayaのウィンドウ全体にフィットさせてから表示する。
            Mayaのウィンドウがない場合は何も表示しない。
        """
        if MayaWindow:
            self.__filelist = []
            self.setGeometry(MayaWindow.rect())
            self.raise_()
            super(FileDroppedWidget, self).show()

def showDroppedArea(mimeData, qdrag):
    r"""
        mimeDataに含まれるアドレスの拡張子が全てMayaのファイルの場合
        のみドラッグ用のウィジェットを表示する。
        
        Args:
            mimeData (QtCore.QMimeData):
            qdrag (QtCore.QDrag):
            
        Returns:
            FileDroppedWidget:
    """
    import os
    extensions = ('.ma', '.mb')
    for file in [x.toLocalFile() for x in mimeData.urls()]:
        if not os.path.splitext(file)[-1].lower() in extensions:
            return
    w = FileDroppedWidget()
    w.show()

    return w

def hideDroppedArea(mimeData, action):
    r"""
        処理終了後、FileDroppedWidgetを非表示にする。
        
        Args:
            mimeData (QtCore.QMimeData):
            action (QtCore.Qt.QDropAction):
    """
    w = FileDroppedWidget()
    w.hide()
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////



# /////////////////////////////////////////////////////////////////////////////
# Mayaのファイル操作に関するクラス。                                         //
# /////////////////////////////////////////////////////////////////////////////
class MayaOperationWidget(uilib.SingletonWidget):
    r"""
        Mayaでファイル操作するためのUIを提供するための規定クラス。
    """
    def buildUI(self):
        r"""
            GUIを構築する。
        """
        # 設定の初期化。-------------------------------------------------------
        r'''
            @brief  UIを作成するためのメソッド。
            @return None
        '''
        self.__pref = None
        self.resize(800, 150)
        self.setScalable(False)
        self.setHiddenTrigger(self.HideByFocusOut)
        # ---------------------------------------------------------------------

        # タイトルバー。=======================================================
        titlebar = QtWidgets.QWidget()
        title_layout = QtWidgets.QHBoxLayout(titlebar)
        title_layout.setContentsMargins(0, 0, 0, 0)

        self.__title = QtWidgets.QLabel('+Maya Operations')
        self.__title.setStyleSheet(
            'QLabel{font-size:20px;}'
        )
        title_layout.addWidget(self.__title)
        title_layout.setAlignment(self.__title, QtCore.Qt.AlignBottom)
        title_layout.addSpacing(10)

        self.__filename = QtWidgets.QLabel()
        title_layout.addWidget(self.__filename)
        title_layout.setAlignment(
            self.__filename, QtCore.Qt.AlignLeft | QtCore.Qt.AlignBottom
        )
        title_layout.addStretch()

        # キャンセルボタン。
        cancel = uilib.OButton()
        cancel.setIcon(uilib.IconPath('uiBtn_x'))
        cancel.setToolTip('Click to cancel operation.')
        cancel.clicked.connect(self.reject)
        title_layout.addWidget(cancel)
        # =====================================================================

        # カスタムウィジェットの作成。
        custom_widget = self.customWidget()

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(titlebar)
        layout.addWidget(custom_widget)
        
        self.__titlebar = titlebar
        
    def setTitle(self, title):
        r"""
            タイトルを設定するためのメソッド。
            
            Args:
                title (str):
        """
        return self.__title.setText(title)

    def label(self):
        r"""
            ラベルとなる文字列を返す。
            
            Returns:
                str:
        """
        return 'Maya Operation'

    def customWidget(self):
        r"""
            内部に表示するカスタムGUIウィジェットを定義するメソッド。
            UI部分はこのメソッドをオーバーライドして定義し、そのトップ
            ウィジェットを返す。
            
            Returns:
                QtWidgets.QWidget:
        """
        return QtWidgets.QWidget()

    def refresh(self):
        r"""
            更新をかけるためのオーバーライド用メソッド。
        """
        pass

    def setPath(self, path):
        r"""
            パスをセットするメソッド。
            
            Args:
                path (str):
        """
        self.__path = path
        self.__filename.setText(os.path.basename(self.path()))
        self.refresh()

    def path(self):
        r"""
            現在セットされているパスを返すメソッド。
            
            Returns:
                str:
        """
        return self.__path

class OpenOption(QtWidgets.QWidget):
    r"""
        Mayaファイルの開くオプションを提供するクラス。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(OpenOption, self).__init__(parent)

        self.selective_preload = QtWidgets.QCheckBox()
        self.selective_preload.setText('Use Selective Preload.')
        self.selective_preload.setChecked(0)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(OptionMargins)
        layout.addStretch()
        layout.addWidget(self.selective_preload)

    def savePreference(self):
        r"""
            SelectivePreloadの設定を保存する。
        """
        pass

    def stateKeywords(self):
        r"""
            GUIのチェック状態からfileOperator.openFileに渡す引数を返す。
            
            Returns:
                dict:
        """
        keywords = {
            'autoProjectSetting' : False,
            'useSelectivePreload' : self.selective_preload.isChecked(),
        }
        return keywords

class ImportOption(QtWidgets.QWidget):
    r"""
        インポートオプションのUIを提供するクラス。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ImportOption, self).__init__(parent)

        self.use_namespace = QtWidgets.QCheckBox()
        self.use_namespace.setText('Use Namespace')
        self.use_namespace.toggled.connect(self.updateState)

        self.apply_to_all = QtWidgets.QCheckBox()
        self.apply_to_all.setText('Apply namespace to all')
        self.apply_to_all.setChecked(False)
        self.apply_to_all.setEnabled(True)
        self.apply_to_all.toggled.connect(self.updateLabel)

        self.namespace_label = QtWidgets.QLabel('Namespace')
        self.namespace = uilib.FilteredLineEdit()
        self.namespace.setFilter('[a-zA-Z_][a-zA-Z\d_]*')

        layout = QtWidgets.QFormLayout(self)
        layout.setContentsMargins(OptionMargins)
        layout.addRow(self.namespace_label, self.namespace)
        layout.addWidget(self.use_namespace)
        layout.addWidget(self.apply_to_all)

    def updateState(self, state):
        r"""
            UIの状態を更新するメソッド。
            
            Args:
                state (bool):
        """
        self.apply_to_all.setEnabled(state == False)
        if state:
            self.namespace_label.setText('Namespace')

    def updateLabel(self, state):
        r"""
            ネームスペース入力欄のラベルを変更するメソッド。
            
            Args:
                state (bool):
        """
        self.use_namespace.setEnabled(state==False)
        if state:
            self.namespace_label.setText('Prefix')
        else:
            self.namespace_label.setText('Namespace')
        

    def setNamespace(self, namespace):
        r"""
            ネームスペースをフィールドにセットするメソッド。
            
            Args:
                namespace (str):
        """
        self.namespace.setText(namespace)

    def stateKeywords(self):
        r"""
            UIの内容をfileOperator.importFileの引数として返すメソッド。
            
            Returns:
                dict:
        """
        return {
            'useNamespace' : self.use_namespace.isChecked(),
            'namespace' : self.namespace.text(),
            'renameAll' : self.apply_to_all.isChecked(),
        }

    def savePreference(self):
        r"""
            プレファレンスを保存する目的で呼ばれる上書き用メソッド。
        """
        pass
        
class ReferenceOption(QtWidgets.QWidget):
    r"""
        リファレンスオプションのUIを提供するクラス。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        class ChoiceButton(QtWidgets.QCheckBox):
            r"""
                ここに説明文を記入
            """
            def uncheck(self):
                r"""
                    チェックをはずすメソッド（ポリモーフィズム用）
                """
                self.setChecked(False)
        # pref_data = settings.GlobalPref().userGlobalPref(
            # 'mayaFileReferenceAction'
        # )
        super(ReferenceOption, self).__init__(parent)

        # ネームスペース入力欄。 ==============================================
        namespace_label = QtWidgets.QLabel('Namespace')
        self.namespace = uilib.FilteredLineEdit()
        self.namespace.setFilter('[a-zA-Z_][a-zA-Z\d_]*')
        # =====================================================================

        # ノード共有オプション。===============================================
        shared_label = QtWidgets.QLabel('Shared')
        shared_widget = QtWidgets.QWidget()

        layout = QtWidgets.QVBoxLayout(shared_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        buttons = []
        from gris3 import lib
        for key in (
            'displayLayers', 'shadingNetworks',
            'renderLayersByName', 'renderLayersById'
        ):
            btn = ChoiceButton(lib.title(key))
            btn.setChecked(False)
            btn.keyword = key
            layout.addWidget(btn)
            buttons.append(btn)
        buttons[-2].clicked.connect(buttons[-1].uncheck)
        buttons[-1].clicked.connect(buttons[-2].uncheck)
        self.__shared_buttons = buttons
        # =====================================================================

        layout = QtWidgets.QFormLayout(self)
        layout.addRow(namespace_label, self.namespace)
        layout.addRow(shared_label, shared_widget)
        layout.setContentsMargins(OptionMargins)

    def setNamespace(self, namespace):
        r"""
            ネームスペースをフィールドにセットするメソッド。
            
            Args:
                namespace (str):
        """
        self.namespace.setText(namespace)

    def stateKeywords(self):
        r"""
            UIの内容をfileOperator.referenceFileの引数として返す。
            
            Returns:
                dict:
        """
        shared = [x.keyword for x in self.__shared_buttons if x.isChecked()]
        keywords = {'namespace' : self.namespace.text()}
        if shared:
            keywords['shared'] = shared
        return keywords

    def savePreference(self):
        r"""
            プレファレンスを保存する目的で呼ばれる上書き用メソッド。
        """
        keywords = {}
        for btn in self.__shared_buttons:
            keywords[btn.keyword] = btn.isChecked()

class MayaFileOperationWidget(uilib.SingletonWidget):
    r"""
        Mayaのファイルを操作するためのGUIを提供するクラス
    """
    WindowOffset = QtCore.QPoint(0, 128)
    Command = (
        fileOperator.openFile, fileOperator.referenceFile,
        fileOperator.importFile
    )
    def buildUI(self):
        r"""
            UIを作成するためのメソッド。
        """
        grp_style = (
            'QGroupBox{'
                'font-size:20px; font-family:arial black;'
                'border: 1px solid #808080;'
                '%s'
            '}'
            'QGroupBox:title{'
                'subcontrol-origin : margin;'
                'subcontrol-position : %s;%s;'
            '}'
        )
        
        # 設定の初期化。=======================================================
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.__pref = None
        self.__title = '+Maya Operations'
        self.__filename = 'Untitled.'
        width, height = self.WindowOffset.y()*5, self.WindowOffset.y()*4
        self.resize(width, height)
        self.setScalable(False)
        self.setHiddenTrigger(self.HideByCursorOut)
        self.setClosedByRightButton(True)
        # =====================================================================

        # Mayaのオペレーションウィジェットの作成。=============================
        column = 0
        self.__option_guis = []
        self.__guiset = {}
        for label, mod, color, opp, cmd in zip(
            ('Open', 'Reference', 'Import'),
            ('Shift', 'Ctrl', 'Alt'),
            ((51, 120, 195), (60, 70, 199), (65, 162, 180)),
            (OpenOption, ReferenceOption, ImportOption),
            (self.openFile, self.referenceFile, self.importFile),
        ):
            btn = uilib.OButton()
            btn.setParent(self)
            btn.setIcon(uilib.IconPath('uiBtn_'+label.lower()))
            btn.setSize(64)
            btn.setToolTip(
                '%s (Press %s + Enter key to %s)' % (label, mod, label.lower())
            )
            btn.setBgColor(*color)
            btn.clicked.connect(cmd)

            option = opp()
            self.__option_guis.append(option)

            grp = QtWidgets.QGroupBox(label, self)
            self.followMouseOperation(grp)
            grp_layout = QtWidgets.QVBoxLayout(grp)
            grp_layout.addSpacing(10)
            grp_layout.addWidget(option)

            self.__guiset[label] = (btn, grp)
        # =====================================================================

        center_x = width / 2
        center_y = height / 2
        hmargin = 50
        vmargin = 50
        icon_offset = 10
        icon_offset_B = 30

        # デフォルトアプリで開くボタンの作成。=================================
        defapp_btn = uilib.OButton(uilib.IconPath('uiBtn_view'))
        defapp_btn.setParent(self)
        defapp_btn.setBgColor(180, 110, 45)
        defapp_btn.setSize(48)
        defapp_btn.setToolTip('Open file in the default application.')
        defapp_btn.clicked.connect(self.openFileInDefaultApp)

        rect = defapp_btn.rect()
        rect.moveCenter(QtCore.QPoint(center_x, center_y))
        rect.moveBottom(height)
        defapp_btn.setGeometry(rect)
        # =====================================================================

        # Open関連GUIの配置。==================================================
        btn, grp = self.__guiset['Open']
        grp.setStyleSheet(
            grp_style % (
                'margin-bottom:0.5em; padding-top:-1em;',
                'bottom center', ''
            )
        )
        btn_rect = btn.rect()
        btn_rect.moveLeft(center_x - btn_rect.width() / 2)
        btn_rect.moveBottom(center_y-icon_offset_B)
        btn.setGeometry(btn_rect)

        grp_rect = grp.rect()
        grp_rect.setSize(QtCore.QSize(250, btn_rect.top()-vmargin-20))
        grp_rect.moveLeft(center_x - grp_rect.width() / 2)
        grp_rect.moveBottom(btn_rect.top())
        grp.setGeometry(grp_rect)
        
        self.__title_top = QtCore.QRect(
            0, 20, width, icon_offset*2
        )
        # =====================================================================

        grp_height = center_y - btn_rect.height() - vmargin
        # Reference関連GUIの配置。=============================================
        btn, grp = self.__guiset['Reference']
        grp.setStyleSheet(
            grp_style % (
                'padding-top:-0.2em; margin-top:0.5em;',
                'top right', 'right : 10px;'
            )
        )
        btn_rect = btn.rect()
        btn_rect.moveRight(center_x-icon_offset_B)
        btn_rect.moveTop(center_y+icon_offset)
        btn.setGeometry(btn_rect)

        grp_rect = grp.rect()
        grp_rect.setSize(QtCore.QSize(center_x-hmargin, grp_height))
        grp_rect.moveRight(center_x-10)
        grp_rect.moveTop(btn_rect.bottom())
        grp.setGeometry(grp_rect)
        # =====================================================================

        # Import関連GUIの配置。=============================================
        btn, grp = self.__guiset['Import']
        grp.setStyleSheet(
            grp_style % (
                'padding-top:-0.2em; margin-top:0.5em;',
                'top left', 'left : 10px;'
            )
        )
        btn_rect = btn.rect()
        btn_rect.moveLeft(center_x+icon_offset_B)
        btn_rect.moveTop(center_y+icon_offset)
        btn.setGeometry(btn_rect)

        grp_rect = grp.rect()
        grp_rect.setSize(QtCore.QSize(center_x-hmargin, grp_height))
        grp_rect.moveLeft(center_x+10)
        grp_rect.moveTop(btn_rect.bottom())
        grp.setGeometry(grp_rect)
        # =====================================================================

        # 描画に関する設定。===================================================
        # 背景グラデーション
        self.__gradient = QtGui.QLinearGradient()
        self.__gradient.setColorAt(0.25, QtGui.QColor(0, 5, 10, 220))
        self.__gradient.setColorAt(1, QtGui.QColor(40, 75, 177, 200))

        # 形状。
        v_mid = height / 5 * 3
        offset = 10
        right = width - offset
        bottom = height - offset
        self.__painterpath = QtGui.QPainterPath()
        self.__painterpath.moveTo(offset+20, bottom)
        self.__painterpath.lineTo(right-20, bottom)
        self.__painterpath.lineTo(right, v_mid)
        self.__painterpath.lineTo(width/7*5, offset)
        self.__painterpath.lineTo(width/7*2, offset)
        self.__painterpath.lineTo(offset, v_mid)
        self.__painterpath.lineTo(offset+20, bottom)
        # =====================================================================

    def paintEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        rect = self.rect()
        self.__gradient.setFinalStop(0, rect.height())
        painter = QtGui.QPainter(self)
        painter.setRenderHints(QtGui.QPainter.Antialiasing)

        # 背景形状の描画。
        painter.setPen(QtGui.QPen(QtGui.QColor(80, 80, 80), 2))
        painter.fillPath(self.__painterpath, QtGui.QBrush(self.__gradient))
        painter.drawPath(self.__painterpath)

        # 中心円の描画。
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawEllipse(rect.center(), 70, 70)
        
        # タイトルの描画。
        painter.setPen(QtGui.QPen(QtGui.QColor(200, 200, 200)))
        painter.setFont(QtGui.QFont('Arial', 20))
        rect.setY(20)
        painter.drawText(
            rect, QtCore.Qt.AlignHCenter|QtCore.Qt.AlignLeft, self.__title
        )
        # painter.drawText(
            # self.__title_top, QtCore.Qt.AlignCenter, self.__filename
        # )

    def leaveEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        self.startAutoFadeOut(300)

    def openFileInDefaultApp(self):
        r"""
            OS上でファイルに紐付けられたアプリで開く。
        """
        print('# Open file : %s' % self.path())
        from gris3 import fileUtil
        fileUtil.openFileInDefaultApp(self.path())

    def operate(self, index):
        r"""
            Mayaのファイル操作を行うメソッド。
            indexの数字はそれぞれ
            0 : ファイルを開く操作
            1 : リファレンスを表す。
            2 : インポート
            
            Args:
                index (int):
        """
        keywords= self.__option_guis[index].stateKeywords()
        self.__option_guis[index].savePreference()
        self.Command[index](self.path(), **keywords)
        self.fadeOut()

    def openFile(self):
        r"""
            ファイルを開く。
        """
        self.operate(0)

    def referenceFile(self):
        r"""
            ファイルをリファレンスする。
        """
        self.operate(1)
        
    def importFile(self):
        r"""
            ファイルをインポートする
        """
        self.operate(2)

    def refresh(self):
        r"""
            ファイル名からネームスペースを自動生成するメソッド。
            NamespaceManagerの中にネームスペースが設定されている場合は
            そちらの文字列を優先させる。
        """
        namespace = fileOperator.NamespaceManager().namespace()
        namespace = (
            namespace if namespace
            else os.path.basename(self.path()).split('.')[0]
        )
        self.__option_guis[1].setNamespace(namespace)
        self.__option_guis[2].setNamespace(namespace)

    def setPath(self, path):
        r"""
            パスをセットするメソッド。
            
            Args:
                path (str):
        """
        self.__path = path
        self.__filename = os.path.basename(self.path())
        self.refresh()

    def path(self):
        r"""
            現在セットされているパスを返すメソッド。
            
            Returns:
                str:
        """
        return self.__path

    def keyPressEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        if not event.key() in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
            super(MayaFileOperationWidget, self).keyPressEvent(event)
            return
        mod = event.modifiers()
        if mod == QtCore.Qt.ShiftModifier:
            self.openFile()
        elif mod == QtCore.Qt.ControlModifier:
            self.referenceFile()
        elif mod == QtCore.Qt.AltModifier:
            self.importFile()

class MayaFileSaveWidget(MayaOperationWidget):
    r"""
        MayaのシーンをセーブするためのUIを提供するクラス。
    """
    TitleLabel = ('Save Scene', 'Export Selection')
    Icon = ('uiBtn_addText', 'uiBtn_export')
    FileType = ['mayaBinary', 'mayaAscii']
    Extensions = ['.mb', '.ma']
    PreviewStyle = 'QLabel{font-size : 24px; %s}'
    def customWidget(self):
        r"""
            カスタムGUIを作成して返す。
            
            Returns:
                QtWidgets.QWidget:
        """
        # ファイルネーム入力GUI。----------------------------------------------
        dirname_label = QtWidgets.QLabel('Save in')
        self.__dirname = QtWidgets.QLineEdit()
        self.__dirname.setReadOnly(True)

        filename_label = QtWidgets.QLabel('&File Name')
        self.__filename = fileUI.FileNameLineEdit()
        self.__filename.textEdited.connect(self.checkFileName)
        filename_label.setBuddy(self.__filename)
        
        self.__name_result = QtWidgets.QLabel()
        self.__name_result.setStyleSheet(self.PreviewStyle % '')

        filename_layout = QtWidgets.QFormLayout()
        filename_layout.addRow(dirname_label, self.__dirname)
        filename_layout.addRow(filename_label, self.__filename)
        # ---------------------------------------------------------------------

        # セーブオプション。===================================================
        # ファイルタイプオプション。-------------------------------------------
        filetype_label = QtWidgets.QLabel('File Type')

        mb_radio = QtWidgets.QRadioButton('m&b')
        ma_radio = QtWidgets.QRadioButton('m&a')
        mb_radio.setChecked(True)
        filetype_widget = QtWidgets.QWidget()
        filetype_btn_grp = QtWidgets.QButtonGroup(filetype_widget)
        filetype_btn_grp.buttonClicked.connect(self.checkFileName)
        filetype_btn_grp.addButton(mb_radio, 0)
        filetype_btn_grp.addButton(ma_radio, 1)
        self.__filetype_btn_grp = filetype_btn_grp

        filetype_layout = QtWidgets.QHBoxLayout(filetype_widget)
        filetype_layout.setContentsMargins(0, 0, 0, 0)
        filetype_layout.addWidget(mb_radio)
        filetype_layout.addWidget(ma_radio)
        # ---------------------------------------------------------------------

        # Set Projectオプション(セーブ時のみ)----------------------------------
        self.__setproj_label = QtWidgets.QLabel('Auto set project')
        self.__setproj_cb = QtWidgets.QCheckBox()
        self.__setproj_cb.setChecked(True)
        # ---------------------------------------------------------------------

        option_grp = QtWidgets.QGroupBox('Save Options')
        option_layout = QtWidgets.QFormLayout(option_grp)
        option_layout.setHorizontalSpacing(40)
        option_layout.addRow(filetype_label, filetype_widget)
        option_layout.addRow(self.__setproj_label, self.__setproj_cb)
        # =====================================================================
       
        self.__export_btn = uilib.OButton(uilib.IconPath('uiBtn_import'))
        self.__export_btn.setSize(80)
        self.__export_btn.setBgColor(*(51, 144, 133))
        self.__export_btn.clicked.connect(self.accept)

        main_widget = QtWidgets.QWidget()
        main_layout = QtWidgets.QGridLayout(main_widget)
        main_layout.addLayout(filename_layout, 0, 0, 1, 2)
        main_layout.addWidget(self.__name_result, 1, 1, 1, 1)
        main_layout.addWidget(option_grp, 2, 1, 1, 1)
        main_layout.addWidget(self.__export_btn, 1, 0, 2, 1)

        return main_widget

    def setPath(self, path):
        r"""
            ファイルパスをセットするメソッド。
            
            Args:
                path (str):
        """
        dirname = ''
        filename = ''

        if os.path.isdir(path):
            dirname = path
        else:
            dirname, filename = os.path.split(path)

        self.__dirname.setText(dirname)
        basename, ext = os.path.splitext(filename)
        if ext in self.Extensions:
            button = self.__filetype_btn_grp.buttons()[
                self.Extensions.index(ext)
            ]
            button.setChecked(True)
            self.__filename.setText(basename)
        else:
            self.__filename.setText(filename)
        self.checkFileName('')

    def setSaveMode(self, mode):
        r"""
            セーブモードを変更するメソッド。
            
            Args:
                mode (int):
        """
        # モードがセーブだった場合、Auto set projectの項目を表示する。
        state = SaveAll != mode
        self.__setproj_cb.setHidden(state)
        self.__setproj_label.setHidden(state)

        self.__save_mode = mode
        self.setTitle('+'+self.TitleLabel[mode])
        self.__export_btn.setIcon(uilib.IconPath(self.Icon[mode]))
        self.__export_btn.setToolTip(self.TitleLabel[mode])

    def checkFileName(self, value):
        r"""
            ファイルネームを適正な名前にしてプレビューに表示するメソッド。
            
            Args:
                value (str):
        """
        text = self.__filename.text()
        if text:
            self.__export_btn.setEnabled(True)
            self.__name_result.setStyleSheet(self.PreviewStyle % '')
        else:
            self.__export_btn.setEnabled(False)
            self.__name_result.setText('Untitled')
            self.__name_result.setStyleSheet(
                self.PreviewStyle % 'color:#808080;'
            )
            return

        name, origext = os.path.splitext(text)
        extensions = self.Extensions[:]
        ext = extensions.pop(self.__filetype_btn_grp.checkedId())
        if origext.lower() == ext:
            self.__name_result.setText(text)
            return

        if origext.lower() == extensions[0]:
            text = text[:-len(extensions[0])]
        text += ext
        self.__name_result.setText(text)

    def exec_(self):
        r"""
            ウィジェットを表示するオーバーライド関数。
            
            Returns:
                bool:
        """
        self.resize(640, 150)
        self.__filename.setFocus(QtCore.Qt.MouseFocusReason)
        self.__filename.selectAll()
        return super(MayaFileSaveWidget, self).exec_()

    def accept(self):
        r"""
            Acceptしてセーブを実行するメソッド。
        """
        if not self.__filename.text():
            return
        dirname = self.__dirname.text()
        filename = self.__name_result.text()

        filetype = self.__filetype_btn_grp.checkedId()
        filetype = self.FileType[filetype]

        auto_set_proj = self.__setproj_cb.isChecked()

        super(MayaFileSaveWidget, self).accept()
        fileOperator.saveFile(
            dirname, filename, filetype, self.__save_mode, auto_set_proj
        )

    def keyPressEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        key = event.key()
        if key in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
            self.accept()
        else:
            super(MayaFileSaveWidget, self).keyPressEvent(event)
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////