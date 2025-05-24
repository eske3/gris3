#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2023/03/05 22:50 Eske Yoshinob[eske3g@gmail.com]
        update:2023/03/05 22:53 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2023 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from maya import cmds

MakeLiveObject = None

class MakeLiveManager(object):
    def __init__(self):
        self.__lived_objects = []

    def __call__(self):
        r"""
            選択オブジェクトをLive化する。既に一度行った場合はそのオブジェクトを
            再度Live化する。
            既にLive化されている場合はLive化を解除する。
        """
        if cmds.ls(live=True):
            cmds.makeLive(n=True)
            return
        objects = self.livedObjects()
        if objects:
            cmds.makeLive(objects)
        else:
            cmds.makeLive()
        self.setLivedObjects(cmds.ls(live=True))

    def livedObjects(self):
        r"""
            登録されているMakeLiveオブジェクトを返す。

            Returns:
                list(str): 
        """
        return self.__lived_objects

    def setLivedObjects(self, objects):
        r"""
            MakeLiveオブジェクトを登録する。

            Args:
                objects (list):
        """
        self.__lived_objects = objects

    def clear(self):
        r"""
            キャッシュされたMakeLiveオブジェクトをクリアする。
        """
        self.setLivedObjects([])
        cmds.makeLive(n=True)


def makeLive():
    r"""
        選択オブジェクト、またはすでに一度Live化されたオブジェクトをLive化する。
        もしくは既にLive化されている場合は解除する。
    """
    global MakeLiveObject
    if not MakeLiveObject:
        MakeLiveObject = MakeLiveManager()
    MakeLiveObject()


def clearCache():
    r"""
        登録されているLive化オブジェクトのリストをクリアする。
    """
    global MakeLiveObject
    if not MakeLiveObject:
        return
    MakeLiveObject.clear()
