# -*- coding: utf-8 -*-
r'''
    @file     extendedUI.py
    @brief    通常のQtウィジェットに使いやすい機能を追加した拡張クラスを
    @brief    提供するモジュール。
    @class    FilteredView : 表示のフィルタ機能付きのViewを提供するクラス。
    @class    EasyMovableSplitter : addWidgetAsHandleで追加したウィジェットがスプリッタハンドルの
    @class    DirectionaalPlaneLine : 方向を提示するためのラインを描画するアイテム。
    @class    DirectionalOperator : QGraphicsViewのオペレーションを行う機能を提供するクラス。
    @class    DirectionView : 方向指示をするためのビューを提供するクラス。
    @date        2017/01/21 23:58[Eske](eske3g@gmail.com)
    @update      2019/01/01 18:42[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
from gris3 import uilib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore

# フィルター表示可能なビュー機能。
class FilteredView(QtWidgets.QWidget):
    r'''
        @brief       表示のフィルタ機能付きのViewを提供するクラス。
        @brief       フィルタに使用するViewを作成するcreateViewメソッドと、
        @brief       そのviewが取り扱うmodelを定義するcreateModelメソッド
        @brief       はヴァーチャルなので必ず再実装する必要がある。
        @inheritance QtWidgets.QWidget
        @date        2018/11/03 5:33[Eske](eske3g@gmail.com)
        @update      2019/01/01 18:42[Eske](eske3g@gmail.com)
    '''
    def __init__(self, parent=None):
        r'''
            @brief  初期化を行う
            @param  parent(None) : [QtWidgets.QWidget]親ウィジェット
            @return None
        '''
        super(FilteredView, self).__init__(parent)
        self.__tool_was_run = False
        self.__selected = 0

        model = self.createModel()
        proxy = QtCore.QSortFilterProxyModel()
        proxy.setFilterKeyColumn(self.filterKeyColumn())
        proxy.setRecursiveFilteringEnabled(True)
        proxy.setSourceModel(model)

        sel_model = QtCore.QItemSelectionModel(proxy)

        self.__view = self.createView()
        self.__view.setModel(proxy)
        self.__view.setSelectionModel(sel_model)
        self.__view.installEventFilter(self)

        self.__field = QtWidgets.QLineEdit()
        self.__field.hide()
        self.__field.installEventFilter(self)
        self.__field.textChanged.connect(self.setFilterToView)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        layout.addWidget(self.__view)
        layout.addWidget(self.__field)

    @uilib.abstractmethod
    def createView(self):
        r'''
            @brief  再実装用メソッド。任意のViewを作成し返す。
            @return (QTreeView/QListView/QTableView)
        '''
        pass

    @uilib.abstractmethod
    def createModel(self):
        r'''
            @brief  再実装用メソッド。任意のItemModeloを作成し返す。
            @return QStandardItemModel
        '''
        pass

    def filterKeyColumn(self):
        r'''
            @brief  SortFilterのキーとなるカラム番号を返す。デフォルトは0
            @return int
        '''
        return 0

    def view(self):
        r'''
            @brief  一覧表示用のViewを返す
            @return QtWidgets.QTreeView
        '''
        return self.__view

    def setFilterToView(self, text):
        r'''
            @brief  ビューの表示フィルタを有効にする
            @param  text : [str]フィルタ文字列
            @return None
        '''
        reg_exp = QtCore.QRegExp(
            text, QtCore.Qt.CaseInsensitive, QtCore.QRegExp.Wildcard
        )
        proxy = self.view().model()
        proxy.setFilterRegExp(reg_exp)

    def eventFilter(self, obj, event):
        r'''
            @brief  イベントフィルタの再実装メソッド
            @param  obj : [QtCore.QObject]
            @param  event : [QtCore.QEvent]
            @return None
        '''
        if event.type() != QtCore.QEvent.KeyPress:
            return False
        key = event.key()
        if obj == self.__field:
            # フィルタ入力フィールド内での操作の場合
            if key == QtCore.Qt.Key_Escape:
                self.__field.hide()
                self.view().setFocus(QtCore.Qt.ShortcutFocusReason)
                self.setFilterToView('')
                return True
            return False
        # それ以外の場合
        if key == QtCore.Qt.Key_Tab:
            self.__field.show()
            self.__field.setFocus(QtCore.Qt.ShortcutFocusReason)
            # self.__field.keyPressEvent(event)
            return True
        return False


class EasyMovableSplitter(QtWidgets.QSplitter):
    r'''
        @brief       addWidgetAsHandleで追加したウィジェットがスプリッタハンドルの
        @brief       代わりを果たすようになる拡張QSplitter。
        @inheritance QtWidgets.QSplitter
        @date        2017/01/21 23:58[Eske](eske3g@gmail.com)
        @update      2019/01/01 18:42[Eske](eske3g@gmail.com)
    '''
    def __init__(self, parent=None):
        r'''
            @brief  ここに説明文を記入
            @param  parent(None) : [edit]
            @return None
        '''
        super(EasyMovableSplitter, self).__init__(parent)
        self.setPrePosition()

    def prePosition(self):
        r'''
            @brief  ドラッグ時
            @return None
        '''
        return self.__pre_pos

    def setPrePosition(self, position=None):
        r'''
            @brief  ここに説明文を記入
            @param  position(None) : [edit]
            @return None
        '''
        self.__pre_pos = position
        
    def addWidget(self, widget):
        r'''
            @brief  ここに説明文を記入
            @param  widget : [edit]
            @return None
        '''
        super(EasyMovableSplitter, self).addWidget(widget)
        for i in range(self.count()):
            self.handle(i).setEnabled(False)

    def addWidgetAsHandle(self, widget):
        r'''
            @brief  ここに説明文を記入
            @param  widget : [edit]
            @return None
        '''
        self.addWidget(widget)
        widget.installEventFilter(self)

    def eventFilter(self, obj, event):
        r'''
            @brief  ここに説明文を記入
            @param  obj : [edit]
            @param  event : [edit]
            @return None
        '''
        event_type = event.type()
        if (
            event_type == QtCore.QEvent.MouseButtonPress and
            event.button() == QtCore.Qt.LeftButton
        ):
            self.setPrePosition(event.globalPos())
            return True
        elif event_type == QtCore.QEvent.MouseMove and self.prePosition():
            pos = event.globalPos()
            delta = pos - self.prePosition()
            index = self.indexOf(obj)
            sizes = self.sizes()

            offset = 1 if index < len(sizes)  - 1 else -1
            moved = (
                (
                    delta.x()
                    if self.orientation() == QtCore.Qt.Horizontal
                    else delta.y()
                )
                * offset
            )
            sizes[index] += moved
            sizes[index + offset] -= moved
                
            self.setSizes(sizes)

            self.setPrePosition(pos)
            return True
        elif event_type == QtCore.QEvent.MouseButtonRelease:
            self.setPrePosition()
            return True
        return False
        

# /////////////////////////////////////////////////////////////////////////////
# スクリーン上でドラッグする事によりラインを描画して方向を確定               //
# させるためのウィジェット。                                                 //
# /////////////////////////////////////////////////////////////////////////////
class DirectionaalPlaneLine(QtWidgets.QGraphicsPathItem):
    r'''
        @brief       方向を提示するためのラインを描画するアイテム。
        @inheritance QtWidgets.QGraphicsPathItem
        @date        2017/06/27 18:56[s_eske](eske3g@gmail.com)
        @update      2019/01/01 18:42[Eske](eske3g@gmail.com)
    '''
    Color = QtGui.QColor(130, 122, 240)
    def __init__(self, scene, parent=None):
        r'''
            @brief  初期化を行う。
            @param  scene : [QtWidgets.QGraphicsScene]
            @param  parent(None) : [QtWidgets.QWidget]
            @return None
        '''
        super(DirectionaalPlaneLine, self).__init__(parent, scene)
        self.setPen(QtGui.QPen(self.Color, 2))
        self.setBrush(QtGui.QBrush(QtCore.Qt.NoBrush))
        self.setZValue(1)
        self.__start = QtCore.QPointF(0, 0)
        self.__end = QtCore.QPointF(0, 0)

    def setStart(self, pos):
        r'''
            @brief  スタート位置を設定する。
            @param  pos : [QtCore.QPointF]
            @return None
        '''
        self.__start = pos
    def start(self):
        r'''
            @brief  セットされているスタート位置を返す。
            @return QtCore.QPointF
        '''
        return self.__start

    def setEnd(self, pos):
        r'''
            @brief  終端位置を設定する。
            @param  pos : [QtCore.QPointF]
            @return None
        '''
        self.__end = pos
    def end(self):
        r'''
            @brief  セットされている終端位置を返す。
            @return QtCore.QPointF
        '''
        return self.__end

    def updatePath(self):
        r'''
            @brief  パスの描画をアップデートする。
            @return None
        '''
        path = QtGui.QPainterPath()
        path.moveTo(self.start())
        path.lineTo(self.end())
        self.setPath(path)

class DirectionalOperator(QtCore.QObject):
    r'''
        @brief       QGraphicsViewのオペレーションを行う機能を提供するクラス。
        @inheritance QtCore.QObject
        @date        2017/06/27 18:56[s_eske](eske3g@gmail.com)
        @update      2019/01/01 18:42[Eske](eske3g@gmail.com)
    '''
    directionChanged = QtCore.Signal(list, int)
    StartMarkerSize = 10
    def __init__(self, view):
        r'''
            @brief  初期化を行う。
            @param  view : [QtWidgets.QGraphicsView]
            @return None
        '''
        super(DirectionalOperator, self).__init__(view)
        self.__scene = view.scene()
        self.scene().installEventFilter(self)
        self.__lineitems = {}
        self.__mouseButton = None

    def view(self):
        r'''
            @brief  セットされているビューを返す。
            @return QtWidgets.QGraphicsView
        '''
        return self.parent()

    def scene(self):
        r'''
            @brief  セットされているビューのシーンオブジェクトを返す。
            @return QtWidgets.QGraphicsScene
        '''
        return self.__scene

    def eventFilter(self, object, event):
        r'''
            @brief  イベントフィルタのオーバーライド
            @param  object : [QtCore.QObject]
            @param  event : [QEvent]
            @return None
        '''
        event_type = event.type()
        p_event_filter = super(DirectionalOperator, self).eventFilter

        if event_type == QtCore.QEvent.GraphicsSceneMousePress:
            scene_pos = event.scenePos()
            # 新しいラインアイテムをカーソル上に作成する。
            self.__lineitems['line'] = DirectionaalPlaneLine(self.scene())
            self.__lineitems['line'].setStart(scene_pos)
            
            # 開始位置を表すマーカーを作成する。
            half_size = self.StartMarkerSize / 2.0
            self.__lineitems['marker'] = QtWidgets.QGraphicsEllipseItem(
                scene_pos.x() - half_size, scene_pos.y() - half_size,
                self.StartMarkerSize, self.StartMarkerSize
            )
            self.__lineitems['marker'].setBrush(DirectionaalPlaneLine.Color)
            self.scene().addItem(self.__lineitems['marker'])
            
            self.__mouseButton = int(QtWidgets.QApplication.mouseButtons())
            return True

        elif event_type == QtCore.QEvent.GraphicsSceneMouseMove:
            if self.__lineitems:
                self.__lineitems['line'].setEnd(event.scenePos())
                self.__lineitems['line'].updatePath()
            return True

        elif event_type == QtCore.QEvent.GraphicsSceneMouseRelease:
            if self.__lineitems:
                start_pos = self.__lineitems['line'].start()
                end_pos = self.__lineitems['line'].end()
                r_vector = [
                    end_pos.x() - start_pos.x(), start_pos.y() - end_pos.y(), 0
                ]

                for key in self.__lineitems:
                    self.scene().removeItem(self.__lineitems[key])
                self.__lineitems = {}

                if self.__mouseButton:
                    self.directionChanged.emit(r_vector, self.__mouseButton)
            return True
        return p_event_filter(object, event)

class DirectionView(QtWidgets.QGraphicsView):
    r'''
        @brief       方向指示をするためのビューを提供するクラス。
        @inheritance QtWidgets.QGraphicsView
        @date        2017/06/27 18:56[s_eske](eske3g@gmail.com)
        @update      2019/01/01 18:42[Eske](eske3g@gmail.com)
    '''
    directionChanged = QtCore.Signal(list, int)
    XYPlane = (0, 1, 2)
    ZYPlane = (2, 1, 0)
    XZPlane = (0, 2, 1)
    def __init__(self, parent=None):
        r'''
            @brief  初期化を行う。
            @param  parent(None) : [QtWidgets.QWidget]
            @return None
        '''
        super(DirectionView, self).__init__(parent)
        self.setCacheMode(QtWidgets.QGraphicsView.CacheBackground)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setRenderHints(
            QtGui.QPainter.Antialiasing |
            QtGui.QPainter.SmoothPixmapTransform |
            QtGui.QPainter.TextAntialiasing
        )
        self.__base_plane = self.XYPlane

        font = QtGui.QFont('arial', 10)
        scene = QtWidgets.QGraphicsScene(QtCore.QRectF(self.rect()))
        self.__textItem = scene.addText('', font)
        self.setScene(scene)

        oprt = DirectionalOperator(self)
        oprt.directionChanged.connect(self.done)

    def setVectorPlane(self, planeType):
        r'''
            @brief  ここに説明文を記入
            @param  planeType : [edit]
            @return None
        '''
        self.__base_plane = planeType

    def setText(self, text):
        r'''
            @brief  左上に表示する注釈テキストを設定する。
            @param  text : [str]
            @return None
        '''
        self.__textItem.setPlainText(text)

    def done(self, vector, mouseButton):
        r'''
            @brief  ドラッグ操作が終了した際に呼ばれる。
            @brief  directionChangedシグナルが創出される。
            @param  vector : [edit]
            @param  mouseButton : [edit]
            @return None
        '''
        newVector = [vector[x] for x in self.__base_plane]
        self.directionChanged.emit(newVector, mouseButton)

    def resizeEvent(self, event):
        r'''
            @brief  リサイズ時のイベントのオーバーライド。
            @param  event : [QEvent]
            @return None
        '''
        self.scene().setSceneRect(QtCore.QRectF(self.rect()))
# /////////////////////////////////////////////////////////////////////////////
#                                                                            //
# /////////////////////////////////////////////////////////////////////////////