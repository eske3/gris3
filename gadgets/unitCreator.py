# -*- coding: utf-8 -*-
r'''
    @file     unitCreator.py
    @brief    ここに説明文を記入
    @class    FloatOptionWidget : float型のオプションを表示する。
    @class    IntOptionWidget : int型のオプションを表示する。
    @class    BoolOptionWidget : ブール型のオプションを表示する。
    @class    EnumOptionWidget : Enumerate型のオプションを表示する。
    @class    StringOptionWidget : 文字入力型のオプションを表示する。
    @class    ParamEditor : ここに説明文を記入
    @class    Creator : 作成用のUIを提供するクラス。
    @class    MainGUI : ここに説明文を記入
    @function showWindow : ウィンドウを作成するためのエントリ関数。
    @date        2017/01/22 0:04[Eske](eske3g@gmail.com)
    @update      2017/09/09 11:18[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
import re

import gris3
from gris3 import factoryModules, exporter, lib, uilib, core, rigScripts
from gris3.uilib import factoryUI
QtWidgets, QtGui, QtCore = (
    factoryModules.QtWidgets, factoryModules.QtGui, factoryModules.QtCore
)

class FloatOptionWidget(QtWidgets.QDoubleSpinBox):
    r'''
        @brief       float型のオプションを表示する。
        @inheritance QtWidgets.QDoubleSpinBox
        @date        2017/01/22 0:04[Eske](eske3g@gmail.com)
        @update      2017/09/09 11:18[Eske](eske3g@gmail.com)
    '''
    def getValue(self):
        r'''
            @brief  floatの値を返す。
            @return float
        '''
        return self.value()

class IntOptionWidget(QtWidgets.QSpinBox):
    r'''
        @brief       int型のオプションを表示する。
        @inheritance QtWidgets.QSpinBox
        @date        2017/01/22 0:04[Eske](eske3g@gmail.com)
        @update      2017/09/09 11:18[Eske](eske3g@gmail.com)
    '''
    def getValue(self):
        r'''
            @brief  Intの値を返す。
            @return int
        '''
        return self.value()

class BoolOptionWidget(QtWidgets.QCheckBox):
    r'''
        @brief       ブール型のオプションを表示する。
        @inheritance QtWidgets.QCheckBox
        @date        2017/01/22 0:04[Eske](eske3g@gmail.com)
        @update      2017/09/09 11:18[Eske](eske3g@gmail.com)
    '''
    def getValue(self):
        r'''
            @brief  チェックされているかどうかを返す。
            @return bool
        '''
        return self.isChecked()

class EnumOptionWidget(QtWidgets.QComboBox):
    r'''
        @brief       Enumerate型のオプションを表示する。
        @inheritance QtWidgets.QComboBox
        @date        2017/01/22 0:04[Eske](eske3g@gmail.com)
        @update      2017/09/09 11:18[Eske](eske3g@gmail.com)
    '''
    def getValue(self):
        r'''
            @brief  現在選択されているテキストを返す。
            @return str
        '''
        return self.currentText()

class StringOptionWidget(QtWidgets.QLineEdit):
    r'''
        @brief       文字入力型のオプションを表示する。
        @inheritance QtWidgets.QLineEdit
        @date        2017/01/22 0:04[Eske](eske3g@gmail.com)
        @update      2017/09/09 11:18[Eske](eske3g@gmail.com)
    '''
    def getValue(self):
        r'''
            @brief  文字列の値を返す。
            @return str
        '''
        return self.text()
        
class ParamEditor(uilib.FlatScrollArea):
    r'''
        @brief       ユニットノパラメータを編集するGUIを提供するクラス。
        @inheritance uilib.FlatScrollArea
        @date        2017/09/09 11:18[Eske](eske3g@gmail.com)
        @update      2017/09/09 11:18[Eske](eske3g@gmail.com)
    '''
    def buildUI(self, parent):
        r'''
            @brief  初期化を行う。
            @param  parent : [QtWidgets.QWidget]
            @return None
        '''
        from gris3 import system

        # パラメータを編集するUI。=============================================
        name_label = QtWidgets.QLabel('Name')
        name_field = QtWidgets.QLineEdit()

        suffix_label = QtWidgets.QLabel('Suffix')
        suffix_field = QtWidgets.QLineEdit()

        pos_label = QtWidgets.QLabel('Position')
        pos_box = QtWidgets.QComboBox()
        pos_box.addItems(system.GlobalSys().defaultPositionList())
        pos_box.setCurrentIndex(1)

        form = QtWidgets.QFormLayout()
        form.addRow(name_label, name_field)
        form.addRow(suffix_label, suffix_field)
        form.addRow(pos_label, pos_box)
        # =====================================================================

        # オプションを編集するUI。=============================================
        option_group = QtWidgets.QGroupBox('Option')
        option_tab = QtWidgets.QStackedWidget()
        
        option_layout = QtWidgets.QVBoxLayout(option_group)
        option_layout.addWidget(option_tab)
        # =====================================================================
        
        layout = QtWidgets.QVBoxLayout(parent)
        layout.addLayout(form)
        layout.addWidget(option_group)
        
        # 外部からのアクセス用メソッドの移植。
        self.setName = name_field.setText
        self.name = name_field.text
        self.setSuffix = suffix_field.setText
        self.suffix = suffix_field.text
        self.setPositionIndex = pos_box.setCurrentIndex
        self.positionIndex = pos_box.currentIndex
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
            

class Creator(QtWidgets.QGroupBox):
    r'''
        @brief       作成用のUIを提供するクラス。
        @inheritance QtWidgets.QGroupBox
        @date        2017/01/22 0:04[Eske](eske3g@gmail.com)
        @update      2017/09/09 11:18[Eske](eske3g@gmail.com)
    '''
    Widgets = {
        'float' : FloatOptionWidget,
        'int' : IntOptionWidget,
        'bool' : BoolOptionWidget,
        'enum' : EnumOptionWidget,
        'string' : StringOptionWidget,
    }
    def __init__(self):
        r'''
            @brief  初期化を行う。
            @return None
        '''
        super(Creator, self).__init__('Base Joint Creator')
        self.setWindowTitle('+Unit Creator')
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

        # プリセット選択UI。---------------------------------------------------
        model = QtGui.QStandardItemModel(0, 1)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Presets')
        
        sel_model = QtCore.QItemSelectionModel(model)
        sel_model.selectionChanged.connect(self.updateEditor)

        self.__selector = QtWidgets.QTreeView()
        self.__selector.setAlternatingRowColors(True)
        self.__selector.setRootIsDecorated(True)
        self.__selector.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers
        )
        self.__selector.setModel(model)
        self.__selector.setSelectionModel(sel_model)
        # ---------------------------------------------------------------------
        
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
        # self.__param_editor.setWidgetResizable(False)
       
        self.create_btn = uilib.OButton()
        self.create_btn.setIcon(uilib.IconPath('uiBtn_addUnit'))
        self.create_btn.clicked.connect(self.create)
        self.create_btn.setSize(48)
        self.create_btn.setBgColor(30, 77, 188)
        self.create_btn.setToolTip('Create selected unit.')
        self.create_btn.setEnabled(False)

        layout = QtWidgets.QGridLayout(self)
        layout.setSpacing(1)
        layout.addLayout(side_layout, 0, 0, 1, 1)
        layout.addWidget(self.__editor, 1, 0, 1, 2)
        layout.addWidget(self.create_btn, 0, 1, 1, 1)
        layout.setRowStretch(0, 2)
        layout.setRowStretch(1, 1)

        self.refreshPresetList()

    def createRoot(self):
        r'''
            @brief  ルートを作成する。
            @return None
        '''
        from gris3 import core
        with core.Do:
            core.createRoot()

    def addOption(self, optionObject):
        r'''
            @brief  オプション表示UIにオプション項目を追加する。
            @param  optionObject : [rigScript.Option]
            @return None
        '''
        parent_widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(parent_widget)

        for data in optionObject.optionlist():
            widget = self.Widgets[data[0]]()
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

        return parent_widget

    def refreshPresetList(self):
        r'''
            @brief  プリセットのリストを更新する。
            @brief  itemのdata内には
            @brief  QtCore.Qt.UserRole+1 : モジュール名
            @brief  QtCore.Qt.UserRole+2 : オプション表示タブのインデックス
            @brief  QtCore.Qt.UserRole+3 : ベースネーム
            @brief  が格納されている。
            @return None
        '''
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

            # モジュール内にBaseName変数があれば、このモジュールが選択された===
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
        r'''
            @brief  編集用UIを更新するメソッド。
            @param  selected : [edit]
            @param  deselected : [edit]
            @return None
        '''
        index = selected.indexes()
        if not index:
            return
        index = index[0]
        if index.column() != 0:
            return

        row_index = index.row()
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
        r'''
            @brief  選択されたユニットのユニットノードとジョイント作成を行う。
            @return None
        '''
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

class MainGUI(uilib.AbstractSeparatedWindow):
    r'''
        @brief       ここに説明文を記入
        @inheritance uilib.AbstractSeparatedWindow
        @date        2017/06/27 18:31[s_eske](eske3g@gmail.com)
        @update      2017/09/09 11:18[Eske](eske3g@gmail.com)
    '''
    def centralWidget(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return Creator()


def showWindow():
    r'''
        @brief  ウィンドウを作成するためのエントリ関数。
        @return QtWidgets.QWidget
    '''
    from gris3.uilib import mayaUIlib
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(400, 600)
    widget.show()
    return widget