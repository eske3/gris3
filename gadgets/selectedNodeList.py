# -*- coding: utf-8 -*-
r'''
    @file     selectedNodeList.py
    @brief    Mayaの選択ノードをPythonのリスト形式で書式化する機能を提供するモジュール。
    @class    TextMaker : ここに説明文を記入
    @class    MainGUI : メインウィンドウ機能を提供するウィジェット。
    @function showWindow : ウィンドウを表示する関数。基本的にはこれを呼び出す。
    @date        2017/01/22 0:01[Eske](eske3g@gmail.com)
    @update      2017/01/22 0:01[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
from gris3 import uilib
from gris3.uilib import mayaUIlib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore
from maya import cmds, OpenMayaUI

class TextMaker(object):
    r'''
        @brief       ここに説明文を記入
        @inheritance object
        @date        2017/01/22 0:01[Eske](eske3g@gmail.com)
        @update      2017/01/22 0:01[Eske](eske3g@gmail.com)
    '''
    AsSpace, AsTab = range(2)
    def __init__(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        self.__number_of_indent = 1
        self.__indent_type = self.AsSpace
        self.__number_of_spaces = 4
        self.__startquote = "'"
        self.__endquote = "'"
        self.__spacer = ','
        self.__space = ' '
        self.__limit = 80

    def setLimit(self, numberOfLimit):
        r'''
            @brief  ここに説明文を記入
            @param  numberOfLimit : [edit]
            @return None
        '''
        self.__limit = int(numberOfLimit)

    def limit(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return self.__limit

    def setStartQuote(self, quote):
        r'''
            @brief  ここに説明文を記入
            @param  quote : [edit]
            @return None
        '''
        self.__startquote = quote

    def startQuote(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return self.__startquote

    def setEndQuote(self, quote):
        r'''
            @brief  ここに説明文を記入
            @param  quote : [edit]
            @return None
        '''
        self.__endquote = quote

    def endQuote(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return self.__endquote

    def spacer(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return self.__spacer

    def space(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return self.__space

    def listed(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return cmds.ls(sl=True)

    def setNumberOfIndent(self, num):
        r'''
            @brief  ここに説明文を記入
            @param  num : [edit]
            @return None
        '''
        self.__number_of_indent = int(num)

    def numberOfIndent(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return self.__number_of_indent

    def setIndentType(self, indentType):
        r'''
            @brief  ここに説明文を記入
            @param  indentType : [edit]
            @return None
        '''
        if not indentType in (self.AsSpace, self.AsTab):
            raise ValueError(
                'The argument must be a following value : '
                '%(class)s.AsSpace or %(class)s.AsTab' % {
                    'class' : self.__name__,
                }
            )
        self.__indent_type = indentType
    def indentType(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return self.__indent_type

    def setNumberOfSpaces(self, num):
        r'''
            @brief  ここに説明文を記入
            @param  num : [edit]
            @return None
        '''
        self.__number_of_spaces = int(num)

    def numberOfSpaces(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return self.__number_of_spaces

    def makeText(self):
        # インデントのテンプレートを作成する。
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        if self.indentType() == self.AsSpace:
            indent = ' ' * self.numberOfSpaces()
        else:
            indent = '\t'
        indent *= self.numberOfIndent()

        # スペーサーに関する情報を取得する。
        spacer = self.spacer()
        space = self.space()

        limit = self.limit()
        slimit = limit - len(space)
        result_lines = []
        templine = indent
        sq = self.startQuote()
        eq = self.endQuote()
        just_finished = False

        for node in self.listed():
            additional = '%s%s%s%s' % (sq, node, eq, spacer)
            test = templine + additional
            if len(test) > slimit:
                result_lines.append(templine)
                templine = indent + additional
                continue
            templine = test

        if templine:
            result_lines.append(templine)
        return '\n'.join(result_lines)



class MainGUI(QtWidgets.QWidget):
    r'''
        @brief       メインウィンドウ機能を提供するウィジェット。
        @inheritance QtWidgets.QWidget
        @date        2017/01/22 0:01[Eske](eske3g@gmail.com)
        @update      2017/01/22 0:01[Eske](eske3g@gmail.com)
    '''
    def __init__(self, parent=None):
        r'''
            @brief  初期化関数。
            @param  parent(None) : [QWidget]親ウィジェット。
            @return None
        '''
        super(MainGUI, self).__init__(parent)
        self.__setting = TextMaker()

        # オプションのGUI。=========================================================
        option_group = QtWidgets.QGroupBox('Settings')
        
        # インデント設定。//////////////////////////////////////////////////////////
        # インデント数の設定。=======================================================
        indent_label = QtWidgets.QLabel('Number of Indent')
        self.indent_field = QtWidgets.QSpinBox()
        self.indent_field.setValue(1)
        self.indent_field.setRange(0, 100)
        # =====================================================================

        # インデントタイプの設定。=====================================================
        indent_type_label = QtWidgets.QLabel('Indent Type')
        indent_type_settings = QtWidgets.QWidget()
        indent_type_layout = QtWidgets.QHBoxLayout(indent_type_settings)
        indent_type_layout.setContentsMargins(2, 2, 2, 2)
        indent_space = QtWidgets.QRadioButton('Space')
        indent_space.setChecked(True)
        indent_tab = QtWidgets.QRadioButton('Tab')
        indent_type_layout.addWidget(indent_space)
        indent_type_layout.addWidget(indent_tab)

        self.indent_type_group = QtWidgets.QButtonGroup(indent_type_settings)
        self.indent_type_group.addButton(indent_space, 0)
        self.indent_type_group.addButton(indent_tab, 1)

        self.indent_space_num_label = QtWidgets.QLabel('Number of Spaces')
        self.indent_space_num = QtWidgets.QSpinBox()
        self.indent_space_num.setValue(4)
        self.indent_space_num.setRange(1, 9999)
        for widget in (self.indent_space_num, self.indent_space_num_label):
            self.indent_type_group.buttonClicked.connect(widget.setHidden)

        indent_group = QtWidgets.QGroupBox('Indent Settings')
        indent_layout = QtWidgets.QFormLayout(indent_group)
        indent_layout.addRow(indent_label, self.indent_field)
        indent_layout.addRow(indent_type_label, indent_type_settings)
        indent_layout.addRow(self.indent_space_num_label, self.indent_space_num)
        # =====================================================================
        # /////////////////////////////////////////////////////////////////////
        
        # 引用符の設定。//////////////////////////////////////////////////////////
        quote_group = QtWidgets.QGroupBox('Quote setting')
        start_quote_label = QtWidgets.QLabel('Start Quote')
        self.start_quote = QtWidgets.QLineEdit("'")
        end_quote_label = QtWidgets.QLabel('End Quote')
        self.end_quote = QtWidgets.QLineEdit("'")

        quote_layout = QtWidgets.QFormLayout(quote_group)
        quote_layout.addRow(start_quote_label, self.start_quote)
        quote_layout.addRow(end_quote_label, self.end_quote)
        # /////////////////////////////////////////////////////////////////////

        option_layout = QtWidgets.QHBoxLayout(option_group)
        option_layout.setContentsMargins(4, 0, 4, 4)
        option_layout.addWidget(indent_group)
        option_layout.addWidget(quote_group)

        exec_btn = QtWidgets.QPushButton('Make Text')
        exec_btn.clicked.connect(self.execute)

        self.result_field = QtWidgets.QTextEdit()

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(option_group)
        layout.addWidget(exec_btn)
        layout.addWidget(self.result_field)

    def execute(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        self.__setting.setNumberOfIndent(self.indent_field.value())
        self.__setting.setNumberOfSpaces(self.indent_space_num.value())
        self.__setting.setIndentType(
            self.indent_type_group.id(self.indent_type_group.checkedButton())
        )
        self.__setting.setStartQuote(self.start_quote.text())
        self.__setting.setEndQuote(self.end_quote.text())
        result = self.__setting.makeText()

        self.result_field.setPlainText(result)
        QtWidgets.QApplication.clipboard().setText(result)


def showWindow():
    r'''
        @brief  ウィンドウを表示する関数。基本的にはこれを呼び出す。
        @return MainGUI
    '''
    win = MainGUI(mayaUIlib.MainWindow)
    win.setWindowFlags(QtCore.Qt.Window)
    win.resize(600, 600)
    win.show()
    return win