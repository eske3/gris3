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
from ... import factoryModules, lib, uilib

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

    def editUnit(self, unit, attr, value):
        unit(attr, value)


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

    def editUnit(self, unit, attr, value):
        unit(attr, value)


class BoolOptionWidget(QtWidgets.QCheckBox):
    r"""
        ブール型のオプションを表示する。
    """
    def __init__(self, parent=None):
        super(BoolOptionWidget, self).__init__(parent)
        self.valueChanged = self.toggled

    def getValue(self):
        r"""
            チェックされているかどうかを返す。

            Returns:
                bool:
        """
        return self.isChecked()

    def setValue(self, value):
        r"""
            値を更新するためのメソッド。他ウィジェットとの統一インターフェース。

            Args:
                value:bool
        """
        self.setChecked(bool(value))

    def editUnit(self, unit, attr, value):
        unit(attr, value)


class EnumOptionWidget(QtWidgets.QComboBox):
    r"""
        Enumerate型のオプションを表示する。
    """
    def __init__(self, parent=None):
        super(EnumOptionWidget, self).__init__(parent)
        self.valueChanged = self.currentIndexChanged

    def getValue(self):
        r"""
            現在選択されているテキストを返す。

            Returns:
                str:
        """
        return self.currentText()

    def setValue(self, value):
        r"""
            値を更新するためのメソッド。他ウィジェットとの統一インターフェース。

            Args:
                value:str
        """
        self.setCurrentText(value)

    def editUnit(self, unit, attr, value):
        unit(attr, value)


class StringOptionWidget(QtWidgets.QLineEdit):
    r"""
        文字入力型のオプションを表示する
    """
    valueChanged = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(StringOptionWidget, self).__init__(parent)
        self.editingFinished.connect(self.__on_editing)

    def getValue(self):
        r"""
            文字列の値を返す。

            Returns:
                str:
        """
        return self.text()

    def setValue(self, value):
        r"""
            値を更新するためのメソッド。他ウィジェットとの統一インターフェース。

            Args:
                value:str
        """
        self.setText(value)

    def __on_editing(self):
        self.valueChanged.emit(self.text())

    def editUnit(self, unit, attr, value):
        unit(attr, value, type='string')


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
            tuple: 作成したウィジェット。
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
    suffixChanged = QtCore.Signal(str)

    def isOption(self):
        return True

    def buildUI(self, parent=None):
        r"""
             Args:
                 parent (QtWidgets.QWidget):親ウィジェット
         """
        from ... import system

        # パラメータを編集するUI。=============================================
        suffix_field = QtWidgets.QLineEdit()
        suffix_field.editingFinished.connect(self.__on_editing)

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
        self.__suffix_field = suffix_field
        self.setSuffix = suffix_field.setText
        self.suffix = suffix_field.text
        self.setPositionIndex = pos_box.setCurrentIndex
        self.positionIndex = pos_box.currentIndex
        self.positionChanged = pos_box.currentIndexChanged
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

    def __on_editing(self):
        suffix = self.__suffix_field.text()
        self.suffixChanged.emit(suffix)