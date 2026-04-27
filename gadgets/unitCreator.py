# -*- coding: utf-8 -*-
r'''
    @brief    ここに説明文を記入
    @date        2017/01/22 0:04[Eske](eske3g@gmail.com)
    @update      2017/09/09 11:18[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
from PySide2 import QtWebEngineWidgets

from .. import grisNode
from .. import factoryModules, lib, uilib, core, rigScripts
QtWidgets, QtGui, QtCore = (
    factoryModules.QtWidgets, factoryModules.QtGui, factoryModules.QtCore
)


class FloatOptionWidget(QtWidgets.QDoubleSpinBox):
    r"""
        float型のオプションを表示する。
    """
    def getValue(self):
        r"""
            floatの値を返す。

            Returns:
                float:
        """
        return self.value()


class IntOptionWidget(QtWidgets.QSpinBox):
    r"""
        int型のオプションを表示する。
    """
    def getValue(self):
        r"""
            Intの値を返す。

            Returns:
                int:
        """
        return self.value()


class BoolOptionWidget(QtWidgets.QCheckBox):
    r"""
        ブール型のオプションを表示する。
    """
    def getValue(self):
        r"""
            チェックされているかどうかを返す。

            Returns:
                bool:
        """
        return self.isChecked()


class EnumOptionWidget(QtWidgets.QComboBox):
    r"""
        Enumerate型のオプションを表示する。
    """
    def getValue(self):
        r"""
            現在選択されているテキストを返す。

            Returns:
                str:
        """
        return self.currentText()


class StringOptionWidget(QtWidgets.QLineEdit):
    r"""
        文字入力型のオプションを表示する
    """
    def getValue(self):
        r"""
            文字列の値を返す。

            Returns:
                str:
        """
        return self.text()


class OptionWidgets(object):
    Widgets = {
        'float' : FloatOptionWidget,
        'int' : IntOptionWidget,
        'bool' : BoolOptionWidget,
        'enum' : EnumOptionWidget,
        'string' : StringOptionWidget,
    }

def createOptionWidget(optionObject):
    r"""
        オプション表示UIにオプション項目を追加する。

        Args:
            optionObject (rigScript.Option):オプション項目を定義したオブジェクト

        Returns:
            QtWidgets.QWidget: 作成したウィジェット。
    """
    parent_widget = QtWidgets.QWidget()
    layout = QtWidgets.QFormLayout(parent_widget)
    created_widgets = []

    for data in optionObject.optionlist():
        widget = OptionWidgets.Widgets[data[0]]()
        widget.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        if data[0] == 'bool':
            widget.setChecked(bool(data[2]))
        elif data[0] == 'enum':
            widget.addItems(data[3])
            widget.setCurrentIndex(data[2])
        elif data[0] == 'string':
            widget.setText(data[2])
        else:
            widget.setValue(data[2])
            widget.setMinimum(data[3])
            widget.setMaximum(data[4])
        widget.optionName = data[1]
        layout.addRow(QtWidgets.QLabel(lib.title(data[1])), widget)
        created_widgets.append(widget)

    return parent_widget, created_widgets


class BasicParamEditor(uilib.FlatScrollArea):
    def isOption(self):
        return True

    def buildUI(self, parent=None):
        r"""
             Args:
                 parent (QtWidgets.QWidget):親ウィジェット
         """
        from .. import system

        # パラメータを編集するUI。=============================================
        suffix_field = QtWidgets.QLineEdit()

        pos_box = QtWidgets.QComboBox()
        pos_box.addItems(system.GlobalSys().defaultPositionList())
        pos_box.setCurrentIndex(1)

        form = QtWidgets.QFormLayout()
        if self.isOption():
            name_field = QtWidgets.QLineEdit()
            form.addRow('Name', name_field)
            self.setName = name_field.setText
            self.name = name_field.text
        form.addRow('Suffix', suffix_field)
        form.addRow('Position', pos_box)
        self.setSuffix = suffix_field.setText
        self.suffix = suffix_field.text
        self.setPositionIndex = pos_box.setCurrentIndex
        self.positionIndex = pos_box.currentIndex
        # =====================================================================

        layout = QtWidgets.QVBoxLayout(parent)
        layout.addLayout(form)

        if not self.isOption():
            return
        # オプションを編集するUI。=============================================
        option_group = QtWidgets.QGroupBox('Option')
        option_tab = QtWidgets.QStackedWidget()

        option_layout = QtWidgets.QVBoxLayout(option_group)
        option_layout.addWidget(option_tab)
        # =====================================================================

        layout.addWidget(option_group)

        # 外部からのアクセス用メソッドの移植。
        self.addOptionWidget = option_tab.addWidget
        self.optionTabCount = option_tab.count
        self.setCurrentIndex = option_tab.setCurrentIndex
        self.currentWidget = option_tab.currentWidget


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


class Creator(QtWidgets.QSplitter):
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

        self.addWidget(main_widget)
        self.addWidget(self.__editor)

        self.refreshPresetList()

    def createRoot(self):
        r'''
            @brief  ルートを作成する。
            @return None
        '''
        from .. import core
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
        return createOptionWidget(optionObject)[0]

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
                item.setData(prename, QtCore.Qt.UserRole+2)
                item.setData(p.description(), QtCore.Qt.UserRole+3)
                item.setData(
                    '\n'.join([x() for x in p.includes()]),
                    QtCore.Qt.UserRole+4
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
            item.setData(basename, QtCore.Qt.UserRole+3)

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
                    self.__param_editor.optionTabCount()-1,
                    QtCore.Qt.UserRole+2
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

        data = index.data(QtCore.Qt.UserRole+1)
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
            self.__currentModule = index.data(QtCore.Qt.UserRole+2)
            self.__is_preset = True
            self.__preset_view.setPreset(
                index.data(),
                index.data(QtCore.Qt.UserRole+3),
                index.data(QtCore.Qt.UserRole+4),
            )
            return

        self.__editor.setCurrentIndex(2)
        self.__currentModule = index.data()
        self.__param_editor.setName(index.data(QtCore.Qt.UserRole+3))
        tab_index = index.data(QtCore.Qt.UserRole+2)
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


class UnitLister(QtWidgets.QWidget):
    r"""
        現在のシーン中にあるユニットを一覧で表示するGUIを提供する
    """
    selectionChanged = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(UnitLister, self).__init__(parent)
        self.__always_update = True
        label = QtWidgets.QLabel('Units')
        model = QtGui.QStandardItemModel(0, 1)
        sel_model = QtCore.QItemSelectionModel(model)
        sel_model.selectionChanged.connect(self.__on_selection)
        self.__view = QtWidgets.QListView()
        self.__view.setModel(model)
        self.__view.setSelectionModel(sel_model)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.__view)

    def view(self):
        return self.__view

    def setIsAlwayUpdate(self, isAllwaysUpdate):
        self.__always_update = bool(isAllwaysUpdate)

    def selectedUnit(self):
        selected = [
                x.data() for x in self.view().selectionModel().selectedIndexes()
        ]
        if not selected:
            return
        return selected[0]

    def refreshList(self):
        model = self.view().model()
        clear_cmd = lambda : model.removeRows(0, model.rowCount())
        old_units = [model.item(x, 0).data() for x in range(model.rowCount())]
        cur_unit = self.selectedUnit()
        try:
            root = grisNode.getGrisRoot()
        except grisNode.GrisRootError as e:
            clear_cmd()
            return
        unit_grp = root.unitGroup()
        new_units = unit_grp.listUnits()

        # 過去のユニット一覧と比較して同一の場合更新をスキップ。
        if len(new_units) != 0 and len(old_units) == len(new_units):
            for ou, nu in zip(old_units, new_units):
                if not ou != nu:
                    break
            else:
                return
        clear_cmd()
        sel_index = None
        for row, unit in enumerate(unit_grp.listUnits()):
            unit_name = unit()
            item = QtGui.QStandardItem(unit_name)
            model.setItem(row, 0, item)
            if cur_unit == unit_name:
                sel_index = model.indexFromItem(item)
        if sel_index:
            self.view().selectionModel().select(
                sel_index, QtCore.QItemSelectionModel.ClearAndSelect
            )

    def enterEvent(self, event):
        if self.__always_update:
            self.refreshList()

    def __on_selection(self, selected, deselected):
        for index in  selected.indexes():
            self.selectionChanged.emit(index.data())
            return


class ParamEditor(BasicParamEditor):
    r"""
        ユニットノパラメータを編集するGUIを提供するクラス。
    """
    pass


class UnitEditorWidget(BasicParamEditor):
    r"""
        各Unitごとの編集機能をGUIとして表示するためのクラス。
    """
    def __init__(self, unit, parent=None):
        self.__unit_node_name = unit()
        self.__tmp_unit = unit
        super(UnitEditorWidget, self).__init__(parent)
        self.__tmp_unit = None
        self.__unit_node_name = ''

    def setUnitNode(self, nodename):
        self.__unit_node_name = nodename

    def unit(self):
        if self.__tmp_unit:
            return self.__tmp_unit
        unit = grisNode.Unit(self.__unit_node_name)
        return unit

    def isOption(self):
        return False

    def buildUI(self, parent=None):
        r"""
            Args:
                parent(QtWidgets.QWidget):親ウィジェット
        """
        super(UnitEditorWidget, self).buildUI(parent)
        module = rigScripts.getRigModule(self.unit().unitName())
        if hasattr(module, 'Editor'):
            obj = module.Editor()
        elif hasattr(module, 'Option'):
            obj = module.Option()
        else:
            return
        widgets = createOptionWidget(obj)
        grp = QtWidgets.QGroupBox('Parameters')
        layout = QtWidgets.QVBoxLayout(grp)
        layout.addWidget(widgets[0])

        layout = parent.layout()
        layout.addWidget(grp)
        layout.addStretch()

    def updateUI(self):
        unit = self.unit()
        print(unit)

class UnitEditorOption(QtWidgets.QWidget):
    r"""
        Unitを編集するためのGUIを提供するクラス。
    """
    def __init__(self, parent=None):
        super(UnitEditorOption, self).__init__(parent)
        self.__created_guis = []
        label = QtWidgets.QLabel('Unit:')
        self.__type_label = QtWidgets.QLabel()
        font = self.__type_label.font()
        font.setPixelSize(int(font.pixelSize() * 1.25))
        font.setBold(True)
        self.__type_label.setFont(font)

        self.__stacked = uilib.ScrolledStackedWidget()
        self.__stacked.setOrientation(QtCore.Qt.Vertical)
        no_operation = QtWidgets.QLabel('No operation')
        no_operation.setAlignment(QtCore.Qt.AlignCenter)
        self.__stacked.addTab(no_operation)

        layout = QtWidgets.QGridLayout(self)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(1, 1)
        layout.addWidget(label, 0, 0, 1, 1, QtCore.Qt.AlignBottom)
        layout.addWidget(self.__type_label, 0, 1, 1, 1, QtCore.Qt.AlignBottom)
        layout.addWidget(self.__stacked, 1, 0, 1, 2)

    def refreshGui(self, unitName):
        try:
            unit = grisNode.Unit(unitName)
        except:
            self.__stacked.moveTo(0)
            self.__type_label.setText('-Not Unit-')
            return
        unit_type = unit.unitName()
        self.__type_label.setText(unit_type)
        if unit_type in self.__created_guis:
            index = self.__created_guis.index(unit_type) + 1
        else:
            edit_option = UnitEditorWidget(unit)
            self.__created_guis.append(unit_type)
            self.__stacked.addTab(edit_option, False)
            index = len(self.__created_guis)
        self.__stacked.moveTo(index)
        editor = self.__stacked.currentWidget()
        editor.setUnitNode(unitName)
        editor.updateUI()


class Editor(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Editor, self).__init__(parent)

        unit_list = UnitLister()
        option = UnitEditorOption()
        unit_list.selectionChanged.connect(option.refreshGui)
        self.refreshList = unit_list.refreshList
        splitter = QtWidgets.QSplitter()
        splitter.addWidget(unit_list)
        splitter.addWidget(option)
        splitter.setStretchFactor(1, 1)

        reload_btn = uilib.OButton(uilib.IconPath('uiBtn_reload.png'))
        reload_btn.clicked.connect(unit_list.refreshList)
        rel_check = QtWidgets.QCheckBox('Auto update when the widget is active')
        rel_check.setChecked(True)
        rel_check.stateChanged.connect(unit_list.setIsAlwayUpdate)

        opt_widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(opt_widget)
        layout.addWidget(reload_btn)
        layout.addStretch()
        layout.addWidget(rel_check)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(opt_widget)
        layout.addWidget(splitter)
        layout.setStretchFactor(splitter, 1)


class Manager(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        super(Manager, self).__init__(parent)
        self.addTab(Creator(), 'Creator')
        self.addTab(Editor(), 'Editor')
        self.currentChanged.connect(self.updateState)

    def updateState(self, index):
        if index == 1:
            self.widget(index).refreshList()


class MainGUI(uilib.AbstractSeparatedWindow):
    def centralWidget(self):
        r"""
            Returns:
                Manager:
        """
        return Manager()


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。

        Returns:
            MainGUI:
    """
    from ..uilib import mayaUIlib
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(400, 600)
    widget.show()
    return widget