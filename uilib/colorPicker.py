#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2020/06/12 13:49 eske yoshinob[eske3g@gmail.com]
        update:2025/11/08 17:49 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2020 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import uilib, style
from . import mayaUIlib
MainWindow = mayaUIlib.MainWindow
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class ColorSlider(QtWidgets.QWidget):
    valueChanged = QtCore.Signal(float)
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ColorSlider, self).__init__(parent)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        self.resize(style.scaled(200), style.scaled(15))
        self.__gradient = QtGui.QLinearGradient()
        self.setValue(0)

    def setValue(self, value):
        r"""
            スライダーの値を設定する。
            
            Args:
                value (float):0~1
        """
        if value < 0:
            value = 0
        elif value > 1:
            value = 1
        self.__value = value
        self.update()

    def value(self):
        r"""
            スライダーの値を返す。
            
            Returns:
                float:0~1
        """
        return self.__value

    def setValueFromCursor(self, position):
        r"""
            GUIの幅に対する任意の位置の割合を値として設定する。
            valueChangedシグナルを送出する。
            
            Args:
                position (int):
        """
        value = float(position) / self.rect().width()
        self.setValue(value)
        self.valueChanged.emit(value)

    def setColor(self, position, rgb):
        r"""
            グラデーションのカラーを設定する
            
            Args:
                position (float):設定する色の位置
                rgb (list):RGBの３色(0.0~1.0)の値を持つlist
        """
        color = QtGui.QColor()
        color.setRgbF(*rgb)
        self.__gradient.setColorAt(position, color)

    def sizeHint(self):
        r"""
            Returns:
                QtCore.QSize:
        """
        return self.rect().size()

    def mousePressEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        self.setValueFromCursor(event.pos().x())

    def mouseMoveEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        self.setValueFromCursor(event.pos().x())

    def paintEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        rect = self.rect()
        # ベース部分の描画。===================================================
        painter = QtGui.QPainter(self)
        painter.setRenderHints(QtGui.QPainter.RenderHint.Antialiasing)
        pen = QtGui.QPen()
        pen.setColor(QtGui.QColor(0, 0, 0))
        painter.setPen(pen)
        self.__gradient.setFinalStop(rect.width(), 0)
        painter.setBrush(self.__gradient)
        painter.drawRoundedRect(rect, style.scaled(4), style.scaled(4))
        # =====================================================================

        # カーソルの描画。=====================================================
        painter.setRenderHints(QtGui.QPainter.RenderHint.Antialiasing, 0)
        painter.setBrush(QtCore.Qt.NoBrush)
        pos = rect.width() * self.value()
        rect.setWidth(style.scaled(5))
        rect.setHeight(rect.height()-1)
        center = QtCore.QPoint(pos, rect.height()*0.5)
        rect.moveCenter(center)
        painter.drawRect(rect)
        
        rect.setWidth(style.scaled(3))
        rect.moveCenter(center)
        pen.setColor(QtGui.QColor(255, 255, 255))
        painter.setPen(pen)
        painter.drawRect(rect)
        # =====================================================================


class ColorSliderGroup(QtWidgets.QGroupBox):
    r"""
        3色分のカラースライダーによる色変更GUIを提供するクラス
    """
    valueChanged = QtCore.Signal(list)
    def __init__(self, label='', parent=None):
        r"""
            Args:
                label (str):グループの枠に指定するラベルのテキスト
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ColorSliderGroup, self).__init__(label, parent)
        self.__is_emitting = True
        layout = QtWidgets.QGridLayout(self)
        gui = []
        factor = {
            QtCore.Qt.LeftButton : 0.01,
            QtCore.Qt.MiddleButton : 0.1,
            QtCore.Qt.RightButton  : 1.0,
        }
        for i in range(3):
            # ラベル
            label = QtWidgets.QLabel()
            
            # スライダー
            slider = ColorSlider()
            
            # 数値フィールド
            field = uilib.DoubleSpiner()
            field.ButtonFactor = factor
            field.setSingleStep(0.01)
            field.setDecimals(3)
            field.setRange(0, 1)
            
            # シグナルの設定。
            slider.valueChanged.connect(field.setValue)
            slider.valueChanged.connect(self.emitValues)
            field.valueChanged.connect(slider.setValue)
            field.valueChanged.connect(self.emitValues)

            layout.addWidget(label, i, 0, 1, 1)
            layout.addWidget(field, i, 1, 1, 1)
            layout.addWidget(slider, i, 2, 1, 1)
            gui.append((label, field, slider))
        layout.setRowStretch(3, 1)
        self.__sliders = gui

    def setLabel(self, index, label):
        r"""
            カラースライダーのラベルを設定する
            
            Args:
                index (int):スライダーの番号
                label (str):設定するテキスト
        """
        self.__sliders[index][0].setText(label)

    def setColor(self, index, position, rgb):
        r"""
            Args:
                index (int):スライダーの番号
                position (float):設定する色の位置
                rgb (list):RGBの３色(0.0~1.0)の値を持つlist
        """
        self.__sliders[index][2].setColor(position, rgb)

    def values(self):
        r"""
            3つのスライダーにリストで返す。
            
            Returns:
                list(float, float, float):
        """
        return [x[1].value() for x in self.__sliders]

    def setValues(self, value1, value2, value3):
        r"""
            3つのスライダーに値をまとめて設定する。
            
            Args:
                value1 (float):
                value2 (float):
                value3 (float):
        """
        self.__is_emitting = False
        for slider, value in zip(
            self.__sliders, (value1, value2, value3)
        ):
            slider[1].setValue(value)
            slider[2].setValue(value)
        self.__is_emitting = True

    def emitValues(self, *args):
        r"""
            スライダ－の値が変更されたときに呼ばれる。
            valueChangedシグナルを送出する。
            
            Args:
                *args (tuple):何らかの引数受け取り用
        """
        if not self.__is_emitting:
            return
        values = [x[2].value() for x in self.__sliders]
        self.valueChanged.emit(values)


class HsvSliderGroup(ColorSliderGroup):
    r"""
        HSV用カラースライダのGUIを提供するクラス。
        HSVスライダを変更した際にSとVのスライダの背景色が変化する。
    """
    def __init__(self, label='', parent=None):
        r"""
            Args:
                label (str):グループの枠に指定するラベルのテキスト
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(HsvSliderGroup, self).__init__(label, parent)
        self.__gamma = 1.0

    def setGamma(self, gamma):
        r"""
            ガンマ値を設定する
            
            Args:
                gamma (float):
        """
        self.__gamma = gamma
        self.updateSliderGradient()

    def gamma(self, forCalc=False):
        r"""
            設定されているガンマ値を返す
            
            Args:
                forCalc (bool):ガンマ値を計算用に変換してから返すかどうか
        """
        return 1.0/self.__gamma if forCalc else self.__gamma
        
    def updateSliderGradient(self):
        r"""
            スライダの背景色を更新する。
        """
        color = QtGui.QColor()
        color.setHsvF(*self.values())
        gamma = self.gamma(True)
        h, s, v = color.hueF(), color.saturationF(), color.valueF()

        getcolor = lambda x : [
            y**gamma for y in (x.redF(), x.greenF(), x.blueF())
        ]
        # 彩度スライダの更新
        for i in range(11):
            f = i*0.1
            color.setHsvF(h, f, v)
            self.setColor(1, f, getcolor(color))
        
        # 明度スライダの更新
        for i in range(11):
            f = i*0.1
            color.setHsvF(h, s, f)
            self.setColor(2, f, getcolor(color))
        self.update()

    def setValues(self, value1, value2, value3):
        r"""
            3つのスライダーに値をまとめて設定する。
            
            Args:
                value1 (float):
                value2 (float):
                value3 (float):
        """
        super(HsvSliderGroup, self).setValues(value1, value2, value3)
        self.updateSliderGradient()

    def emitValues(self, *args):
        r"""
            スライダ－の値が変更されたときに呼ばれる。
            valueChangedシグナルを送出する。
            
            Args:
                *args (tuple):何らかの引数受け取り用
        """
        self.updateSliderGradient()
        super(HsvSliderGroup, self).emitValues(*args)


class RgbSliderGroup(HsvSliderGroup):
    r"""
        RGB用カラースライダのGUIを提供するクラス。
        RGBスライダを変更した際にスライダの背景色が変化する。
    """
    def updateSliderGradient(self):
        r"""
            スライダの背景色を更新する。
        """
        r, g, b = self.values()
        gamma = self.gamma(True)

        getcolor = lambda x : [y**gamma for y in x]
        for i in range(3):
            colorlist = [r, g, b]
            for j in range(11):
                f = j*0.1
                colorlist[i] = f
                self.setColor(i, f, getcolor(colorlist))
        self.update()


class ColorPalette(QtWidgets.QWidget):
    r"""
        色を表示する矩形GUIを提供するクラス。
        また、表示色をテキストとしてコピーする事も可能。
    """
    clicked = QtCore.Signal(list)
    rightButtonClicked = QtCore.Signal()
    AsRgb, AsHsv, AsHex = range(3)
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ColorPalette, self).__init__(parent)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        self.setFocusPolicy(QtCore.Qt.WheelFocus)
        self.setToolTip(
            'Press Ctrl+C key copies a current color as rgb value text,\n'
            'Press Ctrl+Shift+C key copies a current color as color name,\n'
            'Press Ctrl+Alt+C key copies a current color as hsv value text.'
        )
        self.__color = None
        self.__gamma = 1.0
        self.resize(style.scaled(15), style.scaled(15))

    def setGamma(self, gamma):
        r"""
            ガンマ値を設定する
            
            Args:
                gamma (float):
        """
        self.__gamma = gamma
        self.update()

    def gamma(self, forCalc=False):
        r"""
            設定されているガンマ値を返す
            
            Args:
                forCalc (bool):ガンマ値を計算用に変換してから返すかどうか
        """
        return 1.0/self.__gamma if forCalc else self.__gamma

    def setColor(self, color):
        r"""
            パレットの色を変更する
            
            Args:
                color (QtGui.QColor):
        """
        self.__color = color
        self.update()

    def color(self):
        r"""
            設定されているパレットの色を返す
            
            Returns:
                QtGui.QColor:
        """
        return self.__color

    def setColorRgb(self, rgb):
        r"""
            パレットの色を変更する。引数は0~1レンジのRGBの値を持つリスト
            
            Args:
                rgb (list):
        """
        color = QtGui.QColor()
        color.setRgbF(*rgb)
        self.setColor(color)

    def colorRgb(self):
        r"""
            設定されているパレットの色を返す
            
            Returns:
                list(float, float, float):RGBの３色の値を持つリスト
        """
        color = self.color()
        if not color:
            return []
        return [color.redF(), color.greenF(), color.blueF()]


    def colorText(self, mode=0):
        r"""
            現在表示している色をテキスト化して返す
            
            Args:
                mode (int):AsRgbかAsHsvかAsHex
        """
        color = self.color()
        if not color:
            return []
        if mode == self.AsHex:
            return color.name()
        if mode == self.AsHsv:
            attrs = ('hueF', 'saturationF', 'valueF')
        else:
            attrs = ('redF', 'greenF', 'blueF')
        clamp = lambda x : str(round(0 if x < 0 else 1 if x > 1 else x, 3))
        colors = [clamp(getattr(color, x)()) for x in attrs]
        return ', '.join(colors)

    def copyColor(self, mode=0):
        r"""
            現在表示している色をテキストとしてクリップボードに書き出す。
            
            Args:
                mode (int):AsRgbかAsHsvかAsHex
        """
        text = self.colorText(mode)
        if not text:
            return
        QtWidgets.QApplication.clipboard().setText(text)
        print('Copy color in the clipboard as text : %s' % text)
        
    def sizeHint(self):
        r"""
            Returns:
                QtCore.QSize:
        """
        return self.rect().size()

    def paintEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        painter = QtGui.QPainter(self)
        painter.setRenderHints(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setPen(QtGui.QPen())

        rect = self.rect()
        rgb = self.colorRgb()
        if rgb:
            g = self.gamma(True)
            color = QtGui.QColor()
            color.setRgbF(*[x**g for x in rgb])
            painter.setBrush(color)
            painter.drawRoundedRect(rect, style.scaled(4), style.scaled(4))
            return
        # 色が設定されていない場合は斜線表示。
        painter.setBrush(QtGui.QColor(255, 255, 255))
        painter.drawRect(rect)
        painter.setBrush(QtCore.Qt.NoBrush)
        painter.drawLine(rect.topLeft(), rect.bottomRight())

    def mousePressEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        super(ColorPalette, self).mousePressEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit(self.colorRgb())
        else:
            self.rightButtonClicked.emit()

    def keyPressEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        key = event.key()
        mod = event.modifiers()
        if key == QtCore.Qt.Key_C:
            if mod == QtCore.Qt.ControlModifier:
                self.copyColor()
            elif mod == (
                QtCore.Qt.ControlModifier|QtCore.Qt.ShiftModifier
            ):
                self.copyColor(self.AsHex)
            elif mod == (
                QtCore.Qt.ControlModifier|QtCore.Qt.AltModifier
            ):
                self.copyColor(self.AsHsv)
        super(ColorPalette, self).keyPressEvent(event)


class ColorPaletteGroup(QtWidgets.QGroupBox):
    r"""
        カラーパレットの一覧を作成するクラス
    """
    buttonClicked = QtCore.Signal(list)
    rightButtonClicked = QtCore.Signal(ColorPalette)
    def __init__(self, row=2, column=10, parent=None):
        r"""
            Args:
                row (int):パレットの行数
                column (int):パレットの列数
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ColorPaletteGroup, self).__init__('Palettes')
        layout = QtWidgets.QGridLayout(self)
        layout.setSpacing(0)
        
        self.__palettes = []
        size = style.scaled(15)
        for i in range(row):
            for j in range(column):
                palette = ColorPalette()
                palette.resize(size, size)
                palette.clicked.connect(self.emitClickSignal)
                palette.rightButtonClicked.connect(self.emitRightClickSignal)
                layout.addWidget(palette, i, j, 1, 1)
                self.__palettes.append(palette)

    def setGamma(self, gamma):
        r"""
            Args:
                gamma (any):
        """
        for palette in self.__palettes:
            palette.setGamma(gamma)

    def emitClickSignal(self, color):
        r"""
            パレット上で左クリックした際にbuttonClickedシグナルを送出する
            
            Args:
                color (list):
        """
        self.buttonClicked.emit(color)

    def emitRightClickSignal(self):
        r"""
            パレット上で右クリックした際にrightButtonClickedシグナルを送出する
        """
        self.rightButtonClicked.emit(self.sender())
        

class ColorPicker(uilib.SingletonWidget):
    r"""
        カラーピッカー機能を提供するクラス。
    """
    def buildUI(self):
        self.setStyleSheet(style.styleSheet())
        self.__applied_color = None
        self.setScalable(False)
        self.setHiddenTrigger(self.HideByFocusOut)
        self.resize(style.scaled(540), style.scaled(300))
        
        # HSVカラー用==========================================================
        hsv_grp = HsvSliderGroup('HSV')
        for i, label in enumerate('HSV'):
            hsv_grp.setLabel(i, label)
        color = QtGui.QColor()
        for i in range(11):
            f = i*0.1
            color.setHsvF(f, 1, 1)
            hsv_grp.setColor(
                0, f, (color.redF(), color.greenF(), color.blueF())
            )
        hsv_grp.valueChanged.connect(self.setColorHsv)
        # =====================================================================

        # RGBカラー用==========================================================
        rgb_grp = RgbSliderGroup('RGB')
        for i, data in enumerate(
            [('R', (1, 0, 0)), ('G', (0, 1, 0)), ('B', (0, 0, 1))]
        ):
            rgb_grp.setLabel(i, data[0])
            rgb_grp.setColor(i, 0, (0, 0, 0))
            rgb_grp.setColor(i, 1, data[1])
        rgb_grp.valueChanged.connect(self.setColorRgb)
        # =====================================================================
        
        # 色の結果を表示するフィールド=========================================
        result_view = QtWidgets.QWidget()
        palette = ColorPalette()
        palette.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )

        palette_grp = ColorPaletteGroup()
        palette_grp.buttonClicked.connect(self.applyPaletteColor)
        palette_grp.rightButtonClicked.connect(self.setPaletteColor)

        # 16進数表記のフィールド
        hex_label = QtWidgets.QLabel('Hex Color #')
        hex_field = QtWidgets.QLineEdit()
        hex_field.setInputMask('HHHHHH')
        hex_field.textEdited.connect(self.setNamedColor)
        
        # ガンマ
        gma_label = QtWidgets.QLabel('Gamma')
        gma_field = uilib.DoubleSpiner()
        gma_field.setRange(0.01, 100)
        gma_field.setSingleStep(0.1)
        gma_field.setValue(2.2)
        gma_field.setDecimals(1)
        gma_field.valueChanged.connect(self.updateGamma)

        color_layout = QtWidgets.QGridLayout(result_view)
        color_layout.setSpacing(1)
        color_layout.addWidget(palette, 0, 0, 1, 2)
        color_layout.addWidget(palette_grp, 1, 0, 1, 2)
        color_layout.addWidget(hex_label, 2, 0, 1, 1)
        color_layout.addWidget(hex_field, 2, 1, 1, 1)
        color_layout.addWidget(gma_label, 3, 0, 1, 1)
        color_layout.addWidget(gma_field, 3, 1, 1, 1)
        # =====================================================================
        
        # ボタン類=============================================================
        bw = QtWidgets.QWidget()
        l = QtWidgets.QHBoxLayout(bw)
        apply = QtWidgets.QPushButton('Apply')
        apply.clicked.connect(self.accept)
        cancel = QtWidgets.QPushButton('Cancel')
        cancel.clicked.connect(self.reject)
        l.addWidget(apply)
        l.addWidget(cancel)
        # =====================================================================

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(hsv_grp, 0, 0, 1, 1)
        layout.addWidget(rgb_grp, 1, 0, 1, 1)
        layout.addWidget(result_view, 0, 1, 2, 1)
        layout.addWidget(bw, 2, 0, 1, 2)
        layout.setColumnStretch(1, 1)

        self.__palette = palette
        self.__palette_grp = palette_grp
        self.__hsv = hsv_grp
        self.__rgb = rgb_grp
        self.__hex = hex_field
        self.__gma = gma_field
        
        self.updateGamma()

    def updateUI(self, color, updateHsv, updateRgb, updateHex):
        r"""
            Args:
                color (QtGui.QColor):色
                updateHsv (bool):HSVスライダーを更新するかどうか
                updateRgb (bool):RGBスライダーを更新するかどうか
                updateHex (bool):HEX表記を更新するかどうか
        """
        self.__palette.setGamma(self.__gma.value())
        self.__palette.setColor(color)
        if updateHsv:
            self.__hsv.setValues(
                color.hueF(), color.saturationF(), color.valueF()
            )
        if updateRgb:
            self.__rgb.setValues(color.redF(), color.greenF(), color.blueF())
        if updateHex:
            self.__hex.setText(color.name()[1:])

    def updateGamma(self):
        r"""
            ガンマ値を更新した際に、GUIの表示をアップデートする。
        """
        gamma = self.gamma()
        self.__palette.setGamma(gamma)
        self.__palette_grp.setGamma(gamma)
        self.__rgb.setGamma(gamma)
        self.__hsv.setGamma(gamma)

    def setGamma(self, gamma):
        r"""
            ガンマ値を設定する。
            設定を変更するとGUIにも反映される。
            
            Args:
                gamma (float):
        """
        self.__gma.setValue(gamma)
        self.updateGamma()

    def gamma(self):
        r"""
            設定されているガンマ値を返す。
            
            Returns:
                float:
        """
        return self.__gma.value()

    def setColorRgb(self, rgb, updateHsv=True, updateRgb=False, updateHex=True):
        r"""
            Args:
                rgb (list):RGBの３色(0.0~1.0)の値を持つlist
                updateHsv (bool):HSVスライダーを更新するかどうか
                updateRgb (bool):RGBスライダーを更新するかどうか
                updateHex (bool):HEX表記を更新するかどうか
        """
        color = QtGui.QColor()
        color.setRgbF(*rgb)
        self.updateUI(color, updateHsv, updateRgb, updateHex)

    def setColorHsv(self, hsv, updateHsv=False, updateRgb=True, updateHex=True):
        r"""
            Args:
                hsv (list):HSV(0.0~1.0)の3つの値を持つlist
                updateHsv (bool):HSVスライダーを更新するかどうか
                updateRgb (bool):RGBスライダーを更新するかどうか
                updateHex (bool):HEX表記を更新するかどうか
        """
        color = QtGui.QColor()
        color.setHsvF(*hsv)
        self.updateUI(color, updateHsv, updateRgb, updateHex)

    def setNamedColor(self, text):
        r"""
            16進数指定の文字列をベースに色を指定する
            
            Args:
                text (str):
        """
        if not text.startswith('#'):
            text = '#'+text
        color = QtGui.QColor()
        color.setNamedColor(text)
        self.updateUI(color, True, True, False)

    def setColor(self, values, asHsv=False):
        r"""
            GUIのパレットに表示するカラーを設定する
            
            Args:
                values (list):RGBの３色(0.0~1.0)の値を持つlist
                asHsv (bool):Trueの場合引数valuesの値はHSVとして扱う
        """
        method = 'setColorHsv' if asHsv else 'setColorRgb'
        f = getattr(self, method)
        f(values, True, True, True)

    def color(self):
        r"""
            Returns:
                list:RGBの３色(0.0~1.0)の値を持つlist
        """
        return self.__rgb.values()

    def applyPaletteColor(self, color):
        r"""
            引数colorの色をこのウィジェットに設定する。
            
            Args:
                color (list):
        """
        if color:
            self.setColor(color)

    def setPaletteColor(self, palette):
        r"""
            引数paletteにこのウィジェットで設定されているカラーを適用する
            
            Args:
                palette (ColorPalette):
        """
        palette.setColorRgb(self.color())

    def accept(self):
        r"""
            accept送出前に現在のカラーをメモリに残しておく。
        """
        self.__applied_color = self.color()
        super(ColorPicker, self).accept()

    def exec_(self, color=None):
        r"""
            Args:
                color (list):ウィンドウを表示する際に使用するパレットの色
        """
        if not color:
            if self.__applied_color:
                color = self.__applied_color
            else:
                color = (0.5, 0.5, 0.5)
        self.setColor(color)
        self.__init_color = color
        return super(ColorPicker, self).exec_()

class ColorPickerWidget(ColorPalette):
    r"""
        色を表示する矩形ウィジェットと、その色を変更するColorPickerのセット。
    """
    colorIsSet = QtCore.Signal(float, float, float)
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ColorPickerWidget, self).__init__(parent)
        self.__color_as_float = False
        self.clicked.connect(self.showColorPicker)
        self.setGamma(2.2)

    def setColorAsFloat(self, state):
        r"""
            ColorPickerを選択した際に送出されるcolorIsSetシグナルに渡される
            引数をfloatにするかどうかを設定する。
            デフォルトは0～255のint。

            Args:
                state (bool):
        """
        self.__color_as_float = bool(state)

    def isColorAsFloat(self):
        r"""
            ColorPickerを選択した際に送出されるcolorIsSetシグナルに渡される
            引数がfloatかどうかを返す。

            Returns:
                bool:
        """
        return self.__color_as_float

    def showColorPicker(self):
        r"""
            カラーピッカーを表示する
        """
        cp = ColorPicker(MainWindow)
        cp.setGamma(self.gamma())
        result = cp.exec_(self.colorRgb())
        if not result:
            return False
        self.setColorRgb(cp.color())
        self.setGamma(cp.gamma())
        if self.isColorAsFloat():
            data = [x for x in cp.color()]
        else:
            data = [x*255 for x in cp.color()]
        self.colorIsSet.emit(*data)
        return True


def showPicker():
    cp = ColorPicker(MainWindow)
    cp.setColor((0.2, 0.35, 1.0))
    cp.show()