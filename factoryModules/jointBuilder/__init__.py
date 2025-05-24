#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ここに説明文を記入
    
    Dates:
        date:2017/01/21 22:35[Eske](eske3g@gmail.com)
        update:2021/04/23 10:02 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import core, factoryModules, exporter, uilib, func
from gris3.uilib import factoryUI
from gris3.gadgets import jointEditorWidget, unitCreator
from gris3.tools import jointEditor
# from gris3.factoryModules.jointBuilder import unitCreator
QtWidgets, QtGui, QtCore = (
    factoryModules.QtWidgets, factoryModules.QtGui, factoryModules.QtCore
)

class JointManager(factoryModules.AbstractDepartmentGUI):
    r"""
        ベースジョイントの編集・保存などのUIを提供するクラス。
    """
    def init(self):
        view = factoryUI.FileView()
        view.setRootPath(self.workspaceDir())
        view.setBrowserContext(factoryUI.MayaAsciiBrowserContext)
        view.exportButtonClicked.connect(self.export)

        # タブを作成。=========================================================
        tab = factoryUI.ToolTabWidget()
        btn = tab.addTab(
            jointEditorWidget.JointEditor(),
            uilib.IconPath('uiBtn_toolBox'), 'Edit'
        )
        btn.setBgColor(*tab.ToolColor)

        btn = tab.addTab(
            unitCreator.Creator(), uilib.IconPath('unit.png'), 'Unit'
        )
        btn.setBgColor(48, 129, 152)

        btn = tab.addTab(
            view, uilib.IconPath('folder.png'), 'Save Joints'
        )
        btn.setBgColor(*tab.SaveColor)
        # =====================================================================

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(tab)

        self.__view = view

    def export(self, rootpath, filename):
        r"""
            選択アイテムを書き出す。
            
            Args:
                rootpath (str):
                filename (str):
        """
        exporter.exportMayaFile(
            rootpath, filename, self.__view.isOverwrite()
        )


class Department(factoryModules.AbstractDepartment):
    r"""
        ベースジョイントにまつわる機能を管理するためのクラス。
    """
    def init(self):
        self.setDirectoryName('joints')

    def label(self):
        r"""
            Returns:
                str:
        """
        return 'Joint Builder'

    def priority(self):
        r"""
            Returns:
                int:
        """
        return 10

    def GUI(self):
        r"""
            Factoryのタブに表示するUIを定義するクラスを返すメソッド。
            
            Returns:
                JointManager:
        """
        return JointManager
