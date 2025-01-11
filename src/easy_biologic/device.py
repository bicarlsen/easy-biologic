import asyncio
import ctypes as c
from collections import namedtuple

from .lib.ec_errors import EcError
from .lib import ec_find as ecf
from .lib import ec_lib as ecl

HardwareConfiguration = namedtuple(
    "HardwareConfiguration",
    ["connection", "mode"],  # electrode connection  # channel mode
)


TechParams = namedtuple("TechParams", ["technique", "parameters"])


TechData = namedtuple("TechData", ["data", "info", "values"])


class BiologicDevice:
    """Represents a Biologic Device."""

    def __init__(self, address, timeout=5, populate_info=True):
        """
        :param address: The address of the device to connect to.
        :param timeout: Timeout in seconds. [Defualt: 5]
        :param populate_info: Run an initial #populate_info. [Default: True]
        """
        self.__address = address
        self.timeout = timeout

        self.__init_variables()

        self.__info = None
        if populate_info:
            self.populate_info()

    def __del__(self):
        if self.is_connected():
            self.disconnect()

    # --- properties ---

    @property
    def address(self):
        """
        :returns: Connection string of device.
        """
        return self.__address

    @property
    def idn(self):
        """
        :returns: Device identifier.
        """
        return self.__idn

    @property
    def kind(self):
        """
        :returns: Device model.
        :raises: RuntimeError if the device has not been connected.
        """
        if self.info is None:
            # Device has not yet been connected
            raise RuntimeError(
                "Device must have been connected before retrieving info."
            )

        return ecl.DeviceCodes(self.info.DeviceCode)

    @property
    def info(self):
        """
        :returns: DeviceInfo object.
        """
        return self.__info

    @property
    def plugged(self):
        """
        :returns: List of channel availabilities.
        """
        return self.__plugged

    @property
    def channels(self):
        """
        :returns: List of ChannelInfo objects.
        """
        self._validate_connection()

        return [
            ecl.channel_info(self.idn, ch) if available else None
            for ch, available in enumerate(self.plugged)
        ]

    @property
    def hardware_configuration(self):
        """
        :returns: List of HardwareConf objects.
        """
        self._validate_connection()

        if self.kind is not ecl.DeviceCodes.KBIO_DEV_SP300:
            raise RuntimeError(
                "Hardware configuration is only available for SP-300 devices."
            )

        confs = {
            ch: self.channel_configuration(ch) if available else None
            for ch, available in enumerate(self.plugged)
        }

        return confs

    @property
    def techniques(self):
        """
        :returns: List of TechParams loaded on each channel.
        """
        return self.__techniques

    # --- methods ---

    def connect(self, bin_file=None, xlx_file=None):
        """Connects to the device at the address. Checks channel status.

        :param bin_file: Path to the bin file to use. If None, uses default.
            [Default: None]
        :param xlx_file: Path to the xilinx file to use. If None, uses default.
            [Default: None]
        """
        if self.idn is not None:
            raise RuntimeError("Device already connected.")

        (idn, info) = ecl.connect(self.address, self.timeout)

        self.__idn = idn
        self.__info = info

        # initialize only connected channels
        chs = []
        self.__plugged = ecl.get_channels(self.idn)
        for i in range(len(self.plugged)):
            if self.plugged[i]:
                chs.append(i)

        try:
            ecl.init_channels(self.idn, chs, bin_file=bin_file, xlx_file=xlx_file)

        except EcError as err:
            if err.value == -9:
                # ECLab firmware loaded
                pass

        self.__techniques = [list() for ch in self.plugged]

    def disconnect(self):
        """Disconnect from the device."""
        self._validate_connection()
        ecl.disconnect(self.idn)
        self.__init_variables()  # reset vairables

    def populate_info(self):
        """Connects then disconnects from the device in order to populate info."""
        self.connect()
        self.disconnect()

    def is_connected(self):
        """Returns if the device is conencted or not.

        :returns: Boolean descirbing the state of connection.
        """
        if self.idn is None:
            return False

        connected = ecl.is_connected(self.idn)

        # update state
        if not connected:
            self.__init_variables()

        elif self.idn is None:
            # connected but id is None
            raise RuntimeError("Device is connected but does not have an id assigned.")

        return connected

    def channel_configuration(self, ch):
        """
        :param ch: Channel to configure.
        :returns: HardwareConfiguration of the channel, or None if channel is not available.
        """
        self._validate_connection()

        if not self.plugged[ch]:
            return None

        conf = ecl.get_hardware_configuration(self.idn, ch)
        return HardwareConfiguration(
            connection=ecl.ElectrodeConnection(conf.Conn),
            mode=ecl.ChannelMode(conf.Ground),
        )

    def set_channel_configuration(self, ch, mode, connection):
        """Sets the hardware configuration for the given channel.

        :param ch: Channel to set.
        :param mode: ChannelMode.
        :param connection: ElectrodeConnection.
        """
        self._validate_connection()

        if self.kind is not ecl.DeviceCodes.KBIO_DEV_SP300:
            raise RuntimeError(
                "Hardware configuration is only available for SP-300 devices."
            )

        ecl.set_hardware_configuration(self.idn, ch, mode, connection)

    def load_technique(self, ch, technique, params, index=0, last=True, types=None):
        """Loads a single technique on to the given channel.

        :param ch: The channel to load the technique on to.
        :param technique: Name of the technique to load.
        :param params: A dictionary of parameters to use.
        :param index: Index of the technique. [Default: 0]
        :param last: Whether this is the last technique. [Default: True]
        :param types: List of dictionaries or Enums from technique_fields
            to cast parameters, or None if no casting is desired.
            [Default: None]
        """
        self._validate_connection()
        first = index == 0

        if types is not None:
            params = ecl.cast_parameters(params, types)

        ecc_params = ecl.create_parameters(params, index)
        technique = ecl.technique_file(technique, self.kind)

        ecl.load_technique(self.idn, ch, technique, ecc_params, first, last)

        # update technques
        self.__techniques[ch].insert(index, TechParams(technique, params))

    def load_techniques(self, ch, techniques, parameters, types=None):
        """Loads a series of techniques on to the given channel.

        :param ch: Channel.
        :param techniques: A list of techniques.
        :param parameters: A list of dictionaries of key: value parameters,
            to use for the corresponding technique.
        :param types: List of dictonaries or Enums from technique_fields
            to cast parameters, or None if no casting is desired.
            [Default: None]
        """
        self._validate_connection()

        for index, technique in enumerate(techniques):
            params = parameters[index]
            last = index == len(techniques) - 1

            if isinstance(types, list):
                kinds = types[index]

            elif types is None:
                kinds = None

            else:
                raise TypeError("Invalid types provided.")

            self.load_technique(ch, technique, params, index, last, kinds)

    def update_parameters(self, ch, technique, parameters, index=0, types=None):
        """Updates technique parameters.

        :param ch: Channel.
        :param technique: Name of the technique.
        :param parameters: Dictionary of new parameter-values.
        :param index: Index of the technique. [Default: 0]
        :param types: Dictonary or Enum from technique_fields
            to cast parameters, or None if no casting is desired.
            [Default: None]
        """
        self._validate_connection()

        ecc_params = ecl.create_parameters(parameters, index, types)

        ecl.update_parameters(self.idn, ch, technique, ecc_params, index, self.kind)

        # update techniques
        self.__techniques[ch][index] = TechParams(technique, parameters)

    def start_channel(self, ch):
        """Starts a device channel.

        :param ch: Channel to start.
        """
        self._validate_connection()
        ecl.start_channel(self.idn, ch)

    def start_channels(self, chs=None):
        """Starts multiple channels.

        :param chs: List of channels to start, or None to start all.
            [Default: None]
        """
        self._validate_connection()
        if chs is None:
            # start all channels
            chs = list(range(self.info.NumberOfChannels))

        ecl.start_channels(self.idn, chs)

    def stop_channel(self, ch):
        """Stops a device channel.

        :param ch: Channel to stop.
        """
        self._validate_connection()
        ecl.stop_channel(self.idn, ch)

    def stop_channels(self, chs=None):
        """Stops multiple channels.

        :param chs: List of channels to stop, or None to stop all.
            [Default: None]
        """
        self._validate_connection()
        if chs is None:
            # stop all channels
            chs = list(range(self.info.NumberOfChannels))

        ecl.stop_channels(self.idn, chs)

    def channel_info(self, ch):
        """Gets channel info.

        :param ch: The channel to probe.
        :returns: ChannelInfo.
        """
        self._validate_connection()

        info = ecl.channel_info(self.idn, ch)
        return info

    def get_values(self, ch):
        """Gets the current data on the channel.

        :param ch: Channel.
        :returns: A dictionary of key-value pairs.
        """
        self._validate_connection()

        values = ecl.get_values(self.idn, ch)
        return values

    async def get_data(self, ch):
        """Gets data stored on the channel.

        :param ch: Channel.
        :returns: TechData object with properties [ data, info, value ].
        """
        self._validate_connection()

        raw = await ecl.get_data_async(self.idn, ch)
        return TechData(*raw)

    def _validate_connection(self):
        """
        :returns: True if the device has an id assigned.
        :raises: RuntimeError if device does not have an id assigned.
        """
        if self.idn is None:
            raise RuntimeError("Device is not connected.")

        return True

    def __init_variables(self):
        """Initializes instance variables."""
        self.__idn = None  # device identifier
        self.__plugged = None  # list of plugged in channels
        self.__techniques = None  # list of channel techniques


class BiologicDeviceAsync:
    """Represents a Biologic Device."""

    async def __init__(self, address, timeout=5, populate_info=True):
        """
        :param address: The address of the device to connect to.
        :param timeout: Timeout in seconds. [Defualt: 5]
        :param populate_info: Run an initial #populate_info. [Default: True]
        """
        self.__address = address
        self.timeout = timeout

        self.__init_variables()

        self.__info = None
        if populate_info:
            await self.populate_info()

    def __del__(self):
        if self.is_connected():
            self.disconnect()

    @property
    def address(self):
        """
        :returns: Connection string of device.
        """
        return self.__address

    @property
    def idn(self):
        """
        :returns: Device identifier.
        """
        return self.__idn

    @property
    def kind(self):
        """
        :returns: Device model.
        :raises: RuntimeError if no device is connected at the connection string.
        """
        if self.info is None:
            # Device has not yet been connected
            raise RuntimeError(
                "Device must have been connected before retrieving info."
            )

        return ecl.DeviceCodes(self.info.DeviceCode)

    @property
    def info(self):
        """
        :returns: DeviceInfo object.
        """
        return self.__info

    @property
    def plugged(self):
        """
        :returns: List of channel availablilities.
        """
        return self.__plugged

    @property
    def channels(self):
        """
        :returns: List of ChannelInfo objects.
        """
        self._validate_connection()

        return [
            ecl.channel_info(self.idn, ch) if available else None
            for ch, available in enumerate(self.plugged)
        ]

    @property
    async def hardware_configuration(self):
        """
        :returns: Dictionary of HardwareConfigurations for each channel,
            or None if the channel is not available.
        """
        self._validate_connection()

        if self.kind is not ecl.DeviceCodes.KBIO_DEV_SP300:
            raise RuntimeError(
                "Hardware configuration is only available for SP-300 devices."
            )

        # collect channel configurations for available channels
        available_chs = []
        ch_confs = []
        for ch, available in enumerate(self.plugged):
            if available:
                available_chs.appned(ch)
                ch_confs.append(self.channel_configuration(ch))

        ch_confs = await asyncio.gather(*ch_confs)

        # collect results for all channels
        confs = {
            ch: (ch_confs[available_chs.index(ch)] if ch in available_chs else None)
            for ch, available in enumerate(self.plugged)
        }

        return confs

    @property
    def techniques(self):
        """
        :returns: List of TechParams loaded on each channel.
        """
        return self.__techniques

    async def connect(self, bin_file=None, xlx_file=None):
        """Connects to the device at the address. Checks channel status.

        :param bin_file: Path to the bin file to use. If None, uses default.
            [Default: None]
        :param xlx_file: Path to the xilinx file to use. If None, uses default.
            [Default: None]
        """
        if self.idn is not None:
            raise RuntimeError("Device already connected.")

        (idn, info) = await ecl.connect_async(self.address, self.timeout)

        self.__idn = idn
        self.__info = info

        # initialize only connected channels
        chs = []
        self.__plugged = ecl.get_channels_async(self.idn)
        for i in range(len(self.plugged)):
            if self.plugged[i]:
                chs.append(i)

        try:
            await ecl.init_channels_async(
                self.idn, chs, bin_file=bin_file, xlx_file=xlx_file
            )
        except EcError as err:
            if err.value == -9:
                # ECLab firmware loaded
                pass

        self.__techniques = [list() for ch in self.plugged]

    async def disconnect(self):
        """Disconnect form the device."""
        self._validate_connection()
        await ecl.disconnect_async(self.idn)
        self.__init_variables()  # reset vairables

    async def populate_info(self):
        """Connects then disconnects from the device in order to populate info."""
        await self.connect()
        await self.disconnect()

    async def is_connected(self):
        """Returns if the device is conencted or not.

        :returns: Boolean descirbing the state of connection.
        """
        if self.idn is None:
            return False

        connected = await ecl.is_connected_async(self.idn)

        # update state
        if not connected:
            self.__init_variables()

        elif self.idn is None:
            # connected but id is None
            raise RuntimeError("Device is connected but does not have an id assigned.")

        return connected

    async def channel_configuration(self, ch):
        """
        :param ch: Channel to configure.
        :returns: HardwareConf object for the channel or None if channel is not available.
        """
        self._validate_connection()

        if not self.plugged[ch]:
            return None

        conf = await ecl.get_hardware_configuration_async(self.idn, ch)
        return HardwareConfiguration(
            connection=ecl.ElectrodeConnection(conf.Conn),
            mode=ecl.ChannelMode(conf.Ground),
        )

    async def set_channel_configuration(self, ch, mode, connection):
        """Sets the hardware configuration for the given channel.

        :param ch: Channel to set.
        :param mode: ChannelMode.
        :param connection: ElectrodeConnection.
        """
        self._validate_connection()

        if self.kind is not ecl.DeviceCodes.KBIO_DEV_SP300:
            raise RuntimeError(
                "Hardware configuration is only available for SP-300 devices."
            )

        await ecl.set_hardware_configuration_async(self.idn, ch, mode, connection)

    async def load_technique(
        self, ch, technique, params, index=0, last=True, types=None
    ):
        """Loads a single technique on to the given channel.

        :param ch: The channel to load the technique on to.
        :param technique: Name of the technique to load.
        :param params: A dictionary of parameters to use.
        :param index: Index of the technique. [Default: 0]
        :param last: Whether this is the last technique. [Default: True]
        :param types: List of dictonaries or Enums from technique_fields
            to cast parameters, or None if no casting is desired.
            [Default: None]
        """
        self._validate_connection()
        first = index == 0

        if types is not None:
            params = await ecl.cast_parameters_async(params, types)

        ecc_params = ecl.create_parameters(params, index)
        technique = ecl.technique_file(technique, self.kind)

        await ecl.load_technique_async(self.idn, ch, technique, ecc_params, first, last)

        # update technques
        self.__techniques[ch].insert(index, TechParams(technique, params))

    async def load_techniques(self, ch, techniques, parameters, types=None):
        """Loads a series of techniques on to the given channel.

        :param ch: Channel.
        :param techniques: A list of techniques.
        :param parameters: A list of dictionaries of key: value parameters,
            to use for the corresponding technique.
        :param types: List of dictonaries or Enums from technique_fields
            to cast parameters, or None if no casting is desired.
            [Default: None]
        """
        self._validate_connection()

        for index, technique in enumerate(techniques):
            params = parameters[index]
            last = index == len(techniques) - 1

            if isinstance(types, list):
                kinds = types[index]

            elif types is None:
                kinds = None

            else:
                raise TypeError("Invalid types provided.")

            await self.load_technique(ch, technique, params, index, last, kinds)

    async def update_parameters(self, ch, technique, parameters, index=0, types=None):
        """Updates technique parameters.

        :param ch: Channel.
        :param technique: Name of the technique.
        :param parameters: Dictionary of new parameter-values.
        :param index: Index of the technique. [Default: 0]
        :param types: Dictonary or Enum from technique_fields
            to cast parameters, or None if no casting is desired.
            [Default: None]
        """
        self._validate_connection()

        ecc_params = await ecl.create_parameters_async(parameters, index, types)

        await ecl.update_parameters_async(
            self.idn, ch, technique, ecc_params, index, self.kind
        )

        # update techniques
        self.__techniques[ch][index] = TechParams(technique, parameters)

    async def start_channel(self, ch):
        """Starts a device channel.

        :param ch: Channel to start.
        """
        self._validate_connection()
        await ecl.start_channel_async(self.idn, ch)

    async def start_channels(self, chs=None):
        """Starts multiple channels.

        :param chs: List of channels to start, or None to start all.
            [Default: None]
        """
        self._validate_connection()

        if chs is None:
            # start all channels
            chs = list(range(self.info.NumberOfChannels))

        await ecl.start_channels_async(self.idn, chs)

    async def stop_channel(self, ch):
        """Stops a device channel.

        :param ch: Channel to stop.
        """
        self._validate_connection()
        await ecl.stop_channel_async(self.idn, ch)

    async def stop_channels(self, chs=None):
        """Stops multiple channels.

        :param chs: List of channels to stop, or None to stop all.
            [Default: None]
        """
        self._validate_connection()
        if chs is None:
            # stop all channels
            chs = list(range(self.info.NumberOfChannels))

        await ecl.stop_channels_async(self.idn, chs)

    async def channel_info(self, ch):
        """Gets channel info.

        :param ch: The channel to probe.
        :returns: ChannelInfo.
        """
        self._validate_connection()

        info = await ecl.channel_info_async(self.idn, ch)
        return info

    async def get_values(self, ch):
        """Gets the current data on the channel.

        :param ch: Channel.
        :returns: A dictionary of key-value pairs.
        """
        self._validate_connection()

        values = await ecl.get_values_async(self.idn, ch)
        return values

    async def get_data(self, ch):
        """Gets data stored on the channel.

        :param ch: Channel.
        :returns: TechData object with properties [ data, info, value ].
        """
        self._validate_connection()

        (data, info, values) = await ecl.get_data_async(self.idn, ch)
        return TechData(data, info, values)

    # --- private methods ---

    def _validate_connection(self):
        """
        :returns: True if the device has an id assigned.
        :raises: RuntimeError if device does not have an id assigned.
        """
        if self.idn is None:
            raise RuntimeError("Device is not connected.")

        return True

    def __init_variables(self):
        """Initializes instance variables."""
        self.__idn = None  # device identifier
        self.__plugged = None  # list of plugged in channels
        self.__techniques = None  # list of channel techniques
