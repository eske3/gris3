#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    与えられた名前を任意のルールに則って要素分解し、再度リネームするための
    機能を提供するモジュール。
    派生モジュールを作成する場合はこのモジュールのAbstractRenamerEngineクラスを
    継承する。

    Dates:
        date:2025/05/11 01:47 Eske Yoshinob[eske3g@gmail.com]
        update:2025/05/11 07:24 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2025 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from collections import OrderedDict
from . import editorBlocks
from ... import uilib, system
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

# from importlib import reload
# reload(editorBlocks)

class AbstractRenamerEngine(QtWidgets.QWidget):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(AbstractRenamerEngine, self).__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        self.__editor_blocks = OrderedDict()

    def installEditorBlock(self, label, editorType):
        r"""
            Args:
                label (any):
                editorType (any):
        """
        if label in self.__editor_blocks:
            return
        block = editorType(label)
        self.layout().addWidget(block)
        self.__editor_blocks[label] = block
        return block

    def addSeparator(self):
        separator = QtWidgets.QLabel('_')
        separator.setAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignHCenter)
        self.layout().addWidget(separator)

    def getEditorBlock(self, label):
        r"""
            Args:
                label (any):
        """
        return self.__editor_blocks.get(label, None)
    
    def setFocusToBlock(self, index):
        r"""
            任意の番号の編集ブロックへフォーカスを移す。

            Args:
                index (int):
        """
        blocks = list(self.__editor_blocks.values())
        if index > len(blocks):
            return
        blocks[index].setFocusToEditor()
        

    def analyzeName(self, nodeName, fullPathName):
        r"""
            名前を受け取り、その名前を元にGUIを更新する。
            上書き専用メソッド。
            
            Args:
                nodeName (str):
                fullPathName (str):
        """
        pass
    
    def makeName(self):
        r"""
            UI情報から新しい名前を生成し返すメソッド。
            上書き専用メソッド。
            
            Returns:
                str:
        """
        return ''


class BasicRenamerEngine(AbstractRenamerEngine):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(BasicRenamerEngine, self).__init__(parent)
        self.installEditorBlock('basename', editorBlocks.LineEditorBlock)
        self.installEditorBlock('suffix', editorBlocks.LineEditorBlock)
        self.addSeparator()
        self.installEditorBlock(
            'nodeType', editorBlocks.EditableComboBoxBlock
        )
        self.addSeparator()
        pl = self.installEditorBlock('position', editorBlocks.ComboBoxBlock)
        plist = system.BasicNameRule.positionList()
        plist[0] = ''
        pl.addItems(plist)

    def analyzeName(self, nodeName, fullPathName):
        r"""
            名前を受け取り、その名前を元にGUIを更新する。
            
            Args:
                nodeName (str):
                fullPathName (str):
        """
        name = nodeName
        suffix = ''
        node_type = ''
        position = ''
        
        import re
        ptn = re.compile('\d+$')
        if ptn.search(nodeName):
            judged_name = ptn.sub('', nodeName)
        else:
            judged_name = nodeName
        
        try:
            name_obj = system.BasicNameRule(judged_name)
            name = name_obj.name()
            suffix = name_obj.suffix()
            node_type = name_obj.nodeType()
            position = name_obj.position()
        except Exception:
            pass
        if not position:
            position = ''
        _basename = self.getEditorBlock('basename')
        _suffix = self.getEditorBlock('suffix')
        _nodetype = self.getEditorBlock('nodeType')
        _position = self.getEditorBlock('position')
        _basename.setText(name)
        _suffix.setText(suffix)
        _nodetype.setText(node_type)
        _position.setCurrentItem(position)

    def makeName(self):
        _basename = self.getEditorBlock('basename')
        _suffix = self.getEditorBlock('suffix')
        _nodetype = self.getEditorBlock('nodeType')
        _position = self.getEditorBlock('position')
        name_obj = system.BasicNameRule()
        name_obj.setName(_basename.text())
        name_obj.setSuffix(_suffix.text())
        name_obj.setNodeType(_nodetype.text())
        name_obj.setPosition(_position.text())
        return name_obj()


BasicDataTable = OrderedDict({
    'geometry': OrderedDict({
        'geo':[], 'crv':['nurbsCurve']
    }),
    'transform': OrderedDict({'grp':[], 'jnt':['joint']}),
    'lambert': OrderedDict({
        'mat':[], 'png': ['phong'], 'bln':['blinn'], 'lbt':['lambert'], 
    }),
    'sets': OrderedDict({'sg': ['shadingEngine']}),
})


class BasicProductionEngine(BasicRenamerEngine):

    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(BasicProductionEngine, self).__init__(parent)
        nt = self.getEditorBlock('nodeType')
        keys = []
        for keylist in BasicDataTable.values():
            keys.extend(keylist.keys())
        nt.addItems(keys)

    def analyzeName(self, nodeName, fullPathName):
        r"""
            Args:
                nodeName (str):
                fullPathName (str):
        """
        def getNodeType(t, key):
            r"""
                Args:
                    t (str):
                    key (str):
            """
            table = BasicDataTable[key]
            for key, val in table.items():
                if t in val:
                    return key
            default = [x for x, y in table.items() if not y]
            if not default:
                raise RuntimeError(
                    'The given table is invalid : {}'.format(table)
                )
            return default[0]

        def judgeTransformType(basename, suffix, obj):
            r"""
                Args:
                    basename (str):
                    suffix (str):
                    obj (node.Transform):
            """
            shapes = obj.shapes()
            if basename.endswith('Geo'):
                basename = basename[:-3]
            if not shapes:
                # グループであると推察される場合。
                suffix = 'Geo'
                return basename, suffix, 'grp'
            # ジオメトリと推察される場合。
            shape = shapes[0]
            return basename, suffix, getNodeType(shape.type(), 'geometry')
            
        super(BasicProductionEngine, self).analyzeName(nodeName, fullPathName)
        from ... import node
        obj = node.asObject(fullPathName)
        if not obj:
            return
        _basename = self.getEditorBlock('basename')
        t = obj.type()
        typelist = node.cmds.nodeType(obj, i=True)
        node_type = ''
        suffix = ''
        basename = _basename.text()

        if 'lambert' in typelist:
            # マテリアルだった場合の振り分け
            node_type = getNodeType(t, 'lambert')
        elif t == 'transform':
            # トランスフォーム系だった場合の振り分け
            basename, suffix, node_type = judgeTransformType(
                basename, suffix, obj
            )
        elif t == 'joint':
            node_type = 'jnt'
        elif t == 'shadingEngine':
            node_type = 'sg'
        if not node_type:
            return
        _basename.setText(basename)
        self.getEditorBlock('nodeType').setText(node_type)
        self.getEditorBlock('suffix').setText(suffix)




