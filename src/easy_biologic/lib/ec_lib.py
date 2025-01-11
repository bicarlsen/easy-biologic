import logging
import os
import asyncio
import ctypes as c
import platform
import typing
import inspect
import functools
from enum import Enum

from .ec_errors import EcError
from .. import common


class DeviceCodes(Enum):
    """Device codes used to identify the device type."""

    KBIO_DEV_VMP = 0
    KBIO_DEV_VMP2 = 1
    KBIO_DEV_MPG = 2
    KBIO_DEV_BISTAT = 3
    KBIO_DEV_MCS_200 = 4
    KBIO_DEV_VMP3 = 5
    KBIO_DEV_VSP = 6
    KBIO_DEV_HCP803 = 7
    KBIO_DEV_EPP400 = 8
    KBIO_DEV_EPP4000 = 9
    KBIO_DEV_BISTAT2 = 10
    KBIO_DEV_FCT150S = 11
    KBIO_DEV_VMP300 = 12
    KBIO_DEV_SP50 = 13
    KBIO_DEV_SP150 = 14
    KBIO_DEV_FCT50S = 15
    KBIO_DEV_SP300 = 16
    KBIO_DEV_CLB500 = 17
    KBIO_DEV_HCP1005 = 18
    KBIO_DEV_CLB2000 = 19
    KBIO_DEV_VSP300 = 20
    KBIO_DEV_SP200 = 21
    KBIO_DEV_MPG2 = 22
    KBIO_DEV_ND1 = 23
    KBIO_DEV_ND2 = 24
    KBIO_DEV_ND3 = 25
    KBIO_DEV_ND4 = 26
    KBIO_DEV_SP240 = 27
    KBIO_DEV_MPG205 = 28
    KBIO_DEV_MPG210 = 29
    KBIO_DEV_MPG220 = 30
    KBIO_DEV_MPG240 = 31
    KBIO_DEV_BP300 = 32
    KBIO_DEV_VMP3e = 33
    KBIO_DEV_VSP3e = 34
    KBIO_DEV_SP50E = 35
    KBIO_DEV_SP150E = 36
    KBIO_DEV_UNKNOWN = 255


class DeviceCodeDescriptions(Enum):
    """Description of DeviceCodes."""

    KBIO_DEV_VMP = "VMP device"
    KBIO_DEV_VMP2 = "VMP2 device"
    KBIO_DEV_MPG = "MPG device"
    KBIO_DEV_BISTAT = "BISTAT device"
    KBIO_DEV_MCS_200 = "MCS-200 device"
    KBIO_DEV_VMP3 = "VMP3 device"
    KBIO_DEV_VSP = "VSP device"
    KBIO_DEV_HCP803 = "HCP-803 device"
    KBIO_DEV_EPP400 = "EPP-400 device"
    KBIO_DEV_EPP4000 = "EPP-4000 device"
    KBIO_DEV_BISTAT2 = "BISTAT 2 device"
    KBIO_DEV_FCT150S = "FCT-150S device"
    KBIO_DEV_VMP300 = "VMP-300 device"
    KBIO_DEV_SP50 = "SP-50 device"
    KBIO_DEV_SP150 = "SP-150 device"
    KBIO_DEV_FCT50S = "FCT-50S device"
    KBIO_DEV_SP300 = "SP300 device"
    KBIO_DEV_CLB500 = "CLB-500 device"
    KBIO_DEV_HCP1005 = "HCP-1005 device"
    KBIO_DEV_CLB2000 = "CLB-2000 device"
    KBIO_DEV_VSP300 = "VSP-300 device"
    KBIO_DEV_SP200 = "SP-200 device"
    KBIO_DEV_MPG2 = "MPG2 device"
    KBIO_DEV_ND1 = "RESERVED"
    KBIO_DEV_ND2 = "RESERVED"
    KBIO_DEV_ND3 = "RESERVED"
    KBIO_DEV_ND4 = "RESERVED"
    KBIO_DEV_SP240 = "SP-240 device"
    KBIO_DEV_MPG205 = "MPG-205 (VMP3)"
    KBIO_DEV_MPG210 = "MPG-210 (VMP3)"
    KBIO_DEV_MPG220 = "MPG-220 (VMP3)"
    KBIO_DEV_MPG240 = "MPG-240 (VMP3)"
    KBIO_DEV_BP300 = "BP-300 (VMP300)"
    KBIO_DEV_VMP3e = "VMP-3e (VMP3)"
    KBIO_DEV_VSP3e = "VSP-3e (VMP3)"
    KBIO_DEV_SP50E = "SP-50e (VMP3)"
    KBIO_DEV_SP150E = "SP-150e (VMP3)"
    KBIO_DEV_UNKNOWN = "Unknown device"


class IRange(Enum):
    """Current ranges.

    Unit are in Amps.
    `p`: "pico-"
    `n`: "nano-"
    `u`: "micro-"
    `m`: "milli-"
    `a`: "Amps"

    `KEEP` Keeps the previous range.
    """

    p100 = 0
    n1 = 1
    n10 = 2
    n100 = 3
    u1 = 4
    u10 = 5
    u100 = 6
    m1 = 7
    m10 = 8
    m100 = 9
    a1 = 10

    KEEP = -1
    BOOSTER = 11
    AUTO = 12


class ERange(Enum):
    """Voltage ranges.

    Units are Volts.
    """

    v2_5 = 0
    v5 = 1
    v10 = 2
    AUTO = 3


class Bandwidth(Enum):
    """Bandwidths.

    `BW1`: "Slow"
    `BW5`: "Medium"
    `BW7`: "Fast"
    `BW8` and `BW9` are only available for SP300 series devices.
    """

    BW1 = 1
    BW2 = 2
    BW3 = 3
    BW4 = 4
    BW5 = 5
    BW6 = 6
    BW7 = 7
    BW8 = 8
    BW9 = 9


class Filter(Enum):
    """Filter frequencies.

    Units are in Hz.
    `k50`: 50 kHz
    `k1`: 1 kHz
    `h5`: 5 Hz
    """

    OFF = 0
    k50 = 1
    k1 = 2
    h5 = 3


class ElectrodeConnection(Enum):
    """
    `GROUNDED` connects CE to ground.
    """

    STANDARD = 0
    GROUNDED = 1


class ChannelMode(Enum):
    GROUNDED = 0
    FLOATING = 1


class TechniqueId(Enum):
    """Technique identifiers.

    `OCV`: Open circuit voltage
    `CA`: Chrono-amperometry
    `CP`: Chrono-potentiometry
    `CV`: Cyclic voltammetry
    `PEIS`: Potentio electrochemical impedance
    `GEIS`: Galvano electrochemical impedance
    `CALIMIT`: Chrono-amperometry with limits
    """

    NONE = 0
    OCV = 100
    CA = 101
    CP = 102
    CV = 103
    PEIS = 104
    GEIS = 107
    CALIMIT = 157


class ChannelState(Enum):
    """Channel state."""

    STOP = 0
    RUN = 1
    PAUSE = 2


class ParameterType(Enum):
    """Paramter type."""

    INT32 = 0
    BOOLEAN = 1
    SINGLE = 2
    FLOAT = 2


class LimitVariable(Enum):
    """Variable for limit tests."""

    E = 0
    AUX1 = 1
    AUX2 = 2
    I = 3


class LimitComparison(Enum):
    """Comparison operator for limit tests."""

    LT = 0  # Less than
    GT = 1  # Greater than


class LimitLogic(Enum):
    """Logical operator for limit tests."""

    OR = 0
    AND = 1


class ExitCondition(Enum):
    """Exit condition for limit tests."""

    NEXTSTEP = 0
    NEXTTECHNIQUE = 1
    STOP = 2


class DeviceInfo(c.Structure):
    """Stores information about a device.

    `RAMSize`: RAM size, in MB
    `CPU`: Computer board CPU
    `NumberOfChannels`: Number of channels connected
    `NumberOfSlots`: Number of slots available
    `FirmwareVersion`: Communication firmware version
    `FirmwareDate_yyyy`: Communication firmware date YYYY
    `FirmwareDate_mm`: Communication firmware date MM
    `FirmwareDate_dd`: Communication firmware date DD
    `HTdisplayOn`: Hyper-terminal print si available (bool)
    `NbOfConnectedPC`: Number of connected PCs
    """

    _fields_ = [
        ("DeviceCode", c.c_int32),
        ("RAMSize", c.c_int32),
        ("CPU", c.c_int32),
        ("NumberOfChannels", c.c_int32),
        ("NumberOfSlots", c.c_int32),
        ("FirmwareVersion", c.c_int32),
        ("FirmwareDate_yyyy", c.c_int32),
        ("FirmwareDate_mm", c.c_int32),
        ("FirmwareDate_dd", c.c_int32),
        ("HTdisplayOn", c.c_int32),
        ("NbOfConnectedPC", c.c_int32),
    ]


class ChannelInfo(c.Structure):
    """Stores information of a channel.

    `Channel`: Channels (0, 1, 2, ..., 15)
    `FirmwareCode`: Identifier of the firmware loaded on the channel
    `AmpCode`: Amplifier code
    `NbAmps`: Number of amplifiers (0, 1, 2, ..., 16)
    `Lcboard`: Low current board present (= 1)
    `Zboard`: TRUE if channel w/ impedance capabilities
    `RESERVED`: (not used)
    `MemSize`: Memory size (in bytes)
    `MemFilled`: Memory filled (in bytes)
    `State`: Channel state (run/stop/pause)
    `MaxIRange`: Maximum I range allowed
    `MinIRange`: Minimum I range allowed
    `MaxBandwidth`: Maximum bandwidth allowed
    `NbOfTechniques`: Number of techniques loaded
    """

    _fields_ = [
        ("Channel", c.c_int32),
        ("BoardVersion", c.c_int32),
        ("BoardSerialNumber", c.c_int32),
        ("FirmwareCode", c.c_int32),
        ("FirmwareVersion", c.c_int32),
        ("XilinxVersion", c.c_int32),
        ("AmpCode", c.c_int32),
        ("NbAmps", c.c_int32),
        ("Lcboard", c.c_int32),
        ("Zboard", c.c_int32),
        ("RESERVED", c.c_int32),
        ("RESERVED", c.c_int32),
        ("MemSize", c.c_int32),
        ("MemFilled", c.c_int32),
        ("State", c.c_int32),
        ("MaxIRange", c.c_int32),
        ("MinIRange", c.c_int32),
        ("MaxBandwidth", c.c_int32),
        ("NbOfTechniques", c.c_int32),
    ]


class HardwareConf(c.Structure):
    """Stores information about the hardware configuration.

    `Conn`: Electrode connection
    `Ground`: Instrument ground
    """

    _fields_ = [
        ("Conn", c.c_int32),
        ("Ground", c.c_int32),
    ]


class EccParam(c.Structure):
    """Represents a single technique parameter.

    `ParamStr`: String defining the parameter label
    `ParamType`: Parameter type (0=int32, 1=boolean, 2=single)
    `ParamVal`: Parameter value (WARNING: numerical value)
    `ParamIndex`: Parameter index (0-based). Useful for multi-step parameters only.
    """

    _fields_ = [
        ("ParamStr", c.c_char * 64),
        ("ParamType", c.c_int32),
        ("ParamVal", c.c_int32),
        ("ParamIndex", c.c_int32),
    ]


class EccParams(c.Structure):
    """Represents a list of technique parameters."""

    _pack_ = 4

    _fields_ = [("len", c.c_int32), ("pParams", c.POINTER(EccParam))]


class CurrentValues(c.Structure):
    """Represents the values measured from and states of the device.

    `State`: Channel state (run/stop/pause)
    `MemFilled`: Memory filled (in Bytes)
    `TimeBase`: Time base (s)
    `Ewe`: Working electrode potential (V)
    `EweRangeMin`: Ewe min range (V)
    `EweRangeMax`: Ewe max range (V)
    `Ece`: Counter electrode potential (V)
    `EceRangeMin`: Ece min range (V)
    `EceRangeMax`: Ece max range (V)
    `Eoverflow`: Potential overflow
    `I`: Current value (A)
    `IRange`: Current range
    `Ioverflow`: Current overflow
    `ElapsedTime`: Elapsed time (s)
    `Freq`: Frequency (Hz)
    `Rcomp`: R compensation (Ohm)
    `Saturation`: E or/and I saturation
    `OptErr`: Hardware Option Error Code
    `OptPos`: Index of the option generating the OptErr (VMP-300 series only, otherwise 0)
    """

    _fields_ = [
        ("State", c.c_int32),
        ("MemFilled", c.c_int32),
        ("TimeBase", c.c_float),
        ("Ewe", c.c_float),
        ("EweRangeMin", c.c_float),
        ("EweRangeMax", c.c_float),
        ("Ece", c.c_float),
        ("EceRangeMin", c.c_float),
        ("EceRangeMax", c.c_float),
        ("Eoverflow", c.c_int32),
        ("I", c.c_float),
        ("IRange", c.c_int32),
        ("Ioverflow", c.c_int32),
        ("ElapsedTime", c.c_float),
        ("Freq", c.c_float),
        ("Rcomp", c.c_float),
        ("Saturation", c.c_int32),
        ("OptErr", c.c_int32),
        ("OptPos", c.c_int32),
    ]


class DataInfo(c.Structure):
    """Represents metadata for the values measured for a technique.
    Used to parse the data collected from the device.

    `IRQskipped`: Number of IRQ skipped
    `NbRows`: Number of rows in the data buffer
    `NbCols`: Number of columns in the data buffer
    `TechniqueIndex`: Index of technique that has generated data.
        Only useful for linked techniques
    `TechniqueID`: Identifier of the technique which has generated the data.
        Must be used to identify the data format in the data buffer
    `ProcessIndex`: Index of the process of the technique which has generated the data.
        Must be used to identify the data format in the data buffer
    `loop`: Loop number
    `StartTime`: Start time (s)
    `MuxPad`: Depricated
    """

    _fields_ = [
        ("IRQskipped", c.c_int32),
        ("NbRows", c.c_int32),
        ("NbCols", c.c_int32),
        ("TechniqueIndex", c.c_int32),
        ("TechniqueID", c.c_int32),
        ("ProcessIndex", c.c_int32),
        ("loop", c.c_int32),
        ("StartTime", c.c_double),
        ("MuxPad", c.c_int32),
    ]


VMP3_DEVICE_FAMILY = {
    DeviceCodes.KBIO_DEV_VMP2,
    DeviceCodes.KBIO_DEV_VMP3,
    DeviceCodes.KBIO_DEV_BISTAT,
    DeviceCodes.KBIO_DEV_BISTAT2,
    DeviceCodes.KBIO_DEV_MCS_200,
    DeviceCodes.KBIO_DEV_VSP,
    DeviceCodes.KBIO_DEV_SP50,
    DeviceCodes.KBIO_DEV_SP150,
    DeviceCodes.KBIO_DEV_FCT50S,
    DeviceCodes.KBIO_DEV_FCT150S,
    DeviceCodes.KBIO_DEV_CLB500,
    DeviceCodes.KBIO_DEV_CLB2000,
    DeviceCodes.KBIO_DEV_HCP803,
    DeviceCodes.KBIO_DEV_HCP1005,
    DeviceCodes.KBIO_DEV_MPG2,
    DeviceCodes.KBIO_DEV_MPG205,
    DeviceCodes.KBIO_DEV_MPG210,
    DeviceCodes.KBIO_DEV_MPG220,
    DeviceCodes.KBIO_DEV_MPG240,
    DeviceCodes.KBIO_DEV_VMP3e,
    DeviceCodes.KBIO_DEV_VSP3e,
    DeviceCodes.KBIO_DEV_SP50E,
    DeviceCodes.KBIO_DEV_SP150E,
}


# TODO [2]: Incorporate unknown device codes
# Should also include SP100 but do not have their device codes.
# Do not know which family these belong to.
# KBIO_DEV_VMP, KBIO_DEV_MPG, KBIO_DEV_EPP400, KBIO_DEV_EPP4000
SP300_DEVICE_FAMILY = {
    DeviceCodes.KBIO_DEV_SP200,
    DeviceCodes.KBIO_DEV_SP300,
    DeviceCodes.KBIO_DEV_VSP300,
    DeviceCodes.KBIO_DEV_VMP300,
    DeviceCodes.KBIO_DEV_SP240,
    DeviceCodes.KBIO_DEV_BP300,
}

# get platform architecture
arch = platform.architecture()
bits = arch[0]
bits = bits.replace("bit", "")
bits = int(bits)
logging.debug("[biologic_controller] Running on {}-bit platform.".format(bits))

bits = "" if (bits == 32) else "64"
dll_file = os.path.join(common.technique_directory(), "EClib{}.dll".format(bits))
__dll = c.WinDLL(dll_file)

# load DLL functions
# hardware functions
BL_Connect = __dll["BL_Connect"]
BL_Connect.restype = c.c_int32

BL_Disconnect = __dll["BL_Disconnect"]
BL_Disconnect.restype = c.c_int32

BL_TestConnection = __dll["BL_TestConnection"]
BL_TestConnection.restype = c.c_int32

BL_LoadFirmware = __dll["BL_LoadFirmware"]
BL_LoadFirmware.restype = c.c_int32

BL_IsChannelPlugged = __dll["BL_IsChannelPlugged"]
BL_IsChannelPlugged.restype = c.c_bool

BL_GetChannelsPlugged = __dll["BL_GetChannelsPlugged"]
BL_GetChannelsPlugged.restype = c.c_int32

BL_GetChannelInfos = __dll["BL_GetChannelInfos"]
BL_GetChannelInfos.restype = c.c_int32

BL_GetHardConf = __dll["BL_GetHardConf"]
BL_GetHardConf.restype = c.c_int32

BL_SetHardConf = __dll["BL_SetHardConf"]
BL_SetHardConf.restype = c.c_int32

BL_LoadTechnique = __dll["BL_LoadTechnique"]
BL_LoadTechnique.restype = c.c_int32

BL_DefineBoolParameter = __dll["BL_DefineBoolParameter"]
BL_DefineBoolParameter.restype = c.c_int32

BL_DefineSglParameter = __dll["BL_DefineSglParameter"]
BL_DefineSglParameter.restype = c.c_int32

BL_DefineIntParameter = __dll["BL_DefineIntParameter"]
BL_DefineIntParameter.restype = c.c_int32

BL_UpdateParameters = __dll["BL_UpdateParameters"]
BL_UpdateParameters.restype = c.c_int32

BL_StartChannel = __dll["BL_StartChannel"]
BL_StartChannel.restype = c.c_int32

BL_StartChannels = __dll["BL_StartChannels"]
BL_StartChannels.restype = c.c_int32

BL_StopChannel = __dll["BL_StopChannel"]
BL_StopChannel.restype = c.c_int32

BL_StopChannels = __dll["BL_StopChannels"]
BL_StopChannels.restype = c.c_int32

BL_GetCurrentValues = __dll["BL_GetCurrentValues"]
BL_GetCurrentValues.restype = c.c_int32

BL_GetData = __dll["BL_GetData"]
BL_GetData.restype = c.c_int32

BL_ConvertNumericIntoSingle = __dll["BL_ConvertNumericIntoSingle"]
BL_ConvertNumericIntoSingle.restype = c.c_int32

methods = [
    BL_Connect,
    BL_Disconnect,
    BL_TestConnection,
    BL_LoadFirmware,
    BL_IsChannelPlugged,
    BL_GetChannelsPlugged,
    BL_GetChannelInfos,
    BL_GetHardConf,
    BL_SetHardConf,
    BL_LoadTechnique,
    BL_UpdateParameters,
    BL_StartChannel,
    BL_StartChannels,
    BL_StopChannel,
    BL_StopChannels,
    BL_GetCurrentValues,
    BL_GetData,
]


# To handle asyncio.coroutine removal in Python 3.11
# Following suggestion from https://discuss.python.org/t/deprecation-of-asyncio-coroutine/4461/2
def coroutine(fn: typing.Callable) -> typing.Callable:
    if int(platform.python_version_tuple()[1]) <= 10:
        return asyncio.coroutine(fn)

    if inspect.iscoroutinefunction(fn):
        return fn

    @functools.wraps(fn)
    async def _wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return _wrapper


for method in methods:
    async_name = method.__name__ + "_async"
    globals()[async_name] = coroutine(method)


def create_parameter(name, value, index=0, kind=None):
    """Factory to create an EccParam structure.

    :param name: Paramter name.
    :param value: Value of the parameter.
        The kind is interpreted to be a bool, integer, or single (float),
        unless the kind parameter is passed.
    :param index: Parameter index. [Default: 0]
    :param kind: The kind of parameter, or None to interpret from the value.
        Values are [ None, 'bool', 'int', 'single' ].
        [Default: None]
    :returns: An EccParam structure.
    """
    if kind is None:
        # interpret kind from value
        val_kind = type(value)

        if val_kind is bool:
            kind = "bool"

        elif val_kind is int:
            kind = "int"

        elif val_kind is float:
            kind = "single"

        else:
            raise TypeError("[ec_lib] Invalid value type {}.".format(val_kind))

    if kind == "bool":
        create = BL_DefineBoolParameter
        value = c.c_bool(value)

    elif kind == "int":
        create = BL_DefineIntParameter
        value = c.c_int32(value)

    elif kind == "single":
        create = BL_DefineSglParameter
        value = c.c_float(value)

    else:
        raise ValueError("[ec_lib] Invalid kind {}.".format(kind))

    name = name.encode("utf-8")
    index = c.c_int32(index)
    param = EccParam()
    create(name, value, index, c.byref(param))
    return param


def combine_parameters(params):
    """Creates an ECCParams list of parameters.

    :param params: List of EccParam parameters to combine.
    :returns: EccParams structure.
    """
    num_params = len(params)
    param_list = (EccParam * num_params)(*params)
    length = c.c_int32(num_params)

    params = EccParams()
    params.len = length
    params.pParams = c.cast(param_list, c.POINTER(EccParam))

    return params


def create_parameters(params, index=0, types=None):
    """Creates an EccParams list of parameters.

    :param params: A dictionary of parameters, with keys as
        the parameter name and values as the parameter value or a list of values.
        If a value is a list, one parameter is created for each value.
    :param index: Starting index for the parameters.
        For lists of values, the index of the value in the list is added to the index.
        [Default: 0]
    :param types: A dictionary or Enum mapping parameter keys to types for casting,
        or None if type casting is not desired.
        See #cast_parameters.
        [Default: None]
    :returns: EccParams structure.
    """
    # cast types if desired
    if types is not None:
        params = cast_parameters(params, types)

    param_list = []
    for name, values in params.items():
        if not isinstance(values, list):
            # single value given, turn into list
            values = [values]

        for idx, value in enumerate(values):
            # create parameter for each value
            param = create_parameter(name, value, index + idx)
            param_list.append(param)

    return combine_parameters(param_list)


def cast_parameters(parameters, types):
    """Cast parameters to given types.

    :param parameters: Dictionary of key value pairs of parameters.
        If value is a list, each element is cast.
    :param types: Dictionary or enum from technique_fields
        of key type pairs for the parameters.
    :returns: New dictionary of values cast to given types.
        If a key is not provided in the types, no change is made to the value.
    """
    cast = {}
    if isinstance(types, dict):
        # dictionary passed
        for key, value in parameters.items():
            if key in types:
                # type provided
                kind = types[key]
                if isinstance(value, list):
                    value = [kind(val) for val in value]
                else:
                    value = kind(value)
            cast[key] = value
    elif issubclass(types, Enum):
        # enum passed
        for key, value in parameters.items():
            if key in types.__members__:
                kind = types[key].value
                if isinstance(value, list):
                    value = [kind(val) for val in value]
                else:
                    value = kind(parameters[key])
            cast[key] = value
    else:
        raise TypeError("Invalid types provided.")

    return cast


def convert_numeric(num):
    """Converts a numeric value into a single (float).

    :param num: Numeric value to convert.
    :returns: Value of numeric as a float.
    """
    num = c.c_uint32(num)
    val = c.c_float()

    validate(BL_ConvertNumericIntoSingle(num, c.byref(val)))

    return val.value


def connect(address, timeout=5):
    """Connect to the device at the given address.

    :param address: Address of the device.
    :param timout: Timout in seconds. [Default: 5]
    :returns: A tuple of ( id, info ), where id is the connection id,
        and info is a DeviceInfo structure.
    """
    address = c.create_string_buffer(address.encode("utf-8"))
    timeout = c.c_uint8(timeout)
    idn = c.c_int32()
    info = DeviceInfo()

    logging.debug("[easy-biologic] Connecting to device {}.".format(address.value))
    err = BL_Connect(c.byref(address), timeout, c.byref(idn), c.byref(info))

    validate(err)
    logging.debug("[easy-biologic] Conneced to device {}.".format(address.value))

    return (idn.value, info)


def disconnect(idn):
    """Disconnect from the given device.

    :param address: The address of the device.
    """
    idn = c.c_int32(idn)

    logging.debug("[easy-biologic] Disconnecting from device {}.".format(idn.value))
    err = BL_Disconnect(idn)
    validate(err)
    logging.debug("[easy-biologic] Disconnected from device {}.".format(idn.value))


def is_connected(idn):
    """Returns whether the given device is connected or not.

    :param idn: The device id.
    :returns: Boolean of the connection state, or the error code.
    """
    idn = c.c_int32(idn)

    try:
        logging.debug(
            "[easy-biologic] Checking connection of device {}.".format(idn.value)
        )
        validate(BL_TestConnection(idn))

    except:
        return False

    return True


def init_channels(idn, chs, force_reload=False, bin_file=None, xlx_file=None):
    """Initializes a channel by loading its firmware.

    :param idn: Device identifier.
    :param chs: List of channels to initialize.
    :param force_reload: Boolean indicating whether to force a firmware reload each time.
        [Default: False]
    :param bin: bin file containing, or None to use default.
        [Default: None]
    :param xlx_file: xilinx file, or None to use default.
        [Default: None]
    :returns: Results array with error codes for each channel.
    """
    length = max(chs) + 1
    results = (c.c_int32 * length)()
    active = create_active_array(chs, length)
    idn = c.c_int32(idn)
    show_gauge = c.c_bool(False)

    bin_file = (
        c.c_void_p()
        if (bin_file is None)
        else c.byref(c.create_string_buffer(bin_file.encode("utf-8")))
    )

    xlx_file = (
        c.c_void_p()
        if (xlx_file is None)
        else c.byref(c.create_string_buffer(xlx_file.encode("utf-8")))
    )

    logging.debug(f"[easy-biologic] Initializing channels {chs} on device {idn.value}.")
    err = BL_LoadFirmware(
        idn,
        c.byref(active),
        c.byref(results),
        length,
        show_gauge,
        force_reload,
        bin_file,
        xlx_file,
    )

    validate(err)

    return results


def is_channel_connected(idn, ch):
    """:param idn: Id of the device.
    :param ch: Channel to check.
    :returns: If the channel is connected.
    """
    idn = c.c_int32(idn)
    ch = c.c_uint8(ch)

    logging.debug("[easy-biologic] Checking channel {}'s connection.".format(ch.value))
    conn = BL_IsChannelPlugged(idn, ch)

    return conn


def get_channels(idn, size=16):
    """Returns the plugged state of channels.

    :param idn: The device id.
    :param size: The number of channels. [Default: 16]
    :return: A list of booleans indicating the plugged state of the channel.
    """
    idn = c.c_int32(idn)
    channels = (c.c_uint8 * size)()
    size = c.c_int32(size)

    logging.debug("[easy-biologic] Getting channels for device {}.".format(idn.value))
    err = BL_GetChannelsPlugged(idn, c.byref(channels), size)

    validate(err)
    return [(ch == 1) for ch in channels]


def channel_info(idn, ch):
    """Returns information on the specified channel.

    :param idn: The device id.
    :param ch: The channel.
    :returns: ChannelInfo structure.
    """
    idn = c.c_int32(idn)
    ch = c.c_uint8(ch)
    info = ChannelInfo()

    logging.debug(
        "[easy-biologic] Getting info for channel {} on device {}.".format(
            ch.value, idn.value
        )
    )
    err = BL_GetChannelInfos(idn, ch, c.byref(info))

    validate(err)
    return info


def get_hardware_configuration(idn, ch):
    """Returns the hardware configuratiion of the specified channel.

    :param idn: The device id.
    :param ch: The channel.
    :returns: HardwareConf structure.
    """
    idn = c.c_int32(idn)
    ch = c.c_uint8(ch)
    conf = HardwareConf()

    logging.debug(
        "[easy-biologic] Getting hardware configuration for channel {} on device {}.".format(
            ch.value, idn.value
        )
    )
    err = BL_GetHardConf(idn, ch, c.byref(conf))

    validate(err)
    return conf


def set_hardware_configuration(idn, ch, mode, connection):
    """Sets the hardware configuration.

    :param idn: The device id.
    :param ch: The channel.
    :param mode: ChannelMode to set the instrument connection mode.
    :param connection: ElectrodeConnection to set the electrode connection mode.
    """
    idn = c.c_int32(idn)
    ch = c.c_uint8(ch)

    # validate connection parameters
    if isinstance(mode, ChannelMode):
        mode = mode.value

    elif mode not in [0, 1]:
        raise ValueError("Invalid values for mode.")

    if isinstance(connection, ElectrodeConnection):
        connection = connection.value

    elif connection not in [0, 1]:
        raise ValueError("Invalid values for connection.")

    conf = HardwareConf(
        Conn=c.c_int32(connection),  # electrode connection
        Ground=c.c_int32(mode),  # channel mode / instrument ground
    )

    logging.debug(
        "[easy-biologic] Setting hardware configuration for channel {} on device {}.".format(
            ch.value, idn.value
        )
    )
    err = BL_SetHardConf(idn, ch, conf)

    validate(err)


def load_technique(
    idn, ch, technique, params, first=True, last=True, device=None, verbose=False
):
    """Loads a technique onto a specified device channel.

    :param idn: Device id.
    :param ch: Channel.
    :param technique: Name of the technique file.
    :param params: EccParams structure for the technique.
    :param first: True if the technique is loaded first. [Defualt: True]
    :param last: True if this is the last technique. [Default: True]
    :param device: Type of device. Used to modify technique.
        [Default: None]
    :param verbose: Echoes the sent parameters for debugging. [Default: False]
    """
    idn = c.c_int32(idn)
    ch = c.c_uint8(ch)

    technique_path = technique_file(technique, device)
    technique = c.create_string_buffer(technique_path.encode("utf-8"))

    first = c.c_bool(first)
    last = c.c_bool(last)
    verbose = c.c_bool(verbose)

    logging.debug(
        "[easy-biologic] Loading technique on channel {} on device {}.".format(
            ch.value, idn.value
        )
    )
    err = BL_LoadTechnique(idn, ch, c.byref(technique), params, first, last, verbose)

    validate(err)


def update_parameters(idn, ch, technique, params, index=0, device=None):
    """Updates the parameters of a technique.

    :param idn: Device identifier.
    :param ch: Channel number.
    :param technique: Name of the technique file.
    :param params: EccParams struct of new parameters.
    :param index: Index of the technique. [Default: 0]
    :param device: Type of device. Used to modify technique.
        [Default: None]
    """

    idn = c.c_int32(idn)
    ch = c.c_uint8(ch)

    technique = technique_file(technique, device)
    technique = c.create_string_buffer(technique.encode("utf-8"))
    index = c.c_int32(index)

    logging.debug(
        "[easy-biologic] Updating parameters on channel {} on device {}.".format(
            ch.value, idn.value
        )
    )
    err = BL_UpdateParameters(idn, ch, index, params, c.byref(technique))

    validate(err)


def start_channel(idn, ch):
    """Starts techniques loaded on a channel.

    :param idn: Device identifier.
    :param ch: Channel to start.
    """
    idn = c.c_int32(idn)
    ch = c.c_uint8(ch)

    logging.debug(
        "[easy-biologic] Starting channel {} on device {}.".format(ch.value, idn.value)
    )
    err = BL_StartChannel(idn, ch)

    validate(err)


def start_channels(idn, chs):
    """Starts techniques loaded on the given channels.

    :param idn: Device identifier.
    :param chs: List of channels to start.
    """
    num_chs = max(chs) + 1
    results = (c.c_int32 * num_chs)()
    active = create_active_array(chs, num_chs)
    idn = c.c_int32(idn)

    logging.debug(
        "[easy-biologic] Starting channels {} on device {}.".format(chs, idn.value)
    )
    err = BL_StartChannels(idn, c.byref(active), c.byref(results), num_chs)

    validate(err)


def stop_channel(idn, ch):
    """Stops techniques loaded on a channel.

    :param idn: Device identifier.
    :param ch: Channel to stop.
    """
    idn = c.c_int32(idn)
    ch = c.c_uint8(ch)

    logging.debug(
        "[easy-biologic] Stopping channel {} on device {}.".format(ch.value, idn.value)
    )
    err = BL_StopChannel(idn, ch)

    validate(err)


def stop_channels(idn, chs):
    """Stops techniques loaded on the given channels.

    :param idn: Device identifier.
    :param chs: List of channels to stop.
    """
    num_chs = max(chs) + 1
    results = (c.c_int32 * num_chs)()
    active = create_active_array(chs, num_chs)
    idn = c.c_int32(idn)

    logging.debug(
        "[easy-biologic] Stopping channels {} on device {}.".format(chs, idn.value)
    )
    err = BL_StopChannels(idn, c.byref(active), c.byref(results), num_chs)

    validate(err)


def get_values(idn, ch):
    """Gets the current data values on the given device channel.

    :param idn: Device identifier.
    :param ch: Channel.
    :returns: CurrentValues object.
    """
    idn = c.c_int32(idn)
    ch = c.c_uint8(ch)
    values = CurrentValues()

    logging.debug(
        "[easy-biologic] Getting values of channel {} on device {}.".format(
            ch.value, idn.value
        )
    )
    err = BL_GetCurrentValues(idn, ch, c.byref(values))

    validate(err)
    return values


def get_data(idn, ch):
    """Gets data from the given device channel.
    Pulls data from the buffer and clears it.

    :param idn: Device identifier.
    :param ch: Channel.
    :returns: A tuple of ( data, data_info, current_values ) where
        data_info is a DataInfo object representing the data's metadata,
        data is a data array, and
        current_values is a CurrentValues object.
    """
    idn = c.c_int32(idn)
    ch = c.c_uint8(ch)
    data = (c.c_uint32 * 1000)()
    info = DataInfo()
    values = CurrentValues()

    logging.debug(
        "[easy-biologic] Getting data of channel {} on device {}.".format(
            ch.value, idn.value
        )
    )
    err = BL_GetData(idn, ch, c.byref(data), c.byref(info), c.byref(values))

    validate(err)
    return (data, info, values)


async def connect_async(address, timeout=5):
    """Connect to the device at the given address.

    :param address: Address of the device.
    :param timout: Timout in seconds. [Default: 5]
    :returns: A tuple of ( id, info ), where id is the connection id,
        and info is a DeviceInfo structure.
    """
    address = c.create_string_buffer(address.encode("utf-8"))
    timeout = c.c_uint8(timeout)
    idn = c.c_int32()
    info = DeviceInfo()

    logging.debug("[easy-biologic] Connecting to device {}.".format(address.value))
    err = await BL_Connect_async(c.byref(address), timeout, c.byref(idn), c.byref(info))

    validate(err)
    return (idn.value, info)


async def disconnect_async(idn):
    """Disconnect from the given device.

    :param address: The address of the device.
    """
    idn = c.c_int32(idn)

    logging.debug("[easy-biologic] Disconnecting from device {}.".format(idn.vlaue))
    err = await BL_Disconnect_async(idn)
    validate(err)


async def is_connected_async(idn):
    """Returns whether the given device is connected or not.

    :param idn: The device id.
    :returns: Boolean of the connection state, or the error code.
    """
    idn = c.c_int32(idn)

    try:
        logging.debug(
            "[easy-biologic] Checking connection of device {}.".format(idn.value)
        )
        validate(await BL_TestConnection_async(idn))

    except:
        return False

    return True


async def init_channels_async(
    idn, chs, force_reload=False, bin_file=None, xlx_file=None
):
    """Initializes a channel by loading its firmware.

    :param idn: Device identifier.
    :param chs: List of channels to initialize.
    :param force_reload: Boolean indicating whether to force a firmware reload each time.
        [Default: False]
    :param bin: bin file containing, or None to use default.
        [Default: None]
    :param xlx_file: xilinx file, or None to use default.
        [Default: None]
    """
    length = max(chs) + 1
    results = (c.c_int32 * length)()
    active = create_active_array(chs, length)
    idn = c.c_int32(idn)
    show_gauge = c.c_bool(False)

    bin_file = (
        c.c_void_p()
        if (bin_file is None)
        else c.byref(c.create_string_buffer(bin_file.encode("utf-8")))
    )

    xlx_file = (
        c.c_void_p()
        if (xlx_file is None)
        else c.byref(c.create_string_buffer(xlx_file.encode("utf-8")))
    )

    logging.debug(
        "[easy-biologic] Initializing channels {} on device {}.".format(chs, idn.value)
    )
    err = await BL_LoadFirmware_async(
        idn,
        c.byref(active),
        c.byref(results),
        length,
        show_gauge,
        force_reload,
        bin_file,
        xlx_file,
    )

    validate(err)


async def is_channel_connected_async(idn, ch):
    idn = c.c_int32(idn)
    ch = c.c_uint8(ch)

    logging.debug(
        "[easy-biologic] Checking connection of channel {} on device {}.".format(
            ch.value, idn.value
        )
    )
    conn = await BL_IsChannelPlugged_async(idn, ch)

    return conn.value


async def get_channels_async(idn, size=16):
    """Returns the plugged state of channels.

    :param idn: The device id.
    :param size: The number of channels. [Default: 16]
    :return: A list of booleans indicating the plugged state of the channel.
    """
    idn = c.c_int32(idn)
    channels = (c.c_uint8 * size)()
    size = c.c_int32(size)

    logging.debug("[easy-biologic] Getting channels on device {}.".format(idn.value))
    err = await BL_GetChannelsPlugged_async(idn, c.byref(channels), size)

    validate(err)
    return [(ch == 1) for ch in channels]


async def channel_info_async(idn, ch):
    """Returns information on the specified channel.

    :param idn: The device id.
    :param ch: The channel.
    :returns: ChannelInfo structure.
    """
    idn = c.c_int32(idn)
    ch = c.c_uint8(ch)
    info = ChannelInfo()

    logging.debug(
        "[easy-biologic] Getting info of channel {} on device {}.".format(
            ch.value, idn.value
        )
    )
    err = await BL_GetChannelInfos_async(idn, ch, c.byref(info))

    validate(err)
    return info


async def get_hardware_configuration_async(idn, ch):
    """Returns the hardware configuratiion of the specified channel.

    :param idn: The device id.
    :param ch: The channel.
    :returns: HardwareConf structure.
    """
    idn = c.c_int32(idn)
    ch = c.c_uint8(ch)
    conf = HardwareConf()

    logging.debug(
        "[easy-biologic] Getting hardware configuration for channel {} on device {}.".format(
            ch.value, idn.value
        )
    )
    err = await BL_GetHardConf_async(idn, ch, c.byref(conf))

    validate(err)
    return conf


async def set_hardware_configuration_async(idn, ch, mode, connection):
    """Sets the hardware configuration.

    :param idn: The device id.
    :param ch: The channel.
    :param mode: ChannelMode to set the instrument connection mode.
    :param connection: ElectrodeConnection to set the electrode connection mode.
    """
    idn = c.c_int32(idn)
    ch = c.c_uint8(ch)

    # validate connection parameters
    if isinstance(mode, ChannelMode):
        mode = mode.value
    elif mode not in [0, 1]:
        raise ValueError("Invalid values for mode.")

    if isinstance(connection, ElectrodeConnection):
        connection = connection.value
    elif connection not in [0, 1]:
        raise ValueError("Invalid values for connection.")

    conf = HardwareConf(
        Conn=c.c_int32(connection),  # electrode connection
        Ground=c.c_int32(mode),  # channel mode / instrument ground
    )

    logging.debug(
        "[easy-biologic] Setting hardware configuration for channel {} on device {}.".format(
            ch.value, idn.value
        )
    )
    err = await BL_SetHardConf_async(idn, ch, conf)

    validate(err)


async def load_technique_async(
    idn, ch, technique, params, first=True, last=True, device=None, verbose=False
):
    """Loads a technique onto a specified device channel.

    :param idn: Device id.
    :param ch: Channel.
    :param technique: Name of the technique file.
    :param params: EccParams structure for the technique.
    :param first: True if the technique is loaded first. [Defualt: True]
    :param last: True if this is the last technique. [Default: True]
    :param device: Type of device. Used to modify technique.
        [Default: None]
    :param verbose: Echoes the sent parameters for debugging. [Default: False]
    """
    idn = c.c_int32(idn)
    ch = c.c_uint8(ch)

    technique_path = technique_file(technique, device)
    technique = c.create_string_buffer(technique_path.encode("utf-8"))

    first = c.c_bool(first)
    last = c.c_bool(last)
    verbose = c.c_bool(verbose)

    logging.debug(
        "[easy-biologic] Loading technique to channel {} on device {}.".format(
            ch.value, idn.value
        )
    )
    err = await BL_LoadTechnique_async(
        idn, ch, c.byref(technique), params, first, last, verbose
    )

    validate(err)


async def update_parameters_async(idn, ch, technique, params, index=0, device=None):
    """Updates the parameters of a technique.

    :param idn: Device identifier.
    :param ch: Channel number.
    :param technique: Name of the technique file.
    :param params: EccParams struct of new parameters.
    :param index: Index of the technique. [Default: 0]
    :param device: Type of device. Used to modify technique.
        [Default: None]
    """

    idn = c.c_int32(idn)
    ch = c.c_uint8(ch)

    technique = technique_file(technique, device)
    technique = c.create_string_buffer(technique.encode("utf-8"))
    index = c.c_int32(index)

    logging.debug(
        "[easy-biologic] Updating parameters on channel {} of device {}.".format(
            ch.value, idn.value
        )
    )
    err = await BL_UpdateParameters_async(idn, ch, index, params, c.byref(technique))

    validate(err)


async def start_channel_async(idn, ch):
    """Starts techniques loaded on a channel.

    :param idn: Device identifier.
    :param ch: Channel to start.
    """
    idn = c.c_int32(idn)
    ch = c.c_uint8(ch)

    logging.debug(
        "[easy-biologic] Starting channel {} on device {}.".format(ch.value, idn.value)
    )
    err = await BL_StartChannel_async(idn, ch)

    validate(err)


async def start_channels_async(idn, chs):
    """Starts techniques loaded on the given channels.

    :param idn: Device identifier.
    :param chs: List of channels to start.
    """
    num_chs = max(chs) + 1
    results = (c.c_int32 * num_chs)()
    active = create_active_array(chs, num_chs)
    idn = c.c_int32(idn)

    logging.debug(
        "[easy-biologic] Starting channels {} on device {}.".format(chs, idn.value)
    )
    err = await BL_StartChannel_async(idn, c.byref(active), c.byref(results), num_chs)

    validate(err)


async def stop_channel_async(idn, ch):
    """Stops techniques loaded on a channel.

    :param idn: Device identifier.
    :param ch: Channel to stop.
    """
    idn = c.c_int32(idn)
    ch = c.c_uint8(ch)

    logging.debug(
        "[easy-biologic] Stopping channel {} on device {}.".format(ch.value, idn.value)
    )
    err = await BL_StopChannel_async(idn, ch)

    validate(err)


async def stop_channels_async(idn, chs):
    """Stops techniques loaded on the given channels.

    :param idn: Device identifier.
    :param chs: List of channels to stop.
    """
    num_chs = max(chs) + 1
    results = (c.c_int32 * num_chs)()
    active = create_active_array(chs, num_chs)
    idn = c.c_int32(idn)

    logging.debug(
        "[easy-biologic] Stopping channels {} on device {}.".format(chs, idn.value)
    )
    err = await BL_StopChannel_async(idn, c.byref(active), c.byref(results), num_chs)

    validate(err)


async def get_values_async(idn, ch):
    """Gets the current data values on the given device channel.

    :param idn: Device identifier.
    :param ch: Channel.
    :returns: CurrentValues object.
    """
    idn = c.c_int32(idn)
    ch = c.c_uint8(ch)
    values = CurrentValues()

    logging.debug(
        "[easy-biologic] Getting values from channel {} on device {}.".format(
            ch.value, idn.value
        )
    )
    err = await BL_GetCurrentValues_async(idn, ch, c.byref(values))

    validate(err)
    return values


async def get_data_async(idn, ch):
    """Gets data from the given device channel.
    Pulls data from the buffer and clears it.

    :param idn: Device identifier.
    :param ch: Channel.
    :returns: A tuple of ( data, data_info, current_values ) where
        data_info is a DataInfo object representing the data's metadata,
        data is a data array, and
        current_values is a CurrentValues object.
    """
    idn = c.c_int32(idn)
    ch = c.c_uint8(ch)
    data = (c.c_uint32 * 1000)()
    info = DataInfo()
    values = CurrentValues()

    logging.debug(
        "[easy-biologic] Getting data from channel {} on device {}.".format(
            ch.value, idn.value
        )
    )
    err = await BL_GetData_async(idn, ch, c.byref(data), c.byref(info), c.byref(values))

    validate(err)
    return (data, info, values)


def validate(err):
    """Raises an exception based on the return value of the function

    :returns: True if function succeeded,
        or the error code if no known error is associated to it.
    :raise: RuntimeError for an unknown error.
    :raise: TypeError for an invalid parameter.
    """
    if err == 0:
        # no error
        return True
    else:
        raise EcError(err)


def create_active_array(active, size=None, kind=c.c_uint8):
    """Creates an array of active elements from a list.

    :param active: List of active elements.
    :param size: Size of the array. If None the maximum active index is used.
        [Default: None]
    :param kind: Kind of array elements. [Default: ctypes.c_uint8]
    :returns: An array of elements where active elements are 1, and inactive are 0.
    """
    if size is None:
        size = max(active) + 1

    arr = (kind * size)()
    for index in active:
        # activate index
        arr[index] = 1

    return arr


def technique_file(technique, device=None):
    """Returns the file name of teh given technique for the given device.

    :param technique: Technique name.
    :param device: Kind of device. [Default: None]
    :returns: Technique file.
    """
    file_type = ".ecc"
    sp300_mod = "4"

    if (
        device is not None
        and is_in_SP300_family(device)
        and not technique.endswith(sp300_mod)
    ):
        # modify technqiues for SP-300 devices
        technique += sp300_mod

    if not technique.endswith(file_type):
        # append file type extenstion if needed
        technique += file_type

    return technique.lower()


def is_in_SP300_family(device_code):
    """
    :param device_code: DeviceCode.
    :returns: Whether the device is in the SP300 (VMP_300) family or not.
    """
    return device_code in SP300_DEVICE_FAMILY
