import platform

# check that on Windows
if platform.system() != 'Windows':
	raise RuntimeError( 'Invalid Operating System: easy_biologic can only be used on Windows.' )


from .device import BiologicDevice
from .program import BiologicProgram
from .program import ProgramRunner

from . import program
from . import base_programs
