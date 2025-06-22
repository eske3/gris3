#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    フェイシャルの機能の各レイヤ構造の機能を提供するモジュール。
    
    Dates:
        date:2017/02/25 13:10[Eske](eske3g@gmail.com)
        update:2025/06/01 22:19 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from .... import lib
from .. import layer


def listAllLayerOperators():
    r"""
        このモジュールの全てのLayerOperatorを返す。
        LayerOperatorはこのパッケージ内にあるpyファイルから検索される。
        pyファイルの中に、最初の頭文字を大文字にしたクラスが存在し、
        そのクラスがlayer.LayerOperatorクラスのサブクラスである場合その
        クラスがリストされる。
        例）blendShape.pyの中にBlendShapeクラスが存在する場合。
        
        戻り値はレイヤ名をキーとし、そのレイヤ名に対応するクラスを値とした
        辞書オブジェクト。

        Returns:
            dict(str: layer.LayerOperator):
    """
    import os
    modules = lib.loadPythonModules(os.path.dirname(__file__), __package__)
    operators = {}
    for mod in modules:
        name = mod.__name__.rsplit('.', 1)[-1]
        cls_name = name[0].upper() + name[1:]
        if not hasattr(mod, cls_name):
            continue
        cls = getattr(mod, cls_name)
        if not issubclass(cls, layer.LayerOperator):
            continue
        operators[cls.__name__] = cls
    return operators
