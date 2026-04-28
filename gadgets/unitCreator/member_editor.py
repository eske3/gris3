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
from ... import rigScripts
from ... import factoryModules, uilib, grisNode, node
from ...tools import selectionUtil
QtWidgets, QtGui, QtCore = (
    factoryModules.QtWidgets, factoryModules.QtGui, factoryModules.QtCore
)

class AbstractMemberEditor(QtWidgets.QWidget):
    r"""
        ユニットのメンバー編集を行うGUIの基底クラス。
    """
    def __init__(self, attr, parent=None):
        super(AbstractMemberEditor, self).__init__(parent)
        r"""
            Args:
               attr (str): 操作対象となるアトリビュート名
               parent (QtWidgets.QWidget): 親ウィジェット
        """
        self.__unit = None
        self.__attr = attr
        self.__as_root = False

    def attr(self):
        r"""
            編集するユニットを設定する。。

            Returns:
                str:操作対象となる
        """
        return self.__attr

    def updateUI(self, unit, attr):
        r"""
            UIの更新を行うための上書き専用メソッド。

            Args:
                unit (grisNode.Unit):操作対象となるユニット
                attr (str):操作対象となるユニット名
        """
        pass

    def setUnit(self, unit=None):
        r"""
            編集するユニットを設定する。
            合わせてGUIの更新も行う。

            Args:
                str:操作対象となるユニット名
        """
        self.__unit = unit
        u = self.unit()
        if not u:
            return
        attr = self.attr()
        if not u.hasAttr(attr):
            return
        self.updateUI(u, attr)

    def unit(self):
        r"""
            設定された編集ユニットを返す。

            Returns:
                grisNode.Unit:
        """
        try:
            unit = grisNode.Unit(self.__unit)
        except:
            unit = None
        return unit

    def setAsRoot(self, as_root):
        self.__as_root = bool(as_root)

    def isRoot(self):
        return self.__as_root

class SingleMemberEditor(AbstractMemberEditor):
    def __init__(self, attr, parent=None):
        super(SingleMemberEditor, self).__init__(attr, parent)
        self.__name_field = QtWidgets.QLineEdit()
        self.__name_field.setReadOnly(True)

        reg_btn = uilib.OButton(uilib.IconPath('uiBtn_import'))
        reg_btn.clicked.connect(self.setMember)
        reg_btn.setBgColor(*uilib.Color.DebugColor)

        sel_btn = uilib.OButton(uilib.IconPath('uiBtn_select'))
        sel_btn.clicked.connect(self.select)
        sel_btn.setBgColor(*uilib.Color.ExecColor)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(uilib.ZeroMargins)
        layout.addWidget(self.__name_field)
        layout.addWidget(reg_btn)
        layout.addWidget(sel_btn)

    def setNodeName(self, nodeName):
        r"""
            ノード名をフィールドに設定する。

            Args:
                nodeName (str):設定するノード名
        """
        self.__name_field.setText(nodeName)

    def nodeName(self):
        r"""
            フィールドに設定されているノード名を返す。

            Returns:
                str:
        """
        return self.__name_field.text()

    def updateUI(self, unit, attr):
        r"""
            UIの更新を行う。

            Args:
                unit (grisNode.Unit):操作対象となるユニット
                attr (str):操作対象となるユニット名
        """
        member_node = unit.getMember(attr)
        if not member_node:
            member_node = ''
        self.setNodeName(member_node)

    def select(self):
        node_name = self.__name_field.text()
        selectionUtil.selectNodes([node_name])

    def setMember(self):
        unit = self.unit()
        if not unit:
            return
        selected = selectionUtil.selected()
        if not selected:
            return
        attr = self.attr()
        old_member = unit.getMember(attr)
        rigScripts.unsetRootForUnit(unit, old_member)
        unit.setMember(attr, selected[0])
        rigScripts.setRootForUnit(unit, selected[0])
        self.updateUI(unit, attr)


class SoloMemberEditor(SingleMemberEditor):
    deleteButtonClicked = QtCore.Signal(QtWidgets.QWidget)
    memberWasSet = QtCore.Signal(bool)

    def __init__(self, member='', parent=None):
        super(SoloMemberEditor, self).__init__('', parent)
        del_btn = uilib.OButton(uilib.IconPath('uiBtn_trush'))
        del_btn.clicked.connect(self.__on_deleting)
        self.layout().addWidget(del_btn)
        self.setNodeName(member)

    def __on_deleting(self):
        self.deleteButtonClicked.emit(self)

    def setMember(self):
        selected = selectionUtil.selected()
        if not selected:
            return
        self.setNodeName(selected[0])
        self.memberWasSet.emit(True)


class MultMemberEditor(AbstractMemberEditor):
    def __init__(self, attr, parent=None):
        super(MultMemberEditor, self).__init__(attr, parent)
        grp = QtWidgets.QGroupBox('Members')
        self.__layout = QtWidgets.QFormLayout(grp)
        self.__add = uilib.OButton(uilib.IconPath('uiBtn_plus'))
        self.__add.clicked.connect(self.appendEditor)
        self.__apply = QtWidgets.QPushButton('Apply')
        self.__apply.clicked.connect(self.apply)
        self.__cancel = QtWidgets.QPushButton('Cancel')
        self.__cancel.clicked.connect(self.revertUI)

        layout = QtWidgets.QGridLayout(self)
        layout.setSpacing(1)
        layout.setColumnStretch(0, 1)
        layout.addWidget(grp, 0, 0, 1, 4)
        layout.addWidget(self.__add, 1, 1, 1, 1)
        layout.addWidget(self.__cancel, 1, 2, 1, 1)
        layout.addWidget(self.__apply, 1, 3, 1, 1)

    def uiLayout(self):
        return self.__layout

    def setActive(self, isActive):
        self.__cancel.setEnabled(isActive)
        self.__apply.setEnabled(isActive)

    def createSoloEditor(self, member=''):
        editor = SoloMemberEditor(member)
        editor.deleteButtonClicked.connect(self.deleteEditor)
        editor.memberWasSet.connect(self.setActive)
        self.uiLayout().addWidget(editor)
        return editor

    def appendEditor(self):
        selected = selectionUtil.selected()
        if not selected:
            return [self.createSoloEditor()]
        results = []
        for sel in selected:
            editor = self.createSoloEditor(sel)
            results.append(editor)
        self.setActive(True)
        return results

    def updateUI(self, unit, attr):
        member_nodes = unit.getMember(attr)
        layout = self.uiLayout()
        uilib.clearLayout(layout)
        self.setActive(False)
        if not isinstance(member_nodes, list):
            return
        for member in member_nodes:
            self.createSoloEditor(member)

    def revertUI(self):
        unit = self.unit()
        attr = self.attr()
        self.updateUI(unit, attr)

    def deleteEditor(self, editor):
        layout = self.uiLayout()
        layout.removeWidget(editor)
        editor.deleteLater()
        self.setActive(True)

    def listEditors(self):
        layout = self.uiLayout()
        editors = []
        for i in range(layout.count()):
            item = layout.itemAt(i)
            w = item.widget()
            if w:
                editors.append(w)
        return editors

    def apply(self):
        unit = self.unit()
        attr = self.attr()
        editors = self.listEditors()
        old_members = set(unit.getMember(attr))
        plug = unit.attr(attr)
        with node.DoCommand():
            if plug.isArray():
                for p in plug.listArray():
                    p.disconnect()
            if old_members:
                rigScripts.unsetRootForUnit(unit, *old_members)
            target_nodes = []
            for e in editors:
                target = e.nodeName()
                if grisNode.node.cmds.objExists(target):
                    target_nodes.append(target)
            if target_nodes:
                rigScripts.setRootForUnit(unit, *target_nodes)
                unit.addMember(attr, target_nodes)

        self.updateUI(unit, attr)