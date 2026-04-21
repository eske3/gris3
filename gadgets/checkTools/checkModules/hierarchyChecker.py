#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2025/12/09 10:56 Eske Yoshinob[eske3g@gmail.com]
        update:2025/12/09 10:56 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2025 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .... import lib
from ....tools import checkUtil
from . import genericCheckerBase


class CategoryOption(genericCheckerBase.GenericCategoryOption):
    Checker = checkUtil.DataBasedHierarchyChecker
    DefaultPackage = 'gris3AddOns.checkToolsPresets.hierarchyChecker'

    def __init__(self):
        super(CategoryOption, self).__init__()
        self.target_data = []

    def category(self):
        return 'Joint Hierarchy Checker'

    def setOptions(self, **optionData):
        self.target_data = []
        mod_name = optionData.get('presetModule')
        if not mod_name:
            return
        if not '.' in mod_name:
            mod_name = '{}.{}'.format(self.DefaultPackage, mod_name)
        mod = lib.importModule(mod_name, True)
        if not mod:
            return
        if not hasattr(mod, 'HierarchyData'):
            return
        self.target_data = [mod.HierarchyData]

    def initChecker(self, checkerTypeObj):
        r"""
            Args:
                checkerTypeObj (type):checkUtil.DataBasedHierarchyChecker
            
            Returns:
                checkUtil.DataBasedHierarchyChecker: 
        """
        obj = checkerTypeObj()
        obj.setTargets(self.target_data)
        return obj

