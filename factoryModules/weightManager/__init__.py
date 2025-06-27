#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ウェイトの調整ならびに書き出しを行う機能を提供するモジュール
    
    Dates:
        date:2017/01/22 0:04[Eske](eske3g@gmail.com)
        update:2025/05/25 09:50 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import factoryModules, exporter, uilib
from gris3.gadgets import skinningEditor
from gris3.uilib import factoryUI
QtWidgets, QtGui, QtCore = (
    factoryModules.QtWidgets, factoryModules.QtGui, factoryModules.QtCore
)

class ContextOption(factoryUI.ContextOption):
    r"""
        コンテキストメニューに表示するオプション
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ContextOption, self).__init__(parent)

        self.__path_editor = QtWidgets.QLineEdit()
        self.__path_editor.setReadOnly(True)

        # ウェイトファイル情報のエディタ。=====================================
        # インフルエンスのリスト。---------------------------------------------
        model = QtGui.QStandardItemModel(0, 1)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Influences')

        self.__influences = QtWidgets.QTreeView()
        self.__influences.setAlternatingRowColors(True)
        self.__influences.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers
        )
        self.__influences.setRootIsDecorated(False)
        self.__influences.setModel(model)
        # ---------------------------------------------------------------------

        # 適応シェイプ名。-----------------------------------------------------
        self.__target = QtWidgets.QLineEdit()
        self.__target.setToolTip(
            'Shape name that will be binded and restored weight '
            'from the above file.\n'
            'Apply to selected if the field is empty.'
        )
        # ---------------------------------------------------------------------

        # skinCluster名。------------------------------------------------------
        self.__skin_cluster = QtWidgets.QLineEdit()
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        options = QtWidgets.QWidget()
        opt_layout = QtWidgets.QGridLayout(options)
        for i, lw in enumerate(
            (
                ('Apply to', self.__target),
                ('Skin Cluster Name', self.__skin_cluster),
            )
        ):
            opt_layout.addWidget(QtWidgets.QLabel(lw[0]), i, 0, 1, 1)
            opt_layout.addWidget(lw[1], i, 1, 1, 1)
        imp_btn = uilib.OButton(uilib.IconPath('uiBtn_import'))
        imp_btn.setSize(48)
        imp_btn.setBgColor(11, 68, 128)
        imp_btn.setToolTip('Bind and restore the weight.')
        imp_btn.clicked.connect(self.bindAndLoadWeight)
        opt_layout.setRowStretch(i+1, 1)
        opt_layout.addWidget(imp_btn, i+2, 1, 1, 1, QtCore.Qt.AlignRight)

        splitter = QtWidgets.QSplitter()
        splitter.addWidget(self.__influences)
        splitter.addWidget(options)
        splitter.setSizes([280, 250])
        splitter.setStretchFactor(1, 1)

        weightinfo_grp = QtWidgets.QGroupBox('Weight Info')
        weight_layout = QtWidgets.QVBoxLayout(weightinfo_grp)
        weight_layout.addWidget(splitter)
        # ---------------------------------------------------------------------
        # =====================================================================

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(QtWidgets.QLabel('File'), 0, 0, 1, 1)
        layout.addWidget(self.__path_editor, 0, 1, 1, 1)
        layout.addWidget(weightinfo_grp, 1, 0, 1, 2)

    def isScalable(self):
        r"""
            スケール可能かどうかを返すオーバーライド用メソッド。
            
            Returns:
                True:
        """
        return True

    def contextSize(self):
        r"""
            コンテキストのサイズを返すオーバーライド用メソッド
            
            Returns:
                tuple:
        """
        return (1400, 800)

    def setInfluences(self, influences):
        r"""
            influenceのリストをセットする。
            
            Args:
                influences (list):
        """
        model = self.__influences.model()
        model.removeRows(0, model.rowCount())
        for row, i in enumerate(influences):
            item = QtGui.QStandardItem(i)
            model.setItem(row, 0, item)

    def refresh(self):
        r"""
            コンテキスト全体のリフレッシュを行う。
        """
        import os
        files = self.fileNames()
        self.__path_editor.setText('')
        if not files:
            return
        file = os.path.join(self.path(), files[0])
        if not os.path.exists(file):
            return
        self.__path_editor.setText(file)

        from gris3.exporter import skinWeightExporter
        r = skinWeightExporter.Restorer(file)
        data = r.analyzeInfo()
        self.setInfluences(data['Influence order'])

        self.__target.setText(data['Skinned Shape'])
        self.__skin_cluster.setText(data['Skin Cluster'])

    def bindAndLoadWeight(self):
        r"""
            セットされたファイルを用いてバインドとウェイトのロードを行う
        """
        target = self.__target.text()
        sc_name = self.__skin_cluster.text()
        file = self.files()
        if not file:
            return
        from gris3.exporter import skinWeightExporter
        if not target:
            target = skinWeightExporter.cmds.ls(sl=True)[0]
            if not target:
                return
        r = skinWeightExporter.Restorer(file[0])
        r.setShape(target)
        if sc_name:
            r.setSkinClusterName(sc_name)
        r.restore()
        self.hideContext()


class WeightEditor(factoryModules.AbstractDepartmentGUI):
    r"""
        ウェイトにまつわる編集、保存を行うUIを提供するクラス。
    """
    def init(self):
        # ウェイトのエクスポーターGUIの作成。==================================
        weight_exporter = QtWidgets.QWidget()

        self.__view = factoryUI.ModuleBrowserWidget()
        self.__view.setExtraContext(ContextOption)
        self.__view.setExtensions('mel')
        self.__view.setPath(self.workspaceDir())
        
        self.__isOverwrite = QtWidgets.QCheckBox('Overwrite to latest')

        ext_btn = QtWidgets.QPushButton('Export Selected Weights')
        ext_btn.clicked.connect(self.export)

        exp_layout = QtWidgets.QVBoxLayout(weight_exporter)
        exp_layout.setContentsMargins(0, 0, 0, 0)
        exp_layout.addWidget(self.__view)
        exp_layout.addWidget(self.__isOverwrite)
        exp_layout.addWidget(ext_btn)
        # =====================================================================

        # タブを作成。=========================================================
        tab = factoryUI.ToolTabWidget()
        btn = tab.addTab(
            skinningEditor.SkinningEditor(),
            uilib.IconPath('uiBtn_toolBox'), 'Edit'
        )
        btn.setBgColor(*tab.ToolColor)

        btn = tab.addTab(
            weight_exporter, uilib.IconPath('folder.png'), 'Save Weights'
        )
        btn.setBgColor(*tab.SaveColor)
        # =====================================================================

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(tab)

    def export(self):
        r"""
            書き出しを行う。
        """
        rootpath = self.workspaceDir()
        isOverwrite = self.__isOverwrite.isChecked()
        exporter.exportMultSkinWeights(rootpath, isOverwrite)
        self.__view.refresh()


class Department(factoryModules.AbstractDepartment):
    def init(self):
        self.setDirectoryName('weights')

    def label(self):
        r"""
            表示するラベルを返す。
            
            Returns:
                str:
        """
        return 'Weight Exporter'

    def priority(self):
        r"""
            表示順序のプライオリティを返す
            
            Returns:
                int:
        """
        return 8

    def GUI(self):
        r"""
            GUIを返す。
            
            Returns:
                ExtraJointManager:
        """
        return WeightEditor