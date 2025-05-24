# -*- coding: utf-8 -*-
r'''
    @file     __init__.py
    @brief    ケージにまつわる機能を提供するモジュール。
    @class    CageManager : ケージなどを保存したりするUIを提供するクラス。
    @class    Department : ケージにまつわる機能を管理するためのクラス。
    @date        2017/01/22 0:03[Eske](eske3g@gmail.com)
    @update      2017/01/22 0:03[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
from gris3 import factoryModules, exporter
from gris3.uilib import factoryUI
QtWidgets, QtGui, QtCore = (
    factoryModules.QtWidgets, factoryModules.QtGui, factoryModules.QtCore
)

class CageManager(factoryModules.AbstractDepartmentGUI):
    r'''
        @brief       ケージなどを保存したりするUIを提供するクラス。
        @inheritance factoryModules.AbstractDepartmentGUI
        @date        2017/01/22 0:03[Eske](eske3g@gmail.com)
        @update      2017/01/22 0:03[Eske](eske3g@gmail.com)
    '''
    def init(self):
        r'''
            @brief  初期化関数。
            @return None
        '''
        view = factoryUI.FileView()
        view.setRootPath(self.workspaceDir())
        view.setBrowserContext(factoryUI.MayaAsciiBrowserContext)
        view.exportButtonClicked.connect(self.export)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(view)
        
        self.__view = view

    def export(self, rootpath, filename):
        r'''
            @brief  ここに説明文を記入
            @param  rootpath : [edit]
            @param  filename : [edit]
            @return None
        '''
        exporter.exportMayaFile(
            rootpath, filename, self.__view.isOverwrite()
        )


class Department(factoryModules.AbstractDepartment):
    r'''
        @brief       ケージにまつわる機能を管理するためのクラス。
        @inheritance factoryModules.AbstractDepartment
        @date        2017/01/22 0:03[Eske](eske3g@gmail.com)
        @update      2017/01/22 0:03[Eske](eske3g@gmail.com)
    '''
    def init(self):
        r'''
            @brief  初期化関数。
            @return None
        '''
        self.setDirectoryName('cages')

    def label(self):
        r'''
            @brief  Factoryのタブに表示するラベルを返すメソッド。
            @return str
        '''
        return 'Cage Exporter'

    def priority(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return 9
        
    def GUI(self):
        r'''
            @brief  Factoryのタブに表示するUIを定義するクラスを返すメソッド。
            @return CageManager
        '''
        return CageManager
