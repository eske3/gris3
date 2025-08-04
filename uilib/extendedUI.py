#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    通常のQtウィジェットに使いやすい機能を追加した拡張クラスを提供するモジュール。
    
    Dates:
        date:2017/01/21 23:58[Eske](eske3g@gmail.com)
        update:2025/07/21 15:08 Eske Yoshinob[eske3g@gmail.com]

    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import uilib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

# フィルター表示可能なビュー機能。
class FilteredView(QtWidgets.QWidget):
    r"""
        表示のフィルタ機能付きのViewを提供するクラス。
        フィルタに使用するViewを作成するcreateViewメソッドと、
        そのviewが取り扱うmodelを定義するcreateModelメソッド
        はヴァーチャルなので必ず再実装する必要がある。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(FilteredView, self).__init__(parent)
        self.__tool_was_run = False
        self.__selected = 0

        model = self.createModel()
        proxy = QtCore.QSortFilterProxyModel()
        proxy.setFilterKeyColumn(self.filterKeyColumn())
        proxy.setRecursiveFilteringEnabled(True)
        proxy.setSourceModel(model)

        sel_model = QtCore.QItemSelectionModel(proxy)

        self.__view = self.createView()
        self.__view.setModel(proxy)
        self.__view.setSelectionModel(sel_model)
        self.__view.installEventFilter(self)

        self.__field = QtWidgets.QLineEdit()
        self.__field.hide()
        self.__field.installEventFilter(self)
        self.__field.textChanged.connect(self.setFilterToView)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        layout.addWidget(self.__view)
        layout.addWidget(self.__field)

    @uilib.abstractmethod
    def createView(self):
        r"""
            再実装用メソッド。任意のViewを作成し返す。
            
            Returns:
                QtWidgets.QAbstractItemView:
        """
        pass

    @uilib.abstractmethod
    def createModel(self):
        r"""
            再実装用メソッド。任意のItemModelを作成し返す。
            
            Returns:
                QtGui.QStandardItemModel:
        """
        pass

    def filterKeyColumn(self):
        r"""
            SortFilterのキーとなるカラム番号を返す。デフォルトは0
            
            Returns:
                int:
        """
        return 0

    def view(self):
        r"""
            一覧表示用のViewを返す
            
            Returns:
                QtWidgets.QAbstractItemView:
        """
        return self.__view

    def setFilterToView(self, text):
        r"""
            ビューの表示フィルタを有効にする
            
            Args:
                text (str):フィルタ文字列
        """
        reg_exp = QtCore.QRegExp(
            text, QtCore.Qt.CaseInsensitive, QtCore.QRegExp.Wildcard
        )
        proxy = self.view().model()
        proxy.setFilterRegExp(reg_exp)

    def eventFilter(self, obj, event):
        r"""
            Args:
                obj (QtCore.QObject):
                event (QtCore.QEvent):
                
            Returns:
                bool:
        """
        if event.type() != QtCore.QEvent.KeyPress:
            return False
        key = event.key()
        if obj == self.__field:
            # フィルタ入力フィールド内での操作の場合
            if key == QtCore.Qt.Key_Escape:
                self.__field.hide()
                self.view().setFocus(QtCore.Qt.ShortcutFocusReason)
                self.setFilterToView('')
                return True
            return False
        # それ以外の場合
        if key == QtCore.Qt.Key_Tab:
            self.__field.show()
            self.__field.setFocus(QtCore.Qt.ShortcutFocusReason)
            # self.__field.keyPressEvent(event)
            return True
        return False


class EasyMovableSplitter(QtWidgets.QSplitter):
    r"""
        addWidgetAsHandleで追加したウィジェットがスプリッタハンドルの
        代わりを果たすようになる拡張QSplitter。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(EasyMovableSplitter, self).__init__(parent)
        self.setPrePosition()

    def prePosition(self):
        r"""
            ドラッグ時の開始位置を返す。
            
            Returns:
                QtCore.QPoint:
        """
        return self.__pre_pos

    def setPrePosition(self, position=None):
        r"""
            ドラッグ時の開始位置を設定する。

            Args:
                position (QtCore.QPoint):
        """
        self.__pre_pos = position
        
    def addWidget(self, widget):
        r"""
            ウィジェットを追加する。
            
            Args:
                widget (QtWidgets.QWidget):
        """
        super(EasyMovableSplitter, self).addWidget(widget)
        for i in range(self.count()):
            self.handle(i).setEnabled(False)

    def addWidgetAsHandle(self, widget):
        r"""
            分割線制御用となるウィジェットを追加する。
            
            Args:
                widget (QtWidgets.QWidget):
        """
        self.addWidget(widget)
        widget.installEventFilter(self)

    def eventFilter(self, obj, event):
        r"""
            Args:
                obj (QtCore.QObject):
                event (QtCore.QEvent):
                
            Returns:
                bool:
        """
        event_type = event.type()
        if (
            event_type == QtCore.QEvent.MouseButtonPress and
            event.button() == QtCore.Qt.LeftButton
        ):
            self.setPrePosition(event.globalPos())
            return True
        elif event_type == QtCore.QEvent.MouseMove and self.prePosition():
            pos = event.globalPos()
            delta = pos - self.prePosition()
            index = self.indexOf(obj)
            sizes = self.sizes()

            offset = 1 if index < len(sizes)  - 1 else -1
            moved = (
                (
                    delta.x()
                    if self.orientation() == QtCore.Qt.Horizontal
                    else delta.y()
                )
                * offset
            )
            sizes[index] += moved
            sizes[index + offset] -= moved
                
            self.setSizes(sizes)

            self.setPrePosition(pos)
            return True
        elif event_type == QtCore.QEvent.MouseButtonRelease:
            self.setPrePosition()
            return True
        return False
        

# /////////////////////////////////////////////////////////////////////////////
# スクリーン上でドラッグする事によりラインを描画して方向を確定               //
# させるためのウィジェット。                                                 //
# /////////////////////////////////////////////////////////////////////////////
class DirectionaalPlaneLine(QtWidgets.QGraphicsPathItem):
    r"""
        方向を提示するためのラインを描画するアイテム。
    """
    Color = QtGui.QColor(130, 122, 240)
    def __init__(self, scene, parent=None):
        r"""
            Args:
                scene (QtWidgets.QGraphicsScene):
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(DirectionaalPlaneLine, self).__init__(parent, scene)
        self.setPen(QtGui.QPen(self.Color, 2))
        self.setBrush(QtGui.QBrush(QtCore.Qt.NoBrush))
        self.setZValue(1)
        self.__start = QtCore.QPointF(0, 0)
        self.__end = QtCore.QPointF(0, 0)

    def setStart(self, pos):
        r"""
            スタート位置を設定する。
            
            Args:
                pos (QtCore.QPointF):
        """
        self.__start = pos

    def start(self):
        r"""
            セットされているスタート位置を返す。
            
            Returns:
                QtCore.QPointF:
        """
        return self.__start

    def setEnd(self, pos):
        r"""
            終端位置を設定する。
            
            Args:
                pos (QtCore.QPointF):
        """
        self.__end = pos

    def end(self):
        r"""
            セットされている終端位置を返す。
            
            Returns:
                QtCore.QPointF:
        """
        return self.__end

    def updatePath(self):
        r"""
            パスの描画をアップデートする。
        """
        path = QtGui.QPainterPath()
        path.moveTo(self.start())
        path.lineTo(self.end())
        self.setPath(path)


class DirectionalOperator(QtCore.QObject):
    r"""
        QGraphicsViewのオペレーションを行う機能を提供するクラス。
    """
    directionChanged = QtCore.Signal(list, int)
    StartMarkerSize = 10
    def __init__(self, view):
        r"""
            Args:
                view (QtWidgets.QGraphicsView):
        """
        super(DirectionalOperator, self).__init__(view)
        self.__scene = view.scene()
        self.scene().installEventFilter(self)
        self.__lineitems = {}
        self.__mouseButton = None

    def view(self):
        r"""
            セットされているビューを返す。
            
            Returns:
                QtWidgets.QGraphicsView:
        """
        return self.parent()

    def scene(self):
        r"""
            セットされているビューのシーンオブジェクトを返す。
            
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
        event_type = event.type()
        p_event_filter = super(DirectionalOperator, self).eventFilter

        if event_type == QtCore.QEvent.GraphicsSceneMousePress:
            scene_pos = event.scenePos()
            # 新しいラインアイテムをカーソル上に作成する。
            self.__lineitems['line'] = DirectionaalPlaneLine(self.scene())
            self.__lineitems['line'].setStart(scene_pos)
            
            # 開始位置を表すマーカーを作成する。
            half_size = self.StartMarkerSize / 2.0
            self.__lineitems['marker'] = QtWidgets.QGraphicsEllipseItem(
                scene_pos.x() - half_size, scene_pos.y() - half_size,
                self.StartMarkerSize, self.StartMarkerSize
            )
            self.__lineitems['marker'].setBrush(DirectionaalPlaneLine.Color)
            self.scene().addItem(self.__lineitems['marker'])
            
            self.__mouseButton = int(QtWidgets.QApplication.mouseButtons())
            return True

        elif event_type == QtCore.QEvent.GraphicsSceneMouseMove:
            if self.__lineitems:
                self.__lineitems['line'].setEnd(event.scenePos())
                self.__lineitems['line'].updatePath()
            return True

        elif event_type == QtCore.QEvent.GraphicsSceneMouseRelease:
            if self.__lineitems:
                start_pos = self.__lineitems['line'].start()
                end_pos = self.__lineitems['line'].end()
                r_vector = [
                    end_pos.x() - start_pos.x(), start_pos.y() - end_pos.y(), 0
                ]

                for key in self.__lineitems:
                    self.scene().removeItem(self.__lineitems[key])
                self.__lineitems = {}

                if self.__mouseButton:
                    self.directionChanged.emit(r_vector, self.__mouseButton)
            return True
        return p_event_filter(object, event)


class DirectionView(QtWidgets.QGraphicsView):
    r"""
        方向指示をするためのビューを提供するクラス。
    """
    directionChanged = QtCore.Signal(list, int)
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
            QtGui.QPainter.Antialiasing |
            QtGui.QPainter.SmoothPixmapTransform |
            QtGui.QPainter.TextAntialiasing
        )
        self.__base_plane = self.XYPlane

        font = QtGui.QFont('arial', 10)
        scene = QtWidgets.QGraphicsScene(QtCore.QRectF(self.rect()))
        self.__textItem = scene.addText('', font)
        self.setScene(scene)

        oprt = DirectionalOperator(self)
        oprt.directionChanged.connect(self.done)

    def setVectorPlane(self, planeType):
        r"""
            Args:
                planeType (any):
        """
        self.__base_plane = planeType

    def setText(self, text):
        r"""
            左上に表示する注釈テキストを設定する。
            
            Args:
                text (str):
        """
        self.__textItem.setPlainText(text)

    def done(self, vector, mouseButton):
        r"""
            ドラッグ操作が終了した際に呼ばれる。
            directionChangedシグナルが創出される。

            Args:
                vector (list):
                mouseButton (QtCore.Qt.MouseButtons):
        """
        newVector = [vector[x] for x in self.__base_plane]
        self.directionChanged.emit(newVector, mouseButton)

    def resizeEvent(self, event):
        r"""
            リサイズ時のイベントのオーバーライド。
            
            Args:
                event (QtCore.QEvent):
        """
        self.scene().setSceneRect(QtCore.QRectF(self.rect()))
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////