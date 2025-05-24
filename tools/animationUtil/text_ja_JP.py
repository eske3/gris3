#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Dates:
        date:2021/09/11 19:46 eske yoshinob[eske3g@gmail.com]
        update:2021/09/11 19:46 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2021 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""

TEXT_TABLE = {
    u'あ':'a', u'い':'i', u'う':'u', u'え':'e', u'お':'o',
    u'ぁ':'xa', u'ぃ':'xi', u'ぅ':'xu', u'ぇ':'xe', u'ぉ':'xo',
                        'ゔ':'u',
    u'か':'a', u'き':'i', u'く':'u', u'け':'e', u'こ':'o',
    u'が':'a', u'ぎ':'i', u'ぐ':'u', u'げ':'e', u'ご':'o',
    u'さ':'a', u'し':'i', u'す':'u', u'せ':'e', u'そ':'o',
    u'ざ':'a', u'じ':'i', u'ず':'u', u'ぜ':'e', u'ぞ':'o',
    u'た':'a', u'ち':'i', u'つ':'u', u'て':'e', u'と':'o',
                          u'っ':'-',
    u'だ':'a', u'ぢ':'i', u'づ':'u', u'で':'e', u'ど':'o',
    u'な':'a', u'に':'i', u'ぬ':'u', u'ね':'e', u'の':'o',
    u'は':'a', u'ひ':'i', u'ふ':'u', u'へ':'e', u'ほ':'o',
    u'ば':'pa', u'び':'pi', u'ぶ':'pu', u'べ':'pe', u'ぼ':'po',
    u'ぱ':'pa', u'ぴ':'pi', u'ぷ':'pu', u'ぺ':'pe', u'ぽ':'po',
    u'ま':'pa', u'み':'pi', u'む':'pu', u'め':'pe', u'も':'po',
    u'や':'a',           u'ゆ':'u',           u'よ':'o',
    u'ゃ':'xa',          u'ゅ':'xu',          u'ょ':'xo',
    u'ら':'a', u'り':'i', u'る':'u', u'れ':'e', u'ろ':'o',
    u'わ':'a', u'を':'o', u'ん':'n',

    u'ア':'a', u'イ':'i', u'ウ':'u', u'エ':'e', u'オ':'o',
    u'ァ':'xa', u'ィ':'xi', u'ゥ':'xu', u'ェ':'xe', u'ォ':'xo',
                        'ヴ':'u',
    u'カ':'a', u'キ':'i', u'ク':'u', u'ケ':'e', u'コ':'o',
    u'ガ':'a', u'ギ':'i', u'グ':'u', u'ゲ':'e', u'ゴ':'o',
    u'サ':'a', u'シ':'i', u'ス':'u', u'セ':'e', u'ソ':'o',
    u'ザ':'a', u'ジ':'i', u'ズ':'u', u'ゼ':'e', u'ゾ':'o',
    u'タ':'a', u'チ':'i', u'ツ':'u', u'テ':'e', u'ト':'o',
                          u'ッ':'-',
    u'ダ':'a', u'ヂ':'i', u'ヅ':'u', u'デ':'e', u'ド':'o',
    u'ナ':'a', u'ニ':'i', u'ヌ':'u', u'ネ':'e', u'ノ':'o',
    u'ハ':'a', u'ヒ':'i', u'フ':'u', u'ヘ':'e', u'ホ':'o',
    u'バ':'pa', u'ビ':'pi', u'ブ':'pu', u'ベ':'pe', u'ボ':'po',
    u'パ':'pa', u'ピ':'pi', u'プ':'pu', u'ペ':'pe', u'ポ':'po',
    u'マ':'pa', u'ミ':'pi', u'ム':'pu', u'メ':'pe', u'モ':'po',
    u'ヤ':'a',           u'ユ':'u',           u'ヨ':'o',
    u'ャ':'xa',          u'ュ':'xu',          u'ョ':'xo',
    u'ラ':'a', u'リ':'i', u'ル':'u', u'レ':'e', u'ロ':'o',
    u'ワ':'a', u'ヲ':'o', u'ン':'n', 
    
    u'～':'-', u'ー':'-', u'、':'_'
}

