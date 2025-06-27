#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    表示にまつわる情報を提供するモジュール。
    主にStylesheetまわりの情報提供を目的としている。
    
    Dates:
        date:2017/01/22 0:00[Eske](eske3g@gmail.com)
        update:2025/06/27 10:32 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from . import globalpath
from .pyside_module import *


# デスクトップの大きさに関わる情報の収集。=====================================
if NoGui:
    DesktopLongestEdge = 1920
else:
    sizelist = []
    if Package == 'PySide6':
        for screen in QtWidgets.QApplication.screens():
            sizes = screen.availableSize()
            sizelist.extend([sizes.width(), sizes.height()])
    else:
        desktop = QtWidgets.QApplication.desktop()
        for i in range(desktop.screenCount()):
            rect = desktop.screenGeometry(i)
            sizelist.extend([rect.width(), rect.height()])
    DesktopLongestEdge = max(sizelist)
UiScale = 1+((DesktopLongestEdge / 1920.0)-1)*0.5
# =============================================================================


if Package == 'PySide6':
    def screenRect(position):
        r"""
            位置情報から、その座標上にあるスクリーンの矩形情報を返す。

            Args:
                position (QtCore.QPoint):
            
            Returns:
                QtCore.QRect:
        """
        return QtWidgets.QApplication.screenAt(position).availableGeometry()
else:
    def screenRect(position):
        r"""
            位置情報から、その座標上にあるスクリーンの矩形情報を返す。

            Args:
                position (QtCore.QPoint):
            
            Returns:
                QtCore.QRect:
        """
        d = QtWidgets.QApplication.desktop()
        return d.screenGeometry(d.screenNumber(position))


def scaled(size):
    r"""
        Args:
            size (int):
            
        Returns:
            int:
    """
    return int(size * UiScale)


class HiRes(object):
    r"""
        scaled関数の代わりとなる、乗算演算可能なクラス。
        ハイレゾモニター用のスケール補正をかける。
    """
    def __init__(self, uiscale):
        r"""
            Args:
                uiscale (float):
        """
        self.uiscale = uiscale

    def __call__(self, other):
        r"""
            Args:
                other (int):
                
            Returns:
                int:
        """
        return int(other * self.uiscale)

    def __mul__(self, other):
        r"""
            Args:
                other (int):
                
            Returns:
                int:
        """
        return self(other)

    def __rmul__(self, other):
        r"""
            Args:
                other (int):
                
            Returns:
                int:
        """
        return self(other)
hires = HiRes(UiScale)


# StyleSheet template.=========================================================
TitleLabelSize = 18*UiScale
BaseFontSize = 15*UiScale
LineUiSize = 18*UiScale
ScrollBarSize = 8*UiScale
ScrollBarHandleSize = (ScrollBarSize *0.25 + 2)*UiScale
ComboboxArrowSize = 8*UiScale
GlobalFont = "'Lucida Grande','Hiragino Kaku Gothic ProN', Meiryo, sans-serif"

QWidget = '''
QWidget{
    color : #c0c0c0;
    font-family : %(font)s;
}

QWidget:disabled{
    color : #707070;
}'''

QDialog = '''
QDialog{
    background-color : %(widgetGradientColor)s;
    border : 1px solid #000000;
}'''

TitleLabel = '''
QLabel{
    font-size:%spx;
}
''' % TitleLabelSize

QGraphicsView = '''
QGraphicsView{
    background : %(widgetGradientColor)s;
}
'''

QScrollArea = '''
QScrollArea{
    background : %(widgetGradientColor)s;
}
'''

LineEditors = '''
QTextEdit, QLineEdit, QSpinBox{
    background-color : #252525;
    border : 1px solid #000000;
    border-radius : 4px;
}
'''
QPushButton = '''
QPushButton{
    padding-left : 20px;
    padding-right : 20px;
    padding-top : %(buttonPadding)spx;
    padding-bottom : %(buttonPadding)spx;
    border : 1px solid #202020;
    border-radius : 4px;
    background : #555555;
    margin : 2px;
}

QPushButton::disabled{
    color : #808080;
}

QPushButton:hover{
    border : 1px solid #c0c0c0;
    background : #305dad;
}
QPushButton:pressed{
    background : %(selected-color)s;
}
QPushButton:checked{
    background : %(uiGradientColor-act)s;
    border : 1px solid #ffffff;
}
'''

QComboBox = '''
QComboBox{
    background : %(uiGradientColor)s;
    border : 1px solid #000000;
    border-radius : 4px;
    padding-left : 10px;
}
QComboBox::drop-down{
    border : none;
    subcontrol-position : top right;
    margin-right : 10px;
}
QComboBox::down-arrow{
    image : url("%(iconpath)s/uiBtn_downarrow.png");
    width : %(combobox-arrow-size)s;
}
QComboBox::down-arrow:on{
    top : 1px;
    left : 1px;
}
'''

ItemViews = '''
QTreeView, QTableView, QListView{
    outline : 0px;
}
QHeaderView::section{
    background-color : #505050;
    border-top : none;
    border-right : none;
    border-left : 1px solid #000000;
    border-bottom : none;
    height : %(headerSize)s;
    padding-left : 5px;
}

QAbstractItemView, QTreeView, QListView{
    border : 1px solid #000000;
    selection-background-color : #4050e0;
    background : #141414;
    alternate-background-color : #202020;
    font-family : %(font)s;
}

QTreeView::branch:has-siblings:!adjoins-item {
    border-image: url("%(iconpath)s/uiBtn_vline.png") 0;
}

QTreeView::branch:has-siblings:adjoins-item {
    border-image: url("%(iconpath)s/uiBtn_branchMore.png") 0;
}

QTreeView::branch:!has-children:!has-siblings:adjoins-item {
    border-image: url("%(iconpath)s/uiBtn_branchEnd.png") 0;
}

QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
        border-image: none;
        image: url("%(iconpath)s/uiBtn_branchClosed.png");
}

QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings  {
        border-image: none;
        image: url("%(iconpath)s/uiBtn_branchOpen.png");
}

QTreeView::item{
    padding-top : 4px;
    padding-bottom : 4px;
}

QTreeView::item:selected:active, QListView::item:selected:active{
    color : #f0f0f0;
    background : %(selected-color)s;
}

QTreeView::item:hover, QListView::item:hover{
    background : %(hover-color)s;
}

QTreeView::item:selected:!active, QListView::item:selected:!active{
    color : #d0d0d0;
    background : %(selected-color-deact)s;
}
'''

QCheckBox = '''
QCheckBox::indicator:unchecked{
    background : #404040;
    border : 1px solid #000000;
    border-radius : 4px;
}'''

QScrollBar = '''
QScrollBar:vertical {
    border: 1px solid #000000;
    background: #303030;
    width: %(scrollbar-size)s;
    margin: %(scrollbar-margin)spx 0 %(scrollbar-margin)spx 0;
}

QScrollBar::handle:vertical {
    background : qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #505050, stop:1.0 #808080
                );
    min-height: %(scrollbar-handle)spx;
}

QScrollBar::add-line:vertical {
    border: none;
    background: %(scrollbar-color)s;
    height: %(scrollbar-handle)spx;
    border-bottom-right-radius : %(handle-radius)spx;
    border-bottom-left-radius : %(handle-radius)spx;
    subcontrol-position: bottom;
    subcontrol-origin: margin;
}

QScrollBar::sub-line:vertical {
    border: none;
    background: %(scrollbar-color)s;
    height: %(scrollbar-handle)spx;
    border-top-right-radius : %(handle-radius)spx;
    border-top-left-radius : %(handle-radius)spx;
    subcontrol-position: top;
    subcontrol-origin: margin;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
  background: none;
}

QScrollBar:horizontal {
    border: 1px solid #000000;
    background: #303030;
    height: %(scrollbar-size)s;
    margin: 0 %(scrollbar-margin)spx 0 %(scrollbar-margin)spx;
}
QScrollBar::handle:horizontal{
    background : qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #505050, stop:1.0 #808080
                );
    min-width: %(scrollbar-handle)spx;
}

QScrollBar::add-line:horizontal{
    border: none;
    background: %(scrollbar-color)s;
    width: %(scrollbar-handle)spx;
    border-top-right-radius : %(handle-radius)spx;
    border-bottom-right-radius : %(handle-radius)spx;
    subcontrol-position: right;
    subcontrol-origin: margin;
}

QScrollBar::sub-line:horizontal {
    border: none;
    background: %(scrollbar-color)s;
    width: %(scrollbar-handle)spx;
    border-top-left-radius : %(handle-radius)spx;
    border-bottom-left-radius : %(handle-radius)spx;
    subcontrol-position: left;
    subcontrol-origin: margin;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}'''

QSplitter = '''
QSplitter::handle{
    background-color : #000000;
}
QSplitter::handle:horizontal{
    width : 1px;
}
QSplitter::handle:vertical{
    height : 1px;
}
'''

QGroupBox = '''
QGroupBox{
    border : 1px solid #101010;
    border-radius : 6px;
    font-size : %(fontSize)spx;
    margin-top : 0.5em;
}
QGroupBox::title{
    subcontrol-origin : margin;
    padding : 0em 0.5em;
}
'''

QTabWidget = '''
QTabWidget::pane {
    border-top : 1px solid #000000;
}

QTabWidget::tab-bar {
    left: 5px;
}

QTabBar::tab {
    border: 1px solid #000000;
    border-bottom : none;
    padding: 12px;
    padding-left: 20px;
    padding-right: 20px;
}

QTabBar::tab:selected, QTabBar::tab:hover{
    border-color : #606060;
    background: %(selected-color-deact)s;
}

QTabBar::tab:selected {
    border-color: #909090;
    border-bottom-color: none;
}

QTabBar::tab:selected {
    margin-left: -8px;
    margin-right: -8px;
}

QTabBar::close-button{
    image: none;
}

QTabBar::close-button:hover{
    image: url("%(iconpath)s/uiBtn_x.png");
}
'''

QSlider = '''
QSlider::groove:horizontal, QProgressBar{
    border : 1px solid #000000;
    border-radius : 2px;
    background : #202020;
    height : 2px;
}

QSlider::sub-page:horizontal, QProgressBar::chunk{
    background : %(progressGradient)s;
}

QSlider::handle:horizontal{
    background : #909090;
    border : 1px solid #404040;
    border-radius : 8px;
    width : 20px;
    margin-top : -6px;
    margin-bottom : -6px;
}

QSlider::handle:horizontal:hover{
    background : #a0a0a0;
    border : 1px solid #ffffff;
    margin-top : -8px;
    margin-bottom : -8px;
}

QSlider::sub-page:horizontal:disabled{
    background : #707070;
}

QSlider::handle:horizontal:disabled{
    background : #808080;
    border : 1px solid #404040;
}
'''

Phonon = '''
Phonon--SeekSlider > QSlider{
}
'''

StyleSheetParameters = {
    'font' : GlobalFont,
    'fontSize':BaseFontSize,
    'iconpath' : globalpath.IconPath.replace('\\', '/'),

    'lineUISize' : LineUiSize,
    'headerSize' : int(LineUiSize*1.2),
    'buttonPadding' : ComboboxArrowSize * 0.5,

    'combobox-arrow-size' : '%spx' % ComboboxArrowSize,

    'scrollbar-size' : ScrollBarSize,
    'handle-radius' : ScrollBarSize * 0.1,
    'scrollbar-handle' : ScrollBarHandleSize,
    'scrollbar-margin' : ScrollBarHandleSize + 2,
    'scrollbar-color' : '#949494',

    'widgetGradientColor' : (
        'qlineargradient('
        'x1:0, y1:0, x2:0, y2:1.0,'
        'stop:0.0 #323232, stop:1.0 #323232)'
    ),

    'uiGradientColor' : (
        'qlineargradient('
        'x1:0, y1:0, x2:0, y2:1.0,'
        'stop:0 #707070, stop:0.2 #606060, stop:1.0 #404040)'
    ),
    'uiGradientColor-act' : (
        'qlineargradient('
        'x1:0, y1:0, x2:0, y2:1.0, stop:0 #a0a0a0, stop:1.0 #656565)'
    ),
    'selected-color':(
        'qlineargradient('
        'x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #2250c0, stop: 1 #3560ca)'
    ),
    'hover-color':(
        'qlineargradient('
        'x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #7080a0, stop: 1 #405080)'
    ),
    'selected-color-deact':'#3056b7',
        # 'qlineargradient('
        # 'x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #506097, stop: 1 #304080)'
    # ),
    'progressGradient':(
        'qlineargradient('
        'x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #1e53b4, stop: 1 #008ed8)'
    ),
}
# =============================================================================



def styleSheet(
    parts=[
        QWidget, QDialog, QGraphicsView, LineEditors, QPushButton, QComboBox,
        QScrollArea, ItemViews, QCheckBox, QScrollBar, QSplitter, QGroupBox,
        QTabWidget, QSlider, Phonon
    ]
):
    r"""
        規定のスタイルシート文字列を返す。
        
        Args:
            parts (any):
            
        Returns:
            str:
    """
    return ''.join(parts) % StyleSheetParameters