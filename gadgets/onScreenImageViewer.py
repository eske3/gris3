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

class ImageItem(QtWidgets.QGraphicsPixmapItem):
    r"""
    イメージを表示するためのアイテム。
    """
    def __init__(self, pixmap):
        super(ImageItem, self).__init__(pixmap)
        self.setTransformationMode(QtCore.Qt.SmoothTransformation)
        self.setShapeMode(QtWidgets.QGraphicsPixmapItem.BoundingRectShape)

        self.base_scale = 1.0
        self.rotation_deg = 0.0
        self.flip_x = 1.0
        self.flip_y = 1.0

        self._zoom = 1.0
        self._anchor = QtCore.QPointF(0, 0)
        self._last_pos = QtCore.QPointF(0, 0)

        self.setAcceptedMouseButtons(QtCore.Qt.RightButton)

    def boundingRect(self):
        pixmap = self.pixmap()
        return QtCore.QRectF(0, 0, pixmap.width(), pixmap.height())

    def paint(self, painter, option, widget=None):
        pm = self.pixmap()
        if pm.isNull():
            return

        w, h = pm.width(), pm.height()
        z = max(0.2, min(8.0, self._zoom))

        # ズーム率から「元画像のどの範囲を切り出すか」を計算
        src_w = w / z
        src_h = h / z
        cx = self._anchor.x()
        cy = self._anchor.y()

        left = cx - src_w * 0.5
        top = cy - src_h * 0.5

        # はみ出し防止
        left = max(0.0, min(left, w - src_w))
        top = max(0.0, min(top, h - src_h))

        src = QtCore.QRectF(left, top, src_w, src_h)
        dst = self.boundingRect()

        painter.drawPixmap(dst, pm, src)
        # painter.save()
        # painter.setClipRect(self.boundingRect())
        #
        # t = QtGui.QTransform()
        # t.translate(self._anchor.x(), self._anchor.y())
        # t.scale(self._scale, self._scale)
        # t.translate(-self._anchor.x(), -self._anchor.y())
        # painter.setTransform(t, combine=True)
        # painter.drawPixmap(0, 0, self.pixmap())
        #
        # painter.restore()

    def setupToClip(self, pos):
        p = self.mapFromScene(pos)
        self._last_pos = p
        self._anchor = p

    def doClip(self, pos, factor):
        r"""
        Args:
            event(QtWidgets.QGraphicsSceneMouseEvent):
        """
        p = self.mapFromScene(pos)
        self._zoom = max(0.2, min(8.0, self._zoom * factor))
        self._anchor = p
        self._last_pos = p
        self.update()

    def setTransformData(self, scale=1.0, rot=0.0, flipX=1.0, flipY=1.0):
        r"""
        トランスフォーム情報を一括で設定する。

        Args:
            scale(float): スケール値
            rot(float): 回転値（Degree)
            flipX(float): 水平方向のフリップ値
            flipY(float): 垂直方向のフリップ値
        """
        self.base_scale = scale
        self.rotation_deg = rot
        self.flip_x = flipX
        self.flip_y = flipY

    def rebuildTransform(self):
        r"""
        指定した変形情報に基づいて本オブジェクトを変形する。
        """
        t = QtGui.QTransform()
        t.scale(self.base_scale * self.flip_x, self.base_scale * self.flip_y)
        t.rotate(self.rotation_deg)
        self.setTransform(t, False)


class DesktopImageViewer(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super(DesktopImageViewer, self).__init__(parent)

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

        self._last_scene_pos = QtCore.QPointF()
        self._left_drag = False
        self._right_drag = False
        self._active_items = []
        self._z_counter = 1.0
        self._clip_mode = False

        self.__allow_image_addition = True

        self.viewport().setStyleSheet(_STYLE)
        self.viewport().setToolTip(_HELP_TEXT)

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
            return QtCore.QRect(0, 0, 1920, 1080)
        rect = screens[0].geometry()
        for s in screens[1:]:
            rect = rect.united(s.geometry())
        return rect

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

    def _item_from_event(self, event, isAll=False):
        r"""
        与えられたイベントの位置情報から、シーン中のアイテムを特定し返す。

        Args:
            event:
            isAll(bool):

        Returns:
            list(ImageItem):
        """
        if isAll:
            return self.allItems()
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

    def _bring_to_front(self, item):
        r"""
        任意のアイテムを手前に表示する。

        Args:
            item(ImageItem):
        """
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

        if center:
            dw = float(self.desktopRect.width())
            dh = float(self.desktopRect.height())
            iw = float(pix.width())
            ih = float(pix.height())
            if iw > 0 and ih > 0:
                s = min(dw / iw, dh / ih)
            else:
                s = 1.0
            item.setTransformData(s)
            item.rebuildTransform()

            cx = self.desktopRect.left() + dw * 0.5
            cy = self.desktopRect.top() + dh * 0.5
            item.setPos(cx - (iw * s) * 0.5, cy - (ih * s) * 0.5)
        else:
            item.setTransformData()
            item.rebuildTransform()

            c = self.mapToScene(self.viewport().rect().center())
            item.setPos(c.x() - pix.width() * 0.5, c.y() - pix.height() * 0.5)

        self._bring_to_front(item)
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
        screen = QtGui.QGuiApplication.screenAt(cursor_pos)
        if screen is None:
            screen = QtWidgets.QApplication.primaryScreen()
        if screen is None:
            return

        desk = screen.geometry()
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

        # 現在の見かけ幅（回転は無視）を基準に比率を作る
        widths = []
        heights = []
        for it in items:
            pm = it.pixmap()
            base_scale = abs(float(getattr(it, "base_scale", 1.0)))
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
        for it, w0 in zip(items, widths):
            old_scale = float(getattr(it, "base_scale", 1.0))
            it.base_scale = old_scale * k
            it.rebuildTransform()

            # 左から順に配置（上端揃え）
            it.setPos(x, desk_top)
            x += w0 * k

            self._bring_to_front(it)

        self._active_items = items[:]

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

    def applyScaleToItem(self, item, factor, scenePivot):
        r"""
        任意のアイテムをシーン中のピボット位置をベースにスケールする。

        Args:
            item(ImageItem):操作対象アイテム
            factor(float):
            scenePivot(QtCore.QPointF):ピボット位置
        """
        factor = max(0.02, min(50.0, factor))
        old = item.base_scale
        new = max(0.01, min(100.0, old * factor))
        actual = new / old if old != 0 else 1.0
        if abs(actual - 1.0) < 1e-8:
            return

        local = item.mapFromScene(scenePivot)
        item.base_scale = new
        item.rebuildTransform()

        mapped = item.mapToScene(local)
        delta = scenePivot - mapped
        item.setPos(item.pos() + delta)

    def applyRotationToItem(self, item, rot, scenePivot):
        r"""
        任意のアイテムを回転させる。

        Args:
            item(ImageItem): 操作対象アイテム
            rot(float):回転角度（Degree）
            scenePivot(QtCore.QPointF): ピボット位置
        """
        local = item.mapFromScene(scenePivot)
        item.rotation_deg += rot
        item.rebuildTransform()

        mapped = item.mapToScene(local)
        delta = scenePivot - mapped
        item.setPos(item.pos() + delta)

    def applyFlipToItem(self, item, flipX, flipY, scenePivot):
        r"""
        アイテムを任意の倍率で水平・垂直にフリップする。

        Args:
            item(ImageItem): 操作対象アイテム
            flipX(float): 水平方向のフリップ倍率
            flipY(float): 垂直方向のフリップ倍率
            scenePivot(QtCore.QPointF): ピボット位置
        """
        local = item.mapFromScene(scenePivot)
        item.flip_x *= flipX
        item.flip_y *= flipY
        item.rebuildTransform()

        mapped = item.mapToScene(local)
        delta = scenePivot - mapped
        item.setPos(item.pos() + delta)

    def fitItemToScene(self, item):
        r"""
        任意のアイテムを画面全体にフィットさせる。

        Args:
            item(ImageItem):
        """
        pix = item.pixmap()
        iw = float(pix.width())
        ih = float(pix.height())
        if iw <= 0 or ih <= 0:
            return

        dw = float(self.desktopRect.width())
        dh = float(self.desktopRect.height())
        s = min(dw / iw, dh / ih)

        item.base_scale = s
        item.rotation_deg = 0.0
        item.flip_x = 1.0
        item.flip_y = 1.0
        item.rebuildTransform()

        cx = self.desktopRect.left() + dw * 0.5
        cy = self.desktopRect.top() + dh * 0.5
        item.setPos(cx - (iw * s) * 0.5, cy - (ih * s) * 0.5)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._left_drag = True
        if event.button() == QtCore.Qt.RightButton:
            self._right_drag = True
        mod = event.modifiers()
        apply_to_all = mod == QtCore.Qt.ShiftModifier
        self._clip_mode = mod == QtCore.Qt.ControlModifier

        self._last_scene_pos = self._scene_pos_from_event(event)
        self._active_items = self._item_from_event(event, apply_to_all)
        if self._active_items:
            for item in self._active_items:
                item.setupToClip(self._last_scene_pos)
                self._bring_to_front(item)
        event.accept()

    def mouseMoveEvent(self, event):
        if not self._active_items:
            return

        scene_pos = self._scene_pos_from_event(event)
        d = scene_pos - self._last_scene_pos
        self._last_scene_pos = scene_pos

        both = self._left_drag and self._right_drag
        left = self._left_drag and not self._right_drag
        right = self._right_drag and not self._left_drag

        if both:
            # 左右同時: 水平方向ドラッグで回転（ピボット=カーソル）
            for item in self._active_items:
                self.applyRotationToItem(item, d.x() * 0.5, scene_pos)
        elif left:
            # パン: 常にマウスと同速度
            for item in self._active_items:
                item.setPos(item.pos() + d)
        elif right:
            # 右へドラッグで拡大、左へで縮小
            factor = 1.0 + d.x() * 0.0025
            for item in self._active_items:
                if self._clip_mode:
                    item.doClip(scene_pos, factor)
                else:
                    self.applyScaleToItem(item, factor, scene_pos)

        event.accept()

    def mouseReleaseEvent(self, event):
        self._left_drag = False
        self._right_drag = False
        self._clip_mode = False
        self._active_items = []
        event.accept()

    def mouseDoubleClickEvent(self, event):
        item = self._item_from_event(event)
        if item is None:
            return

        self._bring_to_front(item)
        pivot = self._scene_pos_from_event(event)

        if event.button() == QtCore.Qt.LeftButton:
            self.applyFlipToItem(item, -1.0, 1.0, pivot)
        elif event.button() == QtCore.Qt.RightButton:
            self.applyFlipToItem(item, 1.0, -1.0, pivot)

        event.accept()

    def wheelEvent(self, event):
        item = self._item_from_event(event)
        if item is None:
            return

        self._bring_to_front(item)
        d = event.angleDelta().y()
        if d == 0:
            return
        factor = 1.15 ** (d / 120.0)
        pivot = self._scene_pos_from_event(event)
        self.applyScaleToItem(item, factor, pivot)
        event.accept()

    def allItems(self):
        r"""
        すべてのイメージアイテムを返す。

        Returns:
            list(ImageItems):
        """
        return [i for i in self.scene.items() if isinstance(i, ImageItem)]

    def keyPressEvent(self, event):
        key = event.key()
        mod = event.modifiers()
        apply_to_all = (
            mod == QtCore.Qt.ShiftModifier or
            mod == QtCore.Qt.ControlModifier | QtCore.Qt.ShiftModifier
        )

        # カーソル下の画像を優先、なければ最前面画像を対象
        mouse_event = QtGui.QMouseEvent(
            QtCore.QEvent.MouseMove,
            self.mapFromGlobal(QtGui.QCursor.pos()),
            QtCore.Qt.NoButton, QtCore.Qt.NoButton, QtCore.Qt.NoModifier
        )
        targets = self._item_from_event(mouse_event, apply_to_all)

        if targets:
            if key == QtCore.Qt.Key_R:
                for target in targets:
                    target.rotation_deg = 0.0
                    target.rebuildTransform()
                return

            if key == QtCore.Qt.Key_F:
                if apply_to_all:
                    self.layoutImagesToCursorDesktop(targets)
                else:
                    self.fitItemToScene(targets[0])
                return

            if key in (
                QtCore.Qt.Key_Backspace, QtCore.Qt.Key_Delete, QtCore.Qt.Key_W
            ):
                for target in targets:
                    self.deleteItem(target)
                return

        if (
            self.__allow_image_addition and key == QtCore.Qt.Key_A
            and mod == QtCore.Qt.ControlModifier
        ):
            self.addImageFromDialog()
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