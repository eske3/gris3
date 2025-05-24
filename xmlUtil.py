#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ここに説明文を記入
    
    Dates:
        date:2017/01/21 23:57[Eske](eske3g@gmail.com)
        update:2023/02/07 13:52 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from xml.etree.ElementTree import ElementTree
from xml.etree.ElementTree import Element
import os
import re
import codecs
from . import lib, verutil


Header = '<?xml version="1.0" encoding="utf-8" ?>'
if hasattr(Element, 'getchildren'):
    XmlVer = 2.0
else:
    XmlVer = 3.0


def toXmlText(text):
    r"""
        入力テキストをタグ無しのXML用フォーマットに変換する関数。
        
        Args:
            text (str):
            
        Returns:
            str:
    """
    if not text:
        return ''

    return text.replace(
        '<', '&lt;'
    ).replace(
        '>', '&gt;'
    ).replace(
        '&', '&amp;'
    ).replace(
        '"', '&quot;'
    )
 

def fromXmlText(text):
    r"""
        入力テキストをタグありのプレーンテキストに変換する関数。
        
        Args:
            text (str):
            
        Returns:
            str:
    """
    if not text:
        return ''
    return text.replace(
        '&amp;', '&'
    ).replace(
        '&quot;', '"'
    ).replace(
        '&lt;', '<'
    ).replace(
        '&gt;', '>' 
    )


# /////////////////////////////////////////////////////////////////////////////
# XML perser.                                                                //
# /////////////////////////////////////////////////////////////////////////////
class XmlElement(object):
    r"""
        xml.etree.ElementTree.Elementの機能を提供するラッパークラス
    """
    def __init__(self, element, parent=None):
        r"""
            Args:
                element (xml.etree.ElementTree.Element):
                parent (XmlElement):
        """
        self.__element = element
        self.tag       = self.__element.tag
        self.attrib    = self.__element.attrib
        self.__parent  = parent
        if XmlVer < 3:
            self.__get_element_children = self.__element.getchildren

    def sourceElement(self):
        r"""
            情報元となるxmlElementオブジェクトを返す。
            
            Returns:
                xml.etree.ElementTree.Element:
        """
        return self.__element

    def parent(self):
        r"""
            親のXmlElementオブジェクトを返す。
            
            Returns:
                XmlElement:
        """
        return self.__parent

    def setText(self, text):
        r"""
            テキストを設定する
            
            Args:
                text (str):
        """
        self.__element.text = verutil.String(text)

    def text(self):
        r"""
            設定されたテキストを返す。
            
            Returns:
                str:
        """
        return self.__element.text.strip() if self.__element.text else ''

    def textAsList(self):
        r"""
            設定されたテキストを改行コードで分割したリストで返す。
            
            Returns:
                list:
        """
        return [x.strip() for x in self.text().split()]

    def get(self, key, default=''):
        r"""
            任意のキーのアトリビュートの値を返す。
            
            Args:
                key (str):任意のアトリビュート名
                default (any):キーが存在しなかった場合のデフォルト値
                
            Returns:
                any:
        """
        return self.__element.get(key, default)

    def  __get_element_children(self):
        return list(self.__element)

    def getchildren(self):
        r"""
            子要素を返す。
            
            Returns:
                list:
        """
        return [XmlElement(x, self) for x in self.__get_element_children()]

    def items(self):
        r"""
            アトリビュートのキーと価のペアを返す。
            
            Returns:
                dict:
        """
        return self.__element.items()

    def keys(self):
        r"""
            アトリビュートのキー一覧を返す。
            
            Returns:
                list:
        """
        return list(self.__element.keys())

    def set(self, key, value):
        r"""
            任意のキーに対応する価をセットする。
            
            Args:
                key (str):キーワード
                value (any):任意の価。
        """
        self.__element.set(key, value)

    def removeAttr(self, attribute):
        r"""
            任意のキーのアトリビュートを削除する。
            
            Args:
                attribute (str):アトリビュートのキーとなる名前
                
            Returns:
                bool:削除に成功した場合はTrue、対応したものがなければNone
        """
        if not attribute in self.__element.attrib:
            return
        try:
            del self.__element.attrib[attribute]
        except:
            return False
        else:
            return True

    def find(self, match):
        r"""
            任意のキーに該当する価をかえす。
            
            Args:
                match (str):検索文字列
                
            Returns:
                any:
        """
        return [XmlElement(x, self) for x in self.__element.find(match)]

    def findall(self, match):
        r"""
            任意のキーに該当する価全てを返す。
            
            Args:
                match (str):検索文字列
                
            Returns:
                list:
        """
        return [XmlElement(x, self) for x in self.__element.findall(match)]

    def search(self, char):
        r"""
            Args:
                char (str):
        """
        pass

    def append(self, element):
        r"""
            子オブジェクトを追加する。
            
            Args:
                element (XmlElement):
        """
        self.__element.append(element)

    def addChild(self, tag, **keywords):
        r"""
            任意のタグ、アトリビュートのXmlElementを生成して
            子オブジェクトとして追加する。
            
            Args:
                tag (str):タグ名
                **keywords (any):オプション
                
            Returns:
                XmlElement:
        """
        new_element = Element(tag, keywords)
        self.append(new_element)
        return XmlElement(new_element)

    def insertChild(self, index, tag, **keywords):
        r"""
            任意のtag、アトリビュートのXmlElementを生成して、任意の番号の
            子オブジェクトとして差し込む。
            
            Args:
                index (int):番号
                tag (str):タグ
                **keywords (any):オプション
                
            Returns:
                XmlElement:
        """
        new_element = Element(tag, keywords)
        self.__element.insert(index, new_element)
        return XmlElement(new_element)

    def remove(self, element):
        r"""
            任意のXmlElementを削除する。
            
            Args:
                element (XmlElement):
                
            Returns:
                bool:削除に成功した場合Trueを返す。
        """
        srcElm = element.sourceElement()
        if srcElm in self.__element:
            self.__element.remove(srcElm)
            return True
        return False

    def listchildrenAsText(self):
        r"""
            子オブジェクトのtextをリストにして返す。
            
            Returns:
                list:
        """
        return [x.text.strip() for x in self.__get_element_children()]

    def listchildrenByText(self, text, tag=None, textAsRegularExpression=False):
        r"""
            テキストの内容を内包するオブジェクトを返す。
            
            Args:
                text (str):
                tag (str):タグ
                textAsRegularExpression (bool):テキストを正規表現として扱うか
                
            Returns:
                list:
        """
        result = {}
        mobj = re.compile('^%s$' % text) if textAsRegularExpression else None

        for x in self.__get_element_children():
            if tag != None and x.tag != tag:
                continue

            searchText = ''
            if not textAsRegularExpression:
                searchText = text
                label = x.text.strip() if x.text else ''
                mobj = re.compile('^%s$' % label)
            elif x.text:
                searchText = x.text

            if mobj.search(searchText):
                result[label] = XmlElement(x, self)
        keys = result.keys()

        if text in keys:
            return result[text]
        elif not keys:
            return None

        for key in keys:
            if key == '.*':
                continue
            return result[key]
        return result[keys[0]]

    def listchildren(self, tag='.*'):
        r"""
            任意のタグに該当する子オブジェクトを返す。
            
            Args:
                tag (str):('.*') : タグを検出する正規表現
                
            Returns:
                list:
        """
        mobj = re.compile('^%s$' % tag)
        result = []
        for x in self.__get_element_children():
            if not mobj.search(x.tag):
                continue
            result.append(XmlElement(x, self))
        return result

    def listchildtexts(self, tag='.*'):
        r"""
            listchildrenの戻り値をテキスト化して返す。
            
            Args:
                tag (str):('.*') : タグを検出する正規表現
                
            Returns:
                list:
        """
        return [x.text.strip() for x in self.listchildren(tag=tag)]

    def listAllchildren(self, tag=None):
        r"""
            全ての子を返す。
            
            Args:
                tag (str):タグ
                
            Returns:
                list:
        """
        def getChild(xmlElm, results):
            r"""
                子を返すローカル関数。
                
                Args:
                    xmlElm (XmlElement):
                    results (list):結果を格納するリスト
                    
                Returns:
                    list:
            """
            children = xmlElm.getchildren()
            results.extend(children)
            for child in children:
                getChild(child, results)
            return results

        results = []
        getChild(self, results)

        if not tag:
            return results

        mobj = re.compile(tag)
        newResults = []
        for r in results:
            if not mobj.search(r.tag):
                continue
            newResults.append(r)
        return newResults

    def childelement(self, key, tag='.*'):
        r"""
            引数keyと同じtextを持つ子要素を返す。
            
            Args:
                key (str):
                tag (str):('.*') : [edit]
                
            Returns:
                XmlElement:
        """
        children = self.listchildren(tag)
        for xml in children:
            text = xml.text()
            if key == text:
                return xml
        else:
            return None



class Xml(object):
    r"""
        Xmlデータを格納するオブジェクト。
    """
    ReplaceList = [
        ('<', '&lt;'),
        ('>', '&gt;'),
   ]
    def __init__(self, filename):
        r"""
            Args:
                filename (str):xmlのファイルパス
        """
        self.__filename = filename
        self.__isLoaded = True
        self.xml        = None
        self.__root     = None
        try:
            if XmlVer < 3:
                f = open(filename)
            else:
                f = open(filename, encoding='utf-8')
            # Create xml object.
            self.xml    = ElementTree(file=f)
            self.__root = self.xml.getroot()
        except Exception as e:
            self.__isLoaded = False
            return

        f.close()

    def isLoaded(self):
        r"""
            ファイルが読み込み済みかどうかを返す。
            読み込みに失敗している場合はFalseを返す。
            
            Returns:
                bool:
        """
        return self.__isLoaded

    def sourceFile(self):
        r"""
            入力元となっているファイルパスを返す。
            
            Returns:
                str:
        """
        return self.__filename

    def setSourceFile(self, filename):
        r"""
            入力モトとなるファイルを設定する。
            
            Args:
                filename (str):xmlのファイルパス
        """
        self.__file = filename

    def root(self):
        r"""
            ルートのXmlElementを返す。
            
            Returns:
                XmlElement:
        """
        return XmlElement(self.__root)

    def rootValue(self, key):
        r"""
            任意のキーのrootの価を返す。
            
            Args:
                key (str):
                
            Returns:
                any:
        """
        return self.__root.get(key)

    def saveFile(self, **args):
        r"""
            このオブジェクトの内容をXMLファイルに保存する。
            
            Args:
                **args (any):
                
            Returns:
                bool: 保存に成功した場合Trueを返す。
        """
        def getIndent(indent):
            r"""
                引数indent数に応じた空白を返すローカル関数。
                
                Args:
                    indent (int):
                    
                Returns:
                    str:
            """
            return ''.ljust(indent*4)

        def getTagData(rootXml, indent=0):
            r"""
                タグデータの基づいてテキスト化した結果を返すローカル関数。
                
                Args:
                    rootXml (XmlElement):
                    indent (int):
                    
                Returns:
                    str:
            """
            tag    = '<%s' % rootXml.tag
            endtag = '</%s>' % rootXml.tag
            keys   = rootXml.keys()
            for key in keys:
                value = rootXml.get(key)
                tag += ' %s="%s"' % (key, value)
            tag += '>'
            # Add tag and text.
            outputs = '%s%s\n' % (getIndent(indent), tag)
            text = ''
            if rootXml.text():
                text = rootXml.text().strip()
                for searchText, replaceText in self.ReplaceList:
                    text = text.replace(searchText, replaceText)
            if text:
                outputs += '%s%s\n' % (getIndent(indent+1), text)

            # Get children of rootXml.
            children = rootXml.getchildren()
            cIndent  = indent + 1
            for child in children:
                outputs += getTagData(child, cIndent)

            # Add end tag.
            outputs += '%s%s\n' % (getIndent(indent), endtag)
            if indent == 1:
                outputs += '\n'
            return outputs
        # =====================================================================

        codecArg = {}
        if 'codec' in args:
            codecArg['encoding'] = args['codec']

        outputs = '%s\n' % Header
        root = self.root()
        indent = 0
        outputs += getTagData(root, indent)
        outputs =  lib.encode(outputs)

        try:
            f = codecs.open(self.__filename, 'w', **codecArg)
        except Exception as e:
            print(e.args)
            return False

        f.write(outputs)
        f.close()

        return True

# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////



def createXmlTree(
        filepath, rootTag='root', new=False, codec=None, xmlObject=Xml
    ):
    r"""
        XMLファイルを新規で作成し、それを返す関数。
        作成されたファイルは引数xmlObjectクラスのインスタンスとして返す。
        指定ファイルがすでに存在する場合は、そのXMLファイルを展開し
        xmlObjectで指定したクラスのインスタンスとして返す。
        
        Args:
            filepath (str):xmlファイルパス。
            rootTag (str):
            new (bool):Trueの場合強制的に新規XMLファイルにする。
            codec (str):コーデック指定
            xmlObject (Xml):展開する時に使用するXMLクラスを指定する。
            
        Returns:
            xmlObject:
    """
    if os.path.isfile(filepath) and new == False:
        return xmlObject(filepath)

    if codec:
        codecArg = {'encoding':codec}
    else:
        codecArg = {}

    try:
        f = codecs.open(filepath, 'w', **codecArg)
    except Exception as e:
        print(e.args)
        return None

    f.write(Header)
    f.write('\n<%s>\n</%s>\n' % (rootTag, rootTag))
    f.close()

    return xmlObject(filepath)