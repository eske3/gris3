#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ケージにまつわる機能を提供するモジュール。
    
    Dates:
        date:2017/01/22 0:03[Eske](eske3g@gmail.com)
        update:2025/05/25 09:39 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import factoryModules, exporter
from gris3.uilib import factoryUI
QtWidgets, QtGui, QtCore = (
    factoryModules.QtWidgets, factoryModules.QtGui, factoryModules.QtCore
)


class CageManager(factoryModules.AbstractDepartmentGUI):
    r"""
        ケージなどを保存したりするUIを提供するクラス。
    """
    def init(self):
        view = factoryUI.FileView()
        view.setRootPath(self.workspaceDir())
        view.setBrowserContext(factoryUI.MayaAsciiBrowserContext)
        view.exportButtonClicked.connect(self.export)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(view)
        
        self.__view = view

    def export(self, rootpath, filename):
        r"""
            Mayaファイルの書き出しを行う。
            
            Args:
                rootpath (str): 書き出し先のディレクトリパス
                filename (str):ファイル名
        """
        exporter.exportMayaFile(
            rootpath, filename, self.__view.isOverwrite()
        )


class Department(factoryModules.AbstractDepartment):
    r"""
        ケージにまつわる機能を管理するためのクラス。
    """
    def init(self):
        self.setDirectoryName('cages')

    def label(self):
        r"""
            Factoryのタブに表示するラベルを返す。
            
            Returns:
                str:
        """
        return 'Cage Exporter'

    def priority(self):
        r"""
            表示優先順位を返す。
            
            Returns:
                int:
        """
        return 9
        
    def GUI(self):
        r"""
            Factoryのタブに表示するUIを定義するクラスを返す。
            
            Returns:
                CageManager:
        """
        return CageManager
