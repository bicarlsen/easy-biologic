import logging

import easy_biologic as ebl
import easy_biologic.base_programs as ebp

logging.basicConfig( level = logging.DEBUG )

channels = [ 0, 1, 2, 3 ,7 ]
save_path = 'data/mpp'

params = { 
	'run_time': 30
}


bl  = ebl.BiologicDevice( '192.168.0.1' )
ch_params = { ch: params for ch in channels }
prg = ebp.MPP( bl, ch_params )

prg.run( save_path )