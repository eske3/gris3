#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    リネームに関するウィジェットを提供するモジュール。
    
    Dates:
        date:2017/05/30 5:36[Eske](eske3g@gmail.com)
        update:2022/07/31 00:28 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import uilib, node, lib
from gris3.uilib import mayaUIlib
from gris3.tools import nameUtility
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class SimpleRenamer(QtWidgets.QWidget):
    r"""
        シンプルなリネーム機能を提供するクラス。
    """
    renameSucceeded = QtCore.Signal()
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(SimpleRenamer, self).__init__(parent)
        self.__renamer = nameUtility.SimpleRenamer()
        
        # タイトルバー。=======================================================
        label = QtWidgets.QLabel('Single Renamer')
        label.setStyleSheet('QLabel{font-size:20px;}')
        
        pixmap = QtGui.QPixmap(uilib.IconPath('uiBtn_rename'))
        pixmap = pixmap.scaled(
            QtCore.QSize(32, 32),
            QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation
        )
        icon = QtWidgets.QLabel()
        icon.setPixmap(pixmap)

        title_layout = QtWidgets.QHBoxLayout()
        title_layout.addWidget(icon)
        title_layout.addWidget(label)
        title_layout.addStretch()
        # =====================================================================

        self.__editor = uilib.FilteredLineEdit()
        self.__editor.setFilter(nameUtility.NameFilterRegularExpression)

        self.__rename_btn = QtWidgets.QPushButton('Rename')
        self.__rename_btn.clicked.connect(self.rename)
        self.__editor.textEdited.connect(self.updateState)

        cancel_btn = QtWidgets.QPushButton('Cancel')
        self.cancelButtonClicked = cancel_btn.clicked

        layout = QtWidgets.QGridLayout(self)
        layout.addLayout(title_layout, 0, 0, 1, 2)
        layout.addWidget(QtWidgets.QLabel('Enter a new name.'), 1, 0, 1, 2)
        layout.addWidget(self.__editor, 2, 0, 1, 2)
        layout.addWidget(self.__rename_btn, 3, 0, 1, 1)
        layout.addWidget(cancel_btn, 3, 1, 1, 1)

        self.__editor.returnPressed.connect(self.rename)

    def setNode(self, nodeName):
        r"""
            リネーマーの初期化を行う
            
            Args:
                nodeName (str):リネーム対象ノード名。
        """
        self.__renamer.setNode(nodeName)
        self.__editor.setText(self.__renamer.name())
        self.__editor.selectAll()

    def updateState(self, text):
        r"""
            フィールドの入力状態に応じてUIの状態を更新する。
            
            Args:
                text (str):
        """
        self.__rename_btn.setEnabled(True if text else False)

    def rename(self):
        r"""
            リネームを実行する。
        """
        new_name = self.__editor.text()
        if not new_name:
            return
        self.__renamer.rename(new_name)
        self.renameSucceeded.emit()


class SimpleRenamerWindow(uilib.SingletonWidget):
    r"""
        SimpleRenamerの単独ウィンドウを提供するクラス。
    """
    def buildUI(self):
        r"""
            UIの作成を行う。
        """
        self.__renamer = SimpleRenamer(self)
        self.setModal(True)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.__renamer)
        self.__renamer.renameSucceeded.connect(self.accept)
        self.__renamer.cancelButtonClicked.connect(self.reject)

    def show(self, nodeName):
        r"""
            再実装メソッド。内部的にはexec_を行っている。
            
            Args:
                nodeName (str):リネーム対象ノード名。
        """
        self.resize(250, 120)
        self.__renamer.setNode(nodeName)
        test = self.exec_()
        if not test:
            return


class DetailedBox(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(DetailedBox, self).__init__(parent)
        self.__field = QtWidgets.QLineEdit()
        pre_btn = QtWidgets.QPushButton('+')
        del_btn = QtWidgets.QPushButton('X')
        post_btn = QtWidgets.QPushButton('+')
        
        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(self.__field, 0, 0, 1, 3)
        layout.addWidget(pre_btn, 1, 0, 1, 1)
        layout.addWidget(del_btn, 1, 1, 1, 1)
        layout.addWidget(post_btn, 1, 2, 1, 1)
        layout.setColumnStretch(1, 1)


class DetailedRenamer(QtWidgets.QWidget):
    renameSucceeded = QtCore.Signal()
    cancelButtonClicked = QtCore.Signal()

    def __init__(self, parent=None):
        super(DetailedRenamer, self).__init__(parent)
        self.__renamer = SimpleRenamer(self)
        self.__field_layout = QtWidgets.QHBoxLayout()
        self.__editor = QtWidgets.QLineEdit()
        self.__editor.textEdited.connect(self.updateState)
        ccl_btn = QtWidgets.QPushButton('Canncel')
        self.__rename_btn = QtWidgets.QPushButton('Rename')
        
        layout = QtWidgets.QGridLayout(self)
        layout.addLayout(self.__field_layout, 0, 0, 1, 2)
        layout.addLayout(self.__editor, 1, 0, 1, 2)
        layout.addWidget(ccl_btn, 2, 0, 1, 1)
        layout.addWidget(self.__rename_btn, 2, 1, 1, 1)

    def setNode(self, nodeName):
        r"""
            リネーマーの初期化を行う
            
            Args:
                nodeName (str):リネーム対象ノード名。
        """
        self.__renamer.setNode(nodeName)
        # self.__editor.setText(self.__renamer.name())
        # self.__editor.selectAll()

    def updateState(self, text):
        r"""
            フィールドの入力状態に応じてUIの状態を更新する。
            
            Args:
                text (str):
        """
        detailed = DetailedBox()
        self.__field_layout.addWidget(detailed)
        self.__rename_btn.setEnabled(True if text else False)

    def rename(self):
        r"""
            リネームを実行する。
        """
        new_name = self.__editor.text()
        if not new_name:
            return
        self.__renamer.rename(new_name)
        self.renameSucceeded.emit()


        
class DetailedRenamerWindow(uilib.SingletonWidget):
    r"""
        SimpleRenamerの単独ウィンドウを提供するクラス。
    """
    def buildUI(self):
        r"""
            UIの作成を行う。
        """
        self.__renamer = DetailedRenamer(self)
        self.setModal(True)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.__renamer)
        self.__renamer.renameSucceeded.connect(self.accept)
        self.__renamer.cancelButtonClicked.connect(self.reject)

    def show(self, nodeName):
        r"""
            再実装メソッド。内部的にはexec_を行っている。
            
            Args:
                nodeName (str):リネーム対象ノード名。
        """
        self.__renamer.setNode(nodeName)
        test = self.exec_()
        if not test:
            return


class MultiRenamer(QtWidgets.QWidget):
    r"""
        複数ファイルのリネームを行うUIを提供するクラス
    """
    NumericalMask = '\-?[0-9]+'
    AlphabeticalMask = '[a-z]+|[A-Z]+'
    RenamedRegularExpression = '([^|]*$)'
    RenamedSubString = ''
    SubstringFieldFilter = '[\w\ ]+'
    CustomFileRegularExpression = nameUtility.NameFilterRegularExpression

    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(MultiRenamer, self).__init__(parent)
        self.setWindowTitle('+ Multi Renamer')
        self.__doubleRenaming = False
        self.__fixed_list = []
        self.__allow_resizing = True
        self.__manager = nameUtility.MultNameManager()
        self.__manager.setRenamedRegularExpression(
            self.RenamedRegularExpression
        )
        self.__manager.setRenamedSubstring(self.RenamedSubString)

        self.__column_resize_timerid = 0
        
        self.__adv_grp = self.advancedOptionGroup()
        self.__adv_grp.installEventFilter(self)
        
        # ベースネームを設定するオプションUI。=================================
        self.__basename_grp = self.createBaseGroup()
        self.__basename_grp.installEventFilter(self)
        # =====================================================================

        # 名前置換を設定するオプションUI。=====================================
        replace_grp = self.createReplaceGroup()
        replace_grp.installEventFilter(self)
        # =====================================================================

        # プレフィックス・サフィックス設定をするオプションUI。=================
        fix_grp = self.createPrefixSuffixGroup()
        fix_grp.installEventFilter(self)
        # =====================================================================

        # プレビュー用のUI。===================================================
        model = QtGui.QStandardItemModel(0, 2)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Before')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'After')

        self.__preview = QtWidgets.QTreeView()
        self.__preview.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers
        )
        self.__preview.installEventFilter(self)
        self.__preview.setRootIsDecorated(False)
        self.__preview.setAlternatingRowColors(True)
        self.__preview.setModel(model)
        self.__preview.setColumnWidth(0, 150)
        # =====================================================================

        # リネームボタン
        ren_btn = QtWidgets.QPushButton('Rename')
        ren_btn.clicked.connect(self.rename)
        
        # 選択ノードを登録するボタン。
        # add_btn = uilib.OButton()
        # add_btn.setToolTip(
            # 'Set selected nodes to the list.\n'
            # 'If press ctrl button when click here,\n'
            # 'then the selected nodes will be added into the list.'
        # )
        # add_btn.setSize(32)
        # add_btn.setIcon(uilib.IconPath('uiBtn_plus'))
        # add_btn.clicked.connect(self.addSelectedNodes)

        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(1)
        layout.addWidget(self.__adv_grp, 0, 0, 1, 2)
        layout.addWidget(self.__basename_grp, 1, 0, 1, 2)
        layout.addWidget(replace_grp, 2, 0, 1, 2)
        layout.addWidget(fix_grp, 3, 0, 1, 2)
        layout.addWidget(self.__preview, 4, 0, 1, 2)
        # layout.addWidget(add_btn, 5, 0, 1, 1)
        layout.addWidget(ren_btn, 5, 0, 1, 2)
    
    def advancedOptionGroup(self):
        r"""
            拡張オプションのGUIを作成し返す。
            
            Returns:
                QtWidgets.QGroupBox:作成されたGUIオブジェクト
        """
        group = QtWidgets.QGroupBox('Advanced Settings')
        group.setVisible(False)

        layout = QtWidgets.QFormLayout(group)

        label = QtWidgets.QLabel('Renamed Target')
        target_re = QtWidgets.QLineEdit(self.RenamedRegularExpression)
        target_re.textEdited.connect(
            self.__manager.setRenamedRegularExpression
        )
        target_re.textEdited.connect(self.updateList)
        target_re.installEventFilter(self)
        layout.addRow(label, target_re)

        label = QtWidgets.QLabel('Renamed Sub String')
        replaced_method = QtWidgets.QLineEdit(self.RenamedSubString)
        replaced_method.textEdited.connect(
            self.__manager.setRenamedSubstring
        )
        replaced_method.textEdited.connect(self.updateList)
        replaced_method.installEventFilter(self)
        layout.addRow(label, replaced_method)
        group.re_field = target_re
        return group

    def createBaseGroup(self):
        r"""
            ベース名設定のGUIを作成し返す。
            
            Returns:
                QtWidgets.QGroupBox:
        """
        group =  QtWidgets.QGroupBox('Basename Settings')
        group.setCheckable(True)
        group.setChecked(False)
        group.toggled.connect(self.__manager.useBaseName)
        group.toggled.connect(self.updateList)

        layout = QtWidgets.QFormLayout(group)

        # ベースネームを設定するためのフィールド。-----------------------------
        label = QtWidgets.QLabel('Basename')
        self.__basename = uilib.FilteredLineEdit('base')
        self.__basename.setFilter(self.CustomFileRegularExpression)
        self.__basename.installEventFilter(self)
        self.__manager.setBaseName(self.__basename.text())
        self.__basename.textEdited.connect(self.__manager.setBaseName)
        self.__basename.textEdited.connect(self.updateList)

        layout.addRow(label, self.__basename)
        # ---------------------------------------------------------------------

        # ナンバリングを数字ベースにするかアルファベットベースにするかを-------
        # 指定するUI。
        label = QtWidgets.QLabel('Numbering as')

        opt_widget = QtWidgets.QWidget()
        opt_layout = QtWidgets.QHBoxLayout(opt_widget)
        int_box = QtWidgets.QRadioButton('Integer')
        int_box.setChecked(True)
        alp_box = QtWidgets.QRadioButton('Alphabetical')
        opt_layout.addWidget(int_box)
        opt_layout.addSpacing(20)
        opt_layout.addWidget(alp_box)
        opt_layout.addStretch()
        
        self.__numbering_mode = QtWidgets.QButtonGroup(opt_widget)
        self.__numbering_mode.addButton(int_box, 0)
        self.__numbering_mode.addButton(alp_box, 1)
        self.__numbering_mode.buttonClicked.connect(self.changeNumberingMode)
        
        layout.addRow(label, opt_widget)
        # ---------------------------------------------------------------------
        
        # 開始番号を指定するためのUI。-----------------------------------------
        self.__startlabel = QtWidgets.QLabel('Start Number')
        self.__startnumber = uilib.FilteredLineEdit('0')
        self.__startnumber.installEventFilter(self)
        self.__startnumber.setFilter(self.NumericalMask)
        self.__startnumber.textEdited.connect(self.updateStartNumber)

        layout.addRow(self.__startlabel, self.__startnumber)
        # ---------------------------------------------------------------------

        # 桁数を指定するUI。---------------------------------------------------
        label = QtWidgets.QLabel('Padding')
        self.__padding_box = QtWidgets.QSpinBox()
        self.__padding_box.installEventFilter(self)
        self.__padding_box.setMinimum(1)
        self.__padding_box.setMaximum(1024)
        self.__padding_box.valueChanged.connect(self.__manager.setPadding)
        self.__padding_box.valueChanged.connect(self.updateList)

        layout.addRow(label, self.__padding_box)
        # ---------------------------------------------------------------------

        # 数字増減のステップを指定するUI---------------------------------------
        label = QtWidgets.QLabel('Step')
        self.__step_box = QtWidgets.QSpinBox()
        self.__step_box.installEventFilter(self)
        self.__step_box.setMinimum(1)
        self.__step_box.setMaximum(9999999)
        self.__step_box.valueChanged.connect(self.__manager.setStep)
        self.__step_box.valueChanged.connect(self.updateList)

        layout.addRow(label, self.__step_box)
        # ---------------------------------------------------------------------
        
        for widget in [self.__startnumber, self.__padding_box, self.__step_box]:
            widget.setMaximumSize(
                QtCore.QSize(100, widget.maximumSize().height())
            )
        return group

    def createReplaceGroup(self):
        r"""
            置換オプションのGUIを構築する。
            
            Returns:
                QtWidgets.QGroupBox:.
        """
        group = QtWidgets.QGroupBox('Search && Replace')
        layout = QtWidgets.QFormLayout(group)

        self.__use_re = QtWidgets.QCheckBox('Use Regular Expression')
        self.__use_re.setChecked(False)
        self.__use_re.toggled.connect(self.useRegularExpression)
        layout.addWidget(self.__use_re)

        label = QtWidgets.QLabel('&Search for')
        self.__searchtext = uilib.FilteredLineEdit()
        self.__searchtext.installEventFilter(self)
        self.__searchtext.setFilter(self.SubstringFieldFilter)
        self.__searchtext.textEdited.connect(self.updateSearchingText)
        label.setBuddy(self.__searchtext)
        layout.addRow(label, self.__searchtext)

        label = QtWidgets.QLabel('Replace with')
        self.__replacetext = uilib.FilteredLineEdit()
        self.__replacetext.setFilter(self.SubstringFieldFilter)
        self.__replacetext.installEventFilter(self)
        self.__replacetext.textEdited.connect(self.updateRepacingText)
        layout.addRow(label, self.__replacetext)

        return group

    def createPrefixSuffixGroup(self):
        r"""
            プレフィックス・サフィックス設定GUIを構築する。
            
            Returns:
                QtWidgets.QGroupBox:
        """
        group = QtWidgets.QGroupBox('Prefix / Suffix')
        layout = QtWidgets.QFormLayout(group)

        label = QtWidgets.QLabel('Prefix')
        self.__prefixtext = uilib.FilteredLineEdit()
        self.__prefixtext.setFilter(self.CustomFileRegularExpression)
        self.__prefixtext.installEventFilter(self)
        # self.__prefixtext.setFilter(customExpression)
        self.__prefixtext.textEdited.connect(self.__manager.setPrefix)
        self.__prefixtext.textEdited.connect(self.updateList)
        layout.addRow(label, self.__prefixtext)

        label = QtWidgets.QLabel('Suffix')
        self.__suffixtext = uilib.FilteredLineEdit()
        self.__suffixtext.setFilter(self.CustomFileRegularExpression)
        self.__suffixtext.installEventFilter(self)
        # self.__suffixtext.setFilter(customExpression)
        self.__suffixtext.textEdited.connect(self.__manager.setSuffix)
        self.__suffixtext.textEdited.connect(self.updateList)
        layout.addRow(label, self.__suffixtext)

        return group

    def useBaseNmae(self, checked):
        r"""
            ベースネームを仕様するかどうかを指定する
            
            Args:
                checked (bool):
        """
        self.__manager.useBaseName(checked)
        self.updateList()

    def refreshColumnWidth(self):
        r"""
            カラム幅を更新する
        """
        if not self.__allow_resizing:
            return
        self.__preview.setColumnWidth(
            0, self.__preview.rect().width() * 0.5
        )

    def changeNumberingMode(self, id):
        r"""
            連番設定を整数かアルファベットかに変更する
            
            Args:
                id (int):0の場合整数、1の場合アルファベットモード
        """
        self.__manager.setNumberingAs(id)
        if id == nameUtility.MultNameManager.Integer:
            label = 'Start Number'
            num = str(self.__manager.startNumber())
            mask = self.NumericalMask
        else:
            label = 'Start Character'
            num = self.__manager.startCharacter()
            mask = self.AlphabeticalMask

        self.__startlabel.setText(label)
        self.__startnumber.setText(num)
        self.__startnumber.setFilter(mask)

        self.updateList()

    def updateStartNumber(self, char):
        r"""
            開始番号を設定し更新する。
            
            Args:
                char (int):
        """
        if self.__numbering_mode.checkedId() == 0:
            self.__manager.setStartNumber(int(char))
        else:
            self.__manager.setStartCharacter(char)
        self.updateList()

    def useRegularExpression(self, state):
        r"""
            正規表現の使用/未使用の変更。
            
            Args:
                state (bool):
        """
        self.__manager.useRegularExpression(state)
        custom_re = '.*' if state else self.SubstringFieldFilter
        self.__searchtext.setFilter(custom_re)
        self.__replacetext.setFilter(custom_re)
        self.updateList()

    def updateSearchingText(self, text):
        self.__manager.setSearchingText(text)
        self.updateList()

    def updateRepacingText(self, text):
        self.__manager.setReplacingText(text)
        self.updateList()

    def updateList(self):
        r"""
            リストを更新する。
        """
        model = self.__preview.model()
        items = [model.item(x, 1) for x in range(model.rowCount())]
        result = self.__manager.renamedList()
        if len(items) != len(result):
            return

        for item, r in zip(items, result):
            item.setText(r)

    def addSelectedNodes(self):
        r"""
            選択されているノードをリストにセット、または追加する。
        """
        selected = nameUtility.selectedNodes()
        mod = QtWidgets.QApplication.keyboardModifiers()
        self.setNodeList(selected, mod == QtCore.Qt.ControlModifier)

    def setNodeList(self, nodelist, add=False):
        r"""
            ノードのリストをビューにセットまたは追加する
            
            Args:
                nodelist (list):
                add (bool):
        """
        model = self.__preview.model()
        if not add:
            model.removeRows(0, model.rowCount())
            namelist = []
        else:
            namelist = self.__manager.nameList()
            
        for nodename in nodelist:
            if nodename in namelist:
                continue
            row = model.rowCount()
            for i in range(2):
                item = QtGui.QStandardItem(nodename)
                model.setItem(row, i, item)
            namelist.append(nodename)

        self.__preview.setColumnWidth(0, 190)
        self.__manager.setNameList(namelist)
        self.updateList()
        self.__fixed_list = []

    def eventFilter(self, object, event):
        r"""
            Args:
                object (QtWidgets.QObject):
                event (QtCore.QEvent):
        """
        event_type = event.type()
        if isinstance(object, QtWidgets.QGroupBox):
            if event_type == QtCore.QEvent.MouseButtonPress:
                self.mousePressEvent(event)
                return False
            elif event_type == QtCore.QEvent.MouseMove:
                self.mouseMoveEvent(event)
                return False
            elif event_type == QtCore.QEvent.MouseButtonRelease:
                self.mouseReleaseEvent(event)
                return False

        if event_type != QtCore.QEvent.KeyPress:
            return False
        mod = event.modifiers()
        key = event.key()

        if mod != QtCore.Qt.AltModifier:
            if key in (QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter):
                self.rename()
                return True
            return False

        if key == QtCore.Qt.Key_1:
            self.__basename_grp.setChecked(
                self.__basename_grp.isChecked()==False
            )
        elif key == QtCore.Qt.Key_2:
            self.__basename.setFocus(QtCore.Qt.MouseFocusReason)
            self.__basename.selectAll()
        elif key == QtCore.Qt.Key_3:
            id = 1 if self.__numbering_mode.checkedId() == 0 else 0
            button = self.__numbering_mode.button(id)
            button.setChecked(True)
            self.changeNumberingMode(id)
        elif key == QtCore.Qt.Key_Q:
            self.__startnumber.setFocus(QtCore.Qt.MouseFocusReason)
            self.__startnumber.selectAll()
        elif key == QtCore.Qt.Key_W:
            self.__padding_box.setFocus(QtCore.Qt.MouseFocusReason)
            self.__padding_box.selectAll()
        elif key == QtCore.Qt.Key_E:
            self.__step_box.setFocus(QtCore.Qt.MouseFocusReason)
            self.__step_box.selectAll()

        elif key == QtCore.Qt.Key_A:
            self.__use_re.setChecked(self.__use_re.isChecked()==False)
        elif key == QtCore.Qt.Key_S:
            self.__searchtext.setFocus(QtCore.Qt.MouseFocusReason)
            self.__searchtext.selectAll()
        elif key == QtCore.Qt.Key_D:
            self.__replacetext.setFocus(QtCore.Qt.MouseFocusReason)
            self.__replacetext.selectAll()

        elif key == QtCore.Qt.Key_Z:
            self.__prefixtext.setFocus(QtCore.Qt.MouseFocusReason)
            self.__prefixtext.selectAll()
        elif key == QtCore.Qt.Key_X:
            self.__suffixtext.setFocus(QtCore.Qt.MouseFocusReason)
            self.__suffixtext.selectAll()

        elif key == QtCore.Qt.Key_C:
            state = self.__adv_grp.isVisible()==False
            self.__adv_grp.setVisible(state)
            if state:
                self.__adv_grp.re_field.setFocus(QtCore.Qt.MouseFocusReason)
                self.__adv_grp.re_field.selectAll()
            else:
                self.__searchtext.setFocus(QtCore.Qt.MouseFocusReason)
        else:
            return False
        return True

    def rename(self):
        r"""
            リネームを実行する
        """
        src_list = self.__manager.nameList()
        newname_list = self.__manager.result()
        if len(src_list) != len(newname_list):
            return
        from gris3 import node
        with node.DoCommand():    
            newnames = nameUtility.multRename(src_list, newname_list)
        self.setNodeList(newnames)


class MultiRenamerWindow(uilib.AbstractSeparatedWindow):
    r"""
        MultiRenamerの単独ウィンドウを提供するクラス。
    """
    def centralWidget(self):
        r"""
            UIの作成を行い、そのオブジェクトを返す。
            
            Returns:
                MultiRenamer:
        """
        self.__jobid = None
        return MultiRenamer(self)

    def show(self, nodelist):
        r"""
            Args:
                nodelist (list):
        """
        if self.__jobid is None:
            self.__jobid = mayaUIlib.createEventJob(
                self.main().addSelectedNodes
            )
        self.resize(380, 800)
        main = self.main()
        main.setNodeList(nodelist)
        super(MultiRenamerWindow, self).show()

    def closeEvent(self, event):
        r"""
            ウィンドウを閉じる際にスクリプトジョブを削除する。
            
            Args:
                event (QtCore.QEvent):
        """
        if self.__jobid is not None:
            mayaUIlib.killJob(self.__jobid)
            self.__jobid = None


class PasteNameOption(uilib.SingletonWidget):
    def buildUI(self):
        r"""
            UIの作成を行う。
        """
        # タイトルバー。=======================================================
        label = QtWidgets.QLabel('Paste name option')
        label.setStyleSheet('QLabel{font-size:20px;}')
        
        pixmap = QtGui.QPixmap(uilib.IconPath('uiBtn_rename'))
        pixmap = pixmap.scaled(
            QtCore.QSize(32, 32),
            QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation
        )
        icon = QtWidgets.QLabel()
        icon.setPixmap(pixmap)

        title_layout = QtWidgets.QHBoxLayout()
        title_layout.addWidget(icon)
        title_layout.addWidget(label)
        title_layout.addStretch()
        # =====================================================================

        self.__namespace_act = QtWidgets.QButtonGroup()
        # ネームスペースに対する処理
        ns_grp = QtWidgets.QGroupBox('Namespace')
        no_btn = QtWidgets.QRadioButton('Nothing')
        rem_btn = QtWidgets.QRadioButton('Remove')
        rem_btn.setChecked(True)
        pfx_btn = QtWidgets.QRadioButton('Replace as prefix')
        layout = QtWidgets.QHBoxLayout(ns_grp)
        for i, btn in enumerate((no_btn,  rem_btn, pfx_btn)):
            self.__namespace_act.addButton(btn, i)
            layout.addWidget(btn)
        
        # 文字列置換
        rep_grp = QtWidgets.QGroupBox('Replacing')
        self.__srch = QtWidgets.QLineEdit()
        self.__rep = QtWidgets.QLineEdit()
        layout = QtWidgets.QFormLayout(rep_grp)
        layout.addRow('Search string', self.__srch)
        layout.addRow('Replace string', self.__rep)
        
        # 実行ボタン
        btn_layout = QtWidgets.QHBoxLayout()
        for l, f in (('Paste', self.paste), ('Cancel', self.close)):
            btn =  QtWidgets.QPushButton(l)
            btn.clicked.connect(f)
            btn_layout.addWidget(btn)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(title_layout)
        layout.addWidget(ns_grp)
        layout.addWidget(rep_grp)
        layout.addStretch()
        layout.addLayout(btn_layout)

    def paste(self):
        namespace = self.__namespace_act.checkedId()
        search = self.__srch.text()
        rep = self.__rep.text()
        with node.DoCommand():
            nameUtility.pasteName(
                namespaceAs=namespace, searchStr=search, replaceStr=rep
            )


class StandardAutoRename(QtWidgets.QWidget):
    def __init__(self, parent=None):
        def createWidgetByType(value):
            if isinstance(val, int):
                w = QtWidgets.QSpinBox()
                w.setRange(0, 8)
                w.setMinimumWidth(100)
                w.setButtonSymbols(QtWidgets.QSpinBox.NoButtons)
            elif isinstance(val, (list, tuple)):
                w = QtWidgets.QComboBox()
                w.addItems(val)
                w.value = w.currentText
            else:
                w = QtWidgets.QLineEdit()
                w.setText(val)
                w.value = w.text
            return w

        super(StandardAutoRename, self).__init__(parent)
        self.setWindowTitle('+ Standard Auto Renamer for joint')
        opt_grp = QtWidgets.QGroupBox('Options')
        opt_layout = QtWidgets.QFormLayout(opt_grp)
        self.__options = {}
        for key, val in (
            ('baseName', 'baseJoint'),
            ('startChar', 'A'),
            ('padding', 0),
            ('objectType', 'jnt'),
            ('side', ['L', 'R', 'C', 'None']),
        ):
            w = createWidgetByType(val)
            self.__options[key] = w
            opt_layout.addRow(lib.title(key), w)

        adv_opt = uilib.ClosableGroup('AdvancedOption')
        adv_layout = QtWidgets.QFormLayout(adv_opt)
        self.__adv_options = {}
        for key, val in (
            ('suffixFormat', '_{objType}_{position}'),
        ):
            w = createWidgetByType(val)
            self.__adv_options[key] = w
            adv_layout.addRow(lib.title(key), w)
        adv_opt.setExpanding(False)

        ren_btn = QtWidgets.QPushButton('Rename selected')
        ren_btn.clicked.connect(self.rename)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(opt_grp)
        layout.addWidget(adv_opt)
        layout.addStretch()
        layout.addWidget(ren_btn)

    def rename(self):
        ar = nameUtility.AutoRenamer()
        for key, w in self.__options.items():
            f = getattr(ar, 'set' + key[0].upper() + key[1:])
            f(w.value())
        print('--> %s' % ar.padding())
        ar.SuffixFormat = self.__adv_options['suffixFormat'].text()
        with node.DoCommand():
            ar.rename()


class StandardAutoRenameWindow(uilib.AbstractSeparatedWindow):
    def centralWidget(self):
        r"""
            UIの作成を行い、そのオブジェクトを返す。
            
            Returns:
                StandardAutoRename:
        """
        return StandardAutoRename(self)


def showAutoRenameWindow():
    renamer = StandardAutoRenameWindow(mayaUIlib.MainWindow)
    renamer.show()
    return renamer


def showWindow():
    r"""
        選択ノードの数に応じて最適なリネーマーを表示する
    """
    selected = nameUtility.selectedNodes()
    if len(selected) == 1:
        renamer = SimpleRenamerWindow(mayaUIlib.MainWindow)
        renamer.show(selected[0])
    else:
        renamer = MultiRenamerWindow(mayaUIlib.MainWindow)
        renamer.show(selected)


def showPasteNameOption():
    w = PasteNameOption(mayaUIlib.MainWindow)
    w.show()