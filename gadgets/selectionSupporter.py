#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    
    
    Dates:
        date:2017/01/22 0:01[Eske](eske3g@gmail.com)
        update:2025/07/02 20:57 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import uilib, lib, node
from ..tools import selectionUtil
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


# from importlib import reload
# reload(selectionUtil)


class BasicSelectionWidget(uilib.ClosableGroup):
    SelectInSelection, DeselectInSelection = (0, 1)
    DeselectHierarchy, SelectHierarchy = (2, 3)
    buttonClicked = QtCore.Signal(int)

    def __init__(self, label, icon, tooltips, parent=None):
        super(BasicSelectionWidget, self).__init__(label, parent)
        self.setIcon(uilib.IconPath(icon))
        layout = QtWidgets.QGridLayout(self)

        col = 0
        for grp_name, data in (
            ('In Selection', (
                (
                    self.SelectInSelection, 'selectEndNode',
                    uilib.Color.ExecColor
                ),
                (
                    self.DeselectInSelection, 'deselectEndNode', None
                ),
            )),
            ('As Hierarchy', (
                (
                    self.DeselectHierarchy, 'deselectEndNode',
                    uilib.Color.ExecColor
                ),
                (
                    self.SelectHierarchy, 'selectEndNode', uilib.Color.ExecColor
                ),
            )),
        ):
            grp = QtWidgets.QGroupBox(grp_name)
            grp_layout = QtWidgets.QHBoxLayout(grp)
            for mode, icon, color in data:
                icon_path = uilib.IconPath(
                    'uiBtn_{}'.format(icon if icon else method)
                )
                btn = uilib.OButton(icon_path)
                btn.setToolTip(tooltips[mode])
                btn._mode = mode
                btn.clicked.connect(self._do_action)
                if color:
                    btn.setBgColor(*color)
                btn.setSize(48)
                grp_layout.addWidget(btn)
            layout.addWidget(grp, 0, col, 1, 1)
            col += 1

        layout.setColumnStretch(2, 1)

    def _do_action(self):
        self.execCommand(self.sender()._mode)

    def execCommand(self, mode):
        pass


class EndNodeSelectionUtil(BasicSelectionWidget):
    r"""
        DAGの終端ノードの選択や選択解除を行うウィジェット。
    """
    def __init__(self, parent=None):
        super(EndNodeSelectionUtil, self).__init__(
            'End Node Selection', 'uiBtn_selectEndNode',
            (
                'Select End Node', 'Deselect End Node',
                'Select Hierarchy without End Node',
                'Select End Node in Hierarchy',
            )
        )

    def execCommand(self, mode):
        with node.DoCommand():
            if mode == BasicSelectionWidget.SelectInSelection:
                selectionUtil.selectEndNodes(r=True, ne=True)
            elif mode == BasicSelectionWidget.DeselectInSelection:
                selectionUtil.selectEndNodes(d=True)
            elif mode == BasicSelectionWidget.DeselectHierarchy:
                selectionUtil.selectHierarchyWithEndNodes(True)
            elif mode == BasicSelectionWidget.SelectHierarchy:
                selectionUtil.selectHierarchyWithEndNodes(False)


class ConditionalSelectionWidget(BasicSelectionWidget):
    r"""
        ノードタイプや特定の条件に基づいてフィルタして選択を行うウィジェット。
    """
    def __init__(self, parent=None):
        super(ConditionalSelectionWidget, self).__init__(
            'Conditional Selection', 'uiBtn_condition',
            (
                'Select Node', 'Deselect Node',
                'Select Hierarchy without the node that matches the condition.',
                'Select Node that matches the condition in Hierarchy',
            )
        )
        layout = self.layout()
        
        # Node type filter
        nt_filter_grp = QtWidgets.QGroupBox('Node Type Filter')
        label = QtWidgets.QLabel('Enter node type')
        self.__node_types = QtWidgets.QLineEdit()
        self.__node_types.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.__node_types.customContextMenuRequested.connect(
            lambda pos, w=self.__node_types:
            self.showNodeTypesInSelection(pos, w)
        )
        grp_layout = QtWidgets.QHBoxLayout(nt_filter_grp)
        grp_layout.addWidget(label)
        grp_layout.addWidget(self.__node_types)
        layout.addWidget(nt_filter_grp, 1, 0, 1, 3)

    def listFilteredTypes(self):
        r"""
            Node Type Filterに記述されているノードタイプ一覧を返す。

            Returns:
                list:
        """
        text = self.__node_types.text()
        if not text:
            return []
        node_types = [x.strip() for x in text.split(',')]
        return node_types

    def showNodeTypesInSelection(self, pos, widget):
        r"""
            選択しているノードタイプ一覧を右クリックメニューとして表示する。

            Args:
                pos (QtCore.QPoint):
                widget (QtWidgets.QWidget): 呼び出し元のウィジェット
        """
        input_node_types = self.listFilteredTypes()
        node_types = []
        for obj in node.selected():
            nodelist = [obj]
            if obj.isSubType('transform'):
                nodelist.extend(obj.shapes(ni=True))
            for n in nodelist:
                types = [n.type()]
                if n.isSubType('shape'):
                    types.append(
                        '{}{}'.format(
                            types[0],
                            selectionUtil.ConditionalSelection.ShapeKey
                        )
                    )
                for t in types:
                    if t in node_types or t in input_node_types:
                        continue
                    node_types.append(t)
        menu = QtWidgets.QMenu(self)
        for n in node_types:
            menu.addAction(n)
        action = menu.exec_(widget.mapToGlobal(pos))
        menu.deleteLater()
        if not action:
            return
        input_node_types.append(action.text())
        self.__node_types.setText(', '.join(input_node_types))

    def execCommand(self, mode):
        # from importlib import reload
        # reload(selectionUtil)
        cs = selectionUtil.ConditionalSelection()
        cs.setNodeTypes(self.listFilteredTypes())
        with node.DoCommand():
            if mode == BasicSelectionWidget.SelectInSelection:
                cs.select(r=True, ne=True)
            elif mode == BasicSelectionWidget.DeselectInSelection:
                cs.select(d=True)
            elif mode == BasicSelectionWidget.DeselectHierarchy:
                cs.selectHierarchy(d=True)
            elif mode == BasicSelectionWidget.SelectHierarchy:
                cs.selectHierarchy(r=True, ne=True)


class SelectionUtilWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット。
        """
        super(SelectionUtilWidget, self).__init__(parent)
        self.setWindowTitle('Selection Util')

        endnode_selector = EndNodeSelectionUtil()
        endnode_selector.setExpanding(False)
        condtion_selector = ConditionalSelectionWidget()
        condtion_selector.setExpanding(False)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(endnode_selector)
        layout.addWidget(condtion_selector)
        layout.addStretch()


class MainWidget(uilib.AbstractSeparatedWindow):
    r"""
        MaterialListerの単独ウィンドウを提供するクラス。
    """
    def centralWidget(self):
        r"""
            MaterialListerを作成して返す。
            
            Returns:
                SelectionUtilWidget:
        """
        return SelectionUtilWidget(self)


def showWindow():
    r"""
        Returns:
            MainWidget:
    """
    from gris3.uilib import mayaUIlib
    w = MainWidget(mayaUIlib.MainWindow)
    w.resize(480, 500)
    w.show()
    return w

