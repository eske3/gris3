# -*- coding: utf-8 -*-
r'''
    @file     graphicsUI.py
    @brief    QGraphicsSceneを用いたリストライブラリ。
    @class    GraphicsRootItem : ここに説明文を記入
    @class    GraphicsItemListScene : ここに説明文を記入
    @class    GraphicsItemView : ここに説明文を記入
    @class    GraphicsStandardItem : ここに説明文を記入
    @class    GraphicsLabelItem : ここに説明文を記入
    @class    GraphicsStandardList : ここに説明文を記入
    @date        2017/01/21 23:58[Eske](eske3g@gmail.com)
    @update      2017/01/21 23:58[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
import re
import math
import time

from gris3 import uilib, style
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

class GraphicsRootItem(QtWidgets.QGraphicsLineItem):
    r'''
        @brief       ここに説明文を記入
        @inheritance QtWidgets.QGraphicsLineItem
        @date        2017/01/21 23:58[Eske](eske3g@gmail.com)
        @update      2017/01/21 23:58[Eske](eske3g@gmail.com)
    '''
    def __init__(self, parent=None):
        r'''
            @brief  ここに説明文を記入
            @param  parent(None) : [edit]
            @return None
        '''
        super(GraphicsRootItem, self).__init__(parent)

    def boundingRect(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return self.childrenBoundingRect()

    def paint(self, painter, option, widget):
        r'''
            @brief  ここに説明文を記入
            @param  painter : [edit]
            @param  option : [edit]
            @param  widget : [edit]
            @return None
        '''
        pass

class GraphicsItemListScene(QtWidgets.QGraphicsScene):
    r'''
        @brief       ここに説明文を記入
        @inheritance QtWidgets.QGraphicsScene
        @date        2017/01/21 23:58[Eske](eske3g@gmail.com)
        @update      2017/01/21 23:58[Eske](eske3g@gmail.com)
    '''
    AnimTime = 0.5
    nothingPointed = QtCore.Signal()
    def __init__(self, *argv, **keywords):
        r'''
            @brief  ここに説明文を記入
            @param  *argv : [edit]
            @param  **keywords : [edit]
            @return None
        '''
        super(GraphicsItemListScene, self).__init__(*argv, **keywords)
        self.__rootitem = None
        self.__pressed_button = None
        self.__mouse_pressed_time = 0.0
        self.__mouse_dragged_time = 0.0
        
        self.__timerid = None
        self.__ratio = 1.0
        
        self.__ignore_animation_canceld = True
        self.__fit_timerid = None
        self.__fit_starttime = 0
        self.__fit_start_transform = None
        self.__fit_goal_transform = None
        self.__fit__starttime = 0
        self.__occupancy = 1

        self.__current_pos = None
        self.__delta = None

        self.__startpos = None
        self.__screen_pos = None
        self.__screen_delta = None
        
        self.__is_dragged = False

    def setCancelCallIgnored(self, state):
        r'''
            @brief  ここに説明文を記入
            @param  state : [edit]
            @return None
        '''
        self.__ignore_animation_canceld = bool(state)

    def clear(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        if self.__rootitem:
            self.removeItem(self.__rootitem)
            self.__rootitem = None

    def setOccupancy(self, percentage):
        r'''
            @brief  ここに説明文を記入
            @param  percentage : [edit]
            @return None
        '''
        self.__occupancy = percentage

    def resetDragState(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        self.__is_dragged = False

    def isDragged(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return self.__is_dragged

    def rootItem(self):
        r'''
            @brief  ルートアイテムを返すメソッド。ルートアイテムがない場合は新規で
            @brief  作成し、その作成されたアイテムを返す。
            @return None
        '''
        if self.__rootitem:
            return self.__rootitem

        #root_item = QtWidgets.QGraphicsItemGroup()
        root_item = GraphicsRootItem()
        self.addItem(root_item)
        self.__rootitem = root_item
        
        return root_item

    def allItems(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        if not self.__rootitem:
            return []
        return self.__rootitem.childItems()

    def setCurrentPos(self, pos):
        r'''
            @brief  ここに説明文を記入
            @param  pos : [edit]
            @return None
        '''
        self.__current_pos = pos

    def currentPos(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return self.__current_pos

    def pressedButton(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return self.__pressed_button

    def centerTransform(self, occupancy=None, targetRect=None):
        r'''
            @brief  ここに説明文を記入
            @param  occupancy(None) : [edit]
            @param  targetRect(None) : [edit]
            @return None
        '''
        if not occupancy:
            occupancy = self.__occupancy

        if not targetRect:
            root_item = self.rootItem()
            targetRect = root_item.boundingRect()
            children_rect = root_item.childrenBoundingRect()
            offset = QtCore.QPointF(
                children_rect.x() * occupancy,
                children_rect.y() * occupancy
            )
        else:
            offset = QtCore.QPointF(
                targetRect.x() * occupancy,
                targetRect.y() * occupancy
            )
        scene_rect = self.sceneRect()

        if targetRect.width() == 0:
            return QtGui.QTransform()

        item_aspect_ratio = targetRect.width() / targetRect.height()
        scene_aspect_ratio = scene_rect.width() / scene_rect.height()

        if scene_aspect_ratio >= 1:
            # シーンが縦長の場合。
            if item_aspect_ratio > scene_aspect_ratio:
                # イメージの方がシーンよりも横長の場合。
                scale_ratio = scene_rect.width() / targetRect.width()
                fit_vertical = False
            else:
                scale_ratio = scene_rect.height() / targetRect.height()
                fit_vertical = True
        else:
            # シーンが縦長の場合。
            if scene_aspect_ratio > item_aspect_ratio:
                # イメージの方がシーンよりも縦長の場合。
                scale_ratio = scene_rect.height() / targetRect.height()
                fit_vertical = True
            else:
                scale_ratio = scene_rect.width() / targetRect.width()
                fit_vertical = False

        transform = QtGui.QTransform()
        transform.translate(-offset.x() * scale_ratio, -offset.y() * scale_ratio)
        trs_transform = QtGui.QTransform()

        sub_occupancy = 1 - occupancy
        if fit_vertical:
            transform.translate(
                abs(
                    scene_rect.width() -
                    (targetRect.width() * scale_ratio * occupancy)
                ) * 0.5,
                scene_rect.height() * sub_occupancy * 0.5,
            )
        else:
            transform.translate(
                scene_rect.width() * sub_occupancy * 0.5,
                abs(
                    scene_rect.height() -
                    (targetRect.height() * scale_ratio * occupancy)
                    
                ) * 0.5,
            )
        trs_transform.scale(
            scale_ratio * occupancy, scale_ratio * occupancy
        )
        trs_transform *= transform

        return trs_transform

    def fitAll(self, transform=None):
        r'''
            @brief  アイテムをシーンの大きさに合わせるメソッド。
            @param  transform(None) : [edit]
            @return None
        '''
        if not self.rootItem():
            return

        if not transform:
            transform = self.centerTransform()
        
        if self.__fit_timerid:
            self.killTimer(self.__fit_timerid)
            self.__fit_timerid = None
        self.__fit_starttime = time.time()
        self.__fit_start_transform = self.rootItem().transform()
        self.__fit_goal_transform = transform

        self.__fit_timerid = self.startTimer(10)

    def fitSelected(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        selected_items = self.selectedItems()
        if not selected_items:
            self.fitAll()

        root_item = self.rootItem()
        bounding_rect = QtCore.QRectF()
        for item in selected_items:
            bounding_rect = bounding_rect.united(
                item.mapToItem(root_item, item.boundingRect()).boundingRect()
            )
        self.fitAll(self.centerTransform(targetRect=bounding_rect))

    def adjust(self, transform=None):
        r'''
            @brief  アイテムをシーンの大きさに合わせるメソッド。
            @brief  fitAllメソッドはアジャストのアニメーションがあるのに対し、
            @brief  このメソッドの場合は瞬間的にアジャストする。
            @param  transform(None) : [edit]
            @return None
        '''
        if not self.rootItem():
            return
        if not transform:
            transform = self.centerTransform()
        self.rootItem().setTransform(transform)

    def keyPressEvent(self, event):
        r'''
            @brief  ここに説明文を記入
            @param  event : [edit]
            @return None
        '''
        key = event.key()
        mod = event.modifiers()
        if mod == QtCore.Qt.ControlModifier:
            if key == QtCore.Qt.Key_A:
                self.fitAll()
                return
            elif key == QtCore.Qt.Key_F:
                self.fitSelected()
                return
        
        super(GraphicsItemListScene, self).keyPressEvent(event)

    def mouseDoubleClickEvent(self, event):
        r'''
            @brief  ここに説明文を記入
            @param  event : [edit]
            @return None
        '''
        self.fitAll()

    def mousePressEvent(self, event):
        r'''
            @brief  ここに説明文を記入
            @param  event : [edit]
            @return None
        '''
        scene_pos = event.scenePos()
        item = self.itemAt(scene_pos)

        if event.modifiers() != QtCore.Qt.AltModifier and item:
            while(1):
                if (
                    item.flags() & QtWidgets.QGraphicsItem.ItemIsMovable
                ):
                    super(GraphicsItemListScene, self).mousePressEvent(event)
                    self.__startpos = None
                    return
                item = item.parentItem()
                if not item:
                    break

        self.setCurrentPos(scene_pos)
        self.__startpos = event.scenePos()
        self.__delta = QtCore.QPoint()
        self.__screen_pos = event.screenPos()
        self.__screen_delta = QtCore.QPoint()
        self.__is_dragged = False
        self.__mouse_pressed_time = time.time()

        self.__pressed_button = event.button()
        
        if self.__pressed_button == QtCore.Qt.RightButton:
            cursor_shape = QtCore.Qt.SizeAllCursor
        else:
            cursor_shape = QtCore.Qt.ClosedHandCursor
            self.__timerid = self.startTimer(10)
            self.__ratio = 1.0
        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(cursor_shape))

    def mouseMoveEvent(self, event):
        r'''
            @brief  ここに説明文を記入
            @param  event : [edit]
            @return None
        '''
        self.__is_dragged = True
        self.__mouse_dragged_time = time.time()
        if self.__fit_timerid and not self.__ignore_animation_canceld: 
            self.killTimer(self.__fit_timerid)
            self.__fit_timerid = None

        if not self.currentPos() or not self.__startpos:
            super(GraphicsItemListScene, self).mouseMoveEvent(event)
            return
        if not self.rootItem():
            return

        # 現在のシーン上のポジションを取得する。-------------------------------
        cur = event.scenePos()
        self.__delta = cur - self.currentPos()
        self.setCurrentPos(cur)
        local_trs = self.rootItem().mapFromScene(cur)
        # ---------------------------------------------------------------------
        
        #スクリーンスペースでの現在のポジションを取得する。--------------------
        cur = event.scenePos()
        self.__screen_delta = cur - self.__screen_pos
        self.__screen_pos = cur
        # ---------------------------------------------------------------------
        
        transform = self.rootItem().transform()
        if self.__pressed_button == QtCore.Qt.RightButton:
            # スケーリング処理。
            if self.__delta.x() < 0:
                value = 0.95
            else:
                value = 1.05

            transform.translate(local_trs.x(), local_trs.y()) \
                .scale(value, value) \
                .translate(-local_trs.x(), -local_trs.y())
        else:
            # 移動処理。
            transform *= QtGui.QTransform().translate(
                self.__delta.x(), self.__delta.y()
            )
        self.rootItem().setTransform(transform)

    def mouseReleaseEvent(self, event):
        r'''
            @brief  ここに説明文を記入
            @param  event : [edit]
            @return None
        '''
        QtWidgets.QApplication.restoreOverrideCursor()
        sc = super(GraphicsItemListScene, self).mouseReleaseEvent
        # マウスをドラッグし終わってから指を話すまで一定以上の時間が
        # 経った場合は慣性スクロールを行わない。
        if self.__timerid and self.__mouse_dragged_time - time.time() > 0.25:
            self.killTimer(self.__timerid)
        if not self.__startpos:
            sc(event)
            return

        self.__current_pos   = None
        self.__pressed_button = None

        self.__screen_delta  = QtCore.QPoint(
            abs(self.__screen_delta.x()), abs(self.__screen_delta.y())
        )

        sub = event.scenePos() - self.__startpos
        self.__startpos = None
        if sub.manhattanLength() > 3 and self.__is_dragged:
            sc(event)
            return

        item = self.itemAt(event.scenePos())
        if not item:
            sc(event)
            self.nothingPointed.emit()
            return
    
        while(True):
            if item.flags() & QtWidgets.QGraphicsItem.ItemIsSelectable:
                self.clearSelection()
                item.setSelected(True)
                self.selectionChanged.emit()
                break

            item = item.parentItem()
            if not item:
                break

    def timerEvent(self, event):
        r'''
            @brief  ここに説明文を記入
            @param  event : [edit]
            @return None
        '''
        timer_id = event.timerId()
        if timer_id == self.__timerid and not self.__pressed_button:
            '''慣性スクロール制御。'''
            if not self.rootItem():
                self.killTimer(self.__timerid)
                return

            if (isinstance(self.__delta, QtCore.QPoint) or
                self.__ratio < 0.01 or 
                (self.__screen_delta.x() < 3 and self.__screen_delta.y() < 3)):
                self.killTimer(self.__timerid)
                return

            base_transform = QtGui.QTransform()
            base_transform.translate(
                self.__delta.x() * self.__ratio,
                self.__delta.y() * self.__ratio,
            )
            self.rootItem().setTransform(
                base_transform * self.rootItem().transform()
            )
            self.__ratio *= 0.92
        elif timer_id == self.__fit_timerid:
            if not self.__rootitem:
                self.killTimer(self.__fit_timerid)
                return
            time_ratio = (time.time() - self.__fit_starttime) / self.AnimTime
            if time_ratio >= 1:
                self.killTimer(self.__fit_timerid)
                self.__fit_timerid = None
                self.__ignore_animation_canceld = True
                transform = self.__fit_goal_transform
            else:
                moving_ratio = uilib.accelarate(time_ratio, 4)
                transformA = self.__fit_start_transform
                transformB = self.__fit_goal_transform
                
                a = [
                    transformA.m11(), transformA.m12(), transformA.m13(),
                    transformA.m21(), transformA.m22(), transformA.m23(),
                    transformA.m31(), transformA.m32(), transformA.m33(),
                ]
                b = [
                    transformB.m11(), transformB.m12(), transformB.m13(),
                    transformB.m21(), transformB.m22(), transformB.m23(),
                    transformB.m31(), transformB.m32(), transformB.m33(),
                ]
                transform = QtGui.QTransform(
                    *[x + ((y - x) *  moving_ratio) for x, y in zip(a, b)]
                )
            self.rootItem().setTransform(transform)

        super(GraphicsItemListScene, self).timerEvent(event)

class GraphicsItemView(QtWidgets.QGraphicsView):
    r'''
        @brief       ここに説明文を記入
        @inheritance QtWidgets.QGraphicsView
        @date        2017/01/21 23:58[Eske](eske3g@gmail.com)
        @update      2017/01/21 23:58[Eske](eske3g@gmail.com)
    '''
    def __init__(self, parent=None):
        r'''
            @brief  ここに説明文を記入
            @param  parent(None) : [edit]
            @return None
        '''
        super(GraphicsItemView, self).__init__(parent)

        self.setCacheMode(QtWidgets.QGraphicsView.CacheBackground)
        self.setRenderHints(
            QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform |
            QtGui.QPainter.TextAntialiasing
        )
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        scene = self.createScene()(self)
        scene.setSceneRect(QtCore.QRectF(self.rect()))
        self.setScene(scene)

    def createScene(self):
        r'''
            @brief  このViewにセットするGraphicsSceneクラスオブジェクトを返す
            @brief  メソッド。カスタムしたsceneを使用したい場合はこの
            @brief  メソッドをオーバーライドする。
            @return None
        '''
        return GraphicsItemListScene

    def clear(self):
        r'''
            @brief  内部アイテムをクリアする命令をGraphicsSceneに送るメソッド。
            @return None
        '''
        self.scene().clear()

    def fitScene(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        self.scene().setSceneRect(QtCore.QRectF(self.rect()))

    def resizeEvent(self, event):
        r'''
            @brief  リサイズ時の挙動を定義する再実装関数。
            @param  event : [QEvent]
            @return None
        '''
        super(GraphicsItemView, self).resizeEvent(event)
        self.fitScene()

class GraphicsStandardItem(QtWidgets.QGraphicsRectItem):
    r'''
        @brief       ここに説明文を記入
        @inheritance QtWidgets.QGraphicsRectItem
        @date        2017/01/21 23:58[Eske](eske3g@gmail.com)
        @update      2017/01/21 23:58[Eske](eske3g@gmail.com)
    '''
    def __init__(self, itemRect, rootItem):
        r'''
            @brief  ここに説明文を記入
            @param  itemRect : [edit]
            @param  rootItem : [edit]
            @return None
        '''
        super(GraphicsStandardItem, self).__init__(itemRect, rootItem)
        self.setFlags(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.setBrushSet(QtGui.QColor(70, 70, 70))
        self.setPenSet(QtGui.QColor(32, 32, 32))

        self.__actived = True

    def setActived(self, state):
        r'''
            @brief  ここに説明文を記入
            @param  state : [edit]
            @return None
        '''
        self.__actived = bool(state)
        self.update()

    def isActived(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return self.__actived

    def setBrushSet(
        self, defaultBrush,
        activeBrush=None, hoverBrush=None, deactiveBrush=None
    ):
        r'''
            @brief  ここに説明文を記入
            @param  defaultBrush : [edit]
            @param  activeBrush(None) : [edit]
            @param  hoverBrush(None) : [edit]
            @param  deactiveBrush(None) : [edit]
            @return None
        '''
        self.__d_brush = defaultBrush
        self.__a_brush = activeBrush if activeBrush else defaultBrush
        self.__h_brush = hoverBrush if hoverBrush else defaultBrush
        self.__da_brush = deactiveBrush if deactiveBrush else defaultBrush
        
        self.__brush = self.__d_brush

    def setPenSet(
        self, defaultPen,
        activePen=None, hoverPen=None, deactivePen=None
    ):
        r'''
            @brief  ここに説明文を記入
            @param  defaultPen : [edit]
            @param  activePen(None) : [edit]
            @param  hoverPen(None) : [edit]
            @param  deactivePen(None) : [edit]
            @return None
        '''
        self.__d_pen = defaultPen
        self.__a_pen = activePen if activePen else defaultPen
        self.__h_pen = hoverPen if hoverPen else defaultPen
        self.__da_pen = deactivePen if deactivePen else defaultPen  

    def setFont(self, font):
        r'''
            @brief  ここに説明文を記入
            @param  font : [edit]
            @return None
        '''
        pass

    def setFontTransform(self, transform):
        r'''
            @brief  ここに説明文を記入
            @param  transform : [edit]
            @return None
        '''
        pass

    def currentBrushes(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        if self.isActived():
            if self.isSelected():
                brush = self.__a_brush
                pen = self.__a_pen
            else:
                brush = self.__brush
                pen = self.__d_pen
        else:
            brush = self.__da_brush
            pen = self.__da_pen

        return brush, pen

    def paint(self, painter, option, widget):
        r'''
            @brief  ここに説明文を記入
            @param  painter : [edit]
            @param  option : [edit]
            @param  widget : [edit]
            @return None
        '''
        brush, pen = self.currentBrushes()
        rect = self.boundingRect()
        painter.setBrush(brush)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, 1, 1)

    def hoverEnterEvent(self, event):
        r'''
            @brief  ここに説明文を記入
            @param  event : [edit]
            @return None
        '''
        self.__brush = self.__h_brush
        super(GraphicsStandardItem, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        r'''
            @brief  ここに説明文を記入
            @param  event : [edit]
            @return None
        '''
        self.__brush = self.__d_brush
        super(GraphicsStandardItem, self).hoverLeaveEvent(event)


class GraphicsLabelItem(GraphicsStandardItem):
    r'''
        @brief       ここに説明文を記入
        @inheritance GraphicsStandardItem
        @date        2017/01/21 23:58[Eske](eske3g@gmail.com)
        @update      2017/01/21 23:58[Eske](eske3g@gmail.com)
    '''
    def __init__(self, label, itemRect, rootItem):
        r'''
            @brief  ここに説明文を記入
            @param  label : [edit]
            @param  itemRect : [edit]
            @param  rootItem : [edit]
            @return None
        '''
        super(GraphicsLabelItem, self).__init__(itemRect, rootItem)
        
        self.__textitem = QtWidgets.QGraphicsSimpleTextItem(label, self)
        self.__textitem.setBrush(QtGui.QColor(200, 200, 200))
        self.__textitem.setPen(QtCore.Qt.NoPen)

    def textItem(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return self.__textitem

    def setText(self, text):
        r'''
            @brief  ここに説明文を記入
            @param  text : [edit]
            @return None
        '''
        self.__textitem.setText(text)

    def text(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return self.__textitem.text()

    def setFont(self, font):
        r'''
            @brief  ここに説明文を記入
            @param  font : [edit]
            @return None
        '''
        self.__textitem.setFont(font)

    def setFontTransform(self, transform):
        r'''
            @brief  ここに説明文を記入
            @param  transform : [edit]
            @return None
        '''
        self.__textitem.setTransform(transform)

    def paint(self, painter, option, widget):
        r'''
            @brief  ここに説明文を記入
            @param  painter : [edit]
            @param  option : [edit]
            @param  widget : [edit]
            @return None
        '''
        super(GraphicsLabelItem, self).paint(painter, option, widget)
        brush, pen = self.currentBrushes()

        self.textItem().setBrush(pen)


class GraphicsStandardList(uilib.BlackoutDisplay):
    r'''
        @brief       ここに説明文を記入
        @inheritance uilib.BlackoutDisplay
        @date        2017/01/21 23:58[Eske](eske3g@gmail.com)
        @update      2017/01/21 23:58[Eske](eske3g@gmail.com)
    '''
    selectionChanged = QtCore.Signal(QtWidgets.QGraphicsItem)
    LineColor = QtGui.QColor(200, 200, 200)
    LineAnimTime = 2.5
    def __init__(self, parent=None):
        r'''
            @brief  ここに説明文を記入
            @param  parent(None) : [edit]
            @return None
        '''
        super(GraphicsStandardList, self).__init__(parent)
        self.setStyleSheet(
            'QGraphicsView{'
            'background : color(0, 0, 0, 0);'
            'border : none;'
            '}'
        )
        self.__itemlist = []
        self.__updated = False
        self.__stored_selection = None
        self.__hidden_after_selection = True
        margin = 0
        self.__row_count = 0
        self.__column_count = 0
        
        self.__key_stocker = ''
        self.__key_stocked_time = 0

        self.__itemview = GraphicsItemView(self)
        self.__itemview.installEventFilter(self)
        
        self.__line_draw_timerid = None
        self.__line_draw_starttime = 0.0
        self.__line_refreshed = False

        scene = self.__itemview.scene()
        scene.setOccupancy(0.8)
        scene.selectionChanged.connect(self.updateSelection)
        scene.nothingPointed.connect(self.hide)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.addWidget(self.__itemview)

        # ラベルアイテムの作成。
        font = QtGui.QFont(style.GlobalFont)
        self.__labelitem = QtWidgets.QGraphicsSimpleTextItem('Label')
        self.__labelitem.setBrush(self.LineColor)
        self.__labelitem.setZValue(10)
        self.__labelitem.setFont(font)
        self.__itemview.scene().addItem(self.__labelitem)
        
        self.__h_line = QtWidgets.QGraphicsLineItem()
        self.__h_line.setZValue(10)
        self.__itemview.scene().addItem(self.__h_line)
        
        self.__v_line = QtWidgets.QGraphicsLineItem()
        self.__v_line.setZValue(10)
        self.__itemview.scene().addItem(self.__v_line)

    def createItem(self, text, rect, parentItem, index):
        r'''
            @brief  ここに説明文を記入
            @param  text : [edit]
            @param  rect : [edit]
            @param  parentItem : [edit]
            @param  index : [edit]
            @return None
        '''
        return GraphicsLabelItem(text, rect, parentItem)

    def setHiddenAfterSelection(self, state):
        r'''
            @brief  ここに説明文を記入
            @param  state : [edit]
            @return None
        '''
        self.__hidden_after_selection = bool(state)

    def isHiidenAfterSelection(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return self.__hidden_after_selection

    def updateSelection(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        selected_items = self.itemView().scene().selectedItems()
        if not selected_items:
            return
        self.selectionChanged.emit(
            selected_items[0] if selected_items else None
        )
        if self.isHiidenAfterSelection():
            self.hide()
        else:
            self.setHiddenAfterSelection(True)

    def textList(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        textlist = [x.text() for x in self.itemView().scene().allItems()]
        return textlist if textlist else self.__itemlist[:]

    def findText(self, text):
        r'''
            @brief  ここに説明文を記入
            @param  text : [edit]
            @return None
        '''
        textlist = self.textList()
        if text in textlist:
            return text

    def selectByText(self, text):
        r'''
            @brief  ここに説明文を記入
            @param  text : [edit]
            @return None
        '''
        self.__stored_selection = None
        for item in self.itemView().scene().allItems():
            if item.text() == text:
                item.setSelected(True)
                return True
        if text in self.__itemlist:
            self.__stored_selection = text
            return True
        return False

    def itemSize(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return QtCore.QSize(150, 24)

    def setLabel(self, label):
        r'''
            @brief  ここに説明文を記入
            @param  label : [edit]
            @return None
        '''
        self.__labelitem.setText(label)

    def itemGradient(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        size = self.itemSize()
        gradient = QtGui.QLinearGradient(0, 0, size.width(), size.height())
        return gradient

    def defaultItemGradient(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        gradient = self.itemGradient()
        gradient.setColorAt(1.0, QtGui.QColor(90, 90, 90))
        gradient.setColorAt(0.0, QtGui.QColor(65, 65, 65))
        return gradient

    def selectedItemGradient(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        gradient = self.itemGradient()
        gradient.setColorAt(0.0, QtGui.QColor(35, 80, 125))
        gradient.setColorAt(1.0, QtGui.QColor(45, 100, 198))
        return gradient

    def hoverItemGradient(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        gradient = self.itemGradient()
        gradient.setColorAt(0.0, QtGui.QColor(100, 106, 110))
        gradient.setColorAt(1.0, QtGui.QColor(65, 70, 75))
        return gradient

    def deactiveGradient(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        gradient = self.itemGradient()
        gradient.setColorAt(0.0, QtGui.QColor(100, 100, 100, 60))
        gradient.setColorAt(1.0, QtGui.QColor(60, 60, 60, 100))
        return gradient

    def defaultPen(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return QtGui.QColor(180, 180, 180)

    def selectedPen(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return QtGui.QColor(220, 225, 242)

    def deactivePen(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return QtGui.QColor(120, 120, 120, 60)

    def deactiveItemGradient(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        gradient = self.itemGradient()
        return gradient

    def itemSpacing(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return 20

    def itemView(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return self.__itemview

    def clear(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        self.__updated = False
        self.itemView().clear()

    def addItems(self, items):
        r'''
            @brief  ここに説明文を記入
            @param  items : [edit]
            @return None
        '''
        self.__updated = False
        self.__itemlist = items[:]

    def itemlist(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return self.__itemlist

    def font(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return QtGui.QFont(style.GlobalFont)

    def fontTransform(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        item_size = self.itemSize()
        width, height = item_size.width(), item_size.height()
        font_sizes = {}

        for item in self.__itemlist:
            font_sizes[len(item)] = item
        max_string = font_sizes[max(font_sizes.keys())]

        font = QtGui.QFont(self.font())
        font_bounding_rect = QtGui.QFontMetrics(font).boundingRect(max_string)
        if font_bounding_rect.width() >= width:
            font_scale = (
                float(width) / font_bounding_rect.width()
            ) * 0.8
        elif font_bounding_rect.height() > height:
            font_scale = (
                float(height) / font_bounding_rect.height()
            ) * 0.8
        else:
            font_scale = 1.0

        font_transform = QtGui.QTransform()
        font_transform.scale(font_scale, font_scale)
        font_transform.translate(10, 0)
        return font_transform

    def rowCount(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return self.__row_count

    def columnCount(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return self.__column_count

    def updateList(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        if not self.__itemlist:
            self.__row_count = 0
            self.__column_count = 0
            return
        if  self.__updated:
            return

        self.itemView().clear()

        # ライン描画のフラグをFalseにセットする。
        self.__line_refreshed = False

        default_gradient = self.defaultItemGradient()
        default_pen = self.defaultPen()
        selected_gradient = self.selectedItemGradient()
        selected_pen = self.selectedPen()
        deactive_pen = self.deactivePen()
        hover_gradient = self.hoverItemGradient()
        deactive_gradient = self.deactiveGradient()

        num = len(self.__itemlist)
        column = int(math.sqrt(num)) + 1  if num > 3 else 2

        item_size = self.itemSize()
        width = item_size.width()
        height = item_size.height()
        spacing = self.itemSpacing()

        item_rect = QtCore.QRectF(0, 0, width, height)
        root_item = self.itemView().scene().rootItem()
        transform = QtGui.QTransform()

        font_transform = self.fontTransform()
        row_index = 0
        font = self.font()
        for i in range(num):
            self.__row_count = row_index  # 内部保留変数用。

            frameitem = self.createItem(
                self.__itemlist[i], item_rect, root_item, i
            )
            frameitem.setBrushSet(
                default_gradient,
                selected_gradient, hover_gradient, deactive_gradient
            )
            frameitem.setPenSet(
                default_pen, selected_pen, default_pen, deactive_pen
            )
            frameitem.setFlags(QtWidgets.QGraphicsItem.ItemIsSelectable)
            frameitem.setTransform(transform)

            frameitem.setFont(font)
            frameitem.setFontTransform(font_transform)

            if (i + 1) % column == 0:
                row_index += 1
                transform = QtGui.QTransform()
                transform.translate(0, row_index * (height * 0.9 + spacing))
            else:
                transform.translate(width + spacing, 0)
        self.__updated = True

        if self.__stored_selection:
            self.selectByText(self.__stored_selection)
            self.__stored_selection = None

        self.__column_count = column

    def refreshDisplayState(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        reobj = re.compile(
            ''.join(['[%s%s]' % (x.lower(), x.upper()) for x in self.__key_stocker])
        )
        root_item = self.itemView().scene().rootItem()
        for item in root_item.childItems():
            item.setActived(bool(reobj.search(item.text())))

    def setOccupancyFromItemSize(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        scene = self.itemView().scene()
        occupancy = (self.columnCount() / 6.0)
        occupancy = 0.9 if occupancy > 0.9 else occupancy
        scene.setOccupancy(occupancy)
        
    def show(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        self.updateList()
        self.__key_stocker = ''
        self.refreshDisplayState()
        scene = self.itemView().scene()

        # アイテムの画面占有率を決定する。
        self.setOccupancyFromItemSize()

        scene.setCancelCallIgnored(True)
        super(GraphicsStandardList, self).show()

        # ラベルの位置合わせ。================================================
        rect = self.rect()
        # ラベル位置の設定。
        height = scene.sceneRect().height() / 20.0
        scale = (height / self.__labelitem.boundingRect().height())
        height *= 0.75
        transform = QtGui.QTransform()
        transform.translate(height * 1.1, height)
        transform.scale(scale, scale)
        self.__labelitem.setTransform(transform)
        label_rect = self.__labelitem.boundingRect()

        if not self.__line_refreshed:
            h_line = QtCore.QLineF(0, 0, 1, 0)
            v_line = QtCore.QLineF(0, 0, 0, 1)
        else:
            h_line = QtCore.QLineF(0, 0, rect.width(), 0)
            v_line = QtCore.QLineF(0, 0, 0, rect.height())

        # 横線の設定。
        pen = QtGui.QPen(self.LineColor, 2)
        transform = QtGui.QTransform()
        transform.translate(0, height * 1.1 + label_rect.height() * scale)

        self.__h_line.setPen(pen)
        self.__h_line.setTransform(transform)
        self.__h_line.setLine(h_line)
        
        # 縦線の設定。
        line = QtCore.QLineF(0, 0, 0, 1)
        transform = QtGui.QTransform()
        transform.translate(height, 0)
        
        self.__v_line.setPen(pen)
        self.__v_line.setTransform(transform)
        self.__v_line.setLine(v_line)
        # ====================================================================

        scene.adjust(scene.centerTransform(1.25))
        super(GraphicsStandardList, self).show()
        scene.fitAll()
        
        # アイテムの更新があった場合のみライン描画アニメーションを行う。
        if self.__line_refreshed:
            return
        if self.__line_draw_timerid:
            self.killTimer(self.__line_draw_timerid)
        self.__line_draw_starttime = time.time()
        self.__line_draw_timerid = self.startTimer(10)
        self.__line_refreshed = True

    def timerEvent(self, event):
        r'''
            @brief  ここに説明文を記入
            @param  event : [edit]
            @return None
        '''
        if event.timerId() == self.__line_draw_timerid:
            time_ratio = (
                (time.time() - self.__line_draw_starttime) / self.LineAnimTime
            )
            rect = self.rect()
            if time_ratio >= 1:
                self.killTimer(self.__line_draw_timerid)
                self.__line_draw_timerid = None
                width = rect.width()
                height = rect.height()
            else:
                time_ratio = uilib.accelarate(time_ratio, 16)
                width = rect.width() * time_ratio
                height = rect.height() * time_ratio
            h_line = QtCore.QLineF(0, 0, width, 0)
            v_line = QtCore.QLineF(0, 0, 0, height)
            self.__h_line.setLine(h_line)
            self.__v_line.setLine(v_line)
        else:
            super(GraphicsStandardList, self).timerEvent(event)

    def keyPressEvent(self, event):
        r'''
            @brief  ここに説明文を記入
            @param  event : [edit]
            @return None
        '''
        key = event.key()
        mod = event.modifiers()

        if time.time() - self.__key_stocked_time > 0.5:
            self.__key_stocker = ''

        if key in uilib.QtAlphabetKeys:
            self.__key_stocker += uilib.QtAlphabetKeys[key]
        else:
            self.__key_stocker = ''

        self.refreshDisplayState()
        self.__key_stocked_time = time.time()

        #super(GraphicsStandardList, self).keyPressEvent(event)

# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////