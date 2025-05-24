# -*- coding:utf-8 -*-

import sys
import traceback
import maya.OpenMaya as OpenMaya
import maya.cmds as mc

# setup
import os
mel_name = os.path.join(os.path.dirname(__file__), 'globalMelPyConnector.mel')
from maya import mel
mel.eval('source "%s";' % mel_name.replace(os.sep, '/'))
from ... import verutil

# Get maya numerical version.////////////////////////////////////////////////////////////////////
def getMayaVer():
	strver = mc.about( v=True )
	return float( strver.split()[0] )



# Output error code for detail. ///////////////////////////////////////////////////////////////////
def errorout( israise=True ):
	# Get informations of error.-------------------------------------------------------------------
	# 0 : error type.
	# 1 : exception's class with message.
	# 2 : traceback object.
	info = sys.exc_info()
	tb = info[2]
	# ---------------------------------------------------------------------------------------------


	# Get traceback informations as list.----------------------------------------------------------
	tbfmt = traceback.format_tb( tb )
	tbinfo = traceback.extract_tb( tb )
	if len( tbinfo ) == 0:
		return
	# ---------------------------------------------------------------------------------------------

	# Get error type.------------------------------------------------------------------------------
	errTypeStr = str( type( info[1] ) )
	errTypeList = errTypeStr.split( "'" )
	errType = errTypeList[1].split( '.' )[-1]
	# ---------------------------------------------------------------------------------------------

	msg = '\n'.rjust( 80, '-' )
	msg += '# Python Error #\n'
	msg += '\n'.rjust( 80, '-' )
	msg += '    All Error Code List\n'
	msg += '    %s' % ('    '.join( [ '+' + x.replace( '    ', '        ' ) for x in tbfmt ] ))
	msg += '\n'.rjust( 80, '-' )
	msg += '    File       : %s\n' % tbinfo[-1][0]
	msg += '    Line       : %s in "%s"\n' % ( tbinfo[-1][1], tbinfo[-1][2] )
	msg += '    Error Type : %s\n' % (errType)
	msg += '    Message    : %s\n' % str( info[1] )
	msg += '\n'.rjust( 80, '-' )

	print(msg)

	# Call error if the argument "israise" is True.------------------------------------------------
	if israise == True:
		raise info[1]
	# ---------------------------------------------------------------------------------------------


def error( message ):
	OpenMaya.MGlobal.displayError( message )

def warning( message ):
	OpenMaya.MGlobal.displayWarning( message )
# /////////////////////////////////////////////////////////////////////////////////////////////////




# /////////////////////////////////////////////////////////////////////////////////////////////////
def importModule( module, isReload=False, absolute=True, isReport=True ):
	try:
		mod = __import__( module )
	except Exception as e:
		if isReport == True:
			print('-- Module loading error --')
			print('  {}'.format(e.args[0]))
			print('--')
		return None

	if absolute == True:
		components = module.split( '.' )
		for c in components[1:]:
			mod = getattr( mod, c )

	if isReload == True:
		print('Reload Module : {}'.format(module))
		try:
			verutil.reload_module( mod )
		except Exception as e:
			raise e
	return mod
# /////////////////////////////////////////////////////////////////////////////////////////////////



# /////////////////////////////////////////////////////////////////////////////////////////////////
class GlobalMelPyConnector( object ):
	'''This is a singleton instanced class to attach python command as mel command
to GUI that can be passed only mel command.
'''
	def __new__( cls ):
		if not hasattr( cls, '__instance__' ):
			cls.__instance__ = object.__new__( cls )
			cls.__commandStocker = {}
		return cls.__instance__

	def stockCommand( self, tag, command ):
		self.__commandStocker[ tag ] = command
	def exeCommand( self, tag ):
		self.__commandStocker[tag]()
# /////////////////////////////////////////////////////////////////////////////////////////////////

