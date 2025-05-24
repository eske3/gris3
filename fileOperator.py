#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    Mayaを操作するための関数集。
    
    Dates:
        date:2015/02/19 17:11[eske](eske3g@gmail.com)
        update:2023/11/10 19:02 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2015 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
from maya import cmds, mel, OpenMaya
from . import fileInfoManager
from .uilib import mayaUIlib

WORKSPACE_TEMPLATE = '''//Maya %(version)s Project Definition
workspace -fr "scene" "work";
workspace -fr "templates" "assets";
workspace -fr "sourceImages" "resources";
workspace -fr "mayaBinary" "scenes";
workspace -fr "mayaAscii" "scenes";
workspace -fr "images" "images";
workspace -fr "particles" "particles";
workspace -fr "3dPaintTextures" "3dPaintTextures";
workspace -fr "depth" "renderData/depth";
workspace -fr "lights" "renderData/shaders";
workspace -fr "iprImages" "renderData/iprImages";
workspace -fr "diskCache" "resources";
workspace -fr "mel" "mel";
''' % {
    'version' : cmds.about(v=True)
}

def toMayaPath(filepath):
    r"""
        パス区切り文字をスラッシュに変換して返す。
        
        Args:
            filepath (str):
            
        Returns:
            str:
    """
    return filepath.replace('\\', '/')


def isCurrentScene(filepath):
    r"""
        現在のシーンが任意の指定されたパスであるかどうかを返す。
        
        Args:
            filepath (str):
            
        Returns:
            bool:
    """
    return toMayaPath(filepath) == toMayaPath(cmds.file(q=True, sn=True))


class MayaFileManager(object):
    r"""
        Mayaファイルのサムネイル生成管理などを行う機能を提供するクラス
    """
    def __new__(cls):
        if hasattr(cls, '__singletoninstance__'):
            return cls.__singletoninstance__
        obj = super(MayaFileManager, cls).__new__(cls)
        cls.__singletoninstance__ = obj

        obj.job_ids = []
        obj.job_ids.append(
            cmds.scriptJob(e=('SceneSaved', obj.createThumbnail))
        )
        obj.job_ids.append(
            cmds.scriptJob(e=('SceneOpened', obj.clearTargetScene))
        )
        obj.job_ids.append(
            cmds.scriptJob(e=('NewSceneOpened', obj.clearTargetScene))
        )

        obj.__target_scene = None
        obj.__protect = False

        return obj

    def deleteJobs(self):
        r"""
            バックグラウンドで動いているScriptJobを削除する。
        """
        while(len(self.job_ids) > 0):
            id = self.job_ids.pop()
            cmds.scriptJob(k=id)
            print('Deleted job ID : %s' % id)

    def __del__(self):
        r"""
            このクラスが消えるときに、一緒に管理ジョブのIDを消去する
        """
        self.deleteJobs()

    def setTargetScene(self, filepath):
        r"""
            セーブ対象となるシーンパスを設定する
            
            Args:
                filepath (str):
        """
        self.__target_scene = filepath
        self.__protect = True

    def targetScene(self):
        r"""
            セーブ対象となるシーンパスを返す
            
            Returns:
                str:
        """
        return self.__target_scene

    def clearTargetScene(self):
        r"""
            セーブ対象となるファイルの設定をクリアする。
        """
        if self.__protect:
            self.__protect = False
            return
        self.setTargetScene(None)

    def createThumbnail(self):
        r"""
            現在のシーンパスがtargetSceneと同じ場合サムネイルを作成する
        """
        target_scene = self.targetScene()
        if not target_scene:
            return
        if not isCurrentScene(target_scene):
            return
        
        filepath = self.__target_scene+'__thumb__.png'
        mayaUIlib.write3dViewToFile(filepath, 512, 512)
        print('Saved thumbnail in "%s".' % filepath)

        # reload(fileInfoManager)
        m = fileInfoManager.FileInfoManager()
        m.setFile(target_scene)
        m.setImage(filepath, move=True)


class NamespaceManager(object):
    r"""
        グローバルなネームスペース管理を行うためのクラス。
    """
    def __new__(cls):
        if hasattr(cls, '__singletoninstance__'):
            return cls.__singletoninstance__
        obj = super(NamespaceManager, cls).__new__(cls)
        cls.__singletoninstance__ = obj
        cls.__namespace = ''
        return cls.__singletoninstance__

    def setNamespace(self, namespace=''):
        r"""
            ネームスペースを設定するメソッド。
            
            Args:
                namespace (str):
        """
        self.__namespace = namespace

    def namespace(self):
        r"""
            設定されているネームスペースを返すメソッド。
            
            Returns:
                str:
        """
        return self.__namespace


ImportMode, ReferenceMode = range(2)
ImportModeFlags = {
    ImportMode : {
        'i' : True,
    },
    ReferenceMode : {
        'r' : True
    }
}

def makeWorkspaceFile(dirpath, template=None):
    r"""
        仮のworkspace.melを作成するための関数。
        
        Args:
            dirpath (str):ディレクトリパス。
            template (str):workspacel.mel内に記述する内容
    """
    filepath = os.path.join(dirpath, 'workspace.mel')
    template = WORKSPACE_TEMPLATE if template is None else template
    if os.path.exists(filepath):
        return
    try:
        with open(filepath, 'w') as f:
            f.write(template)
    except Exception as e:
        print('Creation Error : {}'.format(e.args[0]))
    else:
        print('Create workspace.mel at {}'.format(filepath))


def setProject(filepath):
    r"""
        MayaでSetProjectするための関数。
        
        Args:
            filepath (str):SetProjectするディレクトリパス。
    """
    cmds.workspace(filepath, o=True)
    cmds.workspace(dir=filepath)
    OpenMaya.MGlobal.displayWarning('Set project at : %s' % filepath)


def searchAndSetProject(startfile):
    r"""
        与えられたファイル名より上の階層を探索し、workspace.mel
        ファイルを持つディレクトリがあった場合、そのディレクトリで
        SetProject:を行う関数。
        
        Args:
            startfile (str):探索の最初となるファイルパス。
            
        Returns:
            bool:
    """
    file = startfile
    while(1):
        if os.path.isfile(os.path.join(file, 'workspace.mel')):
            setProject(file)
            return True
        new_file = os.path.dirname(file)
        if file == new_file:
            return False
        file = new_file
    return False


def openFile(
    filepath,
    autoProjectSetting=True, openAsTemporary=False, useSelectivePreload=True
):
    r"""
        Mayaファイルを開くための関数。
        
        Args:
            filepath (str):
            autoProjectSetting (bool):プロジェクトディレクトリを自動検出してセットする。
            openAsTemporary (bool):開いたファイルをテンポラリとしてリネームする場合はTrue。
            useSelectivePreload (bool):SelectivePreloadを使用する場合はTrue。
    """
    file, ext = os.path.splitext(filepath)
    filetype = {'.ma':'mayaAscii', '.mb':'mayaBinary'}.get(ext.lower())
    filepath = os.path.normpath(filepath).replace('\\', '/')
    
    # Selective Preloadを行う。---------------------------------------------------
    isDone = False
    if useSelectivePreload:
        cmds.file(filepath, f=True, o=True, buildLoadSettings=True)
        if cmds.selLoadSettings(q=True, numSettings=True) > 1:
            cmds.optionVar(stringValue=('preloadRefEdTopLevelFile', filepath))
            mel.eval('PreloadReferenceEditor')
            isDone = True

    if not isDone:
        cmds.file(filepath, f=True, o=True)
    # -------------------------------------------------------------------------

    # 開いたファイルを最近読み込んだファイルのリストに加える。-----------------
    mel.eval(
        'addRecentFile("%s", "%s");' % (
            os.path.normpath(filepath).replace('\\', '/'), filetype
        )
    )
    # -------------------------------------------------------------------------

    # プロジェクトディレクトリを検出し、そのディレクトリでSetProjectを行う。---
    if autoProjectSetting:
        searchAndSetProject(filepath)
    # -------------------------------------------------------------------------

    # 仮想のテンポラリファイルとしてリネームを行う。---------------------------
    temppath = os.path.join(os.environ['TEMP'], 'TMPORARPUBLICFILE')
    if openAsTemporary:
        if isDone:
            cmds.evalDeferred('cmds.file(rename="%s")' % temppath)
        else:
            cmds.file(rename=temppath)
        OpenMaya.MGlobal.displayWarning('Rename file as temporary.')
    # -------------------------------------------------------------------------


def importFile(filepath, namespace='', useNamespace=False, renameAll=False):
    r"""
        ファイルをインポートするためのラッパー関数。
        
        Args:
            filepath (str):入力ファイル
            namespace (str):ネームスペース
            useNamespace (bool):ネームスペースを使うかどうか。
            renameAll (bool):全ノードにプレフィックスを付加するかどうか。
    """
    flags = {'i' : True, 'ignoreVersion' : True}
    if useNamespace:
        if namespace:
            flags['ns'] = namespace
    else:
        if renameAll:
            flags['ra'] = True
        if namespace:
            flags['rpr'] = namespace

    cmds.file(filepath, **flags)


def referenceFile(filepath, namespace, shared=None):
    r"""
        ファイルのリファレンスを行う。
        sharedにはcmds.fileのshdで使用できる文字列のリストを渡す。
        
        Args:
            filepath (str):リファレンスするファイルパス。
            namespace (str):ネームスペース
            shared (list):共有するノードタイプ。
    """
    flags = {'r' : True, 'ignoreVersion' : True, 'ns' : namespace}
    if shared:
        flags['shd'] = shared
    cmds.file(filepath, **flags)


def saveFile(dirname, filename, fileType, saveMode, autoSetProject=True):
    r"""
        Mayaのファイルを保存するメソッド。
        cmds.fileコマンドのラッパー関数。
        戻り値としてセーブ（またはエクスポート）したファイルパスを返す。
        
        Args:
            dirname (str):保存ディレクトリパス。
            filename (str):保存するファイル名。
            fileType (str):データのタイプ。
            saveMode (int):
            autoSetProject (bool):プロジェクトをセットするかどうか
            
        Returns:
            str:
    """
    ext = {'mayaAscii' : '.ma', 'mayaBinary' : '.mb'}.get(fileType, '.mb')

    if not filename.endswith(ext):
        filename += ext
    export_path = os.path.join(dirname, filename).replace('\\', '/')

    if saveMode == 0:
        cmds.file(rename=export_path)
        cmds.file(save=True, type=fileType)
        
        if autoSetProject:
            searchAndSetProject(export_path)
    else:
        cmds.file(export_path, es=True, f=True, type=fileType)

    return export_path
