#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    FactoryのUIを提供するモジュール。
    
    Dates:
        date:2017/01/21 11:47[Eske](eske3g@gmail.com)
        update:2025/05/24 13:50 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os

from .. import uilib, style, factoryModules, lib
from ..uilib import mayaUIlib
from ..gadgets import toolbar
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

class FactoryContext(uilib.ConstantWidget):
    r"""
        Factoryのコンテキストメニューを提供するクラス。
    """
    def buildUI(self):
        r"""
            UIの構築を行う。
        """
        self.resize(style.scaled(320), style.scaled(400))


class TabDock(QtWidgets.QListView):
    r"""
        FactoryTabの内容を一覧するリスト機能を提供するクラス。
    """
    selected = QtCore.Signal(int)
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):
        """
        super(TabDock, self).__init__(parent)
        self.setAlternatingRowColors(True)
        self.setMaximumSize(
            style.scaled(150), self.maximumSize().height()
        )
        self.setIconSize(QtCore.QSize(style.scaled(32), style.scaled(32)))

        model = QtGui.QStandardItemModel()
        selection_model = QtCore.QItemSelectionModel(model)
        selection_model.selectionChanged.connect(self.updateSelectionState)
        self.setModel(model)
        self.setSelectionModel(selection_model)

    def count(self):
        r"""
            タブの数を返す。
            
            Returns:
                int:
        """
        return self.model().rowCount()

    def clear(self):
        r"""
            タブの項目をクリアする。
        """
        model = self.model()
        model.removeRows(0, model.rowCount())

    def clearSelection(self):
        r"""
            タブの選択を解除する。
        """
        self.selectionModel().clear()

    def addTabLabel(self, label, icon):
        r"""
            タブとそのアイコンを追加する。
            
            Args:
                label (str):ラベル
                icon (QtGui.QIcon):アイコン
        """
        model = self.model()
        item = QtGui.QStandardItem(label)
        item.setEditable(False)
        item.setIcon(icon)
        model.setItem(model.rowCount(), 0, item)

    def updateSelectionState(self, selected, deselected):
        r"""
            選択が変更された時に、選択されたアイテムのrowを返す。
            
            Args:
                selected (QItemSelectionLiset):
                deselected (QItemSelectionLiset):
                
            Returns:
                int:
        """
        for index in selected.indexes():
            self.selected.emit(index.row())
            return

    def selectIndex(self, index):
        r"""
            引数で指定された番号のアイテムを選択する。
            
            Args:
                index (int):
        """
        model = self.model()
        sel_model = self.selectionModel()
        
        index = model.indexFromItem(model.item(index, 0))
        sel_model.select(index, QtCore.QItemSelectionModel.ClearAndSelect)
    

class FactoryTab(QtWidgets.QWidget, factoryModules.AbstractFactoryTabMixin):
    r"""
        factoryModuleで提供されるUIを配置するタブを提供するクラス。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (any):(QtWidgets.QWidget) :親ウィジェット
        """
        super(FactoryTab, self).__init__(parent)
        self.customInit()
        self.__cst_index = 0

        self.__tab = uilib.ScrolledStackedWidget()
        self.__tab.setOrientation(QtCore.Qt.Vertical)

        # 左側のサイドバーのUIを作成。=========================================
        self.__tabdock = TabDock()
        self.__tabdock.selected.connect(self.selectTab)
        # =====================================================================

        # コンストラクタ用ボタン。=============================================
        self.__cst_btn = uilib.SqButton()
        self.__cst_btn.setSize(42)
        self.__cst_btn.setBgColor(63, 111, 175)
        self.__cst_btn.setIcon(uilib.IconPath('uiBtn_toolBox'))
        self.__cst_btn.setToolTip("Show consutructor's utilities.")
        self.__cst_btn.clicked.connect(self.selectConstructorTab)
        # =====================================================================

        layout = QtWidgets.QGridLayout(self)
        layout.setVerticalSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.__tabdock, 0, 0, 1, 1)
        layout.addWidget(self.__cst_btn, 1, 0, 1, 1)
        layout.setAlignment(self.__cst_btn, QtCore.Qt.AlignRight)
        layout.setColumnStretch(0, 0)
        layout.addWidget(self.__tab, 0, 1, 2, 1)
        layout.setColumnStretch(1, 1)

    def refreshState(self):
        r"""
            タブの中身を更新するメソッド。
        """
        fs = factoryModules.FactorySettings()
        self.__tabdock.clear()
        self.__tab.clear()
        gui_list = {}
        for module in fs.listModules():
            gui_class = module.GUI()
            if not gui_class:
                continue

            p = module.priority()
            w = gui_class(module.rootPath(), module)
            w.init()

            data = (w, module.listLabel(), module.icon())
            if p in gui_list:
                gui_list[p].append(data)
            else:
                gui_list[p] = [data]

        keys = list(gui_list.keys())
        keys.sort()
        keys.reverse()
        index = 0
        for key in keys:
            for data in gui_list[key]:
                self.__tab.addTab(data[0])
                self.__tabdock.addTabLabel(data[1], data[2])
                index += 1

        # コンストラクタ用ユーティリティタブを表示する。=======================
        from gris3 import constructors
        cm = constructors.ConstructorManager()
        constructor = fs.constructorName(False)
        widget = cm.getUtilityWidget(constructor, True)
        if widget:
            grp = widget()
            self.__tab.addTab(grp)
            self.__cst_index = index
        self.__cst_btn.setVisible(True if widget else False)
        # =====================================================================

        self.__tabdock.selectIndex(0)

    def selectConstructorTab(self):
        r"""
            コンストラクタ用ツールのタブを表示する。
        """
        self.__tabdock.clearSelection()
        self.selectTab(self.__cst_index)

    def selectTab(self, index):
        r"""
            任意の番号のタブを選択する
            
            Args:
                index (int):
        """
        self.__tab.moveTo(index)
        w = self.__tab.widgetFromIndex(index)
        w.refreshState()


class AdvancedTabPage(QtWidgets.QWidget):
    r"""
        タブが初回アクティブになった時にUIの構築を行う仕組み
        を持ったAdvancedTabWidget用のタブページ。
        このインスタンスはUI生成用のクラスを保持し、初回時のみ
        そのクラスを呼び出しUIを生成する。
        UI生成用クラスはfactoryModules.AdvancedFactoryTabクラスを
        継承している必要がある。
    """
    def __init__(self, creatorClass, parent=None):
        r"""
            Args:
                creatorClass (factoryModules.AdvancedFactoryTab):
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(AdvancedTabPage, self).__init__(parent)
        self.setStyleSheet(style.styleSheet())
        self.__creator_class = creatorClass
        self.__child_widget = None
        self.__signal_connections = []

    def isChildWidgetCreated(self):
        r"""
            UIがすでに作成されたかどうかを返す
            
            Returns:
                bool:
        """
        return True if self.__child_widget else False

    def addSignalConnections(self, signalName, method):
        r"""
            createChildWidgetが呼ばれた際に作成されるシグナルの
            接続を行うシグナル名とメソッドを追加する。
            
            Args:
                signalName (str):
                method (method):
        """
        self.__signal_connections.append((signalName, method))

    def createChildWidget(self):
        r"""
            初期化時に渡された生成用クラスを用いてウィジェットを生成する。
            生成するのは１度きりで、すでに生成されている場合は
            生成済みウィジェットを返す。
            
            Returns:
                factoryModules.AdvancedFactoryTab:
        """
        if self.__child_widget:
            return
        child_widget = self.__creator_class()
        layout = QtWidgets.QVBoxLayout(self)
        margins = layout.contentsMargins()
        margins.setTop(0)
        layout.setContentsMargins(margins)
        layout.addWidget(child_widget)
        self.__child_widget = child_widget

        fs = factoryModules.FactorySettings()
        fs.isChanged.connect(child_widget.setChangedSignal)

        for signal_name, method in self.__signal_connections:
            getattr(child_widget, signal_name).connect(method)

    def childWidget(self):
        r"""
            このウィジェットが持つ子ウィジェットを返す。
            
            Returns:
                factoryModules.AdvancedFactoryTab:
        """
        self.createChildWidget()
        return self.__child_widget

class AdvancedTabWidget(QtWidgets.QTabWidget):
    r"""
        このウィジェットへタブを追加してもUIは作成されず、タブが
        アクティブになった時に１度だけUIを作成する機構を提供する
        カスタムタブウィジェット。
    """
    def __init__(self, parent=None):
        r"""
            タブ更新の仕組みが追加されているQTabWidget。
            
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(AdvancedTabWidget, self).__init__(parent)

    def addTab(self, creatorClass, label):
        r"""
            タブを追加するメソッド。ただし、このメソッド実行後にはまだ
            タブの中身は空のQWidgetだけになっている。
            タブが選択された時に一度だけタブの中身のメソッドが呼ばれ
            GUIが作成される。
            
            Args:
                creatorClass (class):
                label (str):
                
            Returns:
                AdvancedTabPage:
        """
        page = AdvancedTabPage(creatorClass)
        super(AdvancedTabWidget, self).addTab(page, label)
        return page

    def updateTab(self, index, force=False):
        r"""
            カレントタブの中身のウィジェットが未更新の場合に更新するメソッド。
            
            Args:
                index (int):
                force (bool):強制的に更新するかどうか
        """
        page = self.currentWidget()
        widget = page.childWidget()
        widget.refresh(force)

    def paintEvent(self, event):
        r"""
            タブ背景色を変更するためのペイントイベントの再実装メソッド
            
            Args:
                event (QtCore.QEvent):
        """
        super(AdvancedTabWidget, self).paintEvent(event)
        tabbar = self.tabBar()
        rect = tabbar.rect()
        rect.setWidth(self.rect().width())

        painter = QtGui.QPainter(self)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(38, 66, 125))
        painter.drawRect(rect)

class MainGUI(AdvancedTabWidget):
    r"""
        FactoryのメインGUIを提供するクラス。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(MainGUI, self).__init__(parent)
        stylesheet = '''
        QTabWidget::pane {
            border-top : 1px solid #000000;
        }
        QTabWidget::tab-bar {
            left: 5px;
            background: #26427d;
        }
        QTabBar::tab {
            background: #26427d;
            border: none;
            min-width: 25ex;
            padding: 7px 0px 7px 0px;

        }
        QTabBar::tab:hover{
             background: #26529d;
        }
        QTabBar::tab:selected {
             background: #26325d;
        }'''
        self.setStyleSheet(stylesheet)
        self.__xml = None
        self.__rootpath = ''

        from gris3.ui import startup, miscWidget, scriptManager

        # スタートアップマネージャの作成。
        st_mng = self.addTab(startup.StartupManager, 'Startup')
        st_mng.addSignalConnections('settingsApplied', self.updateSettings)

        # 実作業用UIを提供するタブの作成。
        self.addTab(FactoryTab, 'Factory')

        # スクリプト管理GUI。
        self.addTab(scriptManager.ScriptManager, 'Scripts')

        # リグのテストを行うためのGUI。
        self.addTab(miscWidget.MiscWidget, 'Misc')

        fs = factoryModules.FactorySettings()
        # fs.isChanged.connect(self.refreshTabState)
        self.currentChanged.connect(self.updateTab)

    def refreshTabState(self):
        r"""
            タブの状態を更新するメソッド。
        """
        fs = factoryModules.FactorySettings()
        index = 1 if fs.settingTest() else 0
        not_changed = self.currentIndex() == index
        if not not_changed:
            self.setCurrentIndex(index)

        if not index:
            self.tabBar().hide()
        else:
            self.tabBar().show()
        if not_changed:
            self.updateTab(index, False)

    def updateSettings(self):
        r"""
            FactoryのUIを更新する。
            戻り値として設定されたアセット名、アセットタイプ、プロジェクト名を
            返す。
            
            Returns:
                tuple: 設定されたセット名、アセットタイプ、プロジェクト名
        """
        fs = factoryModules.FactorySettings()
        fs.isChanged.emit()
        self.refreshTabState()
        size = self.size()
        for f in (1, -1):
            size.setWidth(size.width() + f)
            self.resize(size)
        return fs.assetName(), fs.assetType(), fs.project()

    def setRootPath(self, rootPath, emitSignal=True):
        r"""
            ルートとなるパスをセットするメソッド。
            ルートをセットすると、そのディレクトリ下にある設定ファイルを
            読み込むテストを行い、失敗した場合は設定画面を表示する。
            
            Args:
                rootPath (str):
                emitSignal (bool):
                
            Returns:
                bool:
        """
        fs = factoryModules.FactorySettings()
        if fs.rootPath() == rootPath:
            return False
        fs.setRootPath(rootPath, emitSignal)
        return True

    def setAssetName(self, assetName):
        r"""
            設定オブジェクトにアセット名をセットするメソッド。
            設定オブジェクトにアセット名が登録されていない場合に限る。
            
            Args:
                assetName (str):
                
            Returns:
                bool:
        """
        if not assetName:
            return False
        settings = factoryModules.FactorySettings()
        if settings.assetName(False):
            return False
        settings.setAssetName(assetName)
        return True
    
    def setAssetType(self, assetType):
        r"""
            設定オブジェクトにアセットタイプをセットするメソッド。
            設定オブジェクトにアセットタイプが登録されていない場合に限る。
            
            Args:
                assetType (str):
                
            Returns:
                bool:
        """
        if not assetType:
            return False
        settings = factoryModules.FactorySettings()
        if settings.assetType(False):
            return False
        settings.setAssetType(assetType)
        return True
        
    def setProject(self, project):
        r"""
            設定オブジェクトにプロジェクト名をセットするメソッド。
            設定オブジェクトにプロジェクト名が登録されていない場合に限る。
            
            Args:
                project (str):
                
            Returns:
                bool:
        """
        if not project:
            return False
        settings = factoryModules.FactorySettings()
        if settings.project(False):
            return False
        settings.setProject(project)
        return True

    def setXml(self, xml):
        r"""
            ディレクトリ定義用XMLをセットするメソッド。
            
            Args:
                xml (str):定義用XMLのパスを指す文字列。
        """
        self.__xml = xml

    def xml(self):
        r"""
            セットされているディレクトリ定義用XMLを返すメソッド。
            
            Returns:
                str:
        """
        return self.__xml

    def showContext(self):
        r"""
            右クリックメニューを表示する
        """
        if not self.__context:
            self.__context = FactoryContext(self)
            self.__context.self.setHiddenTrigger(self.__context.HideByFocusOut)
        self.__context.exec_()


class FactoryWidget(QtWidgets.QWidget):
    r"""
        スタンドアローンのウィンドウとして表示するウィンドウ。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(FactoryWidget, self).__init__(parent=parent)
        self.setWindowTitle(
            (
                '<font size=%s>Factory</font> - '
                '<font size=%s>GRIS</font>'
            )%(style.scaled(3), style.scaled(1))
        )

        self.__maingui = MainGUI(self)
        self.setObjectName('GrisFactoryWindow')

        # ツールバーを作成。===================================================
        tool_bar = toolbar.Toolbar(self)
        tool_bar.addPreset(toolbar.FACTORY_TOOLBAR)
        # =====================================================================
        
        # =====================================================================
        self.__sub_label = QtWidgets.QLabel()
        self.__sub_label.setMinimumWidth(10)
        self.__sub_label.setStyleSheet(
            'font-weight: bold;'
        )
        tool_bar.addWidget(self.__sub_label)
        fs = factoryModules.FactorySettings()
        fs.isChanged.connect(self.updateSubLabel)
        # =====================================================================
        

        # プロジェクトセレクタの作成。=========================================
        p_btn = uilib.OButton()
        p_btn.setIcon(uilib.IconPath('uiBtn_option'))
        p_btn.clicked.connect(self.showProjectSelector)
        
        from gris3.ui import projectSelector
        self.__selector = projectSelector.ProjectSelector(self)
        self.__selector.setStyleSheet(style.styleSheet())
        self.__selector.projectDecided.connect(self.applyProject)
        # =====================================================================

        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(style.scaled(5))
        layout.addWidget(tool_bar, 0, 0, 1, 1)
        layout.addWidget(p_btn, 0, 1, 1, 1)
        layout.addWidget(self.__maingui, 1, 0, 1, 2)
        layout.setColumnStretch(0, 1)

        self.showProjectSelector()

    def mainGUI(self):
        r"""
            MainGUIオブジェクトを返す
            
            Returns:
                MainGUI:
        """
        return self.__maingui

    def showProjectSelector(self):
        r"""
            プロジェクトセレクタを表示する。
        """
        fs = factoryModules.FactorySettings()
        self.__selector.showDialog(fs.rootPath())

    def hideProjectSelector(self):
        r"""
            プロジェクトセレクタを非表示にする。
        """
        self.__selector.hide()

    def updateSubLabel(self):
        r"""
            タイトルバーの横に表示するサブラベルを設定する。

            Args:
                name (str):
        """
        fs = factoryModules.FactorySettings()
        p, name, typ = fs.project(), fs.assetName(), fs.assetType()
        label = '{} / {}'.format(lib.title(p), lib.title(name))
        tooltip = 'Asset Name : {}<br>Asset Type : {}<br>Project : {}'.format(
            name, typ, p
        )
        self.__sub_label.setText(label)
        self.__sub_label.setToolTip(tooltip)


    def applyProject(self, path):
        r"""
            プロジェクトをセットする。
            
            Args:
                path (str):プロジェクトパス
        """
        main_gui = self.mainGUI()
        main_gui.setRootPath(path, False)
        main_gui.updateSettings()

    def setup(
        self, directoryPath='', assetName='', assetType='', project='',
        forceUpdate=False
    ):
        r"""
            アセット情報等を設定する。
            引数すべてが設定済みの場合はProjectSelectorを表示しない
            
            Args:
                directoryPath (str):ワークスペースとなるディレクトリパス
                assetName (str):アセット名
                assetType (str):アセットタイプ
                project (str):プロジェクト名
                forceUpdate (bool):強制的に更新をかけるかどうか
        """
        main = self.mainGUI()
        count = 1 if forceUpdate else 0
        if directoryPath:
            from .. import settings
            settings.addPathToHistory(directoryPath)
            if main.setRootPath(directoryPath, False):
                count += 1

        for attr, value in zip(
            ('setAssetName', 'setAssetType', 'setProject'),
            (assetName, assetType, project),
        ):
            if value:
                if getattr(main, attr)(value):
                    count += 1
        if count:
            main.updateSettings()
            self.hideProjectSelector()


class SeparatedFactory(uilib.AbstractSeparatedWindow):
    r"""
        Facotory独立ウィンドウ機能を提供するクラス
    """
    def centralWidget(self):
        r"""
            メインコンテンツとなるウィジェットを返す
            
            Returns:
                FactoryWidget:
        """
        return FactoryWidget()


class DockableFactory(mayaUIlib.SingletonDockableWidget):
    r"""
        ドッキング可能なFactoryUIを提供するローカルクラス
    """
    def centralWidget(self):
        r"""
            配置されるウィジェットを返す。
            
            Returns:
                factory.MainWindow:
        """
        self.layout().setContentsMargins(0, 0, 0, 0)
        return FactoryWidget()


def showWindow(
    directoryPath='', assetName='', assetType='', project='', isDockable=False,
    forceUpdate=False
):
    r"""
        メインGUIを表示する関数。
        
        Args:
            directoryPath (str):ワークスペースとなるディレクトリパス
            assetName (str):アセット名
            assetType (str):アセットタイプ
            project (str):プロジェクト名
            isDockable (bool):ドッキング可能かどうか
            forceUpdate (bool):強制的に更新をかけるかどうか
            
        Returns:
            SeparatedFactory:
    """
    if isDockable:
        widget = DockableFactory(mayaUIlib.MainWindow)
    else:
        widget = SeparatedFactory(mayaUIlib.MainWindow)
    widget.resize(style.scaled(520), style.scaled(600))
    widget.main().setup(
        directoryPath, assetName, assetType, project, forceUpdate
    )
    widget.show()

    return widget

