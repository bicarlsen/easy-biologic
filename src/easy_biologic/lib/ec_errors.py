class EcError(Exception):
    """
    Represents an EC Error.
    """

    errors = {
        # errors with value as key and ( code, message ) as value.
        -1: ("ERR_GEN_NOTCONNECTED", "No instrument connected."),
        -2: ("ERR_GEN_CONNECTIONINPROGRESS", "Connection in progress."),
        -3: ("ERR_GEN_CHANNELNOTPLUGGED", "Selected channel(s) unplugged."),
        -4: ("ERR_GEN_INVALIDPARAMETERS", "Invalid function parameters."),
        -5: ("ERR_GEN_FILENOTEXISTS", "Selected file does not exist."),
        -6: ("ERR_GEN_FUNCTIONFAILED", "Function failed."),
        -7: ("ERR_GEN_NOCHANNELSELECTED", "No channel selected"),
        -8: ("ERR_GEN_INVALIDCONF", "invalid instrument configuration"),
        -9: ("ERR_GEN_ECLAB_LOADED", "ECLab firmware laoded on instrument."),
        -10: (
            "ERR_GEN_LIBNOTCORRECTLYLOADED",
            "Library not correctly loaded in memory.",
        ),
        -11: ("ERR_GEN_USBLIBRARYERROR", "USB library not loaded in memory."),
        -12: (
            "ERR_GEN_FUNCTIONINPROGRESS",
            "Function of the library already in progress.",
        ),
        -13: ("ERR_GEN_CHANNEL_RUNNING", "Selected channel(s) already used."),
        -14: ("ERR_GEN_DEVICE_NOTALLOWED", "Device not allowed."),
        -15: ("ERR_GEN_UPDATEPARAMETERS", "Invalid update function parameters."),
        -101: ("ERR_INSTR_VMEERROR", "Internal instrument communication failed."),
        -102: (
            "ERR_INSTR_TOOMANYDATA",
            "Too many data to transfer from the instrument (device error)",
        ),
        -103: (
            "ERR_INSTR_RESPNOTPOSSIBLE",
            "Selected channel(s) unplugged (device error).",
        ),
        -104: ("ERR_INSTR_RESPERROR", "Instrument response error."),
        -105: ("ERR_INSTR_MSGSIZEERROR", "Invalid message size."),
        -200: ("ERR_COMM_COMMFAILED", "Communication with the instrument failed."),
        -201: (
            "ERR_COMM_CONNECTIONFAILED",
            "Could not establish communication with instrument.",
        ),
        -202: ("ERR_COMM_WAITINGACK", "Waiting for the instrument response."),
        -203: ("ERR_COMM_INVALIDIPADDRESS", "Invalid IP address."),
        -204: ("ERR_COMM_ALLOCMEMFAILED", "Cannot allocate memory in the instrument."),
        -205: (
            "ERR_COMM_LOADFIRMWAREFAILED",
            "Cannot load firmware on the selected channel(s).",
        ),
        -206: (
            "ERR_COMM_INCOMPATIBLESERVER",
            "Communication firmware not compatible with the library.",
        ),
        -207: (
            "ERR_COMM_MAXCONNREACHED",
            "Maximum number of allowed connections reached.",
        ),
        -308: ("ERR_FIRM_FIRMWARENOTLOADED", "No firmware loaded on channel."),
        -309: (
            "ERR_FIRM_FIRMWAREINCOMPATIBLE",
            "Loaded firmware not compatible with the library.",
        ),
        -400: ("ERR_TECH_ECCFILENOTEXISTS", "ECC file does not exist."),
        -401: (
            "ERR_TECH_INCOMPATIBLEECC",
            "Ecc file not compatible with the channel firmware.",
        ),
        -402: ("ERR_TECH_ECCFILECORRUPTED", "ECC file corrupted."),
        -403: ("ERR_TECH_LOADTECHNIQUEFAILED", "Cannot load the ECC file."),
        -404: (
            "ERR_TECH_DATACORRUPTED",
            "Data returned by the instrument are corrupted..",
        ),
        -405: ("ERR_TECH_MEMFULL", "Cannot load techniques: full memory."),
    }

    def __init__(self, value=None, code=None, message=None):
        """
        Creates an EcError.
        If value is passed code and message are automatically filled if found,
        but overridden if also passed.

        :param value: The value of the error. [Default: None]
        :param code: The error code. [Default: None]
        :param message: The error message.
        :returns: EcError
        """
        if value is not None:
            try:
                (code, message) = EcError.errors[value]

            except KeyError as err:
                raise ValueError(f"Unknown error value {value}.")

            out = f"{code} ({value}): {message}"

        else:
            # no error value
            out = ""

        super(EcError, self).__init__(out)
