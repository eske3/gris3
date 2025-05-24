#!/usr/bin/python
# -*- coding: utf-8 -*-
# old_style:google style:google
r"""
    ジョイントの編集機能を提供するGUI。
    
    Dates:
        date:2017/06/15 16:35[Eske](eske3g@gmail.com)
        update:2024/02/03 13:41 Eske Yoshinob[eske3g@gmail.com]
        
    License:
        Copyright 2017 Eske Yoshinob[eske3g@gmail.com] - All Rights Reserved
        Unauthorized copying of this file, via any medium is strictly prohibited
        Proprietary and confidential
"""
from ..tools.animationUtil import humanRigUtil
from ..tools import mirrorUtil
from .. import lib, uilib, node
from ..uilib import mayaUIlib
QtWidgets, QtGui, QtCore = uilib.QtWidgets, uilib.QtGui, uilib.QtCore
Exec_Color = (64, 72, 150)


class IkFkMatcher(uilib.ClosableGroup):
    r"""
        IK/FKマッチ機能を行うためのGUIを提供するクラス。
    """
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(IkFkMatcher, self).__init__(
            'Ik / Fk Match', parent
        )
        self.setIcon(uilib.IconPath('uiBtn_connectInvScale'))
        
        # Ik fk matching.=====================================================
        switch_btn = uilib.OButton(uilib.IconPath('uiBtn_reset'))
        switch_btn.setSize(32)
        switch_btn.setBgColor(*Exec_Color)
        switch_btn.clicked.connect(self.switch_ik_fk)
        switch_label = QtWidgets.QLabel('Switch Ik / Fk with matching')
        # ====================================================================
        
        # bake ik or fk with matching. =======================================
        grp = QtWidgets.QGroupBox('Bake')
        self.__framerange = mayaUIlib.Framerange()
        
        btns = []
        for l, m in (
            ('Bake to IK', self.bake_to_ik),
            ('Bake to FK', self.bake_to_fk)
        ):
            btns.append(QtWidgets.QPushButton(l))
            btns[-1].setMinimumHeight(1)
            btns[-1].clicked.connect(m)

        layout = QtWidgets.QGridLayout(grp)
        layout.setSpacing(1)
        layout.addWidget(self.__framerange, 0, 0, 1, 2)
        layout.addWidget(btns[0], 1, 0, 1, 1)
        layout.addWidget(btns[1], 1, 1, 1, 1)
        # ====================================================================
        
        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(switch_btn, 0, 0, 1, 1)
        layout.addWidget(switch_label, 0, 1, 1, 1)
        layout.addWidget(grp, 1, 0, 1, 2)

    def switch_ik_fk(self):
        r"""
            IKとFKの切り替えを行う。
        """
        from importlib import reload
        reload(humanRigUtil)
        with node.DoCommand():
            humanRigUtil.matchIkFk()

    def bake_to_ik(self):
        r"""
            FKからIKへのベイクを行う。
        """
        start, end = self.__framerange.framerange()
        with node.DoCommand():
            humanRigUtil.bakeIkFk(ikToFk=False, startFrame=start, endFrame=end)

    def bake_to_fk(self):
        r"""
            IKからFKへのベイクを行う。
        """
        start, end = self.__framerange.framerange()
        with node.DoCommand():
            humanRigUtil.bakeIkFk(ikToFk=True, startFrame=start, endFrame=end)


class PoseManager(uilib.ClosableGroup):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(PoseManager, self).__init__(
            'Pose Manager - Mirror / Swap', parent
        )
        self.setIcon(uilib.IconPath('uiBtn_poseManager'))
        
        buttons = []
        for l, f in (
            ('Swap', self.swap),
            ('Mirror', self.mirror)
        ):
            btn = QtWidgets.QPushButton(l)
            btn.clicked.connect(f)
            buttons.append(btn)
        
        layout = QtWidgets.QGridLayout(self)
        layout.setSpacing(1)
        layout.addWidget(buttons[0], 0, 0, 1, 1)
        layout.addWidget(buttons[1], 0, 1, 1, 1)

    def _do_mirror(self, isMirror):
        # from importlib import reload
        # reload(mirrorUtil)
        with node.DoCommand():
            mirrorUtil.swap(isMirror=isMirror)

    def swap(self):
        self._do_mirror(False)

    def mirror(self):
        self._do_mirror(True)



class AnimSupporter(QtWidgets.QScrollArea):
    def __init__(self, parent=None):
        r"""
            Args:
                parent (QtWidgets.QWidget):親ウィジェット
        """
        super(AnimSupporter, self).__init__(parent)
        self.setWindowTitle('+ Anim Supporter')
        ik_fk_matcher = IkFkMatcher()

        widget = QtWidgets.QWidget()
        widget.setObjectName('ScrollAreaTopWidget')
        widget.setStyleSheet(
            'QWidget #ScrollAreaTopWidget{background:transparent;}'
        )
        self.setWidget(widget)
        self.setWidgetResizable(True)
        
        layout = QtWidgets.QVBoxLayout(widget)
        layout.addWidget(IkFkMatcher())
        layout.addWidget(PoseManager())
        layout.addStretch()


class MainGUI(uilib.AbstractSeparatedWindow):
    r"""
        独立ウィンドウ式のAnimSupporterを提供する。
    """
    def centralWidget(self):
        r"""
            Returns:
                AnimSupporter:
        """
        return AnimSupporter()


def showWindow():
    r"""
        ウィンドウを作成するためのエントリ関数。
        
        Returns:
            QtWidgets.QWidget:
    """
    widget = MainGUI(mayaUIlib.MainWindow)
    widget.resize(400*uilib.hires, 330*uilib.hires)
    widget.show()
    return widget
