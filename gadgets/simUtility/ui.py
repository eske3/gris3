# -*- coding:utf-8 -*-
r'''
    @file     ui.py
    @brief    ここに説明文を記入
    @class    FrameRangeSetting : フレームレンジを設定するGUIを提供するクラス。
    @class    ProcessWidget : ここに説明文を記入
    @class    ParamDoubleSpiner : ここに説明文を記入
    @class    PresetList : ここに説明文を記入
    @class    ParameterOption : ここに説明文を記入
    @class    MainWidget : メインとなるUIウィジェットを返す。
    @class    SeparatedWidget : ここに説明文を記入
    @function showWindow : 単独で動くPoseManagerウィンドウを表示する。
    @date        2017/04/22 15:24[Eske](eske3g@gmail.com)
    @update      2017/04/22 18:13[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''

from . import core as simCore
from gris3 import uilib, lib, core, style
from gris3.uilib import mayaUIlib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore


class FrameRangeSetting(QtWidgets.QGroupBox):
    r'''
        @brief       フレームレンジを設定するGUIを提供するクラス。
        @inheritance QtWidgets.QGroupBox
        @date        2017/04/22 15:24[Eske](eske3g@gmail.com)
        @update      2017/04/22 18:13[Eske](eske3g@gmail.com)
    '''
    def __init__(self, parent=None):
        r'''
            @brief  初期化する。
            @param  parent(None) : [QtWidgets.QWidget]
            @return None
        '''
        super(FrameRangeSetting, self).__init__('Simulation Frame', parent)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed
        )
        layout = QtWidgets.QHBoxLayout(self)
        self.__spiners = []
        for label in ('Start Frame', 'End Frame'):
            label = QtWidgets.QLabel(label)
            label.setSizePolicy(
                QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
            )
            spiner = uilib.Spiner()
            spiner.setMaximumSize(
                80, spiner.maximumSize().height()
            )
            spiner.setRange(-100000, 100000)
            layout.addWidget(label)
            layout.setAlignment(label, QtCore.Qt.AlignRight)
            layout.addWidget(spiner)
            
            self.__spiners.append(spiner)

        btn = QtWidgets.QPushButton('Set from scene')
        btn.clicked.connect(self.setRangeFromScene)
        layout.addWidget(btn)

    def setRangeFromScene(self):
        r'''
            @brief  現在のシーンからフレームレンジを設定する。
            @return None
        '''
        for widget, frame in zip(self.__spiners, simCore.getFrameRange()):
            widget.setValue(frame)

    def frameRange(self):
        r'''
            @brief  このUIで設定されているフレームレンジを返す。
            @return tuple(startFrame,  endFrame)
        '''
        return [x.value() for x in self.__spiners]


class ProcessWidget(QtWidgets.QGroupBox):
    r'''
        @brief       ここに説明文を記入
        @inheritance QtWidgets.QGroupBox
        @date        2017/04/22 15:24[Eske](eske3g@gmail.com)
        @update      2017/04/22 18:13[Eske](eske3g@gmail.com)
    '''
    def __init__(self, parent=None):
        r'''
            @brief  ここに説明文を記入
            @param  parent(None) : [edit]
            @return None
        '''
        super(ProcessWidget, self).__init__('Process', parent)
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        )

        st_layout = QtWidgets.QVBoxLayout()
        self.__process_btns = {}
        for key, checked in (
            ('setup', True),
            ('bake', True),
            ('hideObject', False),
        ):
           btn = QtWidgets.QCheckBox(lib.title(key))
           btn.setChecked(checked)
           st_layout.addWidget(btn)
           self.__process_btns[key] = btn

        exe_btn = uilib.OButton()
        exe_btn.setIcon(uilib.IconPath('uiBtn_play'))
        exe_btn.setToolTip('Start simulation.')
        exe_btn.setSize(64)
        exe_btn.setBgColor(44, 96, 183)
        layout = QtWidgets.QHBoxLayout(self)
        layout.addLayout(st_layout)
        layout.addWidget(exe_btn)

        self.clicked = exe_btn.clicked

    def state(self):
        r'''
            @brief  チェックボックスの状態を辞書で返す。
            @return dict
        '''
        return {
            x : y.isChecked() for x,y in self.__process_btns.items()
        }

class ParamDoubleSpiner(QtWidgets.QWidget):
    r'''
        @brief       ここに説明文を記入
        @inheritance QtWidgets.QWidget
        @date        2017/04/22 18:13[Eske](eske3g@gmail.com)
        @update      2017/04/22 18:13[Eske](eske3g@gmail.com)
    '''
    def __init__(self, value, min, max, step, parent=None):
        r'''
            @brief  ここに説明文を記入
            @param  value : [edit]
            @param  min : [edit]
            @param  max : [edit]
            @param  step : [edit]
            @param  parent(None) : [edit]
            @return None
        '''
        super(ParamDoubleSpiner, self).__init__(parent)
        self.__default = value

        self.__spiner = uilib.DoubleSpiner()
        self.__spiner.setMinimumSize(100, self.__spiner.minimumSize().height())
        self.__spiner.setValue(value)
        self.__spiner.setRange(min, max)
        self.__spiner.setSingleStep(step)

        default_btn = QtWidgets.QPushButton('Default')
        default_btn.setMinimumWidth(100)
        default_btn.clicked.connect(self.setToDefault)
        default_btn.setToolTip('Set default value.')

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.__spiner)
        layout.addWidget(default_btn)
        
        self.setValue = self.__spiner.setValue
        self.value = self.__spiner.value

    def setDefaultValue(self, value):
        self.__default = value

    def setToDefault(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        self.__spiner.setValue(self.__default)


class PresetList(QtWidgets.QTreeView):
    r'''
        @brief       ここに説明文を記入
        @inheritance QtWidgets.QTreeView
        @date        2017/04/22 18:13[Eske](eske3g@gmail.com)
        @update      2017/04/22 18:13[Eske](eske3g@gmail.com)
    '''
    itemIsSelected = QtCore.Signal(dict)
    def __init__(self, parent=None):
        r'''
            @brief  ここに説明文を記入
            @param  parent(None) : [edit]
            @return None
        '''
        super(PresetList, self).__init__(parent)
        self.setAlternatingRowColors(True)
        self.setRootIsDecorated(False)
        self.clicked.connect(self.loadPreset)
        
        model = QtGui.QStandardItemModel(0, 1)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Preset')
        self.setModel(model)
        
        sel_model = QtCore.QItemSelectionModel(model)
        self.setSelectionModel(sel_model)
        self.__preset = {}

    def addPreset(self, name, preset):
        r'''
            @brief  ここに説明文を記入
            @param  preset : [dict]
            @return None
        '''
        import time
        key = str(time.time()) + '_' + name
        self.__preset[key] = preset
        item = QtGui.QStandardItem(lib.title(name))
        item.setData(key)
        item.setEditable(False)

        model = self.model()
        model.setItem(model.rowCount(), 0, item)

    def loadPreset(self, index):
        key = index.data(QtCore.Qt.UserRole+1)
        self.itemIsSelected.emit(self.__preset[key])

    def selectPreset(self, label):
        model = self.model()
        for i in range(model.rowCount()):
            index = model.index(i, 0)
            if index.data(QtCore.Qt.DisplayRole) != label:
                continue
            self.selectionModel().select(
                index, QtCore.QItemSelectionModel.ClearAndSelect
            )
            return
        
class ParameterOption(QtWidgets.QWidget):
    r'''
        @brief       ここに説明文を記入
        @inheritance QtWidgets.QWidget
        @date        2017/04/22 18:13[Eske](eske3g@gmail.com)
        @update      2017/04/22 18:13[Eske](eske3g@gmail.com)
    '''
    HairSysParameters = [
        ('stiffness', 0.5, 0, 100, 0.1),
        ('mass', 5.0, 0, 10000, 0.1),
        ('drag', 0.35, 0, 10000, 0.1),
        ('damp', 0.1, 0, 10000, 0.1),
        ('gravity', 9.8, -10000, 10000, 0.1),
    ]
    def __init__(self, parent=None):
        r'''
            @brief  ここに説明文を記入
            @param  parent(None) : [edit]
            @return None
        '''
        super(ParameterOption, self).__init__(parent)
        label = QtWidgets.QLabel('+ Parameters')

        # オプション表示用のスクローラー
        scroll = QtWidgets.QScrollArea()

        # プリセットリスト。
        preset = PresetList()
        for key, value in simCore.ParameterPreset.items():
            preset.addPreset(key, value)
        preset.itemIsSelected.connect(self.updateOption)

        splitter = QtWidgets.QSplitter()
        splitter.addWidget(scroll)
        splitter.addWidget(preset)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes((uilib.hires*240, 80))

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(label)
        layout.addWidget(splitter)

        opt_widget = QtWidgets.QWidget()
        opt_layout = QtWidgets.QGridLayout(opt_widget)
        opt_layout.setColumnStretch(0, 1)
        self.__widgets = {}
        for i, values in enumerate(self.HairSysParameters):
            label, default, min, max, step = values
            l = QtWidgets.QLabel(lib.title(label))
            s = ParamDoubleSpiner(default, min, max, step)
            opt_layout.addWidget(l, i, 0, 1, 1)
            opt_layout.addWidget(s, i, 1, 1, 1)
            self.__widgets[label] = s
        scroll.setWidget(opt_widget)

        preset.selectPreset('Mid')
        # self.updateOption(simCore.ParameterPreset['mid'])
        

    def updateOption(self, preset):
        for key, value in preset.items():
            if key in self.__widgets:
                self.__widgets[key].setValue(value)
                self.__widgets[key].setDefaultValue(value)

    def state(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        return {x:y.value() for x, y in self.__widgets.items()}

class MainWidget(QtWidgets.QWidget):
    r'''
        @brief       メインとなるUIウィジェットを返す。
        @inheritance QtWidgets.QWidget
        @date        2017/04/22 15:24[Eske](eske3g@gmail.com)
        @update      2017/04/22 18:13[Eske](eske3g@gmail.com)
    '''
    def __init__(self, parent=None):
        r'''
            @brief  初期化を行う。
            @param  parent(None) : [QtWidgets.QWidget]
            @return None
        '''
        super(MainWidget, self).__init__(parent)
        self.setWindowTitle('Gris Spiring Simulator')
        
        self.__framerange = FrameRangeSetting()
        self.setRangeFromScene = self.__framerange.setRangeFromScene
        
        self.__param = ParameterOption()
        
        self.__process = ProcessWidget()
        self.__process.clicked.connect(self.startSimulation)

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(self.__framerange, 0, 0, 1, 2)
        layout.addWidget(self.__param, 1, 0, 2, 1)
        layout.addWidget(self.__process, 2, 1, 1, 1)
        layout.setRowStretch(3, 1)


    def startSimulation(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        state = self.__process.state()
        sim_opt = self.__param.state()
        start, end = self.__framerange.frameRange()
        print('-'*80)
        print(sim_opt)
        print('-'*80)

        # sim = simCore.NSpringSimulator()
        sim = simCore.SpringSimulator()
        restore_display = (
            sim.hideObjects() if state['hideObject'] and state['bake']
            else None
        )
        with core.Do:
            if state['setup']:
                sim.setup()
                temp_roots = [sim.createSimulatedSystem(sim_opt)]
            else:
                temp_roots = None
    
            if state['bake']:
                sim.bake(temp_roots, start, end)

            sim.restoreSelection()
        if restore_display:
            sim.restoreHiddenObject()

class SeparatedWidget(uilib.AbstractSeparatedWindow):
    r'''
        @brief       ここに説明文を記入
        @inheritance uilib.AbstractSeparatedWindow
        @date        2017/04/22 18:13[Eske](eske3g@gmail.com)
        @update      2017/04/22 18:13[Eske](eske3g@gmail.com)
    '''
    def centralWidget(self):
        r'''
            @brief  UIの作成を行う。
            @return MainWidget
        '''
        return MainWidget()

    def show(self):
        r'''
            @brief  ここに説明文を記入
            @return None
        '''
        self.setScalable(False)
        self.main().setRangeFromScene()
        super(SeparatedWidget, self).show()
        self.raise_()

def showWindow():
    r'''
        @brief  単独で動くPoseManagerウィンドウを表示する。
        @return SeparatedWidget
    '''
    w = SeparatedWidget(mayaUIlib.MainWindow)
    w.resize(640, 340)
    w.show()
    return w