#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    名前管理を行うシステムを提供するモジュール。
    
    Dates:
        date:2017/01/22 0:00[Eske](eske3g@gmail.com)
        update:2021/04/23 14:34 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import re
from . import verutil

class AbstractNameRule(verutil.String_type):
    r"""
        命名規則にまつわる機能を提供する規定クラス。
        プロジェクトによって命名規則が違う場合は、このクラスをシステムクラスに
        セットする。
    """
    def __new__(cls, name=''):
        r"""
            Args:
                name (str or AbstractNameRule):
                
            Returns:
                AbstractNameRule:
        """
        if isinstance(name, verutil.BaseString):
            return super(AbstractNameRule, cls).__new__(cls, name)

        if not isinstance(name, AbstractNameRule):
            raise TypeError(
                "unsupported operand type(s) for >>: '%s' and '%s'" % (
                    type(name).__name__, type(cls).__name__
                )
            )
        obj = super(AbstractNameRule, cls).__new__(cls, name)
        obj.setNamespace(name.namespace())
        obj.setName(name.name())
        obj.setNodeType(name.nodeType())
        obj.setPosition(name.positionIndex())
        obj.setExtras(name.extras())
        obj.setPrefix(name.prefix())
        obj.setSuffix(name.suffix())
        return obj

    def __init__(self, name=''):
        r"""
            クラスを継承する時は初期文字から命名規則に則っているかどうかを判定し
            ルール外の場合はエラーを返すようにすること。
            また空文字の場合はスルーするようにすること。
            
            Args:
                name (str):初期名。
        """
        if verutil.PyVer < 2:
            super(AbstractNameRule, self).__init__(name)
        else:
            super(AbstractNameRule, self).__init__()
        self.__pos = 0

    def __call__(self):
        r"""
            コールされた場合は、正しいノード名を返す。
            
            Returns:
                str:
        """
        return self.__str__()

    def __rshift__(self, other):
        r"""
            与えられたNameRuleオブジェクトのデータを自身に移す。
            タイプの違うNameRuleのキャストを行う。
            
            Args:
                other (AbstractNameRule):
        """
        if not isinstance(other, AbstractNameRule):
            raise TypeError(
                "unsupported operand type(s) for >>: '%s' and '%s'" % (
                    type(other).__name__, type(self).__name__
                )
            )
        other.setName(self.name())
        other.setNodeType(self.nodeType())
        other.setPosition(self.positionIndex())
        other.setExtras(self.extras())
        other.setPrefix(self.prefix())
        other.setSuffix(self.suffix())

    def namespace(self):
        r"""
            ネームスペースを返す
            
            Returns:
                str:
        """
        return ''

    def setNamespace(self, namespce):
        r"""
            ノードのネームスペースを設定する。
            
            Args:
                namespce (str):
        """
        pass

    def name(self):
        r"""
            ノードの固有名を返す。
            
            Returns:
                str:
        """
        return ''

    def setName(self, name):
        r"""
            ノードの固有名を設定する。
            
            Args:
                name (str):
        """
        pass

    def nodeType(self):
        r"""
            ノードの種類を返す。
            
            Returns:
                str:
        """
        return ''

    def setNodeType(self, name):
        r"""
            ノードの種類を設定する。
            
            Args:
                name (str):
        """
        pass

    def toPositionIndex(self, position):
        r"""
            与えられた文字列を位置を表すインデックスに変換する。
            intが与えれた場合はそのままスルーする。
            
            Args:
                position (str or int):
                
            Returns:
                int:
        """
        if isinstance(position, verutil.BaseString):
            if not position:
                return 0
            plist = self.positionList()
            if not position in plist:
                raise ValueError(
                    'The given position "'
                    + position
                    + '" is invalid as position string.'
                )
            position = plist.index(position)
        elif isinstance(position, int):
            if not (0 <= position < len(self.positionList())):
                raise ValueError(
                    'The given index "'
                    + str(position)
                    + '" is out of range for the position.'
                )
        else:
            raise TypeError(
                'Invalid type "%s" as position.' % position
            )
        return position

    def positionFromIndex(self, index):
        r"""
            与えれたインデックスに該当する位置を表す文字を返す。
            
            Args:
                index (int):
                
            Returns:
                str:
        """
        return self.positionList()[index]

    def setPosition(self, position):
        r"""
            位置を表す値をセットする。
            この値は0~7のインデックスかpositionListに該当する文字のこの値は
            0~7いずれか。
            
            Args:
                position (list or str):
        """
        self.__pos = self.toPositionIndex(position)

    def position(self):
        r"""
            ノードの場所を表す文字列を返す。
            0('None')の場合のみ空文字列を返す。
            
            Returns:
                str:
        """
        if self.__pos == 0:
            return ''
        return self.positionFromIndex(self.__pos)

    def positionIndex(self):
        r"""
            ノードの場所を表すインデックス。
            
            Returns:
                int:
        """
        return self.__pos

    def setExtras(self, *args):
        r"""
            ルール外の特殊な文字列の設定する。
            
            Args:
                *args (tuple):
        """
        pass

    def extras(self):
        r"""
            ルール外の特殊な文字列のリストを返す。
            
            Returns:
                list:
        """
        return []

    def prefix(self):
        r"""
            固有名に追加するプレフィックスを返す。
            
            Returns:
                str:
        """
        return ''

    def setPrefix(self, prefix):
        r"""
            固有名に追加するプレフィックスを設定する。
            
            Args:
                prefix (str):
        """
        pass

    def suffix(self):
        r"""
            固有名に追加するサフィックスを返す。
            
            Returns:
                str:
        """
        return ''

    def setSuffix(self, suffix):
        r"""
            固有名に追加するサフィックスを設定する。
            
            Args:
                suffix (str):
        """
        pass

    def convertType(self, newNodeType, isAppendString=False):
        r"""
            ノードの種類を変更した状態の新しい同クラスを返す。
            
            Args:
                newNodeType (str):変更後のノードタイプを表す文字列。
                isAppendString (bool):ノードタイプに付加する文字列
                
            Returns:
                str:
        """
        return ''

    def uniqueName(self):
        r"""
            ユニーク名を返すメソッド。
            このクラスの持つ設定に従って生成された名前のノードがすでに
            シーンに存在した場合、ルールに従ったインクリメントを行った
            名前を返すこと。
            
            Returns:
                str:
        """
        return ''

    @staticmethod
    def positionList():
        r"""
            ノードの位置を表す8つの文字列を持つリストを返す静的メソッド。
            返す文字列の意味は順番に
            0:/ None : 位置無し
            1:/ C    : (Center)中心
            2:/ L    : (Left)左
            3:/ R    : (Right)右
            4:/ T    : (Top)上
            5:/ D    : (Dowm)下
            6:/ F    : (Front)前
            7:/ B    : (Back)後
            を表す。
            サブクラスが上書きする場合も上記の順番は必ず守る事。
            
            Returns:
                list:
        """
        return ['None', 'C', 'L', 'R', 'U', 'D', 'F', 'B']

    def mirroredName(self, mirroredStrings=None, withPosition=False):
        r"""
            自身のpositionのミラーとなる名前を返す。
            該当がない場合はNoneを返す。
            mirroredStringsには対象となる文字列の辞書を渡す。
            None(デフォルト）の場合は{'L':'R', 'T':'D', 'F':'B'}が使用される。
            withPosition がTrueの場合、ミラー軸として使用された文字のキーを返す。
            
            Args:
                mirroredStrings (dict):
                withPosition (bool):
                
            Returns:
                Name:
        """
        pl = self.positionList()
        mirrored_strings = (
            {pl[2]:pl[3], pl[4]:pl[5], pl[6]:pl[7]}
            if mirroredStrings is None else mirroredStrings
        )
        p = self.position()
        mirrored = None
        for s, d in mirrored_strings.items():
            if p == s:
                mirrored = (d, s)
            elif p == d:
                mirrored = (s, s)
            else:
                continue
            break
        else:
            return
        new = self.__class__(self())
        new.setPosition(mirrored[0])
        if withPosition:
            return (self.__class__(new()), mirrored[1])
        else:
            return self.__class__(new())


class BasicNameRule(AbstractNameRule):
    r"""
        grisの基本形となるノード命名規則を提供するクラス。
    """
    AllNamePattern = re.compile(
        '^([a-zA-Z][a-zA-Z\d]+:|)([a-zA-Z][a-zA-Z\d]+)_([a-zA-Z\d]+)'
        '(?:_([A-Z]+)$|$)'
    )
    NamePattern = re.compile('^[a-zA-Z][a-zA-Z\d]+$')
    TypePattern = re.compile('^[a-zA-Z\d]+$')
    PosPattern = re.compile('^[A-Z]+$')
    def __init__(self, name=''):
        r"""
            Args:
                name (str):
        """
        super(BasicNameRule, self).__init__(name)
        self.__name = ''
        self.__type = None
        self.__prefix = ''
        self.__suffix = ''
        self.__namespace = ''

        if not name:
            return
        p = self.AllNamePattern.search(verutil.String(name))
        if not p:
            raise ValueError('The given name is not supported : %s' % name)
        self.setup(name, p)

    def setup(self, name, mobj):
        r"""
            Args:
                name (str):
                mobj (any):正規表現オブジェクト
        """
        self.setNamespace(mobj.group(1)[:-1])
        self.setName(mobj.group(2))
        self.setNodeType(mobj.group(3))
        if mobj.group(4):
            self.setPosition(mobj.group(4))

    def setName(self, name):
        r"""
            ノードの固有名を設定する。
            
            Args:
                name (str):
        """
        if not self.NamePattern.search(name):
            raise ValueError('The given name is invalid : %s' % name)
        self.__name = name

    def name(self):
        r"""
            ノードの固有名を返す
            
            Returns:
                str:
        """
        return self.__name

    def namespace(self):
        r"""
            ネームスペースを返す
            
            Returns:
                str:
        """
        return self.__namespace

    def setNamespace(self, namespace):
        r"""
            ノードのネームスペースを設定する。
            
            Args:
                namespace (str):
        """
        self.__namespace = namespace

    def setNodeType(self, nodeType):
        r"""
            ノードの種類を設定する。
            
            Args:
                nodeType (str):
        """
        self.__type = nodeType

    def nodeType(self):
        r"""
            ノードの種類を返す。
            
            Returns:
                str:
        """
        return self.__type

    def prefix(self):
        r"""
            セットされたプレフィックスを返す
            
            Returns:
                str:
        """
        return self.__prefix

    def setPrefix(self, prefix):
        r"""
            プレフィックスをセットする
            
            Args:
                prefix (str):
        """
        self.__prefix = prefix

    def suffix(self):
        r"""
            サフィックスを返す
            
            Returns:
                str:
        """
        return self.__suffix

    def setSuffix(self, suffix):
        r"""
            サフィックスをセットする
            
            Args:
                suffix (str):
        """
        self.__suffix = suffix

    def elements(self):
        r"""
            初期化時にパターンにマッチした要素をリストとして返す。
            
            Returns:
                list:
        """
        if self.positionIndex() == 0:
            return [self.name(), self.nodeType()]
        else:
            return [self.name(), self.nodeType(), self.position()]

    def __repr__(self):
        r"""
            文字列としての表記を返す
            
            Returns:
                str:
        """
        elements = [x for x in self.elements() if x is not None]
        elements[0] = self.prefix() + elements[0] + self.suffix()
        ns = self.namespace()
        basename = u'_'.join(elements)
        if not ns:
            return basename
        return ns + ':' + basename

    def __str__(self):
        r"""
            文字列としての表記を返す
            
            Returns:
                str:
        """
        return self.__repr__()

    def __unicode__(self):
        r"""
            文字列としての表記を返す
            
            Returns:
                str:
        """
        return verutil.String(self.__repr__())

    def convertType(self, newNodeType,  isAppendString=False):
        r"""
            nodeTypeをnewNodeTypeに置き換えたNameオブジェクトを返す。
            isAppendStringがTrueの場合、newNodeTypeは既存のnodeTypeの
            末尾に追加される形で設定される。
            
            Args:
                newNodeType (str):
                isAppendString (bool):
                
            Returns:
                Name:
        """
        new = self.__class__(self())
        if isAppendString and self.nodeType():
            newType = newNodeType[0].upper()
            if len(newNodeType) > 1:
                newType = newType + newNodeType[1:]
            new.setNodeType(self.nodeType() + newType)
        else:
            new.setNodeType(newNodeType)
        return new

class GlobalSys(object):
    r"""
        GRISの挙動についてのグローバルな設定を持つクラス。
        このクラスはシングルトンインスタンス。
    """
    def __new__(cls):
        r"""
            シングルトン化処理を行う。
            
            Returns:
                GlobalSys:
        """
        if hasattr(cls, '__singletoninstance__'):
            return cls.__singletoninstance__
        obj = super(GlobalSys, cls).__new__(cls)
        obj.__default_name_rule = BasicNameRule
        obj.__current_name_rule = BasicNameRule

        cls.__singletoninstance__  = obj
        return obj

    def defaultNameRule(self):
        r"""
            デフォルトの名前オブジェクトを返す
            
            Returns:
                AbstractNameRule:
        """
        return self.__default_name_rule

    def nameRule(self):
        r"""
            現在の名前オブジェクトを返す。
            
            Returns:
                AbstractNameRule:
        """
        return self.__current_name_rule

    def setNameRule(self, nameRuleObject=None):
        r"""
            名前オブジェクトを設定する。
            
            Args:
                nameRuleObject (AbstractNameRule):
        """
        if not nameRuleObject:
            self.__current_name_rule = self.defaultNameRule()
        self.__current_name_rule = nameRuleObject

    def positionList(self):
        r"""
            現在の名前ルールの位置を表す8つの文字リストを返す。
            
            Returns:
                str:
        """
        return self.__current_name_rule.positionList()

    def defaultPositionList(self):
        r"""
            デフォルトの名前ルールの位置を表す8つの文字リストを返す。
            
            Returns:
                list:
        """
        return self.__default_name_rule.positionList()

    def toPositionIndex(self, position):
        r"""
            与えられた文字列を、現在の名前ルールの位置を表すインデックスに
            変換する。
            intが与えれた場合はそのままスルーする。
            
            Args:
                position (str or int):
                
            Returns:
                int:
        """
        return self.__current_name_rule().toPositionIndex(position)
        return position

    def positionFromIndex(self, index):
        r"""
            現在の名前ルールで、与えれたインデックスに該当する位置
            を表す文字を返す。
            
            Args:
                index (int):
                
            Returns:
                str:
        """
        return self.__current_name_rule().positionFromIndex(index)

    def defaultPositionFromIndex(self, index):
        r"""
            デフォルトの名前ルールで、与えれたインデックスに該当する位置
            を表す文字を返す。
            
            Args:
                index (int):
                
            Returns:
                str:
        """
        return self.__default_name_rule().positionFromIndex(index)
