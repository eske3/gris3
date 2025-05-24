#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    MayaPythonのバグフィックスバージョンを提供するモジュール。
    
    Dates:
        date:2017/01/22 0:02[Eske](eske3g@gmail.com)
        update:2023/04/27 14:56 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from . import verutil
from functools import partial
from maya.cmds import *
from maya import mel

MAYA_VERSION = float(about(v=True).split()[0])

# プラグインのセットアップ。 ==================================================
for plugin in ['matrixNodes']:
    if not pluginInfo(plugin, q=True, l=True):
        loadPlugin(plugin)
# =============================================================================

# Melのラッパー実行クラスの作成。==============================================
class Mel(object):
    def __getattribute__(self, name):
        self.ProcedureName = name
        return partial(object.__getattribute__(self, '_assemble_proc'), name)

    def _assemble_proc(self, procname, *args):
        cmd = '{} {};'.format(procname, ' '.join([str(x) for x in args]))
        return mel.eval(cmd)
# =============================================================================

def __getObjects(objects):
    r"""
        ここに説明文を記入
        
        Args:
            objects (any):[edit]
            
        Returns:
            any:
    """
    if not objects:
        return ls(sl=True)
    else:
        return ls(*objects)

if abs(MAYA_VERSION - 2014) < 0.001:
    # Fix a bug abount the parent function.////////////////////////////////////
    __old_parent = parent
    def parent(*objects, **flags):
        r"""
            ここに説明文を記入
            
            Args:
                *objects (any):
                **flags (any):
                
            Returns:
                any:
        """
        objects = __getObjects(objects)
        if 'w' in flags or 'world' in flags:
            last_index = None
        else:
            last_index = -1
        for object in objects[:last_index]:
            if nodeType(object) == 'joint':
                con = listConnections(
                    object + '.inverseScale', s=True, d=False, p=True
                )
                if not con:
                    continue
                src = con[0].split('.')[0]
                disconnectAttr(con[0], object + '.inverseScale')

        return __old_parent(*[verutil.String(x) for x in objects], **flags)
    # /////////////////////////////////////////////////////////////////////////

