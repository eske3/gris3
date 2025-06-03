#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ここに説明文を記入
    
    Dates:
        date:2017/07/06 5:35[Eske](eske3g@gmail.com)
        update:2025/05/27 14:24 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from ..tools import facialMemoryManager
from ..uilib import mayaUIlib
from .. import uilib, node, style
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class ManagerEngine(object):
    r"""
        表情管理ノードに関する制御を行う機能を提供するクラス。
        このクラスは表情管理ノードの取得や作成を管理するため、このクラスを
        継承したサブクラスをFacialExpressionManagerにわたすことにより、表情
        管理ノードを独自の仕様で管理できる。
    """
    def __init__(self, blendShapeName=''):
        r"""
            Args:
                blendShapeName (str):
        """
        self.__blend_shape_name = blendShapeName

    def blendShapeName(self):
        return self.__blend_shape_name
    
    def setBlendShapeName(self, blendShapeName):
        r"""
            Args:
                blendShapeName (str):
        """
        self.__blend_shape_name = blendShapeName

    def createManagerNode(self):
        r"""
            getManagerNode内で呼ばれる、管理ノード作成関数。
            必要に応じて継承したクラスでこのメソッドを上書きすることにより
            カスタマイズされたマネージャーノードを作成することが可能。
        """
        with node.DoCommand():
            root = facialMemoryManager.createManagerNode()
            root.setBlendShapeName(self.blendShapeName())
        return root

    def getManagerNode(self, autoCreation=True):
        r"""
            管理ノードを返す。
            autoCreationがTrueの場合で、管理ノードgあみつからない場合、自動で
            作成する。
            
            Args:
                autoCreation (bool): 
                
            Returns:
                tools.facialMemoryManager.FacialMemoryManagerRoot
        """
        if not self.blendShapeName():
            raise RuntimeError(
                'No blend shape name was specified. '
                'Use setBlendShapeName method and set the blend shape name '
                'before use this method.'
            )
        root = facialMemoryManager.listManagerNode()
        if root:
            return root[0]
        if not autoCreation:
            return
        return self.createManagerNode()


class Settings(QtWidgets.QGroupBox):
    reloadButtonClicked = QtCore.Signal(str)
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(Settings, self).__init__('Settings', parent)

        edit_btn = uilib.OButton(uilib.IconPath('uiBtn_edit'))
        edit_btn.setToolTip('Edit expression list.')
        self.editButtonClicked = edit_btn.clicked

        bs_label = QtWidgets.QLabel('Blend Shape')
        self.__bs = QtWidgets.QLineEdit()
        rel_btn = uilib.OButton(uilib.IconPath('uiBtn_reset'))
        rel_btn.clicked.connect(self._emit_reloading)

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(edit_btn, 0, 2, 1, 1)
        layout.addWidget(bs_label, 1, 0, 1, 1)
        layout.addWidget(self.__bs, 1, 1, 1, 1)
        layout.addWidget(rel_btn, 1, 2, 1, 1)

    def setBlendShape(self, blendShapeName):
        r"""
            Args:
                blendShapeName (str):
        """
        self.__bs.setText(blendShapeName)
    
    def blendShape(self):
        return self.__bs.text()
        
    def _emit_reloading(self):
        self.reloadButtonClicked.emit(self.blendShape())


class VirtualSliderButton(QtWidgets.QPushButton):
    facialChanged = QtCore.Signal(str)

    def __init__(self, manager, expressionName, parent=None):
        r"""
            Args:
                manager (facialMemoryManager.FacialMemoryManagerRoot):
                expressionName (str):表情名
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(VirtualSliderButton, self).__init__(expressionName, parent)
        self.clicked.connect(self.__changeExpression)
        self.__manager = manager
        self.__expression = expressionName
        self.__start_pos = None
        self.__slider_width = None
        self.__param_range = []
        self.__current_ratio = -1
        self.slider_gradient = QtGui.QLinearGradient()
        color = QtGui.QColor(*uilib.Color.ExecColor)
        self.slider_gradient.setColorAt(0, color)
        self.slider_gradient.setColorAt(1, color.lighter())

    def expression(self):
        return self.__expression

    def manager(self):
        r"""
            Returns:
                facialMemoryManager.FacialMemoryManagerRoot:
        """
        return self.__manager

    def applyValueFromCurrent(self):
        with node.DoCommand():
            self.manager().setExpressionFromCurrentState(self.expression())

    def __changeExpression(self):
        with node.DoCommand():
            self.manager().applyExpression(self.expression())
        self.facialChanged.emit(self.expression())

    def setup(self):
        manager = self.manager()
        values = manager.listExpressionData().get(self.expression())
        bs = manager.blendShape()
        if not values:
            self.__param_range = {'blendShape': bs, 'values':{}}
            return
        from collections import OrderedDict
        all_values = OrderedDict()
        for attr in bs.listAttrNames():
            all_values[attr] = 0
        all_values.update(values)

        value_range = {
            attr: (bs(attr), val) for attr, val in all_values.items()
        }
        self.__param_range = {
            'blendShape': bs,
            'values': {
                attr: (val[0], val[1] - val[0])
                for attr, val in value_range.items() if val[0] != val[1]
            }
        }

    def changeValue(self, ratio):
        r"""
            Args:
                ratio (float):
        """
        if not self.__param_range:
            return
        bs = self.__param_range['blendShape']
        if ratio < 0:
            ratio = 0
        elif ratio > 1:
            ratio = 1
        for attr, val in self.__param_range['values'].items():
            v = val[1] * ratio + val[0]
            bs(attr, v)

    def restoreDefault(self):
        if self.__param_range:
            bs = self.__param_range['blendShape']
            for attr, val in self.__param_range['values'].items():
                bs(attr, val[0])
        self.__slider_width = None
        self.__start_pos = None
        self.__param_range = []

    def mousePressEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        if event.button() != QtCore.Qt.MidButton:
            super(VirtualSliderButton, self).mousePressEvent(event)
            return
        self.__start_pos = event.pos()

    def mouseMoveEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        if not self.__start_pos:
            super(VirtualSliderButton, self).mouseMoveEvent(event)
            return
        pos = event.pos()
        if not self.__slider_width:
            if (
                (self.__start_pos - pos).manhattanLength() <
                QtWidgets.QApplication.startDragDistance()
            ):
                return
            self.__slider_width = self.geometry().width()
            QtWidgets.QApplication.setOverrideCursor(
                QtGui.QCursor(QtCore.Qt.SizeHorCursor)
            )
            self.setup()
            facialMemoryManager.cmds.undoInfo(openChunk=True)
        val = pos.x() - self.__start_pos.x()
        if val < 0:
            return
        f = 1
        mod = event.modifiers()
        if mod == QtCore.Qt.ControlModifier:
            f = 0.5
        r = self.__slider_width * f
        ratio = val / r
        self.__current_ratio = 1.0 if ratio > 1.0 else ratio
        try:
            self.changeValue(ratio)
        except Exception as e:
            print('Warning : {}'.foramt(e.args))
        self.update()

    def mouseReleaseEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        self.__current_ratio = -1.0
        if not self.__start_pos:
            super(VirtualSliderButton, self).mouseReleaseEvent(event)
            return
        facialMemoryManager.cmds.undoInfo(closeChunk=True)
        QtWidgets.QApplication.restoreOverrideCursor()
        self.restoreDefault()

    def paintEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        offset = 8
        if self.__current_ratio < 0:
            super(VirtualSliderButton, self).paintEvent(event)
            return
        rect = event.rect()
        pen = QtGui.QPen(QtGui.QColor(210, 210, 210), 2)
        painter = QtGui.QPainter(self)
        painter.setRenderHints(QtGui.QPainter.Antialiasing)
        painter.setPen(pen)
        painter.setBrush(QtGui.QBrush(QtGui.QColor(64, 64, 64)))
        painter.drawRoundedRect(rect, offset, offset)

        oh = rect.height()
        top_left =  rect.topLeft()
        rect.setHeight(oh - offset)
        pos_offset = QtCore.QPoint(offset * 0.5, offset * 0.5)
        rect.setWidth((rect.width() - offset) * self.__current_ratio)
        rect.moveTopLeft(top_left + pos_offset)
        self.slider_gradient.setStart(rect.topLeft())
        self.slider_gradient.setFinalStop(rect.topRight())
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(self.slider_gradient)
        painter.drawRect(rect)

        painter.setPen(pen)
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawText(event.rect(), QtCore.Qt.AlignCenter, self.text())


class ExpressionButton(QtWidgets.QWidget):
    r"""
        表情を登録、操作するためのGUIを提供するクラス。
    """
    def __init__(self, root, exp, parent=None):
        r"""
            Args:
                root (facialMemoryManager.FacialMemoryManagerRoot):
                exp (str):表情名
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ExpressionButton, self).__init__(parent)
        self.__v_btn = VirtualSliderButton(root, exp)
        self.__st_btn = uilib.OButton(uilib.IconPath('uiBtn_save'))
        self.__st_btn.clicked.connect(self.storeValue)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(uilib.ZeroMargins)
        layout.setSpacing(1)
        layout.addWidget(self.__v_btn)
        layout.addWidget(self.__st_btn)

        self.refreshState()

    def refreshState(self, useCache=True):
        data = self.__v_btn.manager().listExpressionData(useCache=useCache)
        val = data.get(self.__v_btn.expression())
        color = [] if val is None else [16, 64, 140]
        self.__st_btn.setBgColor(*color)

    def storeValue(self):
        self.__v_btn.applyValueFromCurrent()
        self.refreshState(False)


class FacialExpressionView(QtWidgets.QScrollArea):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(FacialExpressionView, self).__init__(parent)
        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(w)
        self.setWidgetResizable(True)
        self.setWidget(w)

    def clear(self):
        layout = self.widget().layout()
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.isEmpty():
                layout.removeItem(item)
                continue
            widget = item.widget()
            if widget:
                widget.deleteLater()
        return layout

    def reload(self, managerEngine):
        r"""
            Args:
                managerEngine (ManagerEngine):
        """
        layout = self.clear()
        root = managerEngine.getManagerNode()
        for exp in root.listExpressions():
            btn = ExpressionButton(root, exp)
            layout.addWidget(btn)
        layout.addStretch()


class ExpressionEditor(QtWidgets.QWidget):
    editingFinished = QtCore.Signal(int, list)

    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ExpressionEditor, self).__init__(parent)
        self.__editor = QtWidgets.QTextEdit()
        cancel_btn = uilib.OButton(uilib.IconPath('uiBtn_x'))
        cancel_btn.clicked.connect(self.cancelEditing)
        ok_btn = uilib.OButton(uilib.IconPath('uiBtn_save'))
        ok_btn.setSize(48)
        ok_btn.setBgColor(*uilib.Color.ExecColor)
        ok_btn.setToolTip('Finish to edit expression list.')
        ok_btn.clicked.connect(self.saveEditting)
        rem_btn = uilib.OButton(uilib.IconPath('uiBtn_rename'))
        rem_btn.setSize(48)
        rem_btn.setBgColor(168, 50, 68)
        rem_btn.setToolTip('Finish to rename expression list.')
        rem_btn.clicked.connect(self.rename)

        layout = QtWidgets.QGridLayout(self)
        layout.setColumnStretch(0, 1)
        layout.addWidget(self.__editor, 0, 0, 1, 4)
        layout.addWidget(cancel_btn, 1, 1, 1, 1)
        layout.addWidget(rem_btn, 1, 2, 1, 1)
        layout.addWidget(ok_btn, 1, 3, 1, 1)

    def setExpressionList(self, expList):
        r"""
            Args:
                expList (list):
        """
        text = '\n'.join([x.strip() for x in expList])
        self.__editor.setPlainText(text)

    def getExpressionList(self):
        textlist = self.__editor.toPlainText()
        return [x.strip() for x in textlist.split()]
    
    def saveEditting(self):
        self.editingFinished.emit(1, self.getExpressionList())
    
    def rename(self):
        self.editingFinished.emit(2, self.getExpressionList())

    def cancelEditing(self):
        self.editingFinished.emit(0, [])


class FacialExpressionManager(QtWidgets.QWidget):
    r"""
        モデルデータの作成、チェックを行う機能を提供するクラス
    """
    def __init__(self, managerEngine=None, parent=None):
        r"""
            第１引数には表情管理ノードを取得するためのクラス
            ManagerEngine
            のインスタンスを渡す。
            指定がない場合はデフォルトではManagerEngineクラスが使用される。

            Args:
                managerEngine (ManagerEngine):
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(FacialExpressionManager, self).__init__(parent)
        self.setWindowTitle('+Facial Expression Manager')
        
        self.setManagerEngine(managerEngine)

        self.__settings = Settings()
        self.__settings.editButtonClicked.connect(self.editExpressionMode)
        
        self.__f_view = FacialExpressionView()
        self.__settings.reloadButtonClicked.connect(self.reloadView)
        
        self.__exp_editor = ExpressionEditor()
        self.__exp_editor.editingFinished.connect(self.expressionListMode)

        self.__tab = uilib.ScrolledStackedWidget()
        self.__tab.addTab(self.__f_view)
        self.__tab.addTab(self.__exp_editor)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.__settings)
        layout.addWidget(self.__tab)
        layout.setStretchFactor(self.__tab, 1)

    def setManagerEngine(self, managerEngine=None):
        r"""
            表情管理ノードを取得するためのオブジェクトを設定する。

            Args:
                managerEngine (ManagerEngine):
        """
        if not managerEngine:
            managerEngine = ManagerEngine()
        self.__manager_engine = managerEngine

    def managerEngine(self):
        r"""
            設定された表情管理ノードを取得するためのオブジェクトを返す。

            Returns:
                ManagerEngine:
        """
        return self.__manager_engine

    def settings(self):
        r"""
            設定操作を行うためのGUIを返す。

            Returns:
                Settings:
        """
        return self.__settings

    def facialView(self):
        r"""
            設定操作を行うためのGUIを返す。

            Returns:
                Settings:
        """
        return self.__f_view
    
    def expressionEditor(self):
        return self.__exp_editor
    
    def tab(self):
        return self.__tab

    def reloadView(self):
        bs = self.settings().blendShape()
        me = self.managerEngine()
        me.setBlendShapeName(bs)
        self.facialView().reload(me)

    def setBlendShape(self, blendShapeName):
        r"""
            Args:
                blendShapeName (str):
        """
        self.settings().setBlendShape(blendShapeName)
        me = self.managerEngine()
        me.setBlendShapeName(blendShapeName)
        self.facialView().reload(me)

    def editExpressionMode(self):
        tab = self.tab().moveTo(1)
        root = self.managerEngine().getManagerNode()
        explist = list(root.listExpressions().keys())
        self.expressionEditor().setExpressionList(explist)
    
    def expressionListMode(self, mode, textlist):
        r"""
            Args:
                textlist (list):
        """
        result = 0
        if mode == 0:
            self.tab().moveTo(0)
            return

        from importlib import reload
        reload(facialMemoryManager)
        root = self.managerEngine().getManagerNode()
        if mode == 1:
            method = root.updateExpressionFromDataList
        else:
            method = root.renameExpressionFromDataList
               
        with node.DoCommand():
            result = method(textlist)
        self.tab().moveTo(0)
        if result:
            self.reloadView()

    def getExpressionData(self):
        r"""
            登録されている表情とそれを構成するパラメータの一覧を返す。
            
            Returns:
                OrderedDict:
        """
        root = self.managerEngine().getManagerNode()
        return root.listExpressionData()


class MainGUI(uilib.AbstractSeparatedWindow):
    r"""
        メインとなるGUIを提供するクラス
    """
    def centralWidget(self):
        r"""
            中心となるメインウィジェットを作成して返す
            
            Returns:
                FacialExpressionManager:
        """
        return FacialExpressionManager()


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。
        
        Returns:
            QtWidgets.QWidget:
    """
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(uilib.hires(300), uilib.hires(450))
    widget.show()
    return widget
