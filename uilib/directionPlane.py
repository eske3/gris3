#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    プレーン上で方向を指定するラインを描画するUIを提供するモジュール
    
    Dates:
        date:2017/08/17 17:24[eske](eske3g@gmail.com)
        update:2020/12/22 17:24 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import uilib, desktop
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

class Line(QtWidgets.QGraphicsPathItem):
    r"""
        ラインを描画するアイテム。
    """
    Color = QtGui.QColor(130, 122, 240)
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(Line, self).__init__(parent)
        self.setPen(
            QtGui.QPen(self.Color, 2)
        )
        self.setBrush(QtGui.QBrush(QtCore.Qt.NoBrush))
        self.setZValue(1)
        self.__start = QtCore.QPointF(0, 0)
        self.__end = QtCore.QPointF(0, 0)

    def setStart(self, pos):
        r"""
            描画開始座標を指定する。
            
            Args:
                pos (QtCore.QPointF):
        """
        self.__start = pos

    def start(self):
        r"""
            描画開始位置を返す。
            
            Returns:
                QtCore.QPointF:
        """
        return self.__start

    def setEnd(self, pos):
        r"""
            描画終了座標を指定する。
            
            Args:
                pos (QtCore.QPointF):
        """
        self.__end = pos

    def end(self):
        r"""
            描画終了位置を返す。
            
            Returns:
                QtCore.QPointF:
        """
        return self.__end

    def updatePath(self):
        r"""
            パス描画を更新する。
        """
        path = QtGui.QPainterPath()
        path.moveTo(self.start())
        path.lineTo(self.end())
        self.setPath(path)


class Operator(QtCore.QObject):
    r"""
        ここに説明文を記入
    """
    directionChanged = QtCore.Signal(
        list, QtCore.QPoint, QtCore.QPoint,
        QtCore.Qt.MouseButton, QtCore.Qt.KeyboardModifiers
    )
    StartMarkerSize = 12
    def __init__(self, view):
        r"""
            Args:
                view (DirectionView):
        """
        super(Operator, self).__init__(view)
        self.__scene = view.scene()
        self.scene().installEventFilter(self)

        self.__lineItems = {}
        self.__mouse_button = None
        self.__mod = None

    def view(self):
        r"""
            セットされているviewを返す。
            
            Returns:
                DirectionView:
        """
        return self.parent()

    def scene(self):
        r"""
            セットされているsceneを返す。
            
            Returns:
                QtWidgets.QGraphicsScene:
        """
        return self.__scene

    def eventFilter(self, object, event):
        r"""
            Args:
                object (QtCore.QObject):
                event (QtCore.QEvent):
                
            Returns:
                bool:
        """
        eventType = event.type()
        pEventFilter = super(Operator, self).eventFilter

        if eventType == QtCore.QEvent.GraphicsSceneMousePress:
            scenePos = event.scenePos()
            # 現在のカーソル位置に新規でラインを生成する。
            self.__lineItems['line'] = Line()
            self.__lineItems['line'].setStart(scenePos)
            self.scene().addItem(self.__lineItems['line'])
            
            # スタート位置にマーカーを描画する。.
            halfSize = self.StartMarkerSize / 2.0
            self.__lineItems['marker'] = QtWidgets.QGraphicsEllipseItem(
                scenePos.x() - halfSize, scenePos.y() - halfSize,
                self.StartMarkerSize, self.StartMarkerSize
            )
            self.__lineItems['marker'].setBrush(Line.Color)
            self.scene().addItem(self.__lineItems['marker'])
            
            self.__mouse_button = event.button()
            self.__mod = event.modifiers()
            return True
        elif eventType == QtCore.QEvent.GraphicsSceneMouseMove:
            if self.__lineItems:
                self.__lineItems['line'].setEnd(event.scenePos())
                self.__lineItems['line'].updatePath()
            return True
        elif eventType == QtCore.QEvent.GraphicsSceneMouseRelease:
            if self.__lineItems:
                startPos = self.__lineItems['line'].start()
                endPos = self.__lineItems['line'].end()
                resultVector = [
                    endPos.x() - startPos.x(), startPos.y() - endPos.y(), 0
                ]
                for key in self.__lineItems:
                    self.scene().removeItem(self.__lineItems[key])
                self.__lineItems = {}

                if self.__mouse_button and self.__mod is not None:
                    self.directionChanged.emit(
                        resultVector,
                        QtCore.QPoint(startPos.x(), startPos.y()),
                        QtCore.QPoint(endPos.x(), endPos.y()),
                        self.__mouse_button, self.__mod
                    )
            return True
        return pEventFilter(object, event)


class DirectionView(QtWidgets.QGraphicsView):
    r"""
        方向指示を行うためのビューを提供するクラス。
    """
    directionChanged = QtCore.Signal(
        list, QtCore.QPoint, QtCore.QPoint,
        QtCore.Qt.MouseButton, QtCore.Qt.KeyboardModifiers
    )
    XYPlane = (0, 1, 2)
    ZYPlane = (2, 1, 0)
    XZPlane = (0, 2, 1)
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(DirectionView, self).__init__(parent)
        self.setCacheMode(QtWidgets.QGraphicsView.CacheBackground)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setRenderHints(
            QtGui.QPainter.RenderHint.Antialiasing |
            QtGui.QPainter.RenderHint.SmoothPixmapTransform |
            QtGui.QPainter.RenderHint.TextAntialiasing
        )
        self.__basePlane = self.XYPlane

        font = QtGui.QFont('arial', 10)
        scene = QtWidgets.QGraphicsScene(QtCore.QRectF(self.rect()))
        self.__textItem = scene.addText('', font)
        self.setScene(scene)

        oprt = Operator(self)
        oprt.directionChanged.connect(self.done)

    def setVectorPlane(self, planeType):
        r"""
            ベクトルを定義するプレーンを設定する。
            
            Args:
                planeType (list or tuple): ベクトルを表す３軸のリスト
        """
        self.__basePlane = planeType

    def setText(self, text):
        r"""
            ビューに描画する説明用テキストをセットする。
            
            Args:
                text (str):
        """
        self.__textItem.setPlainText(text)

    def done(self, vector, start, end, mouseButton, modifiers):
        r"""
            方向指示終了時にdirectionChangedシグナルを送出する。
            シグナルはベクトル情報とマウスボタン、修飾キー情報を持っている。
            
            Args:
                vector (list):入力ベクトル
                start (QtCore.QPoint):
                end (QtCore.QPoint):
                mouseButton (QtCore.Qt.MouseButton):押されているマウスのボタン
                modifiers (QtCore.Qt.KeyboardModifiers):押されている修飾キー
        """
        newVector = [vector[x] for x in self.__basePlane]
        self.directionChanged.emit(
            newVector, start, end, mouseButton, modifiers
        )

    def resizeEvent(self, event):
        r"""
            resizeEventのオーバーライド。Sceneの大きさを更新する。
            
            Args:
                event (QtCore.QEvent):
        """
        self.scene().setSceneRect(QtCore.QRectF(self.rect()))


class DirectionScreen(DirectionView):
    r"""
        画面全体で方向指示を行うためのGUIを提供するクラス
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(DirectionScreen, self).__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.viewport().setAutoFillBackground(False)
        self.setText('Draw line to snap nodes or vertices.')
        self.directionChanged.connect(self.execOperation)
        self.viewport().setStyleSheet('background:rgba(0, 0, 0, 25);')

    def show(self):
        self.setGeometry(desktop.DesktopInfo().getAvailableGeometry())
        super(DirectionScreen, self).show()

    def execOperation(self, newVector, start, end, mouseButton, modifiers):
        r"""
            Args:
                newVector (list):
                start (QtCore.QPoint):
                end (QtCore.QPoint):
                mouseButton (QtCore.Qt.MouseButton):
                modifiers (int):
        """
        self.close()
        if mouseButton == QtCore.Qt.RightButton:
            return

        self.execute(newVector, start, end, mouseButton, modifiers)
        try:
            self.deleteLater()
        except:
            pass

    def execute(self, newVector, start, end, mouseButton, modifiers):
        r"""
            Args:
                newVector (list):
                start (QtCore.QPoint):
                end (QtCore.QPoint):
                mouseButton (QtCore.Qt.MouseButton):
                modifiers (int):
        """
        pass