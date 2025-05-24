# -*- coding: utf-8 -*-
r'''
    @file     __init__.py
    @brief    ここに説明文を記入
    @class    DrivenKeyEditor : ここに説明文を記入
    @class    DrivenKeyExporter : DrivenKeyを書き出すための補助ツールとエクスポーター
    @class    DrivenManager : ベースジョイントの編集・保存などのUIを提供するクラス。
    @class    Department : ここに説明文を記入
    @date        2017/01/22 0:03[Eske](eske3g@gmail.com)
    @update      2017/09/03 23:28[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
from gris3 import factoryModules, exporter
from gris3 import uilib
from gris3.gadgets import drivenManager
from gris3.uilib import factoryUI
QtWidgets, QtGui, QtCore = (
    factoryModules.QtWidgets, factoryModules.QtGui, factoryModules.QtCore
)

class DrivenKeyExporter(QtWidgets.QWidget):
    r'''
        @brief       DrivenKeyを書き出すための補助ツールとエクスポーター
        @brief       を提供するクラス。
        @inheritance QtWidgets.QWidget
        @date        2017/01/22 0:03[Eske](eske3g@gmail.com)
        @update      2017/09/03 23:28[Eske](eske3g@gmail.com)
    '''
    def __init__(self, parent=None):
        r'''
            @brief  初期化メソッド。
            @param  parent(None) : [QtWidgets.QWidget]
            @return None
        '''
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
        r'''
            @brief  エクスポーターで表示するディレクトリを指定するメソッド。
            @param  path : [str]ディレクトリパス
            @return None
        '''
        self.__view.setRootPath(path)

    def selectDrivenNodes(self):
        r'''
            @brief  選択ノード下のDrivenキーが入っているノードを選択する
            @return None
        '''
        drivenUtilities.selectDrivenNode(isSelecting=True)

    def export(self, rootpath, filename):
        r'''
            @brief  選択ノードについているDrivenキーをエクスポートする
            @param  rootpath : [str]
            @param  filename : [str]
            @return None
        '''
        exporter.exportSelectedDrivenKeys(
            rootpath, filename, self.__view.isOverwrite()
        )


class DrivenManager(factoryModules.AbstractDepartmentGUI):
    r'''
        @brief       ベースジョイントの編集・保存などのUIを提供するクラス。
        @inheritance factoryModules.AbstractDepartmentGUI
        @date        2017/01/22 0:03[Eske](eske3g@gmail.com)
        @update      2017/09/03 23:28[Eske](eske3g@gmail.com)
    '''
    def init(self):
        r'''
            @brief  初期化関数。
            @return None
        '''
        # タブを作成。=========================================================
        view = DrivenKeyExporter()
        view.setRootPath(self.workspaceDir())
        # =====================================================================

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(view)


class Department(factoryModules.AbstractDepartment):
    r'''
        @brief       ここに説明文を記入
        @inheritance factoryModules.AbstractDepartment
        @date        2017/01/22 0:03[Eske](eske3g@gmail.com)
        @update      2017/09/03 23:28[Eske](eske3g@gmail.com)
    '''
    def init(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        self.setDirectoryName('drivenKeys')

    def label(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return 'Driven Manager'

    def priority(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return 5

    def GUI(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return DrivenManager
