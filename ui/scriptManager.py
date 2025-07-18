#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    リグ構築するクリプトを実行するためのUIを提供する
    
    Dates:
        date:2017/01/21 23:59[Eske](eske3g@gmail.com)
        update:2020/10/20 00:02 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
import os
import re

from ..uilib import factoryUI, extendedUI
from .. import lib, uilib, factoryModules, verutil
from ..gadgets import scriptViewer
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

'''

'''
HELP_DOCUMENT_STYLE = '''
<style type="text/css">
.syntax{
    color:#5096f0;
}
.var{
    color:#5096f0;
}
h3{
    color:#d09820;
    margin-bottom:0;
    font-weight:normal;
}
ul{
    margin-top:0;
    margin-bottom:0;
    margin-left:0;
}

div.separator{
    margin-bottom:2em;
}
</style>
'''

class NoConstructorError(Exception):
    pass

def coordinateFiles(files, extensions, format):
    r"""
        ScriptManagerに表示するファイルのフィルタ用関数。
        
        Args:
            files (list):ファイルPASのリスト
            extensions (list):拡張子のリスト
            format (str):
            
        Returns:
            dict:
    """
    reobj = re.compile(format % '|'.join(extensions))
    matchedFiles = {}
    files = [os.path.basename(x) for x in files]
    files.sort()
    for file in files:
        r = reobj.search(file)
        if not r:
            continue
        data = {
            'ver':r.group(3) if r.group(3) else 'cur',
            'sep':r.group(2), 'name':file, 'ext':r.group(3),
            'simpleName':reobj.sub(r'\1\2\3', file)
        }
        if r.group(1) in matchedFiles:
            matchedFiles[r.group(1)].append(data)
        else:
            matchedFiles[r.group(1)] = [data]
    return matchedFiles

def parsePydoc(docstring):
    # /////////////////////////////////////////////////////////////////////////
    # 解析用ローカル関数。                                                   //
    # /////////////////////////////////////////////////////////////////////////
    def parseDoxygenStyle(docstring):
        lines = []
        patterns = {
            'brief' : (re.compile('@brief\s(.*)'), []),
            'param' : (re.compile('@param\s(.*)'), []),
            'return' : (re.compile('@return\s(.*)'), []),
        }
        other = []
        for line in docstring.split('\n'):
            for ptn_name, data in patterns.items():
                r = data[0].search(line)
                if r:
                    data[1].append(r.group(1))
                    break
            else:
                other.append(line)
        # 概要部分の組み立て。=================================================
        for cat, label, fmt in (
            ('brief', 'Brief', '%s<br>'),
            ('param', 'Parameters', '<li>%s</li>'),
            ('return', 'Return', '%s')
        ):
            pre = '\n'.join([fmt % x for x in patterns[cat][1]])
            if not pre:
                continue
            lines.append('<h3>{}</h3><ul>{}</ul>'.format(label, pre))
        # =====================================================================
        # その他。=============================================================
        if other:
            lines.append('<ul>%s</ul>'%('<br>'.join(other)))
        # =====================================================================
        return lines

    def parseGoogleStyle(docstring):
        patterns = [
            ('Parameters', re.compile('Args:'), '<li>%s</li>'), 
            ('Return', re.compile('Returns:'), '%s'),
        ]
        titleformat = '<h3>%s</h3>'
        lineformat =  '   %s<br>'

        ptn = patterns.pop(0)
        lines = [titleformat%('Brief')]
        stacked = []
        for line in [x.strip() for x in docstring.split('\n')]:
            if ptn[1].search(line):
                lines[-1] = lines[-1]+('<ul>%s</ul>'%('\n'.join(stacked)))
                lines.append(titleformat%(ptn[0]))
                stacked = []
                lineformat = ptn[2]
                if not patterns:
                    continue
                ptn = patterns.pop(0)
                continue
            if not line:
                continue
            stacked.append(lineformat%line)
        if stacked:
            lines[-1] = lines[-1]+('<ul>%s</ul>'%'\n'.join(stacked))
        return lines
    # /////////////////////////////////////////////////////////////////////////
    #                                                                        //
    # /////////////////////////////////////////////////////////////////////////

    if re.search('@brief', docstring):
        # Doxygenスタイルのドキュメントストリング
        return parseDoxygenStyle(docstring)
    return parseGoogleStyle(docstring)


class ScriptHelperView(extendedUI.FilteredView):
    r"""
        スクリプトのヘルプを表示するビューワ
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget): 親ウィジェット
        """
        super(ScriptHelperView, self).__init__(parent)
        self.view().setColumnWidth(0, 150)

    def createView(self):
        r"""
            再実装用メソッド。任意のViewを作成し返す。
            
            Returns:
                QTreeView/QListView/QTableView:
        """
        view = QtWidgets.QTreeView()
        view.setAlternatingRowColors(True)
        view.setVerticalScrollMode(QtWidgets.QTreeView.ScrollPerPixel)
        view.setHorizontalScrollMode(QtWidgets.QTreeView.ScrollPerPixel)
        view.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
        return view

    def createModel(self):
        r"""
            再実装用メソッド。任意のItemModelを作成し返す。
            
            Returns:
                QStandardItemModel:
        """
        model = QtGui.QStandardItemModel(0, 2)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Member Name')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Type')
        return model


class ScriptHelper(QtWidgets.QSplitter):
    r"""
        任意のモジュールのコマンドヘルプを表示するUI
    """
    Style = HELP_DOCUMENT_STYLE
    def __init__(self, parent=None):
        r"""
            初期化を行う。
            
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ScriptHelper, self).__init__(parent)
        self.__object = None

        self.__commandlister = ScriptHelperView()
        self.__commandlister.view().selectionModel().selectionChanged.connect(
            self.viewDocument
        )
        
        self.__doc_field = QtWidgets.QTextEdit()
        self.__doc_field.setStyleSheet(
            'QTextEdit{font-family:arial; font-size:%spx;}'%uilib.hires(12)
        )
        self.__doc_field.setWordWrapMode(QtGui.QTextOption.NoWrap)
        self.__doc_field.setReadOnly(True)
        
        self.addWidget(self.__commandlister)
        self.addWidget(self.__doc_field)
        self.setSizes((260, 100))
        self.setStretchFactor(1, 1)

    def listCommands(self, constructor):
        r"""
            一覧に表示するコマンドのリストを返す。
            
            Args:
                constructor (Constructor):
                
            Returns:
                list:
        """
        commands = [x for x in dir(constructor) if not x.startswith('_')]
        commands.sort()
        return ['__init__'] + commands

    def setObject(self, constructor):
        r"""
            ヘルプ表示を行うコンストラクタをセットする
            
            Args:
                constructor (constructors.BasicConstructor):
        """
        def addItem(parentObj, parentItem):
            r"""
                viewにアイテムを追加するローカル関数
                
                Args:
                    parentObj (object):探索オブジェクト
                    parentItem (QtGui.QStandardItem):親アイテム
                    
                Returns:
                    int:クラスを検知した数
            """
            commands = self.listCommands(parentObj)
            result = 0
            row = 0
            for command in commands:
                if not command:
                    continue
                obj = getattr(parentObj, command)
                obj_type = str(type(obj)).split("'")[1]
                if not obj_type or obj_type == 'module':
                    continue
                item = QtGui.QStandardItem(command)
                parentItem.setChild(row, 0, item)

                t_item = QtGui.QStandardItem(obj_type)
                parentItem.setChild(row, 1, t_item)
                row += 1
                
                if obj_type != 'type':
                    continue
                # オブジェクトがクラスの場合、メンバーも追加表示。
                result += 1
                result += addItem(obj, item)
            return result

        sizes = self.sizes()
        if sizes[0] < 2:
            sizes[0] = 260
            self.setSizes(sizes)

        self.__doc_field.setPlainText('')
        model = self.__commandlister.view().model().sourceModel()
        model.removeRows(0, model.rowCount())
        root_item = model.invisibleRootItem()

        self.__object = constructor
        result = addItem(constructor, root_item)
        self.__commandlister.view().setRootIsDecorated(bool(result))

    def viewErrorReports(self, errorText):
        r"""
            エラー内容を表示する。
            
            Args:
                errorText (str):エラー内容
        """
        self.setSizes((0, 200))
        text = '<pre><font size=5 color=#e00020>%s</font></pre>' % lib.encode(
            errorText
        )
        self.__doc_field.setText(text)

    def viewWarningRepots(self, warningText):
        r"""
            警告内容を表示する。
            
            Args:
                warningText (str):エラー内容
        """
        self.setSizes((0, 200))
        text = '<pre><font size=5 color=#4585e0>%s</font></pre>' % lib.encode(
            warningText
        )
        self.__doc_field.setText(text)
    
    def analyzeDocument(self, method):
        r"""
            規定のフォーマットで書かれたドキュメントをリッチテキストに
            変換して返す。
            
            Args:
                method (any):ドキュメントを表示するfunction、classなど
                
            Returns:
                str:
        """
        str_type = verutil.BaseString
        f_type =  type(lambda x:x)
        document = lib.encode(method.__doc__)
        try:
            import inspect
            spec = inspect.getargspec(method)
        except:
            header = self.Style
        else:
            header = '%s<span class="syntax">Syntax</span> : %s' % (
                self.Style,
                method.__name__
            )
            # 引数の組み立て。
            defaultlist = spec.defaults or []
            num = len(defaultlist)
            arglist = spec.args[:-num]
            for a, v in zip(spec.args[len(arglist):], defaultlist):
                if isinstance(v, str_type):
                    v = "'%s'"%v
                elif isinstance(v, f_type):
                    v = 'function'
                arglist.append('%s=%s'%(a, v))
            if spec.varargs:
                arglist.append('*%s'%spec.varargs)
            if spec.keywords:
                arglist.append('**%s'%spec.keywords)

            num = 4
            lines, mod = divmod(len(arglist), num)
            if lines < 1 or (lines==1 and mod==0):
                args = ', '.join(arglist)
            else:
                args = ''
                for i in range(lines):
                    line = ', '.join(arglist[i:i+num+1])
                    args += '<ul>%s,</ul>'%line
                if mod:
                    line = ', '.join(arglist[len(arglist)-mod:])
                    args += '<ul>%s</ul>'%line
            header += '(%s)'%args

        if not document:
            return header

        lines = [header]
        lines.extend(parsePydoc(document))
        return '\n'.join(lines)
    
    def viewDocument(self, selected, deselected):
        r"""
            リストで選択されたメンバーのドキュメントを表示する。
            
            Args:
                selected (QtCore.QItemSelection):
                deselected (QtCore.QItemSelection):
        """
        indexes = selected.indexes()
        if not indexes:
            return
        index = indexes[0]
        methodlist = []
        while(True):
            methodlist.append(index.data())
            parent = index.parent()
            if parent.row() == -1:
                break
            index = parent
        methodlist.reverse()

        self.__doc_field.setPlainText('')
        method = self.__object
        for m in methodlist:
            try:
                method = getattr(method, m)
            except:
                return

        if not hasattr(method, '__doc__'):
            return
        # ドキュメントの解析。
        text = self.analyzeDocument(method)
        self.__doc_field.setText(text)


class ConstructionOrderView(QtWidgets.QWidget):
    r"""
        Construtorの実行メソッドを実行順に表示するビューワー
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ConstructionOrderView, self).__init__(parent)
        note = uilib.ClosableGroup('Note')
        note.IconRect = QtCore.QRect(5, 10, 20, 20)
        note.setIcon(uilib.IconPath('uiBtn_edit'))
        note_text = QtWidgets.QLabel(
            'A construction order was defined by a variable "ProcessList" of'
            'the constructor class.\n'
            'You can change this order if you overwrite this variable.\n'
            'The variable is a list and requires '
            'a list of list that have 3 strings.\n'
            '"name of a method", '
            '"comment you want show before doing the process" '
            'and "comment you want show after done of the process.'
        )
        note_text.setWordWrap(True)
        layout = QtWidgets.QVBoxLayout(note)
        layout.addWidget(note_text)
        note.setExpanding(False)

        self.__view = ScriptHelper()
        self.__view.listCommands = self.listCommands

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(note)
        layout.addWidget(self.__view)
        layout.setStretchFactor(self.__view, 1)

    def listCommands(self, constructor):
        r"""
            ProcessListに則ったメソッドのリストを返す
            
            Args:
                constructor (constructor):
                
            Returns:
                list:
        """
        return [x[0] for x in constructor.ProcessList]

    def setObject(self, constructor):
        r"""
            constructorをセットし、プロセスオーダーを表示する
            
            Args:
                constructor (constructor):
        """
        if not hasattr(constructor, 'ProcessList'):
            return
        self.__view.setObject(constructor)


class ContextOption(factoryUI.ContextOption):
    r"""
        コンテキストメニューに表示するオプション
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ContextOption, self).__init__(parent)
        self.__current_file = ''
        self.__f_btn = uilib.OButton(uilib.IconPath('uiBtn_view'))
        self.__f_btn.setSize(48)
        self.__f_btn.setBgColor(25, 160, 98)
        self.__f_btn.setToolTip('Show function list')
        self.__f_btn.clicked.connect(self.showFunctionManager)

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.__f_btn)
        layout.addStretch()
        
        self.__f_btn.setEnabled(False)

    def refresh(self):
        r"""
            コンテキスト全体のリフレッシュを行う。
        """
        files = self.fileNames()
        self.__current_file = ''
        self.__f_btn.setEnabled(False)
        if not files or len(files) > 1:
            return
        file = os.path.join(self.path(), files[0])
        if not os.path.exists(file):
            return
        self.__current_file = file
        self.__f_btn.setEnabled(True)

    def showFunctionManager(self):
        if not os.path.isfile(self.__current_file):
            return
        w = scriptViewer.showWindow()
        w.main().setTargetModule(self.__current_file)
        self.hideContext()


class ConstructorOperator(QtWidgets.QTabWidget):
    r"""
        ビルド実行用のGUIを作成。
    """
    def __init__(self, parent=None):
        super(ConstructorOperator, self).__init__(parent)
        self.__ext_cst_utils = []

        # ビルド実行、デバッグモード実行用のGUI。==============================
        exec_commands = QtWidgets.QGroupBox('Operations')
        exe_btn = uilib.OButton(uilib.IconPath('uiBtn_play'))
        exe_btn.setSize(40)
        exe_btn.setBgColor(*uilib.Color.ExecColor)
        exe_label = QtWidgets.QLabel('Start to build')

        dbg_btn = uilib.OButton(uilib.IconPath('uiBtn_next'))
        dbg_btn.setSize(40)
        dbg_btn.setBgColor(*uilib.Color.DebugColor)
        
        self.__debug_level = QtWidgets.QComboBox()

        layout = QtWidgets.QGridLayout(exec_commands)
        layout.addWidget(exe_btn, 0, 0, 1, 1)
        layout.addWidget(exe_label, 0, 1, 1, 1)
        layout.addWidget(dbg_btn, 1, 0, 1, 1)
        layout.addWidget(self.__debug_level, 1, 1, 1, 1)
        layout.setRowStretch(2, 1)

        self.execButtonClicked = exe_btn.clicked
        self.debugButtonClicked = dbg_btn.clicked

        self.addTab(exec_commands, 'Build Operator')
        # =====================================================================
        
        # Extra Constructor Utility.===========================================
        ext_cst_util = QtWidgets.QScrollArea()
        ext_cst_util.setWidgetResizable(True)
        
        w = QtWidgets.QWidget()
        w.setObjectName('extCstOpWidget')
        w.setStyleSheet(
            'QWidget#extCstOpWidget{background-color: transparent;}'
        )
        self.__ext_cst_layout = QtWidgets.QVBoxLayout(w)

        ext_cst_util.setWidget(w)
        self.addTab(ext_cst_util, 'Extra Const Util')
        # =====================================================================
        
        self.currentChanged.connect(self.updateExtraConstUtil)

    def updateGui(self, debugModeList, extraConstructorUtils):
        self.__debug_level.clear()
        uilib.clearLayout(self.__ext_cst_layout)
        if debugModeList:
            self.__debug_level.addItems(debugModeList)
        self.__ext_cst_utils = extraConstructorUtils
        self.updateExtraConstUtil(self.currentIndex())

    def updateExtraConstUtil(self, index):
        if index != 1:
            return
        if not self.__ext_cst_utils:
            return
        for widget in self.__ext_cst_utils:
            self.__ext_cst_layout.addWidget(widget)
            widget.initialize()
        self.__ext_cst_utils = []

    def debugLevel(self):
        return self.__debug_level.currentText()


class ScriptManager(QtWidgets.QWidget, factoryModules.AbstractFactoryTabMixin):
    r"""
        メインGUI。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ScriptManager, self).__init__(parent)
        self.customInit()

        # ビルド実行用のモジュール一覧と、実行用のGUIを作成。==================
        self.__view = factoryUI.ModuleBrowserWidget()
        self.__view.setExtensions('py')
        self.__view.setCoordinator(coordinateFiles)
        self.__view.setVersionFormat('^(.*?)(\.|)(v\d+|)\.(%s)$')
        self.__view.setExtraContext(ContextOption)
        self.__view.clicked.connect(self.updateConstructorStats)
        self.__view.browser().setRootIsDecorated(False)

        self.__cst_op = ConstructorOperator()
        self.__cst_op.execButtonClicked.connect(self.executeScript)
        self.__cst_op.debugButtonClicked.connect(self.debugScript)

        exec_gui = QtWidgets.QSplitter()
        exec_gui.addWidget(self.__view)
        exec_gui.addWidget(self.__cst_op)
        exec_gui.setStretchFactor(1, 1)
        exec_gui.setSizes([300, 300])    
        # =====================================================================

        # スクリプトファイルとコマンドヘルパーの作成。=========================
        # ファイルの一覧とコンストラクタの実行メソッドの順序を表示するビュー
        from .. import func, node
        # コンストラクタのコマンドヘルプ
        self.__script_helper = ScriptHelper()
        # コンストラクタの実行順ビューワー
        self.__order_view = ConstructionOrderView()
        # funcのコマンドヘルプ
        func_helper = ScriptHelper()
        func_helper.setObject(func)
        # nodeモジュールの内部一覧
        node_helper = ScriptHelper()
        node_helper.setObject(node)
        # 選択ノードをPythonのリストに書式化するウィンドウ。
        from ..gadgets import selectedNodeList
        node_list = selectedNodeList.MainGUI()

        helper_tab = QtWidgets.QTabWidget()
        helper_tab.addTab(self.__script_helper, 'Constructor Commands')
        helper_tab.addTab(self.__order_view, 'Construction Order')
        helper_tab.addTab(func_helper, 'func Commands')
        helper_tab.addTab(node_helper, 'Node Classes')
        helper_tab.addTab(node_list, 'Node List')
        # =====================================================================

        splitter = QtWidgets.QSplitter()
        splitter.setOrientation(QtCore.Qt.Vertical)
        splitter.addWidget(exec_gui)
        splitter.addWidget(helper_tab)
        splitter.setSizes((200, 200))
        splitter.setStretchFactor(1, 1)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(splitter)

    def view(self):
        r"""
            ファイルを一覧するビューを返す。
            
            Returns:
                factoryUI.ModuleBrowserWidget:
        """
        return self.__view

    def scriptName(self):
        r"""
            スクリプトを格納しているディレクトリ名を返す。
            設定ファイルによって生成される。
            
            Returns:
                str:
        """
        fs = factoryModules.FactorySettings()
        return fs.assetPrefix()

    def refreshState(self):
        r"""
            AdvancedTabWidget内のこのウィジェットがアクティブになった
            時に更新をかける時に呼ばれるメソッド。
        """
        fs = factoryModules.FactorySettings()
        self.view().setPath(fs.subDirPath(self.scriptName()))

    def setup(self):
        r"""
            モジュールを読み込むための準備処理を行う。
            
            Returns:
                tuple:
        """
        import os, sys
        view = self.view()
        root_path = view.path()
        path, top_module = os.path.split(root_path)

        modules = view.selectedItems()
        if not modules:
            return (None, None)
        module = list(set([x.split('.')[0] for x in modules]))[0]

        if not path in sys.path:
            sys.path.append(path)
        return top_module, module

    def getConstructor(self, moduleName, isReload=False):
        r"""
            指定されたモジュールのコンストラクタクラスのインスタンス
            を返す。
            
            Args:
                moduleName (str):モジュール名
                isReload (bool):リロードするかどうか
                
            Returns:
                Constructor:
        """
        fs = factoryModules.FactorySettings()
        mod = lib.importModule(moduleName)
        if isReload:
            # print('Reload mod [%s] : %s [%s]' % (moduleName, mod,  type(mod)))
            verutil.reload_module(mod)
        if not hasattr(mod, 'Constructor'):
            raise NoConstructorError(
                'The object "{}" has no Constructor class.'
            )
        c = mod.Constructor()
        return c

    def listConstructorMethods(self, index):
        r"""
            コンストラクタのメソッドを下部のリストに表示する。
            
            Args:
                index (QtCore.QModelIndex):
        """
        top_module, module = self.setup()
        module_name = '%s.%s' % (top_module, module)
        import traceback
        try:
            constructor = self.getConstructor(module_name, True)
        except NoConstructorError:
            self.__script_helper.viewWarningRepots(
                '[WARNING] : No Cunstructor class.'
            )
            return
        except:
            error_report = '# Error in "{}"\n{}'.format(
                module_name, traceback.format_exc()
            )
            self.__script_helper.viewErrorReports(error_report)
            return
        self.__script_helper.setObject(constructor)
        self.__order_view.setObject(constructor)
        return constructor

    def updateConstructorStats(self, index):
        cst = self.listConstructorMethods(index)
        debug_mode_list = []
        ext_cst_utils = []
        if cst:
            if getattr(cst, 'listDebugModes'):
                debug_mode_list = cst.listDebugModes()
            ext_cst_utils = cst.extraConstructorUtilities()
        self.__cst_op.updateGui(debug_mode_list, ext_cst_utils)

    def executeModule(self, moduleName, debugMode):
        r"""
            モジュール(Constructor)を実行する。
            
            Args:
                moduleName (str):モジュール名
                debugMode (str):デバッグモードの内容。
        """
        c =self.getConstructor(moduleName, True)
        c.IsDebugMode = debugMode is not None
        c.DebugMode = debugMode
        c.execute()

    def execute(self, debugMode=None):
        r"""
            モジュール(Constructor)の実行準備を行い、その後executeModuleを
            呼び出す。
            
            Args:
                debugMode (str):デバッグモードの内容。
        """
        top_module, module = self.setup()
        if not top_module:
            return
        try:
            print('[Execute Module] : {}.{}'.format(top_module, module))
            self.executeModule(
                '{}.{}'.format(top_module, module), debugMode
            )
        except:
            lib.errorout()

    def executeScript(self):
        r"""
            選択されたスクリプトを実行するメソッド。
        """
        self.execute()

    def debugScript(self):
        r"""
            選択されたスクリプトをデバッグモードで実行するメソッド。
        """
        debug_level = self.__cst_op.debugLevel()
        self.execute(debug_level)

