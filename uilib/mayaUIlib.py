#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    mayaのGUIに関する機能を提供するクラス。
    
    Dates:
        date:2017/01/21 23:58 eske yoshinob[eske3g@gmail.com]
        update:2021/10/12 18:39 eske yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 eske yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from abc import ABCMeta, abstractmethod
from maya import cmds, mel
from maya.api import OpenMaya, OpenMayaUI
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from maya.OpenMayaUI import MQtUtil, M3dView

from . import directionPlane, paintApp
from .. import uilib, mathlib, node, lib, verutil
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore
if uilib.Package == 'PySide':
    import shiboken
elif uilib.Package == 'PySide2':
    import shiboken2 as shiboken
else:
    import shiboken6 as shiboken

MainWindow = shiboken.wrapInstance(
    verutil.Long(MQtUtil.mainWindow()), QtWidgets.QWidget
)

def beginCommand():
    r"""
        UndoのOpenChunkのラッパー関数
    """
    cmds.undoInfo(openChunk=True)

def endCommand():
    r"""
        UndoのCloseChunkのラッパー関数
    """
    cmds.undoInfo(closeChunk=True)


class DockableWidget(MayaQWidgetDockableMixin, QtWidgets.QWidget):
    r"""
        ドッキング可能ウィジェットを提供するクラス
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(DockableWidget, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        self.__main = self.centralWidget()
        layout.addWidget(self.__main)
        
    def show(self):
        r"""
            ドッキング可能ウィジェットを表示する
        """
        super(DockableWidget, self).show(dockable=True)

    @abstractmethod
    def centralWidget(self):
        r"""
            配置されるウィジェットを返すバーチャルメソッド。
            
            Returns:
                QtWidgets.QWidget:
        """
        raise NotImplementedError(
            'centralWidget　methods must be implemented.'
        )

    def main(self):
        r"""
            centralWidgetで作成されたウィジェットを返す。
            
            Returns:
                QtWidgets.QWidget:
        """
        return self.__main


class SingletonDockableMeta(uilib.QtSingletonMeta):
    def __call__(self, *args, **dict):
        r"""
            Args:
                *args (any):
                **dict (any):
        """
        obj = super(SingletonDockableMeta, self).__call__(*args, **dict)
        try:
            obj.windowFlags()
        except:
            pass
        return obj


class SingletonDockableWidget(
    SingletonDockableMeta('SingletonDockableWidget', DockableWidget)
):
    r"""
        ドッキング可能シングルトンウィジェットを提供するクラス
    """
    pass

# /////////////////////////////////////////////////////////////////////////////
# ディスプレイに関する関数。                                                 //
# /////////////////////////////////////////////////////////////////////////////
ViewRenderObjects = (
    M3dView.kDisplayNurbsSurfaces | M3dView.kDisplayMeshes
)

def write3dViewToFile(
    filepath, width=256, height=256, displayMask=ViewRenderObjects
):
    r"""
        アクティブなビューポートのキャプチャをQPixmapに変換する。
        内部的にはOpenMaya1.0を使用している。
        
        Args:
            filepath (str):書き出し先のパス
            width (int):横幅
            height (int):高さ
            displayMask (int):表示のフィルタ
    """
    from maya.OpenMaya import MImage
    view = M3dView.active3dView()
    old_display = view.objectDisplay()
    view.setObjectDisplay(displayMask)
    image = MImage()
    view.refresh()
    view.readColorBuffer(image, True)

    ext = filepath.rsplit('.', 1)[-1].lower()
    image.resize(width, height)
    image.writeToFile(filepath, ext)

    view.setObjectDisplay(old_display)
    view.refresh()
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////

def select(*nodelist, **flags):
    r"""
        任意のノードを選択する
        
        Args:
            *nodelist (tuple):選択するノードのリスト
            **flags (dict):cmds.selectに渡す引数
    """
    cmds.select(*nodelist, **flags)


def getActiveCamera(withView=False):
    r"""
        最後にアクティブだったカメラの名前を返す。
        withViewがTrueの場合、アクティブなビューオブジェクト
        (OpenMayaUI.M3dView)とカメラ名を、Falseの場合カメラ名のみを返す。
        
        Args:
            withView (bool):現在アクティブなビューも返すかどうか
            
        Returns:
            (str, OpenMayaUI.M3dView):
    """
    view = OpenMayaUI.M3dView.active3dView()
    dpath = view.getCamera()
    camera_name = dpath.fullPathName()
    return (camera_name, view) if withView else camera_name


def findPanelPopupParent():
    r"""
        Maya内製の同名関数のPython版
        
        Returns:
            str:
    """
    c = cmds.getPanel(up=True)
    if cmds.panel(c, q=True, ex=True):
        c = cmds.layout(c, q=True, p=True)
        while not (
            cmds.paneLayout(c, q=True, ex=True)
            or cmds.workspaceControl(c, q=True, ex=True)
        ):
            c = cmds.control(c, q=True, p=True)
        if (
            cmds.paneLayout(c, q=True, ex=True)
            or cmds.workspaceControl(c, q=True, ex=True)
        ):
            return c
    return 'viewPanes'


class MarkingMenuCreator(object):
    r"""
        標準フォーマットのマーキングメニューを作成するクラス
    """
    Positions = ('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW')

    def buildRadialMenu(self, position, optionMethod, parent):
        r"""
            ラジアルメニューを作成する
            
            Args:
                position (str):MarkingMenuCreator.Positionsのいずれか
                optionMethod (function):
                parent (str):親メニュー
        """
        option = optionMethod()
        option['p'] = parent
        option['rp'] = position
        cmds.menuItem(**option)

    def createLowerMenu(self, parent):
        r"""
            ジェスチャではない下段メニューを作成するためのメソッド
            
            Args:
                parent (str):[]親メニュー
        """
        pass

    def build(self, parent):
        r"""
            メニューを作成する。
            サブクラス内にoptionX(XはPositionsのいずれか)メソッドが書かれて
            いると、そのメソッドをbuildRadialMenuに渡してメニューが作成される。
            optionNメソッドは戻り値としてcmds.menuItemコマンドの引数を辞書で
            返す必要がある。
            
            Args:
                parent (str):親メニュー名
        """
        menu_names = [('option'+x, x) for x in self.Positions]
        methods = self.__class__.__dict__.keys()
        for method, pos in menu_names:
            if not method in methods:
                continue
            self.buildRadialMenu(pos, getattr(self, method), parent)
        self.createLowerMenu(parent)


class MarkingMenuWithTool(object):
    r"""
        マーキングメニューと何らかのツールを起動するクラス
    """
    MarkingMenuName = 'tempMM'
    LeftButton, MiddleButton, RightButton = range(1,4)
    def __new__(
        cls, button=1, startFunc=None, endFunc=None, menuCreator=None
    ):
        r"""
            シングルトン化を行う
            
            Args:
                button (int):反応するボタン（１～３）
                startFunc (function):メニュー表示前に呼ばれる関数
                endFunc (function):メニュー表示後に呼ばれる関数
                menuCreator (MarkingMenuCreator):メニュー作成用クラス
                
            Returns:
                MarkingMenuWithTool:
        """
        if hasattr(cls, '__singletoninstance__'):
            return cls.__singletoninstance__
        obj = super(MarkingMenuWithTool, cls).__new__(cls)
        obj.__menu_creator = menuCreator
        obj.__start_func = startFunc
        obj.__end_func = endFunc
        obj.__button = button
        obj.__menu_is_visible = False
        obj.__panel = None
        cls.__singletoninstance__ = obj
        return obj

    def setButton(self, button):
        r"""
            MMを起動するボタンをセットする。
            引数は
                MarkingMenuWithTool.LeftButton
                MiddleButton/RightButton
            のいずれか。
            
            Args:
                button (int):
        """
        if not button in (self.LeftButton, self.MiddleButton, self.RightButton):
            raise ValueError(
                'Button type must be a LeftButton, MiddleButton or RightButton.'
            )
        self.__button = button

    def createMenu(self, parent):
        r"""
            menuCreatorクラスのbuildを実行する。
            自前で作成したい場合はこのメソッドを上書きする。
            
            Args:
                parent (str):親メニューの名前
        """
        if not self.__menu_creator:
            return
        self.__menu_creator.build(parent)

    def execFunc(self, function):
        r"""
            関数をコールする。関数実行前にUndo制御を行っている
            
            Args:
                function (function):
        """
        if not function:
            return
        with node.DoCommand():
            function()

    def execStartFunc(self):
        r"""
            メニュー作成前関数を実行する
        """
        self.execFunc(self.__start_func)

    def execEndFunc(self):
        r"""
            メニューを閉じた時に呼ばれる関数を実行する
        """
        self.execFunc(self.__end_func)

    def showMenu(self):
        r"""
            MMを表示する。
        """
        self.__menu_is_visible = False
        parent = findPanelPopupParent()
        buttons = QtWidgets.QApplication.mouseButtons()
        modifiers = QtWidgets.QApplication.keyboardModifiers()

        # ポップアップメニュー作成用のオプション設定。
        options = {
            'mm':True, 'button':self.__button, 'p':parent,
            'pmc':self.setMenuIsVisible,
            'sh':0, 'ctl':0, 'alt':0,
        }
        if QtCore.Qt.ControlModifier == modifiers:
            options['ctl'] = 1
        elif QtCore.Qt.ShiftModifier == modifiers:
            options['sh'] = 1
        elif QtCore.Qt.AltModifier == modifiers:
            options['alt'] = 1

        temp_mm = self.MarkingMenuName
        if cmds.popupMenu(temp_mm, ex=True):
            cmds.deleteUI(temp_mm)
        self.execStartFunc()

        self.__panel = parent
        parent = cmds.popupMenu(temp_mm, **options)
        self.createMenu(parent)
        cmds.setParent('..', menu=True)

    def panel(self):
        r"""
            親パネルの名前を返す。
            
            Returns:
                str:
        """
        return self.__panel

    def setMenuIsVisible(self, *args):
        r"""
            メニューが表示された際に呼ばれる。
            
            Args:
                *args (tuple):
        """
        self.__menu_is_visible = True

    def command(self):
        r"""
            上書き用メソッド。MMが表示されない場合にコールされる。
        """
        pass

    def execute(self):
        r"""
            メニューが表示されない場合にコールする。
        """
        temp_mm = self.MarkingMenuName
        if cmds.popupMenu(temp_mm, ex=True):
            cmds.deleteUI(temp_mm)
        if not self.__menu_is_visible:
            self.command()

    def mel(self, command):
        r"""
            メニューの-cに渡すMelを登録する際に使用する便利メソッド
            
            Args:
                command (str):登録するmelコマンド
                
            Returns:
                function:
        """
        from functools import partial
        return partial(self.execMel, command)

    def execMel(self, command, *args):
        r"""
            melメソッドで登録されたmelコマンドを実行する
            
            Args:
                command (str):実行するmelコマンド
                *args (tuple):
        """
        mel.eval(command)


class DirectionPlaneWidget(directionPlane.DirectionView):
    r"""
        ビュー上で指示した方向を、Mayaのアクティブなビュー空間
        に変換したベクトルを渡すUIをを提供するクラス。
    """
    directionDecided = QtCore.Signal(
        mathlib.Axis, mathlib.Axis,
        QtCore.Qt.MouseButton, QtCore.Qt.KeyboardModifiers
    )
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(DirectionPlaneWidget, self).__init__(parent)
        self.directionChanged.connect(self.done)

    def done(self, vector, start, end, mouseButton, modifiers):
        r"""
            与えられたベクトルに対して、ワールド空間行列を作成する。
            
            Args:
                vector (list):入力方向を表すベクトル
                start (any):
                end (any):
                mouseButton (int):押されているマウスボタンを表す整数
                modifiers (int):押されている修飾キーを表す整数
        """
        # アクティブなカメラを取得する。=======================================
        camera = getActiveCamera()
        if cmds.nodeType(camera) == 'camera':
            camera = cmds.listRelatives(camera, p=True, pa=True)[0]
        # =====================================================================

        vector_mtx = mathlib.FMatrix()
        vector_mtx.setTranslate(*vector)
        
        # ビューポートの方向を指し示す行列を生成する。
        cam_dir_mtx = mathlib.FMatrix()
        cam_dir_mtx.setTranslate(0, 0, -1)

        # アクティブなカメラ空間上でのワールドベクターを生成する。
        cam_mtx = mathlib.FMatrix(
            cmds.xform(camera, q=True, ws=True, m=True)
        )
        cam_mtx.setTranslate(0, 0, 0)
        vector_mtx *= cam_mtx
        cam_dir_mtx *= cam_mtx

        # X,Y,Z軸と比較し、最終的な軸を決定する。==============================
        result = []
        for matrix in (vector_mtx, cam_dir_mtx):
            result.append(mathlib.Axis(matrix))
        # =====================================================================

        self.directionDecided.emit(
            result[0], result[1], mouseButton, modifiers
        )


class DrawerOnCamera(paintApp.DesktopCanvas):
    def __init__(self, parent=None, screenNumber=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
                screenNumber (int):デスクトップのスクリーン番号
        """
        self.__camera, self.__view = getActiveCamera(True)
        super(DrawerOnCamera, self).__init__(parent, screenNumber)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setMemoryDrawingHistory(True)
        self.drawingFinished.connect(self.memoryDrawingData)
        self.setBrushColor(80, 168, 255)
        self.__draw_data = []

    def isValid(self):
        return self.__isvalid

    def cameraName(self):
        r"""
            描画時に使用したカメラシェイプの名前を返す。
            
            Returns:
                str:
        """
        return self.__camera

    def cameraMatrix(self):
        r"""
            描画時に使用したカメラのワールド空間での行列を返す。
            
            Returns:
                list:
        """
        return cmds.xform(
            cmds.listRelatives(self.cameraName(), p=True, pa=True),
            q=True, ws=True, m=True
        )

    def cameraAimVector(self):
        r"""
            描画時に使用したカメラのワールド空間での視線方向ベクトルを返す。
            
            Returns:
                list:
        """
        return self.cameraMatrix()[8:11]

    def view(self):
        r"""
            クラスのインスタンス作成時に取得したカメラのM3dViewを返す。
            
            Returns:
                OpenMaya.M3dView:
        """
        return self.__view

    def viewWidget(self):
        view = self.view()
        return shiboken.wrapInstance(
            verutil.Long(view.widget()), QtWidgets.QWidget
        )        

    def editCanvas(self, image, imageRect, desktopRect):
        r"""
        キャンパスのQImageを作成した後に、後編集を行う。
        
        Args:
            image (QtGui.QImage):編集対象となるQImage
            imageRect (QtCore.QRect):渡されたQImageの矩形情報
            desktopRect (QtCore.QRect):使用するデスクトップの矩形情報
            
        Returns:
            QtGui.QImage:
    """
        view = self.viewWidget()
        pos = view.mapToGlobal(view.pos())
        self.__isvalid = desktopRect.contains(pos)

        geo = view.geometry()
        geo.moveTopLeft(pos)
        
        full_path = QtGui.QPainterPath()
        full_path.addRect(imageRect)
        sub_path = QtGui.QPainterPath()
        sub_path.addRect(geo)
        full_path -= sub_path

        painter = QtGui.QPainter(image)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(0, 0, 0, 120))
        painter.drawPath(full_path)
        return image

    def memoryDrawingData(self):
        r"""
            描画情報をインスタンス内に保持する。
        """
        his = self.drawingHistories()
        if not his:
            self.reject()
        
        view = self.view()
        view_widget = self.viewWidget()
        w = view_widget.width()
        h = view_widget.height()
        p = OpenMaya.MPoint()
        v = OpenMaya.MVector()
        draw_data = []
        for pos, size in his[0]:
            l_pos = view_widget.mapFromGlobal(pos)
            view.viewToWorld(l_pos.x(), h - l_pos.y(), p, v)
            draw_data.append((list(p)[:-1], list(v)))
        self.__draw_data = draw_data
        self.accept()
        self.execute()

    def drawData(self, referencePosition=False):
        r"""
            描画情報をリストにして返す。
            返ってくる描画情報は引数referencePositionによって変化する。
            referencePositionがFalseの場合、戻り値は描画座標カメラ空間での
            描画位置を表すためのワールド位置とその地点を指すための
            ベクトルをセットで持つリストになる。
            referencePositionがワールド空間座標の場合、戻り値はその座標を
            中心とした各描画位置のワールド座標を持つlistとなる。
            
            Args:
                referencePosition (list or tuple):
                
            Returns:
                list:
        """
        if not referencePosition:
            return [x for x in self.__draw_data]
        if (
            not isinstance(referencePosition, (list, tuple)) or
            len(referencePosition) != 3
        ):
            raise ValueError(
                'The given argument must be list or tuple '
                'that includes 3 float values.'
            )
        # プロットする対象となる平面の位置とベクトル。=========================
        x = OpenMaya.MVector(referencePosition)
        n = OpenMaya.MVector(self.cameraAimVector())
        h = n * x
        # =====================================================================

        poslist = []
        for data in self.__draw_data:
            x0, m = [OpenMaya.MVector(d) for d in data]
            p = x0 + ((h - n*x0)/(n*m))*m
            poslist.append(list(p))
        return poslist

    def drawVectorData(self, referencePosition):
        r"""
            描画時の各サンプルポイントをワールド空間に変換した座標、
            次のサンプルポイントへのベクトル、開始地点からの距離を持つ
            tupleオブジェクトを持つリストを返す。
            引数referencePositionにはワールド空間での基準点を表す3つのfloatを
            持つリストを渡す必要がある。
            
            Args:
                referencePosition (list or tuple):
                
            Returns:
                list:(OpenMaya.MVector, OpenMaya.MVector, float)
        """
        positions = self.drawData(referencePosition)
        positions.insert(0, referencePosition)
        datalist = []
        total_len = 0
        start = OpenMaya.MVector(positions[0])
        for i in range(len(positions)-1):
            next = OpenMaya.MVector(positions[i+1])
            v = next - start
            datalist.append((start, v.normal(), total_len))
            total_len += v.length()
            start = next
        return datalist

    def preCheck(self):
        pass

    def execute(self):
        r"""
            描画作業終了後に実行される上書き専用メソッド。
        """
        pass

    def mousePressEvent(self, event):
        r"""
            Args:
                event (QtCore.QEvent):
        """
        if (
            event.modifiers() == QtCore.Qt.NoModifier and
            event.button() == QtCore.Qt.RightButton
        ):
            self.close()
            return
        super(DrawerOnCamera, self).mousePressEvent(event)
        

def createEventJob(command, eventType='SelectionChanged'):
    r"""
        イベントドリブンのスクリプトジョブを作成する。
        
        Args:
            command (function):イベント時に呼ばれる関数
            eventType (str):イベントタイプ。デフォルトはSelectionChanged
            
        Returns:
            int:作成されたイベントID
    """
    return cmds.scriptJob(e=(eventType, command))


def killJob(jobId):
    r"""
        任意の番号のスクリプトジョブを削除する
        
        Args:
            jobId (int):ジョブ番号
    """
    cmds.scriptJob(k=jobId)


class Framerange(QtWidgets.QWidget):
    r"""
        フレームレンジを設定するためのGUIを提供するクラス。
    """    
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(Framerange, self).__init__(parent)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(uilib.ZeroMargins)
        self.__ui = {}
        for l in ('start', 'end'):
            self.__ui[l] = QtWidgets.QSpinBox()
            self.__ui[l].setRange(-10000000, 10000000)
            self.__ui[l].setMinimumWidth(40)
            label = QtWidgets.QLabel(lib.title(l))
            label.setMinimumWidth(10)
            layout.addWidget(label)
            layout.setAlignment(label, QtCore.Qt.AlignRight)
            layout.addWidget(self.__ui[l])
        self.setFramerange(0, 100)
        
        set_btn = QtWidgets.QPushButton('Set frame from range')
        set_btn.clicked.connect(self.setFrameFromRange)
        layout.addWidget(set_btn)

    def framerange(self):
        r"""
            このUIに設定されている開始・終了フレームを返す。
            
            Returns:
                list:開始フレーム、終了フレーム
        """    
        return [self.__ui[x].value() for x in ('start', 'end')]

    def setFramerange(self, start, end):
        r"""
            開始・終了フレームを設定する。

            Args:
                start (int):開始フレーム
                end (int):終了フレーム
        """
        for l, v in (('start', start), ('end', end)):
            self.__ui[l].setValue(v)

    def setFrameFromRange(self):
        r"""
            MayaのフレームレンジUIから開始・終了フレームを設定する。
        """    
        start = int(cmds.playbackOptions(q=True, min=True))
        end = int(cmds.playbackOptions(q=True, max=True))
        self.setFramerange(start, end)


class NodePicker(QtWidgets.QWidget):
    r"""
        ノードを選択するための機能を提供するクラス。
    """
    SingleSelection, MultiSelection = list(range(2))
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(NodePicker, self).__init__(parent)
        
        self.__name_editor = QtWidgets.QLineEdit()
        self.__name_editor.setReadOnly(True)
        self.__node_types = []
        self.__nodelist = []
        self.__selection_options = {}
        self.__pickmode = self.MultiSelection
        
        pick_btn = uilib.OButton()
        pick_btn.setIcon(uilib.IconPath('uiBtn_select'))
        pick_btn.setBgColor(70, 120, 165)
        pick_btn.clicked.connect(self.pickSelectedNode)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.__name_editor)
        layout.setAlignment(self.__name_editor, QtCore.Qt.AlignBottom)
        layout.addWidget(pick_btn)
        layout.setAlignment(pick_btn, QtCore.Qt.AlignBottom)

    def setPickMode(self, mode):
        self.__pickmode = mode

    def pickMode(self):
        return self.__pickmode
    
    def setNodeTypes(self, *nodeTypes):
        self.__node_types = list(nodeTypes)

    def nodeTypes(self):
        return self.__node_types

    def setSelectionOptions(self, **options):
        self.__selection_options = {x:y for x, y in options.items()}

    def selectionOptions(self):
        return self.__selection_options

    def pickSelectedNode(self):
        r"""
            シーン中で選択されているノード名をフィールドに表示する。
        """
        extra_options = self.selectionOptions()
        node_types = self.nodeTypes()
        if node_types:
            extra_options['type'] = node_types
        selected = node.selected(**extra_options)
        if not selected:
            self.__nodelist = []
            self.__name_editor.setText('')
            return
        self.__nodelist = [x() for x in selected]
        if self.pickMode() == self.SingleSelection:
            self.__nodelist = [self.__nodelist[0]]
        self.__name_editor.setText(', '.join(self.__nodelist))

    def data(self):
        r"""
            フィールドに入っている文字列を返す。
        """
        return self.__nodelist
