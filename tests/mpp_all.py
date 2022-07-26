import os
import time
import math
import random
import pandas as pd

import easy_biologic as ebl
import easy_biologic.base_programs as blp
import bric_cycling_utilities as bcu
from bric_analysis_libraries import standard_functions as std


# helper functions
def create_path (base_path):
	'''
	Creates a path base_path/run-xx, where xx represents the largest run number
	found in the directory + 1
	:param base_path: Base path to save measurements in.
	:returns: Save path
	'''
	dirs = os.listdir (base_path)
	if len (dirs) is 0:
		run = 0
	else:
		runs = [int (dir.replace ('trial-', '')) for dir in dirs]
		run = max (runs)

	save_path = os.path.join (base_path, 'trial-{:02.0f}'.format (run + 1))		# path to data folder, relative
	return save_path

# lamp parameters
intensity = 0.5 # intensity multiplier
spectra = { 
	'red': 24.3 * intensity, 	# red 
	'green': 80.9 * intensity, 	# green
	'blue': 12.2 * intensity,  	# blue
	'uv' : 0 					# UV
}

# run parameters
channels = [ 0, 1, 2, 3, 4, 5, 6, 7 ]

sleep_time      = 5 * 6				# rest time after a JV scan 
run_time  		= (18 + 18) * 6 	# total run time in seconds
hold_interval 	= 18        		# interval between holds in seconds 
cb_type 		= 'between' 			# 'interval' or 'between'
hold_time 		= 18   		    	# hold time in seconds
probe_step 		= 1e-3					# probe step in volts.

base_path = 'test'

save_path = create_path (base_path)
bcu.log ('Saving data in {}'.format (save_path))
os.makedirs (save_path)

# experiment sequence
def define_rates (rates, channels):
	'''
	Creates a nested dictionary in which every JV experiment
	has assigned scan rate to apply to each channel.
	:param rates: A list containing sweep rates.
	:param channels: A list of channels used in the experiment.
	:returns: A nested dictionary.
	'''
	exp_rates = {i : {} for i in range (len (rates))}

	for ch in channels:
		random.shouffle (rates)

		for i in range (len (rates)):
			exp_rates [i] [ch] = rates [i]

	return exp_rates

def export_rates (
		data,
		path,
		name = 'scan_rate'
	):
	'''
	Takes the nested dictionary with information about the 
	applied scan rates and exports it as a .pkl and a .csv file.
	:param data: A nested dictionary.
	:param path: Path to save data.
	:param name: Name of the newly created files [Default: 'hold_voltage']
	:returns: A .pkl and .csv file.
	'''
	df = pd.DataFrame (data)
	df.rename_axis (index = 'channel', columns = 'measurement', inplace = True)
	std.export_df (df, path = path, name = name)


def define_voltages (hv_params):
    '''
    Creates a nested dictionary in which every experiment
    number has assigned voltages to apply during the hold
    to each channel.
    :param hv_params: A nested dictionary containing 
    MPP and Voc voltages obtained for each channel.
    :returns: A nested dictionary.
    '''

    exp_voltages = {i : {} for i in range (10)}

    for ch, data in hv_params.items ():
        mpp = data ['mpp']
        voc = data ['voc']
        voltages = [  
            -0.5 * mpp,
            -0.25 * mpp,
            0, 
            0.25 * mpp,
            0.5 * mpp,
            0.75 * mpp,
            mpp,
            1/3 * (voc - mpp) + mpp,
            2/3 * (voc - mpp) + mpp,
            voc
        ]
        random.shuffle (voltages)
        
        for i in range (10):
            exp_voltages [i][ch] = voltages [i]
    
    return exp_voltages

def export_voltages (
		data,
		path,
		name = 'hold_voltage'
	):
	'''
	Takes the nested dictionary with information about the 
	applied voltages and exports it as a .pkl and a .csv file.
	:param data: A nested dictionary.
	:param path: Path to save data.
	:param name: Name of the newly created files [Default: 'hold_voltage']
	:returns: A .pkl and .csv file.
	'''
	df = pd.DataFrame (data)
	df.rename_axis (index = 'channel', columns = 'measurement', inplace = True)
	std.export_df (df, path = path, name = name)

#--- callback ---
def callback (
	prg, 
	rest, 
	voltages = None, 
	jump 	= None, 
	rate 	= None,
	jump_step = 5,
	direction = 1,
	lamp = None
):	

	# Turn the light off
	lamp.off ()

	bcu.hold_jump (
		prg, 
		rest, 
		voltages = voltages, 
		jump 	= jump, 
		rate 	= rate,
		jump_step = jump_step,
		direction = direction
	)
	prg.update_voltages (prg.v_mpp)
	
	lamp.on ()


# program setup
bl = ebl.BiologicDevice( '192.168.1.2' )
bl.connect()

params = {
	'run_time': 	run_time,
	'probe_step': 	probe_step
}
mpp_params = {
	ch: params for ch in channels
}

jv_params = {
	'end'	: 0
	}

#JV scan rates
rates = [1, 10, 100, 1000, 10000, 100000]

ocv_params = {
	'time' 				: 1,
	'time_interval' 	: 0.1,
	'voltage_interval'  : 0.001
}


#--- run experiment ---
# lamp on
bcu.log ( 'Turning on lamp...' )

lamp = bcu.SolarSimulatorCommander( 'COM3', spectra = spectra )
lamp.on()

ocv = blp.OCV(
	bl,
	ocv_params,
	channels = channels
)
bcu.log ( 'Running OCV scan...')
ocv.run ()
ocv.save_data (os.path.join (save_path, 'ocv.csv'))
bcu.log ( 'OCV scan done...' )
bcu.log ( 'Turning off lamp...' )
lamp.off ()
time.sleep (sleep_time)

hv_params = {}
for ch, data in ocv.data.items ():
	voltages = [ datum.voltage for datum in data ]
	voc = sum (voltages)/len (voltages)
	hv_params [ch] = {'voc': voc}

ms_rates = define_rates (rates, channels)
export_rates (ms_rates, save_path)

for ms, ch_rate in ms_rates.items ():
	bcu.log ( 'Running JV scan #{}...'.format (ms) )
	
	for ch, rate in ch_rate.items ():
		bcu.log ( 'Applying scan rate {} mV/s on channel {}.'.format (rate, ch))

	jv_prms = {ch : {
		'start' : data ['voc'],
		'rate' : ch_rate [ch],
		**jv_params
		} for ch, data in hv_params }

	jv = blp.JV_Scan(
		bl,
		jv_prms,
		channels = channels
	)
	bcu.log ( 'Turning on lamp...' )
	lamp.on ()
	jv.run ()
	jv.save_data (os.path.join (save_path, 'jv/jv-{}.csv'.format (ms)))
	bcu.log ( 'JV scan done...' )

	bcu.log ( 'Turning off lamp...' )
	lamp.off ()
	bcu.log ( 'Initiating sleep for {} min...'.format (sleep_time/60) )
	time.sleep (sleep_time)



for ch, data in jv.data.items ():
	# taking vmpp
	best = min (data, key = lambda x: x.power)
	hv_params [ch] = {'mpp': best.voltage}


for ch, params in mpp_params.items ():
	params ['init_vmpp'] = hv_params [ch]['mpp']




ms_voltages = define_voltages (hv_params)
export_voltages (ms_voltages, save_path)

for ms, voltages in ms_voltages.items ():
	bcu.log ( 'Running degradation measurement #{}...'.format (ms) )
	
	for ch, voltage in voltages.items ():
		bcu.log ( 'Applying voltage {} on channel {}.'.format (voltage, ch))
	
	mpp = blp.MPP_Tracking(	
		bl,
		params,
		channels = channels
	)

	mpp.on_timeout( 
		callback, 
		hold_interval, 
		args  	= [ hold_time ], 
		timeout_type = cb_type,
		kwargs = { 
			'voltages'  : voltages,
			'jump'   	: None,
			'lamp' 		: lamp,
		}
	)
	bcu.log ( 'Turning on lamp...' )
	lamp.on ()
	bcu.log ( 'Running MPP tracking...' )
	mpp.run (os.path.join (save_path, 'mpp/mpp-{}.csv'.format (ms)))


	bcu.log ( 'Initiating sleep for {:.0f} min...'.format (2 * run_time / 60) )
	time.sleep (2 * run_time)



jv_prms = {ch : {
	'start' : data ['voc'],
	'rate' : 10,
	**jv_params
	} for ch, data in hv_params }

jv = blp.JV_Scan(
	bl,
	jv_prms,
	channels = channels
)

bcu.log ('Running final JV scan...')

jv.run ()
jv.save_data (os.path.join (save_path, 'jv/jv_end.csv'))

# lamp off
bcu.log ( 'Turning off lamp...' )
lamp.off ()

lamp.disconnect ()

bcu.log ( 'Program done.' )
