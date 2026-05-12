#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2025/12/21 11:47 Eske Yoshinob[eske3g@gmail.com]
        update:2025/12/21 17:12 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2025 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""


from ..tools import scriptHolder
from .. import uilib, node
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class Editor(QtWidgets.QWidget):
    CreateMode, EditMode = range(2)
    saveButtonClicked = QtCore.Signal(int, str, str)

    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):
        """
        super(Editor, self).__init__(parent)
        self.__mode = self.CreateMode
        self.__title = QtWidgets.QLabel()
        label = QtWidgets.QLabel('Script Name')
        self.__label = QtWidgets.QLineEdit()
        label_widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(label_widget)
        layout.addWidget(label)
        layout.addWidget(self.__label)

        self.__textedit = QtWidgets.QTextEdit()
        
        test_label = QtWidgets.QLabel('Test Script')
        test_btn = uilib.OButton(uilib.IconPath('uiBtn_play'))
        test_btn.setBgColor(*uilib.Color.DebugColor)
        test_btn.clicked.connect(self.testScript)
        
        self.__save_btn = uilib.OButton(uilib.IconPath('uiBtn_save'))
        self.__save_btn.setSize(32)
        self.__save_btn.setBgColor(*uilib.Color.ExecColor)
        self.__save_btn.clicked.connect(self.save)
        
        ccl_btn = uilib.OButton(uilib.IconPath('uiBtn_x'))
        self.cancelButtonClicked = ccl_btn.clicked

        layout = QtWidgets.QGridLayout(self)
        layout.setColumnStretch(1, 1)
        layout.addWidget(self.__title, 0, 0, 1, 4)
        layout.addWidget(label_widget, 1, 0, 1, 4)
        layout.addWidget(self.__textedit, 2, 0, 1, 4)
        layout.addWidget(test_label, 3, 0, 1, 1)
        layout.addWidget(test_btn, 3, 1, 1, 1, QtCore.Qt.AlignLeft)
        layout.addWidget(self.__save_btn, 3, 2, 1, 1)
        layout.addWidget(ccl_btn, 3, 3, 1, 1)

    def setMode(self, mode, label='', text=''):
        r"""
            Args:
                mode (int):
                label (str):
                text (str):
        """
        self.__mode = mode
        if mode == self.CreateMode:
            title = 'Create New Script'
            icon = 'uiBtn_plus'
        else:
            title = 'Edit Script'
            icon = 'uiBtn_save'
        self.__title.setText('<font size=4><b>{}</b></font>'.format(title))
        self.__save_btn.setIcon(uilib.IconPath(icon))
        self.__label.setText(label)
        self.__textedit.setPlainText(text)

    def save(self):
        label = self.__label.text()
        script_text = self.__textedit.toPlainText()
        if not label or not script_text:
            return
        self.saveButtonClicked.emit(self.__mode, label, script_text)

    def testScript(self):
        script_text = self.__textedit.toPlainText()
        scriptHolder.execScript(script_text)


class ScriptWidget(QtWidgets.QWidget):
    editButtonClicked = QtCore.Signal(QtWidgets.QWidget)

    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):
        """
        super(ScriptWidget, self).__init__(parent)
        self.__btn = QtWidgets.QPushButton('')
        self.__btn.clicked.connect(self.exec_script)
        self.__script = None
        edit_btn = uilib.OButton(uilib.IconPath('uiBtn_edit'))
        edit_btn.setBgColor(*uilib.Color.ExecColor)
        edit_btn.clicked.connect(self._emit_editting)
        del_btn = uilib.OButton(uilib.IconPath('uiBtn_trush'))
        del_btn.clicked.connect(self.remove)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(uilib.ZeroMargins)
        layout.addWidget(self.__btn)
        layout.addWidget(edit_btn)
        layout.addWidget(del_btn)

    def setScript(self, script):
        r"""
            Args:
                script (scriptHolder.Script):
        """
        self.__script = script
        self.__btn.setText(script.name())

    def script(self):
        r"""
            Returns:
                scriptHolder.Script:
        """
        return self.__script

    def _emit_editting(self):
        self.editButtonClicked.emit(self)

    def remove(self):
        self.deleteLater()

    def exec_script(self):
        script = self.script()
        if not script:
            return
        script.execute()
        # script_text = script.scriptText()
        # with node.DoCommand():
            # exec(script_text)
        

class ScriptList(QtWidgets.QWidget):
    editButtonClicked = QtCore.Signal(QtWidgets.QWidget)

    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):
        """
        super(ScriptList, self).__init__(parent)
        add_label = QtWidgets.QLabel('Add Script')
        
        add_btn = uilib.OButton(uilib.IconPath('uiBtn_plus'))
        self.addButtonClicked = add_btn.clicked
        
        scroller = QtWidgets.QScrollArea()
        scroller.setWidgetResizable(True)
        w = QtWidgets.QWidget()
        w.setObjectName('ScriptExecutorList')
        w.setStyleSheet(
            'QWidget#ScriptExecutorList{'
            'background-color : transparent;'
            '}'
        )
        self.__layout = QtWidgets.QVBoxLayout(w)
        self.__layout.setSpacing(1)
        scroller.setWidget(w)
        
        layout = QtWidgets.QGridLayout(self)
        layout.setColumnStretch(0, 1)
        layout.addWidget(add_label, 0, 0, 1, 1, QtCore.Qt.AlignRight)
        layout.addWidget(add_btn, 0, 1, 1, 1, QtCore.Qt.AlignRight)
        layout.addWidget(scroller, 1, 0, 1, 2)

    def listScripts(self):
        scripts = []
        for i in range(self.__layout.count()):
            item = self.__layout.itemAt(i)
            widget = item.widget()
            if not widget:
                continue
            if not getattr(widget, 'script'):
                continue
            scripts.append(widget.script())
        return scripts

    def addScriptWidget(self, script):
        r"""
            Args:
                script (scriptHolder.Script):
        """
        w = ScriptWidget()
        w.setScript(script)
        w.editButtonClicked.connect(self._emit_widget_editting)
        self.__layout.insertWidget(self.__layout.count() - 1, w)        

    def reload(self):
        m = scriptHolder.ScriptHolderManager()
        scripts = m.listScripts()
        uilib.clearLayout(self.__layout)
        self.__layout.addStretch()
        for script in scripts:
            self.addScriptWidget(script)

    def addScript(self, label, scriptText):
        r"""
            Args:
                label (str):
                scriptText (str):
        """
        m = scriptHolder.ScriptHolderManager()
        script = m.addScript(label, scriptText)
        self.addScriptWidget(script)

    def saveScripts(self):
        scripts = self.listScripts()
        scriptHolder.ScriptHolderManager().saveScripts(scripts)

    def _emit_widget_editting(self, scriptWidget):
        r"""
            Args:
                scriptWidget (ScriptWidget):
        """
        self.editButtonClicked.emit(scriptWidget)


class ScriptExecutor(uilib.ScrolledStackedWidget):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):
        """
        super(ScriptExecutor, self).__init__(parent)
        self.setWindowTitle('Script Executor')
        self.__edited = None
        self.__scriptlist = ScriptList()
        self.__editor = Editor()
        self.addTab(self.__scriptlist)
        self.addTab(self.__editor)
        
        self.__scriptlist.addButtonClicked.connect(self.setCreateMode)
        self.__scriptlist.editButtonClicked.connect(self.setEditMode)
        self.__editor.saveButtonClicked.connect(self.saveScript)
        self.__editor.cancelButtonClicked.connect(self.cancelEditting)

    def editor(self):
        return self.__editor

    def scriptList(self):
        return self.__scriptlist
    
    def setCreateMode(self):
        self.editor().setMode(Editor.CreateMode)
        self.moveTo(1)

    def setEditMode(self, scriptWidget):
        r"""
            Args:
                scriptWidget (ScriptWidget):
        """
        self.__edited = scriptWidget
        script = scriptWidget.script()
        self.editor().setMode(
            Editor.EditMode, script.name(), script.scriptText()
        )
        self.moveTo(1)

    def cancelEditting(self):
        self.moveTo(0)

    def saveScript(self, mode, label, scriptText):
        r"""
            Args:
                mode (int):
                label (str):
                scriptText (str):
        """
        if mode == Editor.CreateMode:
            self.scriptList().addScript(label, scriptText)
        else:
            if self.__edited:
                script = self.__edited.script()
                script.setName(label)
                script.setScriptText(scriptText)
                self.__edited.setScript(script)
                self.__edited = None
        self.moveTo(0)

    def reloadList(self):
        self.scriptList().reload()

    def hideEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        self.scriptList().saveScripts()

    def closeEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        self.scriptList().saveScripts()


class MainGUI(uilib.AbstractSeparatedWindow):
    def centralWidget(self):
        r"""
            Returns:
                ScriptExecutor:
        """
        return ScriptExecutor()


def showWindow():
    r"""
        Returns:
            MainGUI:
    """
    from ..uilib import mayaUIlib
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(450, 450)
    widget.main().reloadList()
    widget.show()
    return widget