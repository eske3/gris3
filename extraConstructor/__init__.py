#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Constructorに追加プロセスを入れ込む機能ExtraConstructorを提供するモジュール。
    
    Dates:
        date:2017/01/21 23:55[Eske](eske3g@gmail.com)
        update:2025/06/06 13:36 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
class ExtraConstructor(object):
    r"""
        construct.Constructorオブジェクトで実行される各項目の間に差し込む事が
        できるメソッドを定義する機構を提供するクラス。
        Constructorのinit関数などでinstallExtraConstructorを呼び、
        ExtraConstructorを持つモジュール名を指定する事によりこのクラスが
        差し込まれる。
        各メソッドは、Constructor内の同名メソッドが呼ばれた後に呼ばれるるが、
        _メソッド名にすると、同名メソッド名の前に実行される。
        差し込むことができるメソッドは、このクラスを呼ぶコンストラクタの
        メンバ変数"ProcessList"に依存する。
    """
    def __init__(self, const):
        r"""
            Args:
                const (gris3.constructors.BasicExtractor):
        """
        self.__constructor = const
 
    def constructor(self):
        r"""
            このクラスが取扱うコンストラクタを返す。
            
            Returns:
                constructors.BasicExtractor:
        """
        return self.__constructor

    def createSetupParts(self):
        r"""
            このクラスでリグを組む際に必要なパーツを作成するためのメソッド。
            上書き専用メソッド。
        """
        pass

    def setupUtil(self):
        r"""
            このExtraConstrutorを実行するにあたって必要なノードなどを作成
            するためのGUIを返す。
            必要に応じてQtWidgetsを基底クラスとするサブクラスの
            クラスオブジェクトを返す。
            （インスタンスではない点に注意）

            Returns:
                QtWidgets.QWidget: 
        """
        return

