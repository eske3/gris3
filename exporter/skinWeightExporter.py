#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    スキンウェイトの書き出し、読み込み機能を提供するモジュール。
    
    Dates:
        date:2017/01/21 23:55[Eske](eske3g@gmail.com)
        update:2025/08/05 11:24 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
import re
import datetime

from maya import mel
from gris3 import mayaCmds as cmds
from gris3.exporter import core

Version = '1.0.0'

# /////////////////////////////////////////////////////////////////////////////
# The main classes.                                                          //
# /////////////////////////////////////////////////////////////////////////////
class Exporter(core.AbstractExporter):
    r"""
        スキンウェイトの書き出し機能を提供するクラス。
        書き出されるウェイトファイルはmelファイルとなる。
    """
    Extensions = ['mel']
    NodeType = ['mesh', 'nurbsSurface', 'nurbsCurve', 'lattice']
    def __init__(self):
        super(Exporter, self).__init__()
        self.__shape = ''
        self.__isRemapIndex = True

    def setIsRemapIndex(self, state):
        r"""
            インデックス番号のリマップ処理を行うかどうかセットする。
            デフォルトはTrue。
            
            Args:
                state (bool):
        """
        self.__isRemapIndex = bool(state)

    def isRemapIndex(self):
        r"""
            インデックス番号のりマップ処理を行うかどうかを返す。
            
            Returns:
                bool:
        """
        return self.__isRemapIndex

    def checkExtension(self, path):
        r"""
            拡張子のチェックを行う。
            チェック後、該当拡張子がない場合は付与したものを返す。
            
            Args:
                path (str):チェックするファイルパス。
                
            Returns:
                str:
        """
        path, ext = os.path.splitext(path)
        if not ext in self.Extensions:
            path += '.' + self.Extensions[0]
        return path

    def setShape(self, node):
        r"""
            ウェイトを書き出すシェイプ名をセットする。
            
            Args:
                node (str):
        """
        if not cmds.objExists(node):
            raise RuntimeError(
                "The specified node doesn't exists : %s" % node
            )
        node_type = cmds.nodeType(node)
        if node_type == 'transform':
            shapes = cmds.listRelatives(node, shapes=True, type=self.NodeType)
            if not shapes:
                raise RuntimeError(
                    'Invalid shape type : %s' % node
                )
            self.__shape = shapes[0]
        else:
            if not node_type in self.NodeType:
                raise RuntimeError(
                    'Invalid shape type : %s' % node
                )
            self.__shape = node

    def shape(self):
        r"""
            ウェイトを書き出すシェイプ名を返す。
            
            Returns:
                str:
        """
        return self.__shape

    def export(self):
        r"""
            ウェイトの書き出しを行う。
        """
        methodTypes = ['Classic Lnear', 'Dual Quaternion', 'Weight Blended']
        modulename = __name__.split('.')[-1]
        current_time = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')
        mobj = re.compile('\[\d+\]$')
        
        filepath = self.exportPath()
        shape = self.shape()

        # Find related skinCluster node from shape.
        skinCluster = mel.eval('findRelatedSkinCluster("%s");' % shape)
        if not skinCluster:
            raise RuntimeError(
                'No skinCluster node was found from "%s"' % shape
            )

        # Collect attribute about the skin cluster.----------------------------
        mMaxInf = cmds.getAttr('%s.maintainMaxInfluences' % skinCluster)
        maxInf = cmds.getAttr('%s.maxInfluences' % skinCluster)
        methodType = cmds.getAttr('%s.skinningMethod' % skinCluster)
        distrib = cmds.getAttr('%s.weightDistribution' % skinCluster)
        # ---------------------------------------------------------------------

        # Collects information about influences.-------------------------------
        influences_with_plugs = cmds.listConnections(
            '%s.matrix' % skinCluster, s=True, d=False, c=True, p=True
        )
        influences = []
        index_map = {}
        count = 0
        for i in range(0, len(influences_with_plugs), 2):
            influences.append(influences_with_plugs[i+1].split('.')[0])
            index = mobj.search(influences_with_plugs[i]).group(0)
            index_map[index] = count
            count += 1
        numOfInf = len(influences)
        # ---------------------------------------------------------------------

        # lists weight attr of the skin cluster.
        weightAttr = [ x for x in
            cmds.listAttr('%s.wl' % skinCluster, m=True)
            if x.find('.') > -1
        ]

        # Output informations.
        print('# Skin Weights Exporter.'.ljust(80, '='))
        print('  Export to : %s' % filepath)
        print('    Shape                   : %s' % shape)
        print('    Skin Cluster            : %s' % skinCluster)
        print('    Maintain Max Incluences : %s' % mMaxInf)
        print('    Max Incluences          : %s' % maxInf)
        print('    Skinning Method         : %s' % methodTypes[methodType])
        print('    Weight Distribution     : %s' % distrib)
        print('=' * 80)

        # Write weights to the sepcified file.=================================
        with open(filepath, 'w') as f:
            # Write File information.------------------------------------------
            f.write('// %s %s\n' % (modulename, Version))
            f.write('// Aother               : %s\n' % os.environ['USER'])
            f.write('// Creation Date        : %s\n' % current_time)

            f.write('// '.ljust(80, '-') + '\n')

            f.write('// Skinned Shape        : %s\n' % shape)
            f.write('// Skin Cluster         : %s\n' % skinCluster)
            f.write('// Skinning Method      : %s\n' % methodType)
            f.write('// Maintain Max Inf     : %s\n' % mMaxInf)
            f.write('// Max Influences       : %s\n' % maxInf)
            f.write('// Number of Influences : %s\n' % numOfInf)
            f.write('// Weight Distribution  : %s\n' % distrib)
            f.write('// Influence order      : '
                '{%s}\n' % ', '.join(['"%s"' % x for x in influences])
            )
            f.write('{\n')
            # -----------------------------------------------------------------

            # Adds skin cluster information.-----------------------------------
            f.write('    string $shape = "%s";\n' % shape)
            f.write(
                '    string $skinCluster = findRelatedSkinCluster($shape);\n'
            )
            f.write(
                '    string $attr[] = `listAttr -m -sn -st "w" '
                '($skinCluster + ".wl")`;\n'
            )
            f.write(
                '    for ($a in $attr){\n'
                '        setAttr ($skinCluster + "." + $a) 0;\n'
                '    }\n'
            )
            f.write('\n')
            # -----------------------------------------------------------------
            
            # Get weight and write setAttr script to the output file.----------
            for attr in weightAttr:
                value = cmds.getAttr('%s.%s' % (skinCluster, attr))
                if not value:
                    continue
                if self.isRemapIndex():
                    index = mobj.search(attr).group(0)
                    if not index in index_map:
                        continue
                    new_index = '[%s]' % index_map[index]
                    attr = mobj.sub(new_index, attr)
                f.write(
                    '    setAttr ($skinCluster + ".%s") %s;\n' % (attr, value)
                )
            # -----------------------------------------------------------------
            f.write('}\n')
        # =====================================================================


class Restorer(object):
    r"""
        書き出されたmelのウェイトファイルを復元するクラス。
    """
    def __init__(self, filepath=''):
        r"""
            Args:
                filepath (str):入力melファイル
        """
        self.setFile(filepath)
        self.__shape = ''
        self.__skinClusterName = ''
        self.__influence_replacer = None
        self.__param_cache = {}

    def setFile(self, filepath):
        r"""
            入力ファイルパスをセットする。
            
            Args:
                filepath (str):
        """
        self.__file = filepath
        self.__param_cache = {}

    def file(self):
        r"""
            セットされた入力ファイルパスを返す。
            
            Returns:
                str:
        """
        return self.__file

    def setShape(self, shape):
        r"""
            ターゲットとなるシェイプをセットする。
            
            Args:
                shape (str):
                
            Returns:
                None:
        """
        self.__shape = shape

    def shape(self):
        r"""
            ターゲットとなるシェイプを返す。
            
            Returns:
                None:
        """
        return self.__shape

    def setSkinClusterName(self, name):
        r"""
            復元する時につけるskinClusterの名前をセットする。
            
            Args:
                name (str):
                
            Returns:
                None:
        """
        self.__skinClusterName = name

    def skinClusterName(self):
        r"""
            復元する時につけるskinClusterの名前を返す。
            
            Returns:
                str:
        """
        return self.__skinClusterName

    def setInfluenceReplacer(self, function=None):
        r"""
            インフルエンスを置き換えるための関数を設定する。
            この関数を指定すると、バインドする際にウェイトファイルの
            InfluenceOrderで指定されているバインドジョイント名を任意のルールで
            変更することができる。
            この関数はインフルエンス名のリストを受け取り、置換後のリストを
            返す関数である必要がある。
            
            Args:
                function (function):関数。
        """
        self.__influence_replacer = function

    def analyzeInfo(self, force=False):
        r"""
            与えられたウェイトファイルを解析し、必用な情報を取得する。
            fouceがFalseで、すでにキャッシュがある場合は何もしない。
            
            Args:
                force (bool):キャッシュを破棄して強制的に更新するかどうか
                
            Returns:
                dict:解析結果を持つ辞書オブジェクト
        """
        if self.__param_cache and not force:
            return self.__param_cache
        self.__param_cache = {}
        file = self.file()
        if not os.path.isfile(file):
            raise RuntimeError(
                'The specified file was not found : %s' % file
            )

        # Get a values of the skin cluster's attributes from the file header.--
        with open(file, 'r') as f:
            textline = ''
            parameter_read_mode = False
            while(1):
                textline = f.readline()
                if not textline:
                    break

                is_comment = textline.startswith('//')
                if parameter_read_mode and not is_comment:
                    break

                if textline.startswith('//'):
                    parameter_read_mode = True

                param = textline.strip().split(':')
                if len(param) != 2:
                    continue
                self.__param_cache[param[0].strip()[3:]] = param[1].strip()
        # ---------------------------------------------------------------------
        influences = [
            x[1:-1]
            for x in self.__param_cache.get('Influence order')[1:-1].split(
                ', '
            )
        ]
        self.__param_cache['Influence order'] = influences
        return self.__param_cache

    def restore(self):
        r"""
            復元を開始する。
        """
        boolFromStr = {
            'True':True,   '1':True,  'on':True,
            'False':False, '0':False, 'off':False,
        }
        
        parameters = self.analyzeInfo()
        file = self.file()

        # Gathering a information for the binding.-----------------------------
        skinningMethod = int(parameters.get('Skinning Method', 0))
        maintainMaxInfluences = boolFromStr[
            parameters.get('Maintain Max Inf', 'False')
        ]
        maxInfluences = int(parameters.get('Max Influences', '2'))
        weight_distrib = int(parameters.get('Weight Distribution', '1'))
        influences = parameters['Influence order']
        if self.__influence_replacer:
            influences = self.__influence_replacer(influences)
        if cmds.objExists(self.shape()):
            shape = self.shape()
        else:
            shape = parameters.get('Skinned Shape', '')
        is_matched_name = (shape == parameters.get('Skinned Shape'))
        # ---------------------------------------------------------------------

        # Bind skin.-----------------------------------------------------------
        keywords = {
            'tsb':True, 'omi':True, 'sm':skinningMethod,
            'omi':maintainMaxInfluences, 'mi':0,
            'wd':weight_distrib,
        }
        if self.skinClusterName():
            keywords['n'] = self.skinClusterName()
        else:
            keywords['n'] = (
                os.path.basename(file).split('_')[0].split('.')[0] +
                '_sc'
            )

        influences.append(shape)
        skinCluster = cmds.skinCluster(influences, **keywords)
        cmds.setAttr(skinCluster[0]+'.maxInfluences', maxInfluences)
        # ---------------------------------------------------------------------
        
        # Apply to weight.-----------------------------------------------------
        if is_matched_name:
            mel.eval('source "%s";' % file.replace('\\', '/'))
            print('Matched : %s' % file)
            return

        ptn = re.compile('(\s*string\s+\$shape\s*=\s*")(.*)("\s*;\s*$)')
        with open(file, 'r') as f:
            buffer = []
            while(True):
                text = f.readline()
                if not text:
                    break
                if ptn.match(text):
                    text = ptn.sub(r'\1'+shape+r'\3', text)
                buffer.append(text)
        command = ''.join(buffer)
        mel.eval(''.join(buffer))
        # ---------------------------------------------------------------------

# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////


# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////
class BasicTemporaryWeight(object):
    r"""
        一時的にウェイトを書き出し、復元する機能を提供するクラス。
    """
    def __init__(self):
        self.__exporter = Exporter()
        self.__restorer = Restorer()
        self.__nodename = ''
        import tempfile
        self.__tempfile = os.path.join(
            tempfile.gettempdir(), '__gris_temporary_skin_weight__'
        )

    def tempFile(self):
        r"""
            一時保存ファイルのパス（拡張子なし）を返す。
            
            Returns:
                str:
        """
        return self.__tempfile

    def tempFilePath(self):
        r"""
            一時保存ファイルのパスを返す。
            
            Returns:
                str:
        """
        return '{}{}.mel'.format(self.tempFile(), self.__nodename)

    def setNode(self, nodeName):
        r"""
            ウェイトを書き出すノード名をセットする。
            
            Args:
                nodeName (str):
        """
        self.__nodename = nodeName

    def node(self):
        r"""
            ウェイトを書き出すノード名を返す。
            
            Returns:
                str:
        """
        return self.__nodename

    def save(self):
        r"""
            ウェイトを一時的に書き出す。
        """
        n = self.node()
        if not cmds.objExists(n):
            raise RuntimeError('No saved weight node exists.')
        self.__exporter.setShape(n)
        self.__exporter.setExportPath(self.tempFilePath())
        self.__exporter.export()

    def restore(self, removeWeightFile=True):
        r"""
            一時的に書き出したウェイトを復元する。
            
            Args:
                removeWeightFile (bool):ウェイトファイルを破棄するかどうか
        """
        self.__restorer.setFile(self.tempFilePath())
        self.__restorer.setShape(self.__exporter.shape())
        self.__restorer.restore()
        if not removeWeightFile:
            return
        try:
            os.remove(self.tempFilePath())
        except:
            pass


class TemporaryWeight(BasicTemporaryWeight):
    r"""
        選択オブジェクト１つのウェイトを一時的に保存、復元する。
    """
    def save(self):
        r"""
            選択ノード１つのウェイトを一時的に保存する。
        """
        selected = cmds.ls(sl=True)
        if len(selected) != 1:
            raise RuntimeError('The saved object must be only one.')
        self.setNode(selected[0])
        super(TemporaryWeight, self).save()

    def tempFilePath(self):
        r"""
            一時ファイルのパスを返す。この名前は一意。
            
            Returns:
                str:
        """
        return self.tempFile() + '.mel'

    def restore(self):
        r"""
            復元を行う。
        """
        super(TemporaryWeight, self).restore(False)
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////
