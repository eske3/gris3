#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2024/09/24 15:43 Eske Yoshinob[eske3g@gmail.com]
        update:2024/09/25 14:36 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import lib, uilib, node
from ..tools import blendShapeUtil
from ..uilib import mayaUIlib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


DefaultBlendShapeName = 'facial_bs'


class TargetContainerSetting(uilib.ClosableGroup):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(TargetContainerSetting, self).__init__(
            'Target shape container group'
        )
        label = QtWidgets.QLabel('Group name')
        self.field = mayaUIlib.NodePicker()
        self.field.setPickMode(mayaUIlib.NodePicker.SingleSelection)
        self.field.setNodeTypes('transform')
        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(label)
        layout.addWidget(self.field)

    def selectedNode(self):
        data = self.field.data()
        return data[0] if data else ''


class BlendShapeOption(uilib.ClosableGroup):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(BlendShapeOption, self).__init__('Blend Shape Option', parent)
        self.geometry = mayaUIlib.NodePicker()
        self.geometry.setNodeTypes('transform')
        self.geometry.setPickMode(mayaUIlib.NodePicker.SingleSelection)

        self.bs = QtWidgets.QLineEdit(DefaultBlendShapeName)

        layout = QtWidgets.QFormLayout(self)
        layout.addRow('Target Geometry', self.geometry)
        layout.addRow('Blend Shape', self.bs)

    def targetGeometry(self):
        data = self.geometry.data()
        return data[0] if data else ''

    def blendShape(self):
        return self.bs.text()


class Operator(uilib.ClosableGroup):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(Operator, self).__init__('Operations', parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(2)
        for l, m, icon in (
            # ('Create targets', 'createTargets', 'uiBtn_plus'),
            (
                'Create blend shape for facial', 'createBlendShape',
                'uiBtn_addUnit'
            ),
            ('Duplicate targets', 'duplicate', 'uiBtn_duplicateFace')
        ):
            btn = QtWidgets.QPushButton(l)
            btn.setIcon(uilib.Icon(icon))
            setattr(self, m+'ButtonClicked', btn.clicked)
            layout.addWidget(btn)


class Checker(uilib.ClosableGroup):
    addButtonClicked = QtCore.Signal(int)
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(Checker, self).__init__('Checker', parent)
        self.anim_frame = QtWidgets.QSpinBox()
        self.anim_frame.setButtonSymbols(QtWidgets.QSpinBox.NoButtons)
        self.anim_frame.setRange(1, 1000)
        self.anim_frame.setValue(10)
        add_btn = uilib.OButton(uilib.IconPath('uiBtn_plus'))
        add_btn.clicked.connect(self.emit_add_button)
        rem_btn = uilib.OButton(uilib.IconPath('uiBtn_trush'))
        self.removeButtonClicked = rem_btn.clicked
        
        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(2)
        layout.addStretch()
        layout.addWidget(self.anim_frame)
        layout.addWidget(add_btn)
        layout.addWidget(rem_btn)

    def emit_add_button(self):
        frame = self.anim_frame.value()
        self.addButtonClicked.emit(frame)


class BlendShapeUtil(QtWidgets.QWidget):
    r"""
        主にフェイシャル向けのブレンドシェイプの編集や作成補助昨日を提供する。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(BlendShapeUtil, self).__init__(parent)
        self.setWindowTitle('+Blend Shape Util')

        self.tgt_grp = TargetContainerSetting()
        self.option = BlendShapeOption()

        operator = Operator()
        # operator.createTargetsButtonClicked.connect(self.createTargets)
        operator.createBlendShapeButtonClicked.connect(self.createBlendShape)
        operator.duplicateButtonClicked.connect(self.duplicateTargets)

        checker = Checker()
        checker.setExpanding(False)
        checker.addButtonClicked.connect(self.addAnimForCheck)
        checker.removeButtonClicked.connect(self.removeAnimForCheck)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tgt_grp)
        layout.addWidget(self.option)
        layout.addWidget(operator)
        layout.addWidget(checker)
        layout.addStretch()

    def getData(self):
        result = {
            'targetGroup': self.tgt_grp.selectedNode(),
            'geometry': self.option.targetGeometry(),
            'bsName': self.option.blendShape()
        }
        return result
    
    def createTargets(self):
        pass

    def createBlendShape(self):
        data = self.getData()
        with node.DoCommand():
            blendShapeUtil.createBlendShapeForFacial(
                data['geometry'], data['bsName'], data['targetGroup']
            )

    def duplicateTargets(self):
        data = self.getData()
        with node.DoCommand():
            blendShapeUtil.duplicateTargets(
                data['geometry'], data['bsName'], data['targetGroup']
            )

    def addAnimForCheck(self, interval):
        r"""
            Args:
                interval (int):
        """
        data = self.getData()
        from ..tools import animUtil
        with node.DoCommand():
            animUtil.keyAllBlendShapeTargets(data['bsName'], 0, interval)

    def removeAnimForCheck(self):
        data = self.getData()
        from ..tools import animUtil
        with node.DoCommand():
            animUtil.deleteAllBlendShapeTargetAnims(data['bsName'])


class MainGUI(uilib.AbstractSeparatedWindow):
    r"""
        独立ウィンドウ式のBlendShapeUtilを提供する。
    """
    def centralWidget(self):
        r"""
            Returns:
                BlendShapeUtil:
        """
        return BlendShapeUtil()


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。

        Returns:
            QtWidgets.QWidget:
    """
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(640, 420)
    widget.show()
    return widget