#, *- coding: utf-8, *-
r'''
    @file     selectToolMM.py
    @brief    ここに説明文を記入
    @date        2018/03/05 23:38[Eske](eske3g@gmail.com)
    @update      2018/03/05 23:38[Eske](eske3g@gmail.com)
    このソースの版権はEske Yoshinobにあります
    無断転載、改ざん、無断使用は基本的に禁止しておりますので注意して下さい
    このソースを使用して不具合や不利益等が生じても[Eske Yoshinob]
    は一切責任を負いませんのであらかじめご了承ください
'''
from maya import cmds, mel
from gris3.tools import selectionUtil
from gris3.uilib import mayaUIlib
QtWidgets, QtGui, QtCore = (
    mayaUIlib.QtWidgets, mayaUIlib.QtGui, mayaUIlib.QtCore
)

class MarkingMenu(mayaUIlib.MarkingMenuWithTool):
    def createMenu(self, parent):
        cmds.menuItem(p=parent, l='Grid', rp='NE', c=self.mel('ToggleGrid'))
        cmds.menuItem(l='Grid Options', ob=True, c=self.mel('GridOptions'))

        cmds.menuItem(p=parent, l='Edges', rp='N', sm=1)
        cmds.menuItem(
            l='Hulls / Soft/All Edges', rp='N',
            c=self.mel('ToggleHulls;ToggleSoftEdges;ToggleMeshEdges;')
        )
        cmds.menuItem(
            l='Surface Origin / Border Edges', rp='S',
            c=self.mel('ToggleSurfaceOrigin;ToggleBorderEdges;')
        )
        
        cmds.menuItem(p=parent, l='UVs', rp='E', c='ToggleUVs;ToggleMeshMaps;')

        cmds.menuItem(
            p=parent, l='Face/Patch Centers', rp='S',
            c=self.mel(
                'ToggleSurfaceFaceCenters;TogglePolygonFaceCenters;'
                'ToggleMeshFaces;'
            )
        )
        cmds.menuItem(
            p=parent, l='Edit Points', rp='SW', c=self.mel('ToggleEditPoints')
        )
        cmds.menuItem(
            p=parent, l='CV / Vertices', rp='W',
            c=self.mel(
                'ToggleCVs;ToggleVertices;ToggleMeshPoints;ToggleLatticePoints'
            )
        )

        # カスタムディスプレイオプション。=====================================
        item = cmds.menuItem(
            p=parent, l='customDisplays', rp='NW', aob=1, sm=1
        )
        cmds.menuItem(
            p=item, l='Custom NURBS Smoothness', rp='SE',
            c=self.mel('CustomNURBSSmoothness')
        )
        cmds.menuItem(
            l='CustomNURBSSmoothnessOptions', ob=1,
            c=self.mel('CustomNURBSSmoothnessOptions')
        )

        cmds.menuItem(
            p=item, l='Custom NURBS Components', rp='NE',
            c=self.mel('ToggleCustomNURBSComponents')
        )
        cmds.menuItem(
            l='CustomNURBSComponentsOptions', ob=1,
            c=self.mel('CustomNURBSComponentsOptions')
        )

        cmds.menuItem(
            p=item, l='Custom Polygon Display', rp='NW',
            c=self.mel('CustomPolygonDisplay')
        )
        cmds.menuItem(
            l='CustomPolygonDisplayOptions', ob=1,
            c=self.mel('CustomPolygonDisplayOptions')
        )
        # =====================================================================

        cmds.menuItem(
            p=parent, l='Back Face Culling', rp='SE',
            c=self.mel('polyOptions -fb')
        )

        cmds.menuItem(
            p=parent, l='Local Rotation Axes',
            c=self.mel('ToggleLocalRotationAxes;')
        )
        cmds.menuItem(
            p=parent, l='Joint Labels', c=self.mel('displayJointLabels 2')
        )
        cmds.menuItem(
            p=parent, l='Rotate Pivots', c=self.mel('ToggleRotationPivots;')
        )
        cmds.menuItem(
            p=parent, l='Scale Pivots', c=self.mel('ToggleScalePivots;')
        )
        cmds.menuItem(
            p=parent, l='Selection Handles',
            c=self.mel('ToggleSelectionHandles;')
        )

    def command(self):
        mel.eval('PolyDisplayReset')
