#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ジョイントの編集機能を提供するGUI。
    
    Dates:
        date:2017/06/15 16:35[Eske](eske3g@gmail.com)
        update:2020/07/29 13:04 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3.tools import skinUtility, paintSkinUtility
from gris3 import lib, uilib, node
from gris3.uilib import extendedUI
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore
Exec_Color = (64, 72, 150)


class BindUtility(uilib.ClosableGroup):
    r"""
        バインドに関する機能を提供するGUI。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):
        """
        super(BindUtility, self).__init__('Bind Utility', parent)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(2)
        from gris3.exporter import skinWeightExporter
        from gris3.tools.controllerUtil import restoreToDefault
        self.__temp_wgt = skinWeightExporter.TemporaryWeight()

        for data in (
            (
                skinUtility.showBindSkinOption,
                'Open bind skin option',
                (96, 128, 20), 'uiBtn_bindSkinOption'
            ),
            (
                self.bindFromBinded,
                'Bind skin to selected from last selection that was binded.',
                (38, 128, 148), 'uiBtn_bindSkin'
            ),
            (
                self.bindToTube,
                'Set weight from joint chain to selected faces.',
                (38, 128, 148), 'uiBtn_bindToTube'
            ),
            (
                self.transferObjectsWeights,
                'Transfer selected weights to last selected object.',
                (38, 128, 148), 'uiBtn_extractFace'
            ),
            10,
            (
                self.tempExportWeight,
                'Export weight of selected node temporarily.',
                (11, 68, 128), 'uiBtn_export'
            ),
            (
                self.tempImportWeight,
                'Import weight of selected node temporarily.',
                (11, 68, 128), 'uiBtn_import'
            ),
            10,
            (
                restoreToDefault,
                'Reset selected controllers.',
                (91, 82, 182), 'uiBtn_reset'
            ),
        ):
            if isinstance(data, int):
                layout.addSpacing(data)
                continue
            cmd, tooltip, color, icon = data
            btn = uilib.OButton()
            btn.setToolTip(tooltip)
            btn.setBgColor(*color)
            btn.setIcon(uilib.IconPath(icon))
            btn.setSize(38)
            btn.clicked.connect(cmd)
            layout.addWidget(btn)
        layout.addStretch()

    def bindFromBinded(self):
        r"""
            バインド済みオブジェクトのバインド情報を他のオブジェクトに移す。
        """
        with node.DoCommand():
            selected = node.selected()
            skinUtility.bindFromBinded(selected[:-1], selected[-1])

    def bindToTube(self):
        r"""
            ジョイントチェーン用いてをチューブ上の形状に柔らかくウェイトを
            セットする。
        """
        with node.DoCommand():
            selected = node.selected()
            skinUtility.bindToFace()

    def transferObjectsWeights(self):
        r"""
            任意の複数オブジェクトのウェイトをターゲットに写す
        """
        with node.DoCommand():
            skinUtility.transferObjectsWeights()

    def tempExportWeight(self):
        r"""
            テンポラリに現在選択しているオブジェクトのウェイトを書き出す
        """
        self.__temp_wgt.save()

    def tempImportWeight(self):
        r"""
            テンポラリのウェイトを読み込む
        """
        self.__temp_wgt.restore()


class ValueEditor(uilib.ConstantWidget):
    r"""
        ペイントのOpacityを編集するウィジェット
    """
    def buildUI(self):
        r"""
            GUIの構築を行う。
        """
        margin = 40
        self.setHiddenTrigger(self.HideByCursorOut)
        self.setScalable(False)
        self.resize(300, 150)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.__skincluster = None
        self.__operation = None

        from .. import style
        title = QtWidgets.QLabel('+ Edit Value')
        title.setStyleSheet(style.TitleLabel)
        self.setTitle = title.setText
        
        label = QtWidgets.QLabel('Opacity')
        editor = QtWidgets.QDoubleSpinBox()
        editor.setRange(0, 1)
        editor.setSingleStep(0.02)
        editor.valueChanged.connect(self.updateOpacity)
        self.setValue = editor.setValue
        self.selectField = editor.selectAll
        
        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(20)
        layout.addWidget(title, 0, 0, 1, 2)
        layout.addWidget(label, 1, 0, 1, 1, QtCore.Qt.AlignRight)
        layout.addWidget(editor, 1, 1, 1, 1)
        layout.setRowStretch(2, 1)

    def setup(self, skinCluster, operation):
        r"""
            編集対象をセットする
            
            Args:
                skinCluster (str):スキンクラスタ名
                operation (str):操作タイプ
        """
        self.__skincluster = skinCluster
        self.__operation = operation
        self.setTitle('+ Edit %s Value' % lib.title(operation))
        self.setValue(
            paintSkinUtility.getOperationOpacity(operation, skinCluster)
        )

    def updateOpacity(self, value):
        r"""
            Args:
                value (float):
        """
        paintSkinUtility.changeOperationOpacity(
            self.__operation, value, self.__skincluster
        )

    def show(self):
        r"""
            スキンクラスタと操作タイプが設定されている時だけ表示する
        """
        if not self.__skincluster or not self.__operation:
            return
        self.selectField()
        super(ValueEditor, self).show()

    def paintEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        painter = QtGui.QPainter(self)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(0, 20, 55, 190))
        painter.drawRoundedRect(self.rect(), 8, 8)


class PaintValueButton(QtWidgets.QPushButton):
    r"""
        右ボタンをクリックされた事を検知する拡張ボタン
    """
    rightButtonPressed = QtCore.Signal()
    def __init__(self, *args, **keywords):
        r"""
            Args:
                *args (tuple):QPushButtonに渡す引数と同じ
                **keywords (dict):QPushButtonに渡す引数と同じ
        """
        super(PaintValueButton, self).__init__(*args, **keywords)
        self.setToolTip(
            'Hit by right button then show an editor to change a value.'
        )
        self.__is_right_clicked = False

    def mousePressEvent(self, event):
        r"""
            Args:
                event (QtCore.QEVent):
        """
        self.__is_right_clicked = event.button() == QtCore.Qt.RightButton
        if self.__is_right_clicked:
            self.rightButtonPressed.emit()
        super(PaintValueButton, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        r"""
            Args:
                event (QtCore.QEVent):
        """
        if not self.__is_right_clicked:
            super(PaintValueButton, self).mouseReleaseEvent(event)


class PaintUtility(QtWidgets.QGroupBox):
    r"""
        ペイントスキンに関する便利機能を提供するクラス
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(PaintUtility, self).__init__('Paint', parent)
        self.__skincluster = None
        self.__editor = ValueEditor(self)
        layout = QtWidgets.QGridLayout(self)
        layout.setVerticalSpacing(1)
        layout.setHorizontalSpacing(20)
        base_style = (
            'QPushButton{'
            'padding : 0; margin : 0;'
        )
        left_style = (
            base_style
            +'border-top-right-radius:0; border-bottom-right-radius:0;}'
        )
        center_style = (
            base_style
            +'border-radius:0;}'
        )
        right_style = (
            base_style
            +'border-top-left-radius:0; border-bottom-left-radius:0;}'
        )
        styles = (left_style, center_style, right_style)

        for row, label in enumerate(
            ('replace', 'add', 'scale', 'smooth')
        ):
            preset = QtWidgets.QWidget()
            p_layout = QtWidgets.QHBoxLayout(preset)
            p_layout.setContentsMargins(0, 0, 0, 0)
            p_layout.setSpacing(1)
            for i, st in zip((0.1, 0.5, 1.0), styles):
                btn = PaintValueButton(str(i))
                btn.setStyleSheet(st)
                btn.setSizePolicy(
                    QtWidgets.QSizePolicy.Expanding,
                    QtWidgets.QSizePolicy.Fixed,
                )
                btn.operation = label
                btn.value = i
                btn.clicked.connect(self.changeOperationOpacity)
                btn.rightButtonPressed.connect(self.showValueEditor)
                p_layout.addWidget(btn)
            layout.addWidget(QtWidgets.QLabel(label), row, 0, 1, 1)
            layout.addWidget(preset, row, 1, 1, 1)

        # セパレータ
        row += 1
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setLineWidth(1)
        separator.setMinimumSize(0, 10)
        layout.addWidget(separator, row, 0, 1, 2)

        preset = QtWidgets.QWidget()
        p_layout = QtWidgets.QHBoxLayout(preset)
        p_layout.setContentsMargins(0, 0, 0, 0)
        p_layout.setSpacing(1)
        for i, st in zip((-1.0, 0.0, 1.0), styles):
            btn = QtWidgets.QPushButton(str(i))
            btn.setStyleSheet(st)
            btn.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Fixed,
            )
            btn.value = i
            btn.clicked.connect(self.changePaintValue)
            p_layout.addWidget(btn)
        row += 1
        layout.addWidget(QtWidgets.QLabel('Value'), row, 0, 1, 1)
        layout.addWidget(preset, row, 1, 1, 1)
        layout.setRowStretch(row+1, 1)

    def setSkinCluster(self, skinClusterName):
        r"""
            操作対象となるskinCluster名をセットする
            
            Args:
                skinClusterName (str):
        """
        self.__skincluster = skinClusterName

    def changeOperationOpacity(self):
        r"""
            各オペレーションのオパシティをセットした状態でツール起動する、
            スロット専用メソッド。
        """
        sender = self.sender()
        paintSkinUtility.changeOperationOpacity(
            sender.operation, sender.value, self.__skincluster
        )

    def changePaintValue(self):
        r"""
            ウェイト値をセットした状態でツール起動する、スロット専用メソッド。
        """
        paintSkinUtility.changeValue(self.sender().value, self.__skincluster)

    def showValueEditor(self):
        r"""
            値調整を行なうためのウィジェットを表示する
        """
        sender = self.sender()
        self.__editor.setup(self.__skincluster, sender.operation)
        self.__editor.show()


class JointEditorStyle(QtWidgets.QStyledItemDelegate):
    Offset = 10
    def __init__(self, parent=None):
        super(JointEditorStyle, self).__init__(parent)
        self.__locked_icon = QtGui.QPixmap(uilib.IconPath('uiBtn_locked'))
        self.__unlocked_icon = QtGui.QPixmap(uilib.IconPath('uiBtn_unlocked'))
        
    def paint(self, painter, option, index):
        if index.column() != 0:
            option.rect.setX(option.rect.x() + self.Offset)
            super(JointEditorStyle, self).paint(painter, option, index)
            return
        state = index.data(QtCore.Qt.UserRole + 1)
        
        rect = QtCore.QRect(option.rect)
        painter.setPen(QtCore.Qt.NoPen)
        if state:
            painter.setBrush(QtGui.QColor(220, 145, 42, 120))
            painter.drawRect(rect)
        width = rect.width()
        rect.setWidth(rect.height())
        rect.moveRight(width - self.Offset)
        painter.drawPixmap(
            rect, self.__locked_icon if state else self.__unlocked_icon
        )

class JointEditorView(QtWidgets.QTreeView):
    lockedButtonClicked = QtCore.Signal(QtCore.QModelIndex)

    def __init__(self, parent=None):
        super(JointEditorView, self).__init__(parent)
        self.__index = None
        self.setEditTriggers(self.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setRootIsDecorated(False)
        self.setSelectionMode(self.ExtendedSelection)
        self.setItemDelegate(JointEditorStyle())

    def mousePressEvent(self, event):
        index = self.indexAt(event.pos())
        if index.column() == 0:
            self.__index = index
            return
        self.__index = None
        super(JointEditorView, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.__index:
            return
        super(JointEditorView, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.__index:
            index = self.__index
            self.__index = None
            self.lockedButtonClicked.emit(index)
            return
        super(JointEditorView, self).mouseReleaseEvent(event)


class JointLister(extendedUI.FilteredView):
    r"""
        インフルエンスの一覧を表示、編集する機能を提供する
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(JointLister, self).__init__(parent)
        self.__skincluster = ''
        self.__tool_was_run = False
        self.__selected = 0
        self.view().setColumnWidth(0, 20)

    def createView(self):
        r"""
            再実装用メソッド。任意のViewを作成し返す。
            
            Returns:
                QTreeView/QListView/QTableView:
        """
        view = JointEditorView()
        view.clicked.connect(self.doClickedAction)
        view.doubleClicked.connect(self.startToPaint)
        view.lockedButtonClicked.connect(self.changeLockState)
        return view

    def createModel(self):
        r"""
            再実装用メソッド。任意のItemModeloを作成し返す。
        """
        model = QtGui.QStandardItemModel(0, 2)
        model.setHeaderData(0, QtCore.Qt.Horizontal, '')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Influence')
        return model

    def filterKeyColumn(self):
        return 1

    def setSkinCluster(self, sc):
        r"""
            操作対象となるskinClusterをセットする
            
            Args:
                sc (str):skinCluster名
        """
        self.__skincluster = sc
        self.refresh()

    def skinCluster(self):
        r"""
            セットされている操作対象となるskinCluster名を返す
            
            Returns:
                any:
        """
        return self.__skincluster

    def refresh(self):
        r"""
            リストを更新する
        """
        proxy = self.view().model()
        model = proxy.sourceModel()
        model.removeRows(0, model.rowCount())
        sc = self.skinCluster()
        if not sc:
            return
        sc = node.SkinCluster(sc)
        if not sc:
            return
        for inf in sc.influences():
            row = model.rowCount()
            stat = inf('lockInfluenceWeights')
            locked_item = QtGui.QStandardItem('L' if stat else 'N')
            locked_item.setData(stat)
            name_item = QtGui.QStandardItem(inf())
            model.setItem(row, 0, locked_item)
            model.setItem(row, 1, name_item)

    def doClickedAction(self, index):
        r"""
            任意のインデックスが指し示すインフルエンスを選択する
            
            Args:
                index (QtCore.QModelIndex):
        """
        column = index.column()
        if column == 1:
            # 1行目(インフルエンスの名前)を選択した場合の選択処理
            if self.__selected == 2:
                self.__selected = 0
                return
            inf = index.data()
            if not inf :
                return
            obj = node.asObject(inf)
            if not obj:
                return
            if self.__tool_was_run:
                self.__tool_was_run = False
                return
            obj.select()
            self.__selected = 1
            return

    def changeLockState(self, index):
        view = self.view()
        proxy = view.model()
        model = proxy.sourceModel()
        # インフルエンスのロックの編集を行う
        sel_model = view.selectionModel()
        new_stat = index.data(QtCore.Qt.UserRole+1) == False
        label = 'L' if new_stat else 'N'
        indexes = sel_model.selectedIndexes()
        if index not in indexes:
            indexes.append(index)
        for index in indexes:
            true_index = proxy.mapToSource(index)
            if true_index.column() == 0:
                # ロックステータスを変更する。
                item = model.itemFromIndex(true_index)
                item.setText(label)
                item.setData(new_stat)
                continue
            inf = node.asObject(index.data())
            if not inf:
                continue
            inf('lockInfluenceWeights', new_stat)
        self.__selected = 1
        
    def selectInfluences(self, selected, deselected):
        r"""
            リストで選択している複数のインフルエンスを選択する
            
            Args:
                selected (list):
                deselected (list):
        """
        for index in selected.indexes():
            if index.column() == 0:
                return
        if self.__selected == 1:
            self.__selected = 0
            return
        sel_model = self.view().selectionModel()
        inflist = [
            x.data() for x in sel_model.selectedIndexes() if x.column()==1
        ]
        if inflist:
            node.cmds.select(node.cmds.ls(inflist), r=True, ne=True)
            self.__selected = 2
        else:
            self.__selected = 0

    def startToPaint(self, index):
        r"""
            ペイントを開始する
            
            Args:
                index (QtCore.QModelIndex):
        """
        sc = self.skinCluster()
        sc_obj = node.asObject(sc)
        if not sc_obj:
            return
        paintSkinUtility.runPaintSkinTool(sc)
        self.__tool_was_run = True



class SkinClusterEditor(uilib.ClosableGroup):
    r"""
        SkinClusterを編集するためのUIを提供するクラス。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        thin_margin = QtCore.QMargins(2, 2, 2, 2)
        super(SkinClusterEditor, self).__init__('Skin Cluster', parent)
        self.setIcon(uilib.IconPath('uiBtn_bindSkin'))
        self.__skin_clusters = []

        # SkinClusterのピッカー================================================
        label = QtWidgets.QLabel('Skin Cluster')
        self.__skin_cluster_names = QtWidgets.QLineEdit()
        self.__skin_cluster_names.setReadOnly(True)
        
        pick_btn = uilib.OButton()
        pick_btn.setIcon(uilib.IconPath('uiBtn_select'))
        pick_btn.setToolTip(
            'Pick skin clusters from selected skinned objects.'
        )
        pick_btn.clicked.connect(self.pickSCFromSelected)
        pick_btn.setSize(24)
        pick_btn.setBgColor(12, 65, 160)

        picker = QtWidgets.QWidget()
        picker_layout = QtWidgets.QHBoxLayout(picker)
        picker_layout.setContentsMargins(thin_margin)
        picker_layout.setSpacing(1)
        picker_layout.addWidget(label)
        picker_layout.setAlignment(label, QtCore.Qt.AlignRight)
        picker_layout.addWidget(self.__skin_cluster_names)
        picker_layout.addWidget(pick_btn)
        # =====================================================================

        # 各種編集ボタン。=====================================================
        btn_widget = QtWidgets.QWidget()
        btn_layout = QtWidgets.QHBoxLayout(btn_widget)
        btn_layout.setContentsMargins(thin_margin)
        btn_layout.setSpacing(1)
        for data in (
            (
                (42, 82, 160), 'Add selected nodes as influence.',
                self.addInfluence, 'uiBtn_addInf'
            ),
            (
                (65, 72, 175), 'Remove selected influences.',
                self.removeInfluence, 'uiBtn_removeInf'
            ),
            (
                (162, 42, 100), 'Reset selected influences.',
                self.resetInfluence, 'uiBtn_reset'
            ),
            10,
            (
                (22, 42, 180), 'Hummer Tool.',
                paintSkinUtility.hummberWeigt, 'uiBtn_toolBox'
            ),
            10,
            (
                (49, 115, 154), 'Select influences of the skin cluster.',
                self.selectInfluence, 'uiBtn_select'
            ),
        ):
            if isinstance(data, int):
                btn_layout.addSpacing(data)
                continue
            color, ann, cmd, icon = data
            button = uilib.OButton()
            button.setSize(32)
            button.setIcon(uilib.IconPath(icon))
            button.setToolTip(ann)
            button.clicked.connect(cmd)
            button.setBgColor(*color)
            btn_layout.addWidget(button)
        btn_layout.addStretch()
        # =====================================================================

        # インフルエンスのリストおよびペイント便利ツール。=====================
        self.__joint_lister = JointLister()
        self.__paint_util = PaintUtility()

        splitter = QtWidgets.QSplitter()
        splitter.addWidget(self.__joint_lister )
        splitter.addWidget(self.__paint_util)
        splitter.setSizes([150, 200])
        splitter.setStretchFactor(0, 1)
        # =====================================================================
        
        # SizePolicyの設定。
        for widget in (picker, btn_widget):
            widget.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
            )

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(thin_margin)
        layout.setSpacing(1)
        layout.addWidget(picker)
        layout.addWidget(btn_widget)
        layout.addWidget(splitter)
        self.setExpanding(False)

    def pickSCFromSelected(self):
        r"""
            選択オブジェクトのSkinClusterをリストし、フィールドに表示する。
        """
        sc = skinUtility.listSkinClustersFromSelected()
        self.__skin_cluster_names.setText(', '.join([x() for x in sc]))
        self.__paint_util.setSkinCluster(sc[0])
        self.__joint_lister.setSkinCluster(sc[0])
        self.__skin_clusters = sc

    def selectInfluence(self):
        r"""
            インフルエンスを選択する。
        """
        with node.DoCommand():
            skinUtility.selectInfluences(self.__skin_clusters)

    def resetInfluence(self):
        r"""
            インフルエンスの状態を現在の状態でリセットする。
        """
        selected = node.selected()
        if not selected:
            return
        with node.DoCommand():
            for sc in self.__skin_clusters:
                sc.resetInfluences(selected, False)
        node.cmds.dgdirty(self.__skin_clusters)

    def addInfluence(self):
        r"""
            選択オブジェクトをインフルエンスとしてを追加する。
        """
        selected = node.selected()
        if not selected:
            return
        with node.DoCommand():
            for sc in self.__skin_clusters:
                sc.addInfluences(selected)
        self.__joint_lister.refresh()

    def removeInfluence(self):
        r"""
            選択インフルエンスをインフルエンス解除する。
        """
        selected = node.selected()
        if not selected:
            return
        with node.DoCommand():
            for sc in self.__skin_clusters:
                sc.removeInfluences(selected)
        self.__joint_lister.refresh()


class SkinningEditor(QtWidgets.QWidget):
    r"""
        ジョイントの作成、編集を行うためのツールを提供するクラス。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):
        """
        super(SkinningEditor, self).__init__(parent)
        self.setWindowTitle('+Skinning Editor')
        bind_util = BindUtility()
        skin_editor = SkinClusterEditor()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(bind_util)
        layout.addWidget(skin_editor)
        layout.setStretchFactor(skin_editor, 1)


class MainGUI(uilib.AbstractSeparatedWindow):
    r"""
        独立ウィンドウ式のSkinningEditorを提供する。
    """
    def centralWidget(self):
        r"""
            Returns:
                SkinningEditor:
        """
        return SkinningEditor()


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。
        
        Returns:
            QtWidgets.QWidget:
    """
    from gris3.uilib import mayaUIlib
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(350, 600)
    widget.show()
    return widget