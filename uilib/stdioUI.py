# -*- coding: utf-8 -*-
r'''
    @file     stdioUI.py
    @brief    標準出力に対するアクセスを行うためのヘルパクラスを提供するモジュール。
    @class    StdMessenger : 標準出力・エラーを受け取り、任意のメソッドを呼び出す
    @date        2017/01/21 23:58[Eske](eske3g@gmail.com)
    @update      2017/01/21 23:58[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
import sys
from gris3 import lib

class StdMessenger(object):
    r'''
        @brief       標準出力・エラーを受け取り、任意のメソッドを呼び出す
        @brief       機構を提供するクラス。
        @brief       このクラスのインスタンスをsys.stdoutなどに渡すことにより、このクラスが
        @brief       代わりに標準出力などを受け取り、何らかの処理（初期化時に指定した関数による）
        @brief       を行う。
        @inheritance object
        @date        2017/01/21 23:58[Eske](eske3g@gmail.com)
        @update      2017/01/21 23:58[Eske](eske3g@gmail.com)
    '''
    def __init__(self, callback, defaultStdio=None):
        r'''
            @brief  初期化関数。引数callbackに標準出力から送られてきたメッセージに対する
            @brief  処理を行う関数をセットする。
            @brief  callbackは引数として文字をうけとれるようにする必要がある。
            @param  callback : [function]
            @param  defaultStdio(None) : [edit]
            @return None
        '''
        self.__callback = callback
        self.__default_stdIO = defaultStdio

    def setDefaultStdIO(self, stdio):
        r'''
            @brief  ここに説明文を記入
            @param  stdio : [edit]
            @return None
        '''
        self.__default_stdIO = stdio

    def write(self, message):
        r'''
            @brief  ここに説明文を記入
            @param  message : [edit]
            @return None
        '''
        try:
            self.__callback(lib.decode(message))
        except Exception as e:
            if self.__default_stdIO:
                self.__default_stdIO.write(e.args[0])

        if self.__default_stdIO:
            self.__default_stdIO.write(message)