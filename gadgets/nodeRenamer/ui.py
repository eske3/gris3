#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    任意の命名規則に則ったリネームを行うためのGUIを提供するモジュール

    Dates:
        date:2025/05/11 01:47 Eske Yoshinob[eske3g@gmail.com]
        update:2025/05/11 03:15 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2025 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from . import renamerEngine 
from ... import uilib, node, lib
from ...uilib import mayaUIlib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

from importlib import reload
reload(renamerEngine)

class NameEditor(QtWidgets.QScrollArea):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(NameEditor, self).__init__(parent)
        self.setWidgetResizable(True)
        # self.setEngine(renamerEngine.BasicProductionEngine())

    def setEngine(self, renamerEngine):
        r"""
            Args:
                renamerEngine (renamerEngine.AbstractRenamerEngine):
        """
        widget = self.widget()
        if widget:
            widget.deleteLater()
        self.setWidget(renamerEngine)

    def engine(self):
        r"""
            Returns:
                renamerEngine.AbstractRenamerEngine:
        """
        return self.widget()
    
    def setName(self, nodeName, fullPathName):
        r"""
            操作対象となるノードの名前を設定する。
            設定すると、登録されているエンジンにその名前を渡し、UIの更新を行う。
            
            Args:
                nodeName (str):
                fullPathName (str):
        """
        self.engine().analyzeName(nodeName, fullPathName)

    def makeName(self):
        return self.engine().makeName()

    def setFocusToBlock(self, index):
        self.engine().setFocusToBlock(index)


class NodeRenamer(QtWidgets.QWidget):
    closeButtonClicked = QtCore.Signal()

    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(NodeRenamer, self).__init__(parent)
        self.setWindowTitle('+ Node Renamer')
        
        tgt_label = QtWidgets.QLabel('Rename for')
        self.__target_node = QtWidgets.QLineEdit()
        self.__target_node.setReadOnly(True)

        self.__editor = NameEditor()

        rem_btn = QtWidgets.QPushButton('Rename')
        rem_btn.clicked.connect(self.rename)
        cancel_btn = QtWidgets.QPushButton('Cancel')
        cancel_btn.clicked.connect(self._emit_closing)

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(tgt_label, 0, 0, 1, 1, QtCore.Qt.AlignRight)
        layout.addWidget(self.__target_node, 0, 1, 1, 3)
        layout.addWidget(self.__editor, 1, 0, 1, 4)
        layout.addWidget(rem_btn, 2, 0, 1, 2)
        layout.addWidget(cancel_btn, 2, 2, 1, 2)

    def editor(self):
        return self.__editor

    def setEngine(self, engine):
        self.editor().setEngine(engine)

    def _emit_closing(self):
        self.closeButtonClicked.emit()

    def setTargetNode(self, nodeName=''):
        r"""
            リネーム操作対象のノード名を設定する。
            
            Args:
                nodeName (str):
        """
        self.__target_node.setText(nodeName)
        self.editor().setName(*self.targetNode())
    
    def targetNode(self):
        r"""
            設定されたリネーム操作対象のノード名を返す。
            戻り値は操作対象の純粋なノード名と
            フルパス名（シーン中に名前重複がある場合）のタプル。
            
            Returns:
                tuple(str, str):
        """
        name = self.__target_node.text()
        full_name = name
        if '|' in name:
            name = full_name.rsplit('|', 1)[-1]
        return name, full_name

    def rename(self):
        target = self.__target_node.text()
        new_name = self.editor().makeName()
        tgt_obj = node.asObject(target)
        if tgt_obj:
            tgt_obj.rename(new_name)
        self._emit_closing()
    
    def setFocusToEditor(self, index=0):
        self.editor().setFocusToBlock(index)

    def keyPressEvent(self, event):
        key = event.key()
        mod = event.modifiers()
        if key in (QtCore.Qt.Key_Enter , QtCore.Qt.Key_Return):
            self.rename()
            return
        elif key == QtCore.Qt.Key_Escape:
            self._emit_closing()
            return
        if mod != QtCore.Qt.ControlModifier:
            return
        nums = [getattr(QtCore.Qt, 'Key_{}'.format(x)) for x in range(1, 10)]
        if key in nums:
            index = nums.index(key)
            self.setFocusToEditor(index)
            return
        super(NodeRenamer, self).keyPressEvent(event)


class NodeRenamerWindow(uilib.AbstractSeparatedWindow):
    def centralWidget(self):
        r"""
            UIの作成を行い、そのオブジェクトを返す。
            
            Returns:
                NodeRenamer:
        """
        obj = NodeRenamer(self)
        obj.closeButtonClicked.connect(self.close)
        return obj

    def setSelectedNode(self):
        from ...tools import nameUtility
        selected = nameUtility.selectedNodes()
        main = self.main()
        if len(selected):
            main.setTargetNode(selected[0])
        else:
            main.setTargetNode()

    def setEngine(self, engine=None):
        if not engine:
            engine = renamerEngine.BasicProductionEngine()
        self.main().setEngine(engine)


def showWindow(engine=None):
    r"""
        リネーマーを表示する
        
        Returns:
            NodeRenamerWindow:
    """
    renamer = NodeRenamerWindow(mayaUIlib.MainWindow)
    renamer.setEngine(engine)
    renamer.setSelectedNode()
    renamer.resize(uilib.hires(500), uilib.hires(180))
    renamer.show()
    renamer.main().setFocusToEditor()
    return renamer