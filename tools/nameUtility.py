#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    名前に関する機能を提供するモジュール。
    
    Dates:
        date:2017/05/30 6:07[Eske](eske3g@gmail.com)
        update:2024/01/16 06:21 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import re
from .. import lib, node
from .. import mayaCmds as cmds
from .. import numericalChar
from . import util

SIDE_TABLE = (
    (re.compile('left'), 'right'), (re.compile('right'), 'left'),
    (re.compile('Left'), 'Right'), (re.compile('Right'), 'Left'),
    (re.compile('LEFT'), 'RIGHT'), (re.compile('RIGHT'), 'LEFT'),
    (re.compile('_L'), '_R'), (re.compile('_R'), '_L'),
    (re.compile('^L_'), 'R_'), (re.compile('^R_'), 'L_'),
    (re.compile('L'), 'R'), (re.compile('R'), 'L'),
)
NameFilterRegularExpression = '\w+'


def selectedNodes():
    r"""
        ノードを選択するラッパー関数
        
        Returns:
            list:
    """
    return cmds.ls(sl=True)


class SimpleRenamer(object):
    r"""
        シンプルなリネーム機能を提供するメソッド。
    """
    def __init__(self):
        self.__node = ''

    def setNode(self, nodeName):
        r"""
            リネーム対象ノードを設定する。
            
            Args:
                nodeName (str):
        """
        self.__node = nodeName

    def node(self):
        r"""
            セットされているノード名を返す
            
            Returns:
                str:
        """
        return self.__node

    def name(self):
        r"""
            ノードのショートネームを返す。
            
            Returns:
                str:
        """
        return self.__node.split('|')[-1]

    def rename(self, newName):
        r"""
            リネームを実行する。
            
            Args:
                newName (str):
        """
        return cmds.rename(self.node(), newName)


class OppositeSideRenamer(SimpleRenamer):
    r"""
        特定のルールに従って反対側のオブジェクト名にリネームする
    """
    NumPtn = re.compile('\d+$')
    def oppositeName(self):
        r"""
            対象となる名前を返す。
            
            Returns:
                str:
        """
        node_name = self.name()
        new_name = ''
        for ptn, key in SIDE_TABLE[:-2]:
            if ptn.search(node_name):
                new_name = ptn.sub(key, node_name)
                break
        else:
            return
        return self.NumPtn.sub('', new_name)

    def rename(self):
        r"""
            リネームを行う。
        """
        new_name = self.oppositeName()
        if not new_name:
            return
        cmds.rename(self.node(), new_name)


class MultNameManager(object):
    r"""
        複数の名前のリストをまとめて変更するための機能を提供するクラス。
        いわゆるリネーマーのコア部分となるクラス。
        このクラスではリネーム前とリネーム後の名前の管理を行うがリネーム自体
        は行わない。
    """
    Integer, Alphabetical = range(2)
    def __init__(self):
        self.__renamed_re = ''
        self.__renamed_substring = ''

        self.__namelist = []
        self.__result = []
        self.__use_basename = False
        self.__basename = ''
        self.__numbering_mode = self.Integer
        self.__startnumber = 0
        self.__startchar = 'A'
        self.__padding = 1
        self.__step = 1

        self.__use_re = False
        self.__searching_texts = ''
        self.__replacing_texts = ''

        self.__prefix = ''
        self.__suffix = ''

    def clearResult(self):
        r"""
            キャッシュしている名前変更の結果をクリアする。
        """
        self.__result = []

    def setRenamedRegularExpression(self, expression):
        r"""
            このメソッドで指定された文字列で、リネーム前に予め正規表現による
            置換を行う。
            主にファイルのリネーム時に拡張子を操作対象から外したい時などに
            使用する。
            
            Args:
                expression (str):
        """
        self.__renamed_re = expression
        self.clearResult()

    def setRenamedSubstring(self, character):
        r"""
            リネーム前に予め正規表現による置換を行う際の文字列を指定する。
            
            Args:
                character (str):
        """
        self.__renamed_substring = character
        self.clearResult()

    def setNameList(self, namelist):
        r"""
            置換するファイル名のリストをセットする。
            
            Args:
                namelist (list):
        """
        self.__namelist = namelist[:]
        self.clearResult()

    def nameList(self):
        r"""
            置換するファイル名のリストを返す。
            
            Returns:
                list:
        """
        return self.__namelist[:]

    def useBaseName(self, state):
        r"""
            インクリメントによるリネームを行うかどうかを指定する。
            
            Args:
                state (bool):
        """
        self.__use_basename = bool(state)
        self.clearResult()

    def setBaseName(self, basename):
        r"""
            インクリメントの際のベースとなる名前を指定する。
            
            Args:
                basename (str):
        """
        self.__basename = basename
        self.clearResult()

    def setNumberingAs(self, mode):
        r"""
            インクリメントに使用する文字列の種類を設定する。
            使用できるのはself.Integerかself.Alphabetical。
            
            Args:
                mode (int):
        """
        if not mode in (self.Integer, self.Alphabetical):
            raise ValueError(
                'The mode must be a following value : '
                'MultNameManager.Integer or MultNameManager.Alphabetical'
            )
        self.__numbering_mode = mode
        self.clearResult()

    def setStartNumber(self, number):
        r"""
            インクリメントの際の開始番号を指定する。
            
            Args:
                number (int):
        """
        self.__startnumber = int(number)
        self.clearResult()

    def startNumber(self):
        r"""
            インクリメントの際の開始番号を返す。
            
            Returns:
                int:
        """
        return self.__startnumber

    def setStartCharacter(self, char):
        r"""
            アルファベットによるインクリメントの開始文字を指定する。
            
            Args:
                char (str):
        """
        self.__startchar = char
        self.clearResult()

    def startCharacter(self):
        r"""
            アルファベットによるインクリメントの開始文字を返す。
            
            Returns:
                str:
        """
        return self.__startchar

    def setPadding(self, value):
        r"""
            インクリメントの際の桁数を指定する。
            
            Args:
                value (int):
        """
        self.__padding = int(value)
        self.clearResult()

    def setStep(self, value):
        r"""
            インクリメントの際のステップ数を指定する。
            
            Args:
                value (int):
        """
        self.__step = int(value)
        self.clearResult()

    def useRegularExpression(self, state):
        r"""
            文字列置換に正規表現を使用するかどうかを指定する。
            
            Args:
                state (bool):
        """
        self.__use_re = bool(state)

    def setSearchingText(self, text):
        r"""
            置換される捜索対象文字列を設定する。
            useRegularExpression:がFalseの場合、文字列に"/"を入れることにより
            複数の単語をまとめて置換可能。
            
            Args:
                text (str):
        """
        self.__searching_texts = text
        self.clearResult()

    def searchingText(self):
        r"""
            置換される操作対象文字列を返す。
            
            Returns:
                str:
        """
        return self.__searching_texts

    def setReplacingText(self, text):
        r"""
            置換する文字列を設定する。
            useRegularExpression:がFalseの場合、文字列に"/"を入れること
            により複数の単語をまとめて置換可能。
            
            Args:
                text (str):
        """
        self.__replacing_texts = text
        self.clearResult()

    def replacingText(self):
        r"""
            置換する文字列を返す。
            
            Returns:
                str:
        """
        return self.__replacing_texts

    def setPrefix(self, prefix):
        r"""
            プレフィックスを設定する。
            
            Args:
                prefix (str):
        """
        self.__prefix = prefix
        self.clearResult()

    def setSuffix(self, suffix):
        r"""
            サフィックスを設定する。
            
            Args:
                suffix (str):
        """
        self.__suffix = suffix
        self.clearResult()

    def renamedList(self):
        r"""
            リネーム処理後の名前をリストとしてキャッシュし返す。
            
            Returns:
                list:
        """
        result = [] 
        basename = ''
        number = 0
        is_pre_suffix = self.__prefix or self.__suffix
        
        if self.__renamed_re:
            renamed_reobj = re.compile(self.__renamed_re)
            renamed_substring = self.__renamed_substring
        else:
            renamed_reobj = None
            renamed_substring = ''

        if self.__use_basename:
            # ベースネームを使用する場合の処理。-------------------------------
            basename = self.__basename
            if self.__numbering_mode == self.Integer:
                number = numericalChar.ZInt(self.startNumber())
            else:
                number = numericalChar.Alphabet(self.startCharacter())
            # -----------------------------------------------------------------
    
        # 置換制御の設定。-----------------------------------------------------
        re_obj = None
        if self.__use_re:
            try:
                re_obj = re.compile(self.__searching_texts)
            except Exception as e:
                print(
                    '%s RE Warning : % s' % (
                        self.__class__.__name__, e.args[0]
                    )
                )
            rep_text = self.__replacing_texts
        else:
            searching_texts = self.__searching_texts.split()
            replaces = self.__replacing_texts.split()
            s_num = len(searching_texts)
            r_num = len(replaces)
            if s_num > r_num:
                replaces.extend(['' for x in range(s_num - r_num)])
        # ---------------------------------------------------------------------

        for name in self.__namelist:
            # ベースネームの設定。
            if renamed_reobj:
                try:
                    if renamed_substring:
                        renamed_name = renamed_reobj.sub(
                            renamed_substring, name
                        )
                    else:
                        r = renamed_reobj.search(name)
                        renamed_name = r.group(0) if r else name
                except:
                    renamed_name = name
                    sub_obj = None
                else:
                    if renamed_substring:
                        compiled_name = lib.convNonreText(renamed_name)
                        sub_obj = re.compile(compiled_name)
                    else:
                        sub_obj = None
                        
            else:
                renamed_name   = name
                sub_obj = None

            if basename:
                newname = '%s%s' % (basename, number.zfill(self.__padding))
            else:
                newname = renamed_name  
            # テキスト置換処理。
            if self.__searching_texts:
                if self.__use_re:
                    if re_obj:
                        newname = re_obj.sub(rep_text, newname)
                else:
                    for s, r in zip(searching_texts, replaces):
                        newname = newname.replace(s, r, 1)

            if is_pre_suffix:
                newname = ''.join((self.__prefix, newname, self.__suffix))

            if sub_obj:
                newname = sub_obj.sub(newname, name)

            result.append(newname)
            number += self.__step

        self.__result = result
        return result

    def result(self):
        r"""
            名前変更後の結果を返す。
            キャッシュを取っているので、設定に変更がなければキャッシュを返す。
            
            Returns:
                list:
        """
        if self.__result:
            return self.__result
        else:
            return self.renamedList()


def multRename(srcNodes, newNames):
    r"""
        srcNodesをnewNamesにリネームする。
        srcNodesとnewNamesの頭から順番に処理し、対となる名前でリネームする。
        
        Args:
            srcNodes (list):リネームするノード名のリスト
            newNames (list):新しい名前のリスト
            
        Returns:
            list:
    """
    temp = []
    for src, newname in zip(node.toObjects(srcNodes), newNames):
        if not src:
            continue
        src.rename('__NU_TEMPORARY_NAME__#')
        temp.append([src, newname])
    result = []
    for tempname, newname in temp:
        result.append(tempname.rename(newname)())
    return result


def renameOppositeSide(targets=None):
    r"""
        targetsを特定ルールに従って反対側の名前にリネームする
        
        Args:
            targets (list):対象ノードのリスト
            
        Returns:
            list:
    """
    targets = node.selected(targets)
    renamer = OppositeSideRenamer()
    selected, newnames = [], []

    for s in targets:
        renamer.setNode(s())
        new_name = renamer.oppositeName()
        if not new_name:
            continue
        selected.append(s)
        newnames.append(new_name)
    return multRename(selected, newnames)


def renameByMaterial(
    basename, suffix, patterns, targets=None, useRegularExpression=True
):
    r"""
        任意のオブジェクトにアサインされているマテリアル名を、任意の
        アサインパターン辞書patternsから検索し、該当するマテリアル名に対応する
        文字列と、引数basename、suffixを使用した名前を用いてリネームする。
        リネームに使用される名前は
        basename + マテリアルをキーとしたpatterns内の値 + suffix
        となる。
        なお、アサインされているマテリアル名がpatternsに存在しない場合は、その
        オブジェクトの処理はスキップする。
        
        Args:
            basename (str):リネームする際のベースとなる名前
            suffix (str):リネームする際のサフィックスとなる文字列
            patterns (dict):マテリアルを照会する辞書
            targets (list):操作対象オブジェクトのリスト
            useRegularExpression (bool):patternsのキーを正規表現として使用する
    """
    if not isinstance(patterns, dict):
        raise AttributeError('The first option "patterns" must be type "dict".')
    if useRegularExpression:
        patterns = {re.compile(x): y for x, y in patterns.items()}

    from . import surfaceMaterialUtil
    targets = node.selected(targets)
    src_nodes, new_names = [], []
    for tgt in targets:
        mat_data = surfaceMaterialUtil.listMaterials(tgt)
        if not mat_data:
            continue
        new_name = None
        for mat in mat_data[0]:
            for ptn, ptn_name in patterns.items():
                if not (
                    ptn.search(mat()) if useRegularExpression else mat() == ptn
                ):
                    continue
                new_name = basename + ptn_name + suffix
                break
            if new_name:
                break
        if not new_name:
            print(
                (
                    '[WARNING] No material that matches in the given pattern '
                    'found for "{}".'
                ).format(tgt)
            )
            continue
        src_nodes.append(tgt())
        new_names.append(new_name)
    if src_nodes:
        multRename(src_nodes, new_names)


def separateNameByDefault(name):
    r"""
        名前を任意の処理によって分割し、ベース名と位置を表す文字列に変換する。
        
        Args:
            name (str):
            
        Returns:
            tuple(str, str):分割された結果
    """
    from .. import func
    ptn = re.compile('Geo$')
    name = name.rsplit('|', 1)[-1]
    n = func.Name(name)
    new_name = n.name()
    if ptn.search(new_name):
        new_name = ptn.sub('', new_name)
    pos = '_geo_' + n.position() if n.position() else '_geo'
    return (new_name, pos)
    

def renameFromParentNameAndMaterial(
    patterns, nameAlgorithm=separateNameByDefault,
    targets=None, useRegularExpression=True
):
    r"""
        親ノードの名前をnameAlgorithmによって任意のパターンに分解し、それと
        アサインされているマテリアル名とのパターンから自動的にリネームする。
        
        Args:
            patterns (dict):マテリアルを照会する辞書
            nameAlgorithm (function):
            targets (list):操作対象オブジェクトのリスト
            useRegularExpression (bool):patternsのキーを正規表現として使用する
    """
    targets = node.selected(targets)
    parentlist = {}
    for tgt in targets:
        parent = tgt.parent()
        if not parent:
            continue
        parentlist.setdefault(parent(), []).append(tgt)
    if not parentlist:
        return
    for parent, targets in parentlist.items():
        basename, suffix = nameAlgorithm(parent)
        renameByMaterial(
            basename, suffix, patterns, targets, useRegularExpression
        )


def copyNames(targets=None, writeTo=None):
    r"""
        targetsの名前をwriteToで指定されたメソッドに書き出す。
        writeTo:は指定しなければデフォルトではクリップボードに書き出される。
        
        Args:
            targets (list):名前を取得する対象ノードのリスト
            writeTo (function):書き出し先の関数
            
        Returns:
            str:書き出される名前のリストを表す文字列
    """
    if not writeTo:
        from gris3.uilib import QtWidgets
        writeTo = QtWidgets.QApplication.clipboard().setText
    targets = targets or selectedNodes()
    namelist = ', '.join(["'%s'" % x for x in targets])
    if namelist and writeTo:
        writeTo(namelist)
    return namelist


def pasteName(
    targets=None, readFrom=None, namespaceAs=1,
    searchStr='', replaceStr=''
):
    r"""
        readFromの名前の一覧をtargetsに適応する。
        namespaceAsオプションは、コピーされた名前にネームスペースがついていた
        場合の対処方法を指定する。
        0 : 何もしない
        1 : ネームスペースを削除する。
        2 : ネームスペース区切り文字の:を_に変更する
        
        Args:
            targets (list):リネームされる対象ノードのリスト
            readFrom (str):名前のリスト（copyNamesの書式に準ずる）
            namespaceAs (int):ネームスペースへの操作方法
            searchStr (str):置換対象となる検索文字列
            replaceStr (str):置換文字列
    """
    targets = targets or selectedNodes()
    if not targets:
        return
    if not readFrom:
        from gris3.uilib import QtWidgets
        readFrom = QtWidgets.QApplication.clipboard().text()
    if not readFrom:
        return
    ptn = re.compile("'([a-zA-Z_\|][a-zA-Z\d_\|]*)'")
    elements = [x.strip() for x in readFrom.split(',')]
    namelist = []
    for elm in elements:
        if ':' in elm:
            if namespaceAs == 1:
                elm = "'" + elm.rsplit(':', 1)[-1]
            elif namespaceAs == 2:
                elm = elm.replace(':', '_')
        if searchStr:
            elm = elm.replace(searchStr, replaceStr)
        m = ptn.search(elm)
        if not m:
            return
        namelist.append(m.group(1).rsplit('|')[-1])
    multRename(targets, namelist)


class AutoRenamer(object):
    r"""
        階層構造に応じた連番リネームを自動で行う。
    """
    SuffixFormat = '_{objType}_{position}'

    def __init__(self):
        super(AutoRenamer, self).__init__()
        self.__basename = 'baseName'
        self.__startchar = 'A'
        self.__object_type = 'jnt'
        self.__side = 'C'
        self.__padding = 0

    def setBaseName(self, name):
        r"""
            ノードを表すベースの名前を設定する。
            
            Args:
                name (str):
        """
        self.__basename = name

    def baseName(self):
        r"""
            ノードを表すベースの名前を返す。
            
            Returns:
                str:
        """
        return self.__basename

    def setStartChar(self, char):
        r"""
            連番の開始番号となる文字（大文字）を設定する
            
            Args:
                char (str):
        """
        self.__startchar = char

    def startChar(self):
        r"""
            連番の開始番号となる文字（大文字）を返す
            
            Returns:
                str:
        """
        return self.__startchar
    
    def setPadding(self, padding):
        r"""
            連番の桁数を設定する。
            0以下の場合は自動設定される。
            
            Args:
                padding (int):
        """
        self.__padding = padding

    def padding(self):
        r"""
            連番の桁数を返す。
            0以下の場合は自動設定される。
            
            Returns:
                int:
        """
        return self.__padding

    def setObjectType(self, typeChar):
        r"""
            オブジェクトの種類を表す文字列を設定する。
            
            Args:
                typeChar (str):
        """
        self.__object_type = typeChar

    def objectType(self):
        r"""
            オブジェクトの種類を表す文字列を返す。
            
            Returns:
                str:
        """
        return self.__object_type

    def setSide(self, side):
        r"""
            オブジェクトの位置を表す文字列を設定する。
            
            Args:
                side (str):
        """
        self.__side = side

    def side(self):
        r"""
            オブジェクトの位置を表す文字列を返す。
            
            Returns:
                str:
        """
        return self.__side

    def createPrefix(self):
        return ''

    def createSuffix(self):
        return self.SuffixFormat.format(
            objType=self.objectType(), position=self.side()
        )

    def modifyNameChain(
        self, targets, renamedList, suffixChar, namePattern
    ):
        r"""
            リネーム前に新しい名前の最終調整を行うためのメソッド。
            調整した結果を反映させる場合はrenamedListの中身を直接編集する。
            
            Args:
                targets (list):リネーム対象オブジェクトのリスト。
                renamedList (list):リネーム後の名前のリスト。
                suffixChar (str):チェーン全体の通し番号のサフィックス文字列
                namePattern (re.Pattern):編集用正規表現オブジェクト
        """
        if len(targets) < 2:
            return
        renamedList[-1] = namePattern.sub(
            str(suffixChar) + 'End', renamedList[-1]
        )

    def rename(self):
        r"""
            リネーム実行プロセス。
        """
        def get_padding(namelist):
            r"""
                Args:
                    namelist (list):
            """
            pad_char = numericalChar.digitToAlpha(len(namelist))
            return len(pad_char)

        targetlist = util.analyzeHierarchy()
        start_char = numericalChar.Alphabet(
            self.startChar()
        )
        basename = self.baseName()
        pad = self.padding()
        if pad <= 0:
            pad = get_padding(targetlist)

        # リネーマーの設定。
        manager = MultNameManager()
        manager.setPrefix(self.createPrefix())
        manager.setSuffix(self.createSuffix())
        manager.useBaseName(True)
        manager.setNumberingAs(manager.Alphabetical)
        manager.setStartCharacter('A')

        for targets in targetlist:
            ptn = re.compile(start_char+'[A-Z]+$')
            manager.setBaseName(basename + start_char.zfill(pad))
            manager.setNameList(targets)
            manager.setPadding(get_padding(targets))
            renamed_list = manager.result()

            self.modifyNameChain(targets, renamed_list, start_char, ptn)
            multRename(targets, renamed_list)
            start_char += 1


