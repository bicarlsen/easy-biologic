import logging

import easy_biologic as ebl
import easy_biologic.base_programs as ebp

logging.basicConfig( level = logging.DEBUG )

channels = [ 0, 1, 2, 3 ,7 ]
by_channel = False
params = { 
	'time': 5 
}

save_path = 'data/ocv'
if not by_channel:
	# file if saving individually
	save_path += '.csv'

bl = ebl.BiologicDevice( '192.168.1.2' )
# bl.connect()
prg = ebp.OCV( bl, params, channels )

prg.run()
prg.save_data( save_path, by_channel = by_channel )