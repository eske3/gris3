#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ここに説明文を記入
    
    Dates:
        date:2017/01/21 12:05[Eske](eske3g@gmail.com)
        update:2022/12/07 05:35 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
import re
import datetime
import codecs

from maya import cmds
from gris3.exporter import core

AnimCurveTypes = ('A', 'L', 'T', 'U')
DrivenAnimTypes = ['animCurveU' + x for x in AnimCurveTypes]
DrivenExportedTypes = DrivenAnimTypes[:]
DrivenExportedTypes.extend(['blendWeighted', 'unitConversion'])


class AbstractAnimExporter(core.AbstractExporter):
    r"""
        アニメーション書き出しの基底クラス。
    """

    Extensions = ['ma']
    ExportedTypes = ['animCurveT' + x for x in AnimCurveTypes]
    HeaderTemplate = '''{
    string $namespace = "";
'''
    OutConnectionTemplate = '(":" + $namespace + "%s")'
    FooterTemplate = '}'
    def __init__(self):
        super(AbstractAnimExporter, self).__init__()
        self.initialize()

    def initialize(self):
        r"""
            初期化を行う。
        """
        self.__nodes = []
        self.__temporary = ''
        self.__connection_scripts = []

    def header(self):
        r"""
            ヘッダーの文字列を返す。
            
            Returns:
                str:
        """
        return ''

    def targetNodes(self):
        r"""
            書き出し予定の対象ノードのリストを返す。
            
            Returns:
                list:
        """
        return self.__nodes

    def temporaryFile(self):
        r"""
            書き出し時に一時的に保存するテンポラリファイル名を返す。
            
            Returns:
                str:
        """
        return self.__temporary

    def connectionScripts(self):
        r"""
            接続用のスクリプトを返す。
            
            Returns:
                str:
        """
        return self.__connection_scripts

    def listExportedNodes(self, targetNode):
        r"""
            上書き専用メソッド。
            デフォルトではターゲットに接続されているアニメーションカーブノードの
            リストをかえす。
            
            Args:
                targetNode (str):
                
            Returns:
                dict:
        """
        animCurves = cmds.listConnections(
            targetNode, s=True, d=False, type='animCurve'
        )
        if not animCurves:
            return None
        animCurves = cmds.ls(animCurves, typ=self.ExportedTypes)
        if not animCurves:
            return None

        result = {}
        result['exported'] = animCurves
        result['in'] = animCurves
        result['out'] = animCurves
        return result

    def makeOutputConnection(self, outputNodes):
        r"""
            出力接続用のコマンドリストを生成して返す。
            
            Args:
                outputNodes (list):
                
            Returns:
                list:
        """
        connection_scripts = []
        # Make output connections.---------------------------------------------
        for node in outputNodes:
            con = cmds.listConnections(node, s=False, d=True, c=True, p=True)
            if not con:
                continue
            for i in range(0, len(con), 2):
                target = con[i+1]
                if ':' in target:
                    target = target.rsplit(':',  1)[-1]
                dst_text = self.OutConnectionTemplate % target
                connection_text = '    connectAttr "%s" %s;' % (
                        con[i], dst_text
                    )
                connection_scripts.append(connection_text)
        # ---------------------------------------------------------------------
        return connection_scripts


    def makeInputConnection(self, inputNodes):
        r"""
            入力接続用のコマンドリストを生成して返す。
            
            Args:
                inputNodes (list):
                
            Returns:
                list:
        """
        connection_scripts = []
        # Make input connections.---------------------------------------------
        for node in inputNodes:
            con = cmds.listConnections(node, s=True, d=False, c=True, p=True)
            if not con:
                continue
            for i in range(0, len(con), 2):
                connection_scripts.append(
                    '    connectAttr (":%s") "%s";' % (
                        con[i+1], con[i]
                    )
                )
        # ---------------------------------------------------------------------
        return connection_scripts
        

    def run(self):
        r"""
            実行部分。
        """
        exported = []
        input_nodes = []
        output_nodes = []
        for node in self.targetNodes():
            exported_info = self.listExportedNodes(node)
            if not exported_info:
                continue
            exported.extend(exported_info['exported'])
            input_nodes.extend(exported_info['in'])
            output_nodes.extend(exported_info['out'])

        if not exported:
            return

        # Make script to make connections between target node and anim curve.==
        connection_scripts = [self.HeaderTemplate]
        connection_scripts.extend(self.makeInputConnection(input_nodes))
        connection_scripts.extend(self.makeOutputConnection(output_nodes))

        connection_scripts.append(self.FooterTemplate)

        tmpfile = os.path.join(
            os.environ['TEMP'],
            datetime.datetime.now().strftime(
                '__ANIMEXPTMP_%Y%m%d%H%M%S__.ma'
            )
        )
        cmds.select(exported, r=True)
        cmds.file(
            tmpfile, es=True, f=True, type='mayaAscii',
            ch=False, chn=False, con=False, exp=False, sh=False
        )
        # =====================================================================

        self.__temporary = tmpfile
        self.__connection_scripts = connection_scripts


    def copyFromMayaFile(
            self, temporaryFile, tempMayaFileName, targetMayaFileName,
            fileObject
        ):
        r"""
            Mayaファイルからテンポラリにコピーする。
            
            Args:
                temporaryFile (str):
                tempMayaFileName (str):
                targetMayaFileName (str):
                fileObject (file):
        """
        with open(temporaryFile, 'r') as tmpf:
            while(1):
                text = tmpf.readline()
                if not text:
                    break
                if text.startswith('//Name: %s' % tempMayaFileName):
                    text = '//Name: %s\n' % targetMayaFileName
                elif text.startswith('// End of %s' % tempMayaFileName):
                    text = '// End of %s\n' % targetMayaFileName
                fileObject.write(text)


    def postProcess(self):
        r"""
            後処理を行う。
        """
        tmpfile = self.temporaryFile()
        tmpfilename = os.path.basename(tmpfile)

        connection_scripts = self.connectionScripts()
        script = '\n'.join(connection_scripts)

        result_file = self.exportPath()
        result_name = os.path.basename(result_file)

        with codecs.open(result_file, 'wb', 'utf-8') as f:
            header = self.header()
            if header:
                f.write(header)

            self.copyFromMayaFile(
                tmpfile, tmpfilename, result_name, f
            )

            f.write('\n\n')
            f.write(script)

    ## This method is main rutin.
    #  But basically it is not modified by a inherited class.
    #
    #  When this method is called, it detects a node to export,
    #  and through these nodes to a run method of it.
    #  The run method will call a listExportedNodes method.
    #  So the developer should modify the "listExportedNodes" to
    #  detect a exported animation nodes from the nodes.
    def export(self, nodes=None):
        r"""
            ここに説明文を記入
            
            Args:
                nodes (None):[edit]
                
            Returns:
                any:
        """
        self.checkDirectoryExists()

        self.__nodes = []
        nodes = nodes if nodes else cmds.ls(sl=True)
        if not nodes:
            raise AttributeError(
                "No nodes to export animation were specified."
            )
        self.__nodes = nodes

        self.run()
        if not os.path.isfile(self.temporaryFile()):
            return False
        self.postProcess()
        
        try:
            os.remove(self.temporaryFile())
        except:
            pass
            
        self.initialize()

        return True


class DrivenExporter(AbstractAnimExporter):
    r"""
        ドリブンキーの書き出し機能を提供するクラス。
    """
    ExportedTypes = DrivenExportedTypes[:]
    OutConnectionTemplate = '":%s"'
    def listExportedNodes(self, targetNode):
        r"""
            書き出しノードを特定してリストする。
            
            Args:
                targetNode (str):
                
            Returns:
                dict
        """
        def listAnimCurveWithBlendWeighted(node, isFirst=False):
            r"""
                BlendWeight付きのanimCurveをリストする。
                
                Args:
                    node (str):
                    isFirst (bool):
                    
                Returns:
                    list:
            """
            exported, end_nodes = [], []
            result = [exported, end_nodes, []]
            animCurves = cmds.listConnections(node, s=True, d=False)
            if not animCurves:
                return result
            animCurves = cmds.ls(animCurves, typ=self.ExportedTypes)
            if not animCurves:
                return result

            if isFirst:
                result[2] = animCurves[:]

            for anim in animCurves:
                exported.append(anim)
                if cmds.nodeType(anim) in DrivenAnimTypes:
                    end_nodes.append(anim)
                    continue
                exp, end, inp = listAnimCurveWithBlendWeighted(anim)
                exported.extend(exp)
                end_nodes.extend(end)

            return result

        result = {'exported':[], 'in':[], 'out':[]}
        result['exported'], result['in'], result['out'] = (
            listAnimCurveWithBlendWeighted(targetNode, isFirst=True)
        )
        
        return result

    def copyFromMayaFile(
            self, temporaryFile, tempMayaFileName, targetMayaFileName,
            fileObject
        ):
        r"""
            Mayaファイルからテンポラリにコピーする。
            
            Args:
                temporaryFile (str):
                tempMayaFileName (str):
                targetMayaFileName (str):
                fileObject (file):
        """
        mobj = re.compile('".+"')
        param_mode = False
        with open(temporaryFile, 'r') as tmpf:
            while(1):
                text = tmpf.readline()
                if not text:
                    break

                if param_mode:
                    if text.startswith('connectAttr'):
                        param_mode = False
                    else:
                        continue

                if text.startswith('//Name: %s' % tempMayaFileName):
                    text = '//Name: %s\n' % targetMayaFileName
                elif text.startswith('// End of %s' % tempMayaFileName):
                    text = ''
                elif text.startswith('select '):
                    param_mode = True
                    continue

                fileObject.write(text)