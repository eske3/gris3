#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    コントローラ用カーブシェイプの形状を作成、編集する機能を提供する。
    
    Dates:
        date:2017/06/15 16:35[Eske](eske3g@gmail.com)
        update:2020/06/13 06:10 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import uilib, lib, node
from ..uilib import colorPicker
from ..tools import curvePrimitives
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class CurveView(QtWidgets.QListView):
    r"""
        カーブの一覧を表示するビューを提供するクラス
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(CurveView, self).__init__(parent)
        self.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setIconSize(QtCore.QSize(uilib.hires(48), uilib.hires(48)))

    def copySelectedTypeToClipboard(self, withQuotation=False):
        r"""
            選択されたカーブタイプ名をクリップボードにコピーする
            Args:
                withQuotation (bool):テキストの前後のクォーテーションをつける
        """
        data = [x.data(QtCore.Qt.UserRole+1) for x in self.selectedIndexes()]
        if not data:
            return
        text = "'{}'".format(data[0] if withQuotation else data[0])
        QtWidgets.QApplication.clipboard().setText(text)

    def keyPressEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        key = event.key()
        mod = event.modifiers()
        if key == QtCore.Qt.Key_C:
            if mod == QtCore.Qt.ControlModifier:
                self.copySelectedTypeToClipboard()
                return
            elif mod == QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier:
                self.copySelectedTypeToClipboard(True)
                return
        super(CurveView, self).keyPressEvent(event)


class CommandPreview(QtWidgets.QGroupBox):
    r"""
        コンストラクタで使用できる、カーブを生成するためのコマンドを表示する
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(CommandPreview, self).__init__('Command Preview', parent)
        field = QtWidgets.QTextEdit()
        field.setReadOnly(True)
        btn = QtWidgets.QPushButton('Show Command Preview')
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(field)
        layout.addWidget(btn)
        self.__field = field
        self.buttonClicked = btn.clicked

    def setText(self, text):
        r"""
            フィールドにテキストを表示する
            Args:
                text (str):表示するテキスト
        """
        self.__field.setPlainText(text)


class CtrlCurveToolWidget(QtWidgets.QSplitter):
    r"""
        コントローラ用のカーブにまつわる機能を提供するGUI。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(CtrlCurveToolWidget, self).__init__(parent)
        self.setWindowTitle('+ Controller Curve Tool')

        model = QtGui.QStandardItemModel(0, 1)
        self.__view = CurveView()
        self.__view.setModel(model)
        
        # 編集機能。===========================================================
        editor = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout(editor)
        layout.setContentsMargins(2, 2, 2, 2)
        i = 0
        for icon, tip, func in (
            (
                'uiBtn_plus',
                'Create new curve from the selected in the side list.',
                self.createNewCurve
            ),
            (
                'uiBtn_extractFace',
                (
                    'Replace shape to selected curves '
                    'with a selected in the side list.'
                ),
                self.replaceShape
            ),
        ):
            btn = uilib.OButton(uilib.IconPath(icon))
            btn.setToolTip(tip)
            btn.setSize(32)
            btn.clicked.connect(func)
            layout.addWidget(btn, 0, i, 1, 1, QtCore.Qt.AlignLeft)
            i+=1

        #作成オプション。------------------------------------------------------
        grp = QtWidgets.QGroupBox('Create Option')
        opt_layout = QtWidgets.QFormLayout(grp)

        self.__translations = []
        for label, default in (
            ('offset', (0, 0, 0)), ('rotation', (0, 0, 0)), ('scale', (1, 1, 1))
        ):
            w = QtWidgets.QWidget()
            l = QtWidgets.QHBoxLayout(w)
            l.setContentsMargins(0, 0, 0, 0)
            l.setSpacing(2)
            fields = []
            for i in default:
                b = QtWidgets.QDoubleSpinBox()
                b.setRange(-1000000000, 1000000000)
                b.setValue(i)
                b.setButtonSymbols(QtWidgets.QDoubleSpinBox.NoButtons)
                b.setMinimumSize(
                    40, b.minimumSize().height()
                )
                fields.append(b)
                l.addWidget(b)
            self.__translations.append([x.value for x in fields])
            opt_layout.addRow(label, w)
        # ---------------------------------------------------------------------
        
        # ---------------------------------------------------------------------
        self.__color_picker = colorPicker.ColorPickerWidget()
        self.__color_picker.setColorRgb([0.164, 0.34, 0.865])
        opt_layout.addRow('Color', self.__color_picker)
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        self.__preview = CommandPreview()
        self.__preview.buttonClicked.connect(self.makeCommandPreview)
        # ---------------------------------------------------------------------

        layout.setSpacing(1)
        layout.addWidget(grp, 1, 0, 1, i+1)
        layout.addWidget(self.__preview, 2, 0, 1, i+1)
        layout.setRowStretch(2, 1)
        layout.setColumnStretch(i, 1)
        # =====================================================================

        self.addWidget(self.__view)
        self.addWidget(editor)
        self.setSizes([uilib.hires(120), uilib.hires(200)])
        self.setStretchFactor(1, 1)

    def view(self):
        r"""
            ビューを返す
            
            Returns:
                CurveView:
        """
        return self.__view

    def loadCurves(self):
        r"""
            ビューを更新する
        """
        model = self.view().model()
        model.removeRows(0, model.rowCount())
        for typ in sorted(curvePrimitives.CurveTypeList):
            item = QtGui.QStandardItem(lib.title(typ))
            item.setData(typ)
            model.setItem(model.rowCount(), 0, item)

    def getCreator(self):
        r"""
            UI上の設定に基づいたPrimitiveCreatorを返す
            
            Returns:
                curvePrimitives.PrimitiveCreator:
        """
        indexes = self.view().selectedIndexes()
        if not indexes:
            return
        creator = curvePrimitives.PrimitiveCreator()
        creator.setCurveType(indexes[0].data(QtCore.Qt.UserRole+1))
        for method, values in zip(
            ('setTranslation', 'setRotation', 'setSizes'),
            self.__translations
        ):
            m = getattr(creator, method)
            m([x() for x in values])
        creator.setColorIndex(self.__color_picker.colorRgb())
        return creator

    def createNewCurve(self):
        r"""
            選択アイテムのカーブを作成する
        """
        creator = self.getCreator()
        if not creator:
            return
        with node.DoCommand():
            creator.create()

    def replaceShape(self):
        r"""
            既存のCurveシェイプをこのウィジェットの内容に置き換える。
        """
        creator = self.getCreator()
        if not creator:
            return
        with node.DoCommand():
            creator.replace()

    def makeCommandPreview(self):
        r"""
            コンストラクタで使用出来るコマンドを生成する
        """
        indexes = self.view().selectedIndexes()
        if not indexes:
            return
        lines = [
            'sc = self.shapeCreator()',
            "sc.setCurveType('%s')" % indexes[0].data(QtCore.Qt.UserRole+1)
        ]
        for method, values, default in zip(
            ('setTranslation', 'setRotation', 'setSizes'),
            self.__translations,
            (0, 0, 1)
        ):
            valuelist = [x() for x in values]
            if [x for x in valuelist if x != default]:
                v = '(%s)' % ', '.join([str(x) for x in valuelist])
            else:
                v = ''
            if method == 'setSizes' and v and len(set(valuelist)) == 1:
                method = 'setSize'
                v = valuelist[0]
            lines.append('sc.%s(%s)' % (method, v))
        color = self.__color_picker.colorText()
        lines.append('sc.setColorIndex((%s))'%color)
        self.__preview.setText('\n'.join(lines))


class ControllerMirror(uilib.ClosableGroup):
    r"""
        コントローラをミラーコピーする機能を提供するクラス。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ControllerMirror, self).__init__('Mirror Curve', parent)
        self.setIcon(uilib.IconPath('uiBtn_mirror'))

        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(2)
        for data in (
            (
                self.mirrorByName,
                'Mirror selected controller curve.',
                (11, 68, 128), 'uiBtn_mirror'
            ),
            (
                self.mirror,
                (
                    'Mirror selected controller curve '
                    "from odd number's to even number's."
                    'Select source then select destination.'
                ),
                (64, 45, 128), 'uiBtn_mirror'
            ),

        ):
            if isinstance(data, int):
                layout.addSpacing(data)
                continue
            cmd, tooltip, color, icon = data
            btn = uilib.OButton()
            btn.setToolTip(tooltip)
            btn.setBgColor(*color)
            btn.setIcon(uilib.IconPath(icon))
            btn.setSize(38)
            btn.clicked.connect(cmd)
            layout.addWidget(btn)
        layout.addStretch()

    def mirrorByName(self):
        r"""
            名前を基準にLからR(もしくは逆)へカーブの形状をミラー
        """
        with node.DoCommand():
            curvePrimitives.mirrorCurveByName()

    def mirror(self):
        r"""
            選択ノードを基準にLからR(もしくは逆)へカーブの形状をミラー
        """
        with node.DoCommand():
            curvePrimitives.mirrorCurve()


class ShapeEditor(uilib.ClosableGroup):
    r"""
        カーブの形状を編集する機能を持つGUIを提供するクラス
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ShapeEditor, self).__init__('Edit Shape', parent)
        self.setIcon(uilib.IconPath('uiBtn_toolBox'))

        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(2)
        for data in (
            (
                self.transfer,
                (
                    'Transfer controler shape from first to second '
                    'in the current selection.'
                ),
                (11, 68, 128), 'uiBtn_extractFace'
            ),
        ):
            if isinstance(data, int):
                layout.addSpacing(data)
                continue
            cmd, tooltip, color, icon = data
            btn = uilib.OButton()
            btn.setToolTip(tooltip)
            btn.setBgColor(*color)
            btn.setIcon(uilib.IconPath(icon))
            btn.setSize(38)
            btn.clicked.connect(cmd)
            layout.addWidget(btn)

        layout.addStretch()

    def transfer(self):
        r"""
            最初に選択したカーブ形状を次に選択したカーブへ移植する
        """
        with node.DoCommand():
            curvePrimitives.transferCurveShape()


class WireColorPicker(colorPicker.ColorPickerWidget):
    def showColorPicker(self):
        selected_color = None
        for n in node.selected():
            for crv in node.getShapes(n, 'nurbsCurve'):
                if not crv.hasAttr(curvePrimitives.CurveColorAttr):
                    continue
                selected_color = crv(curvePrimitives.CurveColorAttr)
                break
            if selected_color:
                break
        pre_color = self.colorRgb()
        if selected_color:
            self.setColorRgb(selected_color[0])
        result = super(WireColorPicker, self).showColorPicker()
        if not result:
            self.setColorRgb(pre_color)
        return result


class ApperanceEditor(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(ApperanceEditor, self).__init__('Apperance', parent)
        # ラインの太さ編集
        linewidth = QtWidgets.QWidget()
        self.__linewidth = uilib.DoubleSpiner()
        self.__linewidth.setRange(-1, 100)
        self.__linewidth.setValue(3)
        btn = uilib.OButton(uilib.IconPath('uiBtn_play'))
        btn.clicked.connect(self.applyLineWidth)
        layout = QtWidgets.QHBoxLayout(linewidth)
        layout.addWidget(self.__linewidth)
        layout.addWidget(btn)
        
        # 色編集
        color_picker = WireColorPicker()
        color_picker.setColorRgb([0.164, 0.34, 0.865])
        color_picker.setColorAsFloat(True)
        color_picker.colorIsSet.connect(self.applyColor)
        
        layout = QtWidgets.QFormLayout(self)
        layout.addRow('Line Width', linewidth)
        layout.addRow('Line Color', color_picker)

    def applyLineWidth(self):
        line_width = self.__linewidth.value()
        if line_width < 0:
            line_width = -1
        with node.DoCommand():
            curvePrimitives.applyLineWidth(line_width)

    def applyColor(self, r, g, b):
        from importlib import reload
        reload(curvePrimitives)
        with node.DoCommand():
            curvePrimitives.applyWireColor((r, g, b))


class ControllerShapeEditor(QtWidgets.QWidget):
    r"""
        カーブの作成、編集を行うためのツールを提供するクラス。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ControllerShapeEditor, self).__init__(parent)
        self.setWindowTitle('+Controller Shape Editor')
        mirror = ControllerMirror()
        editor = ShapeEditor()
        apperance = ApperanceEditor()
        self.__tool = CtrlCurveToolWidget()

        layout = QtWidgets.QGridLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(mirror, 0, 0, 1, 1, QtCore.Qt.AlignTop)
        layout.addWidget(editor, 0, 1, 1, 1, QtCore.Qt.AlignTop)
        layout.addWidget(apperance, 0, 2, 1, 1)
        layout.addWidget(self.__tool, 1, 0, 1, 3)
        layout.setRowStretch(1, 1)
        layout.setColumnStretch(2, 1)
        # layout.setStretchFactor(self.__tool, 1)
        
        self.loadCurves()

    def loadCurves(self):
        r"""
            カーブをロードする
        """
        self.__tool.loadCurves()


class MainGUI(uilib.AbstractSeparatedWindow):
    r"""
        単独ウィンドウとして表示されるウィンドウ。
    """
    def centralWidget(self):
        r"""
            センターに登録するウィジェットを作成して返す
            
            Returns:
                ControllerShapeEditor:
        """
        return ControllerShapeEditor()


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。
        
        Returns:
            MainGUI:
    """
    from gris3.uilib import mayaUIlib
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(300, 480)
    widget.main().loadCurves()
    widget.show()
    return widget