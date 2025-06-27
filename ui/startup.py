#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Factory開始時の設定を決めるUIを提供するモジュール。
    
    Dates:
        date:2017/01/21 12:39[Eske](eske3g@gmail.com)
        update:2020/10/18 01:53 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
from gris3 import core, lib, uilib, constructors, factoryModules
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class StartupItemModel(QtGui.QStandardItemModel):
    r"""
        StartupView用のItemModel
    """
    StdItemFlags = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
    def __init__(self):
        super(StartupItemModel, self).__init__(0, 3)
        self.setHeaderData(0, QtCore.Qt.Horizontal, 'Module')
        self.setHeaderData(1, QtCore.Qt.Horizontal, 'Directory Path')
        self.setHeaderData(2, QtCore.Qt.Horizontal, 'Alias Name')

    def flags(self, index):
        r"""
            アイテムの制御メソッドのオーバーライド。
            
            Args:
                index (QModelIndex):
                
            Returns:
                QtCore.Qt.ItemFlags:
        """
        if index.column() == 0:
            return self.StdItemFlags
        else:
            return self.StdItemFlags | QtCore.Qt.ItemIsEditable


class StartupView(QtWidgets.QTreeView):
    r"""
        モジュールとディレクトリの紐付けの一覧機能を提供する。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット。
        """
        super(StartupView, self).__init__(parent)
        self.setRootIsDecorated(False)
        self.setAlternatingRowColors(True)
        self.setIconSize(QtCore.QSize(24, 24))
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        model = StartupItemModel()
        sel_model = QtCore.QItemSelectionModel(model)
        self.setModel(model)
        self.setSelectionModel(sel_model)

    def deleteSelected(self):
        model = self.model()
        sel_model = self.selectionModel()
        rows = list(set([x.row() for x in sel_model.selectedIndexes()]))
        rows.sort()
        rows.reverse()
        for row in rows:
            model.removeRow(row)

    def keyPressEvent(self, event):
        key = event.key()
        if key in (QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace):
            self.deleteSelected()
            return
        super(StartupView, self).keyPressEvent(event)



class AssetInfoWidget(QtWidgets.QGroupBox):
    r"""
        アセット名、アッセとタイプ、プロジェクト名を格納する。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット。
        """
        super(AssetInfoWidget, self).__init__('Asset Information', parent)

        flayout = QtWidgets.QFormLayout(self)

        label = QtWidgets.QLabel('Asset Name')
        self.__assetname = QtWidgets.QLineEdit()
        flayout.addRow(label, self.__assetname)
        
        label = QtWidgets.QLabel('Project')
        self.__project = QtWidgets.QLineEdit()
        flayout.addRow(label, self.__project)

        label = QtWidgets.QLabel('Asset Type')
        self.__assettype = QtWidgets.QComboBox()
        self.__assettype.setMinimumSize(
            150, self.__assetname.minimumSize().height()
        )
        self.__assettype.addItems(core.AssetTypes)
        flayout.addRow(label, self.__assettype)

    def setAssetName(self, name):
        r"""
            アセット名をセットする。
            
            Args:
                name (str):
        """
        self.__assetname.setText(name)

    def assetName(self):
        r"""
            アセット名を返す。
            
            Returns:
                str:
        """
        return self.__assetname.text()

    def setProject(self, project):
        r"""
            プロジェクト名をセットす。
            
            Args:
                project (str):
        """
        self.__project.setText(project)

    def project(self):
        r"""
            プロジェクト名を返す。
            
            Returns:
                str:
        """
        return self.__project.text()

    def setAssetType(self, assetType):
        r"""
            アセットの種類をセットする。
            
            Args:
                assetType (str):
        """
        if not assetType:
            self.__assettype.setCurrentIndex(0)
            return

        index = self.__assettype.findText(assetType)
        if index < 0:
            raise ValueError('Invalid asset type : %s' % assetType)
        self.__assettype.setCurrentIndex(index)

    def assetType(self):
        r"""
            アセットの種類を返す。
            
            Returns:
                str:
        """
        return self.__assettype.currentText()


class ConstructorList(QtWidgets.QGroupBox):
    r"""
        コンストラクタを選択するコンボボックスを提供するクラス。
    """
    currentIndexChanged = QtCore.Signal(str)
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット。
        """
        super(ConstructorList, self).__init__('Constructor', parent)
        self.__constructor_manager = constructors.ConstructorManager()
        self.__is_signal_emitted = True

        # 一覧用のUI構築。=====================================================
        label = QtWidgets.QLabel('Constructor Type')
        self.__cst_list = QtWidgets.QComboBox()
        self.__cst_list.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        #======================================================================

        layout = QtWidgets.QFormLayout(self)
        layout.addRow(label, self.__cst_list)

        self.__cst_list.currentIndexChanged.connect(self.sendSignal)

    def sendSignal(self, index):
        r"""
            ComboBoxの選択に変更があった場合にシグナルを送出する
            ためのコールバック。
            self.__is_signal_emittedがFalseの場合はシグナルを送出しない。
            
            Args:
                index (int):
        """
        if self.__is_signal_emitted:
            data = self.__cst_list.itemData(index)
            self.currentIndexChanged.emit(data)

    def currentConstructorName(self):
        r"""
            現在アクティブになっているconstructorの名前を返す。
            
            Returns:
                str:
        """
        return self.__cst_list.itemData(self.__cst_list.currentIndex())

    def manager(self):
        r"""
            コンストラクタを管理するマネージャーオブジェクトを返す。
            
            Returns:
                constructors.ConstructorManager:
        """
        return self.__constructor_manager

    def updateList(self):
        r"""
            リストを更新する。
            リスト更新中はcurrentIndexChangedは送出しない。
        """
        self.__is_signal_emitted = False
        self.__cst_list.clear()
        for name in self.manager().names():
            self.__cst_list.addItem(lib.title(name), name)
        self.__is_signal_emitted = True

    def setConstructor(self, constructorName, isSilent=False):
        r"""
            constructorをセットする。
            与えらた名前がリストに存在しない場合はFalseを返す。
            isSilentがTrueの場合、値変更に伴うシグナルの送出を行わない。
            
            Args:
                constructorName (str):constructor名。
                isSilent (bool):
                
            Returns:
                bool:
        """
        index = self.__cst_list.findData(constructorName)
        if index == -1:
            return False
        self.__is_signal_emitted = isSilent == False
        self.__cst_list.setCurrentIndex(index)
        self.__is_signal_emitted = True
        return True


class StartupManager(QtWidgets.QWidget, factoryModules.AbstractFactoryTabMixin):
    r"""
        ui.factory.のadvancedTabWidgetに使用するタブの一つ。
        AbstractFactoryTabMixinクラスを継承し、advancedTabWidgetからの信号を受け
        取れるようになっている。
    """
    DirectoryList = {
        'model' : 'models',
        'workspace' : 'workScenes'
    }
    TagName = 'grisFactoryWorkspace'
    
    settingsApplied = QtCore.Signal()
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):
        """
        super(StartupManager, self).__init__(parent)
        self.customInit()

        self.__asset_info = AssetInfoWidget()
        
        self.__const_list = ConstructorList()
        self.__const_list.currentIndexChanged.connect(self.loadSettings)

        self.__startup_view = StartupView(self)
        self.__apply_btn = QtWidgets.QPushButton('Apply')
        self.__apply_btn.clicked.connect(self.applySettings)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.__asset_info)
        layout.addWidget(self.__const_list)
        layout.addWidget(self.__startup_view)
        layout.addWidget(self.__apply_btn)
        
        self.resize(480, 620)

    def loadSettings(self, constructorName):
        r"""
            設定ファイルからUIを構築する。
            
            Args:
                constructorName (str):コンストラクタ名
        """
        class DirectoryName(object):
            r"""
                ローカル専用クラス。
            """
            def __init__(self, name):
                r"""
                    Args:
                        name (str):
                """
                self.name = name
            def directoryName(self):
                r"""
                    ディレクトリ名を返すローカル関数。
                    
                    Returns:
                        str:
                """
                return self.name

        def createItems(
            model, const_modules, itemlist, nameset, moduleIcon,
            constructor=None
        ):
            r"""
                アイテムをモデルに追加するローカル関数。
                
                Args:
                    model (QtGui.QStandardItemModel):
                    const_modules (list):Constructorのモジュール情報
                    itemlist (dict):Factoryで定義されている全モジュール情報
                    nameset (list):設定ファイル側のモジュール情報。
                    moduleIcon (QtGui.QIcon):
                    constructor (None):
            """
            row = model.rowCount()
            for info in const_modules:
                mod_name = info.moduleName()
                default_data = factoryModules.ModuleInfo(
                    mod_name, info.name(), info.alias(), info.tag()
                )
                # モジュール名がFactoryModulesにない場合はエラーを返す。=======
                if constructor and not mod_name in itemlist:
                    raise KeyError(
                        (
                            'The module name "%s"'
                            'that consists of "%s" is invalid.'
                        ) % (mod_name, constructor)
                    )
                # =============================================================
                
                # =============================================================
                datalist = nameset.get(mod_name)
                if not datalist:
                    datalist = [default_data]
                # =============================================================

                # 入力モジュール名に該当するモジュールを取得。
                cls = itemlist.get(mod_name)

                for data in datalist:
                    if data.tag() != info.tag():
                        # data = default_data
                        continue

                    # モジュール名を表示するアイテムを作成。===================
                    mod_item = QtGui.QStandardItem(mod_name)
                    mod_item.setData(info.tag())
                    mod_item.setIcon(moduleIcon)
                    # =========================================================

                    # ディレクトリ名を表示するアイテムを作成。=================
                    if not data.name():
                        name = info.name()
                        name = name if name else cls().directoryName()
                        icon = uilib.Icon('error')
                    else:
                        name = data.name()
                        icon = uilib.Icon('folder')
                    dir_item = QtGui.QStandardItem(name)
                    dir_item.setIcon(icon)
                    # =========================================================

                    # UIに表示するエイリアス名を表示するアイテムを作成。=======
                    alias = data.alias() if data.alias() else info.alias()
                    alias_item = QtGui.QStandardItem(alias)
                    # =========================================================

                    model.setItem(row, 0, mod_item)
                    model.setItem(row, 1, dir_item)
                    model.setItem(row, 2, alias_item)
                    row += 1

        # アイテムをクリアする。
        model = self.__startup_view.model()
        model.removeRows(0, model.rowCount())

        from functools import partial
        c_manager = constructors.ConstructorManager()
        fmm = factoryModules.FactoryModuleManager()
        fs = factoryModules.FactorySettings()
        
        # Constructorで定義されているFactoryModuleの情報を取得する。
        constructor = c_manager.module(constructorName)
        cls = constructor.Constructor()

        # 設定ファイルから読み込んだmodule名と対応ディレクトリ名の ============
        # 組み合わせを辞書型として保持する。
        nameset = fs.listModulesAsDict()
        # =====================================================================

        # Constructorクラスで定義されているFactoryModuleをリストに追加する。
        createItems(
            model,
            cls.FactoryModules, fmm.moduleNameList(), nameset,
            uilib.Icon('unit'), cls.__class__
        )

        # 特別枠のworksとmodelsを追加する。
        createItems(
            model,
            [
                factoryModules.ModuleInfo(x, '', '')
                for x in cls.SpecialModules
            ],
            {
                x : partial(DirectoryName, cls.SpecialModules[x])
                for x in cls.SpecialModules
            },
            nameset, uilib.Icon('uiBtn_system')
        )
        self.__startup_view.setColumnWidth(0, 150)
        self.__startup_view.resizeColumnToContents(1)

    def loadFile(self):
        r"""
            factoryModules.FactorySettingsの内容に従ってUIを更新する。
        """
        fmm = factoryModules.FactoryModuleManager()
        fs = factoryModules.FactorySettings()
        constructor_name = fs.constructorName(False)
        
        self.__asset_info.setAssetName(fs.assetName(False))
        self.__asset_info.setAssetType(fs.assetType(False))
        self.__asset_info.setProject(fs.project(False))

        self.__const_list.updateList()
        self.__const_list.setConstructor(constructor_name)
        self.loadSettings(self.__const_list.currentConstructorName())

    def refreshState(self):
        r"""
            AdvancedTabWidget内のこのウィジェットがアクティブになった
            時に更新をかける時に呼ばれるメソッド。
        """
        self.loadFile()

    def createConstructionScripts(self):
        r"""
            コンストラクタ用のスクリプトファイルを生成する。
        """
        settings = factoryModules.FactorySettings()
        cm = constructors.ConstructorManager()
        cmd, module = cm.getConstructionScriptCmd(
            settings.constructorName(), True
        )
        cmd(settings, module)

    def applySettings(self):
        r"""
            モジュールとディレクトリのひも付けをルート・ディレクトリに
            適用するメソッド。
        """
        model = self.__startup_view.model()
        nameset = {}
        # モジュール名とディレクトリ名の組み合わせをチェックし、==============
        # ディレクトリ名が空の場合はエラーを返す。
        for i in range(model.rowCount()):
            module_item = model.item(i, 0)
            module = module_item.text()
            tag = module_item.data()
            dirname_item = model.item(i, 1)
            dirname = dirname_item.text()

            alias_item = model.item(i, 2)
            alias = alias_item.text()

            if not dirname:
                raise RuntimeError(
                    'Directory name is empty at "%s",' % module
                )

            data = factoryModules.ModuleInfo(module, dirname, alias, tag)
            nameset.setdefault(module, []).append(data)
            # if module in nameset:
                # nameset[module].append(data)
            # else:
                # nameset[module] = [data]
        # =====================================================================

        # XMLファイルを生成する。==============================================
        settings = factoryModules.FactorySettings()
        root = settings.rootPath()
        if not os.path.isdir(root):
            raise IOError('The root directory was not found : "%s"' % root)

        print('# Create Project at : ')
        print('    {}'.format(root))

        # アセット情報を反映させる。-------------------------------------------
        asset_name = self.__asset_info.assetName()
        asset_type = self.__asset_info.assetType()
        project = self.__asset_info.project()
        constructor_name = self.__const_list.currentConstructorName()
        
        if not asset_name:
            raise RuntimeError('No asset name specified.')
        if not asset_type:
            raise RuntimeError('No asset type specified.')
        if not project:
            raise RuntimeError('No project specified.')
        if not constructor_name:
            raise RuntimeError('No constructor specified.')

        settings.setAssetName(asset_name)
        settings.setAssetType(asset_type)
        settings.setProject(project)
        settings.setConstructorName(constructor_name)
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        settings.clearModules()
        for key in nameset:
            for data in nameset[key]:
                settings.addModule(key, data)
        settings.saveFile()
        # ---------------------------------------------------------------------
        # =====================================================================

        # ディレクトリを作成する。=============================================
        factoryModules.createFactoryDirectory()
        # =====================================================================

        self.createConstructionScripts()
        
        settings.updateRootPath()
        self.refreshState()
        
        self.settingsApplied.emit()
