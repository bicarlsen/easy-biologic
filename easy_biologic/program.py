
# coding: utf-8

# # Biologic Programs

# ## Biologic Program 
# `Abstract Class`
# Represents a program to be run on a device channel.
# 
# ### Methods
# **BiologicProgram( device, channel, params, autoconnect = True, barrier = None ):** Creates a new program.
# 
# **channel_state( channels = None):** Returns the state of channels. 
# 
# **on_data( callback, index = None ):** Registers a callback function to run when data is collected.
# 
# **run():** Runs the program.
# 
# **stop():** Sets the stop event flag.
# 
# **save_data( file, append = False ):** Saves data to the given file.
# 
# **sync():** Waits for barrier, if set.
# 
# **_connect():** Connects to the device.
# 
# ### Properties
# **device:** BiologicDevice. <br>
# **channel:** Device channel. <br>
# **params:** Passed in parameters. <br>
# **autoconnect:** Whether connection to the device should be automatic or not. <br>
# **barrier:** A threading.Barrier to use for channel syncronization. [See ProgramRummer] <br>
# **field_titles:** Column names for saving data. <br>
# **data:** Data collected during the program. <br>
# **status:** Status of the program. <br>
# **fields:** Data fields teh program returns. <br>
# **technqiues:** List of techniques the program uses. <br>
# 
# ## Program Runner
# Represents a program to be run on a device channel.
# 
# ### Methods
# **ProgramRunner( programs, sync = False ):** Creates a new program runner.
# 
# **start():** Runs the programs.
# 
# **wait():** Wait for all threads to finish.
# 
# **stop():** Sets the stop event.
# 
# ### Properties
# **threads:** List of threads for each program. <br>
# **sync:** Whether to sync the threads or not.
# 

# In[ ]:


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


# In[4]:


class BiologicProgram( ABC ): 
    """
    Abstract Class
    Represents a Biologic Program
    
    Stores data.
    """
    
    def __init__( 
        self, 
        device,  
        params, 
        channels    = None,
        autoconnect = True,
        barrier     = None,
        stop_event  = None,
        threaded    = False
    ):
        """
        Initialize instance parameters.
        
        :param device: A BiologicDevice to run the program on.
        :param params: Dictionary of parameters to be passed to the program as values,
            or Dictionary of params keyed by channel.
            If dictionary of parameters, channels param must also be passed,
            same parameters used for all channels.
            If keyed by channels, channels are assumed.
        :param channels: List of channels to run the program on, or
             None to interpret channels from params.
             [Default: None]
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
        self.autoconnect  = autoconnect
        self.barrier      = barrier
        self.field_titles = [] # column names for saving data
        
        if channels is None:
            # assume channels from params
            self._channels = list( params.keys() )
            self.params = params
        
        else:
            # use same params for all channels
            self.params = { ch: params.copy() for ch in channels }
            self._channels = channels
            
        self._techniques  = [] # program techniques
        self._data        = { ch: [] for ch in self.channels } # data store
        self._fields      = None # program fields
        self._data_fields = None # technique fields
        self._parameter_types = None # parameter types for the technqiue
        
        self._threaded = threaded
        self._stop_event = stop_event
        self._cb_data = [] 

        # TODO: signal handling
        # register interupt signal
        if self._threaded:
            signal.signal(
                signal.SIGINT,
                self.stop
            )
    
    #--- properties ---
    
    @property
    def channels( self ):
        """
        :returns: List of channels.
        """
        return self._channels
    
        
    @property
    def data( self ):
        """
        :returns: Data collected from program.
        """
        return self._data
    
    
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
    
    def channel_state( self, channels = None ):
        """
        Returns the state of the channels.
        
        :param channels: Channel or list of channels, 
            or None to retrieve all statuses.
            [Default: None]
        :returns: ChannelState, or dictionary of ChannelStates keyed by channel.
        """
        single_ch = False
        
        if channels is None:
            channels = self.channels
            
        elif not isinstance( channels, list ):
            # single channel provided, put in list
            single_ch = True
            channels = [ channels ] 
        
        states = {}
        for ch in channels:
            info = self.device.channel_info( channel )
            states[ ch ] = ecl.ChannelState( info.State )
        
        if single_ch:
            # single channel provided
            return states[ channel ]
        
        return states
        
    
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
        append = False,
        by_channel = False
    ):
        """
        Saves data to a CSV file.
        
        :param file: File or folder path.  
        :param append: True to append to file, false to overwrite.
            [Default: False]
        :param by_channel: Save each channel to own file (True)
            or in same file (False).
            If True, file should be a folder path.
            If False, file should be a file path.
            [Default: False]
        """
        if by_channel:
            self._save_data_individual( file, append )
            
        else:
            self._save_data_together( file, append )

                
    def sync( self ):
        """
        Waits for barrier, if set.
        """
        if self.barrier is not None:
            self.barrier.wait()
            
            
    def stop( self, signal, frame ):
        """
        Sets stop event.
        """
        if self._stop_event is None:
            logging.warning( 'No stop event is present on channels {}.'.format( self.channels ) )
            return
                
        self._stop_event.set()
    
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
        
        for ch, ch_params in params.items():
            self.device.load_technique( 
                ch, 
                technique, 
                ch_params, 
                types = self._parameter_types
            )

        self.device.start_channels( self.channels )
        
        if fields is not None:
            data = asyncio.run( self._retrieve_data( interval ) )
            
            if self.autoconnect is True:
                self._disconnect()

            for ch, ch_data in data.items():
                self._data[ ch ] = [
                    self._fields( *fields( datum, segment ) )
                    for segment in ch_data
                    for datum in segment.data
                ]
    
        
        
    async def _retrieve_data_segment( self, channel ):
        """
        @async
        Gets the current data segment, and parses the data.
        
        :param channel: Channel to retrieve data from.
        :returns: DataSegment.
        """
        raw = await self.device.get_data( channel )
        
        try:
            parsed = dp.parse( 
                raw.data, 
                raw.info, 
                self._data_fields 
            )
            
        except RuntimeError as err:
            msg = 'ch {}: {}'.format( channel, err )
            logging.debug( msg )
            
            return DataSegment( [], raw.info, raw.values )

        segment = DataSegment( parsed, raw.info, raw.values )
        
        # run callbacks
        for cb in self._cb_data:
            cb( segment )
        
        return segment
    
    
    async def _retrieve_data_segments( self, channels = None ):
        """
        @async
        Gets the current data segment for active channels, and parses the data.
        
        :param channels: List of channels ro get data from, or None for all.
            [Default: None]
        :returns: Dictionary of DataSegments keyed by channel.
        """       
        if channels is None:
            channels = self.channels
        
        segments = {}
        for ch in channels:
            segments[ ch ] = await self._retrieve_data_segment( ch )
        
        return segments
        
        
    
    async def _retrieve_data( self, interval = 1 ):
        """
        @async
        Retrieves data from the device until it is stopped.
        Data is parsed.
        
        :param interval: How often to collect data in seconds.
            [Default: 1]      
        :returns: Dictionary of lists of DataSegments with properties 
            [ data, info, values ], keyed by channel.
        """
        data = { ch: []  for ch in self.channels }
        complete = { ch: False for ch in self.channels }
        
        while not all( complete.values() ):
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
            active_channels = [ ch for ch, done in complete.items() if ( not done ) ]
            segments = await self._retrieve_data_segments( active_channels )
            
            for ch, ch_segment in segments.items():
                done = ( ecl.ChannelState( ch_segment.values.State  ) is ecl.ChannelState.STOP )
                data[ ch ].append( ch_segment )   
            
                complete[ ch ] = done
                if done:
                    logging.debug( 'Channel {} complete.'.format( ch ) )

        return data
    
    
    
    def _save_data_together( 
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
                    # write channel header if multichanneled
                    num_titles = len( self.field_titles )
                    ch_header = ''
                    for ch in self.channels:
                        ch_header += ( '{},'.format( ch ) )* num_titles

                    # replace last comma with line end
                    ch_header = ch_header[ :-1 ] + '\n'

                    f.write( ch_header )
                    
                    # field titles
                    title_header = ''
                    for _ in self.channels:
                        # create titles for each channnel
                        title_header += ','.join( self.field_titles ) + ','
                        
                    # replace last comma with new line
                    title_header = title_header[ :-1 ] + '\n'
                        
                    f.write( title_header )

                # write data
                # get maximum rows
                num_ch_cols = len( self.field_titles )
                num_rows = { ch: len( data ) for ch, data in self.data.items() }              
                for index in range( max( num_rows.values() ) ):
                    row_data = ''
                    for ch, ch_data in self.data.items():
                        if index < num_rows[ ch ]:
                            # valid row for channel
                            row_data += ','.join( map( self._datum_to_str, ch_data[ index ] ) ) + ','
                        
                        else:
                            # channel data exhausted, write placeholders
                            row_data += ','* num_ch_cols
                        
                    # new row
                    row_data = row_data[ :-1 ] + '\n'
                    f.write( row_data )
                    
        except Exception as err:
            if self._threaded:
                logging.warning( '[#save_data] CH{}: {}'.format( ch, err ) )
                
            else:
                raise err
                

    def _save_data_individual( 
        self, 
        folder, 
        append = False
    ):
        """
        Saves data to a CSV file.
        
        :param folder: Folder path.  
        :param append: True to append to file, false to overwrite.
            [Default: False]
        """
        mode = 'a' if append else 'w'
        
        if not os.path.exists( folder ):
            os.makedirs( folder )
        
        for ch, ch_data in self.data.items():
            file = os.path.join( folder, 'ch-{}.csv'.format( ch ) )
            
            csv_data = ''
            for datum in ch_data:
                csv_data += ','.join( map( self._datum_to_str, datum ) )
                csv_data += '\n'
                                      
            try:
                with open( file, mode ) as f:
                    if not append:
                        # write header only if not appending
                        f.write( ','.join( self.field_titles ) + '\n' )

                    # write data
                    f.write( csv_data )             

            except Exception as err:
                logging.warning( '[#_save_data_individual] CH{}: {}'.format( ch, err ) )
                
    
    def _datum_to_str( self, datum ):
        """
        Casts data to string.
        If datum is None, casts to empty string intead of 'None'.
        
        :param datum: Datum to cast.
        :returns: Datum as a string.
        """
        if datum is None:
            return ''
        
        # datum is not None
        return str( datum )
        


# In[5]:


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

