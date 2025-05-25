#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ドリブンキーの編集や書き出しなどを行う機能を提供するモジュール。
    
    Dates:
        date:2017/01/22 0:03[Eske](eske3g@gmail.com)
        update:2025/05/25 09:43 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import factoryModules, exporter
from gris3 import uilib
from gris3.gadgets import drivenManager
from gris3.uilib import factoryUI
QtWidgets, QtGui, QtCore = (
    factoryModules.QtWidgets, factoryModules.QtGui, factoryModules.QtCore
)

class DrivenKeyExporter(QtWidgets.QWidget):
    r"""
        DrivenKeyを書き出すための補助ツールとエクスポーターを提供するクラス。
    """
    def __init__(self, parent=None):
        r"""            
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(DrivenKeyExporter, self).__init__(parent)
        
        utility = drivenManager.DrivenUtility()

        view = factoryUI.FileView()
        view.exportButtonClicked.connect(self.export)
        view.setBrowserContext(factoryUI.MayaAsciiBrowserContext)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(utility)
        layout.addWidget(view)

        self.__view = view

    def setRootPath(self, path):
        r"""
            エクスポーターで表示するディレクトリを指定するメソッド。
            
            Args:
                path (str):ディレクトリパス
        """
        self.__view.setRootPath(path)

    def selectDrivenNodes(self):
        r"""
            選択ノード下のDrivenキーが入っているノードを選択する
        """
        drivenUtilities.selectDrivenNode(isSelecting=True)

    def export(self, rootpath, filename):
        r"""
            選択ノードについているDrivenキーをエクスポートする
            
            Args:
                rootpath (str):書き出し先のディレクトリパス
                filename (str):ファイル名
        """
        exporter.exportSelectedDrivenKeys(
            rootpath, filename, self.__view.isOverwrite()
        )


class DrivenManager(factoryModules.AbstractDepartmentGUI):
    r"""
        ベースジョイントの編集・保存などのUIを提供するクラス。
    """
    def init(self):
        # タブを作成。=========================================================
        view = DrivenKeyExporter()
        view.setRootPath(self.workspaceDir())
        # =====================================================================

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(view)


class Department(factoryModules.AbstractDepartment):
    def init(self):
        self.setDirectoryName('drivenKeys')

    def label(self):
        r"""
            Factoryのタブに表示するラベルを返す。
            
            Returns:
                str:
        """
        return 'Driven Manager'

    def priority(self):
        r"""
            表示優先順位を返す
            
            Returns:
                int:
        """
        return 5

    def GUI(self):
        r"""
            Factoryのタブに表示するUIを定義するクラスを返す。
            
            Returns:
                DrivenManager:
        """
        return DrivenManager
