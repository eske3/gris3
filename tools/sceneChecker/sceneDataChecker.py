#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    シーン自体にチェックを行うための機能を提供するモジュール。
    checkUtilを用いたフレームワークに則る形の機能を提供する。

    Dates:
        date:2024/06/03 16:46 Eske Yoshinob[eske3g@gmail.com]
        update:2024/06/03 16:46 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .. import checkUtil, cleanup
from ... import node

class SceneDataChecker(checkUtil.AbstractChecker):
    def __init__(self):
        super(SceneDataChecker, self).__init__()
        self.setCategory('Scene Data Checker')
        self.__invalid_plugins = []

    def setInvalidPlugins(self, *pluginNames):
        self.__invalid_plugins = list(pluginNames)

    def invalidPlugins(self):
        return self.__invalid_plugins[:]
    
    def clearInvalidPlugins(self):
        self.__invalid_plugins = []
    
    def listLoadedInvalidPlugins(self):
        return [
            checkUtil.CheckedResult(x, checkUtil.CheckedResult.Warning)
            for x in self.invalidPlugins()
            if node.cmds.pluginInfo(x, q=True, l=True)
        ]

    @staticmethod
    def listLockedShadingEngines():
        return [
            checkUtil.CheckedResult(x)
            for x in cleanup.DefaultShadingEngines
            if (
                node.cmds.lockNode(x, l=True, q=True)[0] or
                node.cmds.lockNode(x, lu=True, q=True)[0]
            )
        ]

    @staticmethod
    def listUnknownPlugins():
        return [
            checkUtil.CheckedResult(x, checkUtil.CheckedResult.Warning)
            for x in node.cmds.unknownPlugin(q=True, l=True) or []
        ]

    def check(self):
        results = []
        locked_sgs = self.listLockedShadingEngines()
        if locked_sgs:
            results.append(
                ('Locked default shading engine found.', locked_sgs)
            )

        unknown_plugins = self.listUnknownPlugins()
        if unknown_plugins:
            results.append(
                (
                    '{} unknown plugins are detected.'.format(
                        len(unknown_plugins)
                    ),
                    unknown_plugins
                )
            )
        
        invalid_plugins = self.listLoadedInvalidPlugins()
        if invalid_plugins:
            results.append(
                ('These plugins should not be load.', invalid_plugins)
            )
        return results