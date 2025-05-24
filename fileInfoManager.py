#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ファイル情報を管理する機能を提供するモジュール。
    
    Dates:
        date:2017/07/08 2:54[Eske](eske3g@gmail.com)
        update:2022/08/17 18:32 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
import json
import time
import re
import shutil

from . import lib, fileUtil, verutil

class TimeoutError(Exception):
    r"""
        時間切れによる処理の中断が行われた時に送出される例外
    """
    pass

class FileInfoModifier(object):
    r"""
        情報ファイルにロックをかけてから編集を行うコンテキストマネージャ。
        また、ロックをかけるディレクトリが存在しない場合は先に作成も行う。
    """
    def __init__(self, infoDir, timeout=5.0):
        r"""
            引数にはロックをかける情報ディレクトリパスを渡す。
            
            Args:
                infoDir (str):
                timeout (float):タイムアウトまでの時間
        """
        self.__infodir = infoDir
        self.__lockfile = os.path.join(infoDir, '.locked')
        self.__timeout = 5.0

    def isLocked(self):
        r"""
            ファイルのロックがかかっているかどうか
            
            Returns:
                bool:
        """
        return os.path.exists(self.__lockfile)

    def __enter__(self):
        def makeLockFile():
            r"""
                ロック状態を表す空ファイルを生成するローカル関数。
                作成に成功した場合はTrueを返す。
                
                Returns:
                    bool:
            """
            if self.isLocked():
                return False
            try:
                f = open(self.__lockfile, 'w')
                f.close()
            except:
                return False
            else:
                return True

        if not os.path.exists(self.__infodir):
            os.makedirs(self.__infodir)

        st = time.time()
        while(True):
            test = makeLockFile()
            if test:
                return self
            if time.time() - st > self.__timeout:
                raise TimeoutError(
                    'Failed to modify the file info. [%s]' % os.path.basename(
                        self.__infodir
                    )
                )
            time.sleep(0.25)

    def __exit__(self, exc_type, exc_value, traceback):
        r"""
            処理の成否に関わらずロックファイルを消去する。
            
            Args:
                exc_type (any):[edit]
                exc_value (any):[edit]
                traceback (any):[edit]
                
            Returns:
                bool:
        """
        st = time.time()
        while(True):
            try:
                os.remove(self.__lockfile)
            except:
                pass
            else:
                return False
            if time.time() - st > self.__timeout:
                raise TimeoutError(
                    'Failed to release the lock. [%s]' % os.path.basename(
                        self.__infodir
                    )
                )
            time.sleep(0.25)

class FileInfoManager(object):
    r"""
        ファイル情報を編集するための機能を提供するクラス。
    """
    FileTable = {
        'log':['log.json'],
        'image':['images', 'image.png'],
    }
    def __init__(self):
        self.setFile('')

    def infoDir(self, *subDirectories):
        r"""
            ファイル情報を格納するディレクトリパスを返す。
            引数subDirectoriesに文字列を渡すと、ファイル情報ディレクトリの
            サブディレクトリも含めた状態で返す。
            subDirectoriesが一つの場合、このクラスのFileTableのキーとして情報を
            扱う。（キーとして見つからない場合はそのまま使用する）
            
            Args:
                *subDirectories (any):
                
            Returns:
                str:
        """
        if not self.__infodir:
            return ''
        if len(subDirectories) == 1:
            subDirectories = self.FileTable.get(
                subDirectories[0], subDirectories
            )
        return os.path.join(self.__infodir, *subDirectories)

    def isEmpty(self):
        r"""
            情報ファイルが空かどうかを返す。
            
            Returns:
                bool:
        """
        for key in self.FileTable:
            if os.path.exists(self.infoDir(key)):
                return False
        return True

    def removeInfo(self, force=True):
        r"""
            情報ファイルを削除する。
            forceがFalseの場合かつ情報ファイルが残っている場合は削除を行わない。
            
            Args:
                force (bool):
                
            Returns:
                bool:
        """
        if not force and not self.isEmpty():
            return False

        infodir = self.infoDir()
        try:
            if os.path.exists(infodir):
                shutil.rmtree(infodir)
        except Exception as e:
            print(e)
            return False
        rootdir = self.rootInfoDir()
        if not os.listdir(rootdir):
            shutil.rmtree(rootdir)
        return True

    def logData(self):
        r"""
            ログ情報を展開してlistにして返す。
            
            Returns:
                list:
        """
        def load_data(path):
            if verutil.PyVer < 3:
                with open(logpath, 'r') as f:
                    data = json.loads(lib.decode(f.read()))
            else:
                with open(logpath, 'r') as f:
                    data = json.load(f)
            return data
        logpath = self.infoDir('log')
        if os.path.exists(logpath):
            try:
                with open(logpath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except UnicodeDecodeError:
                data = load_data(logpath)
            except TypeError:
                data = load_data(logpath)
            except Exception as e:
                raise e
        else:
            data = []
        return data

    def saveLogData(self, data):
        r"""
            ログ情報を書き出す。
            
            Args:
                data (list):
        """
        logpath = self.infoDir('log')
        data = json.dumps(data, ensure_ascii=False, indent=4)
        with open(logpath, 'w') as f:
            f.write(lib.encode(data))

    def setImage(self, imageFile, move=False):
        r"""
            サムネイルとして使用するイメージをセットする。
            セットされたイメージは情報フォルダへコピーされるが、moveが
            Trueの場合は移動される。現状pngのみをサポートする。
            
            Args:
                imageFile (str):ソースイメージのパス
                move (bool):
        """
        name, ext = os.path.splitext(imageFile)
        if ext.lower() != '.png':
            raise ValueError(
                'Invalid file type "%s".' % imageFile
            )
        with FileInfoModifier(self.infoDir()):
            imagepath = self.infoDir('image')
            imagedir = os.path.dirname(imagepath)
            if not os.path.exists(imagedir):
                os.makedirs(imagedir)

            if not move:
                shutil.copy(imageFile, imagepath)
            else:
                shutil.move(imageFile, imagepath)

    def image(self, checkExisting=False):
        r"""
            セットされているイメージのパスを返す。
            checkExistingがTrueの場合、ファイルパスが存在するかどうかの確認を
            行い、ない場合は空文字列を返す。
            
            Args:
                checkExisting (bool):ファイルが存在するかどうかの確認も行う
                
            Returns:
                str:
        """
        path = self.infoDir('image')
        if not checkExisting:
            return path
        return path if os.path.exists(path) else ''

    def deleteImage(self):
        r"""
            サムネイルとして使用されるイメージを削除する。
        """
        filepath = self.infoDir('image')
        
        if not os.path.exists(filepath):
            return
        try:
            os.remove(filepath)
            self.removeInfo(False)
        except:
            pass

    @staticmethod
    def infoDirName():
        r"""
            ファイル情報を格納するディレクトリ名を返す。
            
            Returns:
                str:
        """
        return '.grisfileproperties'

    def rootInfoDir(self):
        r"""
            情報ファイルをまとめるディレクトリパスを返す。
            
            Returns:
                str:
        """
        return self.__info_rootdir

    def createData(
        self, comment='', userName=None, creationTime=None,
        fgColor=None, bgColor=None, protected=False
    ):
        r"""
            ログとして残すデータを作成する。
            データにはコメント、ユーザー名、作成日時が保持される。
            また、任意で背景色と描画色も保持する事が出来る。
            
            Args:
                comment (str):コメント
                userName (str):ユーザー名
                creationTime (float):作成日時
                fgColor (tuple):r, g, b(int)を持つタプル。
                bgColor (tuple):r, g, b(int)を持つタプル。
                protected (bool):
                
            Returns:
                dict:
        """
        data = {}
        data['name'] = userName if userName else lib.getUserName()
        data['date'] = creationTime if creationTime else time.time()
        data['comment'] = comment
        if fgColor:
            data['fgColor'] = fgColor
        if bgColor:
            data['bgColor'] = bgColor
        if protected:
            data['protected'] = True
        return data

    def addComment(self, comment, **keywords):
        r"""
            コメントをファイルのデータに追加するメソッド。
            作成された辞書データを返す。
            
            Args:
                comment (str):
                **keywords (str):
                
            Returns:
                dict:
        """
        with FileInfoModifier(self.infoDir()):
            data = self.logData()
            new_data = self.createData(comment=comment, **keywords)
            data.append(new_data)
            self.saveLogData(data)
        return new_data

    def setComment(self, comment, **keywords):
        r"""
            コメントをファイルのデータにセットする。
            addCommentと違い、こちらは既存のコメントは削除する。
            作成された辞書データを返す。
            
            Args:
                comment (str):
                **keywords (str):
                
            Returns:
                dict:
        """
        with FileInfoModifier(self.infoDir()):
            # data = self.logData()
            new_data = self.createData(comment=comment, **keywords)
            # data.append(new_data)
            self.saveLogData([new_data])
        return new_data

    def setFile(self, filepath, force=False):
        r"""
            操作対象となるファイルをセットする。
            ファイルが存在しない場合はFalseを返し、ルートディレクトリの
            情報などは空になるが、forceがTrueの場合はFalseを返すが情報
            は構築される。
            
            Args:
                filepath (str):
                force (bool):
                
            Returns:
                bool:
        """
        self.__infoxml = None
        exists = os.path.exists(filepath)
        if exists or force:
            dirpath, filename = os.path.split(filepath)
            if dirpath == filepath:
                raise IOError('The root directory can not have a information.')
            self.__filedir = dirpath
            self.__filename = filename
            self.__info_rootdir = os.path.join(
                self.__filedir, self.infoDirName()
            )
            self.__infodir = os.path.join(self.__info_rootdir, self.__filename)
        else:
            self.__filedir = ''
            self.__filename = ''
            self.__info_rootdir = ''
            self.__infodir = ''
        return exists

    def setDataList(self, dataList):
        r"""
            ログ情報を持つlistをセットし、ファイルに保存する。
            saveLogDataと比較して、こちらはロック処理も行うため、
            通常はこちらを使用すること。
            
            Args:
                dataList (list):
                
            Returns:
                bool:
        """
        try:
            with FileInfoModifier(self.infoDir()):
                if dataList:
                    self.saveLogData(dataList)
                else:
                    os.remove(self.infoDir('log'))

            if not dataList:
                self.removeInfo(False)
            return True
        except Exception as e:
            print(e.args[0])
            return False

    def file(self):
        r"""
            操作対象としてセットされているファイルパスを返す。
            
            Returns:
                str:
        """
        return os.path.join(self.__filedir, self.__filename)

    def rename(self, newName):
        r"""
            setFileで指定されているファイルをnewNameにリネームする。
            リネームすると情報ファイルもともにリネームされる。
            
            Args:
                newName (str):新しい名前を表すフルパス。
                
            Returns:
                bool:
        """
        orig_file = fileUtil.toStandardPath(self.file())
        new_file = fileUtil.toStandardPath(newName)
        if orig_file == new_file:
            # 同じ名前の場合は何も行わない。
            return False

        # リネーム先の情報データを先に確保しておく
        new_fim = FileInfoManager()
        new_fim.setFile(new_file, True)
        new_infodir = new_fim.infoDir()

        # 実ファイルのリネームを行う。
        os.rename(orig_file, new_file)

        # リネーム先の情報ファイルが存在する場合は削除する。===================
        if os.path.exists(new_infodir):
            shutil.rmtree(new_infodir)
        if self.isEmpty():
            return True
        # =====================================================================
        rootdir = os.path.dirname(new_infodir)
        if not os.path.exists(rootdir):
            os.makedirs(rootdir)

        # =====================================================================
        # 現在の情報ファイルを新しい名前としてリネーム。
        shutil.move(self.infoDir(), new_infodir)
        # =====================================================================


# /////////////////////////////////////////////////////////////////////////////
# ファイルを廃棄ディレクトリへの移動、復帰を管理するクラス。                 //
# /////////////////////////////////////////////////////////////////////////////
class FileExistingError(Exception):
    pass


class FileDiscarder(object):
    r"""
        古いファイルの管理を行う機能を提供するクラス。
    """
    TargetDirectoryName = '.discarded'
    Jsonfilename = '.discarded_filemanager'
    def __init__(self, workdir=''):
        r"""
            Args:
                workdir (str):作業対象ディレクトリパス。
        """
        self.__workdir = workdir

    def setWorkdir(self, workdir):
        r"""
            作業対象となるディレクトリパスを設定する。
            
            Args:
                workdir (str):
        """
        self.__workdir = workdir

    def workdir(self):
        r"""
            作業対象となるディレクトリパスを返す。
            
            Returns:
                str:
        """
        return self.__workdir

    def workDiscardedDirs(self):
        r"""
            ワークディレクトリと、その直下のdiscardedディレクトリを返す。
            ワークディレクトリが存在しない場合はNoneを２つ持つタプルを返す。
            
            Returns:
                tuple:
        """
        workdir = self.workdir()
        if not os.path.isdir(workdir):
            return (None, None, None)
        dscdir = os.path.join(workdir, self.TargetDirectoryName)
        jsonfile = os.path.join(dscdir, self.Jsonfilename)
        return (workdir, dscdir, jsonfile)

    def listMovedFiles(self):
        r"""
            移動されたデータのファイル名とその情報を持つ辞書を返す。
            
            Returns:
                dict:
        """
        workdir, dscdir, jsonfile = self.workDiscardedDirs()
        if not workdir:
            return {}

        ignored_ptn = re.compile('^\%s$|^__bk\d+$'+self.Jsonfilename)
        dscdir = os.path.join(workdir, self.TargetDirectoryName)
        files = os.listdir(workdir)

        if os.path.exists(jsonfile):
            with open(jsonfile, 'r') as f:
                newlist = json.load(f)
            # リストのクリーンナップ。
            current_filelist = [
                x for x in os.listdir(dscdir) if not ignored_ptn.match(x)
            ]
            return {
                x:y for x, y in newlist.items()
                if x in current_filelist
            }
        else:
            return {}

    def writeFile(self, filepath, datalist):
        r"""
            ファイル情報をjsonファイルに書き出す。
            失敗した場合はバックアップ用jsonファイルへと書き出す。
            
            Args:
                filepath (str):
                datalist (dict):
        """
        jsontext = json.dumps(datalist, indent=4, ensure_ascii=False)
        try:
            with open(filepath, 'w') as f:
                f.write(lib.encode(jsontext))
        except:
            bkpath = os.path.join(
                os.path.dirname(filepath),
                '__bk%s' % (''.join(str(time.time()).split('.')))
            )
            with open(bkpath, 'w') as f:
                f.write(lib.encode(jsontext))

    def moveTo(self, filepathes):
        r"""
            filepathesをdiscardedディレクトリへ移動する。
            
            Args:
                filepathes (list):
        """
        workdir, dscdir, jsonfile = self.workDiscardedDirs()
        # 作業用ディレクトリに関する設定その他。===============================
        if not workdir:
            raise IOError('Workspace directory does not exist.')
        if not os.path.isdir(dscdir):
            os.makedirs(dscdir)
        # =====================================================================
        
        # 管理用のデータを作成する。
        datalist = self.listMovedFiles()
        # =====================================================================
        cnt = 0
        for file in filepathes:
            if not os.path.exists(file):
                continue
            dirname, filename = os.path.split(file)
            name, ext = os.path.splitext(filename)
            new_filename = 'bkfile_%s%s%s' % (
                ''.join(str(time.time()).split('.')), cnt, ext
            )
            new_filepath = os.path.join(dscdir, new_filename)
            
            # データの移動。(失敗した場合はスルー）
            try:
                shutil.move(file, new_filepath)
                # shutil.copy2(file, new_filepath)
            except Exception as e:
                print(file)
                print(e.args[0])
                continue
            datalist[new_filename] = {
                'filename':filename, 'movedTime':time.time()
            }
            cnt += 1
        if cnt == 0:
            return
        # =====================================================================

        # ファイル情報をjsonファイルに書き出す。===============================
        # 失敗した場合はバックアップ用jsonファイルへと書き出す。
        self.writeFile(jsonfile, datalist)
        # =====================================================================

    def restore(self, filename, fileInfo, overrideTargetName=None):
        r"""
            与えられたファイルを、fileInfoの情報に基いてworkDirに展開する。
            filenameは展開するファイルパス(moveToで移動後の名前）、
            fileInfoは書き出されたjsonファイルに格納されているファイルの辞書情報。
            
            Args:
                filename (str):
                fileInfo (dict):
                overrideTargetName (str):
        """
        workdir, dscdir, jsonfile = self.workDiscardedDirs()
        source_file = os.path.join(dscdir, filename)
        target_name = (
            overrideTargetName if overrideTargetName else fileInfo['filename']
        )
        target_filepath = os.path.join(workdir, target_name)
        if os.path.exists(target_filepath):
            raise FileExistingError('The target file "%s" is already exists.')

        print(
            '# Restore file "%s"' % (fileInfo['filename'])
        )
        print('    as "%s".' % target_filepath)
        print('')
        try:
            shutil.move(source_file, target_filepath)
        except Exception as e:
            return e
        print(os.path.exists(target_name))

    def cleanup(self):
        r"""
            古いデータを格納するディレクトリ内のクリーンナップを行う。
        """
        workdir, dscdir, jsonfile = self.workDiscardedDirs()
        datalist = self.listMovedFiles()
        if not datalist:
            try:
                shutil.rmtree(dscdir)
            except:
                pass
            return

        self.writeFile(jsonfile, datalist)
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////