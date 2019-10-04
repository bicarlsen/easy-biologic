#!/usr/bin/env python
# coding: utf-8

# # Biologic Programs

# In[1]:


import os
import math
import time
import asyncio

from abc import ABC
from collections import namedtuple

from .lib import ec_lib as ecl
from .lib import data_parser as dp


# In[ ]:


DataSegment = namedtuple( 'DataSegment', [
    'data', 'info', 'values'
] )


# In[ ]:


#--- helper function ---
def cast( lst, kind ):
    """
    Casts esch element of a list into the given type.
    
    :param lst: List of elements.
    :param kind: Cast type.
    :returns: List with casted elements.
    """
    return [ ]


# In[1]:


class BiologicProgram( ABC ): 
    """
    Abstract Class
    Represents a Biologic Program
    
    Stores data.
    """
    
    def __init__( self, device, channel, params, autoconnect = True ):
        """
        Initialize instance parameters.
        
        :param device: A BiologicDevice to run the program on.
        :param channel: The channel to run the program on.
        :param params: Dictionary of parameters to be passed to the program.
        :param autoconnect: Automatically connect and disconnect to device during run.
            [Default: True]
        """
        self.device  = device
        self.channel = channel
        self.params  = params
        self.autoconnect  = autoconnect
        self.field_titles = [] # column names for saving data
        
        self._techniques  = [] # program techniques
        self._data        = [] # data store
        self._fields      = None # program fields
        self._data_fields = None # technique fields
        
    
    
    #--- properties ---
    
    @property
    def data( self ):
        """
        :returns: Data collected from program.
        """
        return self._data
    
    
    @property
    def status( self ):
        """
        :returns: Status of the program.
        """
        pass 
    
    
    @property
    def fields( self ):
        """
        :returns: Fields object.
        """
        return self._fields
    
    
    @property
    def techniques( self ):
        """
        :returns: Technqiue(s) of the program
        """
        return self._techniques
    
    #--- public methods ---
    
    
    def run( self, auto_retrieve = True  ):
        """
        Runs the program.
        
        :param auto_retrieve: Automatically retrieve data. [Default: True]
        """
        pass
    
    
    def save_data( self, file, append = False ):
        """
        Saves data to a CSV file.
        
        :param file: File path.
        :param append: True to append to file, false to overwrite.
            [Default: False]
        """
        mode = 'a' if append else 'w'
        
        with open( file, mode ) as file:
            if not append:
                # write header only if not appending
                file.write( ', '.join( self.field_titles ) )
                file.write( '\n' )

            for datum in self.data:
                file.write( ', '.join( map( str, datum ) ) )
                file.write( '\n' )
    
    
    #--- protected methods ---
    
    
    def _connect( self ):
        """
        Connects device if needed
        """
        if not self.device.is_connected():
            self.device.connect()
            
            
    def _disconnect( self ):
        """
        Disconnects device
        """
        if self.device.is_connected():
            self.device.disconnect()
         
    
    def _run( self, technique, params, fields = None, interval = 1 ):
        """
        Runs the program.
        
        :param technqiue: Name of technique.
        :param params: Technique parameters.
        :params fields: Function returning a tuple of fields or None.
            If function, self._data is automatically set.
            Function input is ( datum, segment ).
            If None no data retrieval or processing occurs.
            [Default: None]
        :param interval: Time between data fetches. [Default: 1]
        """
        # run technique
        self._connect()
        self.device.load_technique( self.channel, technique, params )
        self.device.start_channel( self.channel )
        
        if fields is not None:
            data = asyncio.run( self._retrieve_data( interval ) )
            self._disconnect()
            
            self._data = [
                self._fields( *fields( datum, segment ) )
                for segment in data
                for datum in segment.data
            ]
        
    
    async def _retrieve_data( self, interval = 1 ):
        """
        Retrieves data from the device until it is stopped.
        Data is parsed.
        
        :param interval: How often to collect data in seconds.
            [Default: 1]      
        :returns: A list of DataSegments with properties [ data, info, values ].
        """
        data = []
        state = True
        while ( state is not ecl.ChannelState.STOP ):
            await asyncio.sleep( interval ) # wait
            raw = self.device.get_data( self.channel )
            state = ecl.ChannelState( raw.values.State  )
            
            parsed = dp.parse( 
                raw.data, 
                raw.info, 
                self._data_fields 
            )
        
            data.append( 
                DataSegment( parsed, raw.info, raw.values )
            )   

        return data


# In[ ]:


class OCV( BiologicProgram ):
    """
    Runs an open circuit voltage scan.
    """
    
    def __init__( self, device, channel, params, autoconnect = True ):
        """
        Params are
        time: Run time in seconds.
        time_interval: Maximum time between readings.
        voltage_interval: Maximum interval between voltage readings.
        """
        super().__init__( device, channel, params )
        
        self._techniques = [ 'ocv' ]
        self._fields = namedtuple( 'OCV_Datum', [ 'time', 'voltage' ] )
        self.field_titles = [ 'Time [s]', 'Voltage [V]' ]
        self._data_fields = dp.SP300_Fields.OCV
        
        
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
    
    def __init__( self, device, channel, params, autoconnect = True ):
        """
        Params are
        voltages: List of voltages.
        durations: List of times in seconds.
        vs_initial: If step is vs. initial or previous. [Default: False]
        time_interval: Maximum time interval between points. [Default: 1]
        current_interval: Maximum current change between points. [Default: 0.001]
        """
        defaults = {
            'vs_initial': False,
            'time_interval': 1.0,
            'current_interval': 0.001
        }
        
        params = { **defaults, **params }
        super().__init__( device, channel, params )
        
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
        
        self._data_fields = dp.SP300_Fields.CA
        
        
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
            'I_Range':           ecl.IRange.m10.value
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
            self.channel, 'ca', params
        )


# In[ ]:


class JV_Scan( BiologicProgram ):
    """
    Runs a JV scan.
    """
    def __init__( self, device, channel, params, autoconnect = True ):
        """
        Params are
        start: Start voltage. [ Defualt: 0 ]
        end: End voltage.
        step: Voltage step.
        rate: Scan rate in mV/s.
        average: Average over points. [Default: False]
        """
        # defaults
        if 'start' not in params:
            # start not provided, use default
            params[ 'start' ] = 0.0
            
        if 'average' not in params:
            # average not provided, use default
            params[ 'average' ] = False
        
        super().__init__( device, channel, params )
        
        self._techniques = [ 'cv' ]
        self._fields = namedtuple( 'CV_Datum', [
           'voltage', 'current', 'power' 
        ] )
        self.field_titles = [ 'Voltage [V]', 'Current [A]', 'Power [W]' ]
        self._data_fields = dp.SP300_Fields.CV
    
    
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
            'Scan_Rate':    [ self.params[ 'rate' ] ]* 5,
            'Scan_number':  2,
            'Record_every_dE':   self.params[ 'step' ],
            'Average_over_dE':   self.params[ 'average' ],
            'N_Cycles':          0,
            'Begin_measuring_I': 0.0, # start measurement at beginning of interval
            'End_measuring_I':   1.0 # finish measurement at end of interval
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


class MPP( BiologicProgram ):
    """
    Run MPP tracking.
    """
    def __init__( self, device, channel, params, autoconnect = True ):
        """
        Params are
        probe_step: Voltage step for probe.
        run_time: Run time in minutes.
        """
        super().__init__( device, channel, params )
        
        self.v_mpp = None
        self.voc   = None
        self.probe_step = params[ 'probe_step' ]
        self.record_interval = 1
        
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
        
        self._connect()
        
        #--- init ---
        self.__init_mpp_file( mpp_file ) # init file
        
        self.voc = self.__run_ocv( ocv_file ) # voc
        self.v_mpp = self.__run_jv( jv_file ) # jv 
        
        #--- mpp tracking ---
        run_time = self.params[ 'run_time' ]* 60.0
        ca_params = {
            'voltages':  [ self.v_mpp ],
            'durations': [ run_time ],
            'time_interval': self.record_interval,
        }
        
        self.ca_pg = CA(
            self.device,
            self.channel,
            ca_params,
            autoconnect = False
        )

        self.ca_pg.run( retrieve_data = False )
        self.__hold_and_probe()  # hold and probe
        
        # program end
        self._disconnect()
        self.ca_pg.save_data( mpp_file )
        
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
        ocv_params = {
            'time': 1,
            'time_interval': 0.1,
            'voltage_interval': 0.001
        }
        
        ocv_pg = OCV( 
            self.device, 
            self.channel, 
            ocv_params, 
            autoconnect = False 
        )
        
        ocv_pg.run()
        ocv_pg.save_data( file )
        
        voc = [ datum.voltage for datum in ocv_pg.data ]
        voc = sum( voc )/ len( voc )
        
        return voc
        
        
    def __run_jv( self, file ):
        jv_params = {
            'start': self.voc, 
            'end':   0.0,
            'step':  0.01,
            'rate':  10.0,
            'average': False
        }
        
        jv_pg = JV_Scan( 
            self.device, 
            self.channel, 
            jv_params,
            autoconnect = False
        )
        
        jv_pg.run()
        jv_pg.save_data( file )
        
        mpp = min( jv_pg.data, key = lambda d: d.power ) # power of interest is negative
        return mpp.voltage
            
            
    def __hold_and_probe( self ):
        probe_time = 5.0* self.record_interval # 5 measurements
        hold_time  = self.params[ 'probe_interval' ] - probe_time
        
        while True:
            # loop until measurement ends           
            # hold
            ( hold_state, hold_segment ) = self.__hold_and_retrieve( hold_time ) 
            self.__append_data( hold_segment ) # add data
            
            if hold_state is ecl.ChannelState.STOP:
                # program end
                break
                
            # probe
            self.ca_pg.update_voltages( [ self.v_mpp + self.probe_step ] )
            ( probe_state, probe_segment ) = self.__hold_and_retrieve( probe_time ) 
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

    
    
    def __hold_and_retrieve( self, duration ):
        time.sleep( duration )
        raw = self.device.get_data( self.channel )
        state = ecl.ChannelState( raw.values.State  )
        
        parsed = dp.parse( 
            raw.data, 
            raw.info, 
            self.ca_pg._data_fields 
        )
        
        segment = DataSegment( parsed, raw.info, raw.values )
        
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
        probe_better = probe > hold
        
        if not probe_better:
            # probe was worse, move in opposite direction
            self.probe_step *= -1
            
        self.v_mpp += self.probe_step


# In[ ]:


class MPP_JV():
    
    
    def run():
        jv_padding = 1
        if self.params[ 'jv_interval' ] is not False:
            # calculate number of JV scans to occur
            jv_scan_total = self.params[ 'run_time' ] / self.params[ 'jv_interval' ]
            jv_padding = math.ceil( math.log10( jv_scan_total ) )
         
        jv_scan_num = 0
        jv_base = 'jv-scan-{:0' + str( jv_padding ) + 'd}.csv'    
        
        
        
        if self.params[ 'jv_interval' ]:
            probe_interval = min( 0.1* self.params[ 'jv_interval' ], 1 ) # 1 second or 10% of hold time
            hold_interval = self.params[ 'jv_interval' ] - probe_interval
            
            
            
         # jv scan
        if self.params[ 'jv_interval' ]:
            jv_pg.run()
            jv_scan_num += 1
            jv_pg.save_data( 
                os.path.join( 
                    data, 
                    jv_base.format( jv_scan_num ) 
                )
            )

