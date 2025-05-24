#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ここに説明文を記入
    
    Dates:
        date:2017/01/22 23:41[Eske](eske3g@gmail.com)
        update:2022/08/05 12:39 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
import re
import shutil

from maya import cmds
from . import core
from . import skinWeightExporter
from . import animationExporter
from . import curveExporter
from .. import func

class MayaFileExporter(core.BasicExporter):
    r"""
        mayaのファイルをエクスポートする機能を提供するクラス。
    """
    FileTypes = {
        'mayaAscii' : 'ma',
        'mayaBinary' : 'mb',
    }
    def __init__(self):
        super(MayaFileExporter, self).__init__()
        self.__filetype = 'mayaAscii'
        self.setExtension(self.FileTypes[self.fileType()])

    def setFileType(self, filetype):
        r"""
            書き出すファイルタイプをセットする。
            
            Args:
                filetype (str):
        """
        if not filetype in self.FileTypes:
            raise ValueError(
                'The file type must be a "mayaAscii" or "mayaBinary".'
            )
        self.__filetype = filetype
        self.setExtension(self.FileTypes[filetype])

    def fileType(self):
        r"""
            書き出すファイルタイプを返す。
            
            Returns:
                str:
        """
        return self.__filetype

    def export(self, file):
        r"""
            書き出すメソッド。
            
            Args:
                file (str):
        """
        cmds.file(file, es=True, type=self.fileType())
        print('Save in "%s".' % file)


class MayaFileSaver(MayaFileExporter):
    r"""
        mayaのファイルをセーブする機能を提供するクラス。
    """
    def export(self, file):
        r"""
            書き出しの実行。
            
            Args:
                file (str):ファイル名
        """
        cmds.file(rename=file)
        cmds.file(save=True, type=self.fileType())


def exportMultSkinWeights(parentDir, isOverwrite=False, nodes=None):
    r"""
        スキニングのウェイトを書き出す。
        
        Args:
            parentDir (str):
            isOverwrite (bool):
            nodes (list):
    """
    if not nodes:
        nodes = cmds.ls(sl=True)

    exp = skinWeightExporter.Exporter()
    for node in nodes:
        filepath = core.BasicExporter.getLatestFile(
            parentDir, (node + '_wgt'), 'mel', isOverwrite=isOverwrite
        )
        curpath  = os.path.join(parentDir, node + '_wgt.cur.mel')
        exp.setShape(node)

        exp.setExportPath(filepath)
        try:
            exp.export()
        except Exception as e:
            print(e.args)
        else:
            shutil.copy2(filepath, curpath)


def getLatestAndCurrent(parentDir, filename, extension, isOverwrite=False):
    r"""
        最新バージョンとカレントファイルのパスを返す。
        
        Args:
            parentDir (str):ファイルを格納するディレクトリパス
            filename (str):ファイル名
            extension (str):捜査対象拡張子
            isOverwrite (bool):最新版に上書きするかどうか
            
        Returns:
            tuple:(ファイル名, ファイル格納パス, カレントパス)
    """
    if not extension.startswith('.'):
        extension = '.' + extension
    ext_pattern = re.compile(
        extension.replace('.', '\.')+'$', re.IGNORECASE
    )
    filename = ext_pattern.sub('', filename)
    extension = extension[1:]
    ver_pattern = re.compile('(\.v\d+|\.cur)$')
    filename = ver_pattern.sub('', filename)

    filepath = core.BasicExporter.getLatestFile(
        parentDir, filename, extension, isOverwrite=isOverwrite
    )
    curpath = core.BasicExporter.getCurFile(
        parentDir, filename, extension
    )

    return (filename, filepath, curpath)


def exportSelectedDrivenKeys(parentDir, filename, isOverwrite=False):
    r"""
        ドリブンキーを書き出す関数。
        
        Args:
            parentDir (str):書き出し先のルートディレクトリ
            filename (str):書き出すファイル名
            isOverwrite (bool):最新版に上書きするかどうか
    """
    basename, filepath, curpath = getLatestAndCurrent(
        parentDir, filename, 'ma', isOverwrite=isOverwrite
    )
    exp = animationExporter.DrivenExporter()
    exp.setExportPath(filepath)
    exp.export()
    
    if os.path.isfile(filepath):
        shutil.copy2(filepath, curpath)


def exportSelectedCurves(
        parentDir, filename, isOverwrite=False
    ):
    r"""
        カーブを書き出す関数。
        
        Args:
            parentDir (str):書き出し先のルートディレクトリ
            filename (str):書き出すファイル名
            isOverwrite (bool):最新版に上書きするかどうか
    """
    basename, filepath, curpath = getLatestAndCurrent(
        parentDir, filename, 'ma', isOverwrite=isOverwrite
    )
    selected = cmds.ls(sl=True)
    if not selected:
        if not cmds.objExists('all_anmSet'):
            raise RuntimeError('No all_anmSet exists.')
        cmds.select('all_anmSet')
        selected = cmds.ls(sl=True)
    exp = curveExporter.Exporter()
    exp.setExportedNodes(selected)
    exp.setExportPath(filepath)
    exp.export()
    if os.path.isfile(filepath):
        shutil.copy2(filepath, curpath)


def exportExtraJointScripts(parentDir, filename, isOverwrite=False):
    r"""
        エクストラジョイントを書き出す関数。
        
        Args:
            parentDir (str):書き出し先のルートディレクトリ
            filename (str):書き出すファイル名
            isOverwrite (bool):最新版に上書きするかどうか
    """
    from gris3.exporter import extraJointExporter
    exp = extraJointExporter.Exporter()
    basename, filepath, curpath = getLatestAndCurrent(
        parentDir, filename, exp.extension(), isOverwrite=isOverwrite
    )
    exp.setExportDir(parentDir)
    exp.setBasename(basename)
    exp.setIsOverwrite(isOverwrite)
    exp.setExtraJoints(cmds.ls(sl=True))
    exp.execute()


def exportMayaFile(
    parentDir, filename, isOverwrite=False, exporter=MayaFileExporter()
):
    r"""
        mayaのファイルを書き出す関数。
        
        Args:
            parentDir (str):書き出し先のルートディレクトリ
            filename (str):書き出すファイル名
            isOverwrite (bool):最新版に上書きするかどうか
            exporter (MayaFileExporter):
    """
    basename, filepath, curpath = getLatestAndCurrent(
        parentDir, filename, exporter.extension(), isOverwrite=isOverwrite
    )
    exp = exporter
    exp.setExportDir(parentDir)
    exp.setBasename(basename)
    exp.setIsOverwrite(isOverwrite)
    exp.execute()
