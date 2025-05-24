#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    リグのテストを行うためのUIを提供するモジュール。
    
    Dates:
        date:2017/01/21 23:59[Eske](eske3g@gmail.com)
        update:2023/08/17 22:19 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import uilib, factoryModules
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

class UnitTester(QtWidgets.QGroupBox):
    r"""
        ユニットのテスト実行を行うための機能を提供するクラス。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):
        """
        super(UnitTester, self).__init__('Module Tester', parent)

        finalize_btn = QtWidgets.QPushButton('Finalize Base Skeleton')
        finalize_btn.clicked.connect(self.finalize)
        createctrl_btn = QtWidgets.QPushButton('Create Controller')
        createctrl_btn.clicked.connect(self.createCtrl)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(finalize_btn)
        layout.addWidget(createctrl_btn)

    def finalize(self):
        r"""
            ベースジョイントのファイナライズを行う。
        """
        from gris3 import core
        with core.Do:
            core.finalizeBaseSkeleton()

    def createCtrl(self):
        r"""
            コントローラの作成を行う。
        """
        from gris3 import core
        with core.Do:
            core.createRigForAllUnit()

class MiscWidget(QtWidgets.QWidget, factoryModules.AbstractFactoryTab):
    r"""
        メインGUI。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (any):(QtWidgets.QWidget) : 親ウィジェット
        """
        super(MiscWidget, self).__init__(parent)
        self.customInit()

        module_tester = UnitTester()
        from gris3.gadgets import archiver
        self.__archiver = archiver.RigDataArchiver()

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(module_tester, 0, 0, 1, 1)
        layout.addWidget(self.__archiver, 1, 0 , 1, 1)
        layout.setRowStretch(2, 1)

    def refreshState(self):
        r"""
            AdvancedTabWidget内のこのウィジェットがアクティブになった
            時に更新をかける時に呼ばれるメソッド。
        """
        fs = factoryModules.FactorySettings()
        archiver = self.__archiver.view()
        archiver.setPath(fs.subDirPath('archives'))
