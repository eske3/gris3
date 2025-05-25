#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    モデルを保存するための機能を提供するモジュール。
    
    Dates:
        date:2017/01/22 0:03[Eske](eske3g@gmail.com)
        update:2021/04/24 04:29 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3 import factoryModules, exporter, uilib
from gris3.uilib import factoryUI
from gris3.gadgets import modelSetupWidget
QtWidgets, QtGui, QtCore = (
    factoryModules.QtWidgets, factoryModules.QtGui, factoryModules.QtCore
)

class BasenameEditor(QtWidgets.QComboBox):
    r"""
        LODの一覧を選択するUIを提供する。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(BasenameEditor, self).__init__(parent)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        self.setLineEdit(QtWidgets.QLineEdit())

        # アセットの情報を取得。===============================================
        fs = factoryModules.FactorySettings()
        from gris3 import constructors
        cstman = constructors.ConstructorManager()
        lods = cstman.listLod(fs.constructorName())

        prefix = fs.assetName() + '_'
        self.addItems([prefix+x for x in lods])
        # =====================================================================

        # アセットのLODを取得するための正規表現の作成。========================
        import re
        self.__lod_ptn = re.compile('(%s)([a-zA-Z\d]+)' % prefix)
        # =====================================================================

    def setText(self, text):
        r"""
            入力ファイルを受取るメソッド
            
            Args:
                text (str):
        """
        r = self.__lod_ptn.match(text)
        if not r:
            return
        id = self.findText(''.join(r.groups()))
        if id >= 0:
            self.setCurrentIndex(id)

    def text(self):
        r"""
            名前としての文字列を返す。
            
            Returns:
                str:
        """
        return self.currentText()


class ModelFileView(factoryUI.FileView):
    r"""
        モデル名を選択式で設定するビューワーを提供するクラス
    """
    def createBasenameEditor(self):
        r"""
            コンボボックス型のフィールドを返す。
            
            Returns:
                BasenameEditor:
        """
        return BasenameEditor()


class ModelManager(factoryModules.AbstractDepartmentGUI):
    r"""
        モデル編集機能およびセーブ機能を提供するGUIクラス。
    """
    def init(self):
        view = ModelFileView()
        view.setRootPath(self.workspaceDir())
        view.exportButtonClicked.connect(self.export)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(view)

        self.__view = view

    def export(self, rootpath, filename):
        r"""
            選択オブジェクトをエクスポートする。
            
            Args:
                rootpath (str):書き出し先のディレクトリパス
                filename (str):ベースとなるファイル名
        """
        exporter.exportMayaFile(
            rootpath, filename, self.__view.isOverwrite(),
        )


class Department(factoryModules.AbstractDepartment):
    r"""
        ベースジョイントにまつわる機能を管理するためのクラス。
    """
    def init(self):
        self.setDirectoryName('models')

    def label(self):
        r"""
             Factoryのタブに表示するラベルを返す。

            Returns:
                str:
        """
        return 'Models'

    def priority(self):
        r"""
            表示優先順位を返す。

            Returns:
                int:
        """
        return -1000

    def GUI(self):
        r"""
            Factoryのタブに表示するUIを定義するクラスを返すメソッド。
            
            Returns:
                ModelManager:
        """
        return ModelManager
