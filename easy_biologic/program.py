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
# **device:** BiologicDevice.

# **channel:** Device channel.

# **params:** Passed in parameters.

# **autoconnect:** Whether connection to the device should be automatic or not.

# **barrier:** A threading.Barrier to use for channel syncronization. [See ProgramRummer]

# **field_titles:** Column names for saving data.

# **data:** Data collected during the program.

# **status:** Status of the program.

# **fields:** Data fields the program returns.

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
# **wait():** Wait for all threads to finish.
#
# **stop():** Sets the stop event.
#
# ### Properties
# **threads:** List of threads for each program.
# **sync:** Whether to sync the threads or not.
#


import os
import logging
import signal
import asyncio
import threading
from abc import ABC
from collections import namedtuple

from .lib import ec_lib as ecl
from .lib import data_parser as dp


DataSegment = namedtuple( 'DataSegment', [
    'data', 'info', 'values'
] )


CallBack = namedtuple( 'CallBack', [ 'function', 'args', 'kwargs' ] )


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
        channels     = None,
        autoconnect  = True,
        field_values = None,
        barrier      = None,
        stop_event   = None,
        threaded     = False
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
        :raises ValueError: If data_window is a dictionary and missing channel keys.

        Properties
        :write_attempts: Number of attempts to try to write data, afterwhich an exception is raised.
            If None, never raise an exception.
            [Default: 0]
        :field_titles: List of names for each field to be used when writing data.
            Should have same length as number of fields.
        :_fields: A named tuple representing the program data.
        :_field_values: Function returning a tuple of fields or None.
            If a function, data is appended to self.data by calling the function
            with input ( datum, segment ). Returned data should be of type self._fields.
            If None, no data retrieval or processing occurs.
            [Default: None]
        :_data_fields: Technique field types.
            [See lib.data_parser.SP300_Fields and lib.data_parser.VMP3_Fields]
        :_parameter_types: Enum of parameter types for each techinuqe field.
            [See lib.technique_fields]
        """
        self.device       = device
        self.autoconnect  = autoconnect
        self.barrier      = barrier
        self.field_titles = []  # column names for saving data
        self.write_attempts = 0
        self._writes_failed = 0

        if channels is None:
            # assume channels from params
            self._channels = list( params.keys() )
            self.params = params

        else:
            # use same params for all channels
            self.params = { ch: params.copy() for ch in channels }
            self._channels = channels

        self._techniques   = []  # program techniques
        self._fields       = None  # program fields object
        self._field_values = None  # fucntion to compute program fields
        self._data_fields  = None  # technique input fields
        self._parameter_types = None  # parameter types for the technique

        self._data = { ch: [] for ch in self.channels }  # data store
        self._unsaved_data = { ch: [] for ch in self.channels }  # data store for unwritten data
        self.data_window = None  # initialize to keep all data

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
    def data_window( self ):
        """
        :returns: Data window used to trim channel data.
        """
        return self._data_window


    @data_window.setter
    def data_window( self, value ):
        """
        Sets the data window.
        :param value: Dictionary of { channel: amount } for amount of data to keep,
            or an amount to apply to all channels, after each save.
            If amount is a non-negative integer, keeps at that many data points,
                clearing data after each write to file.
            If amount is None, keeps all data.
            [Default: 0]
        """
        if isinstance( value, dict ):
            missing = [ ch for ch in self.channels if ch not in value.keys() ]
            if len( missing ):
                # missing channels
                raise ValueError( f'Channel(s) {missing} missing.' )

            self._data_window = value

        else:
            # static value
            self._data_window = { ch: value for ch in self.channels }


    @property
    def fields( self ):
        """
        :returns: Fields object.
        """
        return self._fields


    @property
    def field_values( self ):
        """
        :returns: Field values function.
        """
        return self._field_values


    @property
    def techniques( self ):
        """
        :returns: Technqiue(s) of the program
        """
        return self._techniques


    @property
    def writes_failed(self):
        """
        :returns: Number of failed writes since last success.
        """
        return self._writes_failed


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
            The function should have signature (segment, program ).
            segment is a DataSegment, a namedtuple with properties
            [ data, info, values ], as returned by BiologicDevice.get_data().
            program is the program being run.
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
        if append is False:
            if not hasattr( self, '_write_header' ):
                self._write_header = True

            else:
                # header already written
                # append to file
                append = True

        else:
            # don't write header if appending
            self._write_header = False

        try:
            if by_channel:
                self._save_data_individual(
                    file,
                    append = append,
                    write_header = self._write_header
                )

            else:
                self._save_data_together(
                    file,
                    append = append,
                    write_header = self._write_header
                )


        except Exception as err:
            self._writes_failed += 1

            if (
                ( self.write_attempts is not None ) and
                ( self.writes_failed > self.write_attempts )
            ):
                raise err

        else:
            # only write header at most once
            self._write_header = False

            # successful write
            # reset failed attempts
            self._writes_failed = 0

        # drop data outside data window
        self.trim_data()


    def trim_data( self, window = None ):
        """
        Trims data to a specific length.

        :param window: Dictionary of { channel: amount } for amount of data to save
            of None to use self.data_window.
            If amount is a non-negative integer, saves at most that many data points,
                clearing data after each write to file.
            If amount is None does not trim any data.
            [Default: None]
        :raises ValueError: If an invalid channel is provided as a window key.
        """
        if window is None:
            window = self.data_window

        # validate channels
        invalid_channels = [ ch for ch in window.keys() if ch not in self.channels ]
        if len( invalid_channels ) > 0:
            raise ValueError( f'Invalid channel(s): {invalid_channels}' )

        # trim data
        for ch, ch_window in window.items():
            if ch_window is None:
                # don't trim data
                continue

            elif ch_window == 0:
                # clear data
                self._data[ ch ] = []

            else:
                self._data[ ch ] = self._data[ ch ][ -ch_window: ]


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
            logging.warning( f'No stop event is present on channels {self.channels}.' )
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


    def _run( self, technique, params, interval = 1, retrieve_data = True ):
        """
        Runs the program.

        :param technqiue: Name of technique.
        :param params: Technique parameters.
        :param interval: Time between data fetches. [Default: 1]
        :param retrieve_data: Whether data should be retrieved or not.
            self.field_values must be valid.
            [Default: True]
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

        if retrieve_data:
            asyncio.run( self._retrieve_data( interval ) )

            if self.autoconnect is True:
                self._disconnect()


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
            msg = f'ch {channel}: {err}'
            logging.debug( msg )

            return DataSegment( [], raw.info, raw.values )

        segment = DataSegment( parsed, raw.info, raw.values )

        if self._fields and self._field_values:
            parsed = [
                self._fields( *self._field_values( datum, segment ) )
                for datum in segment.data
            ]
            self._data[ channel ] += parsed
            self._unsaved_data[ channel ] += parsed

        # run callbacks
        for cb in self._cb_data:
            cb( segment, self )

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
        complete = { ch: False for ch in self.channels }
        while not all( complete.values() ):
            if (  # stop signal received
                self._stop_event is not None
                and self._stop_event.is_set()
            ):
                logging.warning(
                    f'Halting program on channel {self.channel}.'
                )

                break

            await asyncio.sleep( interval ) # wait

            # retrieve data
            active_channels = [ ch for ch, done in complete.items() if ( not done ) ]
            segments = await self._retrieve_data_segments( active_channels )

            for ch, ch_segment in segments.items():
                done = ( ecl.ChannelState( ch_segment.values.State  ) is ecl.ChannelState.STOP )
                complete[ ch ] = done
                if done:
                    logging.debug( f'Channel {ch} complete.' )


    def _save_data_together(
        self,
        file,
        append = False,
        write_header = False
    ):
        """
        Saves data to a CSV file.

        :param file: File path.
        :param append: True to append to file, false to overwrite.
            [Default: False]
        :param write_header: Whether to write header or not.
            [Default: False]
        """
        mode = 'a' if append else 'w'
        try:
            with open( file, mode ) as f:
                num_titles = len( self.field_titles )

                if write_header:
                    # write header only if not appending
                    # write channel header if multichanneled
                    ch_header = ''
                    for ch in self.channels:
                        ch_header += f'{ch},'* num_titles

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

                    try:
                        f.write( title_header )

                    except Exception as err:
                        logging.warning( f'Error writing header: {err}' )

                # write data
                # get maximum rows
                num_rows = { ch: len( data ) for ch, data in self._unsaved_data.items() }
                written = { ch: [] for ch in self._unsaved_data.keys() }
                for index in range( max( num_rows.values() ) ):
                    written_row = { ch: None for ch in self._unsaved_data.keys() }
                    row_data = ''
                    for ch, ch_data in self._unsaved_data.items():
                        if index < num_rows[ ch ]:
                            # valid row for channel
                            ch_datum = ch_data[ index ]
                            row_data += ','.join( map( self._datum_to_str, ch_datum ) ) + ','
                            written_row[ ch ] = ch_datum

                        else:
                            # channel data exhausted, write placeholders
                            row_data += ','* num_titles

                    # new row
                    row_data = row_data[ :-1 ] + '\n'

                    try:
                        f.write( row_data )

                    except Exception as err:
                        logging.warning( f'Error writing data: {err}' )

                    else:
                        # successful write
                        for ch, ch_datum in written_row.items():
                            written[ ch ].append( ch_datum )

                # data written, remove data from unsaved
                for ch, ch_data in written.items():
                    self._unsaved_data[ ch ] = [
                        datum for datum in ch_data
                        if datum not in written[ ch ]
                    ]

        except Exception as err:
            if self._threaded:
                logging.warning( f'[#save_data] CH{ch}: {err}' )

            else:
                raise err


    def _save_data_individual(
        self,
        folder,
        append = False,
        write_header = False
    ):
        """
        Saves data to a CSV file.

        :param folder: Folder path.
        :param append: True to append to file, false to overwrite.
            [Default: False]
        :param write_header: Whether to write header or not.
            [Default: False]
        """
        mode = 'a' if append else 'w'

        if not os.path.exists( folder ):
            os.makedirs( folder )

        for ch, ch_data in self._unsaved_data.items():
            file = os.path.join( folder, f'ch-{ch}.csv' )

            csv_data = ''
            for datum in ch_data:
                csv_data += ','.join( map( self._datum_to_str, datum ) )
                csv_data += '\n'

            try:
                with open( file, mode ) as f:
                    if write_header:
                        # write header only if not appending
                        f.write( ','.join( self.field_titles ) + '\n' )

                    # write data
                    f.write( csv_data )

            except Exception as err:
                logging.warning( f'[#_save_data_individual] CH{ch}: {err}' )

            else:
                # data written successfully
                self._unsaved_data[ ch ] = []


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
