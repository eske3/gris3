#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2025/06/06 16:09 Eske Yoshinob[eske3g@gmail.com]
        update:2025/06/06 16:09 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2025 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import uilib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class ExtraConstructorUtil(QtWidgets.QGroupBox):
    def __init__(self, parent=None):
        super(ExtraConstructorUtil, self).__init__(self.label(), parent)
        self.__is_build = False

    def label(self):
        return 'Extra constructor util'

    def initialize(self):
        if self.__is_build:
            return
        self.__is_build = True
        self.buildUI()
        
    def buildUI(self):
        pass