# -*- coding:utf-8 -*-
# Author        : eske3g@gmail.com
# Version       : 1.5
# Last modified : 28 Dec 2012

from gris3 import node
from . import lib, uilib
import re, sys, os
import maya.mel as mm
cmds = node.cmds

def createPreference(history):
    result = ''
    history = ',\n'.join([ "    ''' %s '''" % x.strip() for x in history ])
    result += '''commandHistory = [
%s
]
''' % (history)

    return result


def getIgnoreUnitConversionFlag(outattr, inattr):
    outtype = cmds.nodeType(outattr)
    intype = cmds.nodeType(inattr)
    return outtype != 'unitConversion' and intype != 'unitConversion'


def autoSetAttr(outattr, inattr):
    if cmds.isConnected(
            outattr, inattr,
            iuc=getIgnoreUnitConversionFlag(outattr, inattr)
        ):
        cmds.disconnectAttr(outattr, inattr)

    outvalue = cmds.getAttr(outattr)
    outAttrType = cmds.getAttr(outattr, type=True)
    if outAttrType == 'matrix':
        # Matrix --------------------------------------------------------------
        outvalue = ' '.join([ str(x) for x in outvalue ])
        cmd = 'setAttr -type "matrix" "%s" %s' % (inattr, outvalue)
        mm.eval(cmd)
        # ---------------------------------------------------------------------
    elif outAttrType == 'double3':
        outvalue = outvalue[0]
        cmds.setAttr(inattr, *outvalue)
    else:
        cmds.setAttr(inattr, outvalue)


class MultAttribute(object):
    def __init__(self, baseattr, start, last):
        self.__baseattr   = baseattr
        self.__startNum   = start
        self.__lastNum    = last
        self.__attrFormat = '%s[%s]'

    def startAttr(self):
        return self.__attrFormat % (self.__baseattr, self.__lastNum)
    def lastAttr(self):
        return self.__attrFormat % (self.__baseattr, self.__lastNum)

    def listAttr(self):
        result = []
        for i in range(self.__startNum, self.__lastNum + 1):
            result.append(self.__attrFormat % (self.__baseattr, i))
        return result



class MainWindow(uilib.Window):
    def __new__(cls, name=None):
        return uilib.Window.__new__(cls,
            windowname='skConnectionEditor',
            t='Connection Editor', iconName='Connection',
            w=400, h=600,
            mb=True
        )

    def __init__(self):
        if self.isOpend:
            return

        # Menu.----------------------------------------------------------------
        cmds.menu(l='File')
        cmds.menuItem(
            l='Save Replace Commands', c=uilib.fp(self.savePreference)
        )
        # ---------------------------------------------------------------------

        #mod = self.loadPreference()
        self.replaceCommandHistory = []
        self.display = {
            'left':{
                'showReadOnly'      : 0,
                'showOutputs'       : 1,
                'showInputs'        : 0,
                'showNonKeyable'    : 1,
                'showConnectedOnly' : 0,
                'showHidden'        : 1,
                'showPublished'     : 0,
            },
            'right':{
                'showReadOnly'      : 0,
                'showOutputs'       : 0,
                'showInputs'        : 1,
                'showNonKeyable'    : 1,
                'showConnectedOnly' : 0,
                'showHidden'        : 1,
                'showPublished'     : 0,
            }
        }

        ver = lib.getMayaVer()
        outcmd = uilib.fp(self.outputCmd)
        incmd  = uilib.fp(self.inputCmd)

        if ver < 2011 or ver >= 2015:
            del(self.display['left']['showPublished'])
            del(self.display['right']['showPublished'])
            gMPConnector = lib.GlobalMelPyConnector()
            gMPConnector.stockCommand(
                'gConnectionEditorOutputCommand', outcmd
            )
            gMPConnector.stockCommand(
                'gConnectionEditorInputCommand', incmd
            )
            outcmd = 'globalMelPyConnector gConnectionEditorOutputCommand;'
            incmd  = 'globalMelPyConnector gConnectionEditorInputCommand;'
            

        #if mod != None:
        #   self.replaceCommandHistory = mod.commandHistory

        form = cmds.formLayout(p=self)

        noteClm = uilib.FrameLayout(p=form)
        cmds.columnLayout(p=noteClm, adj=True)
        uilib.Text(
            l='Press Ctrl + Click is connecting to the multAttr to the next '
            'Avarable index.'
        )
        uilib.Text(
            l='Press Alt + Click is connecting to the multAttr as inserting.'
        )
        uilib.Text(l='Press Shift + Click is copying value.')


        # Auto connection options.---------------------------------------------
        self.autoConnectionFm = uilib.FrameLayout(p=form,
            l='Auto Connection', cll=True, cl=True,
            ann='When this frame expand, Turn auto connection on.'
        )
        acClm = cmds.columnLayout(adj=True)
        self.subAttrTFG = uilib.TextFieldButtonGrp(
            l='Replace Command', text="'%s'", bl='Add',
            ann='Connect input to output that is defined by replaced input attribute.',
            adj=2, cw=(3, 45),
            bc=uilib.fp(self.editSubCmd),
            cc=uilib.fp(self.refreshReplaceCommandField),
        )
        self.subAttrListPM = uilib.PopupMenu(
            b=3, pmc=uilib.fp(self.buildReplaceCommandMenu)
        )
        uilib.Text(l='%s : Input Attribute')
        # ---------------------------------------------------------------------


        # GUI for node outliners.----------------------------------------------
        self.outlinerPane = cmds.paneLayout(
            p=form, cn='vertical2', ps=[(1, 50, 100)]
        )
        self.leftOutliner = uilib.NodeOutliner(p=self.outlinerPane,
            sc=outcmd,
            showNonConnectable=False,
            ms=False,
            **self.display['left']
        )
        self.leftOutlinerPM = uilib.PopupMenu(
            p=self.leftOutliner, b=3, mm=True,
            pmc=uilib.fp(self.buildOutlinerMenu, 'left')
        )
        self.leftSelectPM = uilib.PopupMenu(
            p=self.leftOutliner, b=3, ctl=True, mm=True,
            pmc=uilib.fp(self.buildSelectMenu, 'left')
        )

        self.rightOutliner = uilib.NodeOutliner(p=self.outlinerPane,
            sc=incmd,
            showNonConnectable=False,
            pressHighlightsUnconnected=False,
            ms=True,
            **self.display['right']
        )
        self.rightOutlinerPM = uilib.PopupMenu(
            p=self.rightOutliner, b=3, mm=True,
            pmc=uilib.fp(self.buildOutlinerMenu, 'right')
        )
        # ---------------------------------------------------------------------

        # ---------------------------------------------------------------------
        self.leftNodeName = uilib.Button(
            p=form, l='Output', h=20, bgc=(0.95, 0.6, 0.82),
            c=uilib.fp(self.selectNode, 'left')
        )
        self.leftNodeName.objectList = []
        self.leftNodeMenu = cmds.popupMenu(
            b=3, pmc=uilib.fp(self.buildNodeMenu, 'left')
        )
        self.rightNodeName = uilib.Button(
            p=form, l='Input', h=20, bgc=[0.55, 0.60, 0.95],
            c=uilib.fp(self.selectNode, 'right')
        )
        self.rightNodeName.objectList = []
        self.rightNodeMenu = cmds.popupMenu(
            b=3, pmc=uilib.fp(self.buildNodeMenu, 'right')
        )
        # ---------------------------------------------------------------------

        # Reload Button.-------------------------------------------------------
        relLBtn = cmds.button(
            p=form, l='Reload Left', h=28, bgc=(0.95, 0.4, 0.62),
            c=uilib.fp(self.loadNode, 'left', None)
        )
        relRBtn = cmds.button(
            p=form, l='Reload Right', h=28, bgc=[0.4, 0.46, 0.95],
            c=uilib.fp(self.loadNode, 'right', None)
        )
        # ---------------------------------------------------------------------

        btmsep = cmds.separator(p=form, st='in', h=10)
        clsBtn = cmds.button(p=form, l='Close', c=uilib.fp(self.close))

        cmds.formLayout(form, e=True,
            af=[
                (noteClm, 'top', 2), (noteClm, 'right', 2), (noteClm, 'left', 2),
                (self.autoConnectionFm, 'left', 0), (self.autoConnectionFm, 'right', 0), 
                (relLBtn, 'left', 0),
                (relRBtn, 'right', 0),
                (self.outlinerPane, 'right', 0), (self.outlinerPane, 'left', 0), 
                (self.leftNodeName, 'left', 0),
                (self.rightNodeName, 'right', 0),
                (btmsep, 'right', 0), (btmsep, 'left', 0), 
                (clsBtn, 'right', 2), (clsBtn, 'bottom', 5), (clsBtn, 'left', 2),
            ],
            ac=[
                (self.autoConnectionFm, 'top', 0, noteClm),
                (relLBtn, 'top', 2, self.autoConnectionFm),
                (relRBtn, 'top', 2, self.autoConnectionFm),
                (self.leftNodeName, 'top', 2, relLBtn),
                (self.rightNodeName, 'top', 2, relRBtn),
                (self.outlinerPane, 'top', 2, self.leftNodeName), (self.outlinerPane, 'bottom', 2, btmsep),
                (btmsep, 'bottom', 5, clsBtn), 
            ],
            ap=[
                (relLBtn, 'right', 0,50),
                (relRBtn, 'left', 0,50), 
                (self.leftNodeName, 'right', 0, 50),
                (self.rightNodeName, 'left', 0, 50),
            ]
        )

        self.ui = {
            'left': {
                'text' : self.leftNodeName,
                'textMenu':self.leftNodeMenu,
                'defaultLabel' : 'Output',
                'nodeOutliner' : self.leftOutliner,
                'nodeOutlinerMenu': self.leftOutlinerPM,
                'nodeSelectMenu': self.leftSelectPM,
            },
            'right':{
                'text' : self.rightNodeName,
                'textMenu':self.rightNodeMenu,
                'defaultLabel' : 'Input',
                'nodeOutliner' : self.rightOutliner,
                'nodeOutlinerMenu': self.rightOutlinerPM,
                #'nodeSelectMenu': self.rightSelectPM,
            }
        }

        selection = cmds.ls(sl=True)
        if selection:
            if len(selection) == 1:
                self.loadNode('left', selection)
                self.loadNode('right', None)
            else:
                self.loadNode('left', selection[:-1])
                self.loadNode('right', [ selection[-1] ])

    def getPref(self):
        path = cmds.internalVar(upd=True)
        pref = os.path.join(path, 'connectionEditorGlobalPreference.py')

        return pref


    # Edit nodes.==============================================================
    def selectNode(self, side, *tmp):
        nodelist = self.ui[side]['text'].objectList

        cmds.select(cl=True)
        for node in nodelist:
            if not cmds.objExists(node):
                continue
            cmds.select(node, add=True)
    # =========================================================================


    # Edit GUI.================================================================
    def loadNode(self, side, nodelist=None, *tmp):
        if nodelist == None:
            nodelist = cmds.ls(sl=True)

        num = len(nodelist)
        if num == 0:
            self.ui[side]['text'].set(l=self.ui[side]['defaultLabel'])
            return
        elif num == 1:
            self.ui[side]['text'].set(l=nodelist[0])
        else:
            self.ui[side]['text'].set(l='%s...' % nodelist[0])

        self.ui[side]['text'].objectList = nodelist

        self.ui[side]['nodeOutliner'].set(replace=nodelist[0])
        for i in range(1, num):
            self.ui[side]['nodeOutliner'].set(a=nodelist[i])


    # Functions for connecting attributes.=====================================
    def connect(self, outattr, inattr):
        # Local function.------------------------------------------------------
        def getMultAttr(attr):
            mobj = re.compile('\[\d+\]$')
            index = mobj.search(inattr)
            if not index:
                return

            numchar  = index.group(0)
            num      = len(numchar)
            baseattr = inattr[:-num]
            attrlist = cmds.listAttr(baseattr, m=True)
            if not attrlist:
                return

            attrlist.reverse()
            attribute = ''
            for a in attrlist:
                if '.' in a:
                    continue
                attribute = a
                break
            if not attribute:
                return

            lastindex = mobj.search(attribute)
            i = int(lastindex.group(0)[1:-1])

            return MultAttribute(baseattr, int(numchar[1:-1]), i+1)
        # ---------------------------------------------------------------------

        mod = uilib.getModifier()
        mode = 'connect'

        # Decide behavior by attribute type.
        # Copy values from outattr to inattr.----------------------------------
        if mod['sh']:
            mode = 'copy'

        # Connect attribute to a next avarable attribute (multiple type)-----
        elif mod['ctrl']:
            multAttr = getMultAttr(inattr)
            if multAttr:
                inattr = multAttr.lastAttr()
                
        # Insert connection to the specified index of attribute.---------------
        elif mod['alt']:
            multAttr = getMultAttr(inattr)
            if multAttr:
                attrlist = multAttr.listAttr()
                attrlist.reverse()
                for i in range(0, len(attrlist)-1):
                    srcattr = cmds.listConnections(
                        attrlist[i+1],
                        s=True, d=False, p=True
                    )
                    if srcattr:
                        cmds.disconnectAttr(srcattr[0], attrlist[i+1])
                        cmds.connectAttr(srcattr[0], attrlist[i], f=True)
                    else:
                        autoSetAttr(attrlist[i+1], attrlist[i])
        # ---------------------------------------------------------------------

        if mode == 'connect':
            if cmds.isConnected(
                    outattr, inattr,
                    iuc=getIgnoreUnitConversionFlag(outattr, inattr)
            ):
                cmds.disconnectAttr(outattr, inattr)
            else:
                cmds.connectAttr(outattr, inattr, f=True)
        else:
            autoSetAttr(outattr, inattr)

        self.rightOutliner.set(redraw=True)
        self.rightOutliner.set(r=True)


    def outputCmd(self, *tmp):
        last = self.leftOutliner.get('lastClickedNode')
        self.rightOutliner.set(c=last)
        
        if self.autoConnectionFm.get('cl'):
            #If it is true, Auto connection mode is Off.
            return

        inputAttr = '.'.join(last.split('.')[1:])
        replaceCommand = self.subAttrTFG.get('text')
        if replaceCommand.find('%s') != -1:
            replaceCommand = replaceCommand.replace('%s', inputAttr)

        result = eval(replaceCommand)
        print('Auto connect : {} -> {}'.format(last, result))
        for n in self.ui['right']['text'].objectList:
            if not cmds.attributeQuery(result, ex=True, n=n):
                continue

            target = '%s.%s' % (n, result)
            self.connect(last, target)


    def inputCmd(self, *tmp):
        outattr = self.leftOutliner.get('lastClickedNode')
        inattr = self.rightOutliner.get('lastClickedNode')
        if outattr == ' ' or inattr == ' ':
            return

        if outattr.split('.') == 0  or inattr.split('.') == 0:
            return
        self.connect(outattr, inattr)
    # =========================================================================


    # Edit replace command.====================================================
    def refreshReplaceCommandField(self, *tmp):
        command = self.subAttrTFG.get('text')
        if not command in self.replaceCommandHistory:
            self.subAttrTFG.set(bl='Add')
        else:
            self.subAttrTFG.set(bl='Remove')

    def editSubCmd(self, *tmp):
        command = self.subAttrTFG.get('text')
        if not command in self.replaceCommandHistory:
            self.replaceCommandHistory.append(command)
            self.subAttrTFG.set(bl='Remove')
        else:
            self.replaceCommandHistory.remove(command)
            self.subAttrTFG.set(bl='Add')

    def buildReplaceCommandMenu(self, *tmp):
        self.subAttrListPM.set(dai=True)
        if len(self.replaceCommandHistory) == 0:
            cmds.menuItem(p=self.subAttrListPM, l='Nothing History')

        for cmd in self.replaceCommandHistory :
            cmds.menuItem(
                p=self.subAttrListPM, l=cmd,
                c=uilib.fp(self.setReplaceCommand, cmd)
            )

    def setReplaceCommand(self, command, *tmp):
        self.subAttrTFG.set(text=command)
        self.refreshReplaceCommandField()
    # =========================================================================


    # Edit preferences.========================================================
    def savePreference(self, *tmp):
        pref = self.getPref()
        cmd = createPreference(self.replaceCommandHistory)

        try:
            f = open(pref, 'w')
            f.write(cmd)
            f.close()
        except:
            lib.errorout()
            return 0

        print('Save Preference : {}'.format(pref))
        return 1

    def loadPreference(self, *tmp):
        pref = self.getPref()
        if not os.path.isfile(pref):
            return

        module = os.path.basename(pref).replace('.py', '')
        import sys
        if module in sys.modules:
            del sys.modules[ module ]
        try:
            import module as mod
            return mod
        except:
            lib.errorout()
            return None
    # =========================================================================



    # Build custom menu.=======================================================
    def buildNodeMenu(self, side, *tmp):
        menuName = self.ui[side]['textMenu']
        textName = self.ui[side]['text']

        cmds.popupMenu(menuName, e=True, dai=True)

        nodename = textName.get('label')
        cmds.menuItem(
            p=menuName, l='Select %s' % nodename,
            c=uilib.fp(self.selectNode, side)
        )
        cmds.menuItem(p=menuName, d=True)


    def buildOutlinerMenu(self, side, *tmp):
        pm = self.ui[side]['nodeOutlinerMenu']
        ol = self.ui[side]['nodeOutliner']
        pm.set(dai=True)

        v = ol.get('showReadOnly')
        cmds.menuItem(
            p=pm, l='Show Readable', cb=v, rp='N',
            c=uilib.fp(
                self.setOutlinerOption, side, {'showReadOnly':not(v)}
            )
        )

        v = ol.get('showOutputs')
        cmds.menuItem(
            p=pm, l='Show Outputs', cb=v, rp='NW',
            c=uilib.fp(
                self.setOutlinerOption, side, {'showOutputs':not(v)}
            )
        )

        v = ol.get('showInputs')
        cmds.menuItem(
            p=pm, l='Show Inputs', cb=v, rp='NE',
            c=uilib.fp(
                self.setOutlinerOption, side, {'showInputs':not(v)}
            )
        )

        v = ol.get('showPublished')
        cmds.menuItem(
            p=pm, l='Show Published', cb=v, rp='W',
            c=uilib.fp(
                self.setOutlinerOption, side, {'showPublished':not(v)}
            )
        )

        v = ol.get('showNonKeyable')
        cmds.menuItem(
            p=pm, l='Show Non-Keyable', cb=v, rp='SW',
            c=uilib.fp(
                self.setOutlinerOption, side, {'showNonKeyable':not(v)}
            )
        )

        v = ol.get('showConnectedOnly')
        cmds.menuItem(
            p=pm, l='Show Connected Only', cb=v, rp='SE',
            c=uilib.fp(
                self.setOutlinerOption, side, {'showConnectedOnly':not(v)}
            )
        )

        v = ol.get('showHidden')
        cmds.menuItem(
            p=pm, l='Show Hidden', cb=v, rp='S',
            c=uilib.fp(
                self.setOutlinerOption, side, {'showHidden':not(v)}
            )
        )


    def buildSelectMenu(self, side, *tmp):
        pm = self.ui[side]['nodeSelectMenu']
        pm.set(dai=True)

        cmds.menuItem(
            p=pm, l='Load Connecting in Right', rp='NE',
            c=uilib.fp(self.selectCommand, 'loadTo')
        )
        cmds.menuItem(
            p=pm, l='Select Connecting', rp='E',
            c=uilib.fp(self.selectCommand, 'selectTo')
        )

        cmds.menuItem(
            p=pm, l='Load Connected in Right', rp='NW',
            c=uilib.fp(self.selectCommand, 'loadFrom')
        )
        cmds.menuItem(
            p=pm, l='Select Connected', rp='W',
            c=uilib.fp(self.selectCommand, 'selectFrom')
        )

    def setOutlinerOption(self, side, arg, *tmp):
        self.ui[side]['nodeOutliner'].set(**arg)

    def selectCommand(self, which, *tmp):
        last = self.leftOutliner.get('lastClickedNode')

        # Decide flags for listConnections by "which" argument.----------------
        flags = {'d':True, 's':False}
        if which.endswith('From'):
            flags = {'d':False, 's':True}
        # ---------------------------------------------------------------------

        connectedNode = cmds.listConnections(last, **flags)
        if not connectedNode:
            return

        if which.startswith('select'):
            cmds.select(connectedNode)
        elif which.startswith('load'):
            self.loadNode('right', connectedNode)
    # =========================================================================
