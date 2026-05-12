#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ここに説明文を記入
    
    Dates:
        date:2017/07/06 5:35[Eske](eske3g@gmail.com)
        update:2024/02/22 14:12 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from ..tools import sweepMesh, uvSupporter
from ..uilib import mayaUIlib
from .. import node, uilib, lib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class RebuildModeOption(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(RebuildModeOption, self).__init__('Rebuild Curve Option', parent)
        len_btn = QtWidgets.QRadioButton('Length')
        span_btn = QtWidgets.QRadioButton('Span')
        len_btn.setChecked(True)
        reb_btn_grp = QtWidgets.QButtonGroup()
        reb_btn_grp.addButton(len_btn, 0)
        reb_btn_grp.addButton(span_btn, 1)

        tab = QtWidgets.QStackedWidget()
        self.__spiners = []
        for l, spiner, dv, max_val in (
            ('Length', uilib.DoubleSpiner, 5.0, 10000),
            ('Number of spans', uilib.Spiner, 7, 1000)
        ):
            p = QtWidgets.QWidget()
            label = QtWidgets.QLabel(l)
            field = spiner()
            field.setValue(dv)
            field.setRange(0, max_val)
            layout = QtWidgets.QHBoxLayout(p)
            layout.addWidget(label)
            layout.setAlignment(label, QtCore.Qt.AlignRight)
            layout.addWidget(field)
            tab.addWidget(p)
            self.__spiners.append(field)
        
        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel('Mode :'))
        layout.addWidget(len_btn)
        layout.addWidget(span_btn)
        layout.addWidget(tab)
        self.__mode = reb_btn_grp
        self.__mode.idClicked.connect(tab.setCurrentIndex)

    def mode(self):
        return self.__mode.checkedId()

    def value(self):
        return self.__spiners[self.mode()].value()


class PolySelector(QtWidgets.QWidget):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(PolySelector, self).__init__(parent)
        label = QtWidgets.QLabel('Target Mesh')
        picker = mayaUIlib.NodePicker()
        picker.setPickMode(picker.SingleSelection)
        picker.setNodeTypes('transform', 'mesh')
        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(label)
        layout.setAlignment(label, QtCore.Qt.AlignRight)
        layout.addWidget(picker)
        self.__picker = picker

    def getPolygon(self):
        return self.__picker.data()


class InterpolcationOption(QtWidgets.QGroupBox):
    r"""
        形状の横方向分割に関数るオプションGUIを提供する。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(InterpolcationOption, self).__init__(
            'Interpolcation Option', parent
        )
        layout = QtWidgets.QFormLayout(self)
        self.__distance = uilib.DoubleSpiner()
        self.__distance.setRange(0.00001, 10000000)
        self.__distance.setValue(2)
        layout.addRow('Distance', self.__distance)

    def distance(self):
        return self.__distance.value()


class ShapeOption(QtWidgets.QGroupBox):
    r"""
        形状の横方向分割に関数るオプションGUIを提供する。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ShapeOption, self).__init__('Shape Option', parent)
        layout = QtWidgets.QGridLayout(self)
        self.__ui = {}
        i = 0
        for l, dv in (
            ('width', 2.0),
            ('height', 1.5),
        ):
            widget = uilib.DoubleSpiner()
            widget.setRange(0.0001, 10000000)
            widget.setValue(dv)
            layout.addWidget(
                QtWidgets.QLabel(lib.title(l)), 0, i, 1, 1, QtCore.Qt.AlignRight
            )
            layout.addWidget(widget, 0, i + 1, 1, 1)
            i += 2
            self.__ui[l] = widget
        mat_picker = mayaUIlib.NodePicker()
        mat_picker.setPickMode(mayaUIlib.NodePicker.SingleSelection)
        mat_picker.setSelectionOptions(materials=True)
        layout.addWidget(
            QtWidgets.QLabel('Material'), 1, 0, 1, 1, QtCore.Qt.AlignRight
        )
        layout.addWidget(mat_picker, 1, 1, 1, 3)
        self.__ui['material'] = mat_picker

    def shapeSize(self):
        return [self.__ui[x].value() for x in ('width', 'height')]

    def material(self):
        return self.__ui['material'].data()


class MakeOption(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(MakeOption, self).__init__('Created into', parent)
        layout = QtWidgets.QHBoxLayout(self)
        self.__ui = {}
        for l in ('mesh', 'curve'):
            label = QtWidgets.QLabel(lib.title(l))
            layout.addWidget(label)
            layout.setAlignment(label, QtCore.Qt.AlignRight)

            w = mayaUIlib.NodePicker()
            w.setNodeTypes('transform')
            w.setPickMode(w.SingleSelection)
            layout.addWidget(w)
            self.__ui[l] = w

    def  getData(self, category):
        return self.__ui[category].data()

    def meshGroup(self):
        return self.getData('mesh')

    def curveGroup(self):
        return self.getData('curve')


class Creator(QtWidgets.QScrollArea):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(Creator, self).__init__(parent)
        self.setWindowTitle('Creation')

        w = QtWidgets.QWidget()
        btn = QtWidgets.QPushButton('Create Hair')
        btn.clicked.connect(self.createHair)
        
        self.__rebuild_mode = RebuildModeOption()
        self.__target = PolySelector()
        self.__interp_opt = InterpolcationOption()
        self.__shape_opt = ShapeOption()
        self.__make_opt = MakeOption()

        layout = QtWidgets.QVBoxLayout(w)
        layout.addWidget(self.__rebuild_mode)
        layout.addWidget(self.__target)
        layout.addWidget(self.__interp_opt)
        layout.addWidget(self.__shape_opt)
        layout.addWidget(self.__make_opt)
        layout.addStretch()
        layout.addWidget(btn)
        
        self.setWidgetResizable(True)
        self.setWidget(w)        

    def createHair(self):
        dc = mayaUIlib.DrawerOnCamera(mayaUIlib.MainWindow)
        if not dc.isValid():
            dc.deleteLater()
            del dc
            return
        if not dc.exec_():
            return
        # リビルドオプション
        rebuild_mode = self.__rebuild_mode.mode()
        rebuild_num = self.__rebuild_mode.value()
        
        # 横方向分割オプション
        intp_dist = self.__interp_opt.distance()
        
        # 形状に関するオプション。
        width, height = self.__shape_opt.shapeSize()
        material = self.__shape_opt.material()
        
        # 作成後の形状を格納するグループ
        mesh_grp = self.__make_opt.meshGroup()
        crv_grp = self.__make_opt.curveGroup()

        cam_mtx = dc.cameraMatrix()
        target_mesh = self.__target.getPolygon()
        center = sweepMesh.centerBetweenCamToMesh(cam_mtx, target_mesh, 0.99)
        with node.DoCommand():
            curve = sweepMesh.createProjectionCurve(
                cam_mtx, dc.drawData(center),
                target_mesh, rebuild_mode, rebuild_num,
            )
            sweepMesh.sweepHair(
                [curve], interpolationDistance=intp_dist,
                width=width, height=height, material=material,
                meshInto=mesh_grp, curveInto=crv_grp
            )


class Utilities(QtWidgets.QScrollArea):
    def __init__(self, parent=None):
        super(Utilities, self).__init__(parent)
        self.setWindowTitle('Utilities')
        
        # 選択便利ツール。=====================================================
        sel_grp = QtWidgets.QGroupBox('Selection Util')
        layout = QtWidgets.QGridLayout(sel_grp)
        col = 0
        for l,f in (
            ('to mesh', self.convertSelectionToMesh),
            ('to curve', self.convertSelectionToCurve)
        ):
            btn = QtWidgets.QPushButton(l)
            btn.clicked.connect(f)
            layout.addWidget(btn, 0, col, 1, 1)
            col += 1
        btn = QtWidgets.QPushButton('Select editing')
        btn.clicked.connect(self.selectEditing)
        layout.addWidget(btn, 1, 0, 1, 2)
        # =====================================================================
        
        # 複製に関する機能。===================================================
        dup_grp = QtWidgets.QGroupBox('Duplicating')
        btn = QtWidgets.QPushButton('Duplicate from selected(Param Only)')
        btn.clicked.connect(self.duplicate)
        all_btn = QtWidgets.QPushButton('Duplicate from selected(All)')
        all_btn.clicked.connect(self.duplicateAll)
        layout = QtWidgets.QVBoxLayout(dup_grp)
        layout.addWidget(btn)
        layout.addWidget(all_btn)
        # =====================================================================
        
        # 雑多な機能。=========================================================
        misc_grp = QtWidgets.QGroupBox('Misc')
        btn = QtWidgets.QPushButton('Create from joint chain(Single Only)')
        btn.clicked.connect(self.createFromJoint)
        layout = QtWidgets.QVBoxLayout(misc_grp)
        layout.addWidget(btn)
        # =====================================================================
        
        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(w)
        layout.addWidget(sel_grp)
        layout.addWidget(dup_grp)
        layout.addWidget(misc_grp)
        layout.addStretch()
        self.setWidgetResizable(True)
        self.setWidget(w)

    def convertSelection(self, toMesh):
        with node.DoCommand():
            sweepMesh.convertSelection(toMesh=toMesh)

    def convertSelectionToMesh(self):
        self.convertSelection(True)

    def convertSelectionToCurve(self):
        self.convertSelection(False)

    def selectEditing(self):
        with node.DoCommand():
            sweepMesh.selectEditing()

    def duplicate(self):
        with node.DoCommand():
            sweepMesh.duplicateHair()

    def duplicateAll(self):
        with node.DoCommand():
            sweepMesh.duplicateHairAll()
    
    def createFromJoint(self):
        with node.DoCommand():
            sweepMesh.createHairFromJointChain()


class HairCardsUtilities(QtWidgets.QScrollArea):
    def __init__(self, parent=None):
        super(HairCardsUtilities, self).__init__(parent)
        self.setWindowTitle('Poly Hair Cards')
        self.__is_refresh = True
        
        fb_grp = QtWidgets.QGroupBox('Flipbook')
        layout = QtWidgets.QVBoxLayout(fb_grp)
        opt_layout = QtWidgets.QHBoxLayout()
        l = QtWidgets.QLabel('Number of tiles')
        opt_layout.addWidget(l)
        widgets = []
        for value in (8, 2):
            w = uilib.Spiner()
            w.setRange(1, 99)
            w.setValue(value)
            w.valueChanged.connect(self.rebuildButtons)
            w.setPressedCallback(self.stopRefreshing)
            w.setReleasedCallback(self.startRefreshing)
            widgets.append(w)
            opt_layout.addWidget(w)
        self.__num_tiles = widgets
        layout.addLayout(opt_layout)
        
        self.__flipbook_ui = layout

        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(w)
        layout.addWidget(fb_grp)
        self.setWidgetResizable(True)
        self.setWidget(w)
        
        self.rebuildButtons()

    def stopRefreshing(self):
        self.__is_refresh = False

    def startRefreshing(self):
        self.__is_refresh = True
        self.rebuildButtons()

    def rebuildButtons(self):
        if not self.__is_refresh:
            return
        num_u, num_v = [x.value() for x in self.__num_tiles]
        item = self.__flipbook_ui.itemAt(1)
        if item:
            item.widget().hide()
            self.__flipbook_ui.removeWidget(item.widget())

        w = QtWidgets.QWidget()
        glayout = QtWidgets.QGridLayout(w)
        self.__flipbook_ui.addWidget(w)
        for v in range(num_v):
            for u in range(num_u):
                index = u + (v * num_u)
                button = QtWidgets.QPushButton(str(index))
                button.setSizePolicy(
                    QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
                )
                button.clicked.connect(self.update_flipbook)
                glayout.addWidget(button, (num_v - v + 1), u, 1, 1)

    def update_flipbook(self):
        cmds = sweepMesh.cmds
        index = int(self.sender().text())
        num_u, num_v = [x.value() for x in self.__num_tiles]
        sweepMesh.convertSelection(toMesh=True, isSelecting=True)
        selected = cmds.ls(sl=True)
        meshs = sweepMesh._get_mesh(selected)
        histories = cmds.listHistory(meshs, il=2, pdo=True) or []
        move_uvs = [x for x in histories if cmds.nodeType(x) == 'polyMoveUV']
        if not move_uvs:
            return
        move_uvs = node.toObjects(list(set(move_uvs)))
        uvSupporter.switchUvForFlipbook(index, num_u, num_v, move_uvs)


class PolyHairCreator(QtWidgets.QWidget):
    r"""
        モデルデータの作成、チェックを行う機能を提供するクラス
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(PolyHairCreator, self).__init__(parent)
        self.setWindowTitle('+Poly Hair Creator')
        
        tab = QtWidgets.QTabWidget()
        for w in (Creator, Utilities, HairCardsUtilities):
            widget = w()
            tab.addTab(widget, widget.windowTitle())
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(tab)


class MainGUI(uilib.AbstractSeparatedWindow):
    r"""
        メインとなるGUIを提供するクラス
    """
    def centralWidget(self):
        r"""
            中心となるメインウィジェットを作成して返す
            
            Returns:
                ModelSetupWidget:
        """
        return PolyHairCreator()


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。
        
        Returns:
            QtWidgets.QWidget:
    """
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(uilib.hires(380), uilib.hires(450))
    widget.show()
    return widget
