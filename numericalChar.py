#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    brief This module provides a numerical alphabet object.
    The numerical alphabet object cab be used as number.

    Dates:
        date:2023/08/03 18:25 Eske Yoshinob[eske3g@gmail.com]
        update:2023/08/03 18:25 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2023 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import math
import string
import sys
from . import verutil
alphalist = list(verutil.UPPERCASE)


def digitToAlpha(index):
    r"""
        Args:
            index (int):
    """
    def cnvDigitToAlpha(sIndex):
        r"""
            Args:
                sIndex (any):
        """
        ilist = sIndex.split()
        result = ''
        for i in ilist:
            result += alphalist[int(i)]
        return result

    i = int(index)
    result = ''
    if i == 0:
        result = '0'
    else:
        while(1):
            if i == 0:
                break
            r = i % 26
            i = int(i / 26)
            result = '%d %s' % (r, result)

    result = cnvDigitToAlpha(result)
    return result


def alphaToDigit(character):
    r"""
        Args:
            character (str):
    """
    result = 0
    mul = 1
    for i in range(len(character)-1, -1, -1):
        s = character[i].upper()
        if not s in alphalist:
            return None

        value = alphalist.index(s) * mul
        result += value
        mul *= 26
    return result


def toDigit(value):
    r"""
        Args:
            value (int or str):
    """
    if isinstance(value, str):
        return alphaToDigit(value)
    return value


## The Alphabet object provides a behavior as numerical.
# This object can be used as number. The character behaves like a number like
# below.\n
# A = 0\n
# B = 1\n
# C = 2...\n
# Z = 25\n
# BA = 26\n
# BC = 27...\n
# The Alphabet object can add a number.\n
class Alphabet(str):
    def __new__(cls, index, isUpper=True):
        r"""
            Args:
                index (str):
                isUpper (bool):
        """
        if not isinstance(index, (str, verutil.String)):
            raise TypeError('The argument must be type "str".')

        if not index.isdigit():
            return str.__new__(cls, index.upper())

        index = digitToAlpha(index)
        if not isUpper:
            index = index.lower()
        return str.__new__(cls, index)

    def __add__(self, argument):
        r"""
            Args:
                argument (str or int):
        """
        if isinstance(argument, str):
            a = str(self) + argument.upper()
            return Alphabet(a)
        elif isinstance(argument, int):
            sdigit = alphaToDigit(self)
            total = sdigit + argument
            return Alphabet(str(total))
        else:
            raise TypeError('')

    def __sub__(self, argument):
        r"""
            Args:
                argument (str or int):
        """
        if isinstance(argument, str):
            a = str(self) - argument.upper()
            return Alphabet(a)
        elif isinstance(argument, int):
            sdigit = alphaToDigit(self)
            total = sdigit - argument
            return Alphabet(str(total))
        else:
            raise TypeError('')

    def zfill(self, pad):
        r"""
            Args:
                pad (int):
        """
        length = pad - len(self)
        if length <= 0:
            return self

        result = self
        addChar = 'A'
        if result[0].islower():
            addChar = 'a'
        for i in range(length):
            result = addChar + result
        return result


class ZInt(int):
    def __add__(self, argument):
        r"""
            Args:
                argument (int):
        """
        return ZInt(int(self) + argument)
    def zfill(self, pad):
        r"""
            Args:
                pad (int):
        """
        return str(self).zfill(pad)


