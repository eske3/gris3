#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    仮の作業データ保存機能を提供するモジュール。
    
    Dates:
        date:2017/01/22 0:03[Eske](eske3g@gmail.com)
        update:2025/05/25 09:52 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import factoryModules, exporter, uilib
from gris3.uilib import factoryUI
QtWidgets, QtGui, QtCore = (
    factoryModules.QtWidgets, factoryModules.QtGui, factoryModules.QtCore
)

class WorkspaceManager(factoryModules.AbstractDepartmentGUI):
    r"""
        ファイルの保存、オープンなどのオペレーション機能を提供するクラス。
    """
    def init(self):
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
        r"""
            ファイルをセーブするメソッド。
            
            Args:
                rootpath (str):書き出し先のディレクトリパス
                filename (str):ファイル名
        """
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
    def init(self):
        self.setDirectoryName('workScenes')

    def label(self):
        r"""
            Factoryのタブに表示するラベルを返す。
            
            Returns:
                str:
        """
        return 'Workspace'

    def priority(self):
        r"""
            表示優先順位を返す。
            
            Returns:
                int:
        """
        return -1001

    def GUI(self):
        r"""
            Factoryのタブに表示するUIを定義するクラスを返す。
            
            Returns:
                WorkspaceManager:
        """
        return WorkspaceManager
