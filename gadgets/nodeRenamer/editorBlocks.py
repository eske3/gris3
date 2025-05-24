#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2025/05/11 01:47 Eske Yoshinob[eske3g@gmail.com]
        update:2025/05/11 07:27 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2025 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from ... import uilib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class AbstractEditorBlock(QtWidgets.QWidget):
    r"""
        名前要素ごとの編集機能を提供する基底クラス。
        名前要素のカテゴリ名の表示と、編集機能のUIを提供する。
    """
    def __init__(self, label, parent=None):
        r"""
            Args:
                label (str):
                parent (QtWidgets.QWidget):親オブジェクト
        """
        super(AbstractEditorBlock, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        l = QtWidgets.QLabel(label)
        layout.addWidget(l)
        self.__editor = self.makeEditor()
        layout.addWidget(self.__editor)

    def makeEditor(self):
        r"""
            編集用のエディタを作成して返す上書き専用メソッド。
            
            Returns:
                QtWidgets.QWidget:
        """
        pass

    def editor(self):
        r"""
            編集用のエディタを返す。
            
            Returns:
                QtWidgets.QWidget:
        """
        return self.__editor

    def setFocusToEditor(self):
        r"""
            エディタへフォーカスを移す。
        """
        self.editor().setFocus()


class LineEditorBlock(AbstractEditorBlock):
    r"""
        名前要素ごとの編集機能のうち、文字編集機能を提供する基底クラス。
    """
    def makeEditor(self):
        editor = QtWidgets.QLineEdit()
        editor.setFocusPolicy(QtCore.Qt.StrongFocus)
        print('Strong!')
        return editor

    def setText(self, text):
        r"""
            Args:
                text (str):
        """
        self.editor().setText(text)

    def text(self):
        return self.editor().text()
    
    def setFocusToEditor(self):
        super(LineEditorBlock, self).setFocusToEditor()
        self.editor().selectAll()


class ComboBoxBlock(AbstractEditorBlock):
    def makeEditor(self):
        return QtWidgets.QComboBox()
    
    def addItems(self, itemlist):
        r"""
            Args:
                itemlist (list):
        """
        self.editor().addItems(itemlist)

    def setCurrentItem(self, name):
        r"""
            Args:
                name (str):
        """
        self.editor().setCurrentText(name)

    def text(self):
        return self.editor().currentText()
    
    def setFocusToEditor(self):
        self.editor().showPopup()


class EditableComboBoxBlock(ComboBoxBlock):
    def makeEditor(self):
        editor = super(EditableComboBoxBlock, self).makeEditor()
        editor.setLineEdit(QtWidgets.QLineEdit())
        return editor

    def setText(self, text):
        r"""
            Args:
                text (any):
        """
        self.editor().lineEdit().setText(text)

    def text(self):
        return self.editor().lineEdit().text()