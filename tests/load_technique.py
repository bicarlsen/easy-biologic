import logging
import ctypes as c

# import easy_biologic package
# [https://pypi.org/project/easy-biologic/]
import easy_biologic as ebl
from easy_biologic.lib import ec_lib as ecl #for convenience

# script parameters

debug = True # print debugging messages
device_address = '192.168.1.2'
technique_channel = 0
technique_file = 'ocv.ecc'

technique_params = {
	'Rest_time_T': 		0.1,
	'Record_every_dE': 	0.1,
	'Record_every_dT': 	1.0,
	'E_Range': ecl.ERange.v2_5.value
}
# main script

if debug:
	logging.basicConfig( level = logging.DEBUG ) 


# create a null terminated C string buffer of the technique file
tech_file = c.create_string_buffer( technique_file.encode() )


# Creates an EccParams structure
# by iterating over the dictionary
# interpreting teh data type
# creating the corresponding type of EccParam
# then placing them in a list to create the EccParams
tech_params = ecl.create_parameters( technique_params )

if debug:
	num_params = tech_params.len

	# print created parameters
	print( 'Number of parameters: {}\n'.format( num_params ) )

	for i in range( num_params ):
		param = tech_params.pParams[ i ]

		print( 'Parameter {}'.format( i ) )
		print( 'Name: {}\nType: {}\nValue (integer): {}\nIndex: {}\n'.format(
			param.ParamStr, param.ParamType, param.ParamVal, param.ParamIndex
		) )


# connect to device
# channels are automatically initialized during connection
# with the default firmware using BL_LOADFIRMWARE
bl = ebl.BiologicDevice( device_address )
bl.connect()

if debug:
	print( 'Device Info\n' )
	print( 'Device Type: {}'.format( bl.kind ) )
	print( 'Number of Channels: {}'.format( bl.info.NumberOfChannels ) ) 

	print( '\nChannel Info\n' )
	for ch in bl.channels:
		ch_state = ch.State
		state_err = ''
		try: 
			ch_state = ecl.ChannelState( ch_state )

		except Exception as err:
			state_err = '(Invalid state)'

		print( 'Channel {}'.format( ch.Channel ) )
		print( 'State: {} {}'.format( ch_state, state_err ) )
		print( 'Number of Techniques: {}'.format( ch.NbOfTechniques ) )
		print( 'Min Current Range: {}'.format( ecl.IRange( ch.MinIRange ) ) )
		print( 'Max Current Range: {}'.format( ecl.IRange( ch.MaxIRange ) ) )
		print( '\n' )


# create additional params for load technique
idn 	= c.c_int32( bl.idn )
ch 		= c.c_uint8( technique_channel )
first 	= c.c_bool( True )
last 	= c.c_bool( True )
display = c.c_bool( False )

err_code = ecl.BL_LoadTechnique(
	idn, ch, c.byref( tech_file ), tech_params, first, last, display
)

if debug:
	print( 'Load Technique Error Code: {}'.format( err_code ) )

# clean up
bl.disconnect()