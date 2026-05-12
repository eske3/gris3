#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    チェックを行った結果を一覧で表示するだけの汎用的なチェッカーを提供するモジュール。
    使用する場合はこのモジュールののサブモジュールを作成し、サブモジュール内でクラスのメンバ変数
    Checker
    にtools.checkUtil.AbstractCheckerのサブクラスのタイプオブジェクトを指定する。
    （インスタンスではない）

    Dates:
        date:2025/12/09 10:21 Eske Yoshinob[eske3g@gmail.com]
        update:2025/12/09 10:21 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2025 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import ui, core
from .... import uilib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class GenericCategoryOption(core.AbstractCategoryOption):
    Checker = None
    def setup(self, viewer):
        r"""
            渡されるviewerに対し、ページの追加などのセットアップを行う場合はこのメソッドを上書きする。

            Args:
                viewer (ui.NodeResultViewer):
        """
        pass

    def buildUI(self, parent):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        self.result_view = ui.NodeResultViewer()
        layout = QtWidgets.QVBoxLayout(parent)
        layout.addWidget(self.result_view)
        self.setup(self.result_view)

    def initChecker(self, checkerTypeObj):
        r"""
            チェックを行う際に用いるAbstractCheckerを初期化してインスタンスを返す。
            デフォルトでは初期化するだけだが、何等かの処理を入れたい場合はこｎメソッドを上書きする。

            Args:
                checkerTypeObj (type):AbstractChecker
            
            Returns:
                AbstractChecker: 
        """
        return checkerTypeObj()

    def execCheck(self):
        checker = self.initChecker(self.Checker)
        checked = checker.check()
        self.result_view.setResults(checked)
        return self.getResultFromData(checked)

