# -*- coding: utf-8 -*-
r'''
    @file     extraJointEditor.py
    @brief    ジョイントの編集機能を提供するGUI。
    @class    ExtraJointCreator : ExtraJointを作成するウィジェット。
    @class    Editor : ExtraJointを編集するためのボタンを提供するクラス。
    @class    ExtraJointEditor : ジョイントの作成、編集を行うためのツールを提供するクラス。
    @class    MainGUI : ここに説明文を記入
    @function showWindow : ウィンドウを作成するためのエントリ関数。
    @date        2017/06/15 16:35[Eske](eske3g@gmail.com)
    @update      2017/08/20 2:19[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
from gris3.tools import extraJoint
from gris3 import lib, uilib, node
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore
Exec_Color = (64, 72, 150)


class ExtraJointCreator(uilib.ClosableGroup):
    r'''
        @brief       ExtraJointを作成するウィジェット。
        @inheritance uilib.ClosableGroup
        @date        2017/06/22 17:51[s_eske](eske3g@gmail.com)
        @update      2017/08/20 2:19[Eske](eske3g@gmail.com)
    '''
    def __init__(self, parent=None):
        r'''
            @brief  初期化を行う。
            @param  parent(None) : [QtWidgets.QWidget]
            @return None
        '''
        super(ExtraJointCreator, self).__init__('Creator', parent)
        self.setWindowTitle('Extra Joint Creator')

        # ベースの名前を指定するフィールド。
        b_label = QtWidgets.QLabel('Base Name')
        self.__basename = QtWidgets.QLineEdit()

        # ノードのタイプを選択するコンボボックス。=============================
        t_label = QtWidgets.QLabel('Node Type')
        self.__type_box = QtWidgets.QComboBox()
        self.__type_box.addItems(('joint', 'transform'))
        # =====================================================================

        # 位置を表す文字列を指定するコンボボックス。===========================
        p_label = QtWidgets.QLabel('Position')
        self.__pos_box = QtWidgets.QComboBox()
        # =====================================================================

        # ベースの名前を指定するフィールド。
        n_label = QtWidgets.QLabel('Node Type Label')
        self.__nodetype = QtWidgets.QLineEdit('bndJnt')

        # 作成ボタン。=========================================================
        crt_btn = uilib.OButton()
        crt_btn.setIcon(uilib.IconPath('uiBtn_plus'))
        crt_btn.setSize(48)
        crt_btn.setBgColor(*Exec_Color)
        crt_btn.setToolTip('Create Extra Joint')
        crt_btn.clicked.connect(self.createExtraJoint)
        # =====================================================================


        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(b_label, 0, 0, 1, 1)
        layout.addWidget(self.__basename, 0, 1, 1, 3)
        layout.addWidget(t_label, 1, 0, 1, 1)
        layout.addWidget(self.__type_box, 1, 1, 1, 1)
        layout.addWidget(p_label, 1, 2, 1, 1)
        layout.addWidget(self.__pos_box, 1, 3, 1, 1)
        layout.addWidget(crt_btn, 0, 4, 2, 1)
        layout.addWidget(n_label, 2, 0, 1, 1)
        layout.addWidget(self.__nodetype, 2, 1, 1, 1)
        
        for l in (b_label, t_label, p_label, n_label):
            layout.setAlignment(l, QtCore.Qt.AlignRight)

    def setPositionList(self, positionList=None, defaultIndex=2):
        r'''
            @brief  位置を表す文字列のリストをセットする。
            @param  positionList(None) : [list]
            @param  defaultIndex(2) : [int]最初に選択されている番号。
            @return None
        '''
        if not positionList:
            from gris3 import system
            positionList = system.GlobalSys().positionList()
            defaultIndex = 2
        self.__pos_box.clear()
        self.__pos_box.addItems(positionList)
        self.__pos_box.setCurrentIndex(defaultIndex)

    def createExtraJoint(self):
        r'''
            @brief  ジョイントを新規で作成する。
            @return None
        '''
        basename = self.__basename.text()
        nodetype = self.__type_box.currentText()
        nodetype_label = self.__nodetype.text()
        position = self.__pos_box.currentIndex()

        with node.DoCommand():
            extraJoint.create(
                basename, nodetype, nodetype_label, position,
                offset=0
            )

class Editor(QtWidgets.QGroupBox):
    r'''
        @brief       ExtraJointを編集するためのボタンを提供するクラス。
        @inheritance QtWidgets.QGroupBox
        @date        2017/08/20 2:18[Eske](eske3g@gmail.com)
        @update      2017/08/20 2:19[Eske](eske3g@gmail.com)
    '''
    def __init__(self, parent=None):
        r'''
            @brief  初期化を行う。
            @param  parent(None) : [QtWidgets.QWidget]
            @return None
        '''
        super(Editor, self).__init__('Edit Extra Joints', parent)
        layout = QtWidgets.QHBoxLayout(self)
        
        for color, icon, tooltip, cmd in (
            (
                 (12, 65, 160),
                'uiBtn_select',
                'Select extra joints under the selected nodes',
                self.selectExtraJoints
            ),
            (
                 (49, 115, 154),
                'uiBtn_mirrorJoints',
                'Create mirrored extra joints from selected.',
                self.mirror
            ),
        ):
            btn = uilib.OButton()
            btn.setIcon(uilib.IconPath(icon))
            btn.setSize(48)
            btn.setBgColor(*color)
            btn.setToolTip(tooltip)
            btn.clicked.connect(cmd)
            layout.addWidget(btn)
        layout.addStretch()

    def selectExtraJoints(self):
        r'''
            @brief  選択ノード下の全てのExtraJointを選択する。
            @return None
        '''
        with node.DoCommand():
            extraJoint.selectExtraJoint()

    def mirror(self):
        r'''
            @brief  選択されたExtraJointのミラーを作成する。
            @return None
        '''
        with node.DoCommand():
            extraJoint.createMirroredJoint()


class ExtraJointEditor(QtWidgets.QWidget):
    r'''
        @brief       ジョイントの作成、編集を行うためのツールを提供するクラス。
        @inheritance QtWidgets.QWidget
        @date        2017/07/01 4:07[Eske](eske3g@gmail.com)
        @update      2017/08/20 2:19[Eske](eske3g@gmail.com)
    '''
    def __init__(self, parent=None):
        r'''
            @brief  初期化を行う。
            @param  parent(None) : [QtWidgets.QWidget]
            @return None
        '''
        super(ExtraJointEditor, self).__init__(parent)
        self.setWindowTitle('+Extra Joint Editor')
        builder = ExtraJointCreator()
        self.setPositionList = builder.setPositionList
        
        editor = Editor()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(builder)
        layout.addWidget(editor)
        layout.addStretch()


class MainGUI(uilib.AbstractSeparatedWindow):
    r'''
        @brief       ここに説明文を記入
        @inheritance uilib.AbstractSeparatedWindow
        @date        2017/06/27 18:31[s_eske](eske3g@gmail.com)
        @update      2017/08/20 2:19[Eske](eske3g@gmail.com)
    '''
    def centralWidget(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return ExtraJointEditor()

    def show(self):
        r'''
            @brief  ウィジェットを表示する。その際位置リストを更新する。
            @return None
        '''
        eje = self.main()
        eje.setPositionList()
        super(MainGUI, self).show()


def showWindow():
    r'''
        @brief  ウィンドウを作成するためのエントリ関数。
        @return QtWidgets.QWidget
    '''
    from gris3.uilib import mayaUIlib
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(400, 350)
    widget.show()
    return widget