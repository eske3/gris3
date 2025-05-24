#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ポリゴンの頂点カラーセットの検出を行う。
    checkToolの設定jsonファイルで使用できるオプションは以下の通り。
    {
        "moduleName": "polyCountChecker",
        "modulePrefix": "-default",
        "options": {
            "goalCount": int,
            "limitCount": int,
            "target": ["操作対象グループ"]
        }
    }
    
    Dates:
        date:2024/06/03 17:48 Eske Yoshinob[eske3g@gmail.com]
        update:2024/06/07 15:10 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import core, ui
from ....tools.sceneChecker import polyCounter
from .... import uilib, node
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class ObjectList(QtWidgets.QTreeView):
    def __init__(self, parent=None):
        super(ObjectList, self).__init__(parent)
        self.setSortingEnabled(True)
        self.setRootIsDecorated(False)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setHorizontalScrollMode(self.ScrollPerPixel)
        self.setEditTriggers(self.NoEditTriggers)

        model = QtGui.QStandardItemModel(0, 2)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Polygon Name')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Number of polygons')
        sel_model = QtCore.QItemSelectionModel(model)
        self.setModel(model)
        self.setSelectionModel(sel_model)


class PolyCountViewer(QtWidgets.QWidget):
    Format = 'Triangle : {}'

    def __init__(self, parent=None):
        super(PolyCountViewer, self).__init__(parent)
        self.__goal_count = None
        self.__limit_count = None
        t_label = QtWidgets.QLabel('Total Poly Count')
        self.counter = QtWidgets.QLabel()
        self.counter.setAutoFillBackground(False)
        f = self.counter.font()
        f.setPixelSize(f.pixelSize() * 2)
        self.counter.setFont(f)
        
        self.obj_list = ObjectList()
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(t_label)
        layout.addWidget(self.counter)
        layout.addWidget(self.obj_list)

    def setGoalCount(self, size=None):
        self.__goal_count = size

    def goalCount(self):
        return self.__goal_count

    def setLimitCount(self, count):
        self.__limit_count = count

    def limitCount(self):
        return self.__limit_count

    def setResults(self, checkedResults):
        model = self.obj_list.model()
        model.removeRows(0, model.rowCount())
        countlist = {}
        for r in checkedResults:
            countlist.setdefault(r[1][0].numFaces, []).append(r)
        row = 0
        counts = list(countlist.keys())
        counts.sort()
        counts.reverse()
        total_counts = []
        for count in counts:
            for r in countlist[count]:
                if hasattr(r[0], 'shortName'):
                    name = r[0].shortName()
                else:
                    name = r[0]
                n_item = QtGui.QStandardItem(name)
                n_item.setData(r[0]())

                c_item = QtGui.QStandardItem(str(count))
                c_item.setData(count)

                model.setItem(row, 0, n_item)
                model.setItem(row, 1, c_item)
                row += 1
                total_counts.append(count)
        poly_count = sum(total_counts)

        e_level = polyCounter.errorLevel(
            poly_count, self.goalCount(), self.limitCount()
        )
        self.counter.setText(self.Format.format(poly_count))

        self.counter.setAutoFillBackground(e_level != 0)
        if e_level == 0:
            return
        p = self.counter.palette()
        p.setColor(p.Window, QtGui.QColor(
            255, 128 * (1-e_level), 0, e_level * 255)
        )
        self.counter.setPalette(p)


class CategoryOption(core.AbstractCategoryOption):
    def  __init__(self):
        super(CategoryOption, self).__init__()
        self.goal_count = None
        self.limit_count = None
        self.targets = ['all_grp']

    def category(self):
        return 'Poly count checker'

    def buildUI(self, parent):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        self.result_view = PolyCountViewer()
        layout = QtWidgets.QVBoxLayout(parent)
        layout.addWidget(self.result_view)

    def setOptions(self, **optionData):
        r"""
            Args:
                **optionData (any):
        """
        self.goal_count = optionData.get('goalCount', None)
        self.limit_count = optionData.get('limitCount', None)
        self.targets = optionData.get('target', ['all_grp'])

    def execCheck(self):
        checker = polyCounter.PolyCountChecker()
        checker.setTargets(self.targets)
        checker.setGoalCount(self.goal_count)
        checker.setLimitCount(self.limit_count)
        print('------  %s' % self.limit_count)
        print('Limit : %s' % checker.limitCount())
        checked = checker.check()
        self.result_view.setGoalCount(self.goal_count)
        self.result_view.setLimitCount(self.limit_count)
        self.result_view.setResults(checked)
        
        e_level = checker.errorLevel()
        print(e_level)
        if e_level < 0.5:
            return self.OK
        elif 0.5 <= e_level < 1.0:
            return self.Warning
        else:
            return self.Error

