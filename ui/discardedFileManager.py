# -*- coding: utf-8 -*-
r'''
    @file     discardedFileManager.py
    @brief    ファイル情報を表示、編集する機能を提供するモジュール。
    @class    DiscardedFileManager : 廃棄されたファイルを復帰するための管理ウィジェット。
    @class    MainGUI : ここに説明文を記入
    @function showWindow : ここに説明文を記入
    @date        2017/07/08 3:13[Eske](eske3g@gmail.com)
    @update      2017/07/08 3:13[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
import os
import time
from gris3 import uilib, fileInfoManager
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

class DiscardedFileManager(QtWidgets.QWidget):
    r'''
        @brief       廃棄されたファイルを復帰するための管理ウィジェット。
        @inheritance QtWidgets.QWidget
        @date        2017/07/05 18:29[eske](eske3g@gmail.com)
        @update      2017/07/08 3:13[Eske](eske3g@gmail.com)
    '''
    fileRestored = QtCore.Signal()
    def __init__(self, parent=None):
        r'''
            @brief  初期化を行う。
            @param  parent(None) : [QtWidgets.QWidget]
            @return None
        '''
        super(DiscardedFileManager, self).__init__(parent)
        self.setWindowTitle('Discarded File Manager')

        # 廃棄ファイルの一覧UI。===============================================
        self.__view = QtWidgets.QTreeView()
        self.__view.setAlternatingRowColors(True)
        self.__view.setRootIsDecorated(False)
        self.__view.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )
        
        model = QtGui.QStandardItemModel(0, 2)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'File Name')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Discarded Date')
        self.__view.setModel(model)
        self.__view.setColumnWidth(0, 360)
        # =====================================================================
        
        # 廃棄ファイルの復帰ボタン。===========================================
        restore_btn = uilib.OButton()
        restore_btn.setIcon(uilib.IconPath('uiBtn_export'))
        restore_btn.setToolTip('Restore selected files.')
        restore_btn.setSize(64)
        restore_btn.setBgColor(32, 145, 178)
        restore_btn.clicked.connect(self.restoreSelectedFiles)
        
        restore_label = QtWidgets.QLabel('Restore selected')
        # =====================================================================

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(self.__view, 0, 0, 1, 2)
        layout.addWidget(restore_label, 1, 0, 1, 1)
        layout.setAlignment(restore_label, QtCore.Qt.AlignRight)
        layout.addWidget(restore_btn, 1, 1, 1, 1)

        self.__manager = fileInfoManager.FileDiscarder()
        self.__cached_datalist = []
        self.__workdir = ''

    def setWorkdir(self, workdir):
        r'''
            @brief  ここに説明文を記入
            @param  workdir : [edit]
            @return None
        '''
        model = self.__view.model()
        model.removeRows(0, model.rowCount())

        self.__manager.setWorkdir(workdir)
        datalist = self.__manager.listMovedFiles()
        row = 0
        for file, data in datalist.items():
            f_item = QtGui.QStandardItem(data['filename'])
            f_item.setData(file)
            
            moved_time = time.strftime(
                '%Y/%m/%d %H:%M:%S', time.localtime(data['movedTime'])
            )
            t_item = QtGui.QStandardItem(moved_time)
            t_item.setData(data['movedTime'])
            
            model.setItem(row, 0, f_item)
            model.setItem(row, 1, t_item)
            row += 1
        self.__cached_datalist = datalist
        self.__workdir = workdir

    def workdir(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return self.__workdir

    def restoreSelectedFiles(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        filenamelist = []
        for index in [
            x for x in self.__view.selectedIndexes() if x.column() == 0
        ]:
            filenamelist.append(index.data(QtCore.Qt.UserRole+1))
        for key in [x for x in filenamelist if x in self.__cached_datalist]:
            try:
                self.__manager.restore(key, self.__cached_datalist[key])
            except fileInfoManager.FileExistingError as e:
                print(e)
        self.__manager.cleanup()
        self.setWorkdir(self.workdir())
        self.fileRestored.emit()

class MainGUI(uilib.AbstractSeparatedWindow):
    r'''
        @brief       ここに説明文を記入
        @inheritance uilib.AbstractSeparatedWindow
        @date        2017/07/05 18:29[eske](eske3g@gmail.com)
        @update      2017/07/08 3:13[Eske](eske3g@gmail.com)
    '''
    def centralWidget(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return DiscardedFileManager()


def showWindow(parent=None):
    r'''
        @brief  ここに説明文を記入
        @param  parent(None) : [edit]
        @return None
    '''
    w = MainGUI(parent)
    w.resize(520, 400)
    w.show()
    return w
