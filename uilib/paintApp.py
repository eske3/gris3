#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2021/04/26 12:06 eske yoshinob[eske3g@gmail.com]
        update:2021/05/01 04:59 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2021 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import uilib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

class DrawCanvas(QtWidgets.QDialog):
    drawingFinished = QtCore.Signal()
    def __init__(self, size=QtCore.QSize(), parent=None):
        r"""
            Args:
                size (QtCore.QSize):
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(DrawCanvas, self).__init__(parent)
        self.setWindowTitle('Draw Canvas')
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.clearDrawingHistory()
        self.setMemoryDrawingHistory(False)
        self.__drawing = False
        self.__brush_size = 20
        self.__brush_color = QtCore.Qt.black
        self.__last_point = QtCore.QPoint()
        self.__last_pressure = 1.0
        self.__circle_size = None

        self.__image = self.setupCanvas(size)
        self.updateCanvasRatio()

    def setupCanvas(self, size):
        r"""
            使用するキャンパス用のQImageを作成して返す。
            
            Args:
                size (QtCore.QSize):
                
            Returns:
                QtGui.QImage:
        """
        image = QtGui.QImage(size, QtGui.QImage.Format_RGB32)
        image.fill(QtGui.QColor(255,255,255))
        return image

    def image(self):
        r"""
            現在使用されているQImageを返す
            
            Returns:
                QtGui.QImage:
        """
        return self.__image

    def setMemoryDrawingHistory(self, state):
        r"""
            描画時のストロークの位置とサイズ情報を保持するかどうかを設定する
            
            Args:
                state (bool):
        """
        self.__men_draw_history = bool(state)

    def memoryDrawingHistory(self):
        r"""
            描画時のストロークの位置とサイズ情報を保持するかどうをかえす
            
            Returns:
                bool:
        """
        return self.__men_draw_history

    def clearDrawingHistory(self):
        r"""
            描画時のストローク履歴をクリアする
        """
        self.__draw_histories = []

    def drawingHistories(self):
        r"""
            ブラシの描画履歴のリストを返す。
            描画履歴のリストには
            (描画座標(QtCore.QPoint), ブラシサイズ(float))
            を持つリストを、ストロークした順にその数だけ保持している。
            
            Returns:
                list:
        """
        return [x for x in self.__draw_histories]

    def setBrushSize(self, size):
        r"""
            ブラシサイズを設定する
            
            Args:
                size (int):
        """
        self.__brush_size = size if size > 1 else 1

    def brushSize(self):
        r"""
            ブラシサイズを返す。
            
            Returns:
                int:
        """
        return self.__brush_size

    def setBrush(self, brush):
        r"""
            Args:
                brush (any):
        """
        self.__brush_color = brush

    def setBrushColor(self, r, g, b, a=255):
        r"""
            Args:
                r (any):
                g (any):
                b (any):
                a (any):
        """
        self.setBrush(QtGui.QColor(r, g, b, a))

    def brush(self):
        r"""
            セットされているブラシを返す
            
            Returns:
                QtGui.QBrush:
        """
        return self.__brush_color

    def updateCanvasRatio(self):
        i_size = self.__image.rect().size()
        w_size = self.size()
        self.__ratios = [
            float(i_size.width()) / w_size.width(),
            float(i_size.height()) / w_size.height()
        ]

    def setImageSize(self, size):
        r"""
            キャンパスイメージの大きさを変更する。
            
            Args:
                size (QtCore.QSize):
        """
        self.__image = self.__image.scaled(
            size, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation
        )
        self.updateCanvasRatio()

    def fitCanvasToWidget(self):
        self.setImageSize(self.rect().size())

    def adjustPosToImage(self, pos):
        r"""
            Args:
                pos (QtCore.QPoint):
        """
        return QtCore.QPoint(
            pos.x() * self.__ratios[0], pos.y() * self.__ratios[1]
        )

    def mousePressEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        btn = event.button()
        self.__drawing = False
        if btn == QtCore.Qt.LeftButton:
            self.__drawing = True
            self.__last_point = self.adjustPosToImage(event.pos())
            self.__draw_histories.append([(self.__last_point, 0)])
        elif (
            btn == QtCore.Qt.RightButton and
            event.modifiers() == QtCore.Qt.AltModifier
        ):
            self.__last_point = event.pos()
            self.__circle_size = self.brushSize()
            
    def mouseMoveEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        btns = event.buttons()
        pos = event.pos()
        if btns == QtCore.Qt.LeftButton and self.__drawing:
            pos = self.adjustPosToImage(pos)
            painter = QtGui.QPainter(self.__image)
            painter.setRenderHints(painter.Antialiasing)
            brush_size = self.brushSize() * self.__last_pressure
            painter.setPen(
                QtGui.QPen(
                    self.brush(), brush_size,
                    QtCore.Qt.SolidLine, QtCore.Qt.RoundCap, QtCore.Qt.RoundJoin
                )
            )
            painter.drawLine(self.__last_point, pos)
            if self.memoryDrawingHistory():
                self.__draw_histories[-1].append((pos, brush_size))
            self.__last_point = pos
            self.update()
        elif (
            btns == QtCore.Qt.RightButton and
            event.modifiers() == QtCore.Qt.AltModifier
        ):
            size = pos.x() - self.__last_point.x()
            self.__circle_size = self.brushSize() + size
            if self.__circle_size < 1:
                self.__circle_size = 1
            self.update()

    def mouseReleaseEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        btn = event.button()
        if btn == QtCore.Qt.LeftButton:
            self.__drawing = False
            self.drawingFinished.emit()
        elif (
            btn == QtCore.Qt.RightButton and
            event.modifiers() == QtCore.Qt.AltModifier
        ):
            if isinstance(self.__circle_size, int):
                self.setBrushSize(self.__circle_size)
            self.__circle_size = None
            self.update()

    def tabletEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        self.__last_pressure = event.pressure()

    def paintEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        painter = QtGui.QPainter(self)
        painter.setRenderHints(painter.Antialiasing)
        painter.drawImage(
            self.rect(), self.__image, self.__image.rect()
        )
        
        if not self.__circle_size:
            return
        painter.setPen(QtGui.QPen(QtGui.QColor(0,0,0), 1))
        painter.setBrush(QtGui.QColor(200, 32, 67, 120))
        r = self.__circle_size * 0.5
        painter.drawEllipse(self.__last_point, r, r)

    def resizeEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        self.updateCanvasRatio()

class DesktopCanvas(DrawCanvas):
    def __init__(self, parent=None, screenNumber=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
                screenNumber (int):デスクトップのスクリーン番号
        """
        desktop = QtWidgets.QApplication.desktop()
        if screenNumber is None:
            screenNumber = desktop.screenNumber(QtGui.QCursor().pos())
        screen_geo = desktop.availableGeometry(screenNumber)
        super(DesktopCanvas, self).__init__(screen_geo, parent)
        self.setWindowFlags(QtCore.Qt.Window|QtCore.Qt.FramelessWindowHint)
        self.setGeometry(screen_geo)

    def editCanvas(self, image, imageRect, desktopRect):
        r"""
            キャンパスのQImageを作成した後に、後編集を行う。
        
            Args:
                image (QtGui.QImage):編集対象となるQImage
                imageRect (QtCore.QRect):渡されたQImageの矩形情報
                desktopRect (QtCore.QRect):使用するデスクトップの矩形情報

            Returns:
                QtGui.QImage:
        """
        painter = QtGui.QPainter(image)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(0, 0, 0, 80))
        painter.drawRect(imageRect)
        return image

    def setupCanvas(self, rect):
        r"""
            使用するキャンパス用のQImageを作成して返す。
            
            Args:
                rect (QtCore.QRect):
                
            Returns:
                QtGui.QImage:
        """
        pixmap = QtGui.QPixmap.grabWindow(
            QtWidgets.QApplication.desktop().winId(),
            rect.x(), rect.y(), rect.width(), rect.height()
        )
        image = pixmap.toImage()
        image_rect = QtCore.QRect(rect)
        image_rect.moveTopLeft(QtCore.QPoint(0, 0))
        self.editCanvas(image, image_rect, rect)
        return image


class MainGUI(uilib.AbstractSeparatedWindow):
    r"""
        PolyCutWidgetを起動する
        
        Returns:
            Painter:
    """
    def centralWidget(self):
        # return DrawCanvas(QtCore.QSize(800, 800))
        from . import colorPicker
        w = QtWidgets.QSplitter()
        dc = DrawCanvas(QtCore.QSize(800, 800))
        cp = colorPicker.ColorPickerWidget()
        cp.setGamma(1.0)
        cp.colorIsSet.connect(dc.setBrushColor)
        w.addWidget(dc)
        w.addWidget(cp)
        
        self.fitCanvasToWidget = dc.fitCanvasToWidget
        return w

def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。
        
        Returns:
            QtWidgets.QWidget:
    """
    from gris3.uilib import mayaUIlib
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(uilib.hires(800), uilib.hires(600))
    widget.show()
    widget.fitCanvasToWidget()
    return widget
