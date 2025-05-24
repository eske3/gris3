# -*- coding: utf-8 -*-
r'''
    @file     __init__.py
    @brief    ここに説明文を記入
    @class    Department : ここに説明文を記入
    @date        2017/05/29 18:04[Eske](eske3g@gmail.com)
    @update      2017/05/29 18:04[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
from gris3 import factoryModules
QtWidgets, QtGui, QtCore = (
    factoryModules.QtWidgets, factoryModules.QtGui, factoryModules.QtCore
)

class Department(factoryModules.AbstractDepartment):
    r'''
        @brief       ここに説明文を記入
        @inheritance factoryModules.AbstractDepartment
        @date        2017/05/29 18:04[Eske](eske3g@gmail.com)
        @update      2017/05/29 18:04[Eske](eske3g@gmail.com)
    '''
    def init(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        self.setDirectoryName('facial')

    def label(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return 'Facial'
