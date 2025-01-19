import platform

if platform.system() != "Windows":
    raise OSError("easy_biologic can only be used on Windows.")

from .device import BiologicDevice
from .program import BiologicProgram
from .program import ProgramRunner

from . import program
from . import base_programs
from .common import default_techniques_version