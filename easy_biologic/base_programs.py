#!/usr/bin/env python
# coding: utf-8

# # Base Programs
# Creates basic programs implementing BiologicProgram.

# ## OCV
# ### Params
# **time:** Run time in seconds.
# 
# **time_interval:** Maximum time between readings. 
# [Default: 1]
# 
# **voltage_interval:** Maximum interval between voltage readings.
# [Default: 0.01]
#     
# ## CA
# ### Params
# **voltages:** List of voltages.
# 
# **durations:** List of times in seconds.
# 
# **vs_initial:** If step is vs. initial or previous. 
# [Default: False] 
# 
# **time_interval:** Maximum time interval between points.
# [Default: 1]
#     
# **current_interval:** Maximum current change between points.
# [Default: 0.001]
#             
# **current_range:** Current range. Use ec_lib.IRange.
# [Default: IRange.m10 ]
#             
# ### Methods
# **update_voltage( voltages, durations = None, vs_initial = None ):** Updates the voltage. 
# 
# ## CALimit
# ### Params
# **voltages:** List of voltages.
# 
# **durations:** List of times in seconds.
# 
# **vs_initial:** If step is vs. initial or previous. 
# [Default: False] 
# 
# **time_interval:** Maximum time interval between points.
# [Default: 1]
#     
# **current_interval:** Maximum current change between points.
# [Default: 0.001]
#             
# **current_range:** Current range. Use ec_lib.IRange.
# [Default: IRange.m10 ]
# 
# ### Methods
# **update_voltage( voltages, durations = None, vs_initial = None ):** Updates the voltage.
# 
# ## PEIS
# ### Params
# **voltage:** Initial potential in Volts.
# 
# **amplitude_voltage:** Sinus amplitude in Volts.
# 
# **initial_frequency**: Initial frequency in Hertz.
#        
# **final_frequency:** Final frequency in Hertz.
# 
# **frequency_number:** Number of frequencies.
# 
# **duration:** Overall duration in seconds.
# 
# **vs_initial:** If step is vs. initial or previous. [Default: False]
# 
# **time_interval:** Maximum time interval between points in seconds. [Default: 1]
# 
# **current_interval:** Maximum time interval between points in Amps. [Default: 0.001]
# 
# **sweep:** Defines whether the spacing between frequencies is logarithmic ('log') or linear ('lin'). [Default: 'log'] 
# 
# **repeat:** Number of times to repeat the measurement and average the valuesfor each frequency. [Default: 1]
# 
# **correction:** Drift correction. [Default: False]
# 
# **wait:** Adds a delay before the measurement at each frequency. The delayis expressed as a fraction of the period. [Default: 0]
# 
# ## JV_Scan
# Performs a JV scan.
# 
# ### Params
# **end:** End voltage.
# 
# **start:** Start voltage. 
# [ Defualt: 0 ]
# 
# **step:** Voltage step. 
# [Default: 0.01]
# 
# **rate:** Scan rate in mV/s. 
# [Default: 10]
# 
# **average:** Average over points. 
# [Default: False]
#  
# 
# ## MPP_Tracking
# Performs MPP tracking.
# 
# ### Methods
# **on_timeout( cb, timeout, repeat = True, args = [], kwargs = {}, timeout_type = 'interval' ):** Registers a function to call after a timeout occurs.
# 
# ### Params
# **run_time:** Run time in seconds.
# 
# **init_vmpp:** Initial v_mpp.
# 
# **probe_step:** Voltage step for probe. 
# [Default: 0.01 V]
# 
# **probe_points:** Number of data points to collect for probe. 
# [Default: 5]
# 
# **probe_interval:** How often to probe in seconds. 
# [Default: 2]
# 
# **record_interval:** How often to record a data point in seconds. 
# [Default: 1]
# 
# 
# ## MPP
# Runs MPP tracking and finds the initial Vmpp by finding the Voc, then performing a JV scan.
# 
# ### Params
# **run_time:** Run time in seconds.
# 
# **probe_step:** Voltage step for probe. 
# [Default: 0.01 V]
# 
# **probe_points:** Number of data points to collect for probe. 
# [Default: 5]
# 
# **probe_interval:** How often to probe in seconds. 
# [Default: 2]
# 
# **record_interval:** How often to record a data point in seconds. 
# [Default: 1]
# 
# ## MPP Cycles
# Runs multiple MPP cycles, performing Voc and JV scans at the beginning of each.
# 
# ### Params
# **run_time:** Run time in seconds
# 
# **scan_interval:** How often to perform a JV scan.
# 
# **probe_step:** Voltage step for probe. [Default: 0.01 V]
# 
# **probe_points:** Number of data points to collect for probe. [Default: 5]
# 
# **probe_interval:** How often to probe in seconds. [Default: 2]
# 
# **record_interval:** How often to record a data point in seconds. [Default: 1]

# In[ ]:


import os
import math
import time
from datetime import datetime as dt
import asyncio
from collections import namedtuple

from . import BiologicProgram
from .program import CallBack
from .lib import ec_lib as ecl
from .lib import data_parser as dp
from .lib import technique_fields as tfs


# In[ ]:


class CallBack_Timeout:
    """
    A timeout callback.
    The callback must be started before it can be called.
    """
    
    def __init__( 
        self, 
        program,
        cb, 
        timeout,
        repeat = True, 
        args = [], 
        kwargs = {},
        timeout_type = 'interval'
    ):
        """
        Creates a CallBack_Timeout.

        :param program: BiologicProgram the function is running in.
        :param cb: Callback function to run.
            Should accept the program as the first parameter.
        :param timeout: Timeout is seconds.
        :param repeat: Repeat the callback. 
            If True, repeats indefinitely.
            If a number, repeats that many times.
            If False, only runs once.
            [Default: True]
        :param args: List of arguments to pass to the callback function.
            [Default: []]
        :param kwargs: Dictionary of keywrod arguments to pass to the callback function.
            [Default: {}]
        :param timeout_type: Type of timeout.
            Values are [ 'interval', 'between' ]
            interval: Time between callback starts
            between: Time between last finish and next start
            [Default: 'interval']
        """
        self.__program = program
        self.__cb = CallBack( cb, args, kwargs )
        self.timeout  = timeout
        self.timeout_type = timeout_type
        self.is_alive = False
        
        self.repeat = 1 if ( repeat is False ) else repeat
        
        self.__calls     = 0
        self.__last_call = None
        
        
    @property
    def callback( self ):
        """
        :returns: CallBack structure of the callback function.
        """
        return self.__cb
    
        
    @property
    def elapsed( self ):
        """
        :returns: time since last call.
        """
        return ( time.time() - self.__last_call )
    
    
    @property
    def calls( self ):
        """
        :returns: Number of calls.        
        """
        return self.__calls
    
    
    @property
    def exhausted( self ):
        """
        :returns: If number of calls has reached number of repititions.
        """
        if self.repeat is True:
            return False
        
        return ( self.calls >= self.repeat )

    
    def is_due( self ):
        """
        :returns: If the function is due to be run or not.
        """
        return ( self.elapsed >= self.timeout )
    
    
    def run( self ):
        """
        Runs the callback function.
        """
        # function set up
        cb     = self.callback.function
        args   = self.callback.args
        kwargs = self.callback.kwargs
        
        # internal trackers
        self.__calls += 1
        if self.timeout_type is 'interval':
            self.__last_call = time.time()
        
        # callback
        cb( self.__program, *args, **kwargs )
        
        if self.timeout_type is 'between':
            self.__last_call = time.time()
        
        
    def start( self ):
        """
        Starts the callback.
        """
        self.is_alive = True
        self.__last_call = time.time()
        
    
    def cancel( self ):
        """
        Cancels the callback.
        """
        self.is_alive = False
        
        
    def call( self ):
        """
        Runs the callback is all conditions are met.
        """
        if (
            self.is_alive and
            not self.exhausted and
            self.is_due()
        ):
            self.run()
        


# In[ ]:


#--- helper function ---
def set_defaults( params, defaults, channels ):
    """
    Combines parameter and default dictionaries.
    
    :param params: Parameter or channel parameter dictionary.
    :param defaults: Default dictionary. 
        Values used if key is not present in parameter dictionary.
    :param channels: List of channels or None if params is keyed by channel.
    :returns: Dictionary with defualt values set, if not set in parameters dictionary.
    """
    if channels is None:
        # parameters by channel
        for ch, ch_params in params.items():
            params[ ch ] = { **defaults, **ch_params }
            
    else:
         params = { **defaults, **params }
            
    return params


def map_params( key_map, params, by_channel = True, keep = False, inplace = False ):
    """
    Returns a dictionary with names mapped.
    
    :param key_map: Dictionary keyed by original keys with new keys as values.
    :param params: Dictionary of parameters.
    :param by_channel: Whether params is by channel, or only parameters.
        [Default: True]
    :param keep: True to keep original name, False to remove it.
        [Default: False]
    :param inplace: Transform original params dictionary, or create a new one.
        [Default: False]
    :returns: Dictionary with mapped keys.
    """
    def map_ch_params( ch_params ):
        """
        Maps channel parameters inplace.
        
        :param ch_params: Parameter dictionary.
        :returns: Modified parameter dictionary.
        """
        for o_key, n_key in key_map.items():
            ch_params[ n_key ] = ch_params[ o_key ]

        if not keep:
            # remove original keys
            for o_key in key_map:
                del ch_params[ o_key ]
            
    
    if not inplace:
        params = params.copy()
    
    if by_channel:
        for ch, ch_params in params.items():
            map_ch_params( ch_params )
            
    else:
        map_ch_params( params )
    
    return params


# In[ ]:


class OCV( BiologicProgram ):
    """
    Runs an open circuit voltage scan.
    """
    
    def __init__( 
        self, 
        device, 
        params,
        channels    = None,
        autoconnect = True,
        barrier     = None,
        threaded    = False
    ):
        """
        Params are
        time: Run time in seconds.
        time_interval: Maximum time between readings. [Default: 1]
        voltage_interval: Maximum interval between voltage readings. 
            [Default: 0.01]
        """
        defaults = {
            'time_interval': 1,
            'voltage_interval': 0.01
        }
        params = set_defaults( params, defaults, channels )
        
        super().__init__( 
            device, 
            params, 
            channels    = channels, 
            autoconnect = autoconnect, 
            barrier     = barrier,
            threaded    = threaded
        )
        
        self._techniques = [ 'ocv' ]
        self._fields = namedtuple( 'OCV_Datum', [ 'time', 'voltage' ] )
        self.field_titles = [ 'Time [s]', 'Voltage [V]' ]
        self._data_fields = (
            dp.SP300_Fields.OCV
            if self.device.kind is ecl.DeviceCodes.KBIO_DEV_SP300 else 
            dp.VMP3_Fields.OCV   
        )

        self._parameter_types = tfs.OCV

            
    def run( self, retrieve_data = True ):
        """
        :param retrieve_data: Automatically retrieve and disconenct form device.
            [Default: True]
        """
        # map to ocv params
        key_map = {
            'time': 'Rest_time_T',
            'voltage_interval': 'Record_every_dE',
            'time_interval':    'Record_every_dT'
        }
        params = map_params( key_map, self.params )
            
        fields = None 
        if retrieve_data:
            fields = lambda datum, segment: ( # calculate fields
                dp.calculate_time( # time
                    datum.t_high, 
                    datum.t_low, 
                    segment.info, 
                    segment.values 
                ),

                datum.voltage
            ) 
     
        # run technique
        self._run( 'ocv', params, fields )  


# In[ ]:


class CA( BiologicProgram ):
    """
    Runs a chrono-amperometry technqiue.
    """
    
    def __init__( 
        self, 
        device, 
        params, 
        channels    = None, 
        autoconnect = True,
        barrier     = None,
        threaded    = False
    ):
        """
        Params are
        voltages: List of voltages in Volts.
        durations: List of times in seconds.
        vs_initial: If step is vs. initial or previous. 
            [Default: False]
        time_interval: Maximum time interval between points in seconds. 
            [Default: 1]
        current_interval: Maximum current change between points in Amps. 
            [Default: 0.001]
        """
        defaults = {
            'vs_initial':       False,
            'time_interval':    1.0,
            'current_interval': 1e-3,
            'current_range':    ecl.IRange.m10
        }
        
        params = set_defaults( params, defaults, channels )
        super().__init__( 
            device,  
            params,
            channels    = channels,
            autoconnect = autoconnect, 
            barrier     = barrier,
            threaded    = threaded
        )
        
        self._technqiues = [ 'ca' ]
        self._fields = namedtuple( 'CA_Datum', [
            'time', 'voltage', 'current', 'power', 'cycle'
        ] )
        
        self.field_titles = [ 
            'Time [s]', 
            'Voltage [V]', 
            'Current [A]', 
            'Power [W]', 
            'Cycle' 
        ]
        
        self._data_fields = (
            dp.SP300_Fields.CA
            if self.device.kind is ecl.DeviceCodes.KBIO_DEV_SP300
            else dp.VMP3_Fields.CA
        )
        self._parameter_types = tfs.CA
        
        
    def run( self, retrieve_data = True ):
        """
        :param retrieve_data: Automatically retrieve and disconenct form device.
            [Default: True]
        """
        params = {}
        for ch, ch_params in self.params.items():
            steps = len( ch_params[ 'voltages' ] )
            
            params[ ch ] = {
                'Voltage_step':      ch_params[ 'voltages' ],
                'vs_inital':         [ ch_params[ 'vs_initial' ] ]* steps,
                'Duration_step':     ch_params[ 'durations' ],
                'Step_number':       steps - 1,
                'Record_every_dT':   ch_params[ 'time_interval' ],
                'Record_every_dI':   ch_params[ 'current_interval' ],
                'N_Cycles':          0,
                'I_Range':           ch_params[ 'current_range' ].value
            }

        fields = None
        if retrieve_data:
            fields = lambda datum, segment: (
                dp.calculate_time( 
                    datum.t_high, 
                    datum.t_low, 
                    segment.info, 
                    segment.values 
                ),

                datum.voltage,
                datum.current,
                datum.voltage* datum.current, # power
                datum.cycle
            )
        
        # run technique
        data = self._run( 'ca', params, fields )
    
    
    def update_voltages( 
        self, 
        voltages, 
        durations = None, 
        vs_initial = None 
    ):
        """
        Update voltage and duration parameters
        """
        steps = len( voltages )
        
        params = {
            'Voltage_step': voltages,
            'Step_number':  steps - 1
        }
        
        if durations is not None:
            params[ 'Duration_step' ] = durations
            
        if vs_initial is not None:
            params[ 'vs_initial' ] = vs_initial
        
        self.device.update_parameters(
            self.channel, 
            'ca', 
            params,
            types = self._parameter_types
        )


# In[ ]:


class CP( BiologicProgram ):
    """
    Runs a chorono-potentiometry technqiue.
    """
    
    def __init__( 
        self, 
        device, 
        params, 
        channels    = None, 
        autoconnect = True,
        barrier     = None,
        threaded    = False
    ):
        """
        Params are
        currents: List of currents in Amps.
        durations: List of times in seconds.
        vs_initial: If step is vs. initial or previous. 
            [Default: False]
        time_interval: Maximum time interval between points in seconds. 
            [Default: 1]
        voltage_interval: Maximum voltge change between points in Volts. 
            [Default: 0.001]
        """
        defaults = {
            'vs_initial':       False,
            'time_interval':    1.0,
            'voltage_interval': 1e-3
        }
        
        params = set_defaults( params, defaults, channels )
        super().__init__( 
            device,  
            params,
            channels    = channels,
            autoconnect = autoconnect, 
            barrier     = barrier,
            threaded    = threaded
        )
        
        for ch, ch_params in self.params.items():
            ch_params[ 'current_range' ] = self._get_current_range( 
                ch_params[ 'currents' ]
            )
        
        self._techniques = [ 'cp' ]
        self._fields = namedtuple( 'CP_Datum', [
            'time', 'voltage', 'current', 'power', 'cycle'
        ] )
        
        self.field_titles = [ 
            'Time [s]', 
            'Voltage [V]', 
            'Current [A]', 
            'Power [W]', 
            'Cycle' 
        ]
        
        self._data_fields = (
            dp.SP300_Fields.CP
            if self.device.kind is ecl.DeviceCodes.KBIO_DEV_SP300
            else dp.VMP3_Fields.CP
        )
        self._parameter_types = tfs.CP
        
        
    def run( self, retrieve_data = True ):
        """
        :param retrieve_data: Automatically retrieve and disconenct form device.
            [Default: True]
        """
        params = {}
        for ch, ch_params in self.params.items():
            steps = len( ch_params[ 'currents' ] )
            
            params[ ch ] = {
                'Current_step':      ch_params[ 'currents' ],
                'vs_inital':         [ ch_params[ 'vs_initial' ] ]* steps,
                'Duration_step':     ch_params[ 'durations' ],
                'Step_number':       steps - 1,
                'Record_every_dT':   ch_params[ 'time_interval' ],
                'Record_every_dE':   ch_params[ 'voltage_interval' ],
                'N_Cycles':          0,
                'I_Range':           ch_params[ 'current_range' ].value
            }

        fields = None
        if retrieve_data:
            fields = lambda datum, segment: (
                dp.calculate_time( 
                    datum.t_high, 
                    datum.t_low, 
                    segment.info, 
                    segment.values 
                ),

                datum.voltage,
                datum.current,
                datum.voltage* datum.current, # power
                datum.cycle
            )
        
        # run technique
        data = self._run( 'cp', params, fields )
    
    
    def update_currents( 
        self, 
        currents, 
        durations = None, 
        vs_initial = None 
    ):
        """
        Update current and duration parameters
        """
        steps = len( currents )
        
        params = {
            'Current_step': currents,
            'Step_number':  steps - 1
        }
        
        if durations is not None:
            params[ 'Duration_step' ] = durations
            
        if vs_initial is not None:
            params[ 'vs_initial' ] = vs_initial
         
        # set current ranges
        if isinstance( params, dict ):
            for ch, ch_params in params.items():
                ch_params[ 'current_range' ] = self._get_current_range( 
                    ch_params[ 'currents' ]
                )
                
        else:
            params[ 'current_range' ] = self._get_current_range(
                params[ 'currents' ]
            )
        
        self.device.update_parameters(
            self.channel, 
            'cp', 
            params,
            types = self._parameter_types
        )
        
    
    def _get_current_range( self, currents ):
        """
        Get current range based on maximum current.
        
        :param currents: List of currents.
        :returns: ec_lib.IRange corresponding to largest current.
        """
        i_max = max( currents )
        
        if i_max < 100e-12:
            i_range = ecl.IRange.p100
                
        elif max_i < 1e-9:
            i_range = ecl.IRange.n1
                
        elif max_i < 10e-9:
            i_range = ecl.IRange.n10
            
        elif max_i < 100e-9:
            i_range = ecl.IRange.n100
            
        elif max_i < 1e-6:
            i_range = ecl.IRange.u1
                
        elif max_i < 10e-6:
            i_range = ecl.IRange.u10
            
        elif max_i < 100e-6:
            i_range = ecl.IRange.u100
            
        elif max_i < 1e-3:
            i_range = ecl.IRange.m1
                
        elif max_i < 10e-3:
            i_range = ecl.IRange.m10
            
        elif max_i < 100e-3:
            i_range = ecl.IRange.m100
            
        elif max_i <= 1:
            i_range = ecl.IRange.a1
            
        else:
            raise ValueError( 'Current too large.' )
            
        return i_range


# In[ ]:


class CALimit( BiologicProgram ):
    """
    Runs a cyclic amperometry technqiue.
    """
    # TODO: Add limit conditions as parameters, not hard coded
    def __init__( 
        self, 
        device, 
        params, 
        channels    = None, 
        autoconnect = True,
        barrier     = None,
        threaded    = False
    ):
        """
        Params are
        voltages: List of voltages.
        durations: List of times in seconds.
        vs_initial: If step is vs. initial or previous. 
            [Default: False]
        time_interval: Maximum time interval between points. 
            [Default: 1]
        current_interval: Maximum current change between points. 
            [Default: 0.001]
        current_range: Current range. Use ec_lib.IRange. 
            [Default: IRange.m10 ]
        """
        defaults = {
            'vs_initial':       False,
            'time_interval':    1.0,
            'current_interval': 1e-3,
            'current_range':    ecl.IRange.m10
        }
        
        params = set_defaults( params, defaults, channels )
        super().__init__( 
            device, 
            params, 
            channels    = channels,
            autoconnect = autoconnect, 
            barrier     = barrier,
            threaded    = threaded
        )
        
        self._techniques = [ 'calimit' ]
        self._fields = namedtuple( 'CALimit_Datum', [
            'time', 'voltage', 'current', 'power', 'cycle'
        ] )
        
        self.field_titles = [ 
            'Time [s]', 
            'Voltage [V]', 
            'Current [A]', 
            'Power [W]', 
            'Cycle' 
        ]
        
        self._data_fields = (
            dp.SP300_Fields.CALIMIT
            if self.device.kind is ecl.DeviceCodes.KBIO_DEV_SP300
            else dp.VMP3_Fields.CALIMIT
        )
        self._parameter_types = tfs.CALIMIT
        
        
    def run( self, retrieve_data = True ):
        """
        :param retrieve_data: Automatically retrieve and disconenct form device.
            [Default: True]
        """   
        params = {}
        for ch, ch_params in self.params.items():
            steps = len( ch_params[ 'voltages' ] )
            
            params[ ch ] = {
                'Voltage_step':      ch_params[ 'voltages' ],
                'vs_inital':         [ ch_params[ 'vs_initial' ] ]* steps,
                'Duration_step':     ch_params[ 'durations' ],
                'Step_number':       steps - 1,
                'Record_every_dT':   ch_params[ 'time_interval' ],
                'Record_every_dI':   ch_params[ 'current_interval' ],
                'Test1_Config':      0, # TODO
                'Test1_Value':       0,
                'Test2_Config':      0,
                'Test2_Value':       0,
                'Test3_Config':      0,
                'Test3_Value':       0,
                'Exit_Cond':         0,
                'N_Cycles':          0,
                'I_Range':           ch_params[ 'current_range' ].value
            }

        fields = None
        if retrieve_data:
            fields = lambda datum, segment: (
                dp.calculate_time( 
                    datum.t_high, 
                    datum.t_low, 
                    segment.info, 
                    segment.values 
                ),

                datum.voltage,
                datum.current,
                datum.voltage* datum.current, # power
                datum.cycle
            )
        
        # run technique
        data = self._run( 'calimit', params, fields )
    
    
    def update_voltages( 
        self, 
        voltages, 
        durations  = None, 
        vs_initial = None 
    ):
        """
        Update voltage and duration parameters.
        
        :param voltages: Dictionary of voltages keyed by channel, 
            or single voltage to apply to all channels.
        :param durations: Dictionary of durations keyed by channel,
            or single duration to apply to all channels.
        :param vs_initial: Dictionary of vs. initials keyed by channel,
            or single vs. initial boolean to apply to all channels.
        """
        # format params
        if not isinstance( voltages, dict ):
            # transform to dictionary if needed
            voltages = { ch: voltages for ch in self.channels }
            
        if ( durations is not None ) and ( not isinstance( voltages, dict ) ):
            # transform to dictionary if needed
            durations = { ch: durations for ch in self.channels }
           
        if ( vs_initial is not None ) and ( not isinstance( vs_initial, dict ) ):
            # transform to dictionary if needed
            vs_initial = { ch: vs_initial for ch in self.channels }
         
        # update voltages
        for ch, ch_voltages in voltages.items():
            if not isinstance( ch_voltages, list ):
                # single voltage given, add to list
                ch_voltages = [ ch_voltages ]
            
            steps = len( ch_voltages )

            params = {
                'Voltage_step': ch_voltages,
                'Step_number':  steps - 1
            }

            if ( durations is not None ) and ( durations[ ch ] ):
                params[ 'Duration_step' ] = durations[ ch ]

            if ( vs_initial is not None ) and ( vs_initial[ ch ] ):
                params[ 'vs_initial' ] = vs_initial[ ch ]

            self.device.update_parameters(
                ch, 
                'calimit', 
                params, 
                types = self._parameter_types
            )


# In[ ]:


class PEIS( BiologicProgram ):
    '''
    Runs Potentio Electrochemical Impedance Spectroscopy technique.
    '''
    
    def __init__(
        self,
        device,
        params,
        channels    = None,
        autoconnect = True,
        barrier     = None,
        threaded    = False
    ):
        """
        Params are
        voltage: Initial potential in Volts.
        amplitude_voltage: Sinus amplitude in Volts.
        initial_frequency: Initial frequency in Hertz.
        final_frequency: Final frequency in Hertz.
        frequency_number: Number of frequencies.
        duration: Overall duration in seconds.
        vs_initial: If step is vs. initial or previous. 
            [Default: False]
        time_interval: Maximum time interval between points in seconds.
            [Default: 1]
        current_interval: Maximum time interval between points in Amps.
            [Default: 0.001]
        sweep: Defines whether the spacing between frequencies is logarithmic 
            ('log') or linear ('lin'). [Default: 'log'] 
        repeat: Number of times to repeat the measurement and average the values
            for each frequency. [Default: 1]
        correction: Drift correction. [Default: False]
        wait: Adds a delay before the measurement at each frequency. The delay
            is expressed as a fraction of the period. [Default: 0]
        """
        # set sweep to false if spacing is logarithmic
        if 'sweep' in params:
            if params.sweep is 'log':
                params.sweep = False 

            elif params.sweep is 'lin':
                params.sweep = True

            else: 
                raise ValueError( 'Invalid sweep parameter' )
        
        defaults = {
            'vs_initial':       False,
            'time_interval':    1,
            'current_interval': 0.001,
            'sweep':            False,
            'repeat':           1,
            'correction':       False,
            'wait':             0            
        }
        
        params = set_defaults( params, defaults, channels )
        super().__init__(
            device,
            params,
            channels    = channels,
            autoconnect = autoconnect,
            barrier     = barrier,
            threaded    = threaded
        )
        
        self._fields = namedtuple( 'PEIS_datum', [
            'process',
            'time', 
            'voltage', 
            'current', 
            'abs_voltage',
            'abs_current',
            'impendance_phase',
            'voltage_ce',
            'abs_voltage_ce',
            'abs_current_ce',
            'impendance_ce_phase',
            'frequency'
        ] )
        self.field_titles = [
            'Process',
            'Time [s]',
            'Voltage [V]',
            'Current [A]',
            'abs( Voltage ) [V]',
            'abs( Current ) [A]',
            'Impendance phase',
            'Voltage_ce [V]',
            'abs( Voltage_ce ) [V]',
            'abs( Current_ce ) [A]',
            'Impendance_ce phase',
            'Frequency [Hz]'
            ]
    
        self._techniques = [ 'peis' ]
    
        self._parameter_types = tfs.PEIS   
    
    
    def run( self, retrieve_data = True ):
        """
        :param retrieve_data: Automatically retrieve and disconenct from device.
            [Default: True]
        """
        params = {}
        for ch, ch_params in self.params.items():
            params[ ch ] = {
                'vs_initial':           ch_params[ 'vs_initial' ],
                'vs_final':             ch_params[ 'vs_initial' ],
                'Initial_Voltage_step': ch_params[ 'voltage' ],
                'Final_Voltage_step':   ch_params[ 'voltage' ],
                'Duration_step':        ch_params[ 'duration' ],
                'Step_number':          0,
                'Record_every_dT':      ch_params[ 'time_interval' ],
                'Record_every_dI':      ch_params[ 'current_interval' ],
                'Final_frequency':      ch_params[ 'final_frequency' ],
                'Initial_frequency':    ch_params[ 'initial_frequency' ],
                'sweep':                ch_params[ 'sweep' ], 
                'Amplitude_Voltage':    ch_params[ 'amplitude_voltage' ],
                'Frequency_number':     ch_params[ 'frequency_number' ],
                'Average_N_times':      ch_params[ 'repeat' ],
                'Correction':           ch_params[ 'correction' ],
                'Wait_for_steady':      ch_params[ 'wait' ]
            }

        if retrieve_data:
            def fields( datum, segment ): 
                """
                Define fields for _run function.
                """
                if segment.info.ProcessIndex is 0:
                    f = (
                        segment.info.ProcessIndex,
                        dp.calculate_time(
                            datum.t_high,
                            datum.t_low,
                            segment.info,
                            segment.values
                        ),
                        datum.voltage,
                        datum.current,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None
                    )  
                elif segment.info.ProcessIndex is 1:
                    f = (
                        segment.info.ProcessIndex,
                        datum.time,
                        datum.voltage,
                        datum.current,
                        datum.abs_voltage,
                        datum.abs_current,
                        datum.impendance_phase,
                        datum.voltage_ce,
                        datum.abs_voltage_ce,
                        datum.abs_current_ce,
                        datum.impendance_ce_phase,
                        datum.frequency
                    )
                else:
                    raise valueError( 'Invalid ProcessIndex ({})'.format( segment.info.ProcessIndex ) )
                
                return f

            
        self._data_fields = (
            dp.SP300_Fields.PEIS
            if self.device.kind is ecl.DeviceCodes.KBIO_DEV_SP300
            else dp.VMP3_Fields.PEIS
        )
        
        # run technique
        data = self._run( 'peis', params, fields )


# In[ ]:


class JV_Scan( BiologicProgram ):
    """
    Runs a JV scan.
    """
    def __init__( 
        self, 
        device, 
        params, 
        channels    = None, 
        autoconnect = True,
        barrier     = None,
        threaded    = False
    ):
        """
        Params are
        start: Dictionary of start voltages keyed by channels. [Defualt: 0]
        end: Dictionary of end voltages keyed by channels.
        step: Voltage step. [Default: 0.01]
        rate: Scan rate in mV/s. [Default: 10]
        average: Average over points. [Default: False]
        """
        # defaults
        defaults = {
            'start': 0,
            'step':  0.01,
            'rate':  10,
            'average': False
        }
        params = set_defaults( params, defaults, channels )
        
        super().__init__( 
            device, 
            params, 
            channels    = channels, 
            autoconnect = autoconnect, 
            barrier     = barrier,
            threaded    = threaded
        )
        
        self._techniques = [ 'cv' ]
        
        self._fields = namedtuple( 'CV_Datum', [
           'voltage', 'current', 'power' 
        ] )
        
        self.field_titles = [ 'Voltage [V]', 'Current [A]', 'Power [W]' ]
        
        self._data_fields = (
            dp.SP300_Fields.CV
            if self.device.kind is ecl.DeviceCodes.KBIO_DEV_SP300
            else dp.VMP3_Fields.CV
        )
        
        self._parameter_types = tfs.CV
    
    
    def run( self, retrieve_data = True ):
        """
        :param retrieve_data: Automatically retrieve and disconenct form device.
            [Default: True]
        """
        # setup scan profile ( start -> end -> start )
        params = {}
        for ch, ch_params in self.params.items():
            voltage_profile = [ ch_params[ 'start' ] ]* 5
            voltage_profile[ 1 ] = ch_params[ 'end' ]

            params[ ch ] = {
                'vs_initial':   [ False ]* 5,
                'Voltage_step': voltage_profile,
                'Scan_Rate':    [ ch_params[ 'rate' ]* 10e-3 ]* 5,
                'Scan_number':  2,
                'Record_every_dE':   ch_params[ 'step' ],
                'Average_over_dE':   ch_params[ 'average' ],
                'N_Cycles':          0,
                'Begin_measuring_I': 0, # start measurement at beginning of interval
                'End_measuring_I':   1  # finish measurement at end of interval
            }
        
        fields = None
        if retrieve_data:
            fields = lambda datum, segment: ( 
                datum.voltage, 
                datum.current, 
                datum.voltage* datum.current # power
            ) 
         
        # run technique
        data = self._run( 'cv', params, fields )


# In[ ]:


MPP_Powers = namedtuple( 'MPP_Powers', [ 'hold', 'probe' ] )

class MPP_Tracking( CALimit ):
    """
    Run MPP tracking.
    """
    def __init__( 
        self, 
        device, 
        params, 
        channels    = None, 
        autoconnect = True,
        barrier     = None,
        threaded    = False
    ):
        """
        Params are
        run_time: Run time in seconds.
        init_vmpp: Dictionary of initial v_mpp keyed by channel.
        probe_step: Voltage step for probe. [Default: 0.005 V]
        probe_points: Number of data points to collect for probe. 
            [Default: 5]
        probe_interval: How often to probe in seconds. [Default: 2]
        record_interval: How often to record a data point in seconds.
            [Default: 1]
        """
        # set up params
        defaults = {
            'probe_step':      5e-3,
            'probe_points':    5,
            'probe_interval':  2,
            'record_interval': 1
        }
        params = set_defaults( params, defaults, channels )
        
        # map to ca parameters
        if channels is None:
            self.v_mpp       = {}
            self.probe_steps = {}
            
            # channel params
            for ch, ch_params in params.items():
                init_vmpp = ch_params[ 'init_vmpp' ]
                self.v_mpp[ ch ]        = init_vmpp
                self.probe_steps[ ch ]  = ch_params[ 'probe_step' ]
                
                ch_params[ 'voltages' ]  = [ init_vmpp ]
                ch_params[ 'durations' ] = ch_params[ 'run_time' ]
                ch_params[ 'time_interval' ] = ch_params[ 'record_interval' ]
                
        else:
            init_vmpp  = params[ 'init_vmpp' ]
            self.v_mpp = { ch: init_vmpp for ch in channels }
            self.probe_steps = { ch: params[ 'probe_step' ] for ch in channels }
            
            params[ 'durations' ] = params[ 'run_time' ]
            params[ 'voltages' ]  = [ init_vmpp ]
            
        
        super().__init__( 
            device, 
            params, 
            channels    = channels,
            autoconnect = autoconnect, 
            barrier     = barrier,
            threaded    = threaded
        )
        
        self.active_channels = self.channels
        
        # timers
        self.last_probe = time.time()
        
        # timeout callbacks
        self._cb_timeout = []
    
    
    def on_timeout( 
        self, 
        cb, 
        timeout,
        repeat = True, 
        args   = [], 
        kwargs = {},
        timeout_type = 'interval'
    ):
        """
        Register a timeout callback to run during MPP tracking.
        Callbacks are run after every hold and probe sequence.
        
        :param cb: Callback function to run.
        :param timeout: Timeout is seconds.
        :param repeat: Repeat the callback every timeout.
            [Default: True]
        :param args: List of arguments to pass to the callback function.
            [Default: []]
        :param kwargs: Dictionary of keywrod arguments to pass to the callback function.
            [Default: {}]
        :param timeout_type: Type of timeout.
            Values are [ 'interval', 'between' ]
            interval: Time between callback starts
            between: Time between last finish and next start
            [Default: 'interval']
        """
        callback = CallBack_Timeout( 
            self,
            cb, 
            timeout, 
            repeat = repeat, 
            args   = args, 
            kwargs = kwargs,
            timeout_type = timeout_type
        )
        
        self._cb_timeout.append( callback )
    
        
    def run( self, folder = None, by_channel = False ):
        """
        :param folder: Folder or file for saving data or 
            None if automatic saving is not desired.
            Should be folder if by_channel is False, and file if True.
            [Default: None]
        :param by_channel: Save data by channel. [Default: False]
        """
        # start callbacks
        for cb in self._cb_timeout:
            cb.start()
        
        super().run( retrieve_data = False )
        self.__hold_and_probe( folder, by_channel = by_channel )  # hold and probe
        
        # program end
        if self.autoconnect is True:
            self._disconnect()
        
        self.save_data( folder, by_channel = by_channel )
        
    #--- helper functions ---           
            
    def __hold_and_probe( self, folder = None, by_channel = False ):
        """
        :param folder: Folder or file for saving data or 
            None if automatic saving is not desired.
            Should be folder if by_channel is False, and file if True.
            [Default: None]
        :param by_channel: Save data by channel. [Default: False]
        """        
        # calculate hold and probe times
        # actual hold and probe times are taken as the minimum of sum across the channels.
        probe_times = {
            ch: ch_params[ 'probe_points' ]* ch_params[ 'record_interval' ]
            for ch, ch_params in self.params.items()
        }
        
        hold_times = {
            ch: max( 
                ch_params[ 'probe_interval' ] - probe_times[ ch ],
                probe_times[ ch ]
            )
            
            for ch, ch_params in self.params.items()
        }
        
        cycle_times = { 
            ch: probe_times[ ch ] + hold_times[ ch ]
            for ch in self.params
        }
        
        key_channel = min( cycle_times, key = cycle_times.get ) # get key of shortest cycle time
        hold_time   = hold_times[  key_channel ]
        probe_time  = probe_times[ key_channel ]
        
        while True:
            # loop until measurement ends 
            
            if ( # stop signal received
                self._stop_event is not None
                and self._stop_event.is_set()
            ):
                logging.warning( 
                    'Halting program on channels {}.'.format( ', '.join( self.channels ) ) 
                )
                
                break
            
            # callbacks
            for cb in self._cb_timeout:
                cb.call()  
                      
            # hold
            ( self.active_channels, hold_segments ) = asyncio.run(
                self.__hold_and_retrieve( hold_time ) 
            )
            
            self.__append_data( hold_segments ) # add data
            
            if len( self.active_channels ) is 0:
                # program end
                break
                
            # probe
            probe_voltages = {
                ch: self.v_mpp[ ch ] + self.probe_steps[ ch ]
                for ch in self.active_channels
            }
            
            self.update_voltages( probe_voltages  )
            ( self.active_channels, probe_segments ) = asyncio.run( 
                self.__hold_and_retrieve( probe_time ) 
            )
            
            self.__append_data( probe_segments ) # add data
            
            if len( self.active_channels ) is 0:
                # program end
                break
    
            # compare powers
            powers = self.__calculate_powers( 
                hold_segments,
                probe_segments
            )
               
            # set new v_mpp
            self.__new_v_mpp( powers )
            self.update_voltages( self.v_mpp )

            # save intermediate data
            if folder is not None:
                self.save_data( folder, by_channel = by_channel )
                
    
    async def __hold_and_retrieve( self, duration ):
        """
        @async
        Wait for a given time, then retrieve data
        
        :param duration: Time since last probe in seconds.
        """
        # wait, if needed
        if duration > 0:
            # duration not yet reached
            await asyncio.sleep( duration )
            
        self.last_probe = time.time() # reset last probe time
        
        segments = await self._retrieve_data_segments()
        active = [ 
            ch 
            for ch, segment in segments.items() 
            if ( ecl.ChannelState( segment.values.State  ) is ecl.ChannelState.RUN )
        ]
        
        return ( active, segments )
    
    
    def __append_data( self, segments ):
        fields = lambda datum, segment: (
            dp.calculate_time( 
                datum.t_high, 
                datum.t_low, 
                segment.info, 
                segment.values 
            ),

            datum.voltage,
            datum.current,
            datum.voltage* datum.current, # power
            datum.cycle
        )
        
        for ch, segment in segments.items():
            self._data[ ch ] += [
                self._fields( *fields( datum, segment ) )
                for datum in segment.data
            ]
        
    
    def __calculate_powers( self, hold_segments, probe_segments ):
        powers = {
            ch: self.__calculate_power( 
                hold_segments[ ch ].data, 
                probe_segments[ ch ].data 
            )
            
            for ch in self.active_channels
        }   
            
        return powers
        
    
    def __calculate_power( self, hold_data, probe_data ):
        # normalize compare times
        cmp_len = min( len( hold_data ), len( probe_data ) ) 
        hold_data  = hold_data[  -cmp_len: ]
        probe_data = probe_data[ -cmp_len: ]

        # get power
        hold  = [ datum.voltage* datum.current for datum in hold_data ]
        probe = [ datum.voltage* datum.current for datum in probe_data ]

        # take mean
        hold  = sum( hold )  / len( hold )
        probe = sum( probe ) / len( probe )
           
        return MPP_Powers( hold, probe )
    
    
    def __new_v_mpp( self, powers ):
        for ch, ch_power in powers.items():
            # update probe directions
            probe_better = ( ch_power.probe < ch_power.hold ) # powers are negative

            if not probe_better:
                # probe was worse, move in opposite direction
                self.probe_steps[ ch ] *= -1

        # update v_mpp
        self.v_mpp = { 
            ch: v_mpp + self.probe_steps[ ch ]
            for ch, v_mpp in self.v_mpp.items()
        }


# In[ ]:


class MPP( MPP_Tracking ):
    """
    Makes a JV scan and Voc scan and runs MPP tracking.
    """
    def __init__( 
        self, 
        device, 
        params, 
        channels    = None, 
        autoconnect = True,
        barrier     = None,
        threaded    = False
    ):
        """
        Params are
        run_time: Run time in seconds.
        probe_step: Voltage step for probe. [Default: 0.005 V]
        probe_points: Number of data points to collect for probe. 
            [Default: 5]
        probe_interval: How often to probe in seconds. [Default: 2]
        record_interval: How often to record a data point in seconds.
            [Default: 1]
    
        """
        
        defaults = {
            'init_vmpp': 0 # initial set of vmpp
        }
        params = set_defaults( params, defaults, channels )
        
        super().__init__( 
            device, 
            params, 
            channels    = channels, 
            autoconnect = autoconnect, 
            barrier     = barrier,
            threaded    = threaded
        )
        
        self.voc = None
        self._techniques = [ 'ocv', 'cv', 'ca' ]
    
    
    def run( self, data = 'data', by_channel = False, jv_params = {} ):
        """
        :param data: Data folder path. [Default: 'data']
        :param by_channel: Save data by channel. [Defualt: False]
        :param jv_params: Parameters passed to JV_Scan to find intial MPP,
            or {} for default. [Default: {}]
            
        """
        # create folder path if needed
        if not os.path.exists( data ):
            os.makedirs( data )
            
        ocv_loc = 'voc' if by_channel else 'voc.csv'
        jv_loc  = 'jv'  if by_channel else 'jv.csv'
        mpp_loc = 'mpp' if by_channel else 'mpp.csv'
        
        mpp_loc = os.path.join( data, mpp_loc )
        ocv_loc = os.path.join( data, ocv_loc )
        jv_loc  = os.path.join( data, jv_loc )
        
        if self.autoconnect is True:
            self._connect()
        
        #--- init ---        
        self.voc = self.__run_ocv( ocv_loc, by_channel = by_channel ) # voc
        self.v_mpp = self.__run_jv( self.voc, jv_loc, by_channel = by_channel, jv_params = jv_params ) # jv 
        
        for ch, ch_params in self.params.items():
            ch_params[ 'init_vmpp' ] = self.v_mpp[ ch ]
        
        self.sync()
        
        time_stamp = str( dt.now() )
        time_stamp = time_stamp.split( '.' )[ 0 ]
        print( '[{}] Beginning MPP tracking on channels {}...'.format( 
            time_stamp, self.channels 
        ), flush = True )
            
        super().run( mpp_loc ) # mpp tracking
        
    #--- helper functions ---
    
    def __init_mpp_file( self, file ):
        ca_titles = [ 
            'Time [s]', 
            'Voltage [V]', 
            'Current [A]', 
            'Power [W]', 
            'Cycle' 
        ]
        
        try:
            with open( file, 'w' ) as f:
                # write header only if not appending
                f.write( ', '.join( ca_titles ) )
                f.write( '\n' )
                
        except Exception as err:
            if self._threaded:
                logging.warning( '[#save_data] CH{}: {}'.format( self.channel, err ) )
                
            else:
                raise err
            
            
    def __run_ocv( self, file, by_channel = False ):
        """
        Runs an OCV program to find the voc for each channel.
        
        :param file: File to save data.
        :param by_channel: Save data by channel. [Defualt: False]
        :returns: Averaged open circuit votlages.
        """
        ocv_params = {
            'time': 1,
            'time_interval': 0.1,
            'voltage_interval': 0.001
        }
        
        ocv_pg = OCV( 
            self.device, 
            ocv_params, 
            channels    = self.channels, 
            autoconnect = False,
            barrier  = self.barrier,
            threaded = self._threaded
        )
        
        ocv_pg.run()
        ocv_pg.save_data( file, by_channel = by_channel )
        
        voc = { 
            ch: [ datum.voltage for datum in data ]
            for ch, data in ocv_pg.data.items()
        }
        
        voc = { 
            ch: sum( ch_voc )/ len( ch_voc ) 
            for ch, ch_voc in voc.items()  
        }
        
        return voc
        
        
    def __run_jv( self, voc, file, by_channel = False, jv_params = {} ):
        """
        Runs JV_Scan program to obtain initial v_mpp.
        
        :param file: File for saving data.
        :param voc: Dictionary of open circuit voltages keyed by channel.
            Scan runs from Voc to 0 V.
        :param by_channel: Save data by channel. [Defualt: False]
        :param jv_params: Parameters to use for JV_Scan, or {} for defaults.
            [Default: {}]
        :returns: MPP voltage calculated from the JV scan results.
        """
        defaults = {
            'end':   0,
            'step':  5e-3, # 5 mV
            'rate':  100, # 100 mV/s
            'average': False
        }
        
        jv_params = set_defaults( jv_params, defaults, self.channels )   
        jv_params = {
            ch: {
                'start': ch_voc, 
                **jv_params
            }
            for ch, ch_voc in voc.items()
        }

        prg = JV_Scan( 
            self.device, 
            jv_params,
            channels    = None, # channels implies in params
            autoconnect = False,
            barrier  = self.barrier,
            threaded = self._threaded
        )
        
        prg.run()
        prg.save_data( file, by_channel = by_channel )
        
        mpp = {
            ch: min( data, key = lambda d: d.power ) # power of interest is negative
            for ch, data in prg.data.items()
        }
        
        v_mpp = { 
            ch: ch_mpp.voltage 
            for ch, ch_mpp in mpp.items() 
        }
        
        return v_mpp


# In[ ]:


class MPP_Cycles( MPP ):
    """
    MPP tracking with periodic JV scans.
    """
    
    def __init__( 
        self, 
        device, 
        params, 
        channels    = None, 
        autoconnect = True,
        barrier     = None,
        threaded    = False
    ):
        """
        Params are
        run_time: Cycle run time in seconds.
        cycles: Number of cycles to perform.
        probe_step: Voltage step for probe. [Default: 0.01 V]
        probe_points: Number of data points to collect for probe. 
            [Default: 5]
        probe_interval: How often to probe in seconds. [Default: 2]
        record_interval: How often to record a data point in seconds.
            [Default: 1]
        """       
        super().__init__( 
            device, 
            params, 
            channels    = channels, 
            autoconnect = autoconnect, 
            barrier     = barrier,
            threaded    = threaded
        )
        
        self.cycle = None
       
    
    def run( self, data = 'data', by_channel = False, jv_params = {} ):
        """
        :param data: Data folder path. [Default: 'data']
        :param by_channel: Save data by channel. [Default: False]
        :param jv_params: Parameters for the JV_Scan. [ Default: {} ]
        """
        self.cycle = 0
        cycles = { ch: ch_params[ 'cycles' ] for ch, ch_params in self.params.items() }
        cycles_max = max( cycles.values() )
        
        while self.cycle < cycles_max:
            self._run_mpp_cycle( self.cycle, data, by_channel = by_channel )
            self.cycle += 1
    
    def _run_mpp_cycle( self, cycle, folder, by_channel = False ):
        cycle_path = 'cycle-{:02.0f}'.format( cycle )
        folder = os.path.join( folder, cycle_path )
        
        # reset data
        for ch in self.channels:
            self._data[ ch ] = []

        if self.barrier is not None:
            self.barrier.wait()

        time_stamp = str( dt.now() )
        time_stamp = time_stamp.split( '.' )[ 0 ]
        print( '[{}] Starting cycle {} on channels {}.'.format( 
            time_stamp, cycle, self.channels
        ), flush = True )
        
        super().run( folder, by_channel = by_channel )
        

