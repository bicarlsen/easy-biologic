# Easy Biologic
Allows easy control over [BioLogic](https://www.biologic.net) devices.
High and low level control over BioLogic devices are available. 
Low level control is in the `lib` subpackage, while high level control
is in the main module.
> Install with `python -m pip install easy-biologic`

## API
> For a full overview of both APIs see [`API.md`](./API.md).

### High Level
High level control of devices and programs. Most users will use these.

+ **Biologic Device:** Represents a BioLogic Device.
+ **Biologic Program:** Represents a program to be run on a device.
+ **Program Runner**: Represents a program to be run on a device channel.
+ **Base Programs**: Basic implementations of `BiologicProgram`s.
+ **Find Devices**: A convenience script for finding connected devices.

### Low Level
Gives direct control of the Biologic device using DLL libraries. Used to implement new techniques.

+ **EC Lib:** Contains methods converting the `BL_*` DLL functions for use, enumeration classes to encapsulate program and device states, and C Structures for sending and receiving data from th device.
+ **Data Parser:** Parses data received from a technique and contains technique fields for different device types.
+ **EC Find:** Implements the BL Find DLL.
+ **Technique Fields:** Parameter types for techniques. (Not all techniques are implemented.)
+ **EC Errors:** Implements EC errors.

## Examples

### Basic
Runs an MPP program on channels 0 - 7 for 10 minutes.

```python
import easy_biologic as ebl
import easy_biologic.base_programs as blp

# create device
bl = ebl.BiologicDevice('192.168.1.2')

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
mpp.run('data')
```

### Custom parameters
Runs a CV scan for three cycles at a scan rate of 50 mV/s on channel 0. The experiment begins at 0.5 V and forward scans to -0.25 V, then scans backward to 0.8 V. In the final cycle, it scans to 1.0 V.

```python
import easy_biologic as ebl
import easy_biologic.base_programs as blp        

bl = ebl.BiologicDevice('192.168.1.2')
save_path = '/path/to/data/CV.csv'
params = {
    'start': 0.5,
    'end': -0.25,
    'E2': 0.8,
    'Ef': 1.0,
    'rate': 0.05,  
    'step': 0.001,    
    'N_Cycles': 2,
    'begin_measuring_I': 0.5,
    'End_measuring_I': 1.0,
}  

CV = blp.CV(
    bl,
    params,     
    channels = [0]
)     

CV.run('data')
CV.save_data(save_path)
```

### Advanced
Runs an OCV then uses the final OCV voltage for PEIS.

```python
import easy_biologic as ebl
import easy_biologic.base_programs as blp        

bl = ebl.BiologicDevice('192.168.1.2')
save_path_ocv = '/path/to/data/OCV.csv'

# Run OCV
params_ocv = {
    'time': 2,
    'time_interval': 1,
}

ocv = blp.OCV(
    bl,
    params_ocv,
    channels=[0]
)

ocv.run('data')
ocv.save_data(save_path_ocv)

voc = {
    ch: [datum.voltage for datum in data]
    for ch, data in ocv.data.items()
}

voc = {
    ch: sum(ch_voc) / len(ch_voc)
    for ch, ch_voc in voc.items()
}

# Run PEIS
save_path_peis = '/path/to/data/PEIS.csv'
params_peis = {
    'voltage': list(voc.values())[0],
    'final_frequency': 1000,
    'initial_frequency': 1000000,
    'amplitude_voltage': 0.1,
    'frequency_number': 60,
    'duration': 0,
    'repeat': 10,
    'wait': 0.1
}

peis = blp.PEIS(
    bl,
    params_peis,
    channels=[0]
)

peis.run('data')
peis.save_data(save_path_peis)
```

## Extras
+ `pandas`: Use [`pandas`](https://pandas.pydata.org/) to save data.

## Known issues
+ **USB connection:** Often times using a USB connection will give a `ERR_COMM_CONNECTIONFAILED (-201)` error. We have found that USB can be unreliable, and a TCP connection is resolves this issue.

## Adding techniques
BioLogic will often update their firmware which needs to be included in this package. To do so
0. Download this package. The easiest way to do this is `git clone https://github.com/bicarlsen/easy-biologic.git`.
1. Download the [EC-Lab Developer Package](https://www.biologic.net/softwares/ec-lab-oem-development-package/), noting its install path (typically `C:\EC-Lab Development Package`).
2. Copy the `EC-Lab Development Package\lib` folder (typically `C:\EC-Lab Development Package\lib`) into the folder `easy-biologic/src/techniques` folder and rename it with the major and minor version of the firmware (e.g. `6.04`). You can view previous technique version folders for examples.
3. Update the [`src/data/techniques_version.json`](src/data/techniques_version.json) file to the version you just added.
4. (optional) [Create a pull request](https://github.com/bicarlsen/easy-biologic/pulls) to have it included in the package, so everybody benefits :).