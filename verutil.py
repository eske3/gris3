#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    python2と3の互換を取るための機能を提供するモジュール

    Dates:
        date:2021/02/09 21:53 eske yoshinob[eske3g@gmail.com]
        update:2021/02/09 21:53 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2021 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""

import sys
import string

PyVer = sys.version_info[0]
String_type = type('')

if PyVer < 3:
    # バージョン2シリーズ用
    UPPERCASE = list(string.uppercase)
    LOWERCASE = list(string.lowercase)
    LETTERS = string.letters
    reload_module = reload
    String = unicode
    BaseString = basestring
    Long = long
    execfile = execfile
else:
    UPPERCASE = list(string.ascii_uppercase)
    LOWERCASE = list(string.ascii_lowercase)
    LETTERS = string.ascii_letters
    from importlib import reload as reload_module
    String = str
    BaseString = str
    Long = int

    def execfile(filepath, globals=None, locals=None, encode=None):
        globals = {} if globals is None else globals
        globals.update(
            {'__file__': filepath, '__name__': '__main__'}
        )
        flags = {}
        if encode is None:
            flags['encoding'] = sys.getdefaultencoding()
        elif encode:
            flags['encoding'] = encode

        with open(filepath, 'r', **flags) as f:
            exec(compile(f.read(), filepath, 'exec'), globals, locals)
