#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2024/10/07 15:46 Eske Yoshinob[eske3g@gmail.com]
        update:2024/10/17 17:56 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import lib, uilib, node
from ..uilib import mayaUIlib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore
cmds = node.cmds


class DraggingPlate(QtWidgets.QFrame):
    mousePressed = QtCore.Signal()
    mouseReleased = QtCore.Signal()
    valueChanged = QtCore.Signal(float, float)

    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(DraggingPlate, self).__init__(parent)
        self.setMinimumSize(200, 200)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        self.__bg_color = QtGui.QColor(120, 120, 120)
        self.__line_color = QtGui.QColor(82, 82, 82)
        self.__point_color = QtGui.QColor(20, 64, 250)
        self.__processing = False
        self.__point_pos = None
        self.__point_size = 14

    def setBgColor(self, color):
        r"""
            Args:
                color (QtGui.QColor):
        """
        self.__bg_color = color

    def setBgColorRGB(self, r, g, b):
        r"""
            Args:
                r (float):
                g (float):
                b (float):
        """
        self.setBgColor(QtGui.QColor(r, g, b))

    def bgColor(self):
        return self.__bg_color

    def setLineColor(self, color):
        r"""
            Args:
                color (QtGui.QColor):
        """
        self.__line_color = color

    def setLineColorRGB(self, r, g, b):
        r"""
            Args:
                r (float):
                g (float):
                b (float):
        """
        self.setLineColor(QtGui.QColor(r, g, b))
    
    def lineColor(self):
        return self.__line_color

    def setPointColor(self, color):
        r"""
            Args:
                color (any):
        """
        self.__point_color = color

    def setPointColorRGB(self, r, g, b):
        r"""
            Args:
                r (any):
                g (any):
                b (any):
        """
        self.setPointColor(QtGui.QColor(r, g, b))

    def pointColor(self):
        return self.__point_color

    def setPointSize(self, size):
        r"""
            Args:
                size (any):
        """
        self.__point_size = size

    def pointSize(self):
        return self.__point_size

    def emitPosition(self, pos):
        r"""
            Args:
                pos (QtCore.QPoint):
        """
        center = self.rect().center()
        ratio_h = (center.x() - pos.x()) / -center.x()
        ratio_v = (center.y() - pos.y()) / center.y()
        c_h = max(min(ratio_h, 1.0), -1.0)
        c_v = max(min(ratio_v, 1.0), -1.0)
        self.valueChanged.emit(c_h, c_v)
        self.__point_pos = pos

    def mousePressEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        if event.button() != QtCore.Qt.LeftButton:
            self.__processing = False
            self.__point_pos = None
            return
        self.__processing = True
        self.mousePressed.emit()
    
    def mouseMoveEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        if not self.__processing:
            return
        self.emitPosition(event.pos())
        self.update()

    def mouseReleaseEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        self.__point_pos = None
        self.mouseReleased.emit()
        self.update()
        if self.__processing:
            pass
        self.__processing = False

    def paintEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        rect = event.rect()
        painter = QtGui.QPainter(self)
        painter.setBrush(self.bgColor())
        painter.drawRect(event.rect())

        center = rect.center()
        hx = center.x()
        hy = center.y()
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.setPen(QtGui.QPen(self.lineColor(), 2))
        painter.drawLine(hx, rect.top(), hx, rect.bottom())
        painter.drawLine(rect.left(), hy, rect.right(), hy)

        if not self.__point_pos:
            return
        size = self.pointSize()
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(self.pointColor())
        painter.drawEllipse(self.__point_pos, size, size)
        

class LineOfSightEditor(QtWidgets.QWidget):
    nodeIsSet = QtCore.Signal(list)
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(LineOfSightEditor, self).__init__(parent)
        self.__rot_factor = [20, 20]
        plane = DraggingPlate()
        self.draggingStarted = plane.mousePressed
        self.valueChanged = plane.valueChanged
        self.draggingFinished = plane.mouseReleased
        for attr in ('bgColor', 'lineColor', 'pointColor'):
            setter = 'set' + attr[0].upper() + attr[1:]
            setter_rgb = setter + 'RGB'
            for at in (setter, attr, setter_rgb):
                setattr(self, at, getattr(plane, at))

        # UIにより動かされるターゲットの設定。
        label = QtWidgets.QLabel('Target Joints')
        self.__targets_le = QtWidgets.QLineEdit()
        pick_btn = uilib.OButton()
        pick_btn.setIcon(uilib.IconPath('uiBtn_select'))
        pick_btn.setBgColor(70, 120, 165)
        pick_btn.clicked.connect(self.setNodesBySelected)

        # 動かされるターゲットの角度設定。
        angle_set = uilib.ClosableGroup('Angle Settings')
        angle_set.setIcon(uilib.IconPath('uiBtn_fixOrientation'))
        layout = QtWidgets.QGridLayout(angle_set)
        self.__angle_settings = []
        keys = [['Up', 'Down'], ['Left', 'Right']]
        for i, orientation in enumerate(('vertical', 'horizontal')):
            for j, direction in enumerate(keys[i]):
                key = orientation + direction
                l = QtWidgets.QLabel(lib.title(key))
                angle_ui = QtWidgets.QDoubleSpinBox()
                angle_ui.setRange(1, 90)
                angle_ui.setValue(20)
                angle_ui.setButtonSymbols(QtWidgets.QDoubleSpinBox.NoButtons)
                angle_ui.setMinimumWidth(5)
                layout.addWidget(l, i, j*2, 1, 1)
                layout.addWidget(angle_ui, i, j*2+1, 1, 1)
                self.__angle_settings.append(angle_ui)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(3, 1)

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(label, 0, 0, 1, 1)
        layout.addWidget(self.__targets_le, 0, 1, 1, 1)
        layout.addWidget(pick_btn, 0, 2, 1, 1)
        layout.addWidget(angle_set, 1, 0, 1, 3)
        layout.addWidget(plane, 2, 0, 1, 3)
        layout.setRowStretch(2, 1)
        layout.setColumnStretch(1, 1)
        
        angle_set.setExpanding(False)
        self.setAngleSettingExpanding = angle_set.setExpanding

    def setRotationFactor(self, vFactorUp, vFactorDown, hFactorL, hFactorR):
        r"""
            Args:
                vFactorUp (float):
                vFactorDown (float):
                hFactorL (float):
                hFactorR (float):
        """
        vlist = [vFactorUp, vFactorDown, hFactorL, hFactorR]
        for i in range(len(vlist)):
            self.__angle_settings[i].setValue(vlist[i])

    def rotationFactor(self):
        return [x.value() for x in self.__angle_settings]

    def setNodes(self, nodelist):
        r"""
            Args:
                nodelist (list):
        """
        text = ','.join(nodelist)
        self.__targets_le.setText(text)
        self.nodeIsSet.emit(nodelist)

    def nodes(self):
        nodelist = [x.strip() for x in self.__targets_le.text().split(',')]
        return nodelist

    def setNodesBySelected(self):
        self.setNodes(cmds.ls(sl=True, type='transform'))


class RelatedTargetEditor(uilib.ClosableGroup):
    Keys = ('verticalUp', 'verticalDown', 'horizontalLeft', 'horizontalRight')
    Side = 'LR'
    dataWasChanged = QtCore.Signal(int, str, list)

    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(RelatedTargetEditor, self).__init__('Related Target', parent)
        self.setIcon(uilib.IconPath('uiBtn_reference'))
        self.__relation_uis = {}
        layout = QtWidgets.QFormLayout(self)
        for i, l in enumerate(self.Keys):
            for side in self.Side:
                w = QtWidgets.QLineEdit()
                w.key_index = i
                w.side = side
                w.editingFinished.connect(self.emitEditingSignal)
                layout.addRow(lib.title(l+side), w)
                self.__relation_uis[l+side] = w

    def _setData(self, keyIndex, side, targetAttrList):
        r"""
            Args:
                keyIndex (int):
                targetAttrList (list):
        """
        ui = self.__relation_uis[self.Keys[keyIndex]+side]
        text = ','.join(targetAttrList)
        ui.setText(text)
        self.dataWasChanged.emit(keyIndex, side, targetAttrList)

    def _getData(self, keyIndex, side):
        r"""
            Args:
                keyIndex (int):
        """
        text = self.__relation_uis[self.Keys[keyIndex]+side].text()
        return [x.strip() for x in text.split(',')]

    def setVerticalUp(self, side, targetAttrList):
        r"""
            Args:
                targetAttrList (list):
        """
        self._setData(0, side, targetAttrList)

    def verticalUpAttrList(self, side):
        return self._getData(0, side)

    def setVerticalDown(self, side, targetAttrList):
        r"""
            Args:
                targetAttrList (list):
        """
        self._setData(1, side, targetAttrList)

    def verticalDownAttrList(self, side):
        return self._getData(1, side)

    def setHorizontalLeft(self, side, targetAttrList):
        r"""
            Args:
                targetAttrList (list):
        """
        self._setData(2, side, targetAttrList)
    
    def horizontalLeftAttrList(self, side):
        return self._getData(2, side)
    
    def setHorizontalRight(self, side, targetAttrList):
        r"""
            Args:
                targetAttrList (list):
        """
        self._setData(3, side, targetAttrList)

    def horizontalRightAttrList(self, side):
        return self._getData(2, side)
    
    def allAttrList(self):
        return [
            self._getData(x, y) for x in range(4) for y in self.Side
        ]

    def emitEditingSignal(self):
        sender = self.sender()
        data = self._getData(sender.key_index, sender.side)
        self.dataWasChanged.emit(sender.key_index, sender.side, data)


class LineOfSightManager(QtWidgets.QWidget):
    def  __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(LineOfSightManager, self).__init__(parent)
        self.__targets = []
        self.__related_attrs = []
        self.setWindowTitle('Linf of sight editor')

        # 視線コントローラ
        self.__editor = LineOfSightEditor()
        for attr in (
            'setNodes', 'nodes', 'setRotationFactor', 'rotationFactor'
        ):
            setattr(self, attr, getattr(self.__editor, attr))
        self.nodeIsSet = self.__editor.nodeIsSet
        self.__editor.draggingStarted.connect(self.setupRotation)
        self.__editor.valueChanged.connect(self.rotateNodes)
        self.__editor.draggingFinished.connect(self.terminateRotation)

        # 視線追従に関連するアトリビュートリスト
        self.__related_tgt = RelatedTargetEditor()
        for key in RelatedTargetEditor.Keys:
            base_attr = key[0].upper() + key[1:]
            for attr in ('set' + base_attr, key + 'AttrList'):
                setattr(self, attr, getattr(self.__related_tgt, attr))
        self.relationTargetWasChanged = self.__related_tgt.dataWasChanged
        self.__related_tgt.setExpanding(False)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.__editor)
        layout.addWidget(self.__related_tgt)

    def setTargets(self, targetlist=None):
        r"""
            Args:
                targetlist (list):
        """
        if not targetlist:
            targetlist = []
        self.__targets = targetlist

    def targets(self):
        return self.__targets

    def editor(self):
        return self.__editor

    def relatedTargetEditor(self):
        return self.__related_tgt
    
    def relatedAllAttrs(self):
        all_attrs = []
        for attrs in self.relatedTargetEditor().allAttrList():
            data = []
            for attr in attrs:
                if not attr:
                    continue
                name, attr_name = attr.split('.', 1)
                n = node.asObject(name)
                if not n:
                    continue
                try:
                    at = n.attr(attr_name)
                except Exception as e:
                    print('[Attribute Detection Error] : {}'.format(e.args[0]))
                    continue
                data.append(at)
            all_attrs.append(data)
        return all_attrs

    def setRelatedValues(self, valuelist):
        r"""
            視線の回転に合わせて連動するアトリビュートに変更を加える。
            引数valuelistは4つのfloatを含むリストで
                [0] 縦上方向の移動量
                [1] 縦下方向の移動量
                [2] 右方向の移動量
                [3] 左方向の移動量
            の順に、0～１の範囲の値を持つ。

            Args:
                valuelist (list):
        """
        if not self.__related_attrs:
            return
        for attrs, value in zip(self.__related_attrs, valuelist):
            for attr in attrs:
                attr.set(value)        

    def setupRotation(self):
        targets = node.toObjects(self.nodes())
        self.setTargets()
        self.__related_attrs = []
        for tgt in targets:
            if not tgt:
                return False
        self.setTargets([[x, x.matrix(False)] for x in targets])
        self.__related_attrs = self.relatedAllAttrs()
        cmds.undoInfo(openChunk=True)
        return True

    def calcRotation(self,
        h, v, horizontalFactor, verticalFactor,
        target, initialMatrix
    ):
        r"""
            任意の対象ノードtargetに対する回転値の計算を行い結果を返す。
            デフォルトでは
                h * horizontalFactor
                v * verticalFactor
                target
                initialMatrix
            が返される。
            戻り値のそれぞれの内容は
                最初の戻り値は横方向の回転角度（float / degree)
                2つ目は縦方向の回転角度（float / degree)
                3つ目の戻り値は回転対称となるノード
                4つ目は回転対称が回転前に取る姿勢を表す行列
            となる。

            Args:
                h (float):
                v (float):
                horizontalFactor (float):
                verticalFactor (float):
                target (node.Transform):
                initialMatrix (list):
            
            Returns:
                tuple: 横回転値(float),縦回転値(float), ノード(Transform),行列
        """
        return h * horizontalFactor, v * verticalFactor, target, initialMatrix

    def rotateNodes(self, h, v):
        r"""
            Args:
                h (float):
                v (float):
        """
        targets = self.targets()
        if not targets:
            return
        vu, vd, hl, hr = self.rotationFactor()
        attr_values = [0, 0, 0, 0]
        if h > 0:
            attr_values[2] = abs(h)
            hf = hl
        else:
            attr_values[3] = abs(h)
            hf = hr
        if v > 0:
            attr_values[0] = abs(v)
            vf = -vu
        else:
            attr_values[1] = abs(v)
            vf = -vd
        for tgt, mtx in targets:
            rot_h, rot_v, tgt, mtx = self.calcRotation(h, v, hf, vf, tgt, mtx)
            tgt.setMatrix(mtx, False)
            cmds.rotate(rot_v, rot_h, 0, tgt, r=True, ws=True, fo=True)

        # 視線追従アトリビュートの設定
        self.setRelatedValues([x for x in attr_values for y in 'LR'])

    def terminateRotation(self):
        self.setRelatedValues([0, 0, 0, 0, 0, 0, 0, 0])
        if not self.targets():
            return
        for tgt, mtx in self.targets():
            tgt.setMatrix(mtx, False)
        self.setTargets()
        cmds.undoInfo(closeChunk=True)


class MainGUI(uilib.AbstractSeparatedWindow):
    r"""
        独立ウィンドウ式のBlendShapeUtilを提供する。
    """
    def centralWidget(self):
        r"""
            Returns:
                BlendShapeUtil:
        """
        return LineOfSightManager()


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。
        
        Returns:
            MainGUI:
    """
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(400, 420)
    widget.show()
    return widget





'''
# EX.
from importlib import reload
import traceback
try:
    #from gris3.tools import drivers
    #reload(drivers)
    #drv = drivers.createEyeDriver('leftEye_eyeDrv', 'J_L_eye')
    from gris3.gadgets import lineOfSightManager
    reload(lineOfSightManager)
    w = lineOfSightManager.showWindow()
    m = w.main()
    m.setNodes(['J_L_eye', 'J_R_eye'])
    m.setVerticalUp('L', ['facial_bs.eyeLookUpLeft'])
    m.setVerticalUp('R', ['facial_bs.eyeLookUpRight'])
    m.setVerticalDown('L', ['facial_bs.eyeLookDownLeft'])
    m.setVerticalDown('R', ['facial_bs.eyeLookDownRight'])
    m.setHorizontalLeft('L', ['facial_bs.eyeLookOutLeft'])
    m.setHorizontalLeft('R', ['facial_bs.eyeLookOutRight'])
    m.setHorizontalRight('L', ['facial_bs.eyeLookInLeft'])
    m.setHorizontalRight('R', ['facial_bs.eyeLookInRight'])
except:
    traceback.print_exc()
'''