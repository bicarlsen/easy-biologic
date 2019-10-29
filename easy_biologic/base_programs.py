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
# ## JV_Scan
# Performs a JV scan.
# 
# ### Params
# **start:** Start voltage. 
# [ Defualt: 0 ]
# 
# **end:** End voltage.
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
# ### Params
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
# **run_time:** Run time in seconds.
# 
# **record_interval:** How often to record a data point in seconds. 
# [Default: 1]
# 
# ## MPP_Tracking_Intermittent
# Performs MPP tracking with perdiodic voltage holds.
# 
# ### Params
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
# **run_time:** Run time in seconds.
# 
# **hold_interval:** How often to hold the voltage.
# 
# **hold_time:** How long to hold the voltage.
# 
# **record_interval:** How often to record a data point in seconds. 
# [Default: 1]
# 
# 
# ## MPP
# Runs MPP tracking and finds the initial Vmpp by finding the Voc, then performing a JV scan.
# 
# ### Params
# **probe_step:** Voltage step for probe. 
# [Default: 0.01 V]
# 
# **probe_points:** Number of data points to collect for probe. 
# [Default: 5]
# 
# **probe_interval:** How often to probe in seconds. 
# [Default: 2]
# 
# **run_time:** Run time in seconds.
# 
# **record_interval:** How often to record a data point in seconds. 
# [Default: 1]
# 
# ## MPP_Intermittent
# Runs MPP tracking with voltage holds and finds the initial Vmpp by finding the Voc, then performing a JV scan.
# 
# ### Params
# **probe_step:** Voltage step for probe. 
# [Default: 0.01 V]
# 
# **probe_points:** Number of data points to collect for probe. 
# [Default: 5]
# 
# **probe_interval:** How often to probe in seconds. 
# [Default: 2]
# 
# **run_time:** Run time in seconds.
# 
# **hold_interval:** How often to hold the voltage.
# 
# **hold_time:** How long to hold the voltage.
# 
# **record_interval:** How often to record a data point in seconds. 
# [Default: 1]

# In[3]:


import os
import time
import asyncio
from collections import namedtuple

from . import BiologicProgram
from .program import CallBack
from .lib import ec_lib as ecl
from .lib import data_parser as dp
from .lib import technique_fields as tfs


# In[1]:


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
        kwargs = {} 
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
        """
        self.__program = program
        self.__cb = CallBack( cb, args, kwargs )
        self.timeout  = timeout
        self.is_alive = False
        
        self.repeat = 1 if ( repeat is False ) else repeat
        
        self.__calls   = 0
        self.__elapsed = 0
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
        self.__last_call = time.time()
        self.__calls += 1
        
        # callback
        cb( self.__program, *args, **kwargs )
        
        
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
def set_defaults( params, defaults ):
    """
    Combines parameter and default dictionaries.
    
    :param params: Parameter dictionary.
    :param defaults: Default dictionary. 
        Values used if key is not present in parameter dictionary.
    :returns: Dictionary with defualt values set, if not set in parameters dictionary.
    """
    return { **defaults, **params }


# In[ ]:


class OCV( BiologicProgram ):
    """
    Runs an open circuit voltage scan.
    """
    
    def __init__( 
        self, 
        device, 
        channel,
        params, 
        autoconnect = True,
        barrier = None,
        threaded = False
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
        params = set_defaults( params, defaults )
        
        super().__init__( 
            device, 
            channel, 
            params, 
            autoconnect = autoconnect, 
            barrier = barrier,
            threaded = threaded
        )
        
        self._techniques = [ 'ocv' ]
        self._fields = namedtuple( 'OCV_Datum', [ 'time', 'voltage' ] )
        self.field_titles = [ 'Time [s]', 'Voltage [V]' ]
        self._data_fields = (
            dp.SP300_Fields.OCV
            if self.device.kind is 'SP-300'
            else dp.VMP3_Fields.OCV
        )
        self._parameter_types = tfs.OCV
        
        
    def run( self, retrieve_data = True ):
        """
        :param retrieve_data: Automatically retrieve and disconenct form device.
            [Default: True]
        """
        params = {
            'Rest_time_T':     self.params[ 'time' ],
            'Record_every_dE': self.params[ 'voltage_interval' ],
            'Record_every_dT': self.params[ 'time_interval' ]
        }
            
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
    Runs a cyclic amperometry technqiue.
    """
    
    def __init__( 
        self, 
        device, 
        channel, 
        params, 
        autoconnect = True,
        barrier = None,
        threaded = False
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
        
        params = set_defaults( params, defaults )
        super().__init__( 
            device, 
            channel, 
            params, 
            autoconnect = autoconnect, 
            barrier = barrier,
            threaded = threaded
        )
        
        self.params[ 'voltages' ] = [ 
            float( v ) for v in self.params[ 'voltages' ]
        ]
        
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
            if self.device.kind is 'SP-300'
            else dp.VMP3_Fields.CA
        )
        self._parameter_types = tfs.CA
        
        
    def run( self, retrieve_data = True ):
        """
        :param retrieve_data: Automatically retrieve and disconenct form device.
            [Default: True]
        """
        steps = len( self.params[ 'voltages' ] )
        
        params = {
            'Voltage_step':      self.params[ 'voltages' ],
            'vs_inital':         [ self.params[ 'vs_initial' ] ]* steps,
            'Duration_step':     self.params[ 'durations' ],
            'Step_number':       steps - 1,
            'Record_every_dT':   self.params[ 'time_interval' ],
            'Record_every_dI':   self.params[ 'current_interval' ],
            'N_Cycles':          0,
            'I_Range':           self.params[ 'current_range' ].value
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


class CALimit( BiologicProgram ):
    """
    Runs a cyclic amperometry technqiue.
    """
    # TODO: Add limit conditions as parameters, not hard coded
    def __init__( 
        self, 
        device, 
        channel, 
        params, 
        autoconnect = True,
        barrier = None,
        threaded = False
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
        
        params = set_defaults( params, defaults )
        super().__init__( 
            device, 
            channel, 
            params, 
            autoconnect = autoconnect, 
            barrier = barrier,
            threaded = threaded
        )
        
        self._technqiues = [ 'calimit' ]
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
            if self.device.kind is 'SP-300'
            else dp.VMP3_Fields.CALIMIT
        )
        self._parameter_types = tfs.CALIMIT
        
        
    def run( self, retrieve_data = True ):
        """
        :param retrieve_data: Automatically retrieve and disconenct form device.
            [Default: True]
        """
        steps = len( self.params[ 'voltages' ] )
        
        params = {
            'Voltage_step':      self.params[ 'voltages' ],
            'vs_inital':         [ self.params[ 'vs_initial' ] ]* steps,
            'Duration_step':     self.params[ 'durations' ],
            'Step_number':       steps - 1,
            'Record_every_dT':   self.params[ 'time_interval' ],
            'Record_every_dI':   self.params[ 'current_interval' ],
            'Test1_Config':      0, # TODO
            'Test1_Value':       0,
            'Test2_Config':      0,
            'Test2_Value':       0,
            'Test3_Config':      0,
            'Test3_Value':       0,
            'Exit_Cond':         0,
            'N_Cycles':          0,
            'I_Range':           self.params[ 'current_range' ].value
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
            self.channel, 'calimit', params
        )


# In[ ]:


class JV_Scan( BiologicProgram ):
    """
    Runs a JV scan.
    """
    def __init__( 
        self, 
        device, 
        channel, 
        params, 
        autoconnect = True,
        barrier = None,
        threaded = False
    ):
        """
        Params are
        start: Start voltage. [Defualt: 0]
        end: End voltage.
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
        params = set_defaults( params, defaults )
        
        super().__init__( 
            device, 
            channel, 
            params, 
            autoconnect = autoconnect, 
            barrier = barrier,
            threaded = threaded
        )
        
        self._techniques = [ 'cv' ]
        self._fields = namedtuple( 'CV_Datum', [
           'voltage', 'current', 'power' 
        ] )
        self.field_titles = [ 'Voltage [V]', 'Current [A]', 'Power [W]' ]
        self._data_fields = (
            dp.SP300_Fields.CV
            if self.device.kind is 'SP-300'
            else dp.VMP3_Fields.CV
        )
        self._parameter_types = tfs.CV
    
    
    def run( self, retrieve_data = True ):
        """
        :param retrieve_data: Automatically retrieve and disconenct form device.
            [Default: True]
        """
        # setup scan profile ( start -> end -> start )
        voltage_profile = [ self.params[ 'start' ] ]* 5
        voltage_profile[ 1 ] = self.params[ 'end' ]
        
        params = {
            'vs_initial':   [ False ]* 5,
            'Voltage_step': voltage_profile,
            'Scan_Rate':    [ self.params[ 'rate' ]* 10e-3 ]* 5,
            'Scan_number':  2,
            'Record_every_dE':   self.params[ 'step' ],
            'Average_over_dE':   self.params[ 'average' ],
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


class MPP_Tracking( BiologicProgram ):
    """
    Run MPP tracking.
    """
    def __init__( 
        self, 
        device, 
        channel, 
        params, 
        autoconnect = True,
        barrier = None,
        threaded = False
    ):
        """
        Params are
        init_vmpp: Initial v_mpp.
        probe_step: Voltage step for probe. [Default: 0.01 V]
        probe_points: Number of data points to collect for probe. 
            [Default: 5]
        probe_interval: How often to probe in seconds. [Default: 2]
        run_time: Run time in seconds.
        record_interval: How often to record a data point in seconds.
            [Default: 1]
        """
        defaults = {
            'probe_step':      0.01,
            'probe_points':    5,
            'probe_interval':  2,
            'record_interval': 1
        }
        params = set_defaults( params, defaults )
        
        super().__init__( 
            device, 
            channel, 
            params, 
            autoconnect = autoconnect, 
            barrier = barrier,
            threaded = threaded
        )
        
        self.v_mpp = params[ 'init_vmpp' ]
        self.probe_step = params[ 'probe_step' ]
        self.autoconnect = autoconnect
        
        self._techniques = [ 'ca' ]
        self.field_titles = []
        
        # timers
        self.last_probe = time.time()
        
        # timeout callbacks
        self._cb_timeout = []
    
    
    def on_timeout( self, cb, timeout, repeat = True, args = [], kwargs = {} ):
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
        """
        callback = CallBack_Timeout( 
            self,
            cb, 
            timeout, 
            repeat, 
            args, 
            kwargs 
        )
        
        self._cb_timeout.append( callback )
    
        
    def run( self, file = None ):
        """
        :param file: File for saving data or 
            None if automatic saving is not desired.
            [Default: None]
        """
        run_time = self.params[ 'run_time' ]
        ca_params = {
            'voltages':  [ self.v_mpp ],
            'durations': [ run_time ],
            'time_interval': self.params[ 'record_interval' ],
        }
        
        self.ca_pg = CALimit(
            self.device,
            self.channel,
            ca_params,
            autoconnect = self.autoconnect,
            barrier  = self.barrier,
            threaded = self._threaded
        )

        # start callbacks
        for cb in self._cb_timeout:
            cb.start()
        
        self.ca_pg.run( retrieve_data = False )
        self.__hold_and_probe( file )  # hold and probe
        
        # program end
        if self.autoconnect is True:
            self._disconnect()
        
        self.ca_pg.save_data( file )
        
    #--- helper functions ---           
            
    def __hold_and_probe( self, file = None ):
        """
        :param file: File for saving data or 
            None if automatic saving is not desired.
            [Default: None]
        """
        probe_time = self.params[ 'probe_points' ]* self.params[ 'record_interval' ] # 5 measurements
        hold_time  = max( 
            self.params[ 'probe_interval' ] - probe_time,
            probe_time
        )
        
        while True:
            # loop until measurement ends 
            
            if ( # stop signal received
                self._stop_event is not None
                and self._stop_event.is_set()
            ):
                logging.warning( 
                    'Halting program on channel {}.'.format( self.channel ) 
                )
                
                break
            
            # callbacks
            for cb in self._cb_timeout:
                cb.call()
                
                      
            # hold
            ( hold_state, hold_segment ) = asyncio.run(
                self.__hold_and_retrieve( hold_time ) 
            )
            
            self.__append_data( hold_segment ) # add data
            
            if hold_state is ecl.ChannelState.STOP:
                # program end
                break
                
            # probe
            self.ca_pg.update_voltages( [ self.v_mpp + self.probe_step ] )
            ( probe_state, probe_segment ) = asyncio.run( 
                self.__hold_and_retrieve( probe_time ) 
            )
            
            self.__append_data( probe_segment ) # add data
            
            if probe_state is ecl.ChannelState.STOP:
                # program end
                break
    
            # compare powers
            ( hold_pwr, probe_pwr ) = self.__calculate_powers( 
                hold_segment.data,
                probe_segment.data
            )
            
            # set new v_mpp
            self.__new_v_mpp( hold_pwr, probe_pwr )
            self.ca_pg.update_voltages( [ self.v_mpp ] )

            # save intermediate data
            if file is not None:
                self.ca_pg.save_data( file )
                
    
    async def __hold_and_retrieve( self, duration ):
        """
        Wait for a given time, then retrieve data
        
        :param duration: Time since last probe in seconds.
        """
        # wait, if needed
        if duration > 0:
            # duration not yet reached
            await asyncio.sleep( duration )
            
        self.last_probe = time.time() # reset last probe time
        
        segment = self.ca_pg._retrieve_data_segment()
        state = ecl.ChannelState( segment.values.State  )
        
        return ( state, segment )
    
    
    def __append_data( self, segment ):
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
        
        self.ca_pg._data += [
            self.ca_pg._fields( *fields( datum, segment ) )
            for datum in segment.data
        ]
        
    
    def __calculate_powers( self, hold_data, probe_data ):
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
           
        return ( hold, probe )
    
    
    def __new_v_mpp( self, hold, probe ):
        probe_better = ( probe < hold ) # powers are negative
        
        if not probe_better:
            # probe was worse, move in opposite direction
            self.probe_step *= -1
            
        self.v_mpp += self.probe_step


# In[2]:


class MPP( MPP_Tracking ):
    """
    Makes a JV scan and Voc scan and runs MPP tracking.
    """
    def __init__( 
        self, 
        device, 
        channel, 
        params, 
        autoconnect = True,
        barrier = None,
        threaded = False
    ):
        """
        Params are
        probe_step: Voltage step for probe. [Default: 0.01 V]
        probe_points: Number of data points to collect for probe. 
            [Default: 5]
        probe_interval: How often to probe in seconds. [Default: 2]
        run_time: Run time in seconds.
        record_interval: How often to record a data point in seconds.
            [Default: 1]
        """
        params[ 'init_vmpp' ] = 0 # initial set of vmpp
        super().__init__( 
            device, 
            channel, 
            params, 
            autoconnect = autoconnect, 
            barrier = barrier,
            threaded = threaded
        )
        
        self.voc = None
        self._techniques = [ 'ocv', 'cv', 'ca' ]
        self.field_titles = []
    
    
    def run( self, data = 'data' ):
        """
        :param data: Data folder path. [Default: 'data']
        """
        # create folder path if needed
        if not os.path.exists( data ):
            os.makedirs( data )
            
        ocv_file = 'voc.csv'
        jv_file  = 'jv.csv'
        mpp_file = 'mpp.csv'
        
        mpp_file = os.path.join( data, mpp_file )
        ocv_file = os.path.join( data, ocv_file )
        jv_file  = os.path.join( data, jv_file )
        
        if self.autoconnect is True:
            self._connect()
        
        #--- init ---
        self.__init_mpp_file( mpp_file ) # init file
        
        self.voc = self.__run_ocv( ocv_file ) # voc
        self.v_mpp = self.__run_jv( self.voc, jv_file ) # jv 
        self.params[ 'init_vmpp' ] = self.v_mpp
        
        if self.barrier is not None:
            self.barrier.wait()
            print( 'Beginning MPP tracking on channel {}...'.format( self.channel ) )
            
        super().run( mpp_file ) # mpp tracking
        
    #--- helper functions ---
    
    def __init_mpp_file( self, file ):
        ca_titles = [ 
            'Time [s]', 
            'Voltage [V]', 
            'Current [A]', 
            'Power [W]', 
            'Cycle' 
        ]
        
        with open( file, 'w' ) as f:
            # write header only if not appending
            f.write( ', '.join( ca_titles ) )
            f.write( '\n' )
            
            
    def __run_ocv( self, file ):
        """
        Runs an OCV program to find the voc for each channel.
        
        :param file: File to save data.
        :returns: Averaged open circuit votlages.
        """
        ocv_params = {
            'time': 1,
            'time_interval': 0.1,
            'voltage_interval': 0.001
        }
        
        ocv_pg = OCV( 
            self.device, 
            self.channel, 
            ocv_params, 
            autoconnect = False,
            barrier  = self.barrier,
            threaded = self._threaded
        )
        
        ocv_pg.run()
        ocv_pg.save_data( file )
        
        voc = [ datum.voltage for datum in ocv_pg.data ]
        voc = sum( voc )/ len( voc )
        
        return voc
        
        
    def __run_jv( self, voc, file ):
        """
        Runs JV_Scan program to obtain initial v_mpp.
        
        :param file: File for saving data.
        :param voc: Dictionary of open circuit voltages keyed by channel.
            Scan runs from Voc to 0 V.
        :returns: MPP voltage calculated from teh JV scan results.
        """
        jv_params = {
            'start': voc, 
            'end':   0,
            'step':  5e-3, # 5 mV
            'rate':  100, # 100 mV/s
            'average': False
        }

        prg = JV_Scan( 
            self.device, 
            self.channel, 
            jv_params,
            autoconnect = False,
            barrier  = self.barrier,
            threaded = self._threaded
        )
        
        prg.run()
        prg.save_data( file )
        
        mpp = min( prg.data, key = lambda d: d.power ) # power of interest is negative
        v_mpp = mpp.voltage
        return v_mpp

