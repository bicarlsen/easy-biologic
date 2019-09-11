#!/usr/bin/env python
# coding: utf-8

# # EC Lib
# For basic communication with Biologic devices. Imports selected DLL functions and implements convenience functions.

# ## API
# 
# ### Methods
# **connect( address, timeout = 5 ):** Connects to the device at the given address.
# 
# **disconnect( address ):** Disconnects from the device at the given address.
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
# **start_channels( idn, ch ):** Starts teh given device channels.
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
import ctypes as c
import platform


# In[23]:


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
        ( 'XilinkxVersion',     c.c_int32 ),
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
        ( 'pParams', EccParam* 64 )
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


# In[24]:


#--- init ---
# get platform architecture
arch = platform.architecture()
bits = arch[ 0 ]
bits = bits.replace( 'bit', '' )
bits = int( bits )
logging.debug( '[biologic_controller] Running on {}-bit platform.'.format( bits ) )

bits = '' if ( bits == 32 ) else '64'
__dll = c.WinDLL(
    '../techniques/EClib{}.dll'.format( bits )
)

# load DLL functions
# hardware functions
BL_Connect = __dll[ 'BL_Connect' ]
BL_Connect.restype = c.c_int32

BL_Disconnect = __dll[ 'BL_Disconnect' ]
BL_Disconnect.restype = c.c_int32

BL_TestConnection = __dll[ 'BL_TestConnection' ]
BL_TestConnection.restype = c.c_int32

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

#--- methods ---

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
    
    err = raise_exception( BL_Connect(
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
    :returns: True if successful, or the error code.
    """
    idn = c.c_int32( idn )
    
    err = raise_exception(
        BL_Disconnect( idn )
    )
    
    return err
    
    
def is_connected( idn ):
    """
    Returns whether the given device is connected or not.
    
    :param idn: The device id.
    :returns: Boolean of the connection state, or the error code.
    """
    idn = c.c_int32( idn )
    
    try:
        err = raise_exception( 
            BL_TestConnection( idn )
        )
        
    except:
        return False
    
    if err == 0:
        return True
    
    else:
        return False
    
    
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
    
    err = raise_exception(
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
    
    err = raise_exception( 
        BL_GetChannleInfos(
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
        The full path is not needed, and '.dll' should be excluded.
    :param first: True if the technique is loaded first. [Defualt: True]
    :param last: True if this is the last technique. [Default: True]
    :param verbose: Echoes the sent parameters for debugging. [Default: False]
    """
    idn = c.c_int32( idn )
    ch  = c.c_uint8( ch )
    technique = c.create_string_buffer( 
        '../techniques/{}.dll'.format( technique ) 
    )
    first = c.c_bool( first )
    last  = c.c_bool( last )
    verbose = c.c_bool( verbose )
    
    err = raise_exception(
        BL_LoadTechnique( 
            idn, ch, c.byref( technique ), params, first, lsat, verbose 
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


def update_parameters( idn, ch, technique, params, tech_index = 0 ):
    """
    Updates the parameters of a technique.
    
    :param idn: Device identifier.
    :param ch: Channel number.
    :param technique: Name of the technique file.
    :param params: New parameters to use as an EccParams struct.
    :param tech_index: Index of the technique. [Default: 0]
    :returns: True on success, or error code of failure.
    """
    
    idn = c.c_int32( idn )
    ch  = c.c_uint8( ch )
    technique = c.create_string_buffer( technique )
    tech_index = c.c_int32( tech_index )
    
    err = raise_exception(
        BL_UpdateParameters(
            idn, ch, tech_index, params, technique
        )
    )
    
    return err
    
    
def start_channel( idn, ch ):
    """
    Starts techniques loaded on a channel.
    
    :param idn: Device identifier.
    :param ch: Channel to start.
    :returns: True on success, or error code of failure.
    """
    idn = c.c_int32( idn )
    ch  = c.c_uint8( ch )
    
    err = raise_exception(
        BL_StartChannel( 
            idn, ch 
        )
    )
    
    return err


def start_channels( idn, chs ):
    """
    Starts techniques loaded on the given channels.
    
    :param idn: Device identifier.
    :param chs: List of channels to start.
    :returns: True on success, or error code of failure.
    """
    num_chs = max( chs )
    results = ( c.c_int32()* num_chs )()
    
    active = ( c.c_uint8( 0 )* num_chs )()
    for ch in chs:
        # activate channel
        active[ ch ] = 1
    
    idn = c.c_int32( idn )
    
    err = raise_exception(
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
    :returns: True on success, or error code of failure.
    """
    idn = c.c_int32( idn )
    ch  = c.c_uint8( ch )
    
    err = raise_exception(
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
    :returns: True on success, or error code of failure.
    """
    num_chs = max( chs )
    results = ( c.c_int32()* num_chs )()
    
    active = ( c.c_uint8( 0 )* num_chs )()
    for ch in chs:
        # activate channel
        active[ ch ] = 1
    
    idn = c.c_int32( idn )
    
    err = raise_exception(
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
        :returns: CurrentValues struct.
        """
        idn = c.c_int32( idn )
        ch  = c.c_uint8( ch )
        values = CurrentValues()
        
        err = raise_exception(
            BL_GetCurrentValues(
                idn, ch, c.byref( values )
            )
        )
        
        return values
    
    
def get_data( idn, ch ):
    """
    Gets data from the given device channel.
    """
    pass
        
    
def raise_exception( err ):
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
    
    if err == -11:
        raise RuntimeError( '[ec_lib] (-11 : ERR_GEN_USBLIBRARYERROR) USB library not loaded in memory.')

    else:
        return err


# # Work

# In[ ]:




