# Easy Biologic
A library allowing easy control over BioLogic devices.
High and low level control over Biologic devices are available. 
Low level control is included in the `lib` subpackage, while high level control
is available in the main module. 
> Install with `python -m pip install easy-biologic`

## High Level API
There are two high level API modules containing three classes, and two convenience modules.

### Biologic Device
Represents an instance of a Biologic Device.

#### Methods
+ **BiologicDevice( address, timeout = 5 ):** Creates a new Biologic Device representing the device conencted at `address`.

+ **connect( bin_file, xlx_file ):** Connects to the device, loading the bin and xlx file if provided.

+ **disconnect():** Disconnects from the device.

+ **is_connected():** Whether the device is connected or not.

+ **load_technique( ch, technique, params, index = 0, last = True, types = none ):** Loads a technique onto the given device channel.

+ **load_techniques( ch, techniques, parameters, types = None ):** Loads a series of techniques onto the given device channel.

+ **update_parameters( ch, technique, parameters, index = 0, types = None ):** Update the parameters of the given technqiue on the specified device channel.

+ **start_channel( ch ):** Starts the given channel.

+ **start_channels( chs = None ):** Starts multiple channels.

+ **stop_channel( ch ):** Stops the given channel.

+ **stop_channels( chs = None ):** Stops the given channels.

+ **channel_info( ch ):** Returns information about the given channel.

+ **channel_configuration( ch ):** Returns configuration information of the channel.

+ **set_channel_configuration( ch, mode, conneciton ):** Sets the channel's hardware configuration.

+ **get_values( ch ):** Returns current values of the given channel.

+ **get_data( ch ):** Returns buffered data of the given channel.


#### Properties
+ **address:** Connection address of the device.
+ **idn:** ID of the device.
+ **kind:** Device model.
+ **info:** DeviceInfo structure.
+ **plugged:** List of available channels. 
+ **channels:** List of ChannelInfo structures.
+ **hardware_configuration:** Dictionary of HardwareConfiguration for each channel.
+ **techniques:** List of TechParams loaded on each channel.

### Biologic Program
`Abstract Class`
Represents a program to be run on a device.

#### Methods
+ **BiologicProgram( device, params, channels = None, autoconnect = True, barrier = None, stop_event = None, threaded = False ):** Creates a new program.

+ **channel_state( channels = None ):** Returns the state of the channels.

+ **on_data( callback, index = None ):** Registers a callback function to run when data is collected.

+ **run():** Runs the program.

+ **stop():** Sets the stop event flag.

+ **save_data( file, append = False, by_channel = False ):** Saves data to the given file.

+ **sync():** Waits for barrier, if set.

+ **_connect():** Connects to the device

#### Properties
+ **device:** BiologicDevice. <br>
+ **params:** Passed in parameters. <br>
+ **channels:** Device channels. <br>
+ **autoconnect:** Whether connection to the device should be automatic or + not. <br>
+ **barrier:** A threading.Barrier to use for channel syncronization. [See ProgramRummer] <br>
+ **field_titles:** Column names for saving data. <br>
+ **data:** Data collected during the program. <br>
+ **status:** Status of the program. <br>
+ **fields:** Data fields teh program returns. <br>
+ **technqiues:** List of techniques the program uses.

### Program Runner
Represents a program to be run on a device channel.

#### Methods
+ **ProgramRunner( programs, sync = False ):** Creates a new program runner.

+ **start():** Runs the programs.

+ **wait():** Wait for all threads to finish.

+ **stop():** Sets stop event.

#### Properties
+ **threads:** List of threads for each program. <br>
+ **sync:** Whether to sync the threads or not. 

### Base Programs
Contains basic implementations of BiologicPrograms.

#### OCV
##### Params
+ **time:** Run time in seconds.

+ **time_interval:** Maximum time between readings. 
[Default: 1]

+ **voltage_interval:** Maximum interval between voltage readings.
[Default: 0.01]
    
#### CA
##### Params
+ **voltages:** List of voltages.

+ **durations:** List of times in seconds.

+ **vs_initial:** If step is vs. initial or previous. 
[Default: False] 

+ **time_interval:** Maximum time interval between points.
[Default: 1]
    
+ **current_interval:** Maximum current change between points.
[Default: 0.001]
            
+ **current_range:** Current range. Use ec_lib.IRange.
[Default: IRange.m10 ]
            
##### Methods
+ **update_voltage( voltages, durations = None, vs_initial = None ):** Updates the voltage. 

#### CALimit
##### Params
+ **voltages:** List of voltages.

+ **durations:** List of times in seconds.

+ **vs_initial:** If step is vs. initial or previous. 
[Default: False] 

+ **time_interval:** Maximum time interval between points.
[Default: 1]
+ **current_interval:** Maximum current change between points.
[Default: 0.001]
            
+ **current_range:** Current range. Use ec_lib.IRange.
[Default: IRange.m10 ]

##### Methods
+ **update_voltage( voltages, durations = None, vs_initial = None ):** Updates the voltage.

#### PEIS
##### Params
+ **voltage:** Initial potential in Volts.

+ **amplitude_voltage:** Sinus amplitude in Volts.

+ **initial_frequency**: Initial frequency in Hertz.
       
+ **final_frequency:** Final frequency in Hertz.

+ **frequency_number:** Number of frequencies.

+ **duration:** Overall duration in seconds.

+ **vs_initial:** If step is vs. initial or previous. 
[Default: False]

+ **time_interval:** Maximum time interval between points in seconds. 
[Default: 1]

+ **current_interval:** Maximum time interval between points in Amps. 
[Default: 0.001]

+ **sweep:** Defines whether the spacing between frequencies is logarithmic ('log') or linear ('lin'). 
[Default: 'log'] 

+ **repeat:** Number of times to repeat the measurement and average the values for each frequency. 
[Default: 1]

+ **correction:** Drift correction. 
[Default: False]

+ **wait:** Adds a delay before the measurement at each frequency. The delay is expressed as a fraction of the period. 
[Default: 0]
    
#### JV_Scan
Performs a JV scan.

##### Params
+ **start:** Start voltage. 
[Default: 0]

+ **end:** End voltage.

+ **step:** Voltage step. 
[Default: 0.01]

+ **rate:** Scan rate in V/s. 
[Default: 0.01]

+ **average:** Average over points. 
[Default: False]
 

#### MPP_Tracking
Performs MPP tracking.

##### Params
+ **run_time:** Run time in seconds.

+ **init_vmpp:** Initial v_mpp.

+ **probe_step:** Voltage step for probe. 
[Default: 0.01 V]

+ **probe_points:** Number of data points to collect for probe. 
[Default: 5]

+ **probe_interval:** How often to probe in seconds. 
[Default: 2]

+ **record_interval:** How often to record a data point in seconds. 
[Default: 1]


#### MPP
Runs MPP tracking, finding the initial Vmpp by first measuring Voc, then performing a JV scan from 0 to Voc.

##### Params
+ **run_time:** Run time in seconds.

+ **probe_step:** Voltage step for probe. 
[Default: 0.01 V]

+ **probe_points:** Number of data points to collect for probe. 
[Default: 5]

+ **probe_interval:** How often to probe in seconds. 
[Default: 2]

+ **record_interval:** How often to record a data point in seconds. 
[Default: 1]


#### MPP Cycles
Runs multiple MPP cycles, performing Voc and JV scans at the beginning of each.

##### Params
+ **run_time:** Run time in seconds

+ **scan_interval:** How often to perform a JV scan.

+ **probe_step:** Voltage step for probe. [Default: 0.01 V]

+ **probe_points:** Number of data points to collect for probe. [Default: 5]

+ **probe_interval:** How often to probe in seconds. [Default: 2]

+ **record_interval:** How often to record a data point in seconds. [Default: 1]

### Find Devices
A convenience script for finding connected devices.

#### Use
From a terminal run `python -m easy_biologic.find_devices`.

## Low Level API
The low level API gives direct control of the Biologic device using the provided DLL libraries. The subpackage contains five modules.

### EC Lib
Contains methods converting the `BL_*` DLL functions for use, enumeration classes to encapsulate program and device states, and C Structures for sending and receiving data from th device.

#### Methods
+ **connect( address, timeout = 5 ):** Connects to the device at the given address.

+ **disconnect( idn ):** Disconnects given device.

+ **is_connected( address ):** Checks if the device at the given address is connected.

+ **is_channel_connected( idn, ch ):** Checks whether the given device channel is connected.

+ **get_channels( idn, length = 16 ):** Returns a list of booleans of whether the cahnnel at the index exists.

+ **channel_info( idn, ch ):** Returns a ChannelInfo struct of the given device channel.

+ **get_hardware_configuration( idn, ch ):** Returns a HarwareConf struct of the given device channel.

+ **set_hardware_configuration( idn, ch, mode, connection ):** Sets the hardware configuration of the given device channel.

+ **load_technique( idn, ch, technique, params, first = True, last = True, verbose = False ):** 
Loads the technique with parameter on the given device channel.

+ **create_parameter( name, value, index, kind = None ):** 
Creates an EccParam struct.

+ **update_paramters( idn, ch, technique, params, tech_index = 0 ):** 
Updates the paramters of a technique on teh given device channel.

+ **cast_parameters( parameters, types ):** Cast parameters to given types.

+ **start_channel( idn, ch ):** Starts the given device channel.

+ **start_channels( idn, ch ):** Starts the given device channels.

+ **stop_channel( idn, ch ):** Stops the given device channel.

+ **stop_channels( idn, chs ):** Stops the given device channels.

+ **get_values( idn, ch ):** Gets the current values and states of the given device channel.

+ **raise_exception( err ):** Raises an exception based on a calls error code.

+ **is\_in\_SP300\_family( device_code ):** Determines if the given device is in the SP300 device family.

#### Enum Classes
+ **DeviceCodes:** Device code for identifying model.<br>
Values: [ KBIO_DEV_VMP, KBIO_DEV_VMP2, KBIO_DEV_MPG, KBIO_DEV_BISTAT, KBIO_DEV_MCS_200, KBIO_DEV_VMP3, KBIO_DEV_VSP, KBIO_DEV_HCP803, KBIO_DEV_EPP400, KBIO_DEV_EPP4000, KBIO_DEV_BISTAT2, KBIO_DEV_FCT150S, KBIO_DEV_VMP300, KBIO_DEV_SP50, KBIO_DEV_SP150, KBIO_DEV_FCT50S, KBIO_DEV_SP300, KBIO_DEV_CLB500, KBIO_DEV_HCP1005, KBIO_DEV_CLB2000, KBIO_DEV_VSP300, KBIO_DEV_SP200, KBIO_DEV_MPG2, KBIO_DEV_ND1, KBIO_DEV_ND2, KBIO_DEV_ND3, KBIO_DEV_ND4, KBIO_DEV_SP240, KBIO_DEV_MPG205, KBIO_DEV_MPG210, KBIO_DEV_MPG220, KBIO_DEV_MPG240, KBIO_DEV_UNKNOWN ]

+ **DeviceCodeDescriptions:** Description of DeviceCodes. <br>
Values: [ KBIO_DEV_VMP, KBIO_DEV_VMP2, KBIO_DEV_MPG, KBIO_DEV_BISTAT, KBIO_DEV_MCS_200, KBIO_DEV_VMP3, KBIO_DEV_VSP, KBIO_DEV_HCP803, KBIO_DEV_EPP400, KBIO_DEV_EPP4000, KBIO_DEV_BISTAT2, KBIO_DEV_FCT150S, KBIO_DEV_VMP300, KBIO_DEV_SP50, KBIO_DEV_SP150, KBIO_DEV_FCT50S, KBIO_DEV_SP300, KBIO_DEV_CLB500, KBIO_DEV_HCP1005, KBIO_DEV_CLB2000, KBIO_DEV_VSP300, KBIO_DEV_SP200, KBIO_DEV_MPG2, KBIO_DEV_ND1, KBIO_DEV_ND2, KBIO_DEV_ND3, KBIO_DEV_ND4, KBIO_DEV_SP240, KBIO_DEV_MPG205, KBIO_DEV_MPG210, KBIO_DEV_MPG220, KBIO_DEV_MPG240, KBIO_DEV_UNKNOWN ]

+ **IRange:** Current ranges. <br>
Values: [ p100, n1, n10, n100, u1, u10, u100, m1, m10, m100, a1, KEEP, BOOSTER, AUTO ]

+ **ERange:** Voltage ranges. <br>
Values: [ v2_5, v5, v10, AUTO ]

+ **ElectrodeConnection:** Whether the electrode is in standard or grounded mode.<br>
Values: [ STANDARD, GROUNDED ]

+ **ChannelMode:** Whether the device is floating or grounded. <br>
Values: [ GROUNDED, FLOATING ]

+ **TechniqueId:** ID of the technique. (Not fully implemented.) <br>
Values: [ NONE, OCV, CA, CP, CV, PEIS, CALIMIT ]

+ **ChannelState:** State of the channel. <br>
Values: [ STOP, RUN, PAUSE ]

+ **ParameterType:** Type of a parameter. <br>
Values: [ INT32, BOOLEAN, SINGLE, FLOAT ]
(FLOAT is an alias of SINGLE.)

#### Structures
+ **DeviceInfo:** Information representing the device. Used by `connect()`. <br>
Fields: [ DeviceCode, RAMSize, CPU, NumberOfChannles, NumberOfSlots, FirmwareVersion, FirmwareDate_yyyy, FirmwareDate_mm, FirmwareDate_dd, HTdisplayOn, NbOfConnectedPC ]

+ **ChannelInfo:** Information representing a device channel. Used by `channel_info()`. <br>
Fields: [ Channel, BoardVersion, BoardSerialNumber, FirmwareVersion, XilinxVersion, AmpCode, NbAmps, Lcboard, Zboard, RESERVED, MemSize, State, MaxIRange, MinIRange, MaxBandwidth, NbOfTechniques ]

+ **HardwareConf:** Hardware configuration information for a channel.<br>
Fields: [ Conn, Ground ]

+ **EccParam:** A technique parameter. <br>
Fields: [ ParamStr, ParamType, ParamVal, ParamIndex ]

+ **EccParams:** A bundle of technique parameters. <br>
Fields: [ len, pParams ]

+ **CurrentValues:** Values measured from and states of the device. <br>
Fields: [ State, MemFilled, TimeBase, Ewe, EweRangeMin, EweRangeMax, Ece, EceRangeMin, EceRangeMax, Eoverflow, I, IRange, Ioverflow, ElapsedTime, Freq, Rcomp, Saturation, OptErr, OptPos ]

+ **DataInfo:** Metadata of measured data. <br>
Fields: [ IRQskipped, NbRows, NbCols, TechniqueIndex, TechniqueID, processIndex, loop, StartTime, MuxPad ]

#### Constants
+ **VMP3_DEVICE_FAMILY:** Set of DeviceCodes in the VMP3 device family.<br>
{ DeviceCodes.KBIO_DEV_VMP2, DeviceCodes.KBIO_DEV_VMP3, DeviceCodes.KBIO_DEV_BISTAT, DeviceCodes.KBIO_DEV_BISTAT2, DeviceCodes.KBIO_DEV_MCS_200, DeviceCodes.KBIO_DEV_VSP, DeviceCodes.KBIO_DEV_SP50, DeviceCodes.KBIO_DEV_SP150, DeviceCodes.KBIO_DEV_FCT50S, DeviceCodes.KBIO_DEV_FCT150S, DeviceCodes.KBIO_DEV_CLB500, DeviceCodes.KBIO_DEV_CLB2000, DeviceCodes.KBIO_DEV_HCP803, DeviceCodes.KBIO_DEV_HCP1005, DeviceCodes.KBIO_DEV_MPG2, DeviceCodes.KBIO_DEV_MPG205, DeviceCodes.KBIO_DEV_MPG210, DeviceCodes.KBIO_DEV_MPG220, DeviceCodes.KBIO_DEV_MPG240 }

+ **SP300_DEVICE_FAMILY:** Set of DeviceCodes in the SP300 device family.<br>
{ DeviceCodes.KBIO_DEV_SP200, DeviceCodes.KBIO_DEV_SP300, DeviceCodes.KBIO_DEV_VSP300, DeviceCodes.KBIO_DEV_VMP300, DeviceCodes.KBIO_DEV_SP240 }

### Data Parser
Parses data received from a technique and contains technique fields for different device types.

#### Methods
+ **parse( data, info, fields = None, device = None ):** Parses data received from a technique.

+ **calculate_time( t_high, t_low, data_info, current_value ):** Calculates elapsed time from time data.

#### Classes
+ **VMP3_Fields:** Contains technqiue fields for VMP3 devices. 
(Not all techniques are implemented)
Properties: [ OCV, CP, CA, CPLIMIT, CALIMIT, CV, PEIS ]

+ **SP300_Fields:** Contains technqiue fields for SP-300 devices. 
(Not all techniques are implemented)
Properties: [ OCV, CP, CA, CPLIMIT, CALIMIT, CV, PEIS ]

### EC Find
Implements the BL Find DLL.

#### Methods
All BL Find DLL functions are implemented under the same name.

+ **find_devices( connection = None ):** Finds conencted devices.

### Technique Fields
Parameter types for techniques. (Not all techniques are implemented.)

#### Classes
+ OCV
+ CV
+ CA
+ CALIMIT

### EC Errors
Implements EC errors.

#### Classes
+ **EcError( value = None, code = None, message = None )** 

## Example

A basic example running an MPP program on channels 0 - 7 for 10 minutes.
```python
import easy_biologic as ebl
import easy_biologic.base_programs as blp


# create device
bl = ebl.BiologicDevice( '192.168.1.2' )

# create mpp program
params = {
	'run_time': 10* 60		
}

mpp = blp.MPP(
    bl,
    params, 	
    channels = [ 0, 1, 2, 3, 4, 5, 6 ]        
)

# run program
mpp.run( 'data' )
```
