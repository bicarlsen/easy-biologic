from enum import Enum


class OCV(Enum):
    Rest_time_T = float
    Record_every_dE = float
    Record_every_dT = float


class CV(Enum):
    vs_initial = bool
    Voltage_step = float
    Scan_Rate = float
    Scan_number = int
    Record_every_dE = float
    Average_over_dE = bool
    N_Cycles = int
    Begin_measuring_I = float
    End_measuring_I = float


class CA(Enum):
    Voltage_step = float
    vs_initial = bool
    Duration_step = float
    Step_number = int
    Record_every_dT = float
    Record_every_dI = float
    N_Cycles = int


class CP(Enum):
    Current_step = float
    vs_initial = bool
    Duration_step = float
    Step_number = int
    Record_every_dT = float
    Record_every_dE = float
    N_Cycles = int


class CALIMIT(Enum):
    Voltage_step = float
    vs_initial = bool
    Duration_step = float
    Step_nuber = int
    Record_every_dT = float
    Record_every_dI = float
    Test1_Config = int
    Test1_Value = float
    Test2_Config = int
    Test2_Value = float
    Test3_Config = int
    Test3_Value = float
    Exit_Cond = int
    N_Cycles = int


class CPLIMIT(Enum):
    Current_step = float
    vs_initial = bool
    Duration_step = float
    Step_nuber = int
    Record_every_dT = float
    Record_every_dE = float
    Test1_Config = int
    Test1_Value = float
    Test2_Config = int
    Test2_Value = float
    Test3_Config = int
    Test3_Value = float
    Exit_Cond = int
    N_Cycles = int


class PEIS(Enum):
    vs_initial = bool
    vs_final = bool
    Initial_Voltage_step = float
    Final_Voltage_step = float
    Duration_step = float
    Step_number = int
    Record_every_dT = float
    Record_every_dI = float
    Final_frequency = float
    Initial_frequency = float
    sweep = bool
    Amplitude_Voltage = float
    Frequency_number = int
    Average_N_times = int
    Correction = bool
    Wait_for_steady = float


class GEIS(Enum):
    vs_initial = bool
    vs_final = bool
    Initial_Current_step = float
    Final_Current_step = float
    Duration_step = float
    Step_number = int
    Record_every_dT = float
    Record_every_dV = float
    Final_frequency = float
    Initial_frequency = float
    sweep = bool
    Amplitude_Current = float
    Frequency_number = int
    Average_N_times = int
    Correction = bool
    Wait_for_steady = float
    I_Range = int
