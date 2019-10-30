#!/usr/bin/env python
# coding: utf-8

# # Biologic Programs

# ## Biologic Program 
# `Abstract Class`
# Represents a program to be run on a device channel.
# 
# ### Methods
# **BiologicProgram( device, channel, params, autoconnect = True, barrier = None ):** Creates a new program.
# 
# **on_data( callback, index = None ):** Retgisters a callback function to run when data is collected.
# 
# **run():** Runs the program.
# 
# **save_data( file, append = False ):** Saves data to the given file.
# 
# **_connect():** Connects to the device
# 
# ### Properties
# **device:** BiologicDevice.
# **channel:** Device channel.
# **params:** Passed in parameters.
# **autoconnect:** Whether connection to the device should be automatic or not.
# **barrier:** A threading.Barrier to use for channel syncronization. [See ProgramRummer]
# **field_titles:** Column names for saving data.
# **data:** Data collected during the program.
# **status:** Status of the program.
# **fields:** Data fields teh program returns.
# **technqiues:** List of techniques the program uses.
# 
# ## Program Runner
# Represents a program to be run on a device channel.
# 
# ### Methods
# **ProgramRunner( programs, sync = False ):** Creates a new program runner.
# 
# **start():** Runs the programs.
# 
# ### Properties
# **sync:** Whether to sync the threads or not. If True a threading.sync is 
# 

# In[1]:


import os
import logging
import signal
import asyncio
import threading
from abc import ABC
from collections import namedtuple

from .lib import ec_lib as ecl
from .lib import data_parser as dp


# In[ ]:


DataSegment = namedtuple( 'DataSegment', [
    'data', 'info', 'values'
] )

CallBack = namedtuple( 'CallBack', [ 'function', 'args', 'kwargs' ] )


# In[1]:


class ProgramRunner():
    """
    Runs programs on multiple channels simultaneously, 
    each in its own thread.
    """
    
    def __init__( self, programs, sync = False, timeout = 5 ):
        """
        Create a Program Runner.
        
        :param programs: A list BiologicPrograms to run.
            If run parameters are required use a dictionary
            with keys [program, params] where the program value
            is the program instance to run, and params is a dictionary
            of parameters to pass to #run of the program.
        :param sync: Whether threads should be synced or not.
            Relies on programs using threading.Barrier.
            [Default: False]
        :param timeout: Threading timeout in seconds. Used for signal interuptions.
            [Default: 5]
        """
        self.programs = programs
        self.sync = sync
        self.timeout = timeout
        
        self.__threads = []
        self._stop_event = threading.Event()
        
        if self.sync:
            self.barrier = threading.Barrier( len( programs ) )
            for program in programs:
                prg = ( 
                    program[ 'program' ] 
                    if isinstance( program, dict )
                    else program
                )
                
                prg.barrier = self.barrier
                
        # register interupt signal
        signal.signal(
            signal.SIGINT,
            self.stop
        )
        
    
    @property
    def threads( self ):
        """
        :returns: Current threads.
        """
        return self.__threads
    
        
    def start( self ):
        """
        Start the programs
        """
        self.__threads = []
        for prg in self.programs:
            if isinstance( prg, dict ):
                # run params passed in
                program = prg[ 'program' ]
                params  = prg[ 'params' ]
                
            else:
                # only program passed, no run params
                program = prg
                params = {}
            
            program._stop_event = self._stop_event
            
            t = threading.Thread(
                target = program.run,
                kwargs = params
            )
            
            self.__threads.append( t )
            t.start()
            
    
    def wait( self ):
        """
        Wait for all threads to finish.
        """
        for thread in self.threads:
            thread.join()

        # TODO: Poll is alive with join timeout to allow signals
#         is_alive = [ False ]* len( self.threads )
#         while not all( is_alive ):
#             for index, thread in enumerate( self.threads ):
#                 is_alive[ index ] = thread.is_alive()
#                 thread.join( self.timeout )
            
            
    def stop( self, signal, frame ):
        """
        Sets stop event.
        """
        logging.warning( "Halting programs..." )
        self._stop_event.set()


# In[1]:


class BiologicProgram( ABC ): 
    """
    Abstract Class
    Represents a Biologic Program
    
    Stores data.
    """
    
    def __init__( 
        self, 
        device, 
        channel, 
        params, 
        autoconnect = True,
        barrier = None,
        stop_event = None,
        threaded = False
    ):
        """
        Initialize instance parameters.
        
        :param device: A BiologicDevice to run the program on.
        :param channel: Channel to run the program on.
        :param params: Dictionary of parameters to be passed to the program.
        :param autoconnect: Automatically connect and disconnect to device during run.
            [Default: True]
        :param barrier: threading.Barrier used for synchronization across channels.
            [Default: None]
        :param stop_event: threading.Event indicating to stop the program.
            [Default: None]
        :param threaded: Indicated if the program is running as a thread.
            [Default: False]
        """
        self.device   = device
        self.channel  = channel
        self.params   = params
        self.autoconnect  = autoconnect
        self.barrier      = barrier
        self.field_titles = [] # column names for saving data
        
        self._techniques  = [] # program techniques
        self._data        = [] # data store
        self._fields      = None # program fields
        self._data_fields = None # technique fields
        self._parameter_types = None # parameter types for the technqiue
        
        self._threaded = threaded
        self._stop_event = stop_event
        self._cb_data = [] 

        # register interupt signal
        if not self._threaded:
            signal.signal(
                signal.SIGINT,
                self.stop
            )
    
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
    
    def on_data( self, cb, index = None ):
        """
        Register a callback when data is collected.
        
        :param cb: A callback function to be called.
            The function should accept one parameter of type
            DataSegment, a namedtuple with properties
            [ data, info, values ], as returned by BiologicDevice.get_data().
        :param index: Index at which to run the callback or None to append. 
            If index exceeds current length of callback list, then function is appended.
            [Default: None]
        """
        if index is None:
            index = len( self._cb_data )
            
        self._cb_data.insert( index, cb )
        
    
    def run( self, auto_retrieve = True  ):
        """
        Runs the program.
        
        :param auto_retrieve: Automatically retrieve data. [Default: True]
        """
        pass
    
    
    def save_data( 
        self, 
        file, 
        append = False 
    ):
        """
        Saves data to a CSV file.
        
        :param file: File path.  
        :param append: True to append to file, false to overwrite.
            [Default: False]
        """
        mode = 'a' if append else 'w'
        
        try:
            with open( file, mode ) as f:
                if not append:
                    # write header only if not appending
                    f.write( ', '.join( self.field_titles ) )
                    f.write( '\n' )

                for datum in self.data:
                    f.write( ', '.join( map( str, datum ) ) )
                    f.write( '\n' )
                    
        except Exception as err:
            if self._threaded:
                logging.warning( '[#save_data] CH{}: {}'.format( self.channel, err ) )
                
            else:
                raise err

    
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
            
            
    def stop( self, signal, frame ):
        """
        Sets stop event.
        """
        if self._stop_event is None:
            logging.warning( 'No stop event is present on channel {}.'.format( self.channel ) )
            return
                
        self._stop_event.set()
         
    
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
        if self.autoconnect:
            self._connect()
        
        
        self.device.load_technique( 
            self.channel, 
            technique, 
            params, 
            types = self._parameter_types
        )

        self.device.start_channel( self.channel )
        
        if fields is not None:
            data = asyncio.run( self._retrieve_data( interval ) )
            
            if self.autoconnect is True:
                self._disconnect()

            self._data = [
                    self._fields( *fields( datum, segment ) )
                    for segment in data
                    for datum in segment.data
                ]
        
    
    def _retrieve_data_segment( self ):
        """
        Gets the current data segment, and parses the data.
        
        :returns: DataSegment.
        """
        raw = self.device.get_data( self.channel )
        
        try:
            parsed = dp.parse( 
                raw.data, 
                raw.info, 
                self._data_fields 
            )
            
        except RuntimeError as err:
            msg = 'ch {}: {}'.format( self.channel, err )
            logging.debug( msg )
            
            return DataSegment( [], raw.info, raw.values )

        segment = DataSegment( parsed, raw.info, raw.values )
        
        # run callbacks
        for cb in self._cb_data:
            cb( segment )
        
        return segment
        
    
    async def _retrieve_data( self, interval = 1 ):
        """
        @async
        Retrieves data from the device until it is stopped.
        Data is parsed.
        
        :param interval: How often to collect data in seconds.
            [Default: 1]      
        :returns: List of DataSegments with properties 
            [ data, info, values ].
        """
        data = []
        state = True
        while ( state is not ecl.ChannelState.STOP ):
            if ( # stop signal received
                self._stop_event is not None
                and self._stop_event.is_set()
            ):
                logging.warning( 
                    'Halting program on channel {}.'.format( self.channel ) 
                )
                
                break
                
            await asyncio.sleep( interval ) # wait
            
            # retrieve data
            segment = self._retrieve_data_segment()
            state = ecl.ChannelState( segment.values.State  )
            data.append( segment )   

        return data

