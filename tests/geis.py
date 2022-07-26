"""OCV example"""

from __future__ import print_function
import time
#from bio_logic import GeneralPotentiostat, OCV, CV
from ctypes import create_string_buffer, byref, POINTER, cast, c_uint32
import easy_biologic as ebio
import easy_biologic.__init__
import easy_biologic.base_programs as blp


def run():
    """Test the different techniques"""
    # Set the connection port
    USB = 'USB0'

    # Instantiate the instrument and connect to it
    b1 = ebio.BiologicDevice(USB)
    b1.kind.DeviceCode = 4#'DeviceCodes.KBIO_DEV_SP300'
    print('\nDevice type: ' + str(b1.kind))
    b1.connect()
    print('Potentiostat is connected: ' + str(b1.is_connected()))
    
    #params = {'time': 150,
    #          'time_interval': 0.01,
    #          'voltage_interval': 1.0
    #          }

    params2 = {'current': [0.00001],
            'final_frequency': 0.1,
            'initial_frequency': 100,
            'amplitude_current': 0.00001,
            'frequency_number': 100,
            'duration': 10,
            'vs_final': False,
            'time_interval': 0.1,
            'potential_interval': 0.001
            }

    params3 = {'voltage': [0.1],
            'final_frequency': 1,
            'initial_frequency': 10,
            'amplitude_voltage': 0.01,
            'frequency_number': 10,
            'duration': 10,
    #        'vs_final': False,
            'time_interval': 0.001,
            'current_interval': 0.001
            }

    #'vs_initial': True,
    #'wait': 0.5,
    #


    params = {'time': 10,
              'time_interval': 0.01,
              'voltage_interval': 1.0
              }

    #params = {'voltages': [1],
    #          'durations': [10]
    #          }

    #b1.load_technique(0,'OCV',params)
    #ocv = blp.OCV(
    #        b1,
    #        params,
    #        channels = [0]
    #        )

    #ca = blp.CA(
    #        b1,
    #        params,
    #        channels = [0]
    #        )
    #ca.run('data')
    #print(ca.data)

    #ocv = blp.OCV(
    #        b1,
    #        params,
    #        channels =  [0]
    #        )
    #ocv.run('data')

    #peis = blp.PEIS(
    #        b1,
    #        params3,
    #        channels =  [0]
    #        )        
    #peis.run('data')
    #print(peis.data)
    geis = blp.GEIS(
            b1,
            params2,
            channels =  [0]
            )        
    geis.run('data')
    print(geis.data)
    
    
    #time.sleep(0.1)
    #while True:
        # Get the currently available data on channel 0 (only what has
        # been gathered since last get_data)
    #    data_out = b1.get_data(0)

        # If there is none, assume the technique has finished
    #    if data_out is None:
    #        break

        # The data is available in lists as attributes on the data
        # object. The available data fields are listed in the API
        # documentation for the technique.
    #    print("Time:", data_out.time)
    #    print("Ewe:", data_out.Ewe)

        # If numpy is installed, the data can also be retrieved as
        # numpy arrays
    #    print('Time:', data_out.time_numpy)
    #    print('Ewe:', data_out.Ewe_numpy)
    #    time.sleep(0.1)

   

    #cv = CV(vs_initial=[True,True,True,True,True],
    #        voltage_step = [0,1,0,0,0],
    #        scan_rate = [0.01,0.01,0.01,0.01,0.01],
    #        record_every_dE=1.0,
     #       average_over_dE = False,
    #        N_cycles = 5,
    #        begin_measuring_I=0.5,
    #        end_measuring_I=1.0,
    #       I_range='KBIO_IRANGE_AUTO',
     #       E_range='KBIO_ERANGE_2_5',
     #       bandwidth='KBIO_BW_5'
    #        )

    # Load the technique onto channel 0 of the potentiostat and start it
    #potentiostat.load_technique(0, ocv)
    #potentiostat.start_channel(0)

if __name__ == '__main__':
    run()