# -*- coding: utf-8 -*-
r'''
    @file     widgets.py
    @brief    standardConstructor用の専用ウィジェットを提供するモジュール。
    @class    FactoryUtility : ここに説明文を記入
    @date        2017/06/23 21:13[Eske](eske3g@gmail.com)
    @update      2017/06/23 21:13[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
from ... import node, uilib, verutil
from ...constructors import standardConstructor
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

class FactoryUtility(QtWidgets.QGroupBox):
    r'''
        @brief       Factory内で使用するこのコンストラクタ専用のツール集。
        @inheritance QtWidgets.QWidget
        @date        2017/06/23 21:13[Eske](eske3g@gmail.com)
        @update      2017/06/23 21:13[Eske](eske3g@gmail.com)
    '''
    def __init__(self, parent=None):
        r'''
            @brief  初期化を行う。
            @param  parent(None) : [edit]
            @return None
        '''
        super(FactoryUtility, self).__init__(
            'Standard Constructor Utilities', parent
        )
        
        ren_btn = QtWidgets.QPushButton('Rename and relayout in the all group')
        ren_btn.setToolTip(
            'Rename all geometries in the base skeleton.\n'
            'And relayout these geometries into a root group.\n'
            'The root group will be created if it does not exist.'
        )
        ren_btn.clicked.connect(self.relayoutGeos)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(ren_btn)
        layout.addStretch()

    def relayoutGeos(self):
        verutil.reload_module(standardConstructor)
        with node.DoCommand():
            standardConstructor.relayoutForLow()
        
        