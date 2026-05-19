#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    gadgetsモジュール内の各ガジェットを開くランチャー機能を提供するモジュール。
    
    Dates:
        date:2025/08/02 06:46 Eske Yoshinob[eske3g@gmail.com]
        update:2025/08/02 06:53 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2025 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import lib, uilib, documentUtil
from ..uilib import extendedUI

QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


def listFunctions(disabled=None):
    r"""
        gadgetsモジュール内にあるガジェット呼び出し関数をリストする。
        リストアップされるのは基本的にgagdgetsモジュール内の関数全て。
        また引数disabledで指定した関数は無視される。
        戻り値は関数名をキー、関数オブジェクトを値とする辞書。

        Args:
            disabled (list):
        
        Returns:
            dict:
    """
    disabled = [] if disabled is None else disabled
    from .. import gadgets
    f_type = type(lambda x : x)
    results = {}
    for member in dir(gadgets):
        if member in disabled:
            continue
        f = getattr(gadgets, member)
        if type(f) != f_type:
            continue
        results[member] = f
    return results


class FunctionListStyle(QtWidgets.QStyledItemDelegate):
    BgColor = QtGui.QColor(32, 32, 32)
    HoveredBgColor = QtGui.QColor(32, 42, 64)
    SelectedBgColor = QtGui.QColor(48, 62, 98)
    TitleColor = QtGui.QColor(28, 128, 255)
    TextColor = QtGui.QColor(200, 200, 200)

    def __init__(self, parent=None):
        super(FunctionListStyle, self).__init__(parent)

    def sizeHint(self, option, index):
        r"""
            Args:
                option (QtWidgets.QStyleOptionViewItem):
                index (QtCore.QModelIndex):
        """
        opt = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        height = int(opt.fontMetrics.height() * 5)
        return QtCore.QSize(option.rect.width(), height)

    def paint(self, painter, option, index):
        r"""
            Args:
                painter (QtGui.QPainter):
                option (QtWidgets.QStyleOptionViewItem):
                index (QtCore.QModelIndex):
        """
        text = index.data()
        painter.setRenderHints(QtGui.QPainter.RenderHint.Antialiasing)

        font = painter.font()
        font_m = QtGui.QFontMetrics(font)
        text_rect = font_m.boundingRect('K')
        rect = QtCore.QRect(option.rect)

        t_font = QtGui.QFont(font)
        t_font.setPixelSize(int(font.pixelSize() * 1.25))

        t_rect = QtCore.QRect(rect)
        t_rect.setHeight(int(font.pixelSize() * 2))
        painter.setPen(QtCore.Qt.NoPen)
        bg_color = self.BgColor
        if option.state & QtWidgets.QStyle.State_Selected:
            bg_color = self.SelectedBgColor
        elif option.state & QtWidgets.QStyle.State_MouseOver:
            bg_color = self.HoveredBgColor
        painter.setBrush(bg_color)
        painter.drawRect(rect)
        offset = text_rect.width()

        # タイトルの表示。
        t_rect.setLeft(offset)
        painter.setPen(QtGui.QPen(self.TitleColor))
        t_font.setBold(True)
        painter.setFont(t_font)
        painter.drawText(
            t_rect, text, QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
        )

        rect.setTopLeft(
            QtCore.QPoint(offset * 2, rect.top() + t_rect.height())
        )
        painter.setFont(font)
        painter.setPen(QtGui.QPen(self.TextColor))
        painter.drawText(
            rect, index.data(QtCore.Qt.UserRole + 1),
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop
        )
        
        rect.setLeft(offset)
        rect.setRight(rect.right() - offset)
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())


class AppViewer(extendedUI.FilteredView):
    enterPressed = QtCore.Signal(QtCore.QModelIndex)

    def createView(self):
        view = QtWidgets.QListView()
        view.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
        view.setVerticalScrollMode(QtWidgets.QTreeView.ScrollPerPixel)
        view.setHorizontalScrollMode(QtWidgets.QTreeView.ScrollPerPixel)
        view.setItemDelegate(FunctionListStyle())
        return view

    def createModel(self):
        model = QtGui.QStandardItemModel(0, 1)
        return model

    def __emit_enter_pressed(self):
        model: QtCore.QSortFilterProxyModel = self.view().model()
        start_index = model.index(0, 0)
        self.enterPressed.emit(start_index)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
                self.__emit_enter_pressed()
                return True
        return super(AppViewer, self).eventFilter(obj, event)


class Launcher(QtWidgets.QWidget):
    DisabledFunctions = [
        'openGagetsLauncher', 'openToolbar', 'openPolyHalfRemover',
        'openPolyMirror', 'openPolyCutter', 'openCheckTools'
    ]
    applicationLaunched = QtCore.Signal()

    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(Launcher, self).__init__(parent)
        self.setWindowTitle('Gris Launcher')
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.__functions = {}

        self.__view = AppViewer()
        self.__view.view().clicked.connect(self.execCommand)
        self.__view.installEventFilter(self)
        self.__view.enterPressed.connect(self.execCommand)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.__view)

        self.reload()

    def view(self):
        return self.__view

    def leaveEvent(self, event):
        self.view().view().clearSelection()
        super(Launcher, self).leaveEvent(event)

    def reload(self):
        model = self.view().view().model().sourceModel()
        model.removeRows(0, model.rowCount())
        self.__functions = listFunctions(self.DisabledFunctions)
        for row, f_name in enumerate(sorted(list(self.__functions.keys()))):
            item = QtGui.QStandardItem(lib.title(f_name))
            model.setItem(row, 0, item)
            f = self.__functions[f_name]
            doc_data = documentUtil.parsePydoc(f.__doc__)
            brief = doc_data.get('brief', [])
            item.setData(''.join(brief), QtCore.Qt.UserRole + 1)
            item.setData(f_name, QtCore.Qt.UserRole + 2)

    def execCommand(self, index):
        self.view().view().clearSelection()
        f_name = index.data(QtCore.Qt.UserRole + 2)
        f = self.__functions.get(f_name)
        if f:
            f()
            self.applicationLaunched.emit()


class MainGUI(uilib.AbstractSeparatedWindow):
    r"""
        メインとなるGUIを提供するクラス
    """
    def centralWidget(self):
        r"""
            Returns:
                Launcher:
        """
        l = Launcher()
        return l

    def reload(self):
        self.main().reload()


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。
        
        Returns:
            MainGUI:
    """
    from gris3.uilib import mayaUIlib
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.show()
    return widget

