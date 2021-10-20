import platform

# check that on Windows
if platform.system() != 'Windows':
	raise RuntimeError( 'This library requires a Windows machine.' )


from .device import BiologicDevice
from .program import BiologicProgram
from .program import ProgramRunner

from . import program
from . import base_programs
