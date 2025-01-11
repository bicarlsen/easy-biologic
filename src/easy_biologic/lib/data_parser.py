import math
from collections import namedtuple

from . import ec_lib as ecl


def parse(data, info, fields=None, device=None):
    """
    Parses data retrieved from a technique.

    :param data: Data to parse.
    :param info: DataInfo object representing metadata of the technqiue.
    :param fields: List of FieldInfo used to interpret the data.
        If None, uses the technique ID to retrieve.
    :param device: BioLogic device. Necessary if fields are not defined.
    :returns: A list of namedtuples representing the data.
    """
    if (fields is None) and (device is None):
        raise ValueError(
            "Both fields and device are None, at least one must be defined."
        )

    rows = info.NbRows
    cols = info.NbCols
    technique = ecl.TechniqueId(info.TechniqueID)

    if fields is None:
        # get fields from device
        fields = (
            SP300_Fields[technique]
            if ecl.is_in_SP300_family(device.kind)
            else VMP3_Fields[technique]
        )

    if isinstance(fields, tuple):
        fields = fields[info.ProcessIndex]

    if cols == 0:
        raise RuntimeError("No columns in data.")

    # technique info
    field_names = [field.name for field in fields]
    Datum = namedtuple("Datum", field_names)

    # convert singles
    data = [
        (
            ecl.convert_numeric(datum)
            if (fields[index % cols].type is ecl.ParameterType.SINGLE)
            else datum
        )
        for index, datum in enumerate(data)
    ]

    # group data
    parsed = [Datum(*data[i : i + cols]) for i in range(0, rows * cols, cols)]

    return parsed


def calculate_time(t_high, t_low, data_info, current_value):
    """
    Calculates time from the t_high and t_low fields.

    :param t_high: t_high.
    :param t_low: t_low.
    :param data_info: DataInfo object of the technique.
    :param current_values: CurrentValues object of the technique.
    :returns: Time
    """
    start = data_info.StartTime
    if math.isnan(start):
        # start is not a number, assume 0
        start = 0

    elapsed = current_value.TimeBase * ((t_high << 32) + t_low)
    return start + elapsed


# For holding field info.
FieldInfo = namedtuple("FieldInfo", ["name", "type"])


class VMP3_Fields:
    """
    Holds technique field definitions.
    """

    # for convenience
    TID = ecl.TechniqueId
    INT32 = ecl.ParameterType.INT32
    BOOL = ecl.ParameterType.BOOLEAN
    SINGLE = ecl.ParameterType.SINGLE
    FI = FieldInfo

    OCV = [
        FI("t_high", INT32),
        FI("t_low", INT32),
        FI("voltage", SINGLE),
        FI("control", SINGLE),
    ]

    CP = [
        FI("t_high", INT32),
        FI("t_low", INT32),
        FI("voltage", SINGLE),
        FI("current", SINGLE),
        FI("cycle", INT32),
    ]

    CA = CP
    CPLIMIT = CP
    CALIMIT = CP

    CV = [
        FI("t_high", INT32),
        FI("t_low", INT32),
        FI("control", SINGLE),
        FI("current", SINGLE),
        FI("voltage", SINGLE),
        FI("cycle", INT32),
    ]

    PEIS = (
        [  # process == 0
            FI("t_high", INT32),
            FI("t_low", INT32),
            FI("voltage", SINGLE),
            FI("current", SINGLE),
        ],
        [  # process == 1
            FI("frequency", SINGLE),
            FI("abs_voltage", SINGLE),
            FI("abs_current", SINGLE),
            FI("impedance_phase", SINGLE),
            FI("voltage", SINGLE),
            FI("current", SINGLE),
            FI("empty1", INT32),
            FI("abs_voltage_ce", SINGLE),
            FI("abs_current_ce", SINGLE),
            FI("impedance_ce_phase", SINGLE),
            FI("voltage_ce", SINGLE),
            FI("empty2", INT32),
            FI("empty3", INT32),
            FI("time", SINGLE),
            FI("current_range", SINGLE),
        ],
    )

    GEIS = (
        [  # process == 0
            FI("t_high", INT32),
            FI("t_low", INT32),
            FI("voltage", SINGLE),
            FI("current", SINGLE),
        ],
        [  # process == 1
            FI("frequency", SINGLE),
            FI("abs_voltage", SINGLE),
            FI("abs_current", SINGLE),
            FI("impedance_phase", SINGLE),
            FI("voltage", SINGLE),
            FI("current", SINGLE),
            FI("empty1", INT32),
            FI("abs_voltage_ce", SINGLE),
            FI("abs_current_ce", SINGLE),
            FI("impedance_ce_phase", SINGLE),
            FI("voltage_ce", SINGLE),
            FI("empty2", INT32),
            FI("empty3", INT32),
            FI("time", SINGLE),
            FI("current_range", SINGLE),
        ],
    )


class SP300_Fields:
    """
    Holds technique field definitions.
    """

    # for convenience
    TID = ecl.TechniqueId
    INT32 = ecl.ParameterType.INT32
    BOOL = ecl.ParameterType.BOOLEAN
    SINGLE = ecl.ParameterType.SINGLE
    FI = FieldInfo

    OCV = [FI("t_high", INT32), FI("t_low", INT32), FI("voltage", SINGLE)]

    CP = [
        FI("t_high", INT32),
        FI("t_low", INT32),
        FI("voltage", SINGLE),
        FI("current", SINGLE),
        FI("cycle", INT32),
    ]

    CA = CP
    CPLIMIT = CP
    CALIMIT = CP

    CV = [
        FI("t_high", INT32),
        FI("t_low", INT32),
        FI("current", SINGLE),
        FI("voltage", SINGLE),
        FI("cycle", INT32),
    ]

    PEIS = (
        [  # process == 0
            FI("t_high", INT32),
            FI("t_low", INT32),
            FI("voltage", SINGLE),
            FI("current", SINGLE),
        ],
        [  # process == 1
            FI("frequency", SINGLE),
            FI("abs_voltage", SINGLE),
            FI("abs_current", SINGLE),
            FI("impedance_phase", SINGLE),
            FI("voltage", SINGLE),
            FI("current", SINGLE),
            FI("empty1", INT32),
            FI("abs_voltage_ce", SINGLE),
            FI("abs_current_ce", SINGLE),
            FI("impedance_ce_phase", SINGLE),
            FI("voltage_ce", SINGLE),
            FI("empty2", INT32),
            FI("empty3", INT32),
            FI("time", SINGLE),
        ],
    )

    GEIS = (
        [  # process == 0
            FI("t_high", INT32),
            FI("t_low", INT32),
            FI("voltage", SINGLE),
            FI("current", SINGLE),
        ],
        [  # process == 1
            FI("frequency", SINGLE),
            FI("abs_voltage", SINGLE),
            FI("abs_current", SINGLE),
            FI("impedance_phase", SINGLE),
            FI("voltage", SINGLE),
            FI("current", SINGLE),
            FI("empty1", INT32),
            FI("abs_voltage_ce", SINGLE),
            FI("abs_current_ce", SINGLE),
            FI("impedance_ce_phase", SINGLE),
            FI("voltage_ce", SINGLE),
            FI("empty2", INT32),
            FI("empty3", INT32),
            FI("time", SINGLE),
        ],
    )
