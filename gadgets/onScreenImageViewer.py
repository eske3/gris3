#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    画像を表示するためのビューワ機能を提供するクラス

    Dates:
        date:2026/05/25 12:10 Eske Yoshinob[eske3g@gmail.com]
        update:2026/05/25 12:14 Eske Yoshinob[eske3g@gmail.com]

    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from __future__ import annotations

import math
from .. import uilib
from ..uilib import mayaUIlib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

_ImageViewerObject = None
_HELP_TEXT ='''<h1>Operation</h1>
<p>Move Image   : Drag MLB</p>
<p>Scale Image  : Drag MRB</p>
<p>Rotate Image : Drag MLB + MRB</p>
<p>Flip image horizontally : Double click MLB</p>
<p>Flip image vertically   : Double click MRB</p>
<br>
<h1>Short Cut</h1>
<p>r : Reset rotation</p>
<p>f : Fit view</p>
<p>del : Delete image</p>
<br>
<h1>Notes</h1>
<p>Press shift key when operating: Apply operation to all</p>
'''
_STYLE = '''
QToolTip{
    background-color: #AAAAA;
}
'''

class ImageItem(QtWidgets.QGraphicsObject):
    r"""
    イメージを表示するためのアイテム。
    """
    def __init__(self, pixmap, parent=None):
        r"""
        Args:
            pixmap(QtGui.QPixmap):対象となる画像オブジェクト
            parent(QtWidgets.QGraphicsObject):親オブジェクト
        """
        super().__init__(parent)
        self.pixmap = pixmap
        self.rect = QtCore.QRectF(
            0.0, 0.0, float(pixmap.width()), float(pixmap.height())
        )

        self.ext_scale = 1.0
        self.rotation_deg = 0.0
        self.flip_x = 1.0
        self.flip_y = 1.0
        self.local_pivot = self.rect.center()

        self.inner_scale = 1.0
        self.inner_offset = QtCore.QPointF(0.0, 0.0)
        self.is_active = False

    def boundingRect(self):
        r"""


        Returns:
            QtCore.QRectF:
        """
        return self.rect

    def shape(self):
        r"""
        形状オブジェクトを返す。

        Returns:
            QtGui.QPainterPath:
        """
        p = QtGui.QPainterPath()
        p.addRect(self.rect)
        return p

    def paint(self, painter, option, widget=None):
        r"""
        Args:
            painter(QtGui.QPainter):
            option(QtWidgets.QStyleOptionGraphicsItem):
            widget(QtWidgets.QWidget):
        """
        painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)
        painter.save()
        painter.setClipRect(self.rect)

        t = QtGui.QTransform()
        t.translate(self.inner_offset.x(), self.inner_offset.y())
        t.scale(self.inner_scale, self.inner_scale)
        painter.setTransform(t, True)
        painter.drawPixmap(0, 0, self.pixmap)
        painter.restore()

        if self.is_active:
            painter.save()
            pen = QtGui.QPen(QtGui.QColor(38, 111, 255, 255))
            pen.setWidth(1.0)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(QtCore.Qt.NoBrush)
            painter.drawRect(self.rect)
            painter.restore()

    def setPivot(self, scenePos):
        r"""
        Args:
            scenePos(QtCore.QPointF):
        """
        self.local_pivot = self.mapFromScene(scenePos)
        self.applyExternalTransform()

    def applyExternalTransform(self):
        r"""
        内部データに基づいて回転・スケールを行う。
        """
        sx = self.ext_scale * self.flip_x
        sy = self.ext_scale * self.flip_y
        px = self.local_pivot.x()
        py = self.local_pivot.y()

        t = QtGui.QTransform()
        t.translate(px, py)
        t.rotate(self.rotation_deg)
        t.scale(sx, sy)
        t.translate(-px, -py)
        self.setTransform(t, False)
        self.update()

    def applyExternalTransformWithPivot(self, pivot, scenePivot):
        r"""

        Args:
            pivot(QtCore.QPointF):
            scenePivot(QtCore.QPointF):
        """
        self.local_pivot = pivot
        self.applyExternalTransform()

        cur_scene_piv = self.mapToScene(pivot)
        delta = scenePivot - cur_scene_piv
        self.setPos(self.pos() + delta)

    def translate(self, delta):
        r"""
        オブジェクトを移動する。

        Args:
            delta(QtCore.QPointF):
        """
        self.setPos(self.pos() + delta)

    def scaleWithPivot(self, factor, pivot):
        r"""
        ピボット位置を基準にスケールをかける。

        Args:
            factor(float):
            pivot(QtCore.QPointF):
        """
        self.setPivot(pivot)
        self.ext_scale = max(0.01, self.ext_scale * factor)
        self.applyExternalTransform()

    def rotateWithPivot(self, delta, pivot):
        r"""
        ピボット位置を基準に回転をかける。

        Args:
            delta(float): 回転値（Degree)
            pivot(QtCore.QPointF):
        """
        self.setPivot(pivot)
        self.rotation_deg = delta
        self.applyExternalTransform()

    def flip(self, flipX=True, flipY=False):
        if flipX:
            self.flip_x *= -1.0
        elif flipY:
            self.flip_y *= -1.0
        else:
            return
        local_pivot = self.local_pivot
        self.local_pivot = self.rect.center()
        self.applyExternalTransform()
        self.local_pivot = local_pivot

    def resetScale(self):
        self.ext_scale = 1.0
        self.applyExternalTransform()

    def resetRotation(self):
        self.rotation_deg = 0.0
        self.applyExternalTransform()

    def resetInnerScale(self):
        self.inner_scale = 1.0
        self.inner_offset = QtCore.QPointF(0.0, 0.0)
        self.update()

    def innerTranslate(self, delta):
        delta = delta / self.ext_scale
        new_ox = self.inner_offset.x() + delta.x()
        new_oy = self.inner_offset.y() + delta.y()
        self.inner_offset = QtCore.QPointF(new_ox, new_oy)
        self.update()

    def innerScaleWithPivot(self, factor, pivot):
        r"""
        オブジェクトのフレームは変えずに内部の画像だけスケールをかける。
        （画像スケールがオブジェクトのスケールを超えた場合クリップされた状態になる）

        Args:
            factor(float):
            pivot(QtCore.QPointF):
        """
        local_pivot = self.mapFromScene(pivot)
        prev = self.inner_scale
        new_scale = max(0.01, prev * factor)
        dff = prev - new_scale
        if abs(dff) < 1e-8:
            return

        ox = self.inner_offset.x()
        oy = self.inner_offset.y()
        px = local_pivot.x()
        py = local_pivot.y()

        new_ox = ox + dff * px
        new_oy = oy + dff * py

        self.inner_scale = new_scale
        self.inner_offset = QtCore.QPointF(new_ox, new_oy)
        self.update()


class DesktopImageViewer(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowFlags(QtCore.Qt.Tool | QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.NoAnchor)
        self.setResizeAnchor(QtWidgets.QGraphicsView.NoAnchor)
        self.setRenderHints(
            QtGui.QPainter.Antialiasing
            | QtGui.QPainter.SmoothPixmapTransform
        )
        self.setStyleSheet('background: transparent;')
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
        self.setMouseTracking(True)

        self.scene = QtWidgets.QGraphicsScene(self)
        self.scene.setBackgroundBrush(QtCore.Qt.transparent)
        self.setScene(self.scene)

        self.desktopRect = self._virtual_desktop_rect()
        self.setGeometry(self.desktopRect)
        self.scene.setSceneRect(QtCore.QRectF(self.desktopRect))

        self._active_items = {}
        self._mode = None
        self._last_scene_pos = None
        self._start_scene_pos = None
        self._z_counter = 1.0
        self.__allow_image_addition = True

    def allowImageAddition(self, state):
        self.__allow_image_addition = bool(state)

    def _virtual_desktop_rect(self):
        r"""
        デスクトップ全体の矩形情報を返す。

        Returns:
            QtCore.QRect:
        """
        screens = QtWidgets.QApplication.screens()
        if not screens:
            return QtWidgets.QApplication.primaryScreen()
        rect = screens[0].geometry()
        for s in screens[1:]:
            rect = rect.united(s.geometry())
        return rect

    def screenAtPoint(self, point):
        screens = QtWidgets.QApplication.screens()
        for s in screens:
            rect: QtCore.QRect = s.geometry()
            if rect.contains(point):
                return rect
        return QtWidgets.QApplication.primaryScreen()

    def _scene_pos_from_event(self, event):
        r"""
        与えられたイベントからシーンにマッピングした位置情報を返す。

        Args:
            event:

        Returns:
            QtCore.QPointF:
        """
        if hasattr(event, 'localPos'):
            return self.mapToScene(event.localPos().toPoint())
        return self.mapToScene(event.pos())

    def allItems(self):
        r"""
        すべてのイメージアイテムを返す。

        Returns:
            list(ImageItems):
        """
        return [i for i in self.scene.items() if isinstance(i, ImageItem)]

    def selectedItems(self):
        r"""
        選択されているイメージアイテムをすべて返す。

        Returns:
            list(ImageItem):
        """
        return [
            x for x in self.scene.selectedItems() if isinstance(x, ImageItem)
        ]

    def _item_from_event(self, event, affectsToAll=False):
        r"""
        与えられたイベントの位置情報から、シーン中のアイテムを特定し返す。

        Args:
            event:

        Returns:
            list(ImageItem):
        """
        if event.modifiers() & QtCore.Qt.ShiftModifier:
            all_items = self.allItems()
            if affectsToAll:
                return all_items
            screen = self.screenAtPoint(event.pos())
            results = []
            viewport = self.viewport()
            for item in all_items:
                scene_rect = item.sceneBoundingRect()
                view_polygon = self.mapFromScene(scene_rect)
                view_rect = view_polygon.boundingRect()
                tl = viewport.mapToGlobal(view_rect.topLeft())
                br = viewport.mapToGlobal(view_rect.bottomRight())
                item_rect = QtCore.QRect(tl, br).normalized()
                if screen.intersects(item_rect):
                    results.append(item)
            return results

        selected = self.selectedItems()
        if selected:
            return selected

        if hasattr(event, 'pos'):
            vp = event.pos()
        elif hasattr(event, 'localPos'):
            vp = event.localPos().toPoint()
        else:
            return []
        it = self.itemAt(vp)
        if isinstance(it, ImageItem):
            return [it]
        return []

    def _bring_to_front(self, items):
        r"""
        任意のアイテムを手前に表示する。

        Args:
            item(list):ImageItem
        """
        for item in items:
            self._z_counter += 1.0
            item.setZValue(self._z_counter)

    def addImage(self, imagePath, center=False):
        r"""
        画像を新たに追加する。
        
        Args:
            imagePath(str): 表示する画像ファイルのパス
            center(bool): 画面にフィットさせるかどうか

        Returns:
            ImageItem:
        """
        pix = QtGui.QPixmap(imagePath)
        if pix.isNull():
            return None
        item = ImageItem(pix)
        self.scene.addItem(item)

        self._bring_to_front([item])
        return item

    def layoutImagesToCursorDesktop(self, items, sortFromPosition=True):
        r"""
        任意のアイテムをマウスカーソルが置いてあるデスクトップに横一列に並べる。

        Args:
            items(list): ImageItemのリスト
        """
        if not items:
            return

        cursor_pos = QtGui.QCursor.pos()
        desk = self.screenAtPoint(cursor_pos)

        desk_left = float(desk.left())
        desk_top = float(desk.top())
        desk_w = float(desk.width())
        desk_h = float(desk.height())

        if sortFromPosition:
            buffer = {}
            for item in items:
                item: ImageItem = item
                buffer.setdefault(item.pos().x(), []).append(item)
            keys = list(buffer.keys())
            keys.sort()
            items = []
            for k in keys:
                items.extend(buffer[k])

        widths = []
        heights = []
        for it in items:
            pm = it.pixmap
            base_scale = abs(float(getattr(it, 'ext_scale', 1.0)))
            w = float(pm.width()) * base_scale
            h = float(pm.height()) * base_scale
            widths.append(max(1e-6, w))
            heights.append(max(1e-6, h))
        total_w = sum(widths)
        if total_w <= 0.0:
            return
        k = desk_w / total_w
        m_height = max(heights) * k
        if m_height > desk_h:
            k = k * desk_h / m_height

        x = desk_left
        view = self.scene.views()
        if not view:
            return
        view = view[0]
        for it, w0 in zip(items, widths):
            old_scale = float(getattr(it, 'ext_scale', 1.0))
            it.ext_scale = old_scale * k
            it.applyExternalTransform()

            # 左から順に配置（上端揃え）
            new_pos = QtCore.QPoint(x, desk_top)
            view_pos = view.mapFromGlobal(new_pos)
            tgt_scene = view.mapToScene(view_pos)
            cur_tl = it.mapToScene(QtCore.QPointF(0.0, 0.0))
            delta = tgt_scene - cur_tl
            it.translate(delta)
            x += w0 * k

    def addImageFromDialog(self):
        r"""
        ファイルダイアログを表示し、画像を追加する。

        Returns:
            list:追加されたImageItemのリスト
        """
        paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            mayaUIlib.MainWindow, 'Add Images', '',
            'Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.gif)'
        )
        items = []
        for p in paths:
            items.append(self.addImage(p, center=False))
        self.layoutImagesToCursorDesktop(items, False)

    def deleteItem(self, item, closeIfItemIsNothing=True):
        r"""
        任意のアイテムを削除する。
        また、closeIfItemIsNothingがTrueの場合、削除後アイテムが空であれば
        ウインドウを閉じる。

        Args:
            item(ImageItem): 操作対象となるアイテム。
            closeIfItemIsNothing(bool):削除後ウインドウを閉じるかどうか
        """
        self.scene.removeItem(item)
        del item

        if not closeIfItemIsNothing:
            return
        has_image_item = any(
            isinstance(i, ImageItem) for i in self.scene.items()
        )
        if not has_image_item:
            self.close()

    def deleteItemUnderCursor(self):
        r"""
        マウスカーソル下のアイテムを削除する。
        削除した場合はTrueを返す。

        Returns:
            bool:
        """
        view_pos = self.mapFromGlobal(QtGui.QCursor.pos())
        item = self.itemAt(view_pos)

        if not isinstance(item, ImageItem):
            return False

        # 操作中ターゲットなら解除
        if item in self._active_items:
            self._active_items = []
            self._left_drag = False
            self._right_drag = False

        self.deleteItem(item)
        return True

    def mousePressEvent(self, event):
        scene_pos = self.mapToScene(event.position().toPoint())
        left = bool(event.buttons() & QtCore.Qt.LeftButton)
        right = bool(event.buttons() & QtCore.Qt.RightButton)
        mods = event.modifiers()

        items = self._item_from_event(event)
        self._active_items = {}
        self._last_scene_pos = scene_pos
        self._start_scene_pos = scene_pos
        self._mode = None

        if items:
            for item in items:
                self._active_items[item] = {
                    'local_pivot': item.mapFromScene(scene_pos),
                    'scene_pivot': QtCore.QPointF(scene_pos),
                    'ext_scale': item.ext_scale,
                    'rotation_deg': item.rotation_deg,
                }
                item.is_active = True
            self._bring_to_front(items)

            if left and right:
                self._mode = 'rotate'
            elif right and mods & QtCore.Qt.ControlModifier:
                self._mode = 'inner_scale'
            elif right:
                self._mode = 'scale'
            elif left and mods & QtCore.Qt.ControlModifier:
                self._mode = 'inner_move'
            elif left:
                self._mode = 'move'

            if self._mode:
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self._mode or not self._active_items:
            super().mouseMoveEvent(event)
            return

        scene_pos = self._scene_pos_from_event(event)
        prev = self._last_scene_pos
        delta = scene_pos - prev

        total = scene_pos - self._start_scene_pos
        if self._mode == 'move':
            for i in self._active_items:
                i.translate(delta)
        elif self._mode == 'inner_move':
            for i in self._active_items:
                i.innerTranslate(delta)
        elif self._mode == 'scale':
            d = total.x() + total.y()
            factor = math.exp(d * 0.01)

            for i, cache in self._active_items.items():
                i.ext_scale = max(0.05, cache['ext_scale'] * factor)
                i.applyExternalTransformWithPivot(
                    cache['local_pivot'], cache['scene_pivot']
                )
        elif self._mode == 'rotate':
            deg = total.x() * 0.5
            for i, cache in self._active_items.items():
                i.rotation_deg = cache['rotation_deg'] + deg
                i.applyExternalTransformWithPivot(
                    cache['local_pivot'], cache['scene_pivot']
                )
        elif self._mode == 'inner_scale':
            d = delta.x() + delta.y()
            factor = math.exp(d * 0.01)
            factor = max(0.1, min(10.0, factor))
            for i in self._active_items:
                i.innerScaleWithPivot(factor, scene_pos)

        self._last_scene_pos = scene_pos
        event.accept()

    def mouseReleaseEvent(self, event):
        for item in self._active_items:
            item.is_active = False
        self._active_items = {}
        self._mode = None
        self._last_scene_pos = None
        self._start_scene_pos = None
        event.accept()

    def mouseDoubleClickEvent(self, event):
        items = self._item_from_event(event)
        if not items:
            return

        self._bring_to_front(items)
        if event.button() == QtCore.Qt.LeftButton:
            x = True
            y = False
        elif event.button() == QtCore.Qt.RightButton:
            x = False
            y = True

        for item in items:
            item.flip(x, y)

        event.accept()

    def wheelEvent(self, event):
        items = self._item_from_event(event)
        if not items:
            return

        self._bring_to_front(items)
        d = event.angleDelta().y()
        if d == 0:
            return
        factor = 1.15 ** (d / 120.0)
        pivot = self._scene_pos_from_event(event)
        for item in items:
            item.scaleWithPivot(factor, pivot)
        event.accept()

    def keyPressEvent(self, event):
        key = event.key()
        mod = event.modifiers()

        is_deleting = key in (
            QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Delete, QtCore.Qt.Key_W
        )
        affects_to_all = is_deleting and mod & QtCore.Qt.ControlModifier
        # カーソル下の画像を優先、なければ最前面画像を対象
        mouse_event = QtGui.QMouseEvent(
            QtCore.QEvent.MouseMove,
            self.mapFromGlobal(QtGui.QCursor.pos()),
            QtCore.Qt.NoButton, QtCore.Qt.NoButton, mod
        )
        targets = self._item_from_event(mouse_event, affects_to_all)

        if targets:
            if key == QtCore.Qt.Key_R:
                for target in targets:
                    target.resetRotation()
                event.accept()
                return
            if key == QtCore.Qt.Key_F:
                self.layoutImagesToCursorDesktop(targets)
                event.accept()
                return
            if key == QtCore.Qt.Key_S and mod == QtCore.Qt.ControlModifier:
                for target in targets:
                    target.resetInnerScale()
                event.accept()
                return
            if key == QtCore.Qt.Key_S:
                for target in targets:
                    target.resetScale()
                event.accept()
                return
            if is_deleting:
                for target in targets:
                    self.deleteItem(target)
                event.accept()
                return

        if (
            self.__allow_image_addition and key == QtCore.Qt.Key_O
            and mod == QtCore.Qt.ControlModifier
        ):
            self.addImageFromDialog()
            event.accept()
            return

        super(DesktopImageViewer, self).keyPressEvent(event)


def showWindow(files=None, parent=None):
    r"""
    画像ビューアを表示するエントリ関数。
    この関数から表示するDestopImageViewerは同じものを返す。

    Args:
        files(list):表示させる画像ファイルパスのリスト
        parent(QtWidgets.QWidget):親ウィジェット

    Returns:
        DesktopImageViewer:
    """
    global _ImageViewerObject
    files = files or []
    if _ImageViewerObject is None:
        parent = parent or mayaUIlib.MainWindow
        _ImageViewerObject = DesktopImageViewer(parent=parent)
    items = []
    for file in files:
        items.append(_ImageViewerObject.addImage(file))
    if items:
        _ImageViewerObject.layoutImagesToCursorDesktop(items, False)


    if not _ImageViewerObject.allItems():
        _ImageViewerObject.addImageFromDialog()

    _ImageViewerObject.show()
    _ImageViewerObject.setFocus()

    return _ImageViewerObject