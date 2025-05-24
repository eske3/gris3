# -*- coding: utf-8 -*-
#, *- coding: utf-8, *-
r'''
    @file     attributeEditorMM.py
    @brief    アトリビュートエディタの表示と各種ウィンドウのMMを表示する
    @class    MarkingMenu : マーキングメニューの定義
    @date        2018/03/05 23:38[Eske](eske3g@gmail.com)
    @update      2018/04/15 4:37[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
from maya import cmds, mel
from gris3.uilib import mayaUIlib

class MarkingMenu(mayaUIlib.MarkingMenuWithTool):
    r'''
        @brief       マーキングメニューの定義
        @inheritance mayaUIlib.MarkingMenuWithTool
        @date        2018/03/08 1:14[Eske](eske3g@gmail.com)
        @update      2018/04/15 4:37[Eske](eske3g@gmail.com)
    '''
    def createMenu(self, parent):
        r'''
            @brief  ここに説明文を記入
            @param  parent : [edit]
            @return None
        '''
        cmds.menuItem(
            l='Component Editor...', rp='N', p=parent,
            c=self.mel('ComponentEditor')
        )
        cmds.menuItem(
            l='Connection Editor...', rp='NW', p=parent,
            c=self.showCustomConnectionEditor
        )
        cmds.menuItem(
            l='Attribute Spread Sheet...', rp='NE', p=parent,
            c=self.mel('SpreadSheetEditor')
        )
        cmds.menuItem(
            l='Delete Attribute...', rp='SE', p=parent,
            c=self.mel('DeleteAttribute')
        )
        cmds.menuItem(
            l='Add Attribute...', rp='S', p=parent,
            c=self.mel('AddAttribute')
        )
        cmds.menuItem(
            l='Rename Attribute...', rp='SW', p=parent,
            c=self.mel('RenameAttribute')
        )
        cmds.menuItem(
            l='Channel Control...', rp='W', p=parent,
            c=self.mel('ChannelControlEditor')
        )
        
        cmds.menuItem(
            l='Toggle Transform Channels', rp='E', p=parent,
            c=self.toggleTransformChannel
        )

    def command(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        mel.eval(
            'if(`isAttributeEditorVisible`){setChannelBoxVisible(1); }'
            'else{openAEWindow;}'
        )

    def toggleTransformChannel(self, *args):
        r'''
            @brief  ここに説明文を記入
            @param  *args : [edit]
            @return None
        '''
        from gris3.tools import operationHelper
        with operationHelper.node.DoCommand():
             operationHelper.toggleTransformChannel()

    def showCustomConnectionEditor(self, *args):
        r'''
            @brief  ここに説明文を記入
            @param  *args : [edit]
            @return None
        '''
        from gris3.gadgets.oldModules import connectionEditor
        connectionEditor.MainWindow().show()



