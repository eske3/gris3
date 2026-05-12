#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2025/12/21 10:34 Eske Yoshinob[eske3g@gmail.com]
        update:2025/12/21 15:34 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2025 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""


import re
import os
from .. import settings, node


def execScript(sciptText):
    with node.DoCommand():
        exec(sciptText)


class Script(object):
    def __init__(self, dirpath, filename, perseName=True):
        r"""
            Args:
                dirpath (str):
                filename (str):
                perseName (bool):
        """
        self.__dir = dirpath
        self.__name = filename
        self.__index = -1
        if perseName:
            ptn = re.compile('^(\d+)_(.+)')
            r = ptn.search(filename)
            if r:
                self.__name = r.group(2)
                self.__index = int(r.group(1))
        self.__cache = None

    def setName(self, name):
        self.__name = name

    def name(self):
        r"""
            Returns:
                str:
        """
        return self.__name

    def index(self):
        return self.__index

    def setIndex(self, index):
        r"""
            Args:
                index (int):
        """
        self.__index = index

    def filepath(self):
        r"""
            Returns:
                str:
        """
        p = os.path.join(self.__dir, '{}_{}'.format(self.index(), self.name()))
        return p
    
    def scriptText(self):
        r"""
            Returns:
                str:
        """
        if self.__cache is None:
            with open(self.filepath(), 'r') as f:
                self.__cache = f.read()
        return self.__cache

    def setScriptText(self, text):
        r"""
            Args:
                text (str):
        """
        self.__cache = text

    def save(self):
        filepath = self.filepath()
        script_text = self.scriptText()
        with open(filepath, 'w') as f:
            f.write(script_text)

    def execute(self):
        execScript(self.scriptText())


class ScriptHolderManager(object):
    PrefDirName = 'scriptHolder'

    def __new__(cls):
        r"""
            Returns:
                ScriptHolderManager:
        """
        if hasattr(cls, '__instance__'):
            return cls.__instance__
        obj = super(ScriptHolderManager, cls).__new__(cls)
        obj.__instance__ = obj
        obj.__prefdir = obj._get_pref_dir()
        return obj

    def _get_pref_dir(self):
        return settings.GlobalPref().subPrefDir(self.PrefDirName)

    def prefDir(self):
        return self.__prefdir

    def listScripts(self, resultMode=0):
        r"""
            Args:
                resultMode (int):
                
            Returns:
                list:
        """
        prefdir = self.prefDir()
        scripts = [Script(prefdir, x) for x in os.listdir(prefdir)]
        scripts = [x for x in scripts if x.index() >= 0]
        if resultMode == -1:
            return scripts
        d = {}
        for s in scripts:
            d.setdefault(s.index(), []).append(s)
        if resultMode == 1:
            return d
        results = []
        ids = sorted(list(d.keys()))
        for idx in ids:
            results.extend(d[idx])
        return results

    def addScript(self, label, scriptText):
        r"""
            Args:
                label (str):
                scriptText (str):
        """
        indexlist = self.listScripts(1).keys()
        index = max(indexlist) if indexlist else 0
        script = Script(self.prefDir(), label, False)
        script.setScriptText(scriptText)
        script.setIndex(index)
        with open(script.filepath(), 'w') as f:
            f.write(scriptText)
        return script

    def saveScripts(self, scripts):
        pref_dir = self._get_pref_dir()
        print('# Script Holder - Save scripts')
        print('    in "{}"'.format(pref_dir))
        
        for script in scripts:
            script.scriptText()
        
        for file in os.listdir(pref_dir):
            filepath = os.path.join(pref_dir, file)
            if not os.path.exists(filepath):
                continue
            os.remove(filepath)

        for i, script in enumerate(scripts):
            script.setIndex(i)
            try:
                script.save()
            except Exception as e:
                print('[Error] {}'.format(e.args()))

        print('# Done.')