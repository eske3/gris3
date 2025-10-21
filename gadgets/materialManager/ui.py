#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2020/07/03 01:40 eske yoshinob[eske3g@gmail.com]
        update:2020/07/03 01:40 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2020 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import re
from . import core
from ... import uilib, node
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

Style = '''
QAbstractItemView::item{
    padding-top : 4px;
    padding-bottom : 4px;
}
'''

NAME_RULE_PATTERN = re.compile('^([a-z][a-zA-Z]+)_([a-zA-Z\d]+)(_[LR]$|$)')
class Name(object):
    def __init__(self, name):
        r"""
            Args:
                name (any):
        """
        self.__isvalid = False
        ns, basename = self.splitNamespace(name)
        self.__namespace = ns + ':' if ns else ''
        result = NAME_RULE_PATTERN.search(basename)
        if not result:
            self.__nameinfo = [basename]
            return

        self.__isvalid = True
        self.__nameinfo = []
        self.__nameinfo.append(result.group(1))
        self.__nameinfo.append(result.group(2))

        if result.group(3):
            self.__nameinfo.append(result.group(3)[-1])

    def getName(self, withNamespace=True):
        name = '_'.join(self.__nameinfo)
        if withNamespace:
            name = self.namespace() + name
        return name

    def __repr__(self):
        return self.getName(True)

    def __call__(self):
        return self.__repr__()

    @staticmethod
    def splitNamespace(name):
        if not ':' in name:
            return '', name
        return name.rsplit(':', 1)

    @staticmethod
    def getNoNamespace(name):
        if not name:
            return name
        return name.rsplit(':', 1)[-1]

    def noNamespace(self):
        return self.getName(False)

    def namespace(self):
        return self.__namespace

    def baseName(self):
        return self.__nameinfo[0]

    def nodeType(self):
        return self.__nameinfo[1]

    def position(self):
        return self.__nameinfo[2] if len(self.__nameinfo) == 3 else ''

    def isValid(self):
        return self.__isvalid


class ContextMenu(QtWidgets.QWidget):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ContextMenu, self).__init__(parent)
        self.resize(300, 80)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)

        # マテリアル入れ替えボタン。-------------------------------------------
        swap_btn = QtWidgets.QPushButton('Swap Material')
        swap_btn.setIcon(QtGui.QIcon(':swapBG.png'))
        swap_btn.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding
        )
        self.swapButtonClicked = swap_btn.clicked
        # ---------------------------------------------------------------------
        
        # PxrSurfをRmanPlugに指し直すボタン。----------------------------------
        rman_btn = QtWidgets.QPushButton('Assign shader to Rman Plug')
        rman_btn.setIcon(QtGui.QIcon(':swapBG.png'))
        rman_btn.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding
        )
        self.assignRmanPlugButtonClicked = rman_btn.clicked
        # ---------------------------------------------------------------------

        # マテリアルのアサインボタン。-----------------------------------------
        assign_btn = QtWidgets.QPushButton('Assign Material')
        assign_btn.setIcon(QtGui.QIcon(':/materialEditor.png'))
        self.assignButtonClicked = assign_btn.clicked
        # ---------------------------------------------------------------------

        # マテリアル名適用ボタン。---------------------------------------------
        applyname_btn = QtWidgets.QPushButton('Apply Name')
        applyname_btn.setIcon(QtGui.QIcon(':/rename.png'))
        self.applyNameButtonClicked = applyname_btn.clicked
        # ---------------------------------------------------------------------

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(assign_btn, 0, 0, 1, 1)
        layout.addWidget(applyname_btn, 1, 0, 1, 1)
        layout.addWidget(swap_btn, 0, 1, 1, 1)
        layout.addWidget(rman_btn, 1, 1, 1, 1)

    def leaveEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        self.hide()

    def paintEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        super(ContextMenu, self).paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setPen(QtGui.QPen(QtGui.QColor(2, 2, 2), 2))
        painter.drawRect(self.rect())


class MaterialManagerItemModel(QtGui.QStandardItemModel):
    Flag = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
    def __init__(self):
        super(MaterialManagerItemModel, self).__init__(0, 5)
        self.setHeaderData(0, QtCore.Qt.Horizontal, 'Base Name')
        self.setHeaderData(1, QtCore.Qt.Horizontal, 'Position')
        self.setHeaderData(2, QtCore.Qt.Horizontal, 'Shading Engine')
        self.setHeaderData(3, QtCore.Qt.Horizontal, 'Current Material')
        self.setHeaderData(4, QtCore.Qt.Horizontal, 'Proxy Material')

    def flags(self, index):
        r"""
            Args:
                index (QtCore.QModelIndex):
        """
        if index.parent().row() == -1:
            return QtCore.Qt.ItemIsEnabled
            return

        if index.column() > 1:
            return self.Flag
        return self.Flag | QtCore.Qt.ItemIsEditable


class MaterialManager(QtWidgets.QTreeView):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        rman_color = QtGui.QLinearGradient(0, 0, 0, 0)
        rman_color.setColorAt(0, QtGui.QColor(64, 110, 170))
        rman_color.setColorAt(1, QtGui.QColor(52, 90, 150))
        self.BgColorTable = {'rman':rman_color}
        
        super(MaterialManager, self).__init__(parent)
        self.setAlternatingRowColors(True)
        self.setIconSize(QtCore.QSize(32, 32))
        # self.setRootIsDecorated(False)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.setVerticalScrollMode(QtWidgets.QTreeView.ScrollPerPixel)
        self.setHorizontalScrollMode(QtWidgets.QTreeView.ScrollPerPixel)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.doubleClicked.connect(self.selectItem)
        
        model = MaterialManagerItemModel()
        self.setModel(model)

        sel_model = QtCore.QItemSelectionModel(model)
        self.setSelectionModel(sel_model)

        for i, width in enumerate((80, 40, 120, 120, 120)):
            self.setColumnWidth(i, width)

        # コンテキストメニューの作成。=========================================
        self.__context = ContextMenu(self)
        self.__context.swapButtonClicked.connect(self.swapMaterial)
        self.__context.assignRmanPlugButtonClicked.connect(
            self.assignShaderToRmanPlug
        )
        self.__context.assignButtonClicked.connect(self.assignMaterial)
        self.__context.applyNameButtonClicked.connect(self.applyName)
        # =====================================================================

        self.__job_id = core.createScriptJob(self.hilightSelectedShader)

    def drawBranches(self, painter, option, index):
        if index.parent().row() == -1:
            super(MaterialManager, self).drawBranches(painter, option, index)
            return

    def selectItem(self, index):
        r"""
            任意のインデックスのアイテムをMaya上で選択する。
            Args:
                index (QtCore.QModelIndex):
        """
        column = index.column()
        if column < 2 or index.parent().row() == -1:
            return
        nodes = []
        core.select(
            *[
                x.data(QtCore.Qt.UserRole + 1)
                for x in self.selectionModel().selectedIndexes()
                if x.column() == column
            ]
        )

    def selectedShaderInfo(self):
        r"""
            選択されたリストからシェーダー情報を作成し、コンテキストに渡す。
        """
        from collections import OrderedDict
        sel_model = self.selectionModel()
        model = self.model()
        rows = OrderedDict()
        for index in sel_model.selectedIndexes():
            parent = index.parent()
            if parent.row() == -1:
                # ネームスペースが選択されている場合スキップ。
                continue
            rowlist = rows.setdefault(parent, [])
            row = index.row()
            if row in rowlist:
                continue
            rowlist.append(row)

        shaderinfo = OrderedDict()
        for parent, rowlist in rows.items():
            ns = model.item(parent.row(), 0).data(QtCore.Qt.UserRole + 1)            
            info = []
            parent_item = model.item(parent.row(), 0)
            for row in rowlist:
                data = {
                    y : parent_item.child(row, x).data()
                    for x, y in enumerate(
                        ('sg', 'currentMat', 'proxyMat'), 2
                    )
                }
                data['baseName'] = parent_item.child(row, 0).text()
                data['position'] = parent_item.child(row, 1).text()
                info.append(data)
            shaderinfo[ns] = info
        return shaderinfo

    def swapMaterial(self):
        r"""
            マテリアルの置き換えを実行する。
        """
        shaderinfo = self.selectedShaderInfo()
        if not shaderinfo:
            return
        with node.DoCommand():
            for ns, info in shaderinfo.items():
                core.swapMaterialFromData(info)
        self.refresh(False)
        self.__context.hide()

    def assignShaderToRmanPlug(self):
        shaderinfo = self.selectedShaderInfo()
        with node.DoCommand():
            for ns, info in shaderinfo.items():
                core.assignShaderToRmanPlug(info)
        self.refresh(False)
        self.__context.hide()

    def assignMaterial(self):
        r"""
            マテリアルをアサインする。
        """
        shaderinfo = self.selectedShaderInfo()
        if not shaderinfo:
            return
        with node.DoCommand():
            for ns, info in shaderinfo.items():
                core.applyMaterialToSG([x['sg'] for x in info])
        self.refresh(False)
        self.__context.hide()

    def applyName(self):
        r"""
            名前をマテリアル関連ノード一式に適用する。
        """
        shaderinfo = self.selectedShaderInfo()
        if not shaderinfo:
            return
        with node.DoCommand():
            for ns, info in shaderinfo.items():
                core.applyNameFromData(info)
        self.refresh(False)
        self.__context.hide()

    def showContextMenu(self, pos):
        r"""
            Args:
                pos (QtCore.QPoint):カーソルの座標
        """
        index = self.indexAt(pos)

        rect = self.__context.rect()
        # コンテキストメニューをマウスカーソルの上へ移動する。
        rect.moveCenter(self.mapToGlobal(pos))
        self.__context.setGeometry(rect)

        self.__context.show()

    def hilightSelectedShader(self):
        shading_engines = core.selectedSGList()
        model = self.model()
        gradient = QtGui.QLinearGradient(0, 0, 0, 0)
        gradient.setColorAt(0, QtGui.QColor(120, 100, 65))
        gradient.setColorAt(1, QtGui.QColor(95, 75, 48))
        nocolor = QtGui.QBrush(QtCore.Qt.NoBrush)

        for p_row in range(model.rowCount()):
            p_item = model.item(p_row, 0)
            p_index = model.indexFromItem(p_item)
            hit = False
            for row in range(p_item.rowCount()):
                sg_name = model.index(row, 2, p_index).data(
                    QtCore.Qt.UserRole+1
                )
                proxy_type = model.index(row, 4, p_index).data(
                    QtCore.Qt.UserRole+2
                )
                row_hight = self.sizeHintForRow(row)
                if not sg_name in shading_engines:
                    bg_color = nocolor
                    proxy_color = nocolor
                else:
                    gradient.setFinalStop(0, row_hight)
                    bg_color = gradient
                    hit = True
                colorlist = [bg_color for x in range(4)]

                proxy_color = self.BgColorTable.get(proxy_type, bg_color)
                if hasattr(proxy_color, 'setFinalStop'):
                    proxy_color.setFinalStop(0, row_hight)
                colorlist.append(proxy_color)

                for column, color in enumerate(colorlist):
                    item = p_item.child(row, column)
                    item.setBackground(color)
            
            # 子アイテムに該当するものがあった場合、親もハイライトする。
            bg_color = nocolor
            if hit:
                gradient.setFinalStop(0, self.sizeHintForRow(p_row))
                bg_color = gradient
            for column in range(5):
                item = model.item(p_row, column)
                item.setBackground(bg_color)

    def resizeColumn(self):
        for index in (0, 2, 3):
            self.resizeColumnToContents(index)

    def refresh(self, resizeColumn=True):
        model = self.model()
        expanded = []
        for row in range(model.rowCount()):
            index = model.index(row, 0)
            if not self.isExpanded(index):
                continue
            expanded.append(index.data(QtCore.Qt.UserRole + 1))
        model.removeRows(0, model.rowCount())

        sg_icon = QtGui.QIcon(':/shadingEngine.svg')
        mat_icon = QtGui.QIcon(':/lambert.svg')
        prox_icon = QtGui.QIcon(':/shaderGlow.svg')
        ref_icon = QtGui.QIcon(':/reference.svg')

        expanding = []
        for ns, sglist in core.listShadingEngines().items():
            ns_item = QtGui.QStandardItem(ns if ns else 'Current Scene')
            ns_item.setData(ns)
            if ns:
                ns_item.setIcon(ref_icon)
            row = model.rowCount()
            model.setItem(row, 0, ns_item)
            if ns in expanded:
                expanding.append(model.indexFromItem(ns_item))

            for i in range(4):
                item = QtGui.QStandardItem()
                item.setFlags(QtCore.Qt.ItemIsSelectable)
                model.setItem(row, i+1, item)

            for row, sg in enumerate(sglist):
                name = Name(sg())
                if name.isValid():
                    # 名前とポジションの追加。
                    n_item = QtGui.QStandardItem(name.baseName())
                    n_item.setData(name.baseName())
                    ns_item.setChild(row, 0, n_item)

                    pos_item = QtGui.QStandardItem(name.position())
                    pos_item.setData(name.position())
                    ns_item.setChild(row, 1, pos_item)
                else:
                    # 名前がパターン適合しない場合は空文字を入れる。
                    for i in range(2):
                        ns_item.setChild(row, i, QtGui.QStandardItem())

                # Shading Engine項目の追加。
                item = QtGui.QStandardItem(name.noNamespace())
                item.setData(name())
                item.setIcon(sg_icon)
                ns_item.setChild(row, 2, item)

                # シェーダーの追加。
                current_shader = sg.currentShader()
                c_name = current_shader if current_shader else ''
                c_item = QtGui.QStandardItem(Name.getNoNamespace(c_name))
                c_item.setData(c_name)
                c_item.setIcon(mat_icon)
                ns_item.setChild(row, 3, c_item)

                # プロキシシェーダーの追加。
                shader = sg.proxyShader()
                flag = 'proxy'
                if not shader:
                    shader = sg.rmanShader()
                    if shader:
                        flag = 'rman'
                    else:
                        'no_shader'
                s_name = shader if shader else ''
                p_item = QtGui.QStandardItem(Name.getNoNamespace(s_name))
                p_item.setData(s_name)
                p_item.setData(flag, QtCore.Qt.UserRole + 2)
                if s_name:
                    p_item.setIcon(prox_icon)
                ns_item.setChild(row, 4, p_item)
        
        if model.rowCount() == 1:
            self.setExpanded(model.index(0, 0), True)
        else:
            for index in expanding:
                self.setExpanded(index, True)

        self.hilightSelectedShader()
        if resizeColumn:
            self.resizeColumn()

    def killUpdateJob(self):
        core.killJob(self.__job_id)

    def copySelectedName(self):
        sel_model = self.selectionModel()
        indexes = sel_model.selectedIndexes()
        cur = sel_model.currentIndex()
        column = cur.column()
        datalist = []
        for index in indexes:
            if index.column() != column:
                continue
            datalist.append('%s:%s'%(index.row(), index.data()))
        if not datalist:
            return
        data = '\n'.join(datalist)
        QtWidgets.QApplication.clipboard().setText(data)

    def pasteNameToSelected(self):
        data = QtWidgets.QApplication.clipboard().text()
        datalist = data.split()
        namelist = []
        ptn = re.compile('[a-zA-Z\d_]*?\:([a-zA-Z\d_]*$)')
        for d in datalist:
            r = ptn.match(d)
            if not r:
                return
            namelist.append(r.group(1))
        indexes = [
            x for x in self.selectionModel().selectedIndexes()
            if x.column() == 0
        ]
        model = self.model()
        for index, name in zip(indexes, namelist):
            item = model.itemFromIndex(index)
            item.setText(name)

    def editCurrentName(self):
        sel_model = self.selectionModel()
        cur = sel_model.currentIndex()
        row = cur.row()
        selected = [
            x for x in sel_model.selectedIndexes()
            if x.row()==row and x.column()==0
        ]
        if not selected:
            return
        self.edit(selected[0])

    def keyPressEvent(self, event):
        key = event.key()
        mod = event.modifiers()
        if mod == QtCore.Qt.ControlModifier:
            if key == QtCore.Qt.Key_C:
                self.copySelectedName()
                return
            if key == QtCore.Qt.Key_V:
                self.pasteNameToSelected()
                return
            
            if key == QtCore.Qt.Key_Q:
                self.assignMaterial()
                return
            if key == QtCore.Qt.Key_W:
                self.applyName()
                return
            if key == QtCore.Qt.Key_E:
                self.swapMaterial()
                return
            if key == QtCore.Qt.Key_R:
                self.assignShaderToRmanPlug()
                return
        else:
            if key in (QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return):
                self.editCurrentName()
                return
        super(MaterialManager, self).keyPressEvent(event)

class MultOperator(QtWidgets.QGroupBox):
    def __init__(self, manager, parent=None):
        super(MultOperator, self).__init__('Select selections of view')
        self.__manager = manager
        layout = QtWidgets.QHBoxLayout(self)
        
        for iconpath, method in (
            (':/shadingEngine.svg', self.selectShadingEngines),
            (':/blinn', self.selectMaterials),
        ):
            button = uilib.OButton()
            button.setIcon(iconpath)
            button.setSize(32)
            button.clicked.connect(method)
            layout.addWidget(button)
        
        layout.addStretch()
    
    def manager(self):
        return self.__manager

    def listDataFromSelected(self, key):
        shader_info = self.manager().selectedShaderInfo()
        if not shader_info:
            return
        results = []
        for datalist in shader_info.values():
            for data in datalist:
                results.append(data[key])
        return results
   
    def selectShadingEngines(self):
        sgs = self.listDataFromSelected('sg')
        if not sgs:
            return
        core.select(*sgs)
    
    def selectMaterials(self):
        materials = self.listDataFromSelected('currentMat')
        if not materials:
            return
        core.select(*materials)


class MainGUI(QtWidgets.QWidget):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(MainGUI, self).__init__(parent)
        self.setWindowTitle('Material Manager')
        self.setStyleSheet(Style)

        manager = MaterialManager()
        self.__kill_job = manager.killUpdateJob
        self.refresh = manager.refresh
        
        mult_op = MultOperator(manager)

        ref_btn = uilib.OButton(uilib.IconPath('uiBtn_reload'))
        ref_btn.setSize(32)
        ref_btn.clicked.connect(manager.refresh)
        ref_btn.setFlat(True)

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(mult_op, 0, 0, 1, 1)
        layout.addWidget(ref_btn, 0, 1, 1, 1, QtCore.Qt.AlignRight)
        layout.addWidget(manager, 1, 0, 1, 2)

    def closeEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        self.__kill_job()

