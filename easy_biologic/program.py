#!/usr/bin/env python
# coding: utf-8

# # Biologic Programs

# In[1]:


import os
import logging
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


# In[1]:


class ProgramRunner():
    """
    Runs programs on multiple channels simultaneously, 
    each in its own thread.
    """
    
    def __init__( self, programs, sync = False ):
        """
        Create a Program Runner.
        
        :param programs: A list BiologicPrograms to run.
            If run parameters are required use a dictionary
            with keys [program, params] where the program value
            is the program instance to run, and params is a dictionary
            of parameters to pass to #run of the program.
        :params sync: Whether threads should be synced or not.
            Relies on programs using threading.Barrier.
            [Default: False]
        """
        self.programs = programs
        self.sync = sync
        self.__threads = []
        
        if self.sync:
            self.barrier = threading.Barrier( len( programs ) )
            for program in programs:
                prg = ( 
                    program[ 'program' ] 
                    if isinstance( program, dict )
                    else program
                )
                
                prg.barrier = self.barrier
        
    
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
                params = prg[ 'params' ]
                
            else:
                # only program passed, no run params
                program = prg
                params = {}
            
            t = threading.Thread(
                target = program.run,
                kwargs = params
            )
            
            self.__threads.append( t )
            t.start()


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
        barrier = None
    ):
        """
        Initialize instance parameters.
        
        :param device: A BiologicDevice to run the program on.
        :param channel: Channel to run the program on.
        :param params: Dictionary of parameters to be passed to the program.
        :param autoconnect: Automatically connect and disconnect to device during run.
            [Default: True]
        :param barrier: threading.Barrier used for synchronization across channels.
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
        
        # callbacks
        self._cb_data = [] 
    
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
            biologic_device.TechData, a namedtuple with properties
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
        
        with open( file, mode ) as f:
            if not append:
                # write header only if not appending
                f.write( ', '.join( self.field_titles ) )
                f.write( '\n' )

            for datum in self.data:
                f.write( ', '.join( map( str, datum ) ) )
                f.write( '\n' )

    
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
            await asyncio.sleep( interval ) # wait
            
            # retrieve data
            segment = self._retrieve_data_segment()
            state = ecl.ChannelState( segment.values.State  )
            data.append( segment )   

        return data

