#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    チェック機能のフレームワークを提供するモジュール。
    チェック自体はmodelCheckerなどで行う。
    
    Dates:
        date:2024/05/15 10:46 Eske Yoshinob[eske3g@gmail.com]
        update:2024/06/03 15:29 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2024 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import re
from .. import node


class CheckedResult(object):
    r"""
        チェックのエラー結果を格納するクラス。
        このクラスではエラー内容、エラーレベル、修正ツールへ振り分けするための
        IDなどの情報を持つ。
    """
    Error, Warning = range(2)
    def __init__(self, message='', status=0, processId=-1, **options):
        r"""
            Args:
                message (str):
                status (int):
                processId (int):
        """
        self.status = status
        self.message = message
        self.processId = processId
        for key, val in options.items():
            setattr(self, key, val)


class AbstractChecker(object):
    r"""
        すべてのチェッカーの基底クラス。
    """
    def __init__(self):
        self.__category = ''

    def  setCategory(self, category):
        r"""
            このクラスが取り扱う対象カテゴリ名を設定する
            
            Args:
                category (str):
        """
        self.__category = category

    def category(self):
        r"""
            このクラスが取り扱う対象カテゴリ名を返す。
            
            Returns:
                str:
        """
        return self.__category

    def check(self):
        r"""
            チェックを行うエントリメソッド。
            各種ツールはこのメソッドを呼び、チェック結果を受け取る。

            Returns:
                any:
        """
        return []


class AbstractAssetChecker(AbstractChecker):
    r"""
        アセットチェッカー（ノードベース）の規定クラス。
    """
    def __init__(self):
        super(AbstractAssetChecker, self).__init__()
        self.__targets = []        

    def setTargets(self,  targetlist):
        r"""
            操作対象となるオブジェクトのリストを設定する。
            
            Args:
                targetlist (list):
        """
        self.__targets = targetlist

    def targets(self, convertObject=True):
        r"""
            設定されている操作対象となるオブジェクトのリストを返す。
            
            Args:
                convertObject (bool): node.AbstractNode形式に変換するかどうか
                
            Returns:
                list:
        """
        if convertObject:
            return node.toObjects(self.__targets)
        else:
            return self.__targets[:]
    
    def checkObject(self, targetObject):
        r"""
            対象となるオブジェクトがルールに適合しているかどうかを確認する。
            適合していない場合はエラー内容(CheckedResult)のリストを返す。
            問題ない場合は空のリストを返す。
            
            Args:
                targetObject (gris3.node.AbstractNode):
                
            Returns:
                list(CheckedResult):
        """
        return []

    def search(self, target):
        r"""
            任意のターゲットと関連ノードの名前ルールが適合しているか走査する。
            名前ルールに適合していない場合は、そのノード名と理由を持つtupleの
            リストを返す。
            
            Args:
                target (gris3.node.AbstractNode):
                
            Returns:
                list:不適合ノード名(gris3.node.AbstractNode), 不適合理由(list)
        """
        checked = self.checkObject(target)
        if checked:
            return [(target, checked)]
        return []

    def check(self):
        r"""
            設定されたターゲットオブジェクトに対してチェックを行い、結果を返す。
            戻り値は
                チェック対象オブジェクト名、[CheckResult(エラー内容)...]
            となる。

            Returns:
                list:
        """
        targets = self.targets()
        if not targets:
            raise RuntimeError(
                '[{}] No targets to check was not specified.'.format(
                    self.category()
                )
            )
        result = []
        for target in targets:
            result.extend(self.search(target))
        return result


class REBasedNameChecker(AbstractAssetChecker):
    r"""
        名前ベースのチェッカーの基底クラス。
        メンバー変数NamePatternに適合するかどうかで判断を行う。
        NamePatternには任意のコンパイル済み正規表現オブジェクトを格納する。
    """
    NamePattern = re.compile('.*')
    def checkObject(self, targetObject):
        r"""
            Args:
                targetObject (gris3.node.AbstractNode):
                
            Returns:
                list:エラー内容(CheckedResult)のリスト
        """
        if self.NamePattern.search(targetObject()):
            return []
        return [CheckedResult('Invalid name.')]


class AbstractDagChecker(AbstractAssetChecker):
    r"""
        dagを対象とするチェッカーの基底クラス。
        設定されたターゲットに対して、一番下の階層まで再帰的にチェックを行う。
    """
    def search(self, target):
        r"""
            Args:
                target (gris3.node.AbstractNode):
        """
        result = []
        checked = self.checkObject(target)
        if checked:
            result.append((target, checked))
        for child in target.children():
            result.extend(self.search(child))
        return result


class REBasedDagNameChecker(AbstractDagChecker):
    r"""
        名前ベースのdagを対象とするチェッカーの基底クラス。
        メンバー変数NamePatternに適合するかどうかで判断を行う。
        NamePatternには任意のコンパイル済み正規表現オブジェクトを格納する。
        また、名前がシーン中に重複しているかどうかもチェックする。
    """
    NamePattern = re.compile('.*')
    def checkObject(self, target):
        r"""
            Args:
                target (gris3.node.AbstractNode):
                
            Returns:
                list:
        """
        name = target()
        checked = []
        if '|' in name:
            checked.append(CheckedResult('More than 2 same name objects.'))

        if not self.NamePattern.search(target.shortName()):
            checked.append(CheckedResult('Invalid name'))
        return checked


class GroupMemberChecker(REBasedDagNameChecker):
    r"""
        階層ベースで一番下階層までチェックを行う。
        setTargetで指定したグループの下階層のオブジェクトが対象となる。
        （setTargetしたオブジェクトは走査対象にはならない）
    """
    def originalTargets(self, convertObject=False):
        r"""
            setTargetした際のオブジェクト名を返す。

            Args:
                convertObject (bool):
            
            Returns:
                list:
        """
        return super(GroupMemberChecker, self).targets(
            convertObject=convertObject
        )
        
    def targets(self):
        r"""
            setTargetしたオブジェクトのすべての子を返す。
            setTargetしたオブジェクト自身は含まれない点に注意。

            Returns:
                list:
        """
        parents = self.originalTargets(convertObject=False)
        children = []
        for p in parents:
            obj = node.asObject(p)
            if not obj:
                raise RuntimeError(
                    'Target objects "{}" was not found.'.format(p)
                )
            children.extend(obj.children())
        return children


class DataBasedHierarchyChecker(AbstractAssetChecker):
    r"""
        データ（dict型など）に基づいてチェックを行う機能を提供するクラス。
    """
    def __init__(self):
        super(DataBasedHierarchyChecker, self).__init__()
        self.__priority_level = 0
    
    def setPriorityLevel(self, level):
        r"""
            ノードを検出する際にフィルタとなるpriorityを設定する。
            このpriorityよりも上回る数値を設定されたノードは走査しなくなる。
            
            Args:
                level (int):
        """
        self.__priority_level = int(level)

    def priorityLevel(self):
        r"""
            ノードを検出する際フィルタとなる、設定されたpriorityを返す。
            
            Returns:
                int:
        """
        return self.__priority_level

    def targets(self, isCopy=True):
        r"""
            Args:
                isCopy (bool):
        """
        targets = super(DataBasedHierarchyChecker, self).targets(False)
        if isCopy:
            import copy
            return copy.deepcopy(targets)
        else:
            return targets

    @staticmethod
    def getHir(targets, priorityFilter=None):
        r"""
            階層データを書き出すための便利関数。
            引数targetsにはgris3.node.TransformかJointを渡す必要がある。
            引数priorityFilterには、走査中のオブジェクトのpriorityをいくつに
            設定するかのフィルタ用関数を設定する。
            この関数の書式は
                def priorityFilterFunc(target: node.Transform):
                    return int
            となる。
            現状簡易版のため探査に穴がある可能性あり。

            Args:
                targets (list):走査対象ノードのリスト
                priorityFilter (function):priority値を設定する際のフィルタ関数
        """
        def _g(targets, data, priorityFilter):
            r"""
                Args:
                    targets (list):走査対象ノードのリスト
                    data (dict):結果を格納する辞書オブジェクト
                    priorityFilter (function):priority値のフィルタ関数
            """
            f = priorityFilter if priorityFilter else lambda x : 0
            for tgt in targets:
                key = tgt()
                dc = {'priority': f(tgt)}
                data[key] = dc
                children = tgt.children(type='transform')
                if not children:
                    continue
                dc['children'] = {}
                _g(children, dc['children'], priorityFilter)
        data = {}
        _g(targets, data, priorityFilter)
        return data
    
    def checkObject(self, name, data, parent):
        r"""
            Args:
                name (str):
                data (dict):
                parent (str):
        """
        if data.get('priority') > self.priorityLevel():
            return []
        n = node.asObject(name)
        result = []
        if not n:
            return (name, [CheckedResult('No object was found.')])
        if parent:
            if n.parent() != parent:
                result.append(
                    CheckedResult(
                        'Invalid parent. The parent node must be "{}".'.format(
                            parent
                        )
                    )
                )
        return (n, result) if result else []

    def search(self, target, parent):
        r"""
            Args:
                target (node.DagNode):
                parent (node.DagNode):
        """
        result = []
        for name, sub_data in target.items():
            checked = self.checkObject(name, sub_data, parent)
            if checked:
                result.append(checked)
            children = sub_data.get('children')
            if not children:
                continue
            result.extend(self.search(children, name))
        return result

    def check(self):
        checked_data = self.targets()
        result = []
        for data_dict in checked_data:
            result.extend(self.search(data_dict, None))
        return result
