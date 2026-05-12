#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ディスプレイレイヤーの表示・非表示などの操作利便性向上のためのビューワを
    提供するモジュール。
    
    Dates:
        date:2025/07/16 14:30 Eske Yoshinob[eske3g@gmail.com]
        update:2025/07/16 15:27 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2025 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from collections import OrderedDict
from maya import cmds, mel

from .. import uilib, lib, node, colorUtil
from ..uilib import mayaUIlib, extendedUI
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


ATTR_TABLE = OrderedDict()
ATTR_TABLE['visibility'] = (('uiBtn_visible', 1), ('uiBtn_unvisible', 0))
ATTR_TABLE['shading'] = (('uiBtn_shading', 1), ('uiBtn_wireframe', 0))
ATTR_TABLE['displayType'] = (
    ('uiBtn_displayNormal', 0), ('uiBtn_displayTemplate', 1),
    ('uiBtn_displayReference', 2)
)

        
class LayerStatusStyle(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(LayerStatusStyle, self).__init__(parent)
        self.__status_icons = [
            {y[1] : QtGui.QPixmap(uilib.IconPath(y[0])) for y in x}
            for x in ATTR_TABLE.values()
        ]

    def sizeHint(self, option, index):
        r"""
            Args:
                option (QtWidgets.QStyleOptionViewItem):
                index (QtCore.QModelIndex):
        """
        if index.parent().model():
            height = int(option.fontMetrics.boundingRect('f').height() * 1.5)
            return QtCore.QSize(option.rect.width(), height)
        return super(LayerStatusStyle, self).sizeHint(option, index)

    def paint(self, painter, option, index):
        r"""
            Args:
                painter (QtGui.QPainter):
                option (QtWidgets.QStyleOptionViewItem):
                index (QtCore.QModelIndex):
        """
        if index.parent().model() is None:
            super(LayerStatusStyle, self).paint(painter, option, index)
            return
        data = index.data()
        painter.setRenderHints(QtGui.QPainter.RenderHint.Antialiasing)
        
        d_pen = painter.pen()
        d_brush = painter.brush()

        rect = QtCore.QRect(option.rect)
        font = painter.font()
        font_m = QtGui.QFontMetrics(font)
        text_rect = font_m.boundingRect('K')

        icon_size = int(rect.height() * 0.6)
        width = int(icon_size * 1.1)
        top = rect.top() + int((rect.height() - icon_size) * 0.5)
        left = rect.left()

        # 各種ステータスアイコンの描画。
        status_list = []
        for i, icons in enumerate(self.__status_icons, 1):
            stats = index.data(QtCore.Qt.UserRole + i + 1)
            s_rect = QtCore.QRect(
                left + width * i, top, icon_size, icon_size
            )
            status_list.append(stats)
            painter.drawPixmap(s_rect, icons[stats])
        
        # レイヤ名の描画。
        color = d_pen.color()
        c_pen = QtGui.QPen(d_pen)
        if status_list[0] == 0:
            color.setRed(int(color.red() * 0.5))
            color.setGreen(int(color.green() * 0.5))
            color.setBlue(int(color.blue() * 0.5))
        if status_list[2] == 1:
            color.setRed(int(color.red() * 1.5))
        c_pen.setColor(color)
        painter.setPen(c_pen)
        rect.setX(left + width * (i + 1))
        painter.drawText(
            rect, data, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
        )
        painter.setPen(d_pen)

        # レイヤカラーの描画。
        color_data = index.data(QtCore.Qt.UserRole + i + 2)
        if color_data is None:
            color = QtCore.Qt.NoBrush
        else:
            color = QtGui.QColor(
                *[int(x * 255) for x in color_data]
            )
        rect = QtCore.QRect(left, top, icon_size, icon_size)
        painter.setBrush(color)
        painter.drawEllipse(rect)


class StatusEditor(QtWidgets.QWidget):
    buttonClicked = QtCore.Signal(str, int)

    def __init__(self, parent=None):
        super(StatusEditor, self).__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        
        for attr, values in ATTR_TABLE.items():
            grp = QtWidgets.QGroupBox(lib.title(attr))
            grp_layout = QtWidgets.QHBoxLayout(grp)
            grp_layout.setSpacing(1)
            for st, value in values:
                btn = uilib.OButton(uilib.IconPath(st))
                btn.setToolTip(
                    'Set {}'.format(lib.title(st.split('uiBtn_')[-1]))
                )
                btn.state = (attr, value)
                btn.setSize(32)
                btn.clicked.connect(self.emitButtonSignal)
                grp_layout.addWidget(btn)
            grp_layout.addStretch()
            layout.addWidget(grp)
    
    def emitButtonSignal(self):
        button = self.sender()
        self.buttonClicked.emit(*button.state)


class DisplayerLayerView(QtWidgets.QTreeView):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(DisplayerLayerView, self).__init__(parent)
        self.setRootIsDecorated(False)
        self.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
        self.setSelectionMode(QtWidgets.QTreeView.ExtendedSelection)
        self.setVerticalScrollMode(QtWidgets.QTreeView.ScrollPerPixel)
        self.clicked.connect(self.updateSelectedStatus)
        self.setItemDelegate(LayerStatusStyle())

    def listDisplayLayers(self):
        r"""
            シーン中のディスプレイレイヤーをリストする。
            戻り値はネームスペースごとに区分けされた辞書オブジェクトとなる。
            またdefaultのレイヤーは含まれない。

            Returns:
                dict:
        """
        categolized_layers = {}
        default_layers = node.ls(type='displayLayer', ud=True)
        for n in node.ls(type='displayLayer'):
            if n in default_layers:
                continue
            categolized_layers.setdefault(n.namespace(), []).append(n)
        return categolized_layers

    def updateLayerStatus(self):
        model = self.model()
        for row in range(model.rowCount()):
            namespace_item = model.item(row, 0)
            for c_row in range(namespace_item.rowCount()):
                item = namespace_item.child(c_row, 0)
                l = node.asObject(item.data(QtCore.Qt.UserRole+1))
                if not l:
                    continue
                for x, attr in enumerate(
                    ATTR_TABLE.keys(), 2
                ):
                    item.setData(int(l(attr)), QtCore.Qt.UserRole + x)
                
                if l('overrideRGBColors'):
                    color = l('overrideColorRGB')[0]
                else:
                    color_index = l('color')
                    if color_index == 0:
                        color = None
                    else:
                        color = colorUtil.NewColorIndex[color_index]
                item.setData(color, QtCore.Qt.UserRole + x + 1)        

    def reload(self):
        model = self.model()
        model.removeRows(0, model.rowCount())
        
        layers = self.listDisplayLayers()
        referencelist = list(layers.keys())
        referencelist.sort()
        for row, ref in enumerate(referencelist):
            # 各リファレンスのネームスペースごとのラベルアイテムを作成
            label = 'Current Scene' if ref == '' else '+ ' + ref
            ref_item = QtGui.QStandardItem(label)
            ref_item.setData(ref)
            model.setItem(row, 0, ref_item)

            # レイヤーを追加する。
            for r, l in enumerate(layers[ref]):
                item = QtGui.QStandardItem(l.rsplit(':', 1)[-1])
                item.setData(l())
                ref_item.setChild(r, 0, item)
        self.updateLayerStatus()

    def updateSelectedStatus(self, index):
        r"""
            Args:
                index (QtCore.QModelIndex):
        """
        if not index:
            return
        if not index.parent().model():
            # ネームスペース階層の場合、展開・非展開の状態を更新。
            self.setExpanded(index, self.isExpanded(index) == False)
            return
        
    def listSelectedLayers(self):
        r"""
            現在選択されているアイテムのうち、ディスプレイレイヤの名前だけ
            返す。

            Returns:
                list:
        """
        layers = []
        for index in self.selectionModel().selectedIndexes():
            if not index.parent().model():
                continue
            layers.append(index.data(QtCore.Qt.UserRole + 1))
        return layers

    def drawBranches(self, painter, option, index):
        return


class DisplayLayerFilteredView(extendedUI.FilteredView):
    def createView(self):
        r"""
            再実装用メソッド。任意のViewを作成し返す。
            
            Returns:
                QTreeView/QListView/QTableView:
        """
        return DisplayerLayerView()

    def createModel(self):
        r"""
            再実装用メソッド。任意のItemModelを作成し返す。
            
            Returns:
                QStandardItemModel:
        """
        model = QtGui.QStandardItemModel(0, 1)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'displayLayer')
        return model

    def listDisplayLayers(self):
        r"""
            シーン中のディスプレイレイヤーをリストする。
            戻り値はネームスペースごとに区分けされた辞書オブジェクトとなる。
            またdefaultのレイヤーは含まれない。

            Returns:
                dict:
        """
        categolized_layers = {}
        default_layers = node.ls(type='displayLayer', ud=True)
        for n in node.ls(type='displayLayer'):
            if n in default_layers:
                continue
            categolized_layers.setdefault(n.namespace(), []).append(n)
        return categolized_layers

    def updateLayerStatus(self):
        model = self.view().model().sourceModel()
        for row in range(model.rowCount()):
            namespace_item = model.item(row, 0)
            for c_row in range(namespace_item.rowCount()):
                item = namespace_item.child(c_row, 0)
                l = node.asObject(item.data(QtCore.Qt.UserRole+1))
                if not l:
                    continue
                for x, attr in enumerate(
                    ATTR_TABLE.keys(), 2
                ):
                    item.setData(int(l(attr)), QtCore.Qt.UserRole + x)
                
                if l('overrideRGBColors'):
                    color = l('overrideColorRGB')[0]
                else:
                    color_index = l('color')
                    if color_index == 0:
                        color = None
                    else:
                        color = colorUtil.NewColorIndex[color_index]
                item.setData(color, QtCore.Qt.UserRole + x + 1)        

    def reload(self):
        model = self.view().model().sourceModel()
        model.removeRows(0, model.rowCount())
        
        layers = self.listDisplayLayers()
        referencelist = list(layers.keys())
        referencelist.sort()
        for row, ref in enumerate(referencelist):
            # 各リファレンスのネームスペースごとのラベルアイテムを作成
            label = 'Current Scene' if ref == '' else '+ ' + ref
            ref_item = QtGui.QStandardItem(label)
            ref_item.setData(ref)
            model.setItem(row, 0, ref_item)

            # レイヤーを追加する。
            for r, l in enumerate(layers[ref]):
                item = QtGui.QStandardItem(l.rsplit(':', 1)[-1])
                item.setData(l())
                ref_item.setChild(r, 0, item)
        self.updateLayerStatus()

    def updateSelectedStatus(self, index):
        r"""
            Args:
                index (QtCore.QModelIndex):
        """
        if not index:
            return
        if not index.parent().model():
            # ネームスペース階層の場合、展開・非展開の状態を更新。
            self.setExpanded(index, self.isExpanded(index) == False)
            return
        
    def listSelectedLayers(self):
        r"""
            現在選択されているアイテムのうち、ディスプレイレイヤの名前だけ
            返す。

            Returns:
                list:
        """
        layers = []
        for index in self.view().selectionModel().selectedIndexes():
            if not index.parent().model():
                continue
            layers.append(index.data(QtCore.Qt.UserRole + 1))
        return layers


class DisplayLayerViewer(QtWidgets.QWidget):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(DisplayLayerViewer, self).__init__(parent)
        self.setWindowTitle('+Display Layer Viewer')
        
        reload_btn = uilib.OButton(uilib.IconPath('uiBtn_reload'))
        reload_btn.clicked.connect(self.reload)
        
        # self.__view = DisplayerLayerView()
        self.__view = DisplayLayerFilteredView()
        editor = StatusEditor()
        editor.buttonClicked.connect(self.updateSelectedLayer)

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(self.__view, 0, 0, 1, 2)
        layout.addWidget(editor, 1, 0, 1, 1)
        layout.addWidget(reload_btn, 1, 1, 1, 1, QtCore.Qt.AlignTop)
        layout.setRowStretch(0, 1)

    def view(self):
        return self.__view

    def reload(self):
        self.view().reload()

    def updateSelectedLayer(self, attr, value):
        view = self.view()
        layers = view.listSelectedLayers()
        with node.DoCommand():
            for layer in layers:
                l = node.asObject(layer)
                if not l:
                    continue
                l(attr, value)
        view.updateLayerStatus()

    
class MainGUI(uilib.AbstractSeparatedWindow):
    def centralWidget(self):
        r"""
            中心となるメインウィジェットを作成して返す
            
            Returns:
                DisplayLayerViewer:
        """
        return DisplayLayerViewer()


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。
        
        Returns:
            QtWidgets.QWidget:
    """
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(uilib.hires(300), uilib.hires(450))
    widget.show()
    widget.main().reload()
    return widget

