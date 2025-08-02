#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ジョイントの編集機能を提供するGUI。
    
    Dates:
        date:2017/06/15 16:35[Eske](eske3g@gmail.com)
        update:2020/07/15 14:41 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from ..tools import jointEditor, nameUtility
from ..uilib import directionPlane, mayaUIlib
from .. import lib, uilib, node
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class CameraBasedParentWidget(directionPlane.DirectionScreen):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(CameraBasedParentWidget, self).__init__(parent)
        self.__camera = None

    def show(self):
        self.__camera = jointEditor.CameraBasedParentTool()
        if not self.__camera.isValid():
            return
        super(CameraBasedParentWidget, self).show()

    def execute(self, newVector, start, end, mouseButton, modifiers):
        r"""
            Args:
                newVector (list):
                start (QtCore.QPoint):
                end (QtCore.QPoint):
                mouseButton (int):
                modifiers (int):
        """
        if not self.__camera:
            return
        camera = self.__camera
        self.__camera = None
        with node.DoCommand():
            camera.parent(newVector, start, end)


class ParentTools(uilib.ClosableGroup):
    def __init__(self, parent=None):
        super(ParentTools, self).__init__('Parent Tools', parent)
        self.setIcon(uilib.IconPath('uiBtn_parentChain'))

        buttons = []
        for icon, color, cmd in (
            ('uiBtn_parentChain', uilib.Color.ExecColor, self.parentChain),
            ('uiBtn_parentChainInv', (87, 48, 172), self.parentChainInv),
            ('uiBtn_parentChainInv', (32, 181, 172), self.showParentTool),
        ):
            btn = uilib.OButton(uilib.IconPath(icon))
            btn.setBgColor(*color)
            btn.setSize(32)
            btn.clicked.connect(cmd)
            buttons.append(btn)

        parent_label = QtWidgets.QLabel('Parent chain')
        tool_label = QtWidgets.QLabel('Show camera based parent tool')

        create_layout = QtWidgets.QGridLayout(self)
        create_layout.setVerticalSpacing(1)
        create_layout.addWidget(buttons[0], 0, 0, 1, 1)
        create_layout.addWidget(buttons[1], 0, 1, 1, 1)
        create_layout.addWidget(parent_label, 0, 2, 1, 1)
        create_layout.addWidget(buttons[2], 1, 1, 1, 1)
        create_layout.addWidget(tool_label, 1, 2, 1, 1)
        create_layout.setColumnStretch(3, 1)

    def parentChain(self):
        with node.DoCommand():
            jointEditor.parentChain()

    def parentChainInv(self):
        with node.DoCommand():
            jointEditor.parentChain(isReverse=False)

    def showParentTool(self):
        tool = CameraBasedParentWidget(mayaUIlib.MainWindow)
        tool.show()


class JointSplitter(uilib.ClosableGroup):
    r"""
        選択ジョイントを分割するための機能を提供するUI。
        
        Inheritance:
            uilib:.ClosableGroup
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(JointSplitter, self).__init__('Joint Splitter', parent)
        self.setIcon(uilib.IconPath('uiBtn_bindSkin'))
        self.__start_info = []
        self.__created = []

        layout = QtWidgets.QGridLayout(self)

        fields, sliders = [], []
        for i, label in enumerate(
            ('Interactive Splitter', 'Executive Splitter')
        ):
            label = QtWidgets.QLabel(label)

            # 入力フィールド。
            field = QtWidgets.QSpinBox()
            field.setRange(0, 100)
            field.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
            
            # 入力スライダー。
            slider = QtWidgets.QSlider()
            slider.setOrientation(QtCore.Qt.Horizontal)

            layout.addWidget(label, i, 0, 1, 1)
            layout.addWidget(field, i, 1, 1, 1)
            layout.addWidget(slider, i, 2, 1, 1)

            fields.append(field)
            sliders.append(slider)

        # インタラクティブモード用UIの設定。===================================
        self.__int_slider = sliders[0]
        sliders[0].sliderPressed.connect(self.initializeInteractiveSplitter)
        sliders[0].sliderReleased.connect(self.closeInterativeSplitter)
        self.__int_min = fields[0]

        field = QtWidgets.QSpinBox()
        field.setRange(1, 100)
        field.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.__int_max = field
        layout.addWidget(field, 0, 3, 1, 1)

        field.valueChanged.connect(self.changeIntSliderMax)

        fields[0].valueChanged.connect(self.changeIntSliderMin)
        sliders[0].sliderMoved.connect(self.splitJointsIntaractivity)

        self.changeIntSliderMin(0)
        self.changeIntSliderMax(10)
        # =====================================================================

        # 実行モード用UIの設定。===============================================
        sliders[1].sliderMoved.connect(fields[1].setValue)
        fields[1].valueChanged.connect(sliders[1].setValue)

        self.__exec_slider = sliders[1]
        exec_btn = uilib.OButton(uilib.IconPath('uiBtn_plus'))
        exec_btn.setBgColor(*uilib.Color.ExecColor)
        exec_btn.clicked.connect(self.splitSelectedJoints)
        layout.addWidget(exec_btn, 1, 3, 1, 1)
        # =====================================================================

    def listCreatedJoints(self):
        r"""
            作成されたジョイントをリストで返す。
        """
        created = []
        for jointlist in self.__created:
            created.extend(jointlist)
        return created

    def changeIntSliderMax(self, value):
        r"""
            intのスライダの上限値を変更する。
            
            Args:
                value (int):
        """
        if value < 2:
            value = 2
        if value < self.__int_min.value():
            self.__int_min.setValue(value - 1)
        self.__int_max.setValue(value)
        self.__int_slider.setMaximum(value)

    def changeIntSliderMin(self, value):
        r"""
            intのスライダの下限値を変更する。
            
            Args:
                value (int):
        """
        if value < 0:
            value = 0

        if value >= self.__int_max.value():
            self.__int_max.setValue(value + 1)

        self.__int_min.setValue(value)
        self.__int_slider.setMinimum(value)

    def initializeInteractiveSplitter(self):
        r"""
            インタラクティブ作成スライダの初期化を行う。
        """
        jointEditor.cmds.undoInfo(openChunk=True)
        self.__start_info = []
        self.__created = []
        selected = jointEditor.node.ls(sl=True, type='joint')
        for s in selected:
            parent = s.parent()
            self.__start_info.append((s, parent))

    def splitJointsIntaractivity(self, value):
        r"""
            ジョイントをインタラクティブに分割する。
            
            Args:
                value (int):
        """
        if self.__created:
            for joint, parent in self.__start_info:
                    parent.addChild(joint)
            created = self.listCreatedJoints()
            if created:
                jointEditor.cmds.delete(created)

        if value > 0:
            self.__created = jointEditor.splitJoint(
                value, [x[0] for x in self.__start_info]
            )
            for c in self.listCreatedJoints():
                c.applyColor(17)
        else:
            self.__created = []

    def closeInterativeSplitter(self):
        r"""
            インタラクティブにジョイントを分割するスライダのクローズ処理を行う。
        """
        for c in self.listCreatedJoints():
            c.applyColor(None)
        jointEditor.cmds.undoInfo(closeChunk=True)
        self.__start_info = []
        self.__created = []
        self.__int_slider.setValue(0)

    def splitSelectedJoints(self):
        r"""
            選択ジョイントを任意の数で分割する。
        """
        num = self.__exec_slider.value()
        with node.DoCommand():
            jointEditor.splitJoint(num)


class OptionWidget(QtWidgets.QWidget):
    r"""
        オプション表示用のUIを提供するクラス。
    """
    def data(self):
        r"""
            データを返す。再実装用メソッド。
        """
        return None


class AxisChooser(QtWidgets.QWidget):
    r"""
        軸を選択するUIをを提供するクラス。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(AxisChooser, self).__init__(parent)

        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setVerticalSpacing(0)
        layout.setHorizontalSpacing(20)
        self.__group = QtWidgets.QButtonGroup(self)

        for i, pm in enumerate('+-'):
            for j, axis in enumerate('XYZ'):
                radio = QtWidgets.QRadioButton(pm+axis)
                layout.addWidget(radio, i, j, 1, 1)
                self.__group.addButton(radio, i*3+j)
        layout.setColumnStretch(3, 1)
        self.__group.button(0).setChecked(True)

    def setChecked(self, axis):
        r"""
            引き数axisに該当するボタンをチェックする。
            
            Args:
                axis (str):jointEditor.Axislistのいずれか
        """
        axis = axis.upper()
        index = (
            jointEditor.Axislist.index(axis)
            if axis in jointEditor.Axislist else 0
        )
        self.__group.button(index).setChecked(True)

    def data(self):
        r"""
            チェックされている軸を返す。
            
            Returns:
                str:X,Y,Zのいずれか
        """
        return jointEditor.Axislist[self.__group.checkedId()]


# class JointAxisEditor(uilib.ClosableGroup):
class JointAxisEditor(uilib.ClosableGroup):
    r"""
        ジョイントの軸を編集するためのUIを低居するクラス。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        thin_margin = QtCore.QMargins(2, 2, 2, 2)
        super(JointAxisEditor, self).__init__('Joint Axis Editor', parent)
        self.setIcon(uilib.IconPath('uiBtn_fixOrientation'))
        self.__orient_mod = jointEditor.OrientationModifier()
        self.setWindowTitle('Joint Axis Editor')

        layout = QtWidgets.QGridLayout(self)
        # layout.setContentsMargins(thin_margin)
        layout.setSpacing(1)

        # オプション項目のチェックボックス。===================================
        self.__apply_to_children = QtWidgets.QCheckBox('Apply to Children')
        self.__apply_to_children.setChecked(True)
        self.__freeze = QtWidgets.QCheckBox('Freeze')
        layout.addWidget(self.__apply_to_children, 0, 0, 1, 1)
        layout.addWidget(self.__freeze, 1, 0, 1, 1)
        # =====================================================================
        
        # 実行ボタン===========================================================
        set_btn = uilib.OButton()
        set_btn.setIcon(uilib.IconPath('uiBtn_play'))
        set_btn.setSize(36)
        set_btn.setBgColor(*uilib.Color.ExecColor)
        set_btn.setToolTip('Edit joint axis.')
        set_btn.clicked.connect(self.setAxis)
        layout.addWidget(set_btn, 0, 1, 2, 1)
        layout.setAlignment(set_btn, QtCore.Qt.AlignRight)
        # =====================================================================

        pri_gui_builder = (
            OptionWidget, AxisChooser, AxisChooser, mayaUIlib.NodePicker,
        )
        sec_gui_builder = (
            AxisChooser, AxisChooser, mayaUIlib.NodePicker, mayaUIlib.NodePicker,
        )
        self.__uis = []
        row = 2
        for i, gui_data in enumerate(
            zip(
                ('Primary Axis', 'Secondary Axis'),
                (pri_gui_builder, sec_gui_builder),
                (
                    jointEditor.OrientationModifier.PrimaryMode,
                    jointEditor.OrientationModifier.SecondaryMode
                ),
            )
        ):
            label, gui_builders, gui_labels = gui_data
            group = QtWidgets.QGroupBox(label)
            grp_layout = QtWidgets.QGridLayout(group)

            # メインの軸を指定するUI。
            axis = AxisChooser()
            if i != 0:
                axis.setChecked('+Z')
            grp_layout.addWidget(QtWidgets.QLabel('Axis'), 0, 0, 1, 1)
            grp_layout.addWidget(axis, 0, 1, 1, 1)

            # ターゲットの種類を選択するUI。==================================
            tgt_widget = QtWidgets.QWidget()
            tgt_comb = QtWidgets.QComboBox()
            tgt_layout = QtWidgets.QVBoxLayout(tgt_widget)
            tgt_layout.addStretch()
            tgt_layout.setContentsMargins(thin_margin)
            tgt_layout.addWidget(QtWidgets.QLabel('Target'))
            tgt_layout.addWidget(tgt_comb)
            tgt_layout.addStretch()
            # ================================================================
            
            # ターゲットを指定するGUI。
            tgt_opt = QtWidgets.QStackedWidget()
            tgt_comb.currentIndexChanged.connect(tgt_opt.setCurrentIndex)

            uidic = {
                'grp':group, 'axis':axis,
                'targetType':tgt_comb, 'targetOption':tgt_opt
            }
            options = []
            # ターゲットを指定するGUIを追加。=================================
            for label, gui in zip(gui_labels, gui_builders):
                tgt_comb.addItem(lib.title(label), label)
                opt = gui()
                if gui is AxisChooser:
                    opt.setChecked('+Y')
                tgt_opt.addWidget(opt)
                options.append(opt)
            # ================================================================
            
            tgt_opt_grp = QtWidgets.QGroupBox()
            tgt_opt_layout = QtWidgets.QVBoxLayout(tgt_opt_grp)
            # tgt_opt_layout.setContentsMargins(thin_margin)
            tgt_opt_layout.addWidget(tgt_opt)

            grp_layout.addWidget(tgt_widget, 1, 0, 1, 1)
            grp_layout.addWidget(tgt_opt_grp, 1, 1, 1, 1)

            self.__uis.append(uidic)
            layout.addWidget(group, row, 0, 1, 2)
            row += 1
        layout.setRowStretch(row, 1)

    def setAxis(self):
        r"""
            ジョイントの軸を設定に基づいて変更する
        """
        result = []
        # 軸に関するオプションをUIから取得する。===============================
        for dic in self.__uis:
            main_axis = dic['axis'].data()
            target_type = dic['targetType'].itemData(
                dic['targetType'].currentIndex()
            )
            target_option = dic['targetOption'].currentWidget().data()
            result.append([main_axis, target_type, target_option])
        # =====================================================================

        # 軸に関するオプションを設定する。=====================================
        # primary axis
        self.__orient_mod.setPrimaryAxis(result[0][0])
        self.__orient_mod.setPrimaryMode(result[0][1])
        if result[0][2] in jointEditor.Axislist:
            self.__orient_mod.setPrimaryAimAxis(result[0][2])
        elif result[0][2]:
            self.__orient_mod.setTarget(result[0][2])

        # secondary axis
        self.__orient_mod.setSecondaryAxis(result[1][0])
        self.__orient_mod.setSecondaryMode(result[1][1])
        if result[1][2] in jointEditor.Axislist:
            self.__orient_mod.setTargetUpAxis(result[1][2])
        else:
            self.__orient_mod.setUpTarget(result[1][2])
        # =====================================================================

        # その他オプション設定。===============================================
        self.__orient_mod.setApplyToChildren(
            self.__apply_to_children.isChecked()
        )
        self.__orient_mod.setIsFreeze(self.__freeze.isChecked())
        # =====================================================================

        with node.DoCommand():
            self.__orient_mod.execute()

class JointMirror(uilib.ClosableGroup):
    r"""
        ジョイントをミラーコピーする機能を提供するクラス。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        self.__mirror = jointEditor.JointMirror()
        super(JointMirror, self).__init__('Mirror Joints', parent)
        self.setIcon(uilib.IconPath('uiBtn_mirrorJoints'))
        # 子すべてのミラーを行うかどうか。
        self.__apply_to_children = QtWidgets.QCheckBox('Apply to children')
        self.__apply_to_children.setChecked(True)
        
        # Behaviorかどうか。
        self.__behavior = QtWidgets.QCheckBox('Behavior')
        self.__behavior.setChecked(True)
        
        # 軸の設定。===========================================================
        ax_label = QtWidgets.QLabel('Mirror Axis')
        ax_grp = QtWidgets.QWidget()
        ax_layout = QtWidgets.QHBoxLayout(ax_grp)
        ax_layout.setContentsMargins(0, 0, 0, 0)
        ax_layout.addWidget(ax_label)

        self.__axis_group = QtWidgets.QButtonGroup(self)
        for i, axis in enumerate('XYZ'):
            radio = QtWidgets.QRadioButton(axis)
            self.__axis_group.addButton(radio, i)
            ax_layout.addWidget(radio)
        self.__axis_group.button(0).setChecked(True)
        # =====================================================================

        # ミラージョイントのリネーム設定。=====================================
        rep_grp = QtWidgets.QGroupBox('Replace name for the mirrored joints')
        self.__search = uilib.FilteredLineEdit('_L')
        self.__search.setFilter(nameUtility.NameFilterRegularExpression)
        self.__replaced = uilib.FilteredLineEdit('_R')
        self.__replaced.setFilter(nameUtility.NameFilterRegularExpression)
        
        rep_layout = QtWidgets.QFormLayout(rep_grp)
        rep_layout.addRow(QtWidgets.QLabel('Search for'), self.__search)
        rep_layout.addRow(QtWidgets.QLabel('Replace with'), self.__replaced)
        # =====================================================================

        # 親の設定。===========================================================
        parent_grp = QtWidgets.QGroupBox('Parent Options')
        self.__parent = QtWidgets.QCheckBox('Parent to replaced name parent.')
        self.__p_search = uilib.FilteredLineEdit('_L')
        self.__p_replaced = uilib.FilteredLineEdit('_R')
        for editor in (self.__p_search, self.__p_replaced):
            editor.setFilter(nameUtility.NameFilterRegularExpression)
            editor.setEnabled(False)
            self.__parent.toggled.connect(editor.setEnabled)
        
        parent_layout = QtWidgets.QFormLayout(parent_grp)
        parent_layout.addWidget(self.__parent)
        parent_layout.addRow(QtWidgets.QLabel('Search for'), self.__p_search)
        parent_layout.addRow(
            QtWidgets.QLabel('Replace with'), self.__p_replaced
        )
        # =====================================================================

        # 実行ボタン===========================================================
        mrr_btn = uilib.OButton()
        mrr_btn.setIcon(uilib.IconPath('uiBtn_play'))
        mrr_btn.setSize(36)
        mrr_btn.setBgColor(*uilib.Color.ExecColor)
        mrr_btn.setToolTip('Mirror selected joints.')
        mrr_btn.clicked.connect(self.mirroring)
        # =====================================================================

        layout = QtWidgets.QGridLayout(self)
        layout.setSpacing(1)
        layout.addWidget(mrr_btn, 0, 1, 3, 1)
        layout.setAlignment(mrr_btn, QtCore.Qt.AlignRight)
        layout.addWidget(self.__apply_to_children, 0, 0, 1, 1)
        layout.addWidget(self.__behavior, 1, 0, 1, 1)
        layout.addWidget(ax_grp, 2, 0, 1, 1)
        layout.addWidget(rep_grp, 3, 0, 1, 2)
        layout.addWidget(parent_grp, 4, 0, 1, 2)

    def mirroring(self):
        r"""
            ミラーリングを実行する。
        """
        self.__mirror.setApplyToChildren(self.__apply_to_children.isChecked())
        self.__mirror.setMirrorBehavior(self.__behavior.isChecked())
        self.__mirror.setMirrorAxis('XYZ'[self.__axis_group.checkedId()])
        self.__mirror.setSearchingString(self.__search.text())
        self.__mirror.setReplacedString(self.__replaced.text())
        self.__mirror.setIsReplacingParent(self.__parent.isChecked())
        self.__mirror.setParentSearchingString(self.__p_search.text())
        self.__mirror.setParentReplacedString(self.__p_replaced.text())
        with node.DoCommand():
            self.__mirror.execute()

class Finisher(QtWidgets.QGroupBox):
    r"""
        最終処理を行う機能を提供するクラス。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(Finisher, self).__init__('Finisher', parent)
        
        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(3)
        for color, icon, method, ann in (
            (
                (49, 82, 199), 'uiBtn_fixOrientation', self.fixOrientation,
                'Fix orientation of selected joints.'
            ),
            (
                (49, 115, 154), 'uiBtn_mirrorJoints', self.mirrorSelected,
                'Apply mirrored position of a selected to a opposite side.'
            ),
            (
                (87, 48, 172), 'uiBtn_mirrorJoints', self.mirrorAlternately,
                'Apply mirrored from first selection to second selection.'
            ),
            (
                (60, 160, 135), 'uiBtn_connectInvScale',
                self.reconnectInverseScale,
                'Connects attr "scale" to "inverse scale".'
            ),
        ):
            btn = uilib.OButton()
            btn.setIcon(uilib.IconPath(icon))
            btn.setSize(48)
            btn.setBgColor(*color)
            btn.setToolTip(ann)
            btn.clicked.connect(method)
            layout.addWidget(btn)
        layout.addStretch()

    def fixOrientation(self):
        r"""
            ジョイントのX軸を子に向ける。
        """
        with node.DoCommand():
            jointEditor.fixOrientation()

    def mirrorSelected(self):
        r"""
            選択ノードの反対側のノードをミラーリングする。
        """
        with node.DoCommand():
            jointEditor.mirrorJoints()

    def mirrorAlternately(self):
        r"""
            ここに説明文を記入
        """
        with node.DoCommand():
            jointEditor.mirrorJointsAlternately()

    def reconnectInverseScale(self):
        r"""
            親のscaleをジョイントのinverseScaleにつなぐ。
        """
        with node.DoCommand():
            jointEditor.reconnectInverseScale()


class JointBuilder(uilib.FlatScrollArea):
    r"""
        ジョイントを作成するためのツールを集めたウィジェット。
    """
    def buildUI(self, parent):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        self.setWindowTitle('Joint Builder')

        # ジョインt作成UI。====================================================
        create_btn = uilib.OButton(uilib.IconPath('uiBtn_plus'))
        create_btn.setBgColor(*uilib.Color.ExecColor)
        create_btn.setSize(32)
        create_btn.setToolTip('Create a new joint under the selected node.')
        create_btn.clicked.connect(self.createJoint)
        create_label = QtWidgets.QLabel('Create new joint')

        rad_btn = uilib.OButton(uilib.IconPath('uiBtn_arrangeRadius'))
        rad_btn.setBgColor(*uilib.Color.ExecColor)
        rad_btn.setSize(32)
        rad_btn.setToolTip(
            'Arrange joint radius between 2 joints.\n'
            'Select a start joint and end joint that is under the start joint.'
        )
        rad_btn.clicked.connect(self.arrangeJointRadius)
        rad_label = QtWidgets.QLabel(
            'Arrange radius between start to end joint.'
        )
        
        # parentツール群。-----------------------------------------------------
        create_layout = QtWidgets.QGridLayout()
        create_layout.setSpacing(1)
        create_layout.addWidget(create_btn, 0, 0, 1, 1)
        create_layout.addWidget(create_label, 0, 1, 1, 1, QtCore.Qt.AlignLeft)
        create_layout.addWidget(rad_btn, 1, 0, 1, 1)
        create_layout.addWidget(rad_label, 1, 1, 1, 2, QtCore.Qt.AlignLeft)
        # ---------------------------------------------------------------------
        # =====================================================================
        
        parent_tool = ParentTools()
        splitter = JointSplitter()
        axis_editor = JointAxisEditor()
        mirror = JointMirror()

        layout = QtWidgets.QVBoxLayout(parent)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(create_layout)
        for grp in (parent_tool, splitter, axis_editor, mirror):
            grp.setExpanding(False)
            layout.addWidget(grp)
            grp.installEventFilter(self)
        layout.addStretch()

    def createJoint(self):
        r"""
            ジョイントを新規で作成する。
        """
        mod = QtWidgets.QApplication.keyboardModifiers()
        with node.DoCommand():
            jointEditor.createJointFromSelected(
                mod != QtCore.Qt.ControlModifier
            )

    def arrangeJointRadius(self):
        r"""
            ２つのジョイント間のjointRadiusを揃える
        """
        mod = QtWidgets.QApplication.keyboardModifiers()
        if mod == QtCore.Qt.ControlModifier:
            method = jointEditor.arrangeJointRadiusChain
        else:
            method = jointEditor.arrangeJointRadius
        with node.DoCommand():
            method()


class JointEditor(QtWidgets.QWidget):
    r"""
        ジョイントの作成、編集を行うためのツールを提供するクラス。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(JointEditor, self).__init__(parent)
        self.setWindowTitle('+Joint Editor')
        builder = JointBuilder()
        finisher = Finisher()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(builder)
        layout.addWidget(finisher)


class MainGUI(uilib.AbstractSeparatedWindow):
    r"""
        メインGUIとなるウィジェット
    """
    def centralWidget(self):
        r"""
            Returns:
                JointEditor:
        """
        return JointEditor()


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。
        
        Returns:
            QtWidgets.QWidget:.
    """
    from gris3.uilib import mayaUIlib
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(300, 600)
    widget.show()
    return widget