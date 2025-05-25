#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    モデリング用補助ツール群を提供するガジェット
    
    Dates:
        date:2017/07/06 5:35[Eske](eske3g@gmail.com)
        update:2020/10/12 15:09 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from gris3.tools import modelingSupporter
from gris3.uilib import mayaUIlib
from gris3 import lib, uilib, node
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore
Exec_Color = (64, 72, 150)


class AllGroupCreator(QtWidgets.QWidget):
    r"""
        モデルを格納するall_grpを作成するためのGUIを提供するクラス
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget): 親ウィジェット
        """
        super(AllGroupCreator, self).__init__(parent)
        
        add_btn = uilib.OButton()
        add_btn.setToolTip('Create all_grp for model')
        add_btn.setIcon(uilib.IconPath('uiBtn_plus'))
        add_btn.setBgColor(*Exec_Color)
        add_btn.setSize(32)
        add_btn.clicked.connect(self.createAllGroup)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(add_btn)
        layout.addWidget(QtWidgets.QLabel('Create all_grp'))

    def createAllGroup(self):
        r"""
            all_grpを作成する。
        """
        from gris3 import core
        with node.DoCommand():
            core.createModelRoot()


class PolyEditor(QtWidgets.QGroupBox):
    r"""
        ポリゴン編集用の便利機能を提供するGUI
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(PolyEditor, self).__init__('Edit Polygons', parent)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(1)

        for data in (
            (
                (148, 166, 28), 'Combine selected polygons.',
                'uiBtn_polyCombine',
                self.combine
            ),
            10,
            (
                (96, 28, 211), 'Extract a selected faces.',
                'uiBtn_extractFace',
                self.extractSelectedFaces
            ),
            (
                (128, 22, 211), 'Duplicate a selected faces.',
                'uiBtn_duplicateFace',
                self.duplicateSelectedFaces
            ),
            10,
            (
                (24, 164, 148), 'Boolean(Union) selected polygons.',
                'uiBtn_polyBoolUnion',
                self.boolUnion
            ),
            (
                (24, 144, 188), 'Boolean(Difference) selected polygons.',
                'uiBtn_polyBoolDifference',
                self.boolDifference
            ),
            (
                (24, 124, 228), 'Boolean(Intersection) selected polygons.',
                'uiBtn_polyBoolIntersection',
                self.boolIntersection
            ),
        ):
            if isinstance(data, int):
                layout.addSpacing(data)
                continue
            color, ann, icon, method = data
            button = uilib.OButton()
            button.setIcon(uilib.IconPath(icon))
            button.setBgColor(*color)
            button.setToolTip(ann)
            button.clicked.connect(method)
            button.setSize(38)
            layout.addWidget(button)
        layout.addStretch()

    def combine(self):
        r"""
            コンバインを行う
        """
        with node.DoCommand():
            modelingSupporter.Combine().operate()

    def boolUnion(self):
        r"""
            結合ブーリアンを実行する
        """
        with node.DoCommand():
            modelingSupporter.Boolean('union').operate()

    def boolDifference(self):
        r"""
            差分ブーリアンを実行する
        """
        with node.DoCommand():
            modelingSupporter.Boolean('difference').operate()

    def boolIntersection(self):
        r"""
            ブーリアンのインターセクションを実行する
        """
        with node.DoCommand():
            modelingSupporter.Boolean('intersection').operate()

    def extractSelectedFaces(self):
        r"""
            選択フェースを分離する
        """
        with node.DoCommand():
            modelingSupporter.extractPolyFace(False)

    def duplicateSelectedFaces(self):
        r"""
            選択フェースを複製する
        """
        with node.DoCommand():
            modelingSupporter.extractPolyFace(True)
        

class AbstractMirrorToolOption(QtWidgets.QGroupBox):
    r"""
        ミラーツール用のポストアクションを設定するGUIを提供する抽象クラス。
    """
    def __init__(self, postAction, *args, **keywords):
        r"""
            Args:
                postAction (modelingSupporter.AbstractPostAction):
                *args (tuple):
                **keywords (dict):
        """
        if not isinstance(postAction, modelingSupporter.AbstractPostAction):
            raise RuntimeError(
                'setupAction method must return a inheritance of '
                'modelingSupporter.AbstractPostActiona'
            )
        super(AbstractMirrorToolOption, self).__init__(*args, **keywords)
        self.__post_action = postAction

    def postAction(self):
        r"""
            このクラスが有するpostActionオブジェクトを返す。
            
            Returns:
                modelingSupporter.AbstractPostAction:
        """
        return self.__post_action

    def setupAction(self, action):
        r"""
            postActionにセットアップを行う。
            
            Args:
                action (modelingSupporter.AbstractPostAction):
        """
        pass

    def getAction(self):
        r"""
            このクラスが持つPostActionをセットアップしてから返す。
            
            Returns:
                modelingSupporter.AbstractPostAction:
        """
        post_action = self.postAction()
        self.setupAction(post_action)
        return post_action


class MirrorToolTrsOption(AbstractMirrorToolOption):
    r"""
        ミラー後のTransformノードに対する処理を定義するGUI。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(MirrorToolTrsOption, self).__init__(
            modelingSupporter.TransformPostAction(),
            'Transform Option', parent
        )

        layout = QtWidgets.QGridLayout(self)

        row = 0
        column = 0
        width = 1
        self.__buttons = []
        for attr, label in zip(
            ('t', 'r', 's', 'pn'),
            ('Translate', 'Rorate', 'Scale', 'PreserveNormal'),
        ):
            checkbox = QtWidgets.QCheckBox(label)
            checkbox.setChecked(True)
            self.__buttons.append(checkbox)
            layout.addWidget(
                checkbox, row, column, 1, width
            )
            column += 1
            if column > 2:
                column = 0
                row += 1
                width = 2

    def setupAction(self, action):
        r"""
            GUIの情報からpostActionをセットアップする。
            
            Args:
                action (modelingSupporter.AbstractPostAction):
        """
        flags = eval(
            '0b'+''.join(
                ['1' if x.isChecked() else '0' for x in self.__buttons]
            )
        )
        action.setFlags(flags)


class MirrorToolRenameOption(AbstractMirrorToolOption):
    r"""
        ミラー後のリネーム処理を定義するGUI。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        action, label = self.setupData()
        super(MirrorToolRenameOption, self).__init__(action, label, parent)
        self.__search_edit = QtWidgets.QLineEdit('_L')
        self.__replace_edit = QtWidgets.QLineEdit('_R')

        layout = QtWidgets.QFormLayout(self)
        layout.addRow(QtWidgets.QLabel('Search for'), self.__search_edit)
        layout.addRow(QtWidgets.QLabel('Replace with'), self.__replace_edit)

    def setupData(self):
        r"""
            サブクラス用の再実装メソッド。
            postActionのインスタンスとラベルを返す。
            
            Returns:
                tuple:
        """
        return (modelingSupporter.RenamePostAction(), 'Rename Option')

    def setupAction(self, action):
        r"""
            GUIの情報からpostActionをセットアップする。
            
            Args:
                action (modelingSupporter.AbstractPostAction):
        """
        action.setSearchingText(self.__search_edit.text())
        action.setReplacingText(self.__replace_edit.text())


class MirrorToolParentOption(MirrorToolRenameOption):
    r"""
        ミラー後のペアレント処理を定義するGUI。
    """
    def setupData(self):
        r"""
            parent用postActionとラベルを返す。
            
            Returns:
                tuple:
        """
        return (modelingSupporter.ParentPostAction(), 'Parent Option')


class MirrorTool(uilib.ClosableGroup):
    r"""
        オブジェクトをミラーリングする機能を提供するクラス。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(MirrorTool, self).__init__('Mirror Tool', parent)
        self.setIcon(uilib.IconPath('uiBtn_mirror'))
        self.__mirror_util = modelingSupporter.MirrorObjectUtil()
        self.__options = []
        self.__plane = None
        self.__selected = []

        # インタラクティブドラッグによるミラー用GUI。==========================
        mirror_view = mayaUIlib.DirectionPlaneWidget()
        mirror_view.setText(
            'Left Button : World\n'
            'Middle Button : Bounding Box\n'
            'Right Button : Bounding Box of All Objects'
        )
        mirror_view.directionDecided.connect(self.mirror)
        
        plane_mode_btn = QtWidgets.QPushButton('Use Plane')
        plane_mode_btn.clicked.connect(self.swithPlaneMode)

        view_widget = QtWidgets.QWidget()
        view_layout = QtWidgets.QVBoxLayout(view_widget)
        view_layout.setSpacing(0)
        view_layout.setContentsMargins(0, 0, 0, 0)
        view_layout.addWidget(mirror_view)
        view_layout.addWidget(plane_mode_btn)
        # =====================================================================
        
        # プレーンによるミラー用GUI。==========================================
        self.__plane_name = QtWidgets.QLineEdit()

        plane_dir = mayaUIlib.DirectionPlaneWidget()
        plane_dir.setText('Drag here to dicide a plane direction.')
        plane_dir.directionDecided.connect(self.setPlaneDirection)
        
        mirror_btn = QtWidgets.QPushButton('Mirror')
        mirror_btn.clicked.connect(self.mirrorByPlane)
        ccl_btn = QtWidgets.QPushButton('Cancel')
        ccl_btn.clicked.connect(self.returnViewMode)

        plane_widget = QtWidgets.QWidget()
        plane_layout = QtWidgets.QGridLayout(plane_widget)
        plane_layout.setContentsMargins(0, 0, 0, 0)
        plane_layout.addWidget(self.__plane_name, 0, 0, 1, 2)
        plane_layout.addWidget(plane_dir, 1, 0, 1, 2)
        plane_layout.addWidget(mirror_btn, 2, 0, 1, 1)
        plane_layout.addWidget(ccl_btn, 2, 1, 1, 1)
        plane_layout.setRowStretch(1, 1)
        # =====================================================================

        self.__stacked = QtWidgets.QStackedWidget()
        self.__stacked.addWidget(view_widget)
        self.__stacked.addWidget(plane_widget)

        layout = QtWidgets.QGridLayout(self)
        layout.setSpacing(2)

        for i, option in enumerate(
            (
                MirrorToolTrsOption, MirrorToolRenameOption,
                MirrorToolParentOption
            )
        ):
            widget = option()
            layout.addWidget(widget, i, 1, 1, 1)
            self.__options.append(widget)

        layout.addWidget(self.__stacked, 0, 0, i+1, 1)

    def mirrorWith(self, modifiers=None):
        r"""
            呼び出した時のキーボードの修飾キーの状態に応じてミラー対象
            のモードを返す。
            
            Args:
                modifiers (int):押されている修飾キー
                
            Returns:
                int:
        """
        modifiers = (
            QtWidgets.QApplication.keyboardModifiers()
            if modifiers is None
            else modifiers
        )
        if modifiers == QtCore.Qt.ControlModifier:
            return 1
        elif modifiers == QtCore.Qt.ShiftModifier:
            return 2
        else:
            return 0

    def swithPlaneMode(self):
        r"""
            プレーンを使用したミラーモードへ移行する。
        """
        self.__selected = modelingSupporter.node.selected(type='transform')
        if not self.__selected:
            raise RuntimeError('No transformable object selected.')

        if self.__plane:
            if not self.__plane.exists():
                self.__plane = None
        if not self.__plane:
            self.__plane = self.__mirror_util.createMirrorPlane()
        self.__plane.select()
        self.__plane_name.setText(self.__plane())

        self.__stacked.setCurrentIndex(1)

    def returnViewMode(self):
        r"""
            ドラッグプレーンを使用したミラーモードへ移行する。
        """
        self.__selected = []
        self.__stacked.setCurrentIndex(0)

    def doMirror(self, targets=None):
        r"""
            ミラーリングを行う。
            
            Args:
                targets (list):ミラーリング対象ノードのリスト
        """
        post_actions = [x.getAction() for x in self.__options]
        self.__mirror_util.setPostActions(*post_actions)
        
        with node.DoCommand():
            self.__mirror_util.mirror(targets)

    def mirror(self, axisA, axisB, button, modifiers):
        r"""
            ミラーリングを行う。
            
            Args:
                axisA (str):描画軸をワールド空間に変換した軸
                axisB (str):カメラの向いている軸
                button (int):押されたボタン
                modifiers (int):押された修飾キー
        """
        self.__mirror_util.setMirrorAxis(axisA[1])
        self.__mirror_util.setMirrorWith(self.mirrorWith(modifiers))

        use_bb = self.__mirror_util.NoBoundingBox
        if button == QtCore.Qt.MiddleButton:
            if axisA[0] == '-':
                use_bb = self.__mirror_util.Minimum
            else:
                use_bb = self.__mirror_util.Maximum
        elif button == QtCore.Qt.RightButton:
            if axisA[0] == '-':
                use_bb = self.__mirror_util.MinimumForAll
            else:
                use_bb = self.__mirror_util.MaximumForAll

        self.__mirror_util.setMirrorPivotMatrix()
        self.__mirror_util.useBoundingBox(use_bb)
        self.doMirror()

    def setPlaneDirection(self, axisA, axisB, button, modifiers):
        r"""
            プレーンの方向を設定する
            
            Args:
                axisA (str):描画軸をワールド空間に変換した軸
                axisB (str):カメラの向いている軸
                button (int):押されたボタン
                modifiers (int):押された修飾キー
        """
        self.__mirror_util.setPlaneDirection(
            self.__plane_name.text(), axisA[1]
        )

    def mirrorByPlane(self):
        r"""
            ミラー軸定義プレーンによるミラーリングを実行する。
        """
        
        self.__mirror_util.setMirrorAxis('z')
        self.__mirror_util.setMirrorWith(self.mirrorWith())
        p = self.__mirror_util.setMirrorPivotByNode(self.__plane_name.text())
        self.__mirror_util.useBoundingBox(self.__mirror_util.NoBoundingBox)
        self.doMirror(self.__selected)
        p.delete()
        self.returnViewMode()


class PolyHalfRemover(mayaUIlib.DirectionPlaneWidget):
    r"""
        任意の軸の半分側のフェイスを削除する。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(PolyHalfRemover, self).__init__(parent)
        self.setWindowTitle(self.label())
        self.setText(self.helpText())
        self.directionDecided.connect(self.doIt)

    def label(self):
        r"""
            ラベルを返す
            
            Returns:
                str:
        """
        return '+Poly Half Remover'

    def helpText(self):
        r"""
            フィールド内に表示するヘルプテキストを返す
            
            Returns:
                str:
        """
        return (
            'Left Button : World\n'
            'Middle Button : Pivot\n'
            'Right Button : Object Center\n'
            'Ctrl : Pivot (Local)'
        )

    def getAxis(self, button):
        r"""
            状況に応じたオプション文字列を返す。
            
            Args:
                button (QtCore.Qt.MouseButton):
                
            Returns:
                str:
        """
        if button == QtCore.Qt.MiddleButton:
            return 'pivot'
        elif button == QtCore.Qt.RightButton:
            return 'center'
        else:
            return 'world'

    def doIt(self, axisA, axisB, button, modifiers):
        r"""
            削除を実行する。
            
            Args:
                axisA (str):描画軸をワールド空間に変換した軸
                axisB (str):カメラの向いている軸
                button (int):押されたボタン
                modifiers (int):押された修飾キー
        """
        if modifiers == QtCore.Qt.ControlModifier:
            base_axis = 'local'
        else:
            base_axis = self.getAxis(button)
        modelingSupporter.removePolyFaceOnHalf(axisA, base_axis)


class PolyMirror(PolyHalfRemover):
    r"""
        ミラージオメトリを実行する。
    """
    Direction = {
        '+x' : 0, '-x' : 1, '+y' : 2, '-y' : 3, '+z' : 4, '-z' : 5
    }
    def label(self):
        r"""
            ラベルを返す
            
            Returns:
                str:
        """
        return '+Mirror Geometry'

    def helpText(self):
        r"""
            フィールド内に表示するヘルプテキストを返す
            
            Returns:
                str:
        """
        return (
            'Left Button : World\n'
            'Middle Button : Pivot\n'
            'Right Button : Bounding Box'
        )

    def doIt(self, axisA, axisB, button, modifiers):
        r"""
            ミラーリングを実行する
            
            Args:
                axisA (str):描画軸をワールド空間に変換した軸
                axisB (str):カメラの向いている軸
                button (int):押されたボタン
                modifiers (int):押された修飾キー
        """
        modelingSupporter.mirrorGeometry(
            axis=self.Direction[axisA], baseAxis=self.getAxis(button)
        )


class PolyMirrorEditor(uilib.ClosableGroup):
    r"""
        ポリゴンのミラーリング機能を集めたグループ
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(PolyMirrorEditor, self).__init__('Poly Mirror Editor', parent)
        
        half_cut_view = PolyHalfRemover()
        mirror_view = PolyMirror()
        
        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(
            QtWidgets.QLabel(half_cut_view.windowTitle()), 0, 0, 1, 1,
            QtCore.Qt.AlignLeft
        )
        layout.addWidget(half_cut_view, 1, 0, 1, 1)
        layout.addWidget(
            QtWidgets.QLabel(mirror_view.windowTitle()), 0, 1, 1, 1,
            QtCore.Qt.AlignLeft
        )
        layout.addWidget(mirror_view, 1, 1, 1, 1)


class PolyCutGeometry(PolyHalfRemover):
    r"""
        ミラージオメトリを実行する。
    """
    def label(self):
        r"""
            ラベルを返す
            
            Returns:
                str:
        """
        return '+Cut Polygon'

    def helpText(self):
        r"""
            フィールド内に表示するヘルプテキストを返す
            
            Returns:
                str:
        """
        return ''

    def doIt(self, axisA, axisB, button, modifiers):
        r"""
            ミラーリングを実行する
            
            Args:
                axisA (str):描画軸をワールド空間に変換した軸
                axisB (str):カメラの向いている軸
                button (int):押されたボタン
                modifiers (int):押された修飾キー
        """
        vec_axis = axisA[1]
        cam_axis = axisB[1]
        if (
                (vec_axis=='x' and cam_axis=='z') or
                (vec_axis=='z' and cam_axis=='x')
            ):
            operation = 'y'
        elif (
                (vec_axis=='y' and cam_axis == 'z') or
                (vec_axis=='z' and cam_axis == 'y')
            ):
            operation = 'x'
        else:
            operation = 'z'
        with node.DoCommand():
            modelingSupporter.cutGeometry(operation=operation)


class PolyCutEditor(uilib.ClosableGroup):
    r"""
        ポリゴンのカット機能を集めたグループ
    """
    def __init__(self, parent=None):
        r"""
            初期化を行う
            
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(PolyCutEditor, self).__init__('Poly Cut Editor', parent)

        cut_view = PolyCutGeometry()
        
        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(cut_view, 0, 0, 1, 1)


class SelectedVertexPicker(QtWidgets.QWidget):
    r"""
        選択されているバーテックスをフィールドに登録するGUI
        を提供するクラス。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget): 親ウィジェット
        """
        super(SelectedVertexPicker, self).__init__(parent)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.__field = QtWidgets.QLineEdit()
        self.__field.setReadOnly(True)
        self.__field.returnPressed.connect(self.selectVertices)
        self.__field.setToolTip(
            'Hit return key, then select a registered vertices in this field.'
        )
        pick_btn = uilib.OButton()
        pick_btn.setIcon(uilib.IconPath('uiBtn_select'))
        pick_btn.setBgColor(70, 120, 165)
        pick_btn.clicked.connect(self.pickSelectedVertices)

        layout.setSpacing(1)
        layout.addWidget(self.__field)
        layout.addWidget(pick_btn)
        
        self.__vertslist = []

    def pickSelectedVertices(self):
        r"""
            選択されたバーテックスをフィールドへ登録する。
        """
        self.__vertslist = modelingSupporter.getSekectedComponents()
        self.__field.setText(', '.join(self.__vertslist))

    def vertexList(self):
        r"""
            登録されているバーテックスのリストを返す。
            
            Returns:
                list:
        """
        return self.__vertslist

    def selectVertices(self):
        r"""
            フィールドに登録されているバーテックスを選択する
        """
        vertices = self.vertexList()
        if not vertices:
            return
        node.cmds.select(vertices)


class FitVtsToClosestVts(uilib.ClosableGroup):
    r"""
        任意の頂点を最近接頂点へくっつける機能を提供する
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(FitVtsToClosestVts, self).__init__(
            'Fit Vts to closest Vts', parent
        )
        layout = QtWidgets.QGridLayout(self)
        layout.setVerticalSpacing(1)

        src_label = QtWidgets.QLabel('Source Vertices')
        self.__src_picker = SelectedVertexPicker()
        tgt_label = QtWidgets.QLabel('Target Vertices')
        self.__tgt_picker = SelectedVertexPicker()
        
        set_btn = uilib.OButton()
        set_btn.setIcon(uilib.IconPath('uiBtn_play'))
        set_btn.setSize(36)
        set_btn.setBgColor(64, 72, 150)
        set_btn.clicked.connect(self.fitVertices)

        layout.addWidget(src_label, 0, 0, 1, 1)
        layout.addWidget(self.__src_picker, 0, 1, 1, 1)
        layout.addWidget(tgt_label, 1, 0, 1, 1)
        layout.addWidget(self.__tgt_picker, 1, 1, 1, 1)
        layout.addWidget(set_btn, 0, 2, 2, 1)

    def fitVertices(self):
        r"""
            フィールドに登録差れているバーテックスをくっつける処理を行う。
        """
        src = self.__src_picker.vertexList()
        tgt = self.__tgt_picker.vertexList()
        if not src or not tgt:
            return
        with node.DoCommand():
            modelingSupporter.moveToClosestVtx(src, tgt)


class ModelSetupWidget(QtWidgets.QWidget):
    r"""
        モデルデータの作成、チェックを行う機能を提供するクラス
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(ModelSetupWidget, self).__init__(parent)
        self.setWindowTitle('+Model Setup')
        creator = AllGroupCreator()
        editor = PolyEditor()
        mirror_tool = MirrorTool()
        mirror_tool.setExpanding(False)
        
        poly_mirror = PolyMirrorEditor()
        poly_mirror.setExpanding(False)
        
        poly_cutter = PolyCutEditor()
        poly_cutter.setExpanding(False)
        
        fit_to_closest = FitVtsToClosestVts()
        fit_to_closest.setExpanding(False)
        
        from . import objectFlatter
        flatter = objectFlatter.ObjectFlatter()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(creator)
        layout.addWidget(editor)
        layout.addWidget(mirror_tool)
        layout.addWidget(poly_mirror)
        layout.addWidget(poly_cutter)
        layout.addWidget(fit_to_closest)
        layout.addWidget(flatter)
        layout.addStretch()


class MainGUI(uilib.AbstractSeparatedWindow):
    r"""
        メインとなるGUIを提供するクラス
    """
    def centralWidget(self):
        r"""
            中心となるメインウィジェットを作成して返す
            
            Returns:
                ModelSetupWidget:
        """
        return ModelSetupWidget()


class PolyHalfRemoverWidget(uilib.AbstractSeparatedWindow):
    r"""
        任意の軸でポリゴンフェースを削除するGUIを提供するクラス。
    """
    def centralWidget(self):
        r"""
            中心となるメインウィジェットを作成して返す
            
            Returns:
                PolyHalfRemover:
        """
        self.setHiddenTrigger(self.HideByCursorOut)
        self.resize(uilib.hires(200), uilib.hires(220))
        self.setScalable(False)
        return PolyHalfRemover()


class PolyMirrorWidget(uilib.AbstractSeparatedWindow):
    r"""
        任意の軸でもポリゴンをミラーリングする機能を提供するクラス
    """
    def centralWidget(self):
        r"""
            中心となるメインウィジェットを作成して返す
            
            Returns:
                PolyMirror:
        """
        self.setHiddenTrigger(self.HideByCursorOut)
        self.resize(uilib.hires(200), uilib.hires(220))
        self.setScalable(False)
        return PolyMirror()


class PolyCutWidget(uilib.AbstractSeparatedWindow):
    r"""
        ポリゴンを任意の軸でカットする機能を提供するクラス
    """
    def centralWidget(self):
        r"""
            中心となるメインウィジェットを作成して返す
            
            Returns:
                PolyCutGeometry:
        """
        self.setHiddenTrigger(self.HideByCursorOut)
        self.resize(uilib.hires(250), uilib.hires(250))
        self.setScalable(False)
        return PolyCutGeometry()

    def buildUI(self):
        r"""
            GUI作成を行う
        """
        super(PolyCutWidget, self).buildUI()
        titlebar = self.layout().itemAt(0).widget()
        titlebar.setSpacing(1)
        for icon, color, method in (
            ('uiBtn_option', (39, 88, 175), self.openOption),
            ('uiBtn_toolBox', (39, 88, 175), self.execCutTool),
            ('uiBtn_ctrl', (39, 125, 160), self.execCutToolManip)
        ):
            optbtn = uilib.OButton(uilib.IconPath(icon))
            optbtn.setBgColor(*color)
            optbtn.clicked.connect(method)
            titlebar.addWidgetToEnd(optbtn)

    def openOption(self):
        r"""
            カット機能のオプションを表示する
        """
        self.close()
        from maya import mel
        mel.eval('CutPolygonOptions;')

    def execCutTool(self):
        r"""
            カット機能(CutPolygon)を実行する
        """
        self.close()
        from maya import mel
        mel.eval('CutPolygon;')

    def execCutToolManip(self):
        r"""
            マニピュレータ付きカット機能を実行する。
        """
        with node.DoCommand():
            modelingSupporter.cutToolManipulator()


def showPolyHalfRemover():
    r"""
        PolyHalfRemoverWidgetを起動する
        
        Returns:
            PolyHalfRemoverWidget:
    """
    widget = PolyHalfRemoverWidget(mayaUIlib.MainWindow)
    widget.show()
    return widget


def showPolyMirror():
    r"""
        PolyMirrorWidgetを起動する
        
        Returns:
            PolyMirrorWidget:
    """
    widget = PolyMirrorWidget(mayaUIlib.MainWindow)
    widget.show()
    return widget


def showPolyCutter():
    r"""
        PolyCutWidgetを起動する
        
        Returns:
            PolyCutWidget:
    """
    widget = PolyCutWidget(mayaUIlib.MainWindow)
    widget.show()
    return widget


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。
        
        Returns:
            QtWidgets.QWidget:
    """
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(uilib.hires(450), uilib.hires(450))
    widget.show()
    return widget
