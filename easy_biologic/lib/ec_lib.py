#!/usr/bin/env python
# coding: utf-8

# # EC Lib
# For basic communication with Biologic devices. Imports selected DLL functions and implements convenience functions.

# ## API
# 
# ### Methods
# **connect( address, timeout = 5 ):** Connects to the device at the given address.
# 
# **disconnect( idn ):** Disconnects given device.
# 
# **is_connected( address ):** Checks if teh device at the given address is connected.
# 
# **is_channel_connected( idn, ch ):** Checks whether the given device channel is connected.
# 
# **get_channels( idn, length = 16 ):** Returns a list of booleans of whether the cahnnel at the index exists.
# 
# **channel_info( idn, ch ):** Returns a ChannlInfo struct of the given device channel.
# 
# **load_technique( idn, ch, technique, params, first = True, last = True, verbose = False ):** 
# Loads the technique with parameter on the given device channel.
# 
# **create_parameter( name, value, index, kind = None ):** 
# Creates an EccParam struct.
# 
# **update_paramters( idn, ch, technique, params, tech_index = 0 ):** 
# Updates the paramters of a technique on teh given device channel.
# 
# **start_channel( idn, ch ):** Starts the given device channel.
# 
# **start_channels( idn, ch ):** Starts the given device channels.
# 
# **srop_channel( idn, ch ):** Stops the given device channel.
# 
# **srop_channels( idn, chs ):** Stops the given device channels.
# 
# **get_values( idn, ch ):** Gets the current values and states of the given device channel.
# 
# **raise_exception( err ):** Raises an exception based on a calls error code. 

# In[2]:


# standard imports
import logging
import os
import ctypes as c
import platform
import pkg_resources
from enum import Enum

from .ec_errors import EcError


# ## Constants

# In[8]:


class IRange( Enum ):
    """
    Current ranges.
    """
    p100 = 0
    n1   = 1
    n10  = 2
    n100 = 3
    u1   = 4
    u10  = 5
    u100 = 6
    m1   = 7
    m10  = 8
    m100 = 9
    a1   = 10 # 1 amp
    
    KEEP    = -1
    BOOSTER = 11
    AUTO    = 12
    
    
class ERange( Enum ):
    """
    Voltage ranges
    """
    v2_5 = 0
    v5   = 1
    v10  = 2
    
    AUTO = 3
    
    
class ConnectionType( Enum ):
    """
    Connection types.
    """
    GROUNDED = 0
    FLOATING = 1
    
    
class TechniqueId( Enum ):
    """
    Technique identifiers.
    """
    NONE  = 0
    OCV   = 100 # open circuit voltage
    CA    = 101 # chrono-amperometry
    CP    = 102 # chrono-potentiometry
    CV    = 103 # cyclic voltammetry
    PEIS  = 104 # potentio electrochemical impedance
    
    CALIMIT = 157 # chrono-amperometry with limits
    

class ChannelState( Enum ):
    """
    Channel state.
    """
    STOP  = 0
    RUN   = 1
    PAUSE = 2
    
    
class ParameterType( Enum ):
    """
    Paramter type.
    """
    INT32    = 0
    BOOLEAN  = 1
    SINGLE   = 2


# ## Structs

# In[26]:


# Device Info Structure
class DeviceInfo( c.Structure ):
    """
    Stores information about a device.
    """
    _fields_ = [
        ( "DeviceCode",        c.c_int32 ),
        ( "RAMSize",           c.c_int32 ),
        ( "CPU",               c.c_int32 ),
        ( "NumberOfChannels",  c.c_int32 ),
        ( "NumberOfSlots",     c.c_int32 ),
        ( "FirmwareVersion",   c.c_int32 ),
        ( "FirmwareDate_yyyy", c.c_int32 ),
        ( "FirmwareDate_mm",   c.c_int32 ),
        ( "FirmwareDate_dd",   c.c_int32 ),
        ( "HTdisplayOn",       c.c_int32 ),
        ( "NbOfConnectedPC",   c.c_int32 )
    ];
    

class ChannelInfo( c.Structure ):
    """
    Stores information of a channel.
    """
    _fields_ = [
        ( 'Channel',            c.c_int32 ),
        ( 'BoardVersion',       c.c_int32 ),
        ( 'BoardSerialNumber',  c.c_int32 ),
        ( 'FirmwareVersion',    c.c_int32 ),
        ( 'XilinxVersion',      c.c_int32 ),
        ( 'AmpCode',            c.c_int32 ),
        ( 'NbAmps',             c.c_int32 ),
        ( 'Lcboard',            c.c_int32 ),
        ( 'Zboard',             c.c_int32 ),
        ( 'RESERVED',           c.c_int32 ),
        ( 'RESERVED',           c.c_int32 ),
        ( 'MemSize',            c.c_int32 ),
        ( 'State',              c.c_int32 ),
        ( 'MaxIRange',          c.c_int32 ),
        ( 'MinIRange',          c.c_int32 ),
        ( 'MaxBandwidth',       c.c_int32 ),
        ( 'NbOfTechniques',     c.c_int32 )
        
    ]
    

class EccParam( c.Structure ):
    """
    Represents a single technique parameter.
    """
    _fields_ = [
        ( 'ParamStr',   c.c_char* 64 ),
        ( 'ParamType',  c.c_int32  ),
        ( 'ParamVal',   c.c_int32  ),
        ( 'ParamIndex', c.c_int32  )
    ]
    

class EccParams( c.Structure ):
    """
    Represents a list of technique parameters.
    """
    _fields_ = [
        ( 'len',     c.c_int32 ),
        ( 'pParams', c.POINTER( EccParam ) )
    ]
    
    
class CurrentValues( c.Structure ):
    """
    Represents the values measured from and states of the device.
    """
    _fields_ = [
        ( 'State',       c.c_int32 ),
        ( 'MemFilled',   c.c_int32 ),
        ( 'TimeBase',    c.c_float ),
        ( 'Ewe',         c.c_float ),
        ( 'EweRangeMin', c.c_float ),
        ( 'EweRangeMax', c.c_float ),
        ( 'Ece',         c.c_float ),
        ( 'EceRangeMin', c.c_float ),
        ( 'EceRangeMax', c.c_float ),
        ( 'Eoverflow',   c.c_int32 ),
        ( 'I',           c.c_float ),
        ( 'IRange',      c.c_int32 ),
        ( 'Ioverflow',   c.c_int32 ),
        ( 'ElapsedTime', c.c_float ),
        ( 'Freq',        c.c_float ),
        ( 'Rcomp',       c.c_float ),
        ( 'Saturation',  c.c_int32 ),
        ( 'OptErr',      c.c_int32 ),
        ( 'OptPos',      c.c_int32 )
    ]
    
    
class DataInfo( c.Structure ):
    """
    Represents metadata for the values measured for a technique.
    Used to parse the data collected from the device.
    """
    _fields_ = [
        ( 'IRQskipped',      c.c_int32  ),
        ( 'NbRows',          c.c_int32  ),
        ( 'NbCols',          c.c_int32  ),
        ( 'TechniqueIndex',  c.c_int32  ),
        ( 'TechniqueID',     c.c_int32  ),
        ( 'ProcessIndex',    c.c_int32  ),
        ( 'loop',            c.c_int32  ),
        ( 'StartTime',       c.c_double ),
        ( 'MuxPad',          c.c_int32  )
    ]


# ## DLL Methods

# In[ ]:


#--- init ---
# get platform architecture
arch = platform.architecture()
bits = arch[ 0 ]
bits = bits.replace( 'bit', '' )
bits = int( bits )
logging.debug( '[biologic_controller] Running on {}-bit platform.'.format( bits ) )

bits = '' if ( bits == 32 ) else '64'
dll_file = os.path.join(
    pkg_resources.resource_filename( 'easy_biologic', 'techniques' ),
    'EClib{}.dll'.format( bits )
)
__dll = c.WinDLL( dll_file )

# load DLL functions
# hardware functions
BL_Connect = __dll[ 'BL_Connect' ]
BL_Connect.restype = c.c_int32

BL_Disconnect = __dll[ 'BL_Disconnect' ]
BL_Disconnect.restype = c.c_int32

BL_TestConnection = __dll[ 'BL_TestConnection' ]
BL_TestConnection.restype = c.c_int32

BL_LoadFirmware = __dll[ 'BL_LoadFirmware' ]
BL_LoadFirmware.restype = c.c_int32

BL_IsChannelPlugged = __dll[ 'BL_IsChannelPlugged' ]
BL_IsChannelPlugged.restype = c.c_bool

BL_GetChannelsPlugged = __dll[ 'BL_GetChannelsPlugged' ]
BL_GetChannelsPlugged.restype = c.c_int32

BL_GetChannelInfos = __dll[ 'BL_GetChannelInfos' ]
BL_GetChannelInfos.restype = c.c_int32

# technique functions

BL_LoadTechnique = __dll[ 'BL_LoadTechnique' ]
BL_LoadTechnique.restype = c.c_int32

BL_DefineBoolParameter = __dll[ 'BL_DefineBoolParameter' ]
BL_DefineBoolParameter.restype = c.c_int32

BL_DefineSglParameter = __dll[ 'BL_DefineSglParameter' ]
BL_DefineSglParameter.restype = c.c_int32

BL_DefineIntParameter = __dll[ 'BL_DefineIntParameter' ]
BL_DefineIntParameter.restype = c.c_int32

BL_UpdateParameters = __dll[ 'BL_UpdateParameters' ]
BL_UpdateParameters.restype = c.c_int32

BL_StartChannel = __dll[ 'BL_StartChannel' ]
BL_StartChannel.restype = c.c_int32

BL_StartChannels = __dll[ 'BL_StartChannels' ]
BL_StartChannels.restype = c.c_int32

BL_StopChannel = __dll[ 'BL_StopChannel' ]
BL_StopChannel.restype = c.c_int32

BL_StopChannels = __dll[ 'BL_StopChannels' ]
BL_StopChannels.restype = c.c_int32

# data functions

BL_GetCurrentValues = __dll[ 'BL_GetCurrentValues' ]
BL_GetCurrentValues.restype = c.c_int32

BL_GetData = __dll[ 'BL_GetData' ]
BL_GetData.restype = c.c_int32

BL_ConvertNumericIntoSingle = __dll[ 'BL_ConvertNumericIntoSingle' ]
BL_ConvertNumericIntoSingle.restype = c.c_int32


# ## Methods

# In[28]:


def connect( address, timeout = 5 ):
    """
    Connect to the device at the given address.
    
    :param address: Address of the device.
    :param timout: Timout in seconds. [Default: 5]
    :returns: A tuple of ( id, info ), where id is the connection id, 
        and info is a DeviceInfo structure.
    """
    address = c.create_string_buffer( address.encode( 'utf-8' ) )
    timeout = c.c_uint8( timeout )
    idn     = c.c_int32()
    info    = DeviceInfo()
    
    validate( BL_Connect(
        c.byref( address ),
        timeout,
        c.byref( idn ),
        c.byref( info )
    ) )
    
    return ( idn.value, info )


def disconnect( idn ):
    """
    Disconnect from the given device.
    
    :param address: The address of the device.
    """
    idn = c.c_int32( idn )
    
    validate(
        BL_Disconnect( idn )
    )
    
    
def is_connected( idn ):
    """
    Returns whether the given device is connected or not.
    
    :param idn: The device id.
    :returns: Boolean of the connection state, or the error code.
    """
    idn = c.c_int32( idn )
    
    try:
        validate( 
            BL_TestConnection( idn )
        )
        
    except:
        return False
    
    return True
    

def init_channels( idn, chs, force_reload = False, bin_file = None, xlx_file = None ):
    """
    Initializes a channel by loading its firmware.
    
    :param idn: Device identifier.
    :param chs: List of channels to initialize.
    :param force_reload: Boolean indicating whether to force a firmware reload each time.
        [Default: False]
    :param bin: bin file containing, or None to use default.
        [Default: None]
    :param xlx_file: xilinx file, or None to use default.
        [Default: None]
    """
    length = max( chs ) + 1
    results = ( c.c_int32* length )()
    active = create_active_array(  chs, length )
    idn = c.c_int32( idn )
    show_gauge = c.c_bool( False )
    
    bin_file = (
        c.c_void_p() 
        if ( bin_file is None ) 
        else c.byref( 
            c.create_string_buffer( 
                bin_file.encode( 'utf-8' ) 
            ) 
        )
    )
    
    xlx_file = (
        c.c_void_p() 
        if ( xlx_file is None ) 
        else c.byref( 
            c.create_string_buffer( 
                xlx_file.encode( 'utf-8' )
            ) 
        )
    )
    
    validate(
        BL_LoadFirmware(
            idn, 
            c.byref( active ), 
            c.byref( results ), 
            length, 
            show_gauge,
            force_reload, 
            bin_file, 
            xlx_file
        )
    )

    
def is_channel_connected( idn, ch ):
    idn = c.c_int32( idn )
    ch = c.c_uint8( ch )
    
    conn = BL_IsChannelPlugged( idn, ch )
    
    return conn.value
    

def get_channels( idn, size = 16 ):
    """
    Returns the plugged state of channels.
    
    :param idn: The device id.
    :param size: The number of channels. [Default: 16]
    :return: A list of booleans indicating the plugged state of the channel.
    """
    idn = c.c_int32( idn )
    channels = ( c.c_uint8* size )()
    size = c.c_int32( size )
    
    validate(
        BL_GetChannelsPlugged(
            idn, c.byref( channels ), size
        )
    )
    
    return [ ( ch == 1 ) for ch in channels ]


def channel_info( idn, ch ):
    """
    Returns information on the specified channel.
    
    :param idn: The device id.
    :param ch: The channel.
    :returns: ChannelInfo structure.
    """
    idn  = c.c_int32( idn )
    ch   = c.c_uint8( ch )
    info = ChannelInfo()
    
    validate( 
        BL_GetChannelInfos(
            idn, ch, c.byref( info )
        )
    )
    
    return info


def load_technique( 
    idn, 
    ch, 
    technique, 
    params, 
    first = True, 
    last = True, 
    verbose = False
):
    """
    Loads a technique onto a specified device channel.
    
    :param idn: Device id.
    :param ch: Channel.
    :param technique: Name of the technique file.
    :param params: EccParams structure for the technique.
    :param first: True if the technique is loaded first. [Defualt: True]
    :param last: True if this is the last technique. [Default: True]
    :param verbose: Echoes the sent parameters for debugging. [Default: False]
    """
    idn = c.c_int32( idn )
    ch  = c.c_uint8( ch )
 
    technique_path = technique_file( technique )
    technique = c.create_string_buffer( technique_path.encode( 'utf-8' ) )
    
    first = c.c_bool( first )
    last  = c.c_bool( last )
    verbose = c.c_bool( verbose )
    
    validate(
        BL_LoadTechnique( 
            idn, ch, c.byref( technique ), params, first, last, verbose 
        )
    )
    
    
def create_parameter( name, value, index = 0, kind = None ):
    """
    Factory to create an EccParam structure.
    
    :param name: Paramter name.
    :param value: Value fo the parameter. 
        The kind is interpreted to be a bool, integer, or single (float),
        unless the kind parameter is passed.
    :param index: Parameter index. [Default: 0]
    :param kind: The kind of parameter, or None to interpret from the value.
        Values are [ None, 'bool', 'int', 'single' ].
        [Default: None]
    :returns: An EccParam structure.
    """
    if kind is None:
        # interpret kind from value
        val_kind = type( value )
        
        if val_kind is bool:
            kind = 'bool'
            
        elif val_kind is int:
            kind = 'int'
            
        elif val_kind is float:
            kind = 'single'
            
        else:
            raise TypeError( '[ec_lib] Invalid value type {}.'.format( val_kind ) )
    
    # define parameter 
    if kind is 'bool':
        create = BL_DefineBoolParameter
        value = c.c_bool( value )
        
    elif kind is 'int':
        create = BL_DefineIntParameter
        value = c.c_int32( value )
        
    elif kind is 'single':
        create = BL_DefineSglParameter
        value = c.c_float( value )
        
    else:
        raise ValueError( '[ec_lib] Invalid kind {}.'.format( kind ) )
    
    name = name.encode( 'utf-8' )
    index = c.c_int32( index )
    param = EccParam()
    
    create( name, value, index, c.byref( param ) )
    
    return param


def combine_parameters( params ):
    """
    Creates an ECCParams list of parameters.
    
    :param params: List of parameters to combine.
    :returns: EccParams structure.
    """
    num_params = len( params )
    param_list = ( EccParam* num_params )( *params )
    length = c.c_int32( num_params )
    
    params = EccParams()
    params.len = length
    params.pParams = c.cast( param_list, c.POINTER( EccParam ) )


def create_parameters( params, index = 0 ):
    """
    Creates an EccParams list of parameters.
    
    :param params: A dictionary of parameters, with keys as
        the parameter name and values as the parameter value or a list of values.
        If a value is a list, one parameter is created for each value.
    :param index: Starting index for the parameters.
        For lists of values, the index of the value in the list is added to the index.
        [Default: 0]
    :returns: EccParams structure.
    """
    param_list = []
    for name, values in params.items():
        if type( values ) is not list:
            # single value given, turn into list
            values = [ values ]
            
        for idx, value in enumerate( values ):
            # create parameter for each value
            param = create_parameter( name, value, index + idx )
            param_list.append( param )
        
    num_params = len( param_list )
    param_list = ( EccParam* num_params )( *param_list )
    length = c.c_int32( num_params )
    
    params = EccParams()
    params.len = length
    params.pParams = c.cast( param_list, c.POINTER( EccParam ) )
    
    return params
    

def update_parameters( idn, ch, technique, params, index = 0, device = None ):
    """
    Updates the parameters of a technique.
    
    :param idn: Device identifier.
    :param ch: Channel number.
    :param technique: Name of the technique file.
    :param params: New parameters to use as an EccParams struct.
    :param index: Index of the technique. [Default: 0]
    :param device: Type of device. Used to modify technique. 
        [Default: None]
    """
    
    idn = c.c_int32( idn )
    ch  = c.c_uint8( ch )
    
    technique = technique_file( technique, device )
    technique = c.create_string_buffer( technique.encode( 'utf-8' ) )
    index = c.c_int32( index )
    
    validate(
        BL_UpdateParameters(
            idn, ch, index, params, c.byref( technique )
        )
    )
    
    
def start_channel( idn, ch ):
    """
    Starts techniques loaded on a channel.
    
    :param idn: Device identifier.
    :param ch: Channel to start.
    """
    idn = c.c_int32( idn )
    ch  = c.c_uint8( ch )
    
    validate(
        BL_StartChannel( 
            idn, ch 
        )
    )


def start_channels( idn, chs ):
    """
    Starts techniques loaded on the given channels.
    
    :param idn: Device identifier.
    :param chs: List of channels to start.
    """
    num_chs = max( chs ) + 1
    results = ( c.c_int32* num_chs )()
    active = create_active_array( chs, num_chs )
    idn = c.c_int32( idn )
    
    err = validate(
        BL_StartChannel( 
            idn, c.byref( active ), c.byref( results ), num_chs
        )
    )
    
    return err


def stop_channel( idn, ch ):
    """
    Stops techniques loaded on a channel.
    
    :param idn: Device identifier.
    :param ch: Channel to stop.
    """
    idn = c.c_int32( idn )
    ch  = c.c_uint8( ch )
    
    err = validate(
        BL_StopChannel( 
            idn, ch 
        )
    )
    
    return err


def stop_channels( idn, chs ):
    """
    Stops techniques loaded on the given channels.
    
    :param idn: Device identifier.
    :param chs: List of channels to stop.
    """
    num_chs = max( chs ) + 1
    results = ( c.c_int32* num_chs )()
    active = create_active_array( chs, num_chs )
    idn = c.c_int32( idn )
    
    validate(
        BL_StopChannel( 
            idn, c.byref( active ), c.byref( results ), num_chs
        )
    )
    
    return err


def get_values( idn, ch ):
    """
    Gets the current data values on the given device channel.

    :param idn: Device identifier.
    :param ch: Channel.
    :returns: CurrentValues object.
    """
    idn = c.c_int32( idn )
    ch  = c.c_uint8( ch )
    values = CurrentValues()

    validate(
        BL_GetCurrentValues(
            idn, ch, c.byref( values )
        )
    )

    return values
    
    
def get_data( idn, ch ):
    """
    Gets data from the given device channel.
    
    :param idn: Device identifier.
    :param ch: Channel.
    :returns: A tuple of ( data, data_info, current_values ) where
        data_info is a DataInfo object representing the data's metadata, 
        data is a data array, and 
        current_values is a CurrentValues object.
    """
    idn  = c.c_int32( idn )
    ch   = c.c_uint8( ch )
    data = ( c.c_uint32* 1000 )()
    info = DataInfo()
    values = CurrentValues()
        
    validate(
        BL_GetData(
            idn, ch, c.byref( data ), c.byref( info ), c.byref( values )
        )
    )

    return ( data, info, values )
    
    
def convert_numeric( num ):
    """
    Converts a numeric value into a single (float).
    
    :param num: Numeric value to convert.
    :returns: Value of numeric as a float.
    """
    num = c.c_uint32( num )
    val = c.c_float()
    
    validate( 
        BL_ConvertNumericIntoSingle( 
            num, c.byref( val ) 
        )
    )
    
    return val.value


#--- helper functions ---


def validate( err ):
    """
    Raises an exception based on the return value of the function

    :returns: True if function succeeded, 
        or the error code if no known error is associated to it.
    :raise: RuntimeError for an unknown error.
    :raise: TypeError for an invalid parameter.
    """
    if err == 0:
        # no error
        return True
    
    else:
        raise EcError( err )
    
    
def create_active_array( active, size = None, kind = c.c_uint8 ):
    """
    Creates an array of active elements from a list.
    
    :param active: List of active elements.
    :param size: Size of the array. If None the maximum active index is used.
        [Default: None]
    :param kind: Kind of array elements. [Default: ctypes.c_uint8]
    :returns: An array of elements where active elements are 1, and inactive are 0.
    """
    if size is None:
        size = max( active ) + 1
        
    arr = ( kind* size )()
    for index in active:
        # activate index
        arr[ index ] = 1
        
    return arr


def technique_file( technique, device = None ):
    """
    Returns the file name of teh given technique for the given device.
    
    :param technique: Technique name.
    :param device: Kind of device. [Default: None]
    :returns: Technique file.
    """
    file_type = '.ecc'
    sp300_mod = '4'
    
    if (
        device is not None and
        device.upper() == 'SP-300' and 
        not technique.endswith( sp300_mod )
    ):
        # modify technqiues for SP-300 devices
        technique += sp300_mod
        
    if not technique.endswith( file_type ):
        # append file type extenstion if needed
        technique += file_type
    
    return technique.lower()


# # Work

# In[ ]:




