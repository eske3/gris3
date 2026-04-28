#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2025/05/11 01:47 Eske Yoshinob[eske3g@gmail.com]
        update:2025/05/11 01:47 Eske Yoshinob[eske3g@gmail.com]

    License:
        Copyright 2025 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from . import common
from ... import factoryModules, uilib, core, rigScripts
from ...uilib import extendedUI
QtWidgets, QtGui, QtCore = (
    factoryModules.QtWidgets, factoryModules.QtGui, factoryModules.QtCore
)


class ParamEditor(common.BasicParamEditor):
    r"""
        ユニットノパラメータを編集するGUIを提供するクラス。
    """
    pass


class PresetView(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(PresetView, self).__init__('', parent)
        self.__description = QtWidgets.QLabel()

        model = QtGui.QStandardItemModel(0, 2)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Unit Name')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Position')
        self.__includes = QtWidgets.QTreeView()
        self.__includes.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers
        )
        self.__includes.setSelectionMode(
            QtWidgets.QAbstractItemView.NoSelection
        )
        self.__includes.setRootIsDecorated(False)
        self.__includes.setAlternatingRowColors(True)
        self.__includes.setModel(model)

        layout = QtWidgets.QFormLayout(self)
        layout.addRow(QtWidgets.QLabel('Description'), self.__description)
        layout.addRow(QtWidgets.QLabel('Includes'), self.__includes)

    def setPreset(self, label, description, includesText):
        self.setTitle(label)
        self.__description.setText(description)

        model = self.__includes.model()
        model.removeRows(0, model.rowCount())
        for row, text in enumerate(includesText.split()):
            name, position = text.split('-')
            n_item = QtGui.QStandardItem(name)
            p_item = QtGui.QStandardItem(position)
            model.setItem(row, 0, n_item)
            model.setItem(row, 1, p_item)


class UnitPresetView(QtWidgets.QTreeView):
    r"""
        プリセット選択用のリスト機能を提供するクラス。
    """
    def __init__(self, parent=None):
        super(UnitPresetView, self).__init__(parent)
        model = QtGui.QStandardItemModel(0, 1)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Presets')

        sel_model = QtCore.QItemSelectionModel(model)

        # self.__selector.setAlternatingRowColors(True)
        self.setRootIsDecorated(True)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setModel(model)
        self.setSelectionModel(sel_model)


    def drawBranches(self, painter, option, index):
        if not index.parent().isValid():
            if not index.model().hasChildren(index):
                return
        else:
            if index.column() == 0:
                return
        super(UnitPresetView, self).drawBranches(painter, option, index)



class Creator(extendedUI.EasyMovableSplitter):
    r"""
        作成用のUIを提供するクラス。
    """

    def __init__(self):
        super(Creator, self).__init__()
        self.setWindowTitle('+Unit Creator')
        self.setOrientation(QtCore.Qt.Vertical)
        self.__currentModule = ''
        self.__is_preset = False

        # 左側のウィジェットを作成する。=======================================
        # ルートを作成するボタンとリストのリロードボタン。---------------------
        crt_label = QtWidgets.QLabel('Create Root')
        crt_btn = uilib.OButton(uilib.IconPath('uiBtn_plus'))
        crt_btn.clicked.connect(self.createRoot)

        rld_btn = uilib.OButton(uilib.IconPath('uiBtn_reload'))
        rld_btn.clicked.connect(self.refreshPresetList)

        root_creator_layout = QtWidgets.QHBoxLayout()
        root_creator_layout.addWidget(crt_label)
        root_creator_layout.addWidget(crt_btn)
        root_creator_layout.addStretch()
        root_creator_layout.addWidget(rld_btn)
        # ---------------------------------------------------------------------

        # プリセット選択UI。
        self.__selector = UnitPresetView()
        self.__selector.selectionModel().selectionChanged.connect(
            self.updateEditor
        )

        side_layout = QtWidgets.QVBoxLayout()
        side_layout.addLayout(root_creator_layout)
        side_layout.addWidget(self.__selector)
        # =====================================================================

        self.__param_editor = ParamEditor()
        self.__preset_view = PresetView()
        self.__editor = QtWidgets.QStackedWidget()
        self.__editor.addWidget(QtWidgets.QWidget())
        self.__editor.addWidget(self.__preset_view)
        self.__editor.addWidget(self.__param_editor)

        self.create_btn = uilib.OButton()
        self.create_btn.setIcon(uilib.IconPath('uiBtn_addUnit'))
        self.create_btn.clicked.connect(self.create)
        self.create_btn.setSize(48)
        self.create_btn.setBgColor(30, 77, 188)
        self.create_btn.setToolTip('Create selected unit.')
        self.create_btn.setEnabled(False)

        main_widget = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout(main_widget)
        layout.setSpacing(1)
        layout.addLayout(side_layout, 0, 0, 1, 1)
        layout.addWidget(self.create_btn, 0, 1, 1, 1)

        self.addWidgetAsHandle(main_widget)
        self.addWidget(self.__editor)

        self.refreshPresetList()

    def createRoot(self):
        r'''
            @brief  ルートを作成する。
            @return None
        '''
        from ... import core
        with core.Do:
            core.createRoot()

    def addOption(self, optionObject):
        r"""
            オプション表示UIにオプション項目を追加する。

            Args:
                optionObject (rigScript.Option):オプション項目を定義したオブジェクト

            Returns:
                QtWidgets.QWidget:
        """
        return common.createOptionWidget(optionObject)[0]

    def refreshPresetList(self):
        r"""
            プリセットのリストを更新する。
            itemのdata内には
                QtCore.Qt.UserRole+1 : モジュール名
                QtCore.Qt.UserRole+2 : オプション表示タブのインデックス
                QtCore.Qt.UserRole+3 : ベースネーム
            が格納されている。
        """
        model = self.__selector.model()
        model.removeRows(0, model.rowCount())
        rootitem = model.invisibleRootItem()

        modules = rigScripts.rigModuleList(loadMode=1)
        self.__param_editor.addOptionWidget(QtWidgets.QWidget())

        catitems = {}
        items = []

        for mod in modules:
            mod_name = mod.__name__
            prename = mod_name.split('.')[-1]

            # プリセットだった場合の処理。=====================================
            if hasattr(mod, 'Preset'):
                p = mod.Preset()
                item = QtGui.QStandardItem(p.name())
                item.setData('__preset__')
                item.setIcon(QtGui.QIcon(uilib.IconPath('uiBtn_squareLayout')))
                item.setData(prename, QtCore.Qt.UserRole + 2)
                item.setData(p.description(), QtCore.Qt.UserRole + 3)
                item.setData(
                    '\n'.join([x() for x in p.includes()]),
                    QtCore.Qt.UserRole + 4
                )
                rootitem.setChild(rootitem.rowCount(), 0, item)
                continue
            # =================================================================

            # モジュール内にCategory変数があれば、そのカテゴリ内にこの ========
            # モジュールをまとめる。
            if hasattr(mod, 'Category'):
                catname = mod.Category
                if catname in catitems:
                    parentitem = catitems[catname]
                else:
                    parentitem = QtGui.QStandardItem(catname)
                    catitems[catname] = parentitem
            else:
                parentitem = None
            # =================================================================

            # モジュール内にBaseName変数があれば、このモジュールが選択された
            # 時にオプションUIのNameフィールドに、BaseNameの中身を表示する。
            # 無ければRigNamePatternに沿ってモジュール名からNameを作成する。
            if hasattr(mod, 'BaseName'):
                basename = mod.BaseName
            else:
                basename = rigScripts.RigNamePattern.sub('', prename)
            # =================================================================

            item = QtGui.QStandardItem(prename)
            item.setData(mod_name)
            item.setData(basename, QtCore.Qt.UserRole + 3)

            if parentitem:
                parentitem.setChild(parentitem.rowCount(), 0, item)
            else:
                items.append(item)

            # オプション項目がある場合、それをUIとして保持しておく。===========
            if hasattr(mod, 'Option'):
                self.__param_editor.addOptionWidget(
                    self.addOption(mod.Option())
                )
                item.setData(
                    self.__param_editor.optionTabCount() - 1,
                    QtCore.Qt.UserRole + 2
                )
            # =================================================================
        for cat in sorted(catitems.keys()):
            rootitem.setChild(rootitem.rowCount(), 0, catitems[cat])

        for item in items:
            rootitem.setChild(rootitem.rowCount(), 0, item)

    def updateEditor(self, selected, deselected):
        r"""
            編集用UIを更新する。
        """
        index = selected.indexes()
        if not index:
            return
        index = index[0]
        if index.column() != 0:
            return

        data = index.data(QtCore.Qt.UserRole + 1)
        self.__is_preset = False
        if not data:
            self.__editor.setCurrentIndex(0)
            self.create_btn.setEnabled(False)
            self.__param_editor.setCurrentIndex(0)
            self.__param_editor.setName('')
            return
        self.create_btn.setEnabled(True)

        if data == '__preset__':
            self.__editor.setCurrentIndex(1)
            self.__currentModule = index.data(QtCore.Qt.UserRole + 2)
            self.__is_preset = True
            self.__preset_view.setPreset(
                index.data(),
                index.data(QtCore.Qt.UserRole + 3),
                index.data(QtCore.Qt.UserRole + 4),
            )
            return

        self.__editor.setCurrentIndex(2)
        self.__currentModule = index.data()
        self.__param_editor.setName(index.data(QtCore.Qt.UserRole + 3))
        tab_index = index.data(QtCore.Qt.UserRole + 2)
        if tab_index is None:
            self.__param_editor.setCurrentIndex(0)
        else:
            self.__param_editor.setCurrentIndex(tab_index)

    def create(self):
        r"""
            選択されたユニットのユニットノードとジョイント作成を行う。
        """
        if not self.__currentModule:
            raise RuntimeError('No Presets selected.')

        if self.__is_preset:
            with core.Do:
                core.execPreset(self.__currentModule)
            return

        # 必要パラメータを取得。===============================================
        name = self.__param_editor.name()
        suffix = self.__param_editor.suffix()
        position = self.__param_editor.positionIndex()
        # =====================================================================

        # オプション項目を辞書として取得。=====================================
        widget = self.__param_editor.currentWidget()
        layout = widget.layout()
        options = {}
        if layout:
            row_num = layout.rowCount()
            for index in range(row_num):
                value_widget = layout.itemAt(
                    index, QtWidgets.QFormLayout.FieldRole
                )
                widget = value_widget.widget()

                options[widget.optionName] = widget.getValue()
        # =====================================================================
        with core.Do:
            core.createJoint(
                unitType=self.__currentModule,
                baseName=name, position=position, suffix=suffix,
                options=options
            )

