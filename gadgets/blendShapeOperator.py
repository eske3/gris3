#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2024/09/24 15:43 Eske Yoshinob[eske3g@gmail.com]
        update:2025/08/17 13:28 Eske Yoshinob[eske3g@gmail.com]
        
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
DefaultTargetContainer = 'facialMorph_grp'
DefaultTargetGeometory = 'face_geo'


TargetListTemplate = '''eye_wink_facialGrp_L
eye_wink_facialGrp_R
eye_close_facialGrp_L
eye_close_facialGrp_R
eye_surprise_facialGrp_L
eye_surprise_facialGrp_R
eye_sad_facialGrp_L
eye_sad_facialGrp_R
eye_angry_facialGrp_L
eye_angry_facialGrp_R
eye_downcast_facialGrp_L
eye_downcast_facialGrp_R
mouth_a_facialGrp_C
mouth_i_facialGrp_C
mouth_u_facialGrp_C
mouth_e_facialGrp_C
mouth_o_facialGrp_C
mouth_oh_facialGrp_C
mouth_kiss_facialGrp_C
mouth_shout_facialGrp_C
mouth_small_facialGrp_C
mouth_serious_facialGrp_C
mouth_surprise_facialGrp_C
mouth_upCorner_facialGrp_L
mouth_upCorner_facialGrp_R
mouth_pullCorner_facialGrp_L
mouth_pullCorner_facialGrp_R
mouth_discontent_facialGrp_L
mouth_discontent_facialGrp_R
mouth_strain_facialGrp_L
mouth_strain_facialGrp_R
mouth_up_facialGrp_C
mouth_down_facialGrp_C
mouth_slide_facialGrp_L
mouth_slide_facialGrp_R
nose_up_facialGrp_C
nose_down_facialGrp_C
brow_laugh_facialGrp_L
brow_laugh_facialGrp_R
brow_surprise_facialGrp_L
brow_surprise_facialGrp_R
brow_angry_facialGrp_L
brow_angry_facialGrp_R
brow_troubled_facialGrp_L
brow_troubled_facialGrp_R
brow_shout_facialGrp_L
brow_shout_facialGrp_R
brow_up_facialGrp_L
brow_up_facialGrp_R
brow_down_facialGrp_L
brow_down_facialGrp_R
tooth_up_facialGrp_C
tooth_down_facialGrp_C
pupil_decrease_facialGrp_C
pupil_lookat_facialGrp_C
'''


from importlib import reload
reload(blendShapeUtil)


class TargetListEditor(QtWidgets.QWidget):
    edittingFinished = QtCore.Signal(list)

    def __init__(self, parent=None):
        r"""
            Args:
                parent (any):
        """
        super(TargetListEditor, self).__init__(parent)
        self.__default_template = TargetListTemplate
        self.__editor = QtWidgets.QTextEdit()
        
        d_tmp_btn = QtWidgets.QPushButton('Use Template')
        d_tmp_btn.clicked.connect(self.useDefaultTemplateList)
        ccl_btn = uilib.OButton(uilib.IconPath('uiBtn_x'))
        self.cancelButtonClicked = ccl_btn.clicked
        save_btn = uilib.OButton(uilib.IconPath('uiBtn_save'))
        save_btn.setSize(42)
        save_btn.clicked.connect(self.makeTargetList)
        
        layout = QtWidgets.QGridLayout(self)
        layout.setColumnStretch(1, 1)
        layout.setRowStretch(0, 1)
        layout.addWidget(self.__editor, 0, 0, 1, 4)
        layout.addWidget(d_tmp_btn, 1, 0, 1, 1)
        layout.addWidget(ccl_btn, 1, 2, 1, 1)
        layout.addWidget(save_btn, 1, 3, 1, 1)

    def setTemplateText(self, text):
        r"""
            Args:
                text (str):
        """
        self.__default_template = text

    def useDefaultTemplateList(self):
        self.__editor.setPlainText(self.__default_template)

    def setup(self, targetShapeContainer):
        r"""
            Args:
                targetShapeContainer (any):
        """
        tgt_list = blendShapeUtil.convTargetContainerGroupToList(
            targetShapeContainer
        )
        self.__editor.setPlainText('\n'.join(tgt_list))

    def makeTargetList(self):
        targetlist = self.__editor.toPlainText().split('\n')
        self.edittingFinished.emit(targetlist)


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
        r"""
            設定されているブレンドシェイプターゲットを格納するグループ名を返す。
            
            Returns:
                str:
        """
        return self.field.data()

    def setNode(self, nodeName):
        r"""
            ブレンドシェイプターゲットを格納するグループ名を設定する。
            
            Args:
                nodeName (str):
        """
        self.field.setData([nodeName])


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

    def setTargetGeometry(self, target):
        r"""
            ブレンドシェイプ適用対象ノードを設定する。
            
            Args:
                target (str):
        """
        self.geometry.setData([target])

    def targetGeometry(self):
        r"""
            設定されているブレンドシェイプ適用対象ノードを返す。
            
            Returns:
                str:
        """
        return self.geometry.data()

    def setBlendShape(self, blendShapeName):
        r"""
            ブレンドシェイプノードを設定する。
            
            Args:
                blendShapeName (str):
        """
        self.bs.setText(blendShapeName)

    def blendShape(self):
        r"""
            設定されているブレンドシェイプノードを返す。
            
            Returns:
                str:
        """
        return self.bs.text()

    def setBlendShape(self, blendShapeName):
        self.bs.setText(blendShapeName)


class Operator(uilib.ClosableGroup):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(Operator, self).__init__('Operations', parent)
        
        setup_w = QtWidgets.QWidget()
        btn = QtWidgets.QPushButton('Create targets')
        edit_btn = uilib.OButton(uilib.IconPath('uiBtn_edit'))
        self.createTargetButtonClicked = btn.clicked
        self.editButtonClicked = edit_btn.clicked
        layout = QtWidgets.QHBoxLayout(setup_w)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        layout.addWidget(btn)
        layout.addWidget(edit_btn)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(2)
        layout.addWidget(setup_w)
        for l, m, icon in (
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
        self.setIcon(uilib.IconPath('uiBtn_check'))
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


class BlendShapeUtil(uilib.ScrolledStackedWidget):
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

        w = QtWidgets.QWidget()
        self.tgt_grp = TargetContainerSetting()
        self.option = BlendShapeOption()

        operator = Operator()
        operator.editButtonClicked.connect(self.editTargetList)
        # operator.createTargetsButtonClicked.connect(self.createTargets)
        operator.createBlendShapeButtonClicked.connect(self.createBlendShape)
        operator.duplicateButtonClicked.connect(self.duplicateTargets)

        checker = Checker()
        checker.setExpanding(False)
        checker.addButtonClicked.connect(self.addAnimForCheck)
        checker.removeButtonClicked.connect(self.removeAnimForCheck)

        layout = QtWidgets.QVBoxLayout(w)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tgt_grp)
        layout.addWidget(self.option)
        layout.addWidget(operator)
        layout.addWidget(checker)
        layout.addStretch()
        
        self.addTab(w)

        self.__target_list_editor = TargetListEditor()
        self.__target_list_editor.cancelButtonClicked.connect(
            self.finishEditting
        )
        self.__target_list_editor.edittingFinished.connect(
            self.finishEditting
        )
        self.addTab(self.__target_list_editor)

    def getData(self):
        result = {
            'targetGroup': self.tgt_grp.selectedNode(),
            'geometry': self.option.targetGeometry(),
            'bsName': self.option.blendShape()
        }
        return result

    def setBlendShape(self, blendShapeName):
        r"""
            ブレンドシェイプノードを設定する。
            
            Args:
                blendShapeName (str):
        """
        self.option.setBlendShape(blendShapeName)

    def setTargetGeometry(self, targetGeometry):
        r"""
            ブレンドシェイプ適用対象ノードを設定する。
            
            Args:
                targetGeometry (str):
        """
        self.option.setTargetGeometry(targetGeometry)

    def setTargetShapeContainer(self, targetShapeContainer):
        r"""
            ブレンドシェイプターゲットを格納するグループ名を設定する。
            
            Args:
                targetShapeContainer (any):
        """
        self.tgt_grp.setNode(targetShapeContainer)

    def setDefaultTargetList(self, targetListText):
        r"""
            Args:
                targetListText (any):
        """
        self.__target_list_editor.setTemplateText(targetListText)

    def editTargetList(self):
        data = self.getData()
        if not data['targetGroup']:
            return
        self.__target_list_editor.setup(data['targetGroup'])
        self.moveTo(1)

    def finishEditting(self, targetShapeList=None):
        if targetShapeList:
            data = self.getData()
            blendShapeUtil.makeShapeTargets(
                data['targetGroup'], targetShapeList
            )
        self.moveTo(0)

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


def showWindow(
    blendShapeName='', targetGeometry='', targetShapeContainer='',
    defaultTargetListTemplate=TargetListTemplate
):
    r"""
        ウィンドウを作成するためのエントリ関数。
        
        Args:
            blendShapeName (str):ブレンドシェイプ名
            targetGeometry (str):ブレンドシェイプを適用されるノード名
            targetShapeContainer (str):シェイプターゲットを格納するグループ名
            defaultTargetListTemplate (str):表情リストのテンプレート
            
        Returns:
            QtWidgets.QWidget:
    """
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(640, 420)
    m = widget.main()
    m.setBlendShape(blendShapeName)
    m.setTargetGeometry(targetGeometry)
    m.setTargetShapeContainer(targetShapeContainer)
    m.setDefaultTargetList(defaultTargetListTemplate)
    widget.show()
    return widget