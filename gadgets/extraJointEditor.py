#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ジョイントの編集機能を提供するGUI。
    
    Dates:
        date:2017/06/15 16:35[Eske](eske3g@gmail.com)
        update:2025/05/30 17:25 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from ..tools import extraJoint
from .. import lib, uilib, node
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class ExtraJointCreator(uilib.ClosableGroup):
    r"""
        ExtraJointを作成するウィジェット。
    """
    tagListUpdated = QtCore.Signal(list)
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ExtraJointCreator, self).__init__('Creator', parent)
        self.setWindowTitle('Extra Joint Creator')

        # ベースの名前を指定するフィールド。
        b_label = QtWidgets.QLabel('Base Name')
        self.__basename = QtWidgets.QLineEdit()

        # ノードのタイプを選択するコンボボックス。=============================
        t_label = QtWidgets.QLabel('Node Type')
        self.__type_box = QtWidgets.QComboBox()
        self.__type_box.addItems(('joint', 'transform'))
        # =====================================================================

        # 位置を表す文字列を指定するコンボボックス。===========================
        p_label = QtWidgets.QLabel('Position')
        self.__pos_box = QtWidgets.QComboBox()
        # =====================================================================

        # ベースの名前を指定するフィールド。
        n_label = QtWidgets.QLabel('Node Type Label')
        self.__nodetype = QtWidgets.QLineEdit('bndJnt')
        
        # タグを指定するフィールド
        tg_label = QtWidgets.QLabel('Tag')
        self.__tag = QtWidgets.QComboBox()
        self.__tag.setLineEdit(QtWidgets.QLineEdit())
        rel_btn = uilib.OButton(uilib.IconPath('uiBtn_reset'))
        rel_btn.clicked.connect(self.updateTagList)

        # 作成ボタン。=========================================================
        crt_btn = uilib.OButton()
        crt_btn.setIcon(uilib.IconPath('uiBtn_plus'))
        crt_btn.setSize(48)
        crt_btn.setBgColor(*uilib.Color.ExecColor)
        crt_btn.setToolTip('Create Extra Joint')
        crt_btn.clicked.connect(self.createExtraJoint)
        # =====================================================================

        layout = QtWidgets.QGridLayout(self)
        layout.setVerticalSpacing(2)
        layout.addWidget(b_label, 0, 0, 1, 1)
        layout.addWidget(self.__basename, 0, 1, 1, 3)
        layout.addWidget(t_label, 1, 0, 1, 1)
        layout.addWidget(self.__type_box, 1, 1, 1, 1)
        layout.addWidget(p_label, 1, 2, 1, 1)
        layout.addWidget(self.__pos_box, 1, 3, 1, 1)
        layout.addWidget(crt_btn, 0, 4, 2, 1)
        layout.addWidget(n_label, 2, 0, 1, 1)
        layout.addWidget(self.__nodetype, 2, 1, 1, 1)
        layout.addWidget(tg_label, 3, 0, 1, 1)
        layout.addWidget(self.__tag, 3, 1, 1, 1)
        layout.addWidget(rel_btn, 3, 2, 1, 1)
        
        for l in (b_label, t_label, p_label, n_label, tg_label):
            layout.setAlignment(l, QtCore.Qt.AlignRight)

    def setPositionList(self, positionList=None, defaultIndex=2):
        r"""
            位置を表す文字列のリストをセットする。
            
            Args:
                positionList (list):
                defaultIndex (int):最初に選択されている番号。
        """
        if not positionList:
            from gris3 import system
            positionList = system.GlobalSys().positionList()
            defaultIndex = 2
        self.__pos_box.clear()
        self.__pos_box.addItems(positionList)
        self.__pos_box.setCurrentIndex(defaultIndex)

    def updateTagList(self):
        taglist = [x.tag() for x in extraJoint.listExtraJointsInScene()]
        taglist.append('')
        taglist = list(set(taglist))
        taglist.sort()
        self.__tag.clear()
        self.__tag.addItems(taglist)
        self.tagListUpdated.emit(taglist)

    def createExtraJoint(self):
        r"""
            ジョイントを新規で作成する。
        """
        basename = self.__basename.text()
        nodetype = self.__type_box.currentText()
        nodetype_label = self.__nodetype.text()
        position = self.__pos_box.currentIndex()
        tag = self.__tag.currentText()

        with node.DoCommand():
            extraJoint.create(
                basename, nodetype, nodetype_label, position,
                offset=0, tag=tag
            )


class Editor(QtWidgets.QGroupBox):
    r"""
        ExtraJointを編集するためのボタンを提供するクラス。
    """
    edittingTagFinished = QtCore.Signal()

    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(Editor, self).__init__('Edit Extra Joints', parent)
        
        # 選択GUI。============================================================
        selector = QtWidgets.QWidget()
        btn = uilib.OButton()
        btn.setIcon(uilib.IconPath('uiBtn_select'))
        btn.setSize(32)
        btn.setBgColor(12, 65, 160)
        btn.setToolTip('Select extra joints under the selected nodes')
        btn.clicked.connect(self.selectExtraJoints)
        
        label = QtWidgets.QLabel('Tag Filter :')
        label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.__taglist = QtWidgets.QComboBox()

        layout = QtWidgets.QHBoxLayout(selector)
        layout.addWidget(btn)
        layout.addWidget(label)
        layout.addWidget(self.__taglist)
        layout.setStretchFactor(self.__taglist, 1)
        # =====================================================================
        
        # タグ編集GUI。========================================================
        tag_editor = QtWidgets.QWidget()
        label = QtWidgets.QLabel('Edit tag to selected')
        self.__tag_editor = QtWidgets.QComboBox()
        self.__tag_editor.setLineEdit(QtWidgets.QLineEdit())
        edit_btn = uilib.OButton(uilib.IconPath('uiBtn_edit'))
        edit_btn.clicked.connect(self.editTagToSelected)
        edit_btn.setBgColor(*uilib.Color.ExecColor)
        edit_btn.setSize(32)
        layout = QtWidgets.QHBoxLayout(tag_editor)
        layout.addWidget(label)
        layout.addWidget(self.__tag_editor)
        layout.addWidget(edit_btn)
        layout.setStretchFactor(self.__tag_editor, 1)
        # =====================================================================

        # 編集機能=============================================================
        edit_grp = QtWidgets.QGroupBox('Utilities')
        layout = QtWidgets.QHBoxLayout(edit_grp)
        for color, icon, tooltip, cmd in (
            (
                 (49, 115, 154),
                'uiBtn_mirrorJoints',
                'Create mirrored extra joints from selected.',
                self.mirror
            ),
        ):
            btn = uilib.OButton()
            btn.setIcon(uilib.IconPath(icon))
            btn.setSize(48)
            btn.setBgColor(*color)
            btn.setToolTip(tooltip)
            btn.clicked.connect(cmd)
            layout.addWidget(btn)
        layout.addStretch()
        # =====================================================================

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(1)
        layout.addWidget(selector)
        layout.addWidget(tag_editor)
        layout.addWidget(edit_grp)

    def selectExtraJoints(self):
        r"""
            選択ノード下の全てのExtraJointを選択する。
        """
        tag = self.__taglist.currentText()
        with node.DoCommand():
            extraJoint.selectExtraJoint(tag=tag)

    def mirror(self):
        r"""
            選択されたExtraJointのミラーを作成する。
        """
        with node.DoCommand():
            extraJoint.createMirroredJoint()

    def editTagToSelected(self):
        tag = self.__tag_editor.currentText()
        for ej in extraJoint.listExtraJoints():
            ej.setTag(tag)
        self.edittingTagFinished.emit()

    def setTagList(self, tagList):
        if '' not in tagList:
            tags = [''] + tagList
        else:
            tags = tagList
        for ui in (self.__taglist, self.__tag_editor):
            ui.clear()
            ui.addItems(tags)


class ExtraJointEditor(QtWidgets.QWidget):
    r"""
        ジョイントの作成、編集を行うためのツールを提供するクラス。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ExtraJointEditor, self).__init__(parent)
        self.setWindowTitle('+Extra Joint Editor')
        builder = ExtraJointCreator()
        self.setPositionList = builder.setPositionList
        
        editor = Editor()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(builder)
        layout.addWidget(editor)
        layout.addStretch()
        
        self.__builder = builder
        self.__editor = editor
        builder.tagListUpdated.connect(editor.setTagList)
        editor.edittingTagFinished.connect(self.updateTagList)

    def updateTagList(self):
        self.__builder.updateTagList()


class MainGUI(uilib.AbstractSeparatedWindow):
    def centralWidget(self):
        r"""
            Returns:
                ExtraJointEditor:
        """
        return ExtraJointEditor()

    def show(self):
        r"""
            ウィジェットを表示する。その際位置リストを更新する。
        """
        eje = self.main()
        eje.setPositionList()
        super(MainGUI, self).show()


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。

        Returns:
            MainGUI:
    """
    from gris3.uilib import mayaUIlib
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(400, 350)
    widget.show()
    return widget