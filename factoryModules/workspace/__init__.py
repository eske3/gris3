# -*- coding: utf-8 -*-
r'''
    @file     __init__.py
    @brief    ここに説明文を記入
    @class    WorkspaceManager : ベースジョイントの編集・保存などのUIを提供するクラス。
    @class    Department : ベースジョイントにまつわる機能を管理するためのクラス。
    @date        2017/01/22 0:03[Eske](eske3g@gmail.com)
    @update      2017/01/23 0:17[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
from gris3 import factoryModules, exporter, uilib
from gris3.uilib import factoryUI
QtWidgets, QtGui, QtCore = (
    factoryModules.QtWidgets, factoryModules.QtGui, factoryModules.QtCore
)

class WorkspaceManager(factoryModules.AbstractDepartmentGUI):
    r'''
        @brief       ベースジョイントの編集・保存などのUIを提供するクラス。
        @inheritance factoryModules.AbstractDepartmentGUI
        @date        2017/01/22 0:03[Eske](eske3g@gmail.com)
        @update      2017/01/23 0:17[Eske](eske3g@gmail.com)
    '''
    def init(self):
        r'''
            @brief  初期化関数。
            @return None
        '''
        self.__save_module = exporter.MayaFileSaver()

        view = factoryUI.FileView()
        view.browser().setExtensions(
            list(self.__save_module.FileTypes.values())
        )
        view.setButtonLabel('Save')
        view.setButtonIcon(uilib.IconPath('uiBtn_save'))
        view.setRootPath(self.workspaceDir())
        view.exportButtonClicked.connect(self.save)

        # 拡張子指定用GUIの追加。==============================================
        ext_layout = QtWidgets.QHBoxLayout()

        self.__ext_grp = QtWidgets.QButtonGroup(ext_layout)
        self.__ext_grp.addButton(QtWidgets.QRadioButton('MayaAscii'), 0)
        self.__ext_grp.addButton(QtWidgets.QRadioButton('MayaBinary'), 1)
        self.__ext_grp.button(1).setChecked(True)
        for i in range(2):
            ext_layout.addWidget(self.__ext_grp.button(i))
        ext_layout.addStretch()
        view.addOptionLayout(ext_layout, 2, 0, 1, 2)
        # =====================================================================

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(view)

        self.__view = view
        # self.__save_module.setIsMakingCurrent(False)

    def save(self, rootpath, filename):
        r'''
            @brief  ファイルをセーブするメソッド。
            @param  rootpath : [str]
            @param  filename : [str]
            @return None
        '''
        import re
        extensions = list(self.__save_module.FileTypes.values())
        for ptn in [re.compile('\.'+x+'$', re.IGNORECASE) for x in extensions]:
            if ptn.search(filename):
                filename = ptn.sub('', filename)
                break
        file_type = ['mayaAscii', 'mayaBinary'][self.__ext_grp.checkedId()]
        self.__save_module.setFileType(file_type)
        self.__save_module.setSearchingExtensions(extensions)
        exporter.exportMayaFile(
            rootpath, filename, self.__view.isOverwrite(),
            self.__save_module
        )

class Department(factoryModules.AbstractDepartment):
    r'''
        @brief       ベースジョイントにまつわる機能を管理するためのクラス。
        @inheritance factoryModules.AbstractDepartment
        @date        2017/01/22 0:03[Eske](eske3g@gmail.com)
        @update      2017/01/23 0:17[Eske](eske3g@gmail.com)
    '''
    def init(self):
        r'''
            @brief  初期化関数。
            @return None
        '''
        self.setDirectoryName('workScenes')

    def label(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return 'Workspace'

    def priority(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return -1001

    def GUI(self):
        r'''
            @brief  Factoryのタブに表示するUIを定義するクラスを返すメソッド。
            @return JointManager
        '''
        return WorkspaceManager
