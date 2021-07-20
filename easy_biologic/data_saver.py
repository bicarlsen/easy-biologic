class DataSaver():

	def __init__():
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
