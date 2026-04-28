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
from . import common, member_editor
from ... import factoryModules, lib, uilib, grisNode, rigScripts
from ...uilib import extendedUI
QtWidgets, QtGui, QtCore = (
    factoryModules.QtWidgets, factoryModules.QtGui, factoryModules.QtCore
)

class UnitEditorWidget(common.BasicParamEditor):
    r"""
        各Unitごとの編集機能をGUIとして表示するためのクラス。
    """
    def __init__(self, unit, parent=None):
        self.__option_widgets = []
        self.__member_widgets = []
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

    def addMemberEditor(self, editorObj):
        r"""
            メンバー編集用のGUIを追加する。

            Args:
                editorObj(rigScripts.Editor): Editorクラスのインスタンス

            Returns:
                QtWidgets.QWidget:作成したウィジェット
        """
        member_attrs = editorObj.listMemberAttrs()
        for attr in member_attrs:
            if attr:
                break
        else:
            return None
        parent = QtWidgets.QGroupBox('Members')
        layout = QtWidgets.QFormLayout(parent)
        for attrs, editor in zip(
            member_attrs,
            (member_editor.SingleMemberEditor, member_editor.MultMemberEditor)
        ):
            for attr, as_root in attrs:
                e = editor(attr)
                e.setAsRoot(as_root)
                layout.addRow(lib.title(attr), e)
                self.__member_widgets.append(e)
        return parent

    def buildUI(self, parent=None):
        r"""
            Args:
                parent(QtWidgets.QWidget):親ウィジェット
        """
        super(UnitEditorWidget, self).buildUI(parent)
        self.suffixChanged.connect(self.updateSuffix)
        self.positionChanged.connect(self.updatePosition)

        module = rigScripts.getRigModule(self.unit().unitName())
        if hasattr(module, 'Editor'):
            obj = module.Editor()
        elif hasattr(module, 'Option'):
            obj = rigScripts.Editor(module.Option())
        else:
            return
        layout = parent.layout()
        widgets = common.createOptionWidget(obj)
        self.__option_widgets = widgets[1]
        if len(self.__option_widgets):
            grp = QtWidgets.QGroupBox('Parameters')
            grp_layout = QtWidgets.QVBoxLayout(grp)
            grp_layout.addWidget(widgets[0])
            for w in self.__option_widgets:
                w.valueChanged.connect(self.updateUnitValue)
            layout.addWidget(grp)

        member_widget = self.addMemberEditor(obj)
        if member_widget:
            layout.addWidget(member_widget)
        layout.addStretch()

    def updateUI(self):
        unit = self.unit()
        # 基本情報の更新
        for attr, setter in zip(
            ('suffix', 'position'), (self.setSuffix, self.setPositionIndex)
        ):
            setter(unit(attr))

        for opt in self.__option_widgets:
            attr = opt.optionName
            val = unit(attr)
            opt.setValue(val)
        unit_name = unit()
        for w in self.__member_widgets:
            w.setUnit(unit_name)

    def selectUnitNode(self):
        unit = self.unit()
        unit.select()

    def updateSuffix(self, suffix):
        unit = self.unit()
        unit.setSuffix(suffix)

    def updatePosition(self, index):
        unit = self.unit()
        unit.setPosition(index)

    def updateUnitValue(self, value):
        widget = self.sender()
        widget.editUnit(self.unit(), widget.optionName, value)


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

        sel_btn = uilib.OButton(uilib.IconPath('uiBtn_select'))
        sel_btn.setBgColor(*uilib.Color.ExecColor)
        sel_btn.clicked.connect(self.selectUnitNode)

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
        layout.addWidget(sel_btn, 0, 2, 1, 1)
        layout.addWidget(self.__stacked, 1, 0, 1, 3)

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

    def selectUnitNode(self):
        editor = self.__stacked.currentWidget()
        if hasattr(editor, 'selectUnitNode'):
            editor.selectUnitNode()


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


class Editor(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(Editor, self).__init__(parent)

        unit_list = UnitLister()
        option = UnitEditorOption()
        unit_list.selectionChanged.connect(option.refreshGui)
        self.refreshList = unit_list.refreshList
        splitter = extendedUI.EasyMovableSplitter()
        splitter.addWidget(unit_list)
        splitter.addWidgetAsHandle(option)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([200, 400])

        reload_btn = uilib.OButton(uilib.IconPath('uiBtn_reload.png'))
        reload_btn.clicked.connect(unit_list.refreshList)
        rel_check = QtWidgets.QCheckBox('Auto update when the widget is active')
        rel_check.setChecked(True)
        rel_check.stateChanged.connect(unit_list.setIsAlwayUpdate)

        opt_widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(opt_widget)
        layout.setContentsMargins(uilib.ZeroMargins)
        layout.addWidget(reload_btn)
        layout.addStretch()
        layout.addWidget(rel_check)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(splitter)
        layout.addWidget(opt_widget)
        layout.setStretchFactor(splitter, 1)
