#!/usr/bin/env python
# coding: utf-8

# # EC Find
# Library for finding connected Biologic devices.

# # API
# All functions of the BL Find DLL are implemented under their corresponding names. In addition the following convenience functions are implemented.
# 
# **find_devices( connection ):** Returns a list of Devices of the gievn connection type.
# 
# # Device
# Represents the descriptors of a device.

# In[1]:


import os
import logging
import ctypes as c
import platform
import pkg_resources


# In[2]:


class Device():
    """
    Represents a device.
    """
    
    def __init__(
        self,
        connection,
        address,
        kind, 
        sn,
        gateway = None,
        netmask = None,
        mac     = None,
        idn     = None,
        name    = None
    ):
        """
        :param connection: The connection type used for the device.
            Values are [ 'usb', 'ethernet' ],
        :param addess: The IP Address for ethernet devices, 
            or the USB plug index for USB devices.
        :param kind: The device type.
        :param sn: The device's serial number.
        :param gateway: Device's gateway, for ethernet devices only.
            [Default: None]
        :param netmask: Device's netmask, for ethernet devices only.
            [Default: None]
        :param mac: Device's MAC address, for ethernet devices only.
            [Default: None]
        :param idn: Device's identifier, for ethernet devices only.
            [Default: None]
        :param name: Device's name, for ethernet devices only.
            [Default: None]
        """
        
        self.connection = connection
        self.address    = address
        self.kind       = kind
        self.sn         = sn
        self.gateway    = gateway
        self.netmask    = netmask
        self.mac        = mac
        self.idn        = idn
        self.name       = name
       
    
    @property
    def connection_string( self ):
        if self.connection == 'USB':
            return 'USB{}'.format( self.address )
        
        else:
            return self.address


# In[3]:


#--- init ---
# get platform architecture
arch = platform.architecture()
bits = arch[ 0 ]
bits = bits.replace( 'bit', '' )
bits = int( bits )
logging.debug( '[ec_find] Running on {}-bit platform.'.format( bits ) )

bits = '' if ( bits == 32 ) else '64'
dll_file = os.path.join( 
    pkg_resources.resource_filename( 'easy_biologic', 'techniques' ),
    'blfind{}.dll'.format( bits )
)
__dll = c.WinDLL( dll_file )

# load DLL functions
BL_FindEChemDev = __dll[ 'BL_FindEChemDev' ]
BL_FindEChemDev.restype = c.c_int

BL_FindEChemEthDev = __dll[ 'BL_FindEChemEthDev' ]
BL_FindEChemEthDev.restype = c.c_int

BL_FindEChemUsbDev = __dll[ 'BL_FindEChemUsbDev' ]
BL_FindEChemUsbDev.restype = c.c_int

BL_SetConfig = __dll[ 'BL_SetConfig' ]
BL_SetConfig.restype = c.c_int

BL_GetErrorMsg = __dll[ 'BL_GetErrorMsg' ]
BL_GetErrorMsg.restype = None


#--- methods ---
    

def find_devices( connection = None ):
    """
    Find connected devices.

    :param connection: The connection type to inspect. 
        Values are [ None, 'usb', 'eth' ].
        None searches USB and ethernet,
        'usb' and 'eth' search only USB or ethernet, respectively.

    :return: An array of Devices.
    """
    buffer_len = 4096
    idn  = c.create_string_buffer( buffer_len )
    size = c.c_uint32( buffer_len )
    num  = c.c_uint32()

    if connection is None:
        func = BL_FindEChemDev

    elif connection == 'usb':
        func = BL_FindEChemUsbDev

    elif connection == 'eth':
        func = BL_FindEChemEthDev

    else:
        # invalid connection type
        raise ValueError( 
            'Invalid connection type {}. Must be None, \'usb\', or \'eth\'.'.format(
                connection
            ) 
        )

    err = raise_exception(
        func(
            c.byref( idn  ),
            c.byref( size ),
            c.byref( num  )
        )
    )
    
    if err is not True:
        # unknown error
        raise RuntimeError( 'Unknown error type {}.'.format( err ) )

    # successful call
    # idn is filled with every character null terminated
    # so must remove evey other character
    idn_len = range( len ( idn ) ) 
    
    # check if odd positions are null terminators
    char_term = [ 
        ( idn[ i ] == b'\x00' ) 
        for i in idn_len
        if ( i % 2 == 1 ) 
    ]

    if all( char_term ):
        # all odd positions are null terminators, remove them
        idn = idn[ ::2 ]

    idn = idn.decode( 'utf-8' )

    # devices are separated by %
    ids = idn.split( '%' )
    ids = ids[ :-1 ] # final element is null padding
    
    # create devices
    dev_keys = [
        'connection',
        'address',
        'gateway',
        'netmask', 
        'mac', 
        'idn', 
        'kind', 
        'sn',
        'name'
    ]
    
    devices = []
    for idd in ids:
        desc = idd.split( '$' ) # descriptors are separated by $
        desc = [ None if ( d == '' ) else d for d in desc ]
        desc = dict( zip( dev_keys, desc ) ) # create dictionary of descriptors
        
        connection = desc[ 'connection' ]
        address = desc[ 'address' ]
        kind = desc[ 'kind' ]
        sn = desc[ 'sn' ]
        
        del desc[ 'connection' ]
        del desc[ 'address' ]
        del desc[ 'kind' ]
        del desc[ 'sn' ]
        
        devices.append( Device(
            connection,
            address,
            kind, 
            sn,
            **desc
        ) ) # add new device

    return devices


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

    elif err == -1:
        # unknown error
        raise RuntimeError( 'Unknown Error.' )

    elif err == -2:
        # parameter error
        raise TypeError( 'Invalid parameter.' )

    elif err == -20:
        raise RuntimeError( 'Find failed.' )

    else:
        return err
            


# # Work

# In[ ]:




