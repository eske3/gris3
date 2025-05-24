# -*- coding:utf-8 -*-

import maya.cmds as mc
import functools
from . import lib
fp = functools.partial


# Utility functions.///////////////////////////////////////////////////////////////////////////////
def exe( command, **arg ):
	mc.waitCursor( st=True )
	mc.undoInfo( openChunk=True )

	try:
		command( **args )
	except Exception:
		lib.errorout()
	finally:
		mc.undoInfo( closeChunk=True )
		mc.waitCursor( st=False )


def getCurrent( arg ):
	if arg == None:
		return mc.setParent( q=True )
	else:
		return arg


def getModifier( convertSelectType=False ):
	mod = mc.getModifiers()
	sh, ctl, alt = 0, 0, 0
	if (mod / 1) % 2:
		sh = 1
	if (mod / 4) % 2:
		ctl = 1
	if (mod / 8) % 2:
		alt = 1

	if convertSelectType == False :
		return { 'sh':sh, 'ctrl':ctl, 'alt':alt }

	add, tgl, d = False, False, False
	if sh == 1 and ctl == 1:
		add = True
	elif sh == 1:
		tgl = True
	elif ctl == 1:
		d = True

	return { 'add':add, 'tgl':tgl, 'd':d }
# /////////////////////////////////////////////////////////////////////////////////////////////////




# The base class for GUI.//////////////////////////////////////////////////////////////////////////
class Control( str ):
	"""
	This is a root class of control widget.
	This class have a 2 method. The one is getting value(s) of widget's parameter(s).
	And, another one is setting values to the widget.
	"""
	def __new__( cls, name, ctrl=None ):
		cls.ctrl = ctrl
		return str.__new__( cls, name )

	def get( self, args ):
		if type( args ) in ('tuple', 'list'):
			result = []
			for a in args:
				arg = {a : True}
				result.append( self.ctrl( self, q=True, **arg ) )
			return result
		else:
			arg = {args : True }
			return self.ctrl( self, q=True, **arg )

	def set( self, **args ):
		self.ctrl( self, e=True, **args )
# /////////////////////////////////////////////////////////////////////////////////////////////////




# Basic window class.//////////////////////////////////////////////////////////////////////////////
class Window( str ):
	def __new__( cls,
		windowname=None,
		t='window1', iconName=None,
		w=320, h=250,
		mb=False
	):
		cls.isOpend = False
		if windowname != None:
			if mc.window( windowname, ex=True ):
				mc.showWindow( windowname )
				cls.isOpend = True
				return str.__new__( cls, windowname )

		if iconName == None:
			iconName = t

		window = mc.window( windowname,
			t=t, iconName=iconName,
			w=w, h=h, mb=mb
		)

		return str.__new__( cls, window )

	# Edit window.=================================================================================
	def set( self ):
		mc.setParent( self )

	def show( self, *tmp ):
		if mc.window( self, ex=True ):
			mc.showWindow( self )
			return 1
		return 0

	def close( self, *tmp ):
		if mc.window( self, ex=True ):
			mc.deleteUI( self )
			return 1
		return 0
	# =============================================================================================
# /////////////////////////////////////////////////////////////////////////////////////////////////





# Menus.///////////////////////////////////////////////////////////////////////////////////////////
class PopupMenu( Control ):
	def __new__( cls, uiname=None, p=None, b=1, **args ):
		ui = mc.popupMenu( uiname, p=getCurrent(p), b=b, **args )
		return Control.__new__( cls, ui, mc.popupMenu )
# /////////////////////////////////////////////////////////////////////////////////////////////////





# Layouts./////////////////////////////////////////////////////////////////////////////////////////
class TabLayout( Control ):
	def __new__( cls, uiname=None, p=None, **args ):
		ui = mc.tabLayout( uiname, p=getCurrent(p), **args )
		return Control.__new__( cls, ui, mc.tabLayout )

class FrameLayout( Control ):
	def __new__( cls, uiname=None, p=None, l=None, mw=2, mh=2, cll=False, cl=False, **args ):
		lv = True
		if l == None:
			l = ''
			lv = False
		ui = mc.frameLayout( uiname, p=getCurrent(p), l=l, lv=lv, mw=mw, mh=mh, cll=cll, cl=cl, **args )
		return Control.__new__( cls, ui, mc.frameLayout )
# /////////////////////////////////////////////////////////////////////////////////////////////////





# Controls.////////////////////////////////////////////////////////////////////////////////////////
# Text series.=====================================================================================
class Text( Control ):
	def __new__( cls, uiname=None, p=None, l='text', al='center', fn='plainLabelFont', **args ):
		ui = mc.text( uiname, p=getCurrent(p), l=l, al=al, fn=fn, **args )
		return Control.__new__( cls, ui, mc.text )

class TextFieldGrp( Control ):
	def __new__( cls, uiname=None, p=None, l='textField', text='', cw2=[100, 100], **args ):
		ui = mc.textFieldGrp( uiname, p=getCurrent(p), l=l, text=text, cw2=cw2, **args )
		return Control.__new__( cls, ui,  mc.textFieldGrp )

class TextFieldButtonGrp( Control ):
	def __new__( cls, uiname=None, p=None, l='textField', text='', cw3=[100, 100, 10], **args ):
		ui = mc.textFieldButtonGrp( uiname, p=getCurrent(p), l=l, text=text, cw3=cw3, **args )
		return Control.__new__( cls, ui,  mc.textFieldButtonGrp )
# =================================================================================================

# Button series.===================================================================================
class Button( Control ):
	def __new__( cls, uiname=None, p=None, **args ):
		ui = mc.button( uiname, p=getCurrent(p), **args )
		return Control.__new__( cls, ui, mc.button )


class RadioButtonGrp( Control ):
	def __new__( cls, uiname=None, **args ):
		ui = mc.radioButtonGrp( uiname, **args )
		return Control.__new__( cls, ui, mc.radioButtonGrp )
# =================================================================================================
# /////////////////////////////////////////////////////////////////////////////////////////////////





# Editors./////////////////////////////////////////////////////////////////////////////////////////
# Outliner series.=================================================================================
class NodeOutliner( Control ):
	def __new__( cls, uiname=None, **args ):
		ui = mc.nodeOutliner( uiname, **args )
		return Control.__new__( cls, ui, mc.nodeOutliner )
# =================================================================================================

# List series.=====================================================================================
class TextScrollList( Control ):
	def __new__( cls, uiname=None, **args ):
		ui = mc.textScrollList( uiname, **args )
		return Control.__new__( cls, ui, mc.textScrollList )
# =================================================================================================
# /////////////////////////////////////////////////////////////////////////////////////////////////
